import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import List

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AssetFeature:
    file_name: str
    index: int
    grid_pos: tuple  # (col, row)
    avg_color: List[int]  # [B, G, R]
    luminance: float  # 0-255
    volume: float  # % of cell filled with non-transparent pixels
    center_mass: tuple  # (x, y) relative to cell center (for alignment?)


class AssetIndexer:
    def __init__(self, items_per_row_override=None):
        self.items_per_row = items_per_row_override

    def analyze_file(self, file_path: str) -> List[AssetFeature]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []

        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            logger.error("Failed to load image.")
            return []

        h, w = img.shape[:2]

        # DEBUG: Probe middle row
        mid_y = h // 2
        probe_step = 20
        samples = img[mid_y, ::probe_step]
        print(f"  > Pixel Probe (y={mid_y}, step={probe_step}):")
        # Print simplified brightness
        lumas = [int(0.11 * p[0] + 0.59 * p[1] + 0.3 * p[2]) for p in samples]
        # Visualizing gaps: "." for low luma, "#" for high
        vis = "".join(["#" if l > 20 else "." for l in lumas])
        print(f"    {vis}")

        # 1. Prepare Alpha Mask
        # Try Color Keying again (Strict Black)
        # Most pixel art has absolute black (0,0,0) or near black background
        lower = np.array([0, 0, 0])
        upper = np.array([12, 12, 12])  # Tolerance for compression artifacts
        mask = cv2.inRange(img, lower, upper)
        alpha = 255 - mask

        # ... logic ...

        # If detection fails, use user-derived heuristic:
        # 131 items / 6 files = ~22 items per file.
        # 17 accessories / 1 file = 17 items.
        # Fits 11 cols x 2 rows = 22 slots.
        # 1920 / 11 = 174 px width.
        # 1080 / 6 = 180 px height (if 6 rows).
        # Let's try forcing 11 columns and detecting rows.

        estimated_cols = 0

        if estimated_cols <= 1:
            print(
                "  > Auto-detection failed. Falling back to Heuristic (11 items/row)."
            )
            estimated_cols = 11

        cols = self.items_per_row or estimated_cols
        if cols == 0:
            cols = 1

        cell_w = w // cols

        # Detect Rows from projections enabled by strict mask?
        row_proj = np.sum(alpha, axis=1)
        row_mask = (row_proj > 0).astype(int)
        r_starts = np.where(np.diff(row_mask) == 1)[0]
        # ...
        rows = len(r_starts)
        if row_mask[0]:
            rows += 1

        # Heuristic: If row detection fails (solid block), assume 2 rows?
        # Or 6 rows?
        # If 11 cols, 2 rows = 22 items. 131 / 6 = 21.8. Matches well.
        if rows <= 1:
            rows = 2
            print(f"  > Row detection failed. Defaulting to {rows} rows.")

        cell_h = h // rows
        print(f"  > Grid: {cols}x{rows} ({cell_w}x{cell_h}px)")

        features = []
        features = []
        idx = 0
        for row_idx in range(rows):
            for col_idx in range(cols):
                x1 = int(col_idx * cell_w)
                y1 = int(row_idx * cell_h)
                x2 = int((col_idx + 1) * cell_w)
                y2 = int((row_idx + 1) * cell_h)

                # Slicing
                cell = img[y1:y2, x1:x2]
                cell_alpha = alpha[y1:y2, x1:x2]

                # Check if empty (threshold 0.01% coverage to be safe)
                if np.sum(cell_alpha) == 0:
                    continue

                # Features
                pixels = cell[cell_alpha > 0]
                if len(pixels) > 0:
                    avg = np.mean(pixels, axis=0)  # [B, G, R, A]
                    vol = len(pixels) / (
                        cell.transpose(2, 0, 1).shape[1]
                        * cell.transpose(2, 0, 1).shape[2]
                    )
                    b_val, g_val, r_val = avg[0], avg[1], avg[2]
                    lum = 0.114 * b_val + 0.587 * g_val + 0.299 * r_val
                else:
                    avg = [0, 0, 0, 0]
                    vol = 0
                    lum = 0
                    r_val = 0

                print(f"    > Found Item: Row {row_idx}, Col {col_idx}, Vol {vol:.4f}")

                feat = AssetFeature(
                    file_name=os.path.basename(file_path),
                    index=idx,
                    grid_pos=(col_idx, row_idx),
                    avg_color=[int(x) for x in avg[:3]],
                    luminance=float(lum),
                    volume=float(vol),
                    center_mass=(0, 0),
                )
                features.append(feat)
                idx += 1

        return features

    def run(self, image_dir: str, output_json: str):
        import glob

        all_features = {}

        # Process Hair
        for cat in ["hair", "facial-hair", "accessory"]:
            print(f"Indexing {cat} from {image_dir}...")
            # Pattern matching
            files = sorted(glob.glob(os.path.join(image_dir, f"{cat}-*.png")))
            cat_feats = []

            # Global index for category?
            # User says "All styles are 0-indexed value".
            # Does hair-1 start at 0, and hair-2 continue? assumed YES.

            global_idx = 0
            for f in files:
                feats = self.analyze_file(f)
                # re-index based on global flow?
                # Analyze function returns indices 0..N for that file.
                # We should append them.
                for ft in feats:
                    ft.index = global_idx
                    global_idx += 1
                    cat_feats.append(asdict(ft))

            all_features[cat] = cat_feats
            print(f"Indexed {len(cat_feats)} items for {cat}.")

        with open(output_json, "w") as f:
            json.dump(all_features, f, indent=2)
        print(f"Saved asset index to {output_json}")


if __name__ == "__main__":
    indexer = AssetIndexer()  # Auto-detect defaults
    indexer.run(
        r"c:\Users\73spi\mystuff\hoopland-v2\data\images", "hoopland_assets.json"
    )

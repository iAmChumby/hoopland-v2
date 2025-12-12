"""
Appearance Analysis Module

Analyzes player headshot images to determine appearance attributes:
- Skin tone (1-10 scale)
- Hair style (0-130 index)
- Facial hair (0-24 index)
- Accessory (0-16 index)

Uses the manual appearance mapping as the authoritative source of truth
for style classifications. Enhanced with facial landmark detection for
more accurate ear visibility and chin region detection.
"""

try:
    import cv2
    import numpy as np

    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

import logging
from typing import Optional

import requests

from . import face_landmarks, mapping_loader

logger = logging.getLogger(__name__)


def analyze_player_appearance(image_url: str) -> dict:
    """
    Analyze a player headshot image and return appearance attributes.

    Uses facial landmark detection when available for improved accuracy:
    - Ear visibility detection for hair length estimation
    - Chin polygon for precise facial hair detection
    - Eyebrow position for forehead/hair boundary

    Args:
        image_url: URL to the player headshot image

    Returns:
        dict with keys: skin_tone, hair, facial_hair, accessory
    """
    result = {"skin_tone": 1, "hair": 0, "facial_hair": 0, "accessory": 0}

    if not CV_AVAILABLE:
        return result

    try:
        if not image_url:
            return result

        # Download image
        try:
            resp = requests.get(image_url, stream=True, timeout=5)
        except Exception:
            return result

        if resp.status_code != 200:
            return result

        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)

        if img is None:
            return result

        h, w = img.shape[:2]

        # Convert to YCrCb for skin detection
        # Handle alpha channel if present
        img_bgr = img[:, :, :3] if img.shape[2] == 4 else img
        ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
        lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        mask_skin = cv2.inRange(ycrcb, lower_skin, upper_skin)

        # Try to detect facial landmarks
        landmarks = None
        ear_visibility = None
        chin_polygon = None
        forehead_y = None

        try:
            landmarks = face_landmarks.detect_landmarks(img_bgr)
            if landmarks is not None:
                detector = face_landmarks.get_detector()
                if detector:
                    ear_visibility = detector.detect_ear_visibility(landmarks, w)
                    chin_polygon = detector.get_chin_polygon(landmarks)
                    forehead_y = detector.get_forehead_boundary(landmarks)
                    logger.debug(
                        f"Ears visible: L={ear_visibility[0]}, R={ear_visibility[1]}"
                    )
        except Exception as e:
            logger.debug(f"Landmark detection unavailable: {e}")

        # 1. Skin Tone Detection
        result["skin_tone"] = detect_skin_tone(img_bgr, mask_skin)

        # 2. Hair Style Detection (with landmark enhancement)
        result["hair"] = detect_hair_style(
            img, h, w, mask_skin, ear_visibility=ear_visibility, forehead_y=forehead_y
        )

        # 3. Facial Hair Detection (with chin polygon if available)
        result["facial_hair"] = detect_facial_hair(
            img, h, w, mask_skin, chin_polygon=chin_polygon
        )

        # 4. Accessory Detection
        result["accessory"] = detect_accessory(img, h, w, mask_skin)

    except Exception as e:
        logger.error(f"Error analyzing appearance: {e}")

    return result


def detect_skin_tone(img: np.ndarray, mask_skin: np.ndarray) -> int:
    """
    Detect skin tone on a 1-10 scale.
    Lower values = lighter skin, higher values = darker skin.
    """
    skin_pixels = img[mask_skin > 0]
    if len(skin_pixels) == 0:
        return 1

    avg_skin = np.mean(skin_pixels, axis=0)  # BGR
    # Calculate luminance (weighted sum)
    lum = 0.114 * avg_skin[0] + 0.587 * avg_skin[1] + 0.299 * avg_skin[2]
    # Map luminance to 1-10 scale (lighter = lower number)
    scale = 1 + (255 - lum) / 255 * 9
    return int(round(scale))


def detect_hair_style(
    img: np.ndarray,
    h: int,
    w: int,
    mask_skin: np.ndarray,
    ear_visibility: Optional[tuple[bool, bool]] = None,
    forehead_y: Optional[int] = None,
) -> int:
    """
    Detect hair style based on volume, texture, and coverage analysis.

    Enhanced with facial landmark detection:
    - ear_visibility: (left_visible, right_visible) - covered ears = longer hair
    - forehead_y: Y coordinate of forehead boundary for precise hair region

    Strategy:
    1. Analyze top portion of image for hair presence
    2. Estimate hair volume (how much of the head area is covered)
    3. Analyze texture (smooth vs textured/curly)
    4. Use ear visibility to refine length estimation
    5. Map to appropriate style from the mapping

    Returns:
        Hair style index (0-130)
    """
    # Determine hair region boundary
    if forehead_y is not None and forehead_y > 10:
        # Use landmark-based forehead boundary
        hair_region_height = forehead_y
    else:
        # Fallback to percentage-based
        hair_region_height = int(h * 0.35)

    hair_crop = img[0:hair_region_height, :]

    # Create mask for non-skin, non-background pixels
    mask_hair_region = mask_skin[0:hair_region_height, :]
    mask_not_skin = cv2.bitwise_not(mask_hair_region)

    # Convert to grayscale for analysis
    gray_hair = cv2.cvtColor(hair_crop, cv2.COLOR_BGR2GRAY)

    # Handle transparent backgrounds in PNG images
    if len(img.shape) == 3 and img.shape[2] == 4:
        # Has alpha channel - use it to mask out transparent background
        alpha_crop = img[0:hair_region_height, :, 3]
        mask_transparent = alpha_crop < 128  # Treat semi-transparent as background
        mask_bg = mask_transparent.astype(np.uint8) * 255
    else:
        # No alpha channel - filter out very dark and very bright backgrounds
        mask_bg_dark = gray_hair < 15  # Very dark = likely transparent
        mask_bg_bright = gray_hair > 235  # Very bright = white background
        mask_bg = (mask_bg_dark | mask_bg_bright).astype(np.uint8) * 255

    # Hair = not skin and not background
    mask_hair = cv2.bitwise_and(mask_not_skin, cv2.bitwise_not(mask_bg))

    # For volume calculation, estimate the HEAD width from skin pixels
    skin_columns = np.any(mask_skin > 0, axis=0)
    head_width = np.count_nonzero(skin_columns)
    if head_width < w * 0.3:  # Sanity check
        head_width = int(w * 0.6)  # Assume head takes ~60% of width

    # Calculate hair volume relative to estimated head area
    head_area = hair_region_height * head_width
    hair_pixels = np.count_nonzero(mask_hair)
    hair_coverage = hair_pixels / head_area if head_area > 0 else 0

    # Analyze texture using edge detection
    texture_score = analyze_hair_texture(hair_crop, mask_hair)

    # Determine hair volume classification
    volume = classify_hair_volume_from_coverage(hair_coverage)

    # Determine hair texture classification
    texture = classify_hair_texture_from_score(texture_score, hair_coverage)

    # ENHANCED: Use ear visibility to refine estimation
    # If ears are NOT visible (covered), hair is likely longer
    if ear_visibility is not None:
        left_visible, right_visible = ear_visibility

        if not left_visible and not right_visible:
            # Both ears covered - hair is definitely longer
            # Boost volume classification
            if volume == "none":
                volume = "low"
            elif volume == "low":
                volume = "medium"
            elif volume == "medium":
                volume = "high"
            logger.debug(f"Both ears covered - boosted volume to {volume}")

        elif not left_visible or not right_visible:
            # One ear covered - hair is medium length
            if volume == "none":
                volume = "low"
            elif volume == "low":
                volume = "medium"
            logger.debug(f"One ear covered - adjusted volume to {volume}")

    # Select best matching style with variety based on hair pixel count
    return select_hair_style(volume, texture, variety_seed=hair_pixels)


def analyze_hair_texture(hair_crop: np.ndarray, mask_hair: np.ndarray) -> float:
    """
    Analyze hair texture using edge detection.
    Higher score = more textured (curly, afro, dreads)
    Lower score = smoother (bald, straight, fade)

    Returns:
        Texture score (0.0 - 1.0)
    """
    if np.count_nonzero(mask_hair) == 0:
        return 0.0

    gray = cv2.cvtColor(hair_crop, cv2.COLOR_BGR2GRAY)

    # Apply Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Only count edges in hair region
    hair_edges = cv2.bitwise_and(edges, mask_hair)

    # Calculate edge density within hair region
    hair_pixel_count = np.count_nonzero(mask_hair)
    edge_pixel_count = np.count_nonzero(hair_edges)

    texture_score = edge_pixel_count / hair_pixel_count if hair_pixel_count > 0 else 0

    # Normalize to 0-1 range (empirically, texture scores range 0-0.3)
    return min(texture_score / 0.3, 1.0)


def classify_hair_volume_from_coverage(coverage: float) -> str:
    """
    Classify hair volume based on coverage percentage.

    Args:
        coverage: Percentage of hair region covered by hair (0.0 - 1.0)

    Returns:
        Volume classification: 'none', 'low', 'medium', 'high', 'very_high'
    """
    # Thresholds tuned based on NBA headshot analysis with alpha channel handling
    # Note: Coverage can be low even for players with hair due to:
    # - Dark hair near skin being classified as skin
    # - Dreads/braids being sparse in the hair region
    if coverage < 0.03:
        return "none"  # Truly bald
    elif coverage < 0.10:
        return "low"  # Very short buzzcut, fade
    elif coverage < 0.20:
        return "medium"  # Short styles, short curls, short dreads
    elif coverage < 0.35:
        return "high"  # Medium afro, longer dreads
    else:
        return "very_high"  # Large afro, long flowing hair


def classify_hair_texture_from_score(texture_score: float, coverage: float) -> str:
    """
    Classify hair texture based on edge density.

    Args:
        texture_score: Texture score from edge analysis (0.0 - 1.0)
        coverage: Hair coverage to help distinguish styles

    Returns:
        Texture classification: 'smooth', 'wavy', 'curly', 'afro', 'dreads'
    """
    if coverage < 0.05:
        return "smooth"  # Bald has no texture

    if texture_score < 0.2:
        return "smooth"  # Straight, bald, buzzcut
    elif texture_score < 0.4:
        return "wavy"  # Wavy, slight texture
    elif texture_score < 0.6:
        return "curly"  # Curly, coils
    elif texture_score < 0.8:
        return "afro"  # Afro, high texture
    else:
        return "dreads"  # Dreads, braids, very high texture


def select_hair_style(volume: str, texture: str, variety_seed: int = 0) -> int:
    """
    Select the best matching hair style based on detected attributes.
    Uses the mapping loader to find styles matching the criteria.

    Args:
        volume: Volume classification
        texture: Texture classification
        variety_seed: Seed for deterministic variety within matched styles

    Returns:
        Hair style index (0-130)
    """
    # Build index if not cached
    hair_index = mapping_loader.build_hair_index_by_attributes()

    # Get candidates matching volume
    volume_candidates = set(hair_index.get("volume", {}).get(volume, []))

    # Get candidates matching texture
    texture_candidates = set(hair_index.get("texture", {}).get(texture, []))

    # Find intersection of volume and texture
    matching = volume_candidates & texture_candidates

    if matching:
        # ADD VARIETY: Pick from matches based on variety_seed
        sorted_matches = sorted(matching)
        return sorted_matches[variety_seed % len(sorted_matches)]

    # For distinctive textures (dreads, afro), prefer texture match over volume
    # These styles are recognizable even at lower detected volumes
    if texture in ("dreads", "afro", "curly"):
        if texture_candidates:
            # Pick a style from the texture category with variety
            for vol_level in [volume, "medium", "low", "high"]:
                vol_set = set(hair_index.get("volume", {}).get(vol_level, []))
                cross = texture_candidates & vol_set
                if cross:
                    sorted_cross = sorted(cross)
                    return sorted_cross[variety_seed % len(sorted_cross)]
            sorted_tex = sorted(texture_candidates)
            return sorted_tex[variety_seed % len(sorted_tex)]

    # Fallback: prefer volume match for non-distinctive textures
    if volume_candidates:
        sorted_vol = sorted(volume_candidates)
        return sorted_vol[variety_seed % len(sorted_vol)]

    # Final fallback based on texture with sensible defaults
    texture_fallback = {
        "smooth": 0,  # Bald/minimal
        "wavy": 18,  # Wavy short cut
        "curly": 2,  # Short curls
        "afro": 10,  # Rounded medium afro
        "dreads": 19,  # Short dreads/twists
    }
    if texture in texture_fallback:
        return texture_fallback[texture]

    # Ultimate fallback based on volume
    fallback_map = {
        "none": 0,  # Bald
        "low": 1,  # Tight buzzcut
        "medium": 2,  # Short curls
        "high": 17,  # Fluffy afro
        "very_high": 82,  # Large afro
    }
    return fallback_map.get(volume, 0)


def detect_facial_hair(
    img: np.ndarray,
    h: int,
    w: int,
    mask_skin: np.ndarray,
    chin_polygon: Optional[np.ndarray] = None,
) -> int:
    """
    Detect facial hair by analyzing the chin/jawline region.

    Enhanced with facial landmark detection:
    - chin_polygon: Precise chin region from landmarks for better isolation

    Strategy:
    1. Focus on lower face region (chin area)
    2. Look for dark pixels within skin region (facial hair is darker)
    3. Analyze density and coverage pattern
    4. Map to facial hair style based on density

    Returns:
        Facial hair style index (0-24)
    """
    # Determine chin region
    if chin_polygon is not None and len(chin_polygon) > 3:
        # Use landmark-based chin polygon for precise region
        chin_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.fillPoly(chin_mask, [chin_polygon.astype(np.int32)], 255)

        # Find bounding box of chin region
        y_coords = chin_polygon[:, 1]
        chin_start = int(np.min(y_coords))
        chin_end = int(np.max(y_coords))

        chin_region = img[chin_start:chin_end, :]
        chin_mask_cropped = chin_mask[chin_start:chin_end, :]

        logger.debug(f"Using landmark-based chin region: {chin_start}-{chin_end}")
    else:
        # Fallback to percentage-based chin region
        chin_start = int(h * 0.55)
        chin_region = img[chin_start:, :]
        chin_mask_cropped = mask_skin[chin_start:, :]

    # Find skin pixels in chin region
    chin_skin_count = np.count_nonzero(chin_mask_cropped)
    if chin_skin_count < 100:
        return 0  # Can't detect, assume clean shaven

    # Get skin pixels - ensure 3 channels for color analysis
    if len(chin_region.shape) == 3 and chin_region.shape[2] == 4:
        chin_region_bgr = chin_region[:, :, :3]
    else:
        chin_region_bgr = chin_region

    chin_skin_pixels = chin_region_bgr[chin_mask_cropped > 0]

    # Look for dark patches within skin region (facial hair indicators)
    gray_chin = cv2.cvtColor(chin_region_bgr, cv2.COLOR_BGR2GRAY)

    # Find dark pixels that overlap with skin (potential facial hair)
    # Use adaptive threshold based on average skin brightness
    chin_skin_brightness = np.mean(chin_skin_pixels)
    dark_threshold = max(60, chin_skin_brightness * 0.5)  # Beard is darker

    dark_mask = gray_chin < dark_threshold
    facial_hair_mask = cv2.bitwise_and(
        dark_mask.astype(np.uint8) * 255, chin_mask_cropped
    )

    # Calculate facial hair coverage
    facial_hair_pixels = np.count_nonzero(facial_hair_mask)
    facial_hair_ratio = (
        facial_hair_pixels / chin_skin_count if chin_skin_count > 0 else 0
    )

    # Check for textured areas in chin region (beards have texture)
    edges = cv2.Canny(gray_chin, 20, 80)
    chin_edges = cv2.bitwise_and(edges, chin_mask_cropped)
    edge_ratio = (
        np.count_nonzero(chin_edges) / chin_skin_count if chin_skin_count > 0 else 0
    )

    # Use chin_skin_count as a variety seed (different for each player's unique face)
    variety_seed = chin_skin_count
    
    # Combine metrics to classify facial hair density
    return select_facial_hair_style(facial_hair_ratio, edge_ratio, player_id=variety_seed)


def select_facial_hair_style(dark_ratio: float, edge_ratio: float, player_id: int = 0) -> int:
    """
    Select facial hair style based on detection metrics.

    Args:
        dark_ratio: Ratio of dark pixels in chin region
        edge_ratio: Ratio of edge pixels in chin region (texture)
        player_id: Optional player ID for deterministic variety

    Returns:
        Facial hair style index (0-24)
    """
    # Build facial hair index
    fh_index = mapping_loader.build_facial_hair_index_by_density()

    # Determine density classification
    # Weight edge ratio higher as beards have significant texture
    combined_score = dark_ratio * 0.4 + edge_ratio * 0.6
    
    # Log for debugging
    logger.debug(f"Facial hair detection: dark={dark_ratio:.3f}, edge={edge_ratio:.3f}, combined={combined_score:.3f}")

    # FIXED THRESHOLDS - more conservative to prevent over-classification
    # Most NBA players have some edge texture even without beards
    if combined_score < 0.02:
        density = "none"
    elif combined_score < 0.05:
        density = "stubble"
    elif combined_score < 0.10:
        density = "goatee"
    elif combined_score < 0.18:
        density = "beard"
    else:
        density = "full_beard"

    # Get styles for this density
    candidates = fh_index.get(density, [0])

    if not candidates:
        return 0  # Clean shaven fallback

    # ADD VARIETY: Use player_id to deterministically select from candidates
    # This ensures the same player always gets the same style, but different
    # players get different styles within the same density category
    if len(candidates) > 1:
        selection_index = player_id % len(candidates)
        return candidates[selection_index]
    
    return candidates[0]


def detect_accessory(img: np.ndarray, h: int, w: int, mask_skin: np.ndarray) -> int:
    """
    Detect head accessories (headbands, caps, etc.).

    Strategy:
    1. Analyze forehead region for horizontal bands
    2. Check for consistent colored stripes
    3. Detect if hair area is covered uniformly (cap/beanie)

    Returns:
        Accessory style index (0-16)
    """
    # Focus on forehead region (between top of head and eyes)
    forehead_start = int(h * 0.10)
    forehead_end = int(h * 0.30)
    forehead_region = img[forehead_start:forehead_end, :]

    # Convert to grayscale for analysis
    gray_forehead = cv2.cvtColor(forehead_region, cv2.COLOR_BGR2GRAY)

    # Look for horizontal bands (headbands appear as consistent color stripes)
    # Analyze row-wise variance - require very low variance for true headband
    row_means = np.mean(gray_forehead, axis=1)
    row_stds = np.std(gray_forehead, axis=1)

    # A headband would show as rows with very low variance (uniform color)
    # Use stricter threshold to avoid false positives
    low_variance_rows = row_stds < 12

    # Count consecutive low-variance rows (potential headband)
    max_band_height = 0
    current_band = 0
    band_brightness = []
    band_start = -1

    for i, is_low_var in enumerate(low_variance_rows):
        if is_low_var:
            if current_band == 0:
                band_start = i
            current_band += 1
            band_brightness.append(row_means[i])
        else:
            if current_band > max_band_height:
                max_band_height = current_band
            current_band = 0
            band_brightness = []

    # Check final band
    if current_band > max_band_height:
        max_band_height = current_band

    # Headband detection: 8+ pixel height avoids hair line false positives
    # Also check that the band spans width (real headband, not hairline)
    if max_band_height >= 8 and band_brightness:
        avg_band_brightness = np.mean(band_brightness)

        # Verify it's a real headband by checking the band is at forehead level
        # (not at the very top which could be background)
        if band_start > 5:  # Not at the very top edge
            # Classify by color
            if avg_band_brightness < 60:
                return 1  # Thin Black Athletic Headband
            elif avg_band_brightness > 180:
                return 4  # Thin White Athletic Headband
            else:
                return 2  # Thick Black and White Headband

    # Check for sunglasses/eye band (much stricter detection)
    # Only detect if there's a very clear dark band across eye level
    eye_level_start = int(h * 0.35)
    eye_level_end = int(h * 0.45)
    eye_region = img[eye_level_start:eye_level_end, :]
    gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)

    # Check for consistent dark band (sunglasses create uniform darkness)
    eye_row_means = np.mean(gray_eye, axis=1)
    eye_row_stds = np.std(gray_eye, axis=1)

    # Sunglasses: multiple rows of very dark, low-variance pixels
    dark_uniform_rows = (eye_row_means < 40) & (eye_row_stds < 20)
    if np.sum(dark_uniform_rows) >= 5:
        return 6  # Black Sunglasses/Goggles

    # No accessory detected
    return 0


def get_skin_tone(image_url: str) -> int:
    """
    Wrapper for legacy compatibility.
    Returns just the skin tone value.
    """
    res = analyze_player_appearance(image_url)
    return res["skin_tone"]

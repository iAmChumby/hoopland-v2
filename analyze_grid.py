
import cv2
import numpy as np
import os
import sys

TARGET_FILE = r"c:\Users\73spi\mystuff\hoopland-v2\data\images\facial-hair-1.png"

def analyze_grid():
    if not os.path.exists(TARGET_FILE):
        print(f"File not found: {TARGET_FILE}")
        return

    print(f"Loading {TARGET_FILE}...")
    img = cv2.imread(TARGET_FILE, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Failed to load image.")
        return

    # Extract Alpha channel
    if img.shape[2] < 4:
        print("Image has no alpha channel. Cannot detect sprites by transparency.")
        return

    alpha = img[:, :, 3]
    h, w = alpha.shape

    # Find contours
    print("Finding contours...")
    contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(contours)} disconnected blobs.")

    # Get bounding boxes
    boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw > 2 and bh > 2: # Filter noise
            boxes.append((x, y, bw, bh))

    # Sort by Y (rows) then X (cols)
    # Allow small fuzz factor for Y alignment
    boxes.sort(key=lambda b: (int(b[1] // 20), b[0]))

    if not boxes:
        print("No sprites found.")
        return

    print("\nTop 10 Boxes (X, Y, W, H):")
    for b in boxes[:10]:
        print(b)

    # Estimate Grid
    # Gaps between X coords
    xs = [b[0] for b in boxes]
    min_gap = w # Start with image width
    
    # Calculate horizontal gaps
    gaps = []
    for i in range(len(boxes) - 1):
        # Only compare if in same 'row' (Y diff is small)
        if abs(boxes[i][1] - boxes[i+1][1]) < 20:
             gap = boxes[i+1][0] - boxes[i][0]
             if gap > 10: # Filter overlapping
                 gaps.append(gap)
    
    if gaps:
        median_stride = np.median(gaps)
        print(f"\nEstimated Horizontal Stride: {median_stride:.2f} px")
        
        # Verify columns per row
        # 1920 / stride
        approx_cols = 1920 / median_stride
        print(f"Approximate Columns per Row: {approx_cols:.2f}")
    else:
        print("\nCould not determine stride (only 1 item per row?).")

    # Item Size estimate
    ws = [b[2] for b in boxes]
    hs = [b[3] for b in boxes]
    print(f"Avg Sprite Size: {np.mean(ws):.1f}x{np.mean(hs):.1f}")
    print(f"Max Sprite Size: {np.max(ws)}x{np.max(hs)}")

if __name__ == "__main__":
    analyze_grid()

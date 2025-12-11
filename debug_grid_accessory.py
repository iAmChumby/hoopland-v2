import cv2
import numpy as np

img = cv2.imread(r"c:\Users\73spi\mystuff\hoopland-v2\data\images\accessory-1.png", cv2.IMREAD_UNCHANGED)
h, w = img.shape[:2]

# Alpha
# Check BG color first
print(f"Top-Left Pixel: {img[0,0]}")
if img.shape[2] == 4:
    print("Has Alpha Channel")
    alpha = img[:,:,3]
else:
    print("3-Channel Image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bg_luma = gray[0,0]
    print(f"BG Luma: {bg_luma}")
    
    if bg_luma > 200: # Light background
        print("Inverting threshold for Light BG...")
        _, alpha = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    else:
        print("Standard threshold for Dark BG...")
        _, alpha = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)

# Horizontal Projection (to find columns)
col_proj = np.sum(alpha, axis=0)
col_mask = (col_proj > 0).astype(int)

# Detect gaps
c_gaps = np.where(col_mask == 0)[0]
print(f"Column Gaps (pixels with 0 alpha sum): {len(c_gaps)}")

starts = np.where(np.diff(col_mask) == 1)[0]
ends = np.where(np.diff(col_mask) == -1)[0]
if col_mask[0]: starts = np.insert(starts, 0, 0)
if col_mask[-1]: ends = np.append(ends, w)

print(f"Detected {len(starts)} distinct column islands.")
for s, e in zip(starts, ends):
    print(f"  > Col: {s}-{e} (Width: {e-s}) center={s + (e-s)//2}")

# Vertical Projection (to find rows)
row_proj = np.sum(alpha, axis=1)
row_mask = (row_proj > 0).astype(int)

r_gaps = np.where(row_mask == 0)[0]
print(f"Row Gaps: {len(r_gaps)}")

r_starts = np.where(np.diff(row_mask) == 1)[0]
r_ends = np.where(np.diff(row_mask) == -1)[0]
if row_mask[0]: r_starts = np.insert(r_starts, 0, 0)
if row_mask[-1]: r_ends = np.append(r_ends, h)

print(f"Detected {len(r_starts)} distinct row islands.")
for s, e in zip(r_starts, r_ends):
    print(f"  > Row: {s}-{e} (Height: {e-s}) center={s + (e-s)//2}")

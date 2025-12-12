import os
import cv2
import glob

IMAGE_DIR = r"c:\Users\73spi\mystuff\hoopland-v2\data\images"


def analyze():
    files = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
    for f in files:
        img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Failed to load {os.path.basename(f)}")
            continue

        h, w = img.shape[:2]
        print(f"File: {os.path.basename(f)} | Size: {w}x{h}")

        # Try to guess cell size
        # Hoop Land is 16-bit style. Char sprites might be ~32px?
        # Let's check common divisors
        divs = [16, 24, 32, 48, 64]
        guesses = []
        for d in divs:
            if w % d == 0 and h % d == 0:
                guesses.append(d)
        print(f"  > Possible cell sizes: {guesses}")


if __name__ == "__main__":
    analyze()

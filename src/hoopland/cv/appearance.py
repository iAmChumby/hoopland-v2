import cv2
import numpy as np
import requests
import logging

logger = logging.getLogger(__name__)

def get_skin_tone(image_url):
    """
    Determines skin tone code (1-10) from an image URL.
    """
    try:
        if not image_url:
            logger.warning("Empty image URL provided.")
            return 1
            
        logger.debug(f"Fetching image: {image_url}")
        resp = requests.get(image_url, stream=True, timeout=5)
        
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch image {image_url}: Status {resp.status_code}")
            return 1
            
        # Convert to numpy array
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        
        if img is None:
            return 1 # Fallback
            
        # Convert to YCrCb
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        
        # Skin color range in YCrCb (Approximate)
        lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        
        mask = cv2.inRange(ycrcb, lower_skin, upper_skin)
        
        # Calculate average color of skin pixels
        skin_pixels = img[mask > 0]
        
        if len(skin_pixels) == 0:
            return 1 # Fallback
            
        avg_color = np.mean(skin_pixels, axis=0)
        
        # Map average BGR to 1-10 scale
        # This is a simplified mapping based on brightness/darkness 
        # A real implementation might use KNN against known skin tone palettes.
        # Here we use luminance approximation for simplicity as a placeholder.
        luminance = 0.114 * avg_color[0] + 0.587 * avg_color[1] + 0.299 * avg_color[2]
        
        # Invert: Darker skin (low luminance) -> Higher Code (maybe?) 
        # Spec says "0-10 codes". Usually 1 is light, 10 is dark or vice versa.
        # Let's assume 1=Light, 10=Dark.
        # Luminance 0 (Black) -> 10, Luminance 255 (White) -> 1
        
        scale = 1 + (255 - luminance) / 255 * 9
        return int(round(scale))

    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return 1

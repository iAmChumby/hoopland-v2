try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    
import requests
import logging

logger = logging.getLogger(__name__)


import json
import os
import math

# Load Asset Index
ASSETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "hoopland_assets.json")
ASSETS_CACHE = {}

def load_assets():
    global ASSETS_CACHE
    if not ASSETS_CACHE and os.path.exists(ASSETS_FILE):
        try:
            with open(ASSETS_FILE, 'r') as f:
                ASSETS_CACHE = json.load(f)
            logger.info("Loaded Hoopland Asset Index.")
        except Exception as e:
            logger.error(f"Failed to load assets: {e}")

def match_asset(category: str, target_rgb: tuple) -> int:
    """Finds best matching asset index based on color distance."""
    if not ASSETS_CACHE:
        load_assets()
    
    candidates = ASSETS_CACHE.get(category, [])
    if not candidates:
        return 0
        
    best_idx = 0
    min_dist = float('inf')
    
    r, g, b = target_rgb
    
    for item in candidates:
        # Asset color is BGR or RGB? AssetIndexer saved [B, G, R].
        # Let's assume AssetIndexer saved [B, G, R] as per its code `avg[:3]`.
        # So stored is [B, G, R].
        # Target passed here should probably be [R, G, B] usually.
        # Let's align them.
        
        ac = item['avg_color'] 
        # AssetIndexer: avg = np.mean... [B, G, R]. JSON: [B, G, R]
        
        # Distance (Euclidean in RGB space)
        # item is BGR, target is RGB
        dist = math.sqrt((ac[2]-r)**2 + (ac[1]-g)**2 + (ac[0]-b)**2)
        
        if dist < min_dist:
            min_dist = dist
            best_idx = item['index']
            
    return best_idx

def analyze_player_appearance(image_url: str) -> dict:
    """
    Returns dict with keys: skin_tone, hair, facial_hair, accessory
    """
    result = {"skin_tone": 1, "hair": 0, "facial_hair": 0}
    
    if not CV_AVAILABLE:
        return result

    try:
        if not image_url:
            return result
            
        # Download
        # logger.debug(f"Fetching image: {image_url}") # Reduce noise
        try:
            resp = requests.get(image_url, stream=True, timeout=5)
        except:
            return result
            
        if resp.status_code != 200:
            return result
            
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        
        if img is None:
            return result

        # 1. Skin Tone (Existing Logic)
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        mask_skin = cv2.inRange(ycrcb, lower_skin, upper_skin)
        
        skin_pixels = img[mask_skin > 0]
        if len(skin_pixels) > 0:
            avg_skin = np.mean(skin_pixels, axis=0) # BGR
            lum = 0.114*avg_skin[0] + 0.587*avg_skin[1] + 0.299*avg_skin[2]
            scale = 1 + (255 - lum) / 255 * 9
            result["skin_tone"] = int(round(scale))
        
        # 2. Hair Color Estimate
        # Heuristic: Sample top 20% of image (forehead/hair)
        h, w = img.shape[:2]
        hair_crop = img[0:int(h*0.25), :]
        
        # Exclude skin from hair crop (simple avoidance)
        # We want dark/dominant color that isn't background or skin.
        # Assuming background is white/transparent?
        # Let's just take average of "non-skin, non-white" pixels.
        
        mask_hair = cv2.bitwise_not(mask_skin[0:int(h*0.25), :])
        # Also filter bright background (white)
        gray_hair = cv2.cvtColor(hair_crop, cv2.COLOR_BGR2GRAY)
        _, mask_bg = cv2.threshold(gray_hair, 240, 255, cv2.THRESH_BINARY)
        mask_hair = cv2.bitwise_and(mask_hair, cv2.bitwise_not(mask_bg))
        
        hair_pixels = hair_crop[mask_hair > 0]
        if len(hair_pixels) > 0:
            avg_hair = np.mean(hair_pixels, axis=0) # BGR
            # Match to asset (Target RBG)
            # Match function expects RGB target
            best_hair = match_asset("hair", (avg_hair[2], avg_hair[1], avg_hair[0]))
            result["hair"] = best_hair
            
            # Use same color for beard for now?
            # Or assume no beard unless we detect chin color?
            # Detecting chin beard is hard without landmarks.
            # Default to no beard (0) or shadow?
            # Let's randomize beard if old? 
            # For now, just map hair style.
            pass

    except Exception as e:
        logger.error(f"Error analyzing apperance: {e}")
        
    return result

def get_skin_tone(image_url):
    # Wrapper for legacy compatibility
    res = analyze_player_appearance(image_url)
    return res["skin_tone"]

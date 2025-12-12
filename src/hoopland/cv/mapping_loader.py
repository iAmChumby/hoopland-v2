"""
Appearance Mapping Loader

Loads and provides access to the manual appearance mappings from 
data/mappings/appearance-mapping.json. This is the authoritative source 
of truth for mapping visual features to Hoopland character style indices.

Categories:
- accessories: 17 styles (index 0-16)
- facial_hair: 25 styles (index 0-24)
- hair: 131 styles (index 0-130)
"""

import json
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Path to the appearance mapping file
MAPPING_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "mappings",
    "appearance-mapping.json",
)

# Global cache for mappings
_MAPPING_CACHE: Dict[str, Any] = {}


def load_appearance_mapping() -> Dict[str, Any]:
    """
    Load the appearance mapping JSON file.
    Returns cached data if already loaded.
    """
    global _MAPPING_CACHE
    
    if _MAPPING_CACHE:
        return _MAPPING_CACHE
    
    if not os.path.exists(MAPPING_FILE):
        logger.error(f"Appearance mapping file not found: {MAPPING_FILE}")
        return {}
    
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        _MAPPING_CACHE = data
        logger.info(f"Loaded appearance mapping: {data.get('meta', {})}")
        return _MAPPING_CACHE
    
    except Exception as e:
        logger.error(f"Failed to load appearance mapping: {e}")
        return {}


def get_all_styles(category: str) -> List[Dict[str, Any]]:
    """
    Get all styles for a category.
    
    Args:
        category: One of 'accessories', 'facial_hair', or 'hair'
    
    Returns:
        List of style dictionaries
    """
    mapping = load_appearance_mapping()
    mappings = mapping.get("mappings", {})
    return mappings.get(category, [])


def get_style_by_index(category: str, index: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific style by its index.
    
    Args:
        category: One of 'accessories', 'facial_hair', or 'hair'
        index: The 0-based style index
    
    Returns:
        Style dictionary or None if not found
    """
    styles = get_all_styles(category)
    for style in styles:
        if style.get("index") == index:
            return style
    return None


def get_style_description(category: str, index: int) -> str:
    """
    Get the description for a style by index.
    
    Args:
        category: One of 'accessories', 'facial_hair', or 'hair'
        index: The 0-based style index
    
    Returns:
        Description string or empty string if not found
    """
    style = get_style_by_index(category, index)
    return style.get("description", "") if style else ""


def search_styles(category: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Search for styles matching any of the given keywords.
    
    Args:
        category: One of 'accessories', 'facial_hair', or 'hair'
        keywords: List of keywords to search for (case-insensitive)
    
    Returns:
        List of matching style dictionaries
    """
    styles = get_all_styles(category)
    keywords_lower = [k.lower() for k in keywords]
    
    matches = []
    for style in styles:
        desc = style.get("description", "").lower()
        if any(kw in desc for kw in keywords_lower):
            matches.append(style)
    
    return matches


def get_style_count(category: str) -> int:
    """Get the total number of styles in a category."""
    return len(get_all_styles(category))


# Style classification helpers based on description parsing

def classify_hair_length(description: str) -> str:
    """
    Classify hair length from description.
    
    Returns one of: 'bald', 'very_short', 'short', 'medium', 'long'
    """
    desc_lower = description.lower()
    
    if any(kw in desc_lower for kw in ["bald", "shaved head"]):
        return "bald"
    if any(kw in desc_lower for kw in ["very short", "buzzcut", "minimal"]):
        return "very_short"
    if any(kw in desc_lower for kw in ["long", "over shoulders", "hanging down"]):
        return "long"
    if any(kw in desc_lower for kw in ["medium"]):
        return "medium"
    # Default to short for most styles
    return "short"


def classify_hair_texture(description: str) -> str:
    """
    Classify hair texture from description.
    
    Returns one of: 'smooth', 'wavy', 'curly', 'afro', 'dreads', 'braids'
    """
    desc_lower = description.lower()
    
    if any(kw in desc_lower for kw in ["dreads", "dread", "twists"]):
        return "dreads"
    if any(kw in desc_lower for kw in ["braid", "braids"]):
        return "braids"
    if any(kw in desc_lower for kw in ["afro", "coils", "coil"]):
        return "afro"
    if any(kw in desc_lower for kw in ["curl", "curls", "curly", "ringlets"]):
        return "curly"
    if any(kw in desc_lower for kw in ["wavy", "wave"]):
        return "wavy"
    # Default to smooth (includes bald, fade, buzzcut, straight, ponytail, bun)
    return "smooth"


def classify_hair_volume(description: str) -> str:
    """
    Classify hair volume from description.
    
    Returns one of: 'none', 'low', 'medium', 'high', 'very_high'
    """
    desc_lower = description.lower()
    
    if any(kw in desc_lower for kw in ["bald", "shaved head"]):
        return "none"
    if any(kw in desc_lower for kw in ["very large", "massive", "highest volume", "puffy"]):
        return "very_high"
    if any(kw in desc_lower for kw in ["large", "high volume", "fluffy", "wild"]):
        return "high"
    if any(kw in desc_lower for kw in ["medium", "rounded afro"]):
        return "medium"
    if any(kw in desc_lower for kw in ["buzzcut", "fade", "minimal", "very short", "tight"]):
        return "low"
    # Default to medium
    return "medium"


def classify_facial_hair_density(description: str) -> str:
    """
    Classify facial hair density from description.
    
    Returns one of: 'none', 'stubble', 'goatee', 'beard', 'full_beard'
    """
    desc_lower = description.lower()
    
    if any(kw in desc_lower for kw in ["clean shaven", "no facial hair"]):
        return "none"
    if any(kw in desc_lower for kw in ["full", "long", "dark beard"]):
        return "full_beard"
    if any(kw in desc_lower for kw in ["boxed beard", "beard", "chin strap"]):
        return "beard"
    if any(kw in desc_lower for kw in ["goatee", "soul patch", "moustache", "chin patch"]):
        return "goatee"
    if any(kw in desc_lower for kw in ["stubble", "scruff", "light", "pencil"]):
        return "stubble"
    return "none"


def get_styles_by_hair_length(length: str) -> List[Dict[str, Any]]:
    """Get all hair styles matching a length classification."""
    styles = get_all_styles("hair")
    return [s for s in styles if classify_hair_length(s.get("description", "")) == length]


def get_styles_by_hair_texture(texture: str) -> List[Dict[str, Any]]:
    """Get all hair styles matching a texture classification."""
    styles = get_all_styles("hair")
    return [s for s in styles if classify_hair_texture(s.get("description", "")) == texture]


def get_styles_by_facial_hair_density(density: str) -> List[Dict[str, Any]]:
    """Get all facial hair styles matching a density classification."""
    styles = get_all_styles("facial_hair")
    return [s for s in styles if classify_facial_hair_density(s.get("description", "")) == density]


# Pre-computed index lookups for fast access during matching

def build_hair_index_by_attributes() -> Dict[str, Dict[str, List[int]]]:
    """
    Build an index of hair styles organized by attributes.
    
    Returns:
        {
            'length': {'bald': [0, 39, ...], 'short': [...], ...},
            'texture': {'afro': [...], 'dreads': [...], ...},
            'volume': {'none': [...], 'high': [...], ...}
        }
    """
    styles = get_all_styles("hair")
    
    index = {
        "length": {},
        "texture": {},
        "volume": {},
    }
    
    for style in styles:
        idx = style.get("index")
        desc = style.get("description", "")
        
        length = classify_hair_length(desc)
        texture = classify_hair_texture(desc)
        volume = classify_hair_volume(desc)
        
        index["length"].setdefault(length, []).append(idx)
        index["texture"].setdefault(texture, []).append(idx)
        index["volume"].setdefault(volume, []).append(idx)
    
    return index


def build_facial_hair_index_by_density() -> Dict[str, List[int]]:
    """
    Build an index of facial hair styles organized by density.
    
    Returns:
        {'none': [0, 16], 'stubble': [1, 4, 6, ...], ...}
    """
    styles = get_all_styles("facial_hair")
    
    index = {}
    for style in styles:
        idx = style.get("index")
        desc = style.get("description", "")
        density = classify_facial_hair_density(desc)
        index.setdefault(density, []).append(idx)
    
    return index

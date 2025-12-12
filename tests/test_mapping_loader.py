
import pytest
from hoopland.cv import mapping_loader

def test_load_appearance_mapping():
    """Test that the mapping file loads and returns a dictionary."""
    mapping = mapping_loader.load_appearance_mapping()
    assert isinstance(mapping, dict)
    assert "mappings" in mapping
    assert "accessories" in mapping["mappings"]
    assert "facial_hair" in mapping["mappings"]
    assert "hair" in mapping["mappings"]

def test_get_all_styles():
    """Test retrieving all styles for a category."""
    hair_styles = mapping_loader.get_all_styles("hair")
    assert isinstance(hair_styles, list)
    assert len(hair_styles) > 0
    # Check structure of a style item
    first_style = hair_styles[0]
    assert "index" in first_style
    assert "description" in first_style

def test_get_style_by_index():
    """Test retrieving a specific style."""
    # Assuming index 0 always exists for hair
    style = mapping_loader.get_style_by_index("hair", 0)
    assert style is not None
    assert style["index"] == 0
    
    # Test non-existent index
    style = mapping_loader.get_style_by_index("hair", 9999)
    assert style is None

def test_search_styles():
    """Test searching for styles by keyword."""
    # "Bald" should definitely be in hair descriptions
    matches = mapping_loader.search_styles("hair", ["bald"])
    assert len(matches) > 0
    for m in matches:
        assert "bald" in m["description"].lower()

def test_style_classification():
    """Test the helper classification functions."""
    assert mapping_loader.classify_hair_length("Bald/Shaved Head") == "bald"
    assert mapping_loader.classify_hair_volume("Large Afro") == "high"
    assert mapping_loader.classify_facial_hair_density("Clean Shaven") == "none"

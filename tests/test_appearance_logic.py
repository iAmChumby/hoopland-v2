import pytest
import sys
import os

# Ensure src is importable (conftest should handle this usually via pythonpath in pyproject.toml,
# but explicit import here for clarity matches original script intent)
from hoopland.cv import appearance


def test_match_asset_colors():
    """
    Test valid color matching for hair assets.
    """
    # Ideally we mock load_assets, but if it loads static JSON/local files it might be fast enough.
    appearance.load_assets()

    # Test Black Hair (R=0, G=0, B=0)
    idx_black = appearance.match_asset("hair", (0, 0, 0))
    # Asserting it returns an integer index
    assert isinstance(idx_black, int)

    # Test Blonde Hair (R=240, G=240, B=100)
    idx_blonde = appearance.match_asset("hair", (240, 240, 100))
    assert isinstance(idx_blonde, int)

    # Test Brown Hair (R=100, G=50, B=0)
    idx_brown = appearance.match_asset("hair", (100, 50, 0))
    assert isinstance(idx_brown, int)


@pytest.mark.integration
def test_url_analysis_integration():
    """
    Test fetching and analyzing a real image URL.
    Marked as integration because it hits the network.
    """
    # A.J. Guyton (2062)
    url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2062.png"

    try:
        res = appearance.analyze_player_appearance(url)
        assert isinstance(res, dict)
        assert "skin_tone" in res or "hair_color" in res  # Depending on what it returns
    except Exception as e:
        pytest.fail(f"Analysis failed: {e}")

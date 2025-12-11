import sys
import os
import logging

# Setup path to import src
sys.path.append(os.getcwd())

from src.hoopland.cv import appearance

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_matching():
    print("Testing Asset Matching...")
    appearance.load_assets()
    
    # Test Black Hair (R=0, G=0, B=0)
    idx_black = appearance.match_asset("hair", (0, 0, 0))
    print(f"Match for Black (0,0,0): {idx_black}")
    
    # Test Blonde Hair (R=240, G=240, B=100)
    idx_blonde = appearance.match_asset("hair", (240, 240, 100))
    print(f"Match for Blonde (240,240,100): {idx_blonde}")
    
    # Test Brown Hair (R=100, G=50, B=0)
    idx_brown = appearance.match_asset("hair", (100, 50, 0))
    print(f"Match for Brown (100,50,0): {idx_brown}")

def test_url_analysis():
    # A.J. Guyton (2062)
    url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2062.png"
    print(f"\nAnalyzing URL: {url}")
    res = appearance.analyze_player_appearance(url)
    print(f"Result: {res}")

if __name__ == "__main__":
    test_matching()
    test_url_analysis()

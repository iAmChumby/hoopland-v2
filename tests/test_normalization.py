"""
Unit tests for the stats/normalization module.
Tests attribute calculation from raw stats.
"""

from hoopland.stats.normalization import StatsConverter, calculate_overall_rating


def test_lebron_2015_ratings():
    """Test LeBron 2014-15 Stats produce expected ratings."""
    stats = {
        "GP": 69,
        "PTS": 1743, "REB": 416, "AST": 511, "STL": 109, "BLK": 49,
        "FGM": 624, "FGA": 1279,
        "FG3M": 120, "FG3A": 339,
        "FTM": 375, "FTA": 528,
        "FG_PCT": 0.488, "FG3_PCT": 0.354, "FT_PCT": 0.710
    }

    ratings = StatsConverter.calculate_ratings(stats)
    print("\nLeBron 2015 Ratings:")
    for k, v in ratings.items():
        print(f"{k}: {v}")

    # Check structure - should have 15 keys with [current, potential] arrays
    assert len(ratings) == 15
    assert "INS" in ratings
    assert "TPT" in ratings
    assert "PAS" in ratings

    # Check format - each should be [current, potential]
    assert isinstance(ratings["INS"], list)
    assert len(ratings["INS"]) == 2

    # Check values - Inside scoring high (high volume, good efficiency)
    assert ratings["INS"][0] >= 7  # Current inside scoring

    # Passing high (7.4 assists)
    assert ratings["PAS"][0] >= 7


def test_curry_2016_ratings():
    """Test Curry 2015-16 Unanimous MVP Stats."""
    stats = {
        "GP": 79,
        "PTS": 2375, "REB": 430, "AST": 527, "STL": 169, "BLK": 15,
        "FGM": 805, "FGA": 1598,
        "FG3M": 402, "FG3A": 886,
        "FTM": 363, "FTA": 400,
        "FG_PCT": 0.504, "FG3_PCT": 0.454, "FT_PCT": 0.908
    }

    ratings = StatsConverter.calculate_ratings(stats)
    print("\nCurry 2016 Ratings:")
    for k, v in ratings.items():
        print(f"{k}: {v}")

    # 3pt: 402 makes is insane volume. 45% is insane efficiency. MUST be 10.
    assert ratings["TPT"][0] == 10

    # Free throws 90.8% should be high
    assert ratings["FTS"][0] >= 8


def test_all_15_attributes_present():
    """Verify all 15 target attributes are returned."""
    stats = {"GP": 50, "PTS": 500, "AST": 200, "REB": 300}
    ratings = StatsConverter.calculate_ratings(stats)

    expected_keys = ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                     "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                     "STR", "SPD", "STM"]

    for key in expected_keys:
        assert key in ratings, f"Missing attribute: {key}"
        assert isinstance(ratings[key], list), f"{key} should be a list"
        assert len(ratings[key]) == 2, f"{key} should have [current, potential]"


def test_calculate_overall_rating():
    """Test overall rating calculation."""
    # High skill player
    high_attrs = {k: [8, 9] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                       "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                       "STR", "SPD", "STM"]}
    rating = calculate_overall_rating(high_attrs)
    assert 7.5 <= rating <= 8.5

    # Low skill player
    low_attrs = {k: [3, 5] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                      "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                      "STR", "SPD", "STM"]}
    rating = calculate_overall_rating(low_attrs)
    assert 2.5 <= rating <= 3.5


def test_legacy_ratings():
    """Test legacy 6-attribute format for backward compatibility."""
    stats = {"GP": 50, "PTS": 500, "AST": 200, "REB": 300,
             "FG_PCT": 0.45, "FT_PCT": 0.80}
    
    ratings = StatsConverter.calculate_legacy_ratings(stats)
    
    assert "shooting_inside" in ratings
    assert "shooting_mid" in ratings
    assert "shooting_3pt" in ratings
    assert "defense" in ratings
    assert "rebounding" in ratings
    assert "passing" in ratings
    
    # Check they're integers, not arrays
    assert isinstance(ratings["shooting_inside"], int)


if __name__ == "__main__":
    test_lebron_2015_ratings()
    test_curry_2016_ratings()
    test_all_15_attributes_present()
    test_calculate_overall_rating()
    test_legacy_ratings()

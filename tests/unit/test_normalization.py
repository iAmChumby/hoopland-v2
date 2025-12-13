"""
Unit tests for the stats normalization module.
Tests rating calculations and stat conversions for the 15-attribute target schema.
"""

import pytest
from hoopland.stats.normalization import normalize_rating, StatsConverter, calculate_overall_rating


class TestNormalizeRating:
    """Tests for the normalize_rating function."""

    def test_normalize_rating_mid_range(self):
        """Test normalization of a mid-range value."""
        result = normalize_rating(17.5, 0, 35)
        assert result == 5

    def test_normalize_rating_min_value(self):
        """Test normalization of minimum value."""
        result = normalize_rating(0, 0, 35)
        assert result == 1

    def test_normalize_rating_max_value(self):
        """Test normalization of maximum value."""
        result = normalize_rating(35, 0, 35)
        assert result == 10

    def test_normalize_rating_below_min(self):
        """Test that values below min are clipped."""
        result = normalize_rating(-5, 0, 35)
        assert result == 1

    def test_normalize_rating_above_max(self):
        """Test that values above max are clipped."""
        result = normalize_rating(50, 0, 35)
        assert result == 10

    def test_normalize_rating_none_value(self):
        """Test that None returns 1."""
        result = normalize_rating(None, 0, 35)
        assert result == 1

    def test_normalize_rating_equal_min_max(self):
        """Test when min equals max returns default."""
        result = normalize_rating(5, 5, 5)
        assert result == 5

    def test_normalize_rating_percentage(self):
        """Test normalization of percentage values."""
        result = normalize_rating(0.45, 0.3, 0.6)
        assert result == 5

    def test_normalize_rating_high_percentage(self):
        """Test high percentage normalization."""
        result = normalize_rating(0.58, 0.3, 0.6)
        assert result >= 9


class TestStatsConverter:
    """Tests for the StatsConverter class with 15-attribute target schema."""

    def test_calculate_ratings_returns_15_attributes(self):
        """Test that calculate_ratings returns all 15 target attributes."""
        stats = {
            "GP": 82,
            "PTS": 2000,
            "REB": 500,
            "AST": 400,
            "STL": 120,
            "BLK": 60,
            "FG_PCT": 0.50,
            "FG3_PCT": 0.38,
            "FT_PCT": 0.85
        }

        ratings = StatsConverter.calculate_ratings(stats)

        # Should return 15 attributes
        expected_keys = ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                         "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                         "STR", "SPD", "STM"]
        for key in expected_keys:
            assert key in ratings, f"Missing attribute: {key}"

    def test_calculate_ratings_array_format(self):
        """Test that each attribute is [current, potential] array."""
        stats = {"GP": 50, "PTS": 500}

        ratings = StatsConverter.calculate_ratings(stats)

        for key, value in ratings.items():
            assert isinstance(value, list), f"{key} should be a list"
            assert len(value) == 2, f"{key} should have [current, potential]"
            assert isinstance(value[0], int), f"{key}[0] should be int"
            assert isinstance(value[1], int), f"{key}[1] should be int"

    def test_calculate_ratings_values_in_range(self):
        """Test rating values are in valid 1-10 range."""
        stats = {
            "GP": 0,
            "PTS": 25.0,
            "REB": 7.0,
            "AST": 5.0,
            "STL": 1.5,
            "BLK": 0.5,
            "FG_PCT": 0.48,
            "FG3_PCT": 0.40,
            "FT_PCT": 0.88
        }

        ratings = StatsConverter.calculate_ratings(stats)

        for key, value in ratings.items():
            assert 1 <= value[0] <= 10, f"{key} current rating {value[0]} out of range"
            assert 1 <= value[1] <= 10, f"{key} potential rating {value[1]} out of range"

    def test_calculate_ratings_empty_stats(self):
        """Test rating calculation with empty stats."""
        stats = {}
        ratings = StatsConverter.calculate_ratings(stats)

        assert len(ratings) == 15

    def test_calculate_ratings_star_player(self):
        """Test ratings for a star player."""
        stats = {
            "GP": 70,
            "PTS": 2100,
            "REB": 700,
            "AST": 350,
            "STL": 100,
            "BLK": 70,
            "FG_PCT": 0.55,
            "FG3_PCT": 0.42,
            "FT_PCT": 0.90
        }

        ratings = StatsConverter.calculate_ratings(stats)

        # Star player should have high rebounding
        assert ratings["DRE"][0] >= 6
        # High inside scoring
        assert ratings["INS"][0] >= 6

    def test_calculate_ratings_defensive_player(self):
        """Test ratings for a defensive specialist."""
        stats = {
            "GP": 82,
            "PTS": 600,
            "REB": 300,
            "AST": 150,
            "STL": 180,
            "BLK": 80,
            "FG_PCT": 0.45,
            "FG3_PCT": 0.33
        }

        ratings = StatsConverter.calculate_ratings(stats)

        # Should have high steal rating
        assert ratings["STL"][0] >= 5

    def test_inside_scoring_calculation(self):
        """Test inside scoring calculation."""
        stats = {"FG_PCT": 0.55, "FGM": 8.0}
        rating = StatsConverter._calc_inside_scoring(stats)
        assert rating >= 7

    def test_mid_range_calculation(self):
        """Test mid-range shooting calculation."""
        stats = {"FG_PCT": 0.45}
        rating = StatsConverter._calc_mid_range(stats)
        assert 4 <= rating <= 6

    def test_ranges_defined(self):
        """Test that all required ranges are defined."""
        required_ranges = ["pts", "reb", "ast", "stl", "blk", "fg_pct", "fg3_pct", "ft_pct"]
        for key in required_ranges:
            assert key in StatsConverter.RANGES
            min_val, max_val = StatsConverter.RANGES[key]
            assert min_val < max_val

    def test_legacy_ratings_format(self):
        """Test legacy 6-attribute format for backward compatibility."""
        stats = {"GP": 50, "PTS": 500, "AST": 200, "REB": 300, "FG_PCT": 0.45}

        ratings = StatsConverter.calculate_legacy_ratings(stats)

        # Should have 6 attributes
        assert "shooting_inside" in ratings
        assert "shooting_mid" in ratings
        assert "shooting_3pt" in ratings
        assert "defense" in ratings
        assert "rebounding" in ratings
        assert "passing" in ratings

        # Should be single int values, not arrays
        assert isinstance(ratings["shooting_inside"], int)


class TestCalculateOverallRating:
    """Tests for overall rating calculation."""

    def test_high_skill_player(self):
        """Test overall rating for high skill player."""
        attrs = {k: [8, 9] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                      "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                      "STR", "SPD", "STM"]}
        rating = calculate_overall_rating(attrs)
        assert 7.5 <= rating <= 8.5

    def test_low_skill_player(self):
        """Test overall rating for low skill player."""
        attrs = {k: [3, 5] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                      "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                      "STR", "SPD", "STM"]}
        rating = calculate_overall_rating(attrs)
        assert 2.5 <= rating <= 3.5

    def test_empty_attributes(self):
        """Test overall rating with empty attributes."""
        rating = calculate_overall_rating({})
        assert rating == 0.0

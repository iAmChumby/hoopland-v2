"""
Unit tests for the stats normalization module.
Tests rating calculations and stat conversions.
"""

import pytest
from hoopland.stats.normalization import normalize_rating, StatsConverter


class TestNormalizeRating:
    """Tests for the normalize_rating function."""

    def test_normalize_rating_mid_range(self):
        """Test normalization of a mid-range value."""
        # Value of 17.5 in range 0-35 should be ~5
        result = normalize_rating(17.5, 0, 35)
        assert result == 5

    def test_normalize_rating_min_value(self):
        """Test normalization of minimum value."""
        result = normalize_rating(0, 0, 35)
        assert result == 1  # Minimum rating is 1

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
        # 45% FG in range 30%-60% should be ~5
        result = normalize_rating(0.45, 0.3, 0.6)
        assert result == 5

    def test_normalize_rating_high_percentage(self):
        """Test high percentage normalization."""
        result = normalize_rating(0.58, 0.3, 0.6)
        assert result >= 9


class TestStatsConverter:
    """Tests for the StatsConverter class."""

    def test_calculate_ratings_with_totals(self):
        """Test rating calculation with total stats."""
        stats = {
            "GP": 82,
            "PTS": 2000,  # 24.4 PPG
            "REB": 500,   # 6.1 RPG
            "AST": 400,   # 4.9 APG
            "STL": 120,   # 1.5 SPG
            "BLK": 60,    # 0.7 BPG
            "FG_PCT": 0.50,
            "FG3_PCT": 0.38,
            "FT_PCT": 0.85
        }
        
        ratings = StatsConverter.calculate_ratings(stats)
        
        assert "shooting_inside" in ratings
        assert "shooting_mid" in ratings
        assert "shooting_3pt" in ratings
        assert "defense" in ratings
        assert "rebounding" in ratings
        assert "passing" in ratings

    def test_calculate_ratings_per_game(self):
        """Test rating calculation with per-game stats."""
        stats = {
            "GP": 0,  # Indicates already per-game
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
        
        # All ratings should be in valid range
        for key, value in ratings.items():
            assert 1 <= value <= 10, f"{key} rating {value} out of range"

    def test_calculate_ratings_empty_stats(self):
        """Test rating calculation with empty stats."""
        stats = {}
        ratings = StatsConverter.calculate_ratings(stats)
        
        # Should return default ratings
        assert len(ratings) == 6
        for value in ratings.values():
            assert 1 <= value <= 10

    def test_calculate_ratings_star_player(self):
        """Test ratings for a star player."""
        stats = {
            "GP": 70,
            "PTS": 2100,  # 30 PPG
            "REB": 700,   # 10 RPG
            "AST": 350,   # 5 APG
            "STL": 100,   # 1.4 SPG
            "BLK": 70,    # 1 BPG
            "FG_PCT": 0.55,
            "FG3_PCT": 0.42,
            "FT_PCT": 0.90
        }
        
        ratings = StatsConverter.calculate_ratings(stats)
        
        # Star player should have high ratings
        assert ratings["rebounding"] >= 6
        assert ratings["shooting_inside"] >= 6

    def test_calculate_ratings_defensive_player(self):
        """Test ratings for a defensive specialist."""
        stats = {
            "GP": 82,
            "PTS": 600,   # 7.3 PPG
            "REB": 300,   # 3.7 RPG
            "AST": 150,   # 1.8 APG
            "STL": 180,   # 2.2 SPG
            "BLK": 80,    # 1.0 BPG
            "FG_PCT": 0.45,
            "FG3_PCT": 0.33
        }
        
        ratings = StatsConverter.calculate_ratings(stats)
        
        # Should have higher defense rating
        assert ratings["defense"] >= 5

    def test_shooting_inside_calculation(self):
        """Test inside shooting calculation."""
        stats = {"FG_PCT": 0.55}  # High FG%
        rating = StatsConverter._calc_shooting_inside(stats)
        assert rating >= 7

    def test_shooting_mid_calculation(self):
        """Test mid-range shooting calculation."""
        stats = {"FG_PCT": 0.45}  # Average FG%
        rating = StatsConverter._calc_shooting_mid(stats)
        assert 4 <= rating <= 6

    def test_ranges_defined(self):
        """Test that all required ranges are defined."""
        required_ranges = ["pts", "reb", "ast", "stl", "blk", "fg_pct", "fg3_pct", "ft_pct"]
        for key in required_ranges:
            assert key in StatsConverter.RANGES
            min_val, max_val = StatsConverter.RANGES[key]
            assert min_val < max_val

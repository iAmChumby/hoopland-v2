"""
Unit tests for the stats normalization module.
Tests rating calculations and stat conversions for the 15-attribute target schema.
"""

import pytest
from hoopland.stats.normalization import (
    normalize_rating,
    StatsConverter,
    calculate_overall_rating,
    apply_nba_floor,
    calculate_potential_bonus,
)


class TestNormalizeRating:
    """Tests for the normalize_rating function."""

    def test_normalize_rating_mid_range(self):
        """Test normalization of a mid-range value."""
        result = normalize_rating(17.5, 0, 35)
        assert 11 <= result <= 13  # Mid-range on 1-20 scale with power curve

    def test_normalize_rating_min_value(self):
        """Test normalization of minimum value."""
        result = normalize_rating(0, 0, 35)
        assert result == 1

    def test_normalize_rating_max_value(self):
        """Test normalization of maximum value."""
        result = normalize_rating(35, 0, 35)
        assert result == 20  # Max on 1-20 scale

    def test_normalize_rating_below_min(self):
        """Test that values below min are clipped."""
        result = normalize_rating(-5, 0, 35)
        assert result == 1

    def test_normalize_rating_above_max(self):
        """Test that values above max are clipped."""
        result = normalize_rating(50, 0, 35)
        assert result == 20  # Clipped to max on 1-20 scale

    def test_normalize_rating_none_value(self):
        """Test that None returns 1."""
        result = normalize_rating(None, 0, 35)
        assert result == 1

    def test_normalize_rating_equal_min_max(self):
        """Test when min equals max returns default."""
        result = normalize_rating(5, 5, 5)
        assert result == 10  # Returns scale // 2 = 10 on 1-20 scale

    def test_normalize_rating_percentage(self):
        """Test normalization of percentage values."""
        result = normalize_rating(0.45, 0.3, 0.6)
        assert 11 <= result <= 13  # Mid-range on 1-20 scale with power curve

    def test_normalize_rating_high_percentage(self):
        """Test high percentage normalization."""
        result = normalize_rating(0.58, 0.3, 0.6)
        assert result >= 18  # High value on 1-20 scale

    def test_normalize_rating_power_curve_rewards_elite(self):
        """Elite values (95th percentile) should map to 18-20."""
        result = normalize_rating(27, 0, 28, power=0.7)
        assert result >= 18, f"Elite performance should get 18+, got {result}"
    
    def test_normalize_rating_power_curve_maintains_middle(self):
        """Middle values should still be in 12-15 range."""
        result = normalize_rating(14, 0, 28, power=0.7)
        assert 12 <= result <= 16, f"Middle should be 12-16, got {result}"
    
    def test_normalize_rating_power_curve_vs_linear(self):
        """Power curve should give higher ratings at high end than linear."""
        linear_result = normalize_rating(20, 0, 28, power=1.0)
        power_result = normalize_rating(20, 0, 28, power=0.7)
        assert power_result > linear_result, "Power curve should boost middle-high stats"


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
        """Test rating values are in valid 1-20 range."""
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
            assert 1 <= value[0] <= 20, f"{key} current rating {value[0]} out of range"
            assert 1 <= value[1] <= 20, f"{key} potential rating {value[1]} out of range"

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
        assert rating >= 14  # High on 1-20 scale

    def test_mid_range_calculation(self):
        """Test mid-range shooting calculation."""
        stats = {"FG_PCT": 0.45}
        rating = StatsConverter._calc_mid_range(stats)
        assert 5 <= rating <= 10  # Mid-range on 1-20 scale (45% is average)

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
        # Attributes on 1-20 scale, rating output on 0-10
        attrs = {k: [16, 18] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                      "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                      "STR", "SPD", "STM"]}
        rating = calculate_overall_rating(attrs)
        assert 7.5 <= rating <= 8.5

    def test_low_skill_player(self):
        """Test overall rating for low skill player."""
        # Attributes on 1-20 scale, rating output on 0-10
        attrs = {k: [6, 10] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                      "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                      "STR", "SPD", "STM"]}
        rating = calculate_overall_rating(attrs)
        assert 2.5 <= rating <= 3.5

    def test_empty_attributes(self):
        """Test overall rating with empty attributes."""
        rating = calculate_overall_rating({})
        assert rating == 0.0


from hoopland.stats.normalization import (
    percentile_to_rating,
    calculate_league_ratings,
    calculate_minutes_bonus,
)


class TestPercentileToRating:
    """Tests for percentile-to-rating mapping function."""

    def test_mvp_tier(self):
        """Top 1% should get rating 10."""
        assert percentile_to_rating(99.5) == 10.0
        assert percentile_to_rating(100.0) == 10.0

    def test_all_star_tier(self):
        """95-99% should get rating 9.x."""
        rating = percentile_to_rating(97)
        assert 9.0 <= rating < 10.0

    def test_solid_starter_tier(self):
        """80-95% should get rating 8.x."""
        rating = percentile_to_rating(88)
        assert 8.0 <= rating < 9.0

    def test_rotation_tier(self):
        """50-80% should get rating 7.x."""
        rating = percentile_to_rating(65)
        assert 7.0 <= rating < 8.0

    def test_bench_tier(self):
        """0-50% should get rating 6.x."""
        rating = percentile_to_rating(25)
        assert 6.0 <= rating < 7.0

    def test_minimum_percentile(self):
        """0th percentile should get rating 6.0 (3 star floor)."""
        rating = percentile_to_rating(0)
        assert rating == 6.0

    def test_tier_boundaries(self):
        """Test exact tier boundaries."""
        assert percentile_to_rating(99) == 10.0
        assert percentile_to_rating(95) >= 9.0
        assert percentile_to_rating(80) >= 8.0
        assert percentile_to_rating(50) >= 7.0
        assert percentile_to_rating(0) >= 6.0


class TestCalculateMinutesBonus:
    """Tests for minutes-based bonus calculation."""

    def test_no_games_played(self):
        """Player with no games should get 0 bonus."""
        stats = {"GP": 0, "MIN": 0}
        assert calculate_minutes_bonus(stats) == 0.0

    def test_low_minutes_no_bonus(self):
        """Player with <15 mpg should get 0 bonus."""
        stats = {"GP": 50, "MIN": 500}
        assert calculate_minutes_bonus(stats) == 0.0

    def test_moderate_minutes_bonus(self):
        """Player with 25 mpg should get moderate bonus."""
        stats = {"GP": 50, "MIN": 1250}
        bonus = calculate_minutes_bonus(stats)
        assert 0.3 <= bonus <= 0.5

    def test_high_minutes_bonus(self):
        """Player with 35 mpg should get high bonus."""
        stats = {"GP": 50, "MIN": 1750}
        bonus = calculate_minutes_bonus(stats)
        assert 0.7 <= bonus <= 1.0

    def test_max_bonus_cap(self):
        """Bonus should be capped at 1.0."""
        stats = {"GP": 50, "MIN": 2500}
        bonus = calculate_minutes_bonus(stats)
        assert bonus <= 1.0


class TestCalculateLeagueRatings:
    """Tests for league-wide percentile-based ratings."""

    def test_empty_list(self):
        """Empty list should return empty list."""
        assert calculate_league_ratings([]) == []

    def test_single_player(self):
        """Single player should get middle rating."""
        attrs = {k: [10, 12] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                       "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                       "STR", "SPD", "STM"]}
        ratings = calculate_league_ratings([attrs])
        assert len(ratings) == 1
        assert ratings[0] == 7.0

    def test_rating_range(self):
        """All ratings should be in 6.0-10.0 range (3-5 star floor)."""
        attrs_list = []
        for base in range(5, 16):
            attrs = {k: [base, base + 2] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                                   "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                                   "STR", "SPD", "STM"]}
            attrs_list.append(attrs)

        ratings = calculate_league_ratings(attrs_list)

        for r in ratings:
            assert 6.0 <= r <= 10.0

    def test_ordering_preserved(self):
        """Higher base ratings should result in higher final ratings."""
        low_attrs = {k: [5, 7] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                         "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                         "STR", "SPD", "STM"]}
        mid_attrs = {k: [10, 12] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                           "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                           "STR", "SPD", "STM"]}
        high_attrs = {k: [18, 20] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                            "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                            "STR", "SPD", "STM"]}

        ratings = calculate_league_ratings([low_attrs, mid_attrs, high_attrs])

        assert ratings[0] < ratings[1] < ratings[2]

    def test_distribution_spread(self):
        """League of players should have spread distribution."""
        attrs_list = []
        for i in range(100):
            base = 5 + (i % 15)
            attrs = {k: [base, base + 2] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                                   "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                                   "STR", "SPD", "STM"]}
            attrs_list.append(attrs)

        ratings = calculate_league_ratings(attrs_list)

        assert min(ratings) >= 6.0
        assert max(ratings) >= 9.5

        import statistics
        std_dev = statistics.stdev(ratings)
        assert std_dev >= 0.8

    def test_original_order_maintained(self):
        """Ratings should be returned in same order as input."""
        attrs_list = []
        for base in [15, 5, 10, 20, 8]:
            attrs = {k: [base, base + 2] for k in ["LAY", "DNK", "INS", "MID", "TPT", "FTS",
                                                   "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                                                   "STR", "SPD", "STM"]}
            attrs_list.append(attrs)

        ratings = calculate_league_ratings(attrs_list)

        assert len(ratings) == 5
        assert ratings[3] == max(ratings)
        assert ratings[1] == min(ratings)


class TestApplyNBAFloor:
    """Tests for NBA attribute floor enforcement."""

    def test_physical_attribute_floor(self):
        """Physical attributes (STR, SPD, STM) should have floor of 10."""
        assert apply_nba_floor(5, "STR") == 10
        assert apply_nba_floor(8, "SPD") == 10
        assert apply_nba_floor(1, "STM") == 10

    def test_physical_attribute_above_floor(self):
        """Physical attributes above floor should be unchanged."""
        assert apply_nba_floor(15, "STR") == 15
        assert apply_nba_floor(18, "SPD") == 18
        assert apply_nba_floor(12, "STM") == 12

    def test_core_skill_floor(self):
        """Core skills (LAY, INS, DRB, PAS, ORE, DRE) should have floor of 8."""
        assert apply_nba_floor(3, "LAY") == 8
        assert apply_nba_floor(5, "INS") == 8
        assert apply_nba_floor(1, "DRB") == 8
        assert apply_nba_floor(6, "PAS") == 8
        assert apply_nba_floor(4, "ORE") == 8
        assert apply_nba_floor(2, "DRE") == 8

    def test_core_skill_above_floor(self):
        """Core skills above floor should be unchanged."""
        assert apply_nba_floor(12, "LAY") == 12
        assert apply_nba_floor(15, "INS") == 15
        assert apply_nba_floor(10, "DRB") == 10

    def test_specialty_skill_floor(self):
        """Specialty skills (TPT, FTS, MID, STL, BLK, DNK) should have floor of 6."""
        assert apply_nba_floor(1, "TPT") == 6
        assert apply_nba_floor(3, "FTS") == 6
        assert apply_nba_floor(2, "MID") == 6
        assert apply_nba_floor(4, "STL") == 6
        assert apply_nba_floor(1, "BLK") == 6
        assert apply_nba_floor(5, "DNK") == 6

    def test_specialty_skill_above_floor(self):
        """Specialty skills above floor should be unchanged."""
        assert apply_nba_floor(10, "TPT") == 10
        assert apply_nba_floor(15, "FTS") == 15
        assert apply_nba_floor(8, "MID") == 8


class TestCalculatePotentialBonus:
    """Tests for age-based potential bonus calculation."""

    def test_young_player_bonus(self):
        """Young players (age <= 22) should get +8 bonus."""
        assert calculate_potential_bonus(19) == 8
        assert calculate_potential_bonus(20) == 8
        assert calculate_potential_bonus(22) == 8

    def test_entering_prime_bonus(self):
        """Players 23-26 should get +5 bonus."""
        assert calculate_potential_bonus(23) == 5
        assert calculate_potential_bonus(25) == 5
        assert calculate_potential_bonus(26) == 5

    def test_prime_years_bonus(self):
        """Players 27-29 should get +2 bonus."""
        assert calculate_potential_bonus(27) == 2
        assert calculate_potential_bonus(28) == 2
        assert calculate_potential_bonus(29) == 2

    def test_veteran_bonus(self):
        """Veterans 30-34 should get +1 bonus."""
        assert calculate_potential_bonus(30) == 1
        assert calculate_potential_bonus(32) == 1
        assert calculate_potential_bonus(34) == 1

    def test_older_player_no_penalty(self):
        """Older players (35+) should get +0 bonus (no penalty)."""
        assert calculate_potential_bonus(35) == 0
        assert calculate_potential_bonus(38) == 0
        assert calculate_potential_bonus(40) == 0


class TestCalculateRatingsWithAge:
    """Tests for calculate_ratings with age parameter."""

    def test_young_player_gets_high_potential(self):
        """Young player (age 20) should have high potential relative to current."""
        stats = {"GP": 5, "PTS": 0, "REB": 10, "AST": 5}
        ratings = StatsConverter.calculate_ratings(stats, age=20)

        # All attributes should have potential = min(20, current + 8)
        for key, value in ratings.items():
            current, potential = value
            expected_potential = min(20, current + 8)
            assert potential == expected_potential, f"{key}: potential {potential} != expected {expected_potential}"
            assert potential <= 20, f"{key}: potential {potential} exceeds max 20"

    def test_veteran_player_at_ceiling(self):
        """Veteran player (age 35) should have potential = current."""
        stats = {"GP": 70, "PTS": 1500, "REB": 600, "AST": 300}
        ratings = StatsConverter.calculate_ratings(stats, age=35)

        # Veterans at ceiling should have potential = current
        for key, value in ratings.items():
            current, potential = value
            assert potential == current, f"{key}: veteran should be at ceiling"

    def test_nba_floors_applied(self):
        """Even with terrible stats, NBA floors should be applied."""
        stats = {"GP": 2, "PTS": 0, "REB": 0, "AST": 0}
        ratings = StatsConverter.calculate_ratings(stats, age=25)

        # Physical attributes should be >= 10
        assert ratings["STR"][0] >= 10
        assert ratings["SPD"][0] >= 10
        assert ratings["STM"][0] >= 10

        # Core skills should be >= 8
        assert ratings["LAY"][0] >= 8
        assert ratings["INS"][0] >= 8
        assert ratings["DRB"][0] >= 8
        assert ratings["PAS"][0] >= 8
        assert ratings["ORE"][0] >= 8
        assert ratings["DRE"][0] >= 8

        # Specialty skills should be >= 6
        assert ratings["TPT"][0] >= 6
        assert ratings["FTS"][0] >= 6
        assert ratings["MID"][0] >= 6
        assert ratings["STL"][0] >= 6
        assert ratings["BLK"][0] >= 6
        assert ratings["DNK"][0] >= 6

    def test_all_values_within_bounds(self):
        """All attribute values should be 1-20."""
        stats = {"GP": 82, "PTS": 2500, "REB": 800, "AST": 700}
        ratings = StatsConverter.calculate_ratings(stats, age=22)

        for key, value in ratings.items():
            current, potential = value
            assert 1 <= current <= 20, f"{key} current {current} out of bounds"
            assert 1 <= potential <= 20, f"{key} potential {potential} out of bounds"

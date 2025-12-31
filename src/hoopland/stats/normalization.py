"""
Stats normalization and attribute calculation for Hoopland.

Converts raw player statistics into game-ready attributes matching
the target schema format (15 attributes with [current, potential] arrays).
"""

import math
from typing import Dict, List, Any


def ceil_to_half(value: float) -> float:
    """
    Round a value UP to the next half-star increment (0.5).
    
    Examples:
        7.1 -> 7.5
        7.5 -> 7.5 (already on half-star)
        7.6 -> 8.0
        8.0 -> 8.0 (already on half-star)
    
    Args:
        value: The value to round up
        
    Returns:
        Value rounded up to nearest 0.5
    """
    return math.ceil(value * 2) / 2


def normalize_rating(value, min_val, max_val, scale: int = 20, power: float = 0.7) -> int:
    """
    Normalize a value to a 1-20 rating scale with steeper curve for elite performers.
    
    Uses a power curve (exponent < 1.0) to reward high-end performance.
    This makes elite stats (95th+ percentile) map to 18-20 while maintaining
    differentiation across the spectrum.
    
    Args:
        value: The raw stat value
        min_val: Minimum expected value for this stat
        max_val: Maximum expected value for this stat  
        scale: Output scale (default 20 to match game)
        power: Exponent for power curve (< 1.0 = steeper at top, default 0.7)
    """
    if value is None:
        return 1

    val = max(min_val, min(value, max_val))

    if max_val == min_val:
        return scale // 2

    # Power curve: compress low end, stretch high end
    normalized = (val - min_val) / (max_val - min_val)
    powered = normalized ** power
    rating = powered * scale
    
    return max(1, min(scale, int(round(rating))))


def apply_nba_floor(value: int, attribute_type: str) -> int:
    """
    Apply NBA minimum floors - these are professional players.
    
    Target: Struggling bench (0 stats) = 2.0-2.5 stars (8-10 avg attributes).
    Actual stats naturally push players higher from there.
    """
    if attribute_type in ["STR", "SPD", "STM"]:
        return max(10, value)
    elif attribute_type in ["LAY", "INS", "DRB", "PAS", "ORE", "DRE"]:
        return max(8, value)
    else:
        return max(6, value)


def calculate_potential_bonus(age: int) -> int:
    """
    Calculate potential bonus based on age.
    Young players have room to grow, veterans are at their ceiling.
    No age penalties - ceiling never artificially lowered.
    """
    if age <= 22:
        return 8
    elif age <= 26:
        return 5
    elif age <= 29:
        return 2
    elif age <= 34:
        return 1
    else:
        return 0


class StatsConverter:
    """
    Converts raw NBA/NCAA statistics to Hoop Land attribute ratings.

    Target attributes (15):
    - LAY: Layup ability
    - DNK: Dunk ability  
    - INS: Inside scoring
    - MID: Mid-range shooting
    - TPT: Three-point shooting
    - FTS: Free throw shooting
    - DRB: Dribbling
    - PAS: Passing
    - ORE: Offensive rebounding
    - DRE: Defensive rebounding
    - STL: Steals
    - BLK: Blocks
    - STR: Strength
    - SPD: Speed
    - STM: Stamina
    """

    RANGES = {
        "pts": (0, 28),
        "reb": (0, 12.0),
        "oreb": (0, 4.0),
        "dreb": (0, 10.0),
        "ast": (0, 10.0),
        "stl": (0, 2.2),
        "blk": (0, 2.5),
        "fg_pct": (0.35, 0.60),
        "fg3_pct": (0.28, 0.42),
        "ft_pct": (0.5, 0.92),
        "fgm": (0, 10.0),
        "fg3m": (0, 3.5),
        "min": (0, 40),
    }

    @staticmethod
    def calculate_ratings(stats: Dict, height: int = 78, weight: int = 220, age: int = 25) -> Dict[str, List[int]]:
        """
        Convert raw stats to 15 attributes in [current, potential] format.

        Args:
            stats: Raw per-game or total stats dict
            height: Player height in inches (for derived attributes)
            weight: Player weight in lbs (for strength)
            age: Player age (for potential calculation)

        Returns:
            Dict with 15 attribute keys, each containing [current, potential] array
        """
        # Convert totals to per-game if needed
        pg_stats = stats.copy()
        gp = stats.get("GP", 0)

        stat_keys = [
            "PTS", "REB", "OREB", "DREB", "AST", "STL", "BLK", "TOV",
            "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "MIN"
        ]

        if gp > 0:
            for k in stat_keys:
                if k in stats:
                    pg_stats[k] = stats[k] / gp

        # Calculate each attribute
        ins = StatsConverter._calc_inside_scoring(pg_stats)
        mid = StatsConverter._calc_mid_range(pg_stats)
        tpt = StatsConverter._calc_three_point(pg_stats)
        fts = StatsConverter._calc_free_throw(pg_stats)

        # Layup: based on inside scoring + touch (FT%)
        lay = StatsConverter._calc_layup(pg_stats, ins)

        # Dunk: based on height + inside scoring
        dnk = StatsConverter._calc_dunk(pg_stats, height, ins)

        # Dribbling: derived from assists + turnovers
        drb = StatsConverter._calc_dribbling(pg_stats)

        # Passing
        pas = normalize_rating(pg_stats.get("AST", 0), *StatsConverter.RANGES["ast"])

        # Rebounding split
        ore = normalize_rating(pg_stats.get("OREB", 0), *StatsConverter.RANGES["oreb"])
        dre = normalize_rating(pg_stats.get("DREB", pg_stats.get("REB", 0) * 0.75), 0, 8.0)

        # Defensive attributes
        stl = normalize_rating(pg_stats.get("STL", 0), *StatsConverter.RANGES["stl"])
        blk = normalize_rating(pg_stats.get("BLK", 0), *StatsConverter.RANGES["blk"])

        # Physical attributes
        strength = StatsConverter._calc_strength(weight, height)
        speed = StatsConverter._calc_speed(height, weight)
        stamina = StatsConverter._calc_stamina(pg_stats)

        # Build attributes dict with [current, potential] format
        # Apply NBA floors and age-based potential
        def make_attr(current: int, age: int) -> List[int]:
            """
            Create [current, potential] array with age-based ceiling.
            Ensures potential is never less than current - if a player performs
            at a high level, their ceiling is at least that high.
            """
            pot_bonus = calculate_potential_bonus(age)
            pot = min(20, max(current, current + pot_bonus))
            return [current, pot]

        return {
            "LAY": make_attr(apply_nba_floor(lay, "LAY"), age),
            "DNK": make_attr(apply_nba_floor(dnk, "DNK"), age),
            "INS": make_attr(apply_nba_floor(ins, "INS"), age),
            "MID": make_attr(apply_nba_floor(mid, "MID"), age),
            "TPT": make_attr(apply_nba_floor(tpt, "TPT"), age),
            "FTS": make_attr(apply_nba_floor(fts, "FTS"), age),
            "DRB": make_attr(apply_nba_floor(drb, "DRB"), age),
            "PAS": make_attr(apply_nba_floor(pas, "PAS"), age),
            "ORE": make_attr(apply_nba_floor(ore, "ORE"), age),
            "DRE": make_attr(apply_nba_floor(dre, "DRE"), age),
            "STL": make_attr(apply_nba_floor(stl, "STL"), age),
            "BLK": make_attr(apply_nba_floor(blk, "BLK"), age),
            "STR": make_attr(apply_nba_floor(strength, "STR"), age),
            "SPD": make_attr(apply_nba_floor(speed, "SPD"), age),
            "STM": make_attr(apply_nba_floor(stamina, "STM"), age),
        }

    @staticmethod
    def calculate_legacy_ratings(stats: Dict) -> Dict[str, int]:
        """
        Legacy 6-attribute calculation for backward compatibility.
        Returns single int values instead of arrays.
        """
        pg_stats = stats.copy()
        gp = stats.get("GP", 0)

        stat_keys = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"]

        if gp > 0:
            for k in stat_keys:
                if k in stats:
                    pg_stats[k] = stats[k] / gp

        ratings = {}
        ratings["shooting_inside"] = StatsConverter._calc_inside_scoring(pg_stats)
        ratings["shooting_mid"] = StatsConverter._calc_mid_range(pg_stats)
        ratings["shooting_3pt"] = StatsConverter._calc_three_point(pg_stats)

        def_impact = pg_stats.get("STL", 0) * 1.5 + pg_stats.get("BLK", 0)
        ratings["defense"] = normalize_rating(def_impact, 0, 3.5)
        ratings["rebounding"] = normalize_rating(pg_stats.get("REB", 0), *StatsConverter.RANGES["reb"])
        ratings["passing"] = normalize_rating(pg_stats.get("AST", 0), *StatsConverter.RANGES["ast"])

        return ratings

    @staticmethod
    def _calc_inside_scoring(stats: Dict) -> int:
        """Calculate inside scoring (INS) - FG% weighted by volume."""
        fg_pct = stats.get("FG_PCT", 0)
        fgm_pg = stats.get("FGM", 0)

        eff_score = normalize_rating(fg_pct, *StatsConverter.RANGES["fg_pct"])
        vol_score = normalize_rating(fgm_pg, *StatsConverter.RANGES["fgm"])

        return int(round(eff_score * 0.5 + vol_score * 0.5))

    @staticmethod
    def _calc_mid_range(stats: Dict) -> int:
        """Calculate mid-range shooting (MID) - FG% + FT% as touch indicator."""
        fg_pct = stats.get("FG_PCT", 0)
        ft_pct = stats.get("FT_PCT", 0)

        touch_rating = (normalize_rating(fg_pct, 0.35, 0.50) + normalize_rating(ft_pct, 0.60, 0.90)) / 2
        return int(round(touch_rating))

    @staticmethod
    def _calc_three_point(stats: Dict) -> int:
        """Calculate three-point shooting (TPT) - 3P% weighted by volume."""
        pct = stats.get("FG3_PCT", 0)
        makes = stats.get("FG3M", 0)
        attempts = stats.get("FG3A", 0)

        if attempts < 0.1:
            return 1

        eff_score = normalize_rating(pct, *StatsConverter.RANGES["fg3_pct"])
        vol_score = normalize_rating(makes, *StatsConverter.RANGES["fg3m"])

        return int(eff_score * 0.5 + vol_score * 0.5)

    @staticmethod
    def _calc_free_throw(stats: Dict) -> int:
        """Calculate free throw shooting (FTS)."""
        ft_pct = stats.get("FT_PCT", 0)
        return normalize_rating(ft_pct, *StatsConverter.RANGES["ft_pct"])

    @staticmethod
    def _calc_layup(stats: Dict, inside_score: int) -> int:
        """
        Calculate layup ability (LAY) on 1-20 scale.
        Based on inside scoring + free throw touch.
        """
        ft_pct = stats.get("FT_PCT", 0)
        touch_bonus = normalize_rating(ft_pct, 0.6, 0.85) - 10  # -9 to +10 bonus on 20 scale

        lay = inside_score + touch_bonus // 2
        return max(1, min(20, lay))

    @staticmethod
    def _calc_dunk(stats: Dict, height: int, inside_score: int) -> int:
        """
        Calculate dunk ability (DNK) on 1-20 scale.
        Based on height + inside scoring. Taller players dunk more.
        """
        # Height bonus: 6'6" (78") = 0, 6'10" (82") = +4, 7'0" (84") = +6
        height_bonus = max(0, (height - 78))

        # Inside scorers more likely to dunk (inside_score is 0-20)
        inside_bonus = max(0, (inside_score - 10) // 2)

        dnk = 6 + height_bonus + inside_bonus
        return max(1, min(20, dnk))

    @staticmethod
    def _calc_dribbling(stats: Dict) -> int:
        """
        Calculate dribbling (DRB) on 1-20 scale.
        Based on assists and turnover rate.
        """
        ast = stats.get("AST", 0)
        tov = stats.get("TOV", 0)

        # High assist, low turnover = good handles (normalize_rating now returns 1-20)
        assist_score = normalize_rating(ast, 0, 8.0)

        # Penalize turnovers (scaled for 20 scale)
        if tov > 0:
            tov_penalty = min(6, int(tov / 0.75))
        else:
            tov_penalty = 0

        return max(1, min(20, assist_score - tov_penalty + 4))

    @staticmethod
    def _calc_strength(weight: int, height: int) -> int:
        """
        Calculate strength (STR) on 1-20 scale based on weight and height ratio.
        Heavier relative to height = stronger.
        """
        # Expected weight for height (roughly 2.5 lbs per inch over 60")
        expected_weight = 140 + (height - 60) * 2.5

        # Bonus for being heavier than expected
        weight_diff = weight - expected_weight

        # Normalize to 1-20 scale: -30 lbs = 6, 0 = 10, +30 lbs = 14, +60 = 18
        strength = 10 + int(weight_diff / 7.5)
        return max(1, min(20, strength))

    @staticmethod
    def _calc_speed(height: int, weight: int) -> int:
        """
        Calculate speed (SPD) on 1-20 scale inversely related to height/weight.
        Guards faster than centers.
        """
        # Shorter, lighter = faster
        height_penalty = max(0, (height - 74))  # Penalty starts at 6'2"
        weight_penalty = max(0, (weight - 200) // 10)

        spd = 16 - height_penalty - weight_penalty
        return max(1, min(20, spd))

    @staticmethod
    def _calc_stamina(stats: Dict) -> int:
        """
        Calculate stamina (STM) based on minutes played.
        High-minute players have better conditioning.
        """
        min_pg = stats.get("MIN", 0)
        return normalize_rating(min_pg, 15, 38)


def calculate_overall_rating(attributes: Dict[str, List[int]], nba_mode: bool = False) -> float:
    """
    Calculate overall rating from 15 attributes.

    Args:
        attributes: Dict with 15 attribute keys, each containing [current, potential]
        nba_mode: If True, apply NBA floor (ratings scaled to 3-5 star range)

    Returns:
        float between 0-10 (or 5-10 in NBA mode)
    """
    if not attributes:
        return 0.0

    # Weighted categories
    offense_attrs = ["LAY", "DNK", "INS", "MID", "TPT", "FTS"]
    playmaking_attrs = ["DRB", "PAS"]
    defense_attrs = ["ORE", "DRE", "STL", "BLK"]
    physical_attrs = ["STR", "SPD", "STM"]

    def avg_category(attr_list: List[str]) -> float:
        vals = [attributes.get(k, [0, 0])[0] for k in attr_list]
        return sum(vals) / len(vals) if vals else 0

    offense = avg_category(offense_attrs)
    playmaking = avg_category(playmaking_attrs)
    defense = avg_category(defense_attrs)
    physical = avg_category(physical_attrs)

    # Weighted average - attributes are 0-20, normalize to 0-10 for rating
    base_rating = (offense * 0.35 + playmaking * 0.15 + defense * 0.25 + physical * 0.25) / 2.0

    if nba_mode:
        # NBA players should be rated 5.0-10.0 (3-5 stars in game)
        # Scale: base 0-10 -> nba 5-10
        nba_rating = 5.0 + (base_rating / 10.0) * 5.0
        return round(min(10.0, max(5.0, nba_rating)), 1)
    
    return round(base_rating, 1)


def calculate_nba_rating(attributes: Dict[str, List[int]], is_starter: bool = False) -> float:
    """
    Calculate NBA player rating with proper floor for professional players.
    
    NBA players are the best in the world - no one in the league should be 
    below a 3-star rating. Elite players get 5 stars.
    
    Args:
        attributes: Dict with 15 attribute keys (0-20 scale)
        is_starter: If True, boost rating slightly (starters are better than bench)
        
    Returns:
        Rating between 5.0-10.0 (3-5 stars in game)
    """
    if not attributes:
        return 5.0  # Minimum NBA floor
    
    # Get base rating (already normalized to 0-10 from 0-20 attributes)
    base = calculate_overall_rating(attributes, nba_mode=False)
    
    # Apply NBA scaling
    # - Minimum rating: 5.0 (3 stars)
    # - Average NBA player: ~7.0 (mid 3-4 stars)
    # - Great player: ~8.5 (high 4 stars)
    # - Elite/MVP: ~9.5 (5 stars)
    
    # Use sigmoid-like scaling to compress low values and spread high values
    # This prevents too many low-rated players while still differentiating elite
    if base <= 4.0:
        # Low performers get floor rating with small variance
        nba_rating = 5.0 + (base / 4.0) * 1.5  # 5.0 - 6.5
    elif base <= 6.0:
        # Average players
        nba_rating = 6.5 + ((base - 4.0) / 2.0) * 1.5  # 6.5 - 8.0
    elif base <= 8.0:
        # Good players
        nba_rating = 8.0 + ((base - 6.0) / 2.0) * 1.0  # 8.0 - 9.0
    else:
        # Elite players
        nba_rating = 9.0 + ((base - 8.0) / 2.0) * 1.0  # 9.0 - 10.0
    
    # Starter bonus (small boost)
    if is_starter:
        nba_rating = min(10.0, nba_rating + 0.3)

    return round(min(10.0, max(5.0, nba_rating)), 1)


def percentile_to_rating(percentile: float) -> float:
    """
    Map a percentile (0-100) to a 2K-style rating (6.0-10.0).

    All NBA players are professionals, so minimum is 3 stars (6.0).

    Target distribution:
    - 99%+: 10 (5 stars - MVP/Superstar)
    - 95-99%: 9.x (4.5 stars - All-Star/Key players)
    - 80-95%: 8.x (4 stars - Solid starters/contributors)
    - 50-80%: 7.x (3.5 stars - Rotation players)
    - 0-50%: 6.x (3 stars - Bench/End of rotation)
    """
    if percentile >= 99:
        return 10.0
    elif percentile >= 95:
        return 9.0 + (percentile - 95) / 4.0 * 0.9
    elif percentile >= 80:
        return 8.0 + (percentile - 80) / 15.0 * 0.9
    elif percentile >= 50:
        return 7.0 + (percentile - 50) / 30.0 * 0.9
    else:
        return 6.0 + percentile / 50.0 * 0.9


def calculate_minutes_bonus(stats: Dict[str, Any]) -> float:
    """
    Calculate bonus rating based on minutes played.

    Players who play more minutes are generally more valuable to their team.
    This helps differentiate key contributors from deep bench players.

    Args:
        stats: Player's raw stats dict containing MIN and GP

    Returns:
        Bonus value from 0.0 to 1.0
    """
    gp = stats.get("GP", 0)
    if gp <= 0:
        return 0.0

    total_min = stats.get("MIN", 0)
    min_pg = total_min / gp

    if min_pg >= 30:
        return 0.5 + min(0.5, (min_pg - 30) / 10.0)
    elif min_pg >= 15:
        return (min_pg - 15) / 30.0
    return 0.0


def calculate_league_ratings(
    all_player_attributes: List[Dict[str, List[int]]],
    all_player_stats: List[Dict[str, Any]] = None
) -> List[float]:
    """
    Calculate ratings for all players using percentile-based distribution.

    This function produces a 2K-style distribution where elite players
    are clearly separated from average players. It also applies a minutes
    bonus to differentiate key contributors from deep bench players.

    Args:
        all_player_attributes: List of attribute dicts for all players
        all_player_stats: Optional list of raw stats dicts for minutes bonus

    Returns:
        List of ratings (6.0-10.0) in same order as input
    """
    if not all_player_attributes:
        return []

    n = len(all_player_attributes)
    if n == 1:
        bonus = 0.0
        if all_player_stats and len(all_player_stats) > 0:
            bonus = calculate_minutes_bonus(all_player_stats[0])
        return [min(10.0, 7.0 + bonus)]

    base_ratings = []
    for attrs in all_player_attributes:
        base = calculate_overall_rating(attrs, nba_mode=False)
        base_ratings.append(base)

    indexed_ratings = [(i, r) for i, r in enumerate(base_ratings)]
    sorted_by_rating = sorted(indexed_ratings, key=lambda x: x[1])

    final_ratings = [0.0] * n

    for rank, (original_idx, _) in enumerate(sorted_by_rating):
        percentile = (rank / (n - 1)) * 100.0 if n > 1 else 50.0
        rating = percentile_to_rating(percentile)

        if all_player_stats and original_idx < len(all_player_stats):
            bonus = calculate_minutes_bonus(all_player_stats[original_idx])
            rating = min(10.0, rating + bonus)

        final_ratings[original_idx] = ceil_to_half(rating)

    return final_ratings


PROSPECT_ARCHETYPES = {
    "scorer": {
        "INS": 1.3, "MID": 1.2, "TPT": 1.1, "LAY": 1.2, "DNK": 1.1,
        "FTS": 1.1, "DRB": 0.9, "PAS": 0.85, "DRE": 0.8, "STL": 0.85,
    },
    "playmaker": {
        "PAS": 1.4, "DRB": 1.3, "SPD": 1.15, "STL": 1.05, "LAY": 1.0,
        "INS": 0.85, "BLK": 0.7, "DRE": 0.8, "STR": 0.85,
    },
    "rim_protector": {
        "BLK": 1.5, "DRE": 1.3, "STR": 1.25, "ORE": 1.1, "INS": 0.9,
        "LAY": 1.0, "DNK": 1.1, "TPT": 0.6, "DRB": 0.7, "PAS": 0.75,
    },
    "stretch_big": {
        "TPT": 1.35, "MID": 1.25, "DRE": 1.1, "BLK": 1.0, "FTS": 1.1,
        "STR": 1.05, "INS": 0.85, "SPD": 0.85, "DRB": 0.8,
    },
    "three_and_d": {
        "TPT": 1.35, "STL": 1.25, "DRE": 1.15, "SPD": 1.05, "STM": 1.05,
        "PAS": 0.85, "INS": 0.8, "DRB": 0.85, "ORE": 0.9,
    },
    "slasher": {
        "LAY": 1.35, "DNK": 1.35, "SPD": 1.25, "DRB": 1.1, "STM": 1.1,
        "TPT": 0.75, "MID": 0.85, "BLK": 0.8, "STR": 0.95,
    },
    "floor_general": {
        "PAS": 1.45, "DRB": 1.2, "MID": 1.1, "FTS": 1.1, "STL": 1.0,
        "SPD": 1.0, "INS": 0.8, "DNK": 0.7, "BLK": 0.6, "STR": 0.8,
    },
    "athletic_big": {
        "DNK": 1.4, "BLK": 1.25, "ORE": 1.2, "DRE": 1.15, "STR": 1.2,
        "SPD": 1.0, "STM": 1.05, "TPT": 0.6, "MID": 0.7, "PAS": 0.75,
    },
    "balanced": {
        "LAY": 1.0, "DNK": 1.0, "INS": 1.0, "MID": 1.0, "TPT": 1.0,
        "FTS": 1.0, "DRB": 1.0, "PAS": 1.0, "ORE": 1.0, "DRE": 1.0,
        "STL": 1.0, "BLK": 1.0, "STR": 1.0, "SPD": 1.0, "STM": 1.0,
    },
}


def detect_prospect_archetype(
    height: int,
    college_stats: Dict[str, Any] = None,
    position: int = 3,
) -> str:
    if college_stats is None:
        college_stats = {}

    ppg = college_stats.get("PTS", college_stats.get("ppg", 0)) or 0
    apg = college_stats.get("AST", college_stats.get("apg", 0)) or 0
    rpg = college_stats.get("REB", college_stats.get("rpg", 0)) or 0
    bpg = college_stats.get("BLK", college_stats.get("bpg", 0)) or 0
    spg = college_stats.get("STL", college_stats.get("spg", 0)) or 0
    tpp = college_stats.get("FG3_PCT", college_stats.get("tp_pct", 0)) or 0

    if height >= 82:
        if bpg >= 2.0:
            return "rim_protector"
        if tpp >= 0.33 or tpp >= 33:
            return "stretch_big"
        return "athletic_big"

    if height >= 78:
        if ppg >= 15 and apg < 4:
            return "scorer"
        if apg >= 4 and ppg >= 12:
            return "playmaker"
        if tpp >= 0.35 or tpp >= 35:
            if spg >= 1.2:
                return "three_and_d"
            return "stretch_big"
        if bpg >= 1.5:
            return "rim_protector"
        return "balanced"

    if position <= 1 or height <= 75:
        if apg >= 5:
            return "floor_general"
        if ppg >= 15:
            if tpp >= 0.35 or tpp >= 35:
                return "scorer"
            return "slasher"
        return "playmaker"

    if ppg >= 16:
        return "scorer"
    if spg >= 1.5 and (tpp >= 0.34 or tpp >= 34):
        return "three_and_d"
    if apg >= 4:
        return "playmaker"

    return "balanced"


def calculate_prospect_grade(
    pick: int,
    career_eff: float = 0,
    career_gp: int = 0,
) -> tuple:
    if pick <= 3:
        base_rating, base_pot = 7.5, 9.5
    elif pick <= 5:
        base_rating, base_pot = 7.0, 9.0
    elif pick <= 10:
        base_rating, base_pot = 6.5, 8.5
    elif pick <= 14:
        base_rating, base_pot = 6.5, 8.0
    elif pick <= 20:
        base_rating, base_pot = 6.0, 7.5
    elif pick <= 30:
        base_rating, base_pot = 6.0, 7.0
    elif pick <= 45:
        base_rating, base_pot = 5.5, 6.5
    else:
        base_rating, base_pot = 5.0, 6.0

    if career_gp > 0 and career_eff > 0:
        if career_eff > 20:
            eff_bonus = 1.0
        elif career_eff > 15:
            eff_bonus = 0.5
        elif career_eff > 10:
            eff_bonus = 0.0
        elif career_eff > 5:
            eff_bonus = -0.5
        else:
            eff_bonus = -1.0

        base_pot = min(10.0, max(5.0, base_pot + eff_bonus))

    return (ceil_to_half(base_rating), ceil_to_half(min(10.0, base_pot)))


def calculate_prospect_attributes(
    rating: float,
    potential: float,
    archetype: str,
    college_stats: Dict[str, Any] = None,
    height: int = 78,
) -> Dict[str, List[int]]:
    if college_stats is None:
        college_stats = {}

    template = PROSPECT_ARCHETYPES.get(archetype, PROSPECT_ARCHETYPES["balanced"])

    base_current = int(rating * 1.8)
    base_potential = int(potential * 1.9)

    base_current = max(6, min(16, base_current))
    base_potential = max(10, min(19, base_potential))

    all_attrs = ["LAY", "DNK", "INS", "MID", "TPT", "FTS", "DRB", "PAS", "ORE", "DRE", "STL", "BLK", "STR", "SPD", "STM"]

    attributes = {}
    for attr in all_attrs:
        mult = template.get(attr, 1.0)
        current = int(base_current * mult)
        pot = int(base_potential * mult)

        current = max(4, min(18, current))
        pot = max(current, min(20, pot))

        attributes[attr] = [current, pot]

    if height >= 82:
        attributes["BLK"][0] = max(attributes["BLK"][0], 8)
        attributes["DRE"][0] = max(attributes["DRE"][0], 8)
        attributes["STR"][0] = max(attributes["STR"][0], 9)
        attributes["SPD"][0] = min(attributes["SPD"][0], 14)
    elif height <= 74:
        attributes["SPD"][0] = max(attributes["SPD"][0], 10)
        attributes["DRB"][0] = max(attributes["DRB"][0], 8)
        attributes["BLK"][0] = min(attributes["BLK"][0], 8)
        attributes["STR"][0] = min(attributes["STR"][0], 12)

    ppg = college_stats.get("PTS", college_stats.get("ppg", 0)) or 0
    apg = college_stats.get("AST", college_stats.get("apg", 0)) or 0
    rpg = college_stats.get("REB", college_stats.get("rpg", 0)) or 0
    spg = college_stats.get("STL", college_stats.get("spg", 0)) or 0
    bpg = college_stats.get("BLK", college_stats.get("bpg", 0)) or 0

    if ppg >= 18:
        attributes["INS"][0] = min(18, attributes["INS"][0] + 2)
        attributes["MID"][0] = min(18, attributes["MID"][0] + 1)
    if apg >= 5:
        attributes["PAS"][0] = min(18, attributes["PAS"][0] + 2)
        attributes["DRB"][0] = min(18, attributes["DRB"][0] + 1)
    if rpg >= 9:
        attributes["DRE"][0] = min(18, attributes["DRE"][0] + 2)
        attributes["ORE"][0] = min(18, attributes["ORE"][0] + 1)
    if spg >= 1.8:
        attributes["STL"][0] = min(18, attributes["STL"][0] + 2)
    if bpg >= 2.0:
        attributes["BLK"][0] = min(18, attributes["BLK"][0] + 2)

    for attr in all_attrs:
        attributes[attr][1] = max(attributes[attr][0], attributes[attr][1])

    return attributes

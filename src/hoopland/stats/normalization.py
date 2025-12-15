"""
Stats normalization and attribute calculation for Hoopland.

Converts raw player statistics into game-ready attributes matching
the target schema format (15 attributes with [current, potential] arrays).
"""

from typing import Dict, List, Any


def normalize_rating(value, min_val, max_val, scale: int = 20) -> int:
    """
    Normalize a value to a 1-20 rating scale (matching target schema).
    
    The game uses 1-20 scale for all attributes. Previously this was 1-10
    which caused all players to have low ratings in-game.
    
    Args:
        value: The raw stat value
        min_val: Minimum expected value for this stat
        max_val: Maximum expected value for this stat  
        scale: Output scale (default 20 to match game)
    """
    if value is None:
        return 1

    val = max(min_val, min(value, max_val))

    if max_val == min_val:
        return scale // 2

    rating = ((val - min_val) / (max_val - min_val)) * scale
    return max(1, min(scale, int(round(rating))))


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
        "pts": (0, 30),
        "reb": (0, 12.0),
        "oreb": (0, 4.0),
        "dreb": (0, 10.0),
        "ast": (0, 9.5),
        "stl": (0, 2.2),
        "blk": (0, 2.5),
        "fg_pct": (0.35, 0.55),
        "fg3_pct": (0.28, 0.44),
        "ft_pct": (0.5, 0.92),
        "fgm": (0, 10.0),
        "fg3m": (0, 3.5),
        "min": (0, 40),
    }

    @staticmethod
    def calculate_ratings(stats: Dict, height: int = 78, weight: int = 220) -> Dict[str, List[int]]:
        """
        Convert raw stats to 15 attributes in [current, potential] format.

        Args:
            stats: Raw per-game or total stats dict
            height: Player height in inches (for derived attributes)
            weight: Player weight in lbs (for strength)

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
        # Potential is current + slight bonus (capped at 20 to match game scale)
        def make_attr(current: int, pot_bonus: int = 0) -> List[int]:
            pot = min(20, max(current, current + pot_bonus))
            return [current, pot]

        return {
            "LAY": make_attr(lay),
            "DNK": make_attr(dnk),
            "INS": make_attr(ins),
            "MID": make_attr(mid),
            "TPT": make_attr(tpt),
            "FTS": make_attr(fts),
            "DRB": make_attr(drb),
            "PAS": make_attr(pas),
            "ORE": make_attr(ore),
            "DRE": make_attr(dre),
            "STL": make_attr(stl),
            "BLK": make_attr(blk),
            "STR": make_attr(strength),
            "SPD": make_attr(speed),
            "STM": make_attr(stamina),
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

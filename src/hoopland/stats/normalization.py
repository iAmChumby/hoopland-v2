def normalize_rating(value, min_val, max_val):
    if value is None:
        return 1

    # Clip values
    val = max(min_val, min(value, max_val))

    # Formula: Rating = (PlayerStat - MinStat) / (MaxStat - MinStat) * 10
    if max_val == min_val:
        return 5  # default

    rating = ((val - min_val) / (max_val - min_val)) * 10
    return max(1, min(10, int(round(rating))))


class StatsConverter:
    # Baseline stats (approximate min/max for normalization)
    RANGES = {
        "pts": (0, 30),      
        "reb": (0, 12.0),    # Lowered to 12.0. 6 RPG -> 5. 12 RPG -> 10.
        "ast": (0, 9.5),     # Lowered to 9.5. 7.4 APG -> 8 rating.
        "stl": (0, 2.2),     
        "blk": (0, 2.5),
        "fg_pct": (0.35, 0.55), # Widen range to handle 45-50% being "good"
        "fg3_pct": (0.28, 0.44), 
        "ft_pct": (0.5, 0.92),
        
        # Volume ranges for weighted ratings
        "fgm": (0, 10.0),    # 9.0 makes -> 9 rating.
        "fg3m": (0, 3.5),
    }

    @staticmethod
    def calculate_ratings(stats):
        """
        Takes a dict of raw stats and returns Hoop Land ratings.
        Handles both Per Game and Total stats if 'GP' is present.
        """
        ratings = {}

        # Determine if we need to convert totals to per-game
        pg_stats = stats.copy()
        gp = stats.get("GP", 0)

        # List of keys to average
        stat_keys = [
            "PTS", "REB", "AST", "STL", "BLK", "TOV",
            "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"
        ]

        if gp > 0:
            for k in stat_keys:
                if k in stats:
                    pg_stats[k] = stats[k] / gp

        ratings["shooting_inside"] = StatsConverter._calc_shooting_inside(pg_stats)
        ratings["shooting_mid"] = StatsConverter._calc_shooting_mid(pg_stats)
        ratings["shooting_3pt"] = StatsConverter._calc_shooting_3pt(pg_stats)

        # Defense: STL + BLK roughly
        # 1.5 multiplier for steals makes them valuable
        def_impact = pg_stats.get("STL", 0) * 1.5 + pg_stats.get("BLK", 0)
        ratings["defense"] = normalize_rating(def_impact, 0, 3.5)

        ratings["rebounding"] = normalize_rating(
            pg_stats.get("REB", 0), *StatsConverter.RANGES["reb"]
        )
        ratings["passing"] = normalize_rating(
            pg_stats.get("AST", 0), *StatsConverter.RANGES["ast"]
        )

        return ratings

    @staticmethod
    def _calc_shooting_inside(stats):
        # Primary driver: FG% inside arc (proxy using FG%)
        # But weight by volume to reward primary scorers
        fg_pct = stats.get("FG_PCT", 0)
        fgm_pg = stats.get("FGM", 0)
        
        eff_score = normalize_rating(fg_pct, *StatsConverter.RANGES["fg_pct"])
        vol_score = normalize_rating(fgm_pg, *StatsConverter.RANGES["fgm"])
        
        # 50/50 split works better with the new relaxed ranges
        return int(round(eff_score * 0.5 + vol_score * 0.5))

    @staticmethod
    def _calc_shooting_mid(stats):
        # Proxy: mixture of FG% and FT% (good indicator of shooting touch)
        fg_pct = stats.get("FG_PCT", 0)
        ft_pct = stats.get("FT_PCT", 0)
        
        touch_rating = (normalize_rating(fg_pct, 0.35, 0.50) + normalize_rating(ft_pct, 0.60, 0.90)) / 2
        return int(round(touch_rating))

    @staticmethod
    def _calc_shooting_3pt(stats):
        pct = stats.get("FG3_PCT", 0)
        makes = stats.get("FG3M", 0)
        
        # If low attempts, penalty
        attempts = stats.get("FG3A", 0)
        if attempts < 0.1:
            return 1
            
        eff_score = normalize_rating(pct, *StatsConverter.RANGES["fg3_pct"])
        vol_score = normalize_rating(makes, *StatsConverter.RANGES["fg3m"])
        
        # 50/50 split. 
        # Steph Curry (5 makes, 45%): Vol(10) * 0.5 + Eff(10) * 0.5 = 10
        # Specialist (2 makes, 40%): Vol(6) * 0.5 + Eff(8) * 0.5 = 7
        # Chucker (2 makes, 30%): Vol(6) * 0.5 + Eff(2) * 0.5 = 4
        return int(eff_score * 0.5 + vol_score * 0.5)

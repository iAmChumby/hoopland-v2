def normalize_rating(value, min_val, max_val):
    if value is None:
        return 1
    
    # Clip values
    val = max(min_val, min(value, max_val))
    
    # Formula: Rating = (PlayerStat - MinStat) / (MaxStat - MinStat) * 10
    if max_val == min_val:
        return 5 # default
        
    rating = ((val - min_val) / (max_val - min_val)) * 10
    return max(1, min(10, int(round(rating))))

class StatsConverter:
    # Baseline stats (approximate min/max for normalization)
    RANGES = {
        'pts': (0, 35),
        'reb': (0, 15),
        'ast': (0, 12),
        'stl': (0, 3),
        'blk': (0, 3),
        'fg_pct': (0.3, 0.6), # 30% to 60%
        'fg3_pct': (0.2, 0.5),
        'ft_pct': (0.5, 0.95)
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
        gp = stats.get('GP', 0)
        
        # List of keys to average
        stat_keys = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA']
        
        if gp > 0:
            for k in stat_keys:
                if k in stats:
                    pg_stats[k] = stats[k] / gp
        
        # Use pg_stats for volume-based ratings, but keep percentages from original (they are usually already %)
        # Note: NBA API usually gives percentages as 0.XYZ, checking range might be needed but assuming 0-1 or 0-100 logic in converter
        
        ratings['shooting_inside'] = StatsConverter._calc_shooting_inside(pg_stats)
        ratings['shooting_mid'] = StatsConverter._calc_shooting_mid(pg_stats)
        ratings['shooting_3pt'] = normalize_rating(pg_stats.get('FG3_PCT', 0), *StatsConverter.RANGES['fg3_pct'])
        
        # Defense: STL + BLK roughly
        def_impact = pg_stats.get('STL', 0) + pg_stats.get('BLK', 0)
        ratings['defense'] = normalize_rating(def_impact, 0, 3) # Reduced max from 5 to 3 for tighter distribution
        
        ratings['rebounding'] = normalize_rating(pg_stats.get('REB', 0), *StatsConverter.RANGES['reb'])
        ratings['passing'] = normalize_rating(pg_stats.get('AST', 0), *StatsConverter.RANGES['ast'])
        
        return ratings

    @staticmethod
    def _calc_shooting_inside(stats):
        # Heavy weight on FG% but factor volume
        eff = normalize_rating(stats.get('FG_PCT', 0), *StatsConverter.RANGES['fg_pct'])
        return eff

    @staticmethod
    def _calc_shooting_mid(stats):
        # Just use FG% for now
        return normalize_rating(stats.get('FG_PCT', 0), *StatsConverter.RANGES['fg_pct'])

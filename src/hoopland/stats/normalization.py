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
        Takes a dict of raw stats (per game) and returns Hoop Land ratings.
        """
        ratings = {}
        
        # Example mapping
        ratings['shooting_inside'] = StatsConverter._calc_shooting_inside(stats)
        ratings['shooting_mid'] = StatsConverter._calc_shooting_mid(stats) # Approximation
        ratings['shooting_3pt'] = normalize_rating(stats.get('FG3_PCT', 0), *StatsConverter.RANGES['fg3_pct'])
        
        # Defense: STL + BLK roughly
        def_impact = stats.get('STL', 0) + stats.get('BLK', 0)
        ratings['defense'] = normalize_rating(def_impact, 0, 5) 
        
        ratings['rebounding'] = normalize_rating(stats.get('REB', 0), *StatsConverter.RANGES['reb'])
        ratings['passing'] = normalize_rating(stats.get('AST', 0), *StatsConverter.RANGES['ast'])
        
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

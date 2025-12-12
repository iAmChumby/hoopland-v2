
from hoopland.stats.normalization import StatsConverter

def test_lebron_2015_ratings():
    # LeBron 2014-15 Stats
    stats = {
        "GP": 69,
        "PTS": 1743, "REB": 416, "AST": 511, "STL": 109, "BLK": 49,
        "FGM": 624, "FGA": 1279, 
        "FG3M": 120, "FG3A": 339, 
        "FTM": 375, "FTA": 528,
        # Pre-calculated percentages usually present in row
        "FG_PCT": 0.488, "FG3_PCT": 0.354, "FT_PCT": 0.710
    }
    
    ratings = StatsConverter.calculate_ratings(stats)
    print("\nLeBron 2015 Ratings:")
    for k, v in ratings.items():
        print(f"{k}: {v}")
        
    # Expectations
    # Inside: High volume, good efficiency -> 9-10
    # Mid: Decent -> 7-8
    # 3pt: Avg efficiency, some volume -> 5-6
    # Defense: 1.6 stl + 0.7 blk = 2.3 -> ~6-7
    # Passing: 7.4 ast -> 7-8
    
    assert ratings["shooting_inside"] >= 8
    assert ratings["passing"] >= 7

def test_curry_2016_ratings():
    # Curry 2015-16 Unanimous MVP
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

    # Expectations
    # 3pt: 402 makes is insane volume. 45% is insane efficiency. MUST be 10.
    # Inside: 50% FG overall, high volume. 
    # Finishing at rim was elite for guard.
    
    assert ratings["shooting_3pt"] == 10
    
if __name__ == "__main__":
    test_lebron_2015_ratings()
    test_curry_2016_ratings()

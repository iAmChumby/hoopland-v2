
import json
import math
import statistics
import os

# Configuration
INPUT_FILE = r"C:\Users\73spi\Projects\hoopland-v2\NBA_2003_League.txt"
OUTPUT_FILE = r"C:\Users\73spi\Projects\hoopland-v2\NBA_2003_League_Tendencies.txt"

def load_league(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        # The file might have line numbers from previous view_file, but assuming direct file access it's raw JSON
        # If it's not valid JSON, we might need to handle per-line parsing, but usually it's one big JSON object
        return json.load(f)

def safe_div(num, denom):
    return num / denom if denom > 0 else 0.0

def calculate_derived_stats(player):
    stats = player.get('stats', {})
    
    # Basic stats
    fga = stats.get('FGA', 0)
    fgm = stats.get('FGM', 0)
    fg3a = stats.get('FG3A', 0)
    fg3m = stats.get('FG3M', 0)
    fta = stats.get('FTA', 0)
    ftm = stats.get('FTM', 0)
    ast = stats.get('AST', 0)
    oreb = stats.get('OREB', 0)
    dreb = stats.get('DREB', 0)
    stl = stats.get('STL', 0)
    blk = stats.get('BLK', 0)
    tov = stats.get('TOV', 0)
    pf = stats.get('PF', 0)
    min_played = stats.get('MIN', 0)
    height = player.get('ht', 75) # Default to 6'3"
    weight = player.get('wt', 200)
    
    # Derived rates
    fg_pct = safe_div(fgm, fga)
    three_rate = safe_div(fg3a, fga) # % of shots that are 3s
    mid_rate = safe_div(fga - fg3a, fga) # % of shots that are 2s (rough approx for mid/close split later)
    ast_per_min = safe_div(ast, min_played)
    oreb_per_min = safe_div(oreb, min_played)
    dreb_per_min = safe_div(dreb, min_played)
    stl_per_min = safe_div(stl, min_played)
    blk_per_min = safe_div(blk, min_played)
    tov_per_min = safe_div(tov, min_played)
    ft_rate = safe_div(fta, fga) # Free Throw Attempt Rate (proxy for drawing fouls/aggressive play)
    
    # Special composites
    # Dunk tendency proxy: High FG% + Height + Low 3P Rate
    dunk_score = (height - 70) * 0.5 + (fg_pct * 100) * 0.5 - (three_rate * 50)
    
    return {
        'three_rate': three_rate,
        'mid_rate': mid_rate,
        'ast_per_min': ast_per_min,
        'oreb_per_min': oreb_per_min,
        'dreb_per_min': dreb_per_min,
        'stl_per_min': stl_per_min,
        'blk_per_min': blk_per_min,
        'tov_per_min': tov_per_min,
        'ft_rate': ft_rate,
        'dunk_score': dunk_score,
        'fg_pct': fg_pct,
        'height': height,
        'fga': fga,
        'min_played': min_played
    }

def collect_league_stats(league_data):
    all_player_stats = []
    
    for team in league_data.get('teams', []):
        for player in team.get('roster', []):
            stats = player.get('stats', {})
            # Only consider players with some minutes to avoid skewing averages with 0s
            if stats.get('MIN', 0) > 50: 
                derived = calculate_derived_stats(player)
                all_player_stats.append(derived)
                
    return all_player_stats

def calculate_stats_distribution(all_stats):
    keys = all_stats[0].keys()
    distribution = {}
    
    for key in keys:
        values = [p[key] for p in all_stats]
        if not values:
            distribution[key] = {'mean': 0, 'stdev': 1}
            continue
            
        mean = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            stdev = 1
            
        distribution[key] = {'mean': mean, 'stdev': stdev if stdev > 0 else 1}
        
    return distribution

def get_z_score(val, dist_key, distribution):
    dist = distribution.get(dist_key)
    if not dist:
        return 0
    return (val - dist['mean']) / dist['stdev']

def map_z_to_tendency(z_score, scalar=2.0, min_val=-5, max_val=5, offset=0):
    # scalar = sensitivity. Higher scalar means easier to reach extremes? No.
    # z=2 => 2*2 = 4. 
    # If we want top 5% (z approx 2) to be 5, scalar should be 2.5
    raw = (z_score * scalar) + offset
    val = int(round(raw))
    return max(min_val, min(max_val, val))

def generate_tendencies_for_player(player, distribution):
    ds = calculate_derived_stats(player)
    
    t = {}
    
    # 1. Three Point Tendency
    z_3pt = get_z_score(ds['three_rate'], 'three_rate', distribution)
    t['threePoint'] = map_z_to_tendency(z_3pt, scalar=2.5, min_val=-5, max_val=5)
    
    # 2. Two Point / Mid Range
    # If 3PT is low, 2PT is naturally higher, but we want verify if they actually shoot
    z_2pt = get_z_score(ds['mid_rate'], 'mid_rate', distribution)
    # Penalize if they explicitly don't shoot much at all
    # But analyzing 2pt vs 3pt balance:
    t['twoPoint'] = map_z_to_tendency(z_2pt, scalar=2.0)
    
    # 3. Dunk
    z_dunk = get_z_score(ds['dunk_score'], 'dunk_score', distribution)
    t['dunk'] = map_z_to_tendency(z_dunk, scalar=2.0)
    
    # 4. Post - Correlation with Weight/Height and Low 3PA
    # Heuristic: Centers weight
    z_wt = get_z_score(player.get('wt', 200), 'height', distribution) # Using height/weight proxy? 
    # Actually let's use a custom score for post: Weight + (Height-75)*2 - 3PT rate*100
    post_score = player.get('wt', 200) + (player.get('ht', 75) - 75) * 3 - (ds['three_rate'] * 100)
    # We can't use z-score easily without adding post_score to initial pass.
    # Let's just use simplified mapping or recalculate locally if needed, but better to stick to standard derived stats
    # Using height z-score as proxy for now + position check
    pos = player.get('pos', 0) # 1=PG, 5=C presumably
    if pos >= 4: # PF/C
        t['post'] = 2
        t['hook'] = 1
        t['runPlay'] = 0
    else:
        t['post'] = -3
        t['hook'] = -4
        t['runPlay'] = 2
        
    if t['dunk'] > 3:
        t['post'] += 1
        
    # 5. Passing
    z_ast = get_z_score(ds['ast_per_min'], 'ast_per_min', distribution)
    t['pass'] = map_z_to_tendency(z_ast, scalar=2.5)
    t['lob'] = map_z_to_tendency(z_ast, scalar=2.0, offset=-1) # Lobs correlated with passing
    
    # 6. Rebounding
    z_oreb = get_z_score(ds['oreb_per_min'], 'oreb_per_min', distribution)
    t['offReb'] = map_z_to_tendency(z_oreb, scalar=2.5)
    
    z_dreb = get_z_score(ds['dreb_per_min'], 'dreb_per_min', distribution)
    t['defReb'] = map_z_to_tendency(z_dreb, scalar=2.5)
    
    # 7. Defense / Steals / Blocks
    z_stl = get_z_score(ds['stl_per_min'], 'stl_per_min', distribution)
    t['stealOnBall'] = map_z_to_tendency(z_stl, scalar=2.5)
    t['stealOffBall'] = map_z_to_tendency(z_stl, scalar=2.0, offset=-1)
    
    z_blk = get_z_score(ds['blk_per_min'], 'blk_per_min', distribution)
    t['block'] = map_z_to_tendency(z_blk, scalar=2.5)
    
    # 8. Handling / Crossover
    # High AST usually implies ball dominance -> crossover
    t['cross'] = map_z_to_tendency(z_ast, scalar=1.5, offset=-1)
    if pos == 1: # PG
        t['cross'] += 2
        
    # 9. Aggression / Drawing Fouls
    z_ft = get_z_score(ds['ft_rate'], 'ft_rate', distribution)
    t['pumpFake'] = map_z_to_tendency(z_ft, scalar=2.0)
    t['takeCharge'] = 0 # No good proxy
    
    # 10. Fill others with defaults or inferred
    t['floater'] = 0
    t['fades'] = 0
    t['spin'] = 0
    t['step'] = 0
    
    # Floater: Small guys who score inside?
    if player.get('ht', 75) < 75 and ds['mid_rate'] > 0.4:
        t['floater'] = 2
        
    # Step-back: High 3pt shooters
    if t['threePoint'] > 2:
        t['step'] = 2
        
    return t

def main():
    print(f"Loading {INPUT_FILE}...")
    try:
        data = load_league(INPUT_FILE)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    print("Analyzing league statistics...")
    all_derived_stats = collect_league_stats(data)
    distribution = calculate_stats_distribution(all_derived_stats)
    
    print("Generating player tendencies...")
    count = 0
    for team in data.get('teams', []):
        for player in team.get('roster', []):
            tendencies = generate_tendencies_for_player(player, distribution)
            player['tendencies'] = tendencies
            count += 1
            
    print(f"Updated {count} players.")
    
    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4) # Indent for readability, remove if size is critical
        
    print("Done.")

if __name__ == "__main__":
    main()

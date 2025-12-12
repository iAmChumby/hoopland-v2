
import math
import statistics
from typing import Dict, List, Any

def safe_div(num, denom):
    return num / denom if denom > 0 else 0.0

def calculate_derived_stats(stats: Dict[str, Any], height: int = 75) -> Dict[str, float]:
    """
    Calculate derived statistics from raw stats for a single player.
    """
    # Basic stats
    fga = float(stats.get('FGA', 0))
    fgm = float(stats.get('FGM', 0))
    fg3a = float(stats.get('FG3A', 0))
    fta = float(stats.get('FTA', 0))
    ast = float(stats.get('AST', 0))
    oreb = float(stats.get('OREB', 0))
    dreb = float(stats.get('DREB', 0))
    stl = float(stats.get('STL', 0))
    blk = float(stats.get('BLK', 0))
    tov = float(stats.get('TOV', 0))
    min_played = float(stats.get('MIN', 0))
    
    # Derived rates
    fg_pct = safe_div(fgm, fga)
    three_rate = safe_div(fg3a, fga) # % of shots that are 3s
    mid_rate = safe_div(fga - fg3a, fga) # % of shots that are 2s
    
    # Per Minute stats (to normalize playing time)
    ast_per_min = safe_div(ast, min_played)
    oreb_per_min = safe_div(oreb, min_played)
    dreb_per_min = safe_div(dreb, min_played)
    stl_per_min = safe_div(stl, min_played)
    blk_per_min = safe_div(blk, min_played)
    tov_per_min = safe_div(tov, min_played)
    ft_rate = safe_div(fta, fga) # Free Throw Attempt Rate
    three_pa_per_min = safe_div(fg3a, min_played) # [NEW] Volume Metric
    
    # Special composites
    # Dunk tendency proxy: High FG% + Height + Low 3P Rate
    dunk_score = (height - 70) * 0.5 + (fg_pct * 100) * 0.5 - (three_rate * 50)
    
    return {
        'three_rate': three_rate,
        'three_pa_per_min': three_pa_per_min,
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
        'min_played': min_played
    }

def calculate_distribution(all_derived_stats: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate mean and standard deviation for each derived stat across the league.
    """
    if not all_derived_stats:
        return {}
        
    keys = all_derived_stats[0].keys()
    distribution = {}
    
    for key in keys:
        values = [p[key] for p in all_derived_stats]
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
    raw = (z_score * scalar) + offset
    val = int(round(raw))
    return max(min_val, min(max_val, val))

def generate_player_tendencies(
    stats: Dict[str, Any], 
    height: int, 
    position: int, 
    distribution: Dict[str, Dict[str, float]]
) -> Dict[str, int]:
    """
    Generate tendency dictionary for a single player.
    """
    ds = calculate_derived_stats(stats, height)
    
    t = {}
    
    # 1. Three Point Tendency
    # 1. Three Point Tendency
    # We use a blend of Rate (% of shots that are 3s) and Volume (3PA per minute)
    # This prevents low volume shooters with high % from getting high tendency
    # and rewards high volume shooters like Curry even if their rate is just "good"
    z_3pt_rate = get_z_score(ds['three_rate'], 'three_rate', distribution)
    z_3pt_vol = get_z_score(ds['three_pa_per_min'], 'three_pa_per_min', distribution)
    
    # Weight volume slightly more (60/40) because tendency drives attempts
    z_3pt_final = (z_3pt_rate * 0.4) + (z_3pt_vol * 0.6)
    
    t['threePoint'] = map_z_to_tendency(z_3pt_final, scalar=2.5)
    
    # 2. Two Point
    z_2pt = get_z_score(ds['mid_rate'], 'mid_rate', distribution)
    t['twoPoint'] = map_z_to_tendency(z_2pt, scalar=2.0)
    
    # 3. Dunk
    z_dunk = get_z_score(ds['dunk_score'], 'dunk_score', distribution)
    t['dunk'] = map_z_to_tendency(z_dunk, scalar=2.0)
    
    # 4. Post
    # Heuristic: Centers/PFs have higher base post tendency
    if position >= 4: # PF/C
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
    t['lob'] = map_z_to_tendency(z_ast, scalar=2.0, offset=-1)
    
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
    if position == 1: # PG
        t['cross'] += 2
        
    # 9. Aggression / Drawing Fouls
    z_ft = get_z_score(ds['ft_rate'], 'ft_rate', distribution)
    t['pumpFake'] = map_z_to_tendency(z_ft, scalar=2.0)
    t['takeCharge'] = 0 
    
    # 10. Fill others
    t['floater'] = 0
    t['fades'] = 0
    t['spin'] = 0
    t['step'] = 0
    
    # Specific archetypes
    # Floater: Small guys who score inside
    if height < 75 and ds['mid_rate'] > 0.4:
        t['floater'] = 2
        
    # Step-back: High 3pt shooters
    if t['threePoint'] > 2:
        t['step'] = 2
        
    return t

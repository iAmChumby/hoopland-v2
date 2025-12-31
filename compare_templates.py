#!/usr/bin/env python3
import json
from typing import Dict, Any

def get_file_content(path: str) -> Dict[str, Any]:
    """Load JSON file with proper encoding."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return {}

def analyze_field(obj: Any, path: str = "") -> Dict[str, Any]:
    """Recursively analyze object structure."""
    if isinstance(obj, dict):
        return {k: "dict" if v else "empty_dict" if isinstance(v, dict) else 
                "list" if isinstance(v, list) else 
                type(v).__name__ for k, v in obj.items()}
    elif isinstance(obj, list):
        return "list"
    else:
        return "value"

def compare_team_fields(nba_team: Dict, ncaa_team: Dict, template_team: Dict) -> Dict[str, Any]:
    """Compare team-level fields across all three."""
    comparison = {}
    
    # Get all unique keys
    all_keys = set(nba_team.keys()) | set(ncaa_team.keys()) | set(template_team.keys())
    
    for key in sorted(all_keys):
        nba_val = nba_team.get(key)
        ncaa_val = ncaa_team.get(key)
        tmpl_val = template_team.get(key)
        
        # Check if fields are populated
        nba_populated = bool(nba_val) if not isinstance(nba_val, (int, float)) else nba_val != 0
        ncaa_populated = bool(ncaa_val) if not isinstance(ncaa_val, (int, float)) else ncaa_val != 0
        tmpl_populated = bool(tmpl_val) if not isinstance(tmpl_val, (int, float)) else tmpl_val != 0
        
        comparison[key] = {
            "nba_has": nba_populated,
            "ncaa_has": ncaa_populated,
            "template_has": tmpl_populated,
            "nba_type": type(nba_val).__name__ if nba_val is not None else "None",
            "ncaa_type": type(ncaa_val).__name__ if ncaa_val is not None else "None",
            "template_type": type(tmpl_val).__name__ if tmpl_val is not None else "None",
        }
    
    return comparison

def main():
    # Load all files
    print("Loading files...")
    nba_gen = get_file_content("output/2016/NBA_2016_League.txt")
    ncaa_gen = get_file_content("output/2016/NCAA_2016_Tournament_League.txt")
    ncaa_tmpl = get_file_content("data/CBB 2026 OCT25 _ ALPHA.txt")
    
    print(f"NBA generated: {len(nba_gen.get('teams', []))} teams")
    print(f"NCAA generated: {len(ncaa_gen.get('teams', []))} teams")
    print(f"NCAA template: {len(ncaa_tmpl.get('teams', []))} teams")
    
    # Compare league-level fields
    print("\n" + "="*80)
    print("LEAGUE-LEVEL COMPARISON")
    print("="*80)
    
    league_fields = {
        "leagueName": (nba_gen.get("leagueName"), ncaa_gen.get("leagueName"), ncaa_tmpl.get("leagueName")),
        "shortName": (nba_gen.get("shortName"), ncaa_gen.get("shortName"), ncaa_tmpl.get("shortName")),
        "logoURL": (nba_gen.get("logoURL"), ncaa_gen.get("logoURL"), ncaa_tmpl.get("logoURL")),
        "logoSize": (nba_gen.get("logoSize"), ncaa_gen.get("logoSize"), ncaa_tmpl.get("logoSize")),
        "leagueType": (nba_gen.get("leagueType"), ncaa_gen.get("leagueType"), ncaa_tmpl.get("leagueType")),
        "conferences": (len(nba_gen.get("conferences", [])), len(ncaa_gen.get("conferences", [])), len(ncaa_tmpl.get("conferences", []))),
        "divisions": (len(nba_gen.get("divisions", [])), len(ncaa_gen.get("divisions", [])), len(ncaa_tmpl.get("divisions", []))),
    }
    
    print(f"{'Field':<20} {'NBA':<30} {'NCAA Generated':<30} {'NCAA Template':<30}")
    print("-" * 110)
    for field, (nba, ncaa, tmpl) in league_fields.items():
        nba_str = str(nba)[:28]
        ncaa_str = str(ncaa)[:28]
        tmpl_str = str(tmpl)[:28]
        print(f"{field:<20} {nba_str:<30} {ncaa_str:<30} {tmpl_str:<30}")
    
    # Compare first team
    print("\n" + "="*80)
    print("TEAM-LEVEL COMPARISON (First Team)")
    print("="*80)
    
    nba_team = nba_gen.get("teams", [{}])[0]
    ncaa_team = ncaa_gen.get("teams", [{}])[0]
    ncaa_tmpl_team = ncaa_tmpl.get("teams", [{}])[0]
    
    print(f"NBA Team: {nba_team.get('name')} ({nba_team.get('city')})")
    print(f"NCAA Generated: {ncaa_team.get('name')} ({ncaa_team.get('city')})")
    print(f"NCAA Template: {ncaa_tmpl_team.get('name')} ({ncaa_tmpl_team.get('city')})")
    
    comparison = compare_team_fields(nba_team, ncaa_team, ncaa_tmpl_team)
    
    print(f"\n{'Field':<20} {'NBA':<8} {'NCAA Gen':<12} {'Template':<12} {'Status':<20}")
    print("-" * 90)
    
    for field in sorted(comparison.keys()):
        comp = comparison[field]
        nba_check = "Y" if comp["nba_has"] else "N"
        ncaa_check = "Y" if comp["ncaa_has"] else "N"
        tmpl_check = "Y" if comp["template_has"] else "N"
        
        if comp["ncaa_has"] != comp["template_has"]:
            status = "MISSING" if not comp["ncaa_has"] else "EXTRA"
        elif comp["ncaa_has"] and comp["template_has"]:
            status = "OK"
        else:
            status = "BOTH EMPTY"
        
        print(f"{field:<20} {nba_check:<8} {ncaa_check:<12} {tmpl_check:<12} {status:<20}")
    
    # Court comparison
    print("\n" + "="*80)
    print("COURT DESIGN COMPARISON")
    print("="*80)
    
    nba_court = nba_team.get("court", {})
    ncaa_court = ncaa_team.get("court", {})
    tmpl_court = ncaa_tmpl_team.get("court", {})
    
    print(f"{'Field':<25} {'NBA':<25} {'NCAA Gen':<25} {'Template':<25}")
    print("-" * 100)
    
    court_fields = ["outerWood", "outerWoodC", "innerWood", "innerWoodC", "outerFT", "outerFTC",
                    "outerKey", "outerKeyC", "innerKey", "innerKeyC", "outerBorder", "innerBorder",
                    "outerFloor", "logoSize", "overlayURL", "baseline1", "baseline2", "sideline1", "sideline2"]
    
    for field in court_fields:
        nba_val = str(nba_court.get(field, ""))[:23]
        ncaa_val = str(ncaa_court.get(field, ""))[:23]
        tmpl_val = str(tmpl_court.get(field, ""))[:23]
        print(f"{field:<25} {nba_val:<25} {ncaa_val:<25} {tmpl_val:<25}")
    
    # Uniforms comparison
    print("\n" + "="*80)
    print("UNIFORMS COMPARISON")
    print("="*80)
    
    nba_unis = nba_team.get("uniforms", [])
    ncaa_unis = ncaa_team.get("uniforms", [])
    tmpl_unis = ncaa_tmpl_team.get("uniforms", [])
    
    print(f"NBA uniforms: {len(nba_unis)} uniforms")
    if nba_unis:
        print(f"  Keys: {list(nba_unis[0].keys())[:5]}...")
    
    print(f"NCAA Generated uniforms: {len(ncaa_unis)} uniforms")
    if ncaa_unis:
        print(f"  Keys: {list(ncaa_unis[0].keys())}")
    
    print(f"NCAA Template uniforms: {len(tmpl_unis)} uniforms")
    if tmpl_unis:
        print(f"  Keys: {list(tmpl_unis[0].keys())}")
    
    # Front office comparison
    print("\n" + "="*80)
    print("FRONT OFFICE COMPARISON")
    print("="*80)
    
    nba_fo = nba_team.get("frontOffice", {})
    ncaa_fo = ncaa_team.get("frontOffice", {})
    tmpl_fo = ncaa_tmpl_team.get("frontOffice", {})
    
    print(f"NBA FO: {list(nba_fo.keys())}")
    print(f"NCAA Gen FO: {list(ncaa_fo.keys())}")
    print(f"Template FO: {list(tmpl_fo.keys())}")
    
    if ncaa_fo:
        print(f"\nNCAA Generated FO detail:")
        print(f"  coins: {ncaa_fo.get('coins')}")
        print(f"  facilities: {len(ncaa_fo.get('facilities', []))} items")
        print(f"  staff: {len(ncaa_fo.get('staff', []))} items")
    
    if tmpl_fo:
        print(f"\nTemplate FO detail:")
        print(f"  coins: {tmpl_fo.get('coins')}")
        print(f"  facilities: {len(tmpl_fo.get('facilities', []))} items")
        print(f"  staff: {len(tmpl_fo.get('staff', []))} items")
    
    # Summary
    print("\n" + "="*80)
    print("ENRICHMENT PROGRESS SUMMARY")
    print("="*80)
    
    missing = []
    for field, comp in comparison.items():
        if not comp["ncaa_has"] and comp["template_has"]:
            missing.append(field)
    
    print(f"\nFields in template but missing in NCAA generated:")
    for field in missing:
        print(f"  - {field}")
    
    print(f"\nTotal missing fields: {len(missing)} out of {len(comparison)}")
    print(f"Completion: {((len(comparison) - len(missing)) / len(comparison) * 100):.1f}%")

if __name__ == "__main__":
    main()


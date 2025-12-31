#!/usr/bin/env python3
import json

# Read NCAA template
with open("data/CBB 2026 OCT25 _ ALPHA.txt", "r", encoding="utf-8") as f:
    ncaa = json.load(f)

# Read NBA template
with open("data/nba0203.txt", "r", encoding="utf-8") as f:
    nba = json.load(f)

print("=" * 80)
print("NCAA TEMPLATE STRUCTURE")
print("=" * 80)
print(f"League Name: {ncaa.get('leagueName')}")
print(f"Short Name: {ncaa.get('shortName')}")
print(f"Logo URL: {ncaa.get('logoURL')}")
print(f"Logo Size: {ncaa.get('logoSize')}")
print(f"League Type: {ncaa.get('leagueType')}")
print(f"\nConferences: {ncaa.get('conferences')}")
print(f"Divisions: {ncaa.get('divisions')}")
print(f"\nMeta buildVersion: {ncaa.get('meta', {}).get('buildVersion')}")
print(f"Teams Count: {len(ncaa.get('teams', []))}")

if ncaa.get('teams'):
    team = ncaa['teams'][0]
    print(f"\n--- First Team ({team.get('name')}) Structure ---")
    print(f"Team ID: {team.get('id')}")
    print(f"City: {team.get('city')}")
    print(f"Arena: {team.get('arenaName')}")
    print(f"Logo URL: {team.get('logoURL')}")
    print(f"Logo Size: {team.get('logoSize')}")
    print(f"\nTeam Colors: {team.get('teamColors')}")
    print(f"\nCourt keys: {list(team.get('court', {}).keys())}")
    print(f"Court structure:\n{json.dumps(team.get('court', {}), indent=2)}")
    
    print(f"\nFront Office keys: {list(team.get('frontOffice', {}).keys())}")
    print(f"Front Office structure:\n{json.dumps(team.get('frontOffice', {}), indent=2)[:500]}...")
    
    print(f"\nUniform count: {len(team.get('uniforms', []))}")
    if team.get('uniforms'):
        print(f"Uniform 0 keys: {list(team['uniforms'][0].keys())}")
        print(f"Uniform 0:\n{json.dumps(team['uniforms'][0], indent=2)}")
    
    if team.get('history'):
        print(f"\nHistory keys: {list(team.get('history', {}).keys())}")
    
    if team.get('championships'):
        print(f"\nChampionships structure:\n{json.dumps(team.get('championships', {}), indent=2)[:500]}...")

print("\n" + "=" * 80)
print("NBA TEMPLATE STRUCTURE (for comparison)")
print("=" * 80)
print(f"League Name: {nba.get('leagueName')}")
print(f"Short Name: {nba.get('shortName')}")
print(f"Logo URL: {nba.get('logoURL')}")
print(f"League Type: {nba.get('leagueType')}")
print(f"Teams Count: {len(nba.get('teams', []))}")

if nba.get('teams'):
    team = nba['teams'][0]
    print(f"\n--- First Team ({team.get('name')}) Structure ---")
    print(f"Court keys: {list(team.get('court', {}).keys())}")
    print(f"Front Office keys: {list(team.get('frontOffice', {}).keys())}")


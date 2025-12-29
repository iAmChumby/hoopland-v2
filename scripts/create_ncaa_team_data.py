"""Script to create NCAA team data JSON from glidej/ncaa-team-colors."""

import json
import requests

MULTI_WORD_MASCOTS = {
    'Crimson Tide', 'Golden Bears', 'Blue Devils', 'Yellow Jackets', 'Tar Heels',
    'Demon Deacons', 'Fighting Irish', 'Red Storm', 'Golden Eagles', 'Blue Hens',
    'Great Danes', 'Big Red', 'Big Green', 'Green Wave', 'Mean Green',
    'Red Raiders', 'Red Wolves', 'Golden Flashes', 'Golden Hurricane', 
    'Fighting Illini', 'Black Knights', 'Black Bears', 'Sun Devils', 
    'Golden Grizzlies', 'Golden Panthers', 'Blue Demons', 'Golden Lions',
    'Red Foxes', 'Blue Hose', 'Gold Rush', 'River Hawks', 'Sea Wolves',
    'Golden Suns', 'Crimson Hawks', 'Purple Aces', 'Golden Griffins',
}


def parse_team_name(full_name):
    for mascot in sorted(MULTI_WORD_MASCOTS, key=len, reverse=True):
        if full_name.endswith(mascot):
            school = full_name[:-len(mascot)].strip()
            return school, mascot
    parts = full_name.rsplit(' ', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return full_name, ''


def main():
    url = 'https://raw.githubusercontent.com/glidej/ncaa-team-colors/master/ncaa-team-colors.json'
    resp = requests.get(url)
    raw_teams = resp.json()
    print(f'Fetched {len(raw_teams)} teams')

    ncaa_data = {}
    for idx, team in enumerate(raw_teams):
        slug = team.get('slug', '').lower().replace(' ', '_')
        full_name = team.get('name', '')
        school, mascot = parse_team_name(full_name)
        
        colors = [c.replace('#', '') for c in team.get('colors', ['CC0000', 'FFFFFF', '000000'])]
        while len(colors) < 3:
            colors.append('000000')
        
        words = school.split()
        if len(words) >= 2:
            tag = ''.join([w[0] for w in words[:3]]).upper()
        else:
            tag = school[:3].upper()
        
        ncaa_data[slug] = {
            'target_id': idx + 1,
            'name': mascot,
            'school': school,
            'full_name': full_name,
            'tag': tag,
            'colors': colors[:3],
            'uuid': team.get('id', ''),
            'conference': '',
            'division': 0,
            'location': {'x': 0, 'y': 0}
        }

    with open('src/hoopland/data/ncaa_team_data.json', 'w') as f:
        json.dump(ncaa_data, f, indent=2)
    
    print(f'Saved {len(ncaa_data)} teams')
    
    samples = ['alabama_crimson_tide', 'duke_blue_devils', 'kentucky_wildcats', 'north_carolina_tar_heels']
    for s in samples:
        if s in ncaa_data:
            t = ncaa_data[s]
            print(f"{t['school']} {t['name']}: {t['tag']} - colors: {t['colors']}")


if __name__ == '__main__':
    main()

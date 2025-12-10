
import os
from ..models import structs
from ..data import repository
from ..db import init_db, Player
from ..cv import appearance
from ..stats import normalization
from dataclasses import asdict
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        # Initialize DB and Repo
        self.Session = init_db() 
        self.session = self.Session()
        self.repo = repository.DataRepository(self.session)

    def generate_league(self, year: str) -> structs.League:
        logger.info(f"Generating NBA league for year: {year}")
        print(f"Generating NBA {year}...")
        
        # 1. Sync Data (Performance Stats)
        season_str = self._year_to_season(year)
        try:
            self.repo.sync_nba_season_stats(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync stats: {e}")
        
        # 2. Sync Roster Metadata (Age, Ht, Wt, Pos, Country) - NEW
        try:
             self.repo.sync_nba_roster_data(season=season_str)
        except Exception as e:
             logger.error(f"Failed to sync roster metadata: {e}")

        # 3. Backfill Appearance
        logger.info("Backfilling appearance data...")
        try:
             self.repo.backfill_appearance(appearance.get_skin_tone)
        except Exception as e:
             logger.error(f"Failed to backfill appearance: {e}")
        
        # 4. Fetch Players form DB
        players = self.session.query(Player).filter_by(season=season_str, league='NBA').all()
        logger.info(f"Fetched {len(players)} players from database.")
        print(f"Fetched {len(players)} players.")
        
        # 5. Group by Team
        team_map = defaultdict(list)
        for p in players:
            team_map[p.team_id].append(p)
            
        # 6. Build Teams (Pure Logic, No API Calls)
        league_teams = []
        total_teams = len(team_map)
        current_team = 0
        
        print("Building Teams (Offline Mode)...")
        for tid, roster in team_map.items():
            current_team += 1
            if current_team % 5 == 0:
                print(f"Built {current_team}/{total_teams} teams...")
            
            # Get Team Info (could be cached too, but single dict lookup is fast usually)
            # The client usually scrapes on first load, so getting by ID from cache is fast.
            team_info = self.repo.nba_client.get_team_by_id(int(tid))
            city = team_info.get('city', 'Unknown') if team_info else "Unknown"
            name = team_info.get('nickname', f"Team {tid}") if team_info else f"Team {tid}"
            short_name = team_info.get('abbreviation', "TM") if team_info else "TM"

            # Helper Functions
            def parse_position(pos_str):
                if not pos_str: return 1
                p = str(pos_str).upper()
                if "C" in p: return 5
                if "F" in p: return 4 if "G" not in p else 3
                return 1 if "G" in p else 1

            def parse_height(h_str):
                try:
                    if not h_str or '-' not in str(h_str): return 72 
                    ft, inches = str(h_str).split('-')
                    return int(ft) * 12 + int(inches)
                except: return 72
            
            def parse_weight(w_str):
                try: return int(w_str)
                except: return 200

            def parse_country(c_str):
                # Map country string to ID
                if not c_str or c_str == 'USA': return 0
                return 1 # Generic International

            # Build Roster
            struct_roster = []
            for p in roster:
                raw_stats = p.raw_stats if p.raw_stats else {}
                ratings = normalization.StatsConverter.calculate_ratings(raw_stats)
                app_data = p.appearance if p.appearance else {}
                
                # Metadata from raw_stats (populated by sync_nba_roster_data)
                age = 0
                try:
                     age_val = raw_stats.get('ROSTER_AGE', raw_stats.get('AGE', 0))
                     age = int(float(age_val))
                except: pass

                ht_val = parse_height(raw_stats.get('ROSTER_HEIGHT', raw_stats.get('HEIGHT', '')))
                wt_val = parse_weight(raw_stats.get('ROSTER_WEIGHT', raw_stats.get('WEIGHT', '')))
                pos_val = parse_position(raw_stats.get('ROSTER_POSITION', raw_stats.get('POSITION', '')))
                ctry_val = parse_country(raw_stats.get('ROSTER_COUNTRY', 'USA'))
                
                # Potential
                pot_bonus = max(0, (28 - age) / 2) if age > 0 else 0
                avg_rating = sum(ratings.values()) / len(ratings) if ratings else 5
                pot_val = min(10, int(round(avg_rating + pot_bonus)))

                struct_player = structs.Player(
                    id=p.id, tid=int(tid),
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    age=age, ht=ht_val, wt=wt_val, pos=pos_val, ctry=ctry_val, pot=pot_val,
                    appearance=app_data.get('skin_tone', 1),
                    stats=raw_stats, attributes=ratings
                )
                struct_roster.append(struct_player)
            
            t = structs.Team(id=int(tid), city=city, name=name, shortName=short_name, roster=struct_roster)
            league_teams.append(t)

        return structs.League(
            leagueName=f"NBA {year}", shortName="NBA",
            settings=self._get_default_settings(), teams=league_teams,
            meta=structs.Meta(saveName=f"NBA {year} Season", dataType="League")
        )

    def generate_ncaa_league(self, year: str) -> structs.League:
        logger.info(f"Generating NCAA league for year: {year}")
        # Sync NCAA Data
        try:
             self.repo.sync_ncaa_season_stats(season=year)
        except Exception as e:
             logger.error(f"Failed to sync NCAA stats: {e}")

        # Fetch Players
        players = self.session.query(Player).filter_by(season=year, league='NCAA').all()
        
        team_map = defaultdict(list)
        for p in players:
            team_map[p.team_id].append(p)

        league_teams = []
        for tid, roster in team_map.items():
            # Basic Team Logic for NCAA
            struct_roster = []
            for p in roster:
                # Basic Player logic (similar to NBA but might have less data)
                struct_player = structs.Player(
                    id=p.id, tid=int(tid),
                    fn=p.name.split(" ")[0], ln=" ".join(p.name.split(" ")[1:]),
                    rating=5, pot=7 # Placeholder
                )
                struct_roster.append(struct_player)
            
            t = structs.Team(id=int(tid), city="College", name=f"Team {tid}", shortName=f"C{tid}", roster=struct_roster)
            league_teams.append(t)

        return structs.League(
            leagueName=f"NCAA {year}", shortName="NCAA",
            settings=self._get_default_settings(), teams=league_teams,
            meta=structs.Meta(saveName=f"NCAA {year}", dataType="League")
        )

    def generate_draft_class(self, year: str) -> structs.League:
        logger.info(f"Generating draft class for year: {year}")
        # Use NBA Draft History
        try:
            df = self.repo.nba_client.get_draft_history(league_id='00')
            # Filter by year
            df_year = df[df['SEASON'] == year]
        except Exception as e:
            logger.error(f"Failed to fetch draft history: {e}")
            df_year = None
        
        draft_players = []
        if df_year is not None:
             for _, row in df_year.iterrows():
                 p = structs.Player(
                     id=int(row['PERSON_ID']), tid=-1,
                     fn=row['PLAYER_NAME'].split(" ")[0], ln=" ".join(row['PLAYER_NAME'].split(" ")[1:]),
                     rating=6, pot=8 # Heuristic
                 )
                 draft_players.append(p)
                 
        return structs.League(
            leagueName=f"NBA {year} Draft",
            settings=self._get_default_settings(),
            teams=[], 
            meta=structs.Meta(saveName=f"{year} Draft Class", dataType="Draft Class")
        )

    def _year_to_season(self, year: str) -> str:
        try:
            y = int(year)
            return f"{y-1}-{str(y)[2:]}"
        except: return year

    def _get_default_settings(self) -> dict:
        return {"gameLength": 12, "difficulty": 2}

    def to_json(self, league_obj: structs.League, filename: str):
        try: year = league_obj.leagueName.split(" ")[1] 
        except: year = "unknown"
        output_dir = os.path.join("output", year)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        data = asdict(league_obj)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

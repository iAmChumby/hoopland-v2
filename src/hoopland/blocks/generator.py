
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
        logger.info(f"Generating league for year: {year}")
        
        # 1. Sync Data
        season_str = self._year_to_season(year)
        logger.info(f"Syncing stats for season {season_str}...")
        try:
            self.repo.sync_nba_season_stats(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync stats: {e}")
            # Continue with existing data if possible
        
        # 2. Backfill Appearance
        logger.info("Backfilling appearance data...")
        try:
             self.repo.backfill_appearance(appearance.get_skin_tone)
        except Exception as e:
             logger.error(f"Failed to backfill appearance: {e}")
        
        # 3. Fetch Players form DB
        players = self.session.query(Player).filter_by(season=season_str, league='NBA').all()
        
        # 4. Group by Team
        team_map = defaultdict(list)
        for p in players:
            team_map[p.team_id].append(p)
            
        # 5. Build Teams
        league_teams = []
        for tid, roster in team_map.items():
            # Get Team Info
            # Attempt to fetch team details using the NBA client in repo
            team_info = self.repo.nba_client.get_team_by_id(int(tid))
            city = "Unknown"
            name = f"Team {tid}"
            short_name = "TM"
            
            if team_info:
                 city = team_info.get('city', 'Unknown')
                 name = team_info.get('nickname', f"Team {tid}")
                 short_name = team_info.get('abbreviation', "TM")

            # Use roster to build detailed player objects
            struct_roster = []
            for p in roster:
                # Calculate ratings
                raw_stats = p.raw_stats if p.raw_stats else {}
                ratings = normalization.StatsConverter.calculate_ratings(raw_stats)
                
                # Fetch appearance cache
                app_data = p.appearance if p.appearance else {}
                
                # Safely parse stats
                struct_player = structs.Player(
                    id=p.id, # Internal DB ID
                    tid=int(tid),
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    appearance=app_data.get('skin_tone', 1),
                    stats=raw_stats,
                    attributes=ratings # Need to map to specific schema keys if strict
                )
                struct_roster.append(struct_player)
            
            # Create Team Struct
            t = structs.Team(
                id=int(tid),
                city=city,
                name=name,
                shortName=short_name,
                roster=struct_roster
            )
            league_teams.append(t)

        # 6. Create League
        league = structs.League(
            leagueName=f"NBA {year}",
            shortName="NBA",
            settings=self._get_default_settings(),
            teams=league_teams,
            meta=structs.Meta(
                saveName=f"NBA {year} Season",
                dataType="League"
            )
        )
        
        return league

    def generate_draft_class(self, year: str) -> structs.League:
        """
        Generates a Draft Class for the given year.
        Integration with ESPN client or Drafthistory endpoint needed here.
        For now, we'll keep the placeholder but ensure file structure works.
        """
        logger.info(f"Generating draft class for year: {year}")
        
        league = structs.League(
            leagueName=f"NBA {year} Draft",
            settings=self._get_default_settings(),
            meta=structs.Meta(
                saveName=f"{year} Draft Class",
                dataType="Draft Class"
            )
        )
        return league

    def _year_to_season(self, year: str) -> str:
        # 2024 -> 2023-24
        try:
            y = int(year)
            prev = y - 1
            return f"{prev}-{str(y)[2:]}"
        except:
            return year # Fallback if invalid format

    def _get_default_settings(self) -> dict:
        return {
            "gameLength": 12,
            "difficulty": 2,
        }

    def to_json(self, league_obj: structs.League, filename: str):
        # Handle Output Directory
        # Extract year from league name "NBA 2003" -> "2003"
        try:
             year = league_obj.leagueName.split(" ")[1] 
        except:
             year = "unknown"
             
        output_dir = os.path.join("output", year)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        data = asdict(league_obj)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

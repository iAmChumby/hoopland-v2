from sqlalchemy.orm import Session
from ..db import Player, init_db
from .nba_client import NBAClient

from .espn_client import ESPNClient
import json
import logging

logger = logging.getLogger(__name__)

class DataRepository:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.nba_client = NBAClient()
        self.espn_client = ESPNClient()

    def get_player(self, source_id, league='NBA', season='2023-24'):
        # Check DB first
        player = self.session.query(Player).filter_by(source_id=str(source_id), league=league, season=season).first()
        if player:
            return player

        # Fetch from API
        if league == 'NBA':
            # This is tricky because NBA API fetches lists, not single players easily by ID for stats
            # Implementation detail: we might need to fetch the whole league and cache it, 
            # or just fetch the roster. 
            # For this MVP, let's assume we are calling this as part of a bulk load or we implement a fetch.
            pass
        elif league == 'NCAA':
            pass
            
        return None


    def sync_nba_season_stats(self, season='2023-24'):
        """
        Fetches all NBA player stats for the season and updates the DB.
        """
        logger.info(f"Fetching NBA league stats for season {season}")
        try:
            df = self.nba_client.get_league_stats(season=season)
        except Exception as e:
            logger.error(f"Failed to fetch league stats from NBA API: {e}")
            raise

        count = 0
        new_count = 0
        logger.info(f"Processing {len(df)} players from API...")
        
        for index, row in df.iterrows():
            player_id = str(row['PLAYER_ID'])
            player = self.session.query(Player).filter_by(source_id=player_id, league='NBA', season=season).first()
            
            raw_stats = row.to_json()
            
            if not player:
                player = Player(
                    source_id=player_id,
                    league='NBA',
                    season=season,
                    name=row['PLAYER_NAME'],
                    team_id=str(row['TEAM_ID']),
                    raw_stats=json.loads(raw_stats),
                    appearance={}
                )
                self.session.add(player)
            else:
                player.raw_stats = json.loads(raw_stats)
                # update other fields if needed
            count += 1
        
        self.session.commit()
        logger.info(f"Sync complete. Processed {count} players. Added {new_count} new players.")
    
    def backfill_appearance(self, cv_engine_func):
        """
        Iterates over players with missing appearance data and fills it.
        """
        # Filter in python to be safe against DB JSON quirks
        all_players = self.session.query(Player).all()
        players = [p for p in all_players if not p.appearance or 'skin_tone' not in p.appearance]
        
        logger.info(f"Found {len(players)} players missing appearance data.")
        for p in players:
            try:
                if p.league == 'NBA':
                    url = self.nba_client.fetch_player_headshot_url(p.source_id)
                    skin_tone = cv_engine_func(url)
                    p.appearance = {'skin_tone': skin_tone}
                    self.session.commit() # Commit proactively or batch it
                    logger.debug(f"Backfilled appearance for player {p.name}: {skin_tone}")
            except Exception as e:
                logger.error(f"Error backfilling appearance for player {p.name}: {e}")

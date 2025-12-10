from .data.repository import DataRepository
from .db import init_db
from .stats.normalization import StatsConverter
from .cv.appearance import get_skin_tone
import json

def refresh_nba_data():
    """
    Main workflow to sync NBA data and process it.
    """
    Session = init_db()
    session = Session()
    repo = DataRepository(session)
    
    print("Syncing NBA season stats...")
    repo.sync_nba_season_stats()
    
    print("Backfilling appearance data...")
    repo.backfill_appearance(get_skin_tone)
    
    print("Data sync complete.")
    session.close()

def export_player_json(player_name):
    """
    Queries DB and generates Hoop Land JSON format.
    """
    Session = init_db()
    session = Session()
    # Simple query by name for demo
    from .db import Player
    player = session.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
    
    if not player:
        print(f"Player {player_name} not found.")
        return
        
    ratings = StatsConverter.calculate_ratings(player.raw_stats)
    
    output = {
        "name": player.name,
        "team": player.team_id,
        "appearance": player.appearance,
        "attributes": ratings
    }
    
    print(json.dumps(output, indent=2))
    session.close()

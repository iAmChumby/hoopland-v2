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

    def get_player(self, source_id, league="NBA", season="2023-24"):
        # Check DB first
        player = (
            self.session.query(Player)
            .filter_by(source_id=str(source_id), league=league, season=season)
            .first()
        )
        if player:
            return player
        return None

    def sync_ncaa_season_stats(self, season="2023"):
        import time

        logger.info(f"Syncing NCAA stats for {season}...")
        print(f"Syncing NCAA stats for {season}...")

        # 1. Fetch Teams
        teams = self.espn_client.get_all_teams()
        logger.info(f"Found {len(teams)} NCAA teams.")
        print(f"Found {len(teams)} NCAA teams.")

        current = 0
        total = len(teams)

        for team in teams:
            current += 1
            tid = team.get("id")
            slug = team.get("slug", tid)
            name = team.get("displayName", "Unknown")

            # Optimization: Check existing
            # We can check if any player exists for this team/season
            exists = (
                self.session.query(Player)
                .filter_by(team_id=str(tid), season=season, league="NCAA")
                .first()
            )
            if exists:
                if current % 10 == 0:
                    print(f"Skipping NCAA Team {current}/{total} (Data exists)...")
                continue

            print(f"Syncing NCAA Team {current}/{total}: {name}...")

            try:
                time.sleep(0.5)  # Politeness
                roster_data = self.espn_client.get_team_roster(
                    tid
                )  # Using ID preferred
                if not roster_data or "athletes" not in roster_data:
                    continue

                # ESPN API structure for roster:
                # { "team": {...}, "athletes": [ { "id": "...", "fullName": "...", ... } ] }
                # Note: The 'athletes' structure usually contains 'items' or is a list itself depending on endpoint version.
                # Inspecting espn_client.py, it calls /roster.
                # We need to handle the response safely.

                athletes = roster_data.get("athletes", [])
                # Sometimes it's nested like athletes:[ {items: []} ] or just athletes:[]
                # Let's assume list of dicts for now based on typical ESPN V2 API.

                for ath in athletes:
                    # Athlete fields: id, fullName, height, weight, position, birthPlace
                    player_id = str(ath.get("id"))
                    p_name = ath.get("fullName", "Unknown")

                    p = (
                        self.session.query(Player)
                        .filter_by(source_id=player_id, league="NCAA", season=season)
                        .first()
                    )

                    # Convert stats/metadata
                    raw_dump = ath  # Store full object

                    if not p:
                        p = Player(
                            source_id=player_id,
                            league="NCAA",
                            season=season,
                            name=p_name,
                            team_id=str(tid),
                            raw_stats=raw_dump,
                            appearance={},
                        )
                        self.session.add(p)
                    else:
                        p.raw_stats = raw_dump

                self.session.commit()

            except Exception as e:
                logger.error(f"Failed to sync NCAA team {name}: {e}")
                self.session.rollback()

    def sync_nba_season_stats(self, season="2023-24"):
        """
        Fetches all NBA player stats for the season and updates the DB.
        Always fetches if season data is missing or incomplete.
        """
        # Check if data already exists
        existing_count = (
            self.session.query(Player).filter_by(season=season, league="NBA").count()
        )
        
        if existing_count > 400:
            logger.info(
                f"Season {season} already cached ({existing_count} players). Skipping fetch."
            )
            return
        
        # New season or incomplete data - fetch from API
        logger.info(f"Fetching NBA season {season} from API (not in cache)...")

        try:
            df = self.nba_client.get_league_stats(season=season)
        except Exception as e:
            logger.error(f"Failed to fetch season {season} from NBA API: {e}")
            raise

        total = len(df)
        if total == 0:
            logger.warning(f"NBA API returned 0 players for season {season}")
            return
            
        logger.info(f"Processing {total} players for season {season}...")
        
        count = 0
        for index, row in df.iterrows():
            if index % 100 == 0 and index > 0:
                logger.info(f"Processed {index}/{total} players for {season}...")

            player_id = str(row["PLAYER_ID"])
            player = (
                self.session.query(Player)
                .filter_by(source_id=player_id, league="NBA", season=season)
                .first()
            )

            raw_stats = row.to_json()

            if not player:
                player = Player(
                    source_id=player_id,
                    league="NBA",
                    season=season,
                    name=row["PLAYER_NAME"],
                    team_id=str(row["TEAM_ID"]),
                    raw_stats=json.loads(raw_stats),
                    appearance={},
                )
                self.session.add(player)
            else:
                player.raw_stats = json.loads(raw_stats)
                # update other fields if needed
            count += 1

        self.session.commit()
        logger.info(
            f"Season {season} sync complete: {count} players stored in database."
        )

    def sync_nba_roster_data(self, season="2023-24"):
        """
        Fetches roster data (Age, Height, Weight, Pos, Country) for all teams and merges into player.raw_stats.
        """
        import time

        logger.info(f"Syncing NBA roster metadata for {season}...")

        # 1. Get unique Team IDs from existing players
        players = (
            self.session.query(Player).filter_by(season=season, league="NBA").all()
        )
        team_ids = set()
        for p in players:
            if p.team_id:
                team_ids.add(p.team_id)

        total_teams = len(team_ids)
        logger.info(f"Found {total_teams} teams to sync rosters for season {season}.")

        current = 0
        for tid in team_ids:
            current += 1

            # Optimization: Check if data already exists for at least one player on this team
            sample_p = (
                self.session.query(Player)
                .filter_by(team_id=str(tid), season=season, league="NBA")
                .first()
            )
            if sample_p and sample_p.raw_stats and "ROSTER_POS" in sample_p.raw_stats:
                # Using ROSTER_POS as a marker that sync happened
                continue

            logger.info(f"Syncing roster {current}/{total_teams} (Team {tid})...")
            try:
                # Rate Limit Protection
                time.sleep(1.0)

                # Fetch Roster
                roster_df = self.nba_client.get_roster(team_id=int(tid), season=season)

                # Check for Country Key (Debug once)
                if current == 1 and not roster_df.empty:
                    keys = roster_df.columns.tolist()
                    logger.info(f"Roster Keys: {keys}")

                # Update Players
                for _, row in roster_df.iterrows():
                    pid = str(row["PLAYER_ID"])
                    # Find player in DB
                    p = (
                        self.session.query(Player)
                        .filter_by(source_id=pid, season=season, league="NBA")
                        .first()
                    )
                    if p:
                        # Merge metadata into raw_stats
                        meta = row.to_dict()
                        current_stats = p.raw_stats if p.raw_stats else {}

                        current_stats["ROSTER_AGE"] = meta.get("AGE")
                        current_stats["ROSTER_HEIGHT"] = meta.get("HEIGHT")
                        current_stats["ROSTER_WEIGHT"] = meta.get("WEIGHT")
                        current_stats["ROSTER_POSITION"] = meta.get("POSITION")
                        # Use ROSTER_POS as a completion marker
                        current_stats["ROSTER_POS"] = meta.get("POSITION")
                        current_stats["ROSTER_COUNTRY"] = meta.get(
                            "BIRTH_COUNTRY", meta.get("COUNTRY", "USA")
                        )
                        current_stats["ROSTER_SCHOOL"] = meta.get("SCHOOL", "")

                        p.raw_stats = current_stats

                self.session.commit()

            except Exception as e:
                self.session.rollback()

        logger.info(f"Roster metadata sync complete for {season}.")

    def backfill_appearance(self, cv_engine_func):
        """
        Iterates over players with missing appearance data and fills it.
        """
        # Filter in python to be safe against DB JSON quirks
        all_players = self.session.query(Player).all()
        players = [
            p
            for p in all_players
            if not p.appearance or "skin_tone" not in p.appearance
        ]

        logger.info(f"Found {len(players)} players missing appearance data.")
        # print(f"Backfilling appearance for {len(players)} players...")

        for p in players:
            try:
                if p.league == "NBA":
                    url = self.nba_client.fetch_player_headshot_url(p.source_id)
                    # Returns dict {'skin_tone', 'hair', 'facial_hair'} by convention now
                    appearance_data = cv_engine_func(url)

                    # Ensure compatibility if func returns just int (legacy)
                    if isinstance(appearance_data, int):
                        appearance_data = {"skin_tone": appearance_data}

                    p.appearance = appearance_data
                    self.session.commit()
                    logger.debug(
                        f"Backfilled appearance for player {p.name}: {appearance_data}"
                    )
            except Exception as e:
                logger.error(f"Error backfilling appearance for player {p.name}: {e}")

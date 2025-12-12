import os
from ..models import structs
from ..data import repository
from ..db import init_db, Player
from ..cv import appearance
from ..stats import normalization, tendencies
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
            # Use advanced appearance analysis (Skin, Hair, Facial Hair)
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, season=season_str, league="NBA"
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # 4. Fetch Players form DB
        players = (
            self.session.query(Player).filter_by(season=season_str, league="NBA").all()
        )
        logger.info(f"Fetched {len(players)} players from database.")
        print(f"Fetched {len(players)} players.")

        # 5. Group by Team
        team_map = defaultdict(list)
        
        # [NEW] Calculate League Distribution for Tendencies
        print("Calculating league stat distribution...")
        # Check if p is SQL Model or Struct. Line 51 says "fetched form database", so it's SQL Model.
        # DB Model usually has .raw_stats attribute.
        all_raw_stats_dicts = [p.raw_stats if p.raw_stats else {} for p in players]
        
        # We need derived stats for distribution
        all_derived = []
        for raw in all_raw_stats_dicts:
            # Need height for derived stats (dunk score)
            h_str = raw.get("ROSTER_HEIGHT", raw.get("HEIGHT", ""))
            # Need to parse height here or inside loop? 
            # Helper function parse_height is strictly defined inside loop currently.
            # Let's extract parsing logic or duplicate briefly for this pre-pass.
            # Simplified height parse for distribution
            ht = 75
            try:
                if h_str and "-" in str(h_str):
                    f, i = str(h_str).split("-")
                    ht = int(f)*12 + int(i)
            except: pass
            
            all_derived.append(tendencies.calculate_derived_stats(raw, height=ht))
            
        distribution = tendencies.calculate_distribution(all_derived)

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
            city = team_info.get("city", "Unknown") if team_info else "Unknown"
            name = (
                team_info.get("nickname", f"Team {tid}") if team_info else f"Team {tid}"
            )
            short_name = team_info.get("abbreviation", "TM") if team_info else "TM"

            # Helper Functions
            def parse_position(pos_str):
                if not pos_str:
                    return 1
                p = str(pos_str).upper()
                if "C" in p:
                    return 5
                if "F" in p:
                    return 4 if "G" not in p else 3
                return 1 if "G" in p else 1

            def parse_height(h_str):
                try:
                    if not h_str or "-" not in str(h_str):
                        return 72
                    ft, inches = str(h_str).split("-")
                    return int(ft) * 12 + int(inches)
                except:
                    return 72

            def parse_weight(w_str):
                try:
                    return int(w_str)
                except:
                    return 200

            def parse_country(c_str):
                # Map country string to ID
                if not c_str or c_str == "USA":
                    return 0
                return 1  # Generic International

            # Build Roster
            struct_roster = []
            for p in roster:
                raw_stats = p.raw_stats if p.raw_stats else {}
                ratings = normalization.StatsConverter.calculate_ratings(raw_stats)
                app_data = p.appearance if p.appearance else {}

                # Metadata from raw_stats (populated by sync_nba_roster_data)
                age = 0
                try:
                    age_val = raw_stats.get("ROSTER_AGE", raw_stats.get("AGE", 0))
                    age = int(float(age_val))
                except:
                    pass

                ht_val = parse_height(
                    raw_stats.get("ROSTER_HEIGHT", raw_stats.get("HEIGHT", ""))
                )
                wt_val = parse_weight(
                    raw_stats.get("ROSTER_WEIGHT", raw_stats.get("WEIGHT", ""))
                )
                pos_val = parse_position(
                    raw_stats.get("ROSTER_POSITION", raw_stats.get("POSITION", ""))
                )
                ctry_val = parse_country(raw_stats.get("ROSTER_COUNTRY", "USA"))

                # Potential
                pot_bonus = max(0, (28 - age) / 2) if age > 0 else 0
                avg_rating = sum(ratings.values()) / len(ratings) if ratings else 5
                # Boost potential: Base + Bonus + 2 (Skew), Min 5 (2.5 stars)
                pot_val = min(10, max(5, int(round(avg_rating + pot_bonus + 2))))

                # Appearance & Accessories
                skin_val = app_data.get("skin_tone", 1)
                hair_val = app_data.get("hair", 0)
                beard_val = app_data.get("facial_hair", 0)

                # Map to Struct
                acc_dict = {"hair": hair_val, "beard": beard_val}

                # Tendencies
                tends = tendencies.generate_player_tendencies(
                    stats=raw_stats,
                    height=ht_val,
                    position=pos_val,
                    distribution=distribution
                )

                struct_player = structs.Player(
                    id=p.id,
                    tid=int(tid),
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    age=age,
                    ht=ht_val,
                    wt=wt_val,
                    pos=pos_val,
                    ctry=ctry_val,
                    pot=pot_val,
                    appearance=skin_val,
                    accessories=acc_dict,
                    stats=raw_stats,
                    attributes=ratings,
                    tendencies=tends
                )
                struct_roster.append(struct_player)

            t = structs.Team(
                id=int(tid),
                city=city,
                name=name,
                shortName=short_name,
                roster=struct_roster,
            )
            league_teams.append(t)

        return structs.League(
            leagueName=f"NBA {year}",
            shortName="NBA",
            settings=self._get_default_settings(),
            teams=league_teams,
            meta=structs.Meta(saveName=f"NBA {year} Season", dataType="League"),
        )

    def generate_ncaa_league(self, year: str, tournament_mode: bool = False) -> structs.League:
        mode_str = "Tournament (64 teams)" if tournament_mode else "Full"
        logger.info(f"Generating NCAA league for year: {year} [{mode_str}]")

        # 1. Sync NCAA Data (pass tournament mode for filtering)
        team_ids = []
        try:
            team_ids = self.repo.sync_ncaa_season_stats(season=year, tournament_only=tournament_mode)
        except Exception as e:
            logger.error(f"Failed to sync NCAA stats: {e}")

        # 2. Backfill Appearance
        logger.info("Backfilling appearance data for NCAA players...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, 
                season=year, 
                league="NCAA",
                team_ids=team_ids if tournament_mode else None
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # 3. Fetch Players from DB
        query = self.session.query(Player).filter_by(season=year, league="NCAA")
        if tournament_mode and team_ids:
            query = query.filter(Player.team_id.in_(team_ids))
        players = query.all()
        logger.info(f"Fetched {len(players)} NCAA players from database.")

        # 4. Group by Team
        team_map = defaultdict(list)
        for p in players:
            team_map[p.team_id].append(p)

        # Helper functions
        def parse_height(h_str):
            """Convert height string like '6' 9"' to inches"""
            try:
                if not h_str:
                    return 72
                # Handle formats: "6' 9\"", "6-9", etc.
                h_str = str(h_str).replace('"', '').replace("'", '-')
                if '-' in h_str:
                    parts = h_str.split('-')
                    ft = int(parts[0].strip())
                    inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                    return ft * 12 + inches
                return 72
            except:
                return 72

        def parse_weight(w_str):
            """Convert weight string like '250 lbs' to int"""
            try:
                if not w_str:
                    return 200
                return int(str(w_str).split()[0])
            except:
                return 200

        def parse_position(pos_data):
            """Convert position to int (1-5)"""
            if not pos_data:
                return 3
            abbrev = pos_data.get("abbreviation", "") if isinstance(pos_data, dict) else str(pos_data)
            abbrev = abbrev.upper()
            if "C" in abbrev:
                return 5
            if "F" in abbrev:
                return 4
            if "G" in abbrev:
                return 1 if "PG" in abbrev else 2
            return 3

        # 5. Build Teams
        league_teams = []
        total_teams = len(team_map)
        current_team = 0

        # Fetch Team Metadata for Naming (Optimized: Get all once)
        tid_to_meta = {}
        try:
            logger.info("Fetching NCAA team metadata for naming...")
            all_teams = self.repo.espn_client.get_all_teams()
            for t in all_teams:
                tid = str(t.get("id"))
                tid_to_meta[tid] = {
                    "name": t.get("displayName", f"Team {tid}"),
                    "shortName": t.get("abbreviation", f"T{tid[-3:]}")
                }
        except Exception as e:
            logger.warning(f"Could not fetch team metadata: {e}")

        for tid, roster in team_map.items():
            current_team += 1
            if current_team % 50 == 0:
                logger.info(f"Building team {current_team}/{total_teams}...")

            # Get team name from metadata map
            tid_str = str(tid)
            meta = tid_to_meta.get(tid_str, {})
            team_name = meta.get("name", f"Team {tid}")
            team_abbrev = meta.get("shortName", f"T{str(tid)[-3:]}")

            # Build roster
            struct_roster = []
            for p in roster:
                raw = p.raw_stats if p.raw_stats else {}
                app_data = p.appearance if p.appearance else {}

                # Parse player metadata from ESPN data
                ht_val = parse_height(raw.get("displayHeight"))
                wt_val = parse_weight(raw.get("displayWeight"))
                pos_val = parse_position(raw.get("position"))

                # Appearance & Accessories
                skin_val = app_data.get("skin_tone", 1)
                hair_val = app_data.get("hair", 0)
                beard_val = app_data.get("facial_hair", 0)
                acc_dict = {"hair": hair_val, "beard": beard_val}

                # Default ratings for NCAA (college players)
                rating_val = 5
                pot_val = 7

                struct_player = structs.Player(
                    id=p.id,
                    tid=int(tid),
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    age=20,
                    ht=ht_val,
                    wt=wt_val,
                    pos=pos_val,
                    ctry=0,
                    rating=rating_val,
                    pot=pot_val,
                    appearance=skin_val,
                    accessories=acc_dict,
                )
                struct_roster.append(struct_player)

            t = structs.Team(
                id=int(tid),
                city="", # NCAA teams typically use the school name as the "city" equivalent or full name
                name=team_name,
                shortName=team_abbrev,
                roster=struct_roster,
            )
            league_teams.append(t)

        logger.info(f"NCAA league generation complete: {len(league_teams)} teams, {len(players)} players")

        return structs.League(
            leagueName=f"NCAA {year}",
            shortName="NCAA",
            settings=self._get_default_settings(),
            teams=league_teams,
            meta=structs.Meta(saveName=f"NCAA {year}", dataType="League"),
        )

    def generate_draft_class(self, year: str) -> structs.League:
        logger.info(f"Generating draft class for year: {year}")

        # Use NBA Draft History
        try:
            logger.info(f"Fetching draft history for {year}...")
            df = self.repo.nba_client.get_draft_history(
                league_id="00", season_year=year
            )

            # Additional safety filter if API ignores arg
            df_year = df
            if "SEASON" in df.columns:
                df_year = df[df["SEASON"] == year]

            logger.info(f"Found {len(df_year)} draft picks for {year}.")
        except Exception as e:
            logger.error(f"Failed to fetch draft history: {e}")
            df_year = None

        if df_year is None or len(df_year) == 0:
            logger.warning(f"No draft data found for {year}")
            return structs.League(
                leagueName=f"NBA {year} Draft Class",
                shortName="Draft",
                teams=[],
                meta=structs.Meta(saveName=f"{year} Draft Class", dataType="Draft Class"),
            )

        # Store draft picks in database for caching
        draft_season = f"draft-{year}"
        import time

        for i, row in df_year.iterrows():
            pid = str(row["PERSON_ID"])
            p_name = row["PLAYER_NAME"]

            # Check if already in DB
            existing = (
                self.session.query(Player)
                .filter_by(source_id=pid, season=draft_season, league="NBA")
                .first()
            )
            if existing:
                continue

            # Create new player entry
            player = Player(
                source_id=pid,
                league="NBA",
                season=draft_season,
                name=p_name,
                team_id="-1",  # Draft class team
                raw_stats={
                    "PERSON_ID": int(row["PERSON_ID"]),
                    "PLAYER_NAME": p_name,
                    "OVERALL_PICK": int(row["OVERALL_PICK"]),
                    "ROUND_NUMBER": int(row["ROUND_NUMBER"]) if "ROUND_NUMBER" in row else 1,
                    "DRAFT_YEAR": year,
                },
                appearance={},
            )
            self.session.add(player)

        self.session.commit()
        logger.info(f"Stored draft picks in database for season {draft_season}")

        # Fetch player career stats and metadata (for potential/ratings calculation)
        players = (
            self.session.query(Player)
            .filter_by(season=draft_season, league="NBA")
            .all()
        )

        logger.info(f"Processing {len(players)} draft picks for stats and appearance...")

        for i, p in enumerate(players):
            raw = p.raw_stats if p.raw_stats else {}
            pid = int(p.source_id)
            pick = raw.get("OVERALL_PICK", 60)

            # Skip if already has career stats
            if "CAREER_EFF" in raw:
                continue

            if i % 10 == 0:
                logger.info(f"Processing draft pick {i+1}/{len(players)}...")

            time.sleep(0.8)  # Rate limiting

            try:
                stats_data = self.repo.nba_client.get_player_career_stats(pid)
                career_df = stats_data.get("career_totals")
                season_df = stats_data.get("season_totals")

                # Calculate efficiency from career
                eff = 0
                gp = 0
                if career_df is not None and not career_df.empty:
                    pts = career_df["PTS"].sum()
                    reb = career_df["REB"].sum()
                    ast = career_df["AST"].sum()
                    stl = career_df["STL"].sum() if "STL" in career_df else 0
                    blk = career_df["BLK"].sum() if "BLK" in career_df else 0
                    gp = career_df["GP"].sum()
                    if gp > 0:
                        eff = (pts + 1.2 * reb + 1.5 * ast + 2 * stl + 2 * blk) / gp

                raw["CAREER_GP"] = int(gp)
                raw["CAREER_EFF"] = round(eff, 2)

                # Rookie season stats for attributes
                if season_df is not None and not season_df.empty:
                    rookie = season_df.iloc[0]
                    rgp = rookie["GP"]
                    if rgp > 0:
                        raw["ROOKIE_PPG"] = round(rookie["PTS"] / rgp, 1)
                        raw["ROOKIE_RPG"] = round(rookie["REB"] / rgp, 1)
                        raw["ROOKIE_APG"] = round(rookie["AST"] / rgp, 1)
                        raw["ROOKIE_SPG"] = round(rookie["STL"] / rgp, 1)
                        raw["ROOKIE_BPG"] = round(rookie["BLK"] / rgp, 1)

                p.raw_stats = raw
                self.session.commit()

            except Exception as e:
                logger.debug(f"Stats not available for {p.name}: {e}")

        # Backfill appearance data for draft picks
        logger.info("Backfilling appearance data for draft picks...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, season=draft_season, league="NBA"
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # Refresh players from DB
        players = (
            self.session.query(Player)
            .filter_by(season=draft_season, league="NBA")
            .filter_by(season=draft_season, league="NBA")
            .all()
        )
        
        # Calculate Distribution for Draft Class (Using their own stats? Or NBA Standards?)
        # Draft prospects have college/international stats, so distributions might differ from NBA.
        # But we want to map them to NBA tendencies. 
        # Ideally we compare them to NBA distribution, but we don't have that loaded here easily unless we passed it.
        # For now, let's self-reference the draft class distribution to find relative strengths.
        all_raw_stats_dicts = [p.raw_stats if p.raw_stats else {} for p in players]
        all_derived = []
        for raw in all_raw_stats_dicts:
            # Draft picks have default height 78 in Loop below?
            # Actually line 565 hardcodes ht=78.
            # Let's use 78 for now.
            all_derived.append(tendencies.calculate_derived_stats(raw, height=78))
        distribution = tendencies.calculate_distribution(all_derived)

        # Build draft class output
        draft_players = []
        for p in players:
            raw = p.raw_stats if p.raw_stats else {}
            app_data = p.appearance if p.appearance else {}
            pick = raw.get("OVERALL_PICK", 60)
            gp = raw.get("CAREER_GP", 0)
            eff = raw.get("CAREER_EFF", 0)

            # Calculate potential from career performance
            # Calculate potential from career performance
            if gp > 0:
                # Skewed thresholds for generous potential
                if eff > 26:        # Was 35
                    pot_val = 10
                elif eff > 20:      # Was 25
                    pot_val = 9
                elif eff > 16:      # Was 20
                    pot_val = 8
                elif eff > 12:      # Was 15
                    pot_val = 7
                elif eff > 8:       # Was 10
                    pot_val = 6
                elif eff > 4:       # Was 5
                    pot_val = 5
                elif gp > 100:
                    pot_val = 4
                else:
                    pot_val = 4     # Bumped min from 3 to 4
            else:
                # Fallback based on pick
                if pick <= 5:
                    pot_val = 9
                elif pick <= 15:
                    pot_val = 7
                elif pick <= 30:
                    pot_val = 6
                else:
                    pot_val = 5

            # Calculate attributes from rookie stats
            attrs = {k: 3 for k in [
                "shooting_inside", "shooting_mid", "shooting_3pt",
                "defense", "rebounding", "passing"
            ]}
            if "ROOKIE_PPG" in raw:
                ppg = raw["ROOKIE_PPG"]
                rpg = raw.get("ROOKIE_RPG", 0)
                apg = raw.get("ROOKIE_APG", 0)
                spg = raw.get("ROOKIE_SPG", 0)
                bpg = raw.get("ROOKIE_BPG", 0)

                attrs["shooting_inside"] = min(10, int(ppg / 2.5))
                attrs["shooting_mid"] = min(10, int(ppg / 3.0))
                attrs["shooting_3pt"] = min(10, int(ppg / 4.0))
                attrs["defense"] = min(10, int((spg + bpg) * 3))
                attrs["rebounding"] = min(10, int(rpg * 1.5))
                attrs["passing"] = min(10, int(apg * 2.0))

            avg_attr = sum(attrs.values()) / 6
            rating_val = max(1, int(avg_attr))

            # Appearance data
            skin_val = app_data.get("skin_tone", 1)
            hair_val = app_data.get("hair", 0)
            beard_val = app_data.get("facial_hair", 0)
            acc_dict = {"hair": hair_val, "beard": beard_val}

            # Tendencies
            tends = tendencies.generate_player_tendencies(
                stats=raw,
                height=78, # Hardcoded in loop below
                position=3, # Hardcoded below
                distribution=distribution
            )

            draft_player = structs.Player(
                id=int(p.source_id),
                tid=-1,
                fn=p.name.split(" ")[0] if " " in p.name else p.name,
                ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                age=20,
                ht=78,
                wt=210,
                pos=3,
                ctry=0,
                rating=rating_val,
                pot=pot_val,
                appearance=skin_val,
                accessories=acc_dict,
                attributes=attrs,
                tendencies=tends
            )
            draft_players.append(draft_player)

        # Sort by pick order
        draft_players.sort(key=lambda x: x.id)

        draft_team = structs.Team(
            id=-1, city="Draft", name="Class", shortName="DRF", roster=draft_players
        )

        logger.info(f"Draft class generation complete: {len(draft_players)} players")

        return structs.League(
            leagueName=f"NBA {year} Draft Class",
            shortName="Draft",
            settings=self._get_default_settings(),
            teams=[draft_team],
            meta=structs.Meta(saveName=f"{year} Draft Class", dataType="Draft Class"),
        )

    def _year_to_season(self, year: str) -> str:
        try:
            y = int(year)
            return f"{y - 1}-{str(y)[2:]}"
        except:
            return year

    def _get_default_settings(self) -> dict:
        return {"gameLength": 12, "difficulty": 2}

    def to_json(self, league_obj: structs.League, filename: str):
        try:
            year = league_obj.leagueName.split(" ")[1]
        except:
            year = "unknown"
        output_dir = os.path.join("output", year)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        data = asdict(league_obj)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

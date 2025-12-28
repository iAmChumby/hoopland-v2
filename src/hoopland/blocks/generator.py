"""
League generation module for Hoopland.

Generates NBA, NCAA, and draft class data with full target schema compliance.
"""

import os
import json
import time
import logging
from collections import defaultdict
from dataclasses import asdict

from ..models import structs
from ..data import repository
from ..db import init_db, Player
from ..cv import appearance
from ..stats import normalization, tendencies
from .formatter import save_compact_json
from . import team_assets

logger = logging.getLogger(__name__)


class Generator:
    def __init__(self):
        self.Session = init_db()
        self.session = self.Session()
        self.repo = repository.DataRepository(self.session)

    def generate_league(self, year: str) -> structs.League:
        """Generate NBA league data for a specific year."""
        logger.info(f"Generating NBA league for year: {year}")
        print(f"Generating NBA {year}...")

        # 1. Sync Data (Performance Stats)
        season_str = self._year_to_season(year)
        try:
            self.repo.sync_nba_season_stats(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync stats: {e}")

        # 2. Sync Roster Metadata (Age, Ht, Wt, Pos, Country)
        try:
            self.repo.sync_nba_roster_data(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync roster metadata: {e}")

        # 3. Backfill Appearance
        logger.info("Backfilling appearance data...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, season=season_str, league="NBA"
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # 4. Fetch Players from DB
        players = (
            self.session.query(Player).filter_by(season=season_str, league="NBA").all()
        )
        logger.info(f"Fetched {len(players)} players from database.")
        print(f"Fetched {len(players)} players.")

        # 5. Group by Team
        team_map = defaultdict(list)

        # Calculate League Distribution for Tendencies
        print("Calculating league stat distribution...")
        all_raw_stats_dicts = [p.raw_stats if p.raw_stats else {} for p in players]

        all_derived = []
        for raw in all_raw_stats_dicts:
            h_str = raw.get("ROSTER_HEIGHT", raw.get("HEIGHT", ""))
            ht = 75
            try:
                if h_str and "-" in str(h_str):
                    f, i = str(h_str).split("-")
                    ht = int(f) * 12 + int(i)
            except:
                pass
            all_derived.append(tendencies.calculate_derived_stats(raw, height=ht))

        distribution = tendencies.calculate_distribution(all_derived)

        for p in players:
            team_map[p.team_id].append(p)

        # 6. Pre-calculate league-wide ratings using percentile distribution
        print("Calculating league-wide player ratings...")
        player_attributes_list = []
        player_stats_list = []
        player_id_to_attrs = {}

        for p in players:
            raw_stats = p.raw_stats if p.raw_stats else {}
            age = self._parse_age(raw_stats)
            ht_val = self._parse_height(raw_stats)
            wt_val = self._parse_weight(raw_stats)
            attrs = normalization.StatsConverter.calculate_ratings(
                raw_stats, height=ht_val, weight=wt_val, age=age
            )
            player_attributes_list.append(attrs)
            player_stats_list.append(raw_stats)
            player_id_to_attrs[p.id] = attrs

        league_ratings = normalization.calculate_league_ratings(
            player_attributes_list, player_stats_list
        )
        player_id_to_rating = {
            players[i].id: league_ratings[i] for i in range(len(players))
        }

        # 7. Build Teams
        league_teams = []
        total_teams = len(team_map)
        current_team = 0
        year_int = int(year)

        print("Building Teams...")
        for tid, roster in team_map.items():
            current_team += 1
            if current_team % 5 == 0:
                print(f"Built {current_team}/{total_teams} teams...")

            # Get Team Info
            team_info = self.repo.nba_client.get_team_by_id(int(tid))
            city = team_info.get("city", "Unknown") if team_info else "Unknown"
            name = team_info.get("nickname", f"Team {tid}") if team_info else f"Team {tid}"
            short_name = team_info.get("abbreviation", "TM") if team_info else "TM"

            # Get team assets from lookup
            tid_str = str(tid)
            target_id = team_assets.get_target_team_id(tid_str)
            team_colors = team_assets.get_team_colors(tid_str)
            team_location = team_assets.get_team_location(tid_str)
            arena_name = team_assets.get_team_arena(tid_str)
            division = team_assets.get_team_division(tid_str)

            # Build Roster
            struct_roster = []
            player_id_counter = 0

            for p in roster:
                raw_stats = p.raw_stats if p.raw_stats else {}
                app_data = p.appearance if p.appearance else {}

                # Parse metadata
                age = self._parse_age(raw_stats)
                ht_val = self._parse_height(raw_stats)
                wt_val = self._parse_weight(raw_stats)
                pos_val = self._parse_position(raw_stats)
                ctry_val = self._parse_country(raw_stats)

                # Use pre-calculated attributes and league-wide ratings
                attributes = player_id_to_attrs.get(p.id, {})
                rating_val = player_id_to_rating.get(p.id, 5.0)

                # Calculate pot from attribute potentials (simple average, position-agnostic)
                attribute_potentials = [attributes[key][1] for key in attributes.keys()]
                avg_potential = sum(attribute_potentials) / len(attribute_potentials)
                # Convert from 1-20 scale to 0-10 scale, round to nearest 0.5
                pot_val = round((avg_potential / 2.0) * 2) / 2
                pot_val = min(10, max(0, pot_val))

                # Appearance (full object)
                skin_val = app_data.get("skin_tone", 1)
                player_appearance = team_assets.generate_player_appearance(app_data, skin_val)

                # Accessories (4 uniform-specific dicts)
                player_accessories = team_assets.generate_player_accessories(skin_val)

                # Suits
                player_suits = team_assets.generate_player_suits()

                # Tendencies
                tends = tendencies.generate_player_tendencies(
                    stats=raw_stats,
                    height=ht_val,
                    position=pos_val,
                    distribution=distribution
                )

                # Skills/badges
                skills = team_assets.generate_skills(attributes, raw_stats)

                # Game status
                game_status = team_assets.generate_game_status()

                # Contract
                contract = team_assets.generate_contract(rating_val, age, pot_val)
                contract["tid"] = target_id
                contract["pid"] = p.id

                # History
                history = team_assets.generate_player_history(years_exp=max(0, age - 22))

                struct_player = structs.Player(
                    id=p.id,
                    tid=target_id,
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    tag="",
                    home="",
                    num=player_id_counter + 1,
                    age=age,
                    ht=ht_val,
                    wt=wt_val,
                    pos=pos_val,
                    ctry=ctry_val,
                    rating=rating_val,
                    pot=pot_val,
                    appearance=player_appearance,
                    accessories=player_accessories,
                    suits=player_suits,
                    attributes=attributes,
                    tendencies=tends,
                    skills=skills,
                    gameStatus=game_status,
                    contract=contract,
                    history=history,
                    stats=raw_stats,
                    careerStats={"season": [], "playoffs": [], "finals": [], "highs": {}},
                )
                struct_roster.append(struct_player)
                player_id_counter += 1

            # Generate team assets
            front_office = team_assets.generate_front_office(target_id, name)
            court = team_assets.generate_court(team_colors)
            uniforms = team_assets.generate_uniforms(team_colors)
            championships = team_assets.generate_championships()
            draft_picks = team_assets.generate_draft_picks(target_id, year_int)

            t = structs.Team(
                id=target_id,
                city=city,
                name=name,
                shortName=short_name,
                tag=short_name,
                arenaName=arena_name,
                logoURL="",
                division=division,
                location=team_location,
                roster=struct_roster,
                teamColors=team_colors,
                frontOffice=front_office,
                inbox=[],
                uniforms=uniforms,
                court=court,
                startingLineup=[],
                currentLineup=[],
                lineupPreset=0,
                draftPicks=draft_picks,
                retiredNumbers=[],
                season=[],
                history={},
                headToHeads={},
                scoringOptions={},
                quickPlays=[],
                coinFlip=0,
                status=0,
                rnk=current_team,
                championships=championships,
            )
            league_teams.append(t)

        # Generate league-level data
        meta = structs.Meta(
            saveName=f"NBA {year} Season",
            buildVersion="1.0",
            uPID=-1,
            uTID=-1,
            uGID=0,
            dataType=1,  # 1 = League
            countryGeneration=0,
            generatedCountries=[0],
            gender=0,
            filesize=0,
        )

        # Commissioner and referee
        commissioner = {
            "fn": "David",
            "ln": "Stern",
            "age": 60,
            "ctry": 0,
            "appearance": {},
        }
        referee = {
            "fn": "Dick",
            "ln": "Bavetta",
            "age": 65,
            "ctry": 0,
            "appearance": {},
        }

        return structs.League(
            leagueName=f"NBA {year}",
            shortName="NBA",
            logoURL="",
            logoSize=0,
            leagueType=0,
            meta=meta,
            conferences=self._get_default_conferences(),
            divisions=self._get_default_divisions(),
            teams=league_teams,
            freeAgents=[],
            draftClass=[],
            retirees=[],
            hallOfFame=[],
            coaches=[],
            referee=referee,
            commissioner=commissioner,
            starTeams=[],
            gameballs=[],
            media={},
            threePointContestants=[],
            contractOffers=[],
            awards=[],
            records={},
            settings=self._get_default_settings(),
            rules=self._get_default_rules(),
            sliders={},
            difficulty={"level": 2},
            simulationSliders={},
            optimization={},
            coachSettings={},
            career={},
            season={},
            currentGame=None,
        )

    def generate_ncaa_league(self, year: str, tournament_mode: bool = False) -> structs.League:
        """Generate NCAA league data."""
        mode_str = "Tournament (64 teams)" if tournament_mode else "Full"
        logger.info(f"Generating NCAA league for year: {year} [{mode_str}]")

        # 1. Sync NCAA Data
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

        # 5. Build Teams
        league_teams = []
        total_teams = len(team_map)
        current_team = 0

        # Fetch Team Metadata
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

            tid_str = str(tid)
            meta = tid_to_meta.get(tid_str, {})
            team_name = meta.get("name", f"Team {tid}")
            team_abbrev = meta.get("shortName", f"T{str(tid)[-3:]}")

            # Build roster
            struct_roster = []
            for p in roster:
                raw = p.raw_stats if p.raw_stats else {}
                app_data = p.appearance if p.appearance else {}

                ht_val = self._parse_height_ncaa(raw)
                wt_val = self._parse_weight_ncaa(raw)
                pos_val = self._parse_position_ncaa(raw)

                skin_val = app_data.get("skin_tone", 1)
                player_appearance = team_assets.generate_player_appearance(app_data, skin_val)
                player_accessories = team_assets.generate_player_accessories(skin_val)

                # Default ratings for NCAA
                attributes = {k: [5, 7] for k in [
                    "LAY", "DNK", "INS", "MID", "TPT", "FTS",
                    "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                    "STR", "SPD", "STM"
                ]}

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
                    rating=5.0,
                    pot=7,
                    appearance=player_appearance,
                    accessories=player_accessories,
                    attributes=attributes,
                )
                struct_roster.append(struct_player)

            # Generate team colors (placeholder for NCAA)
            team_colors = ["CC0000", "FFFFFF", "000000"]

            t = structs.Team(
                id=int(tid),
                city="",
                name=team_name,
                shortName=team_abbrev,
                tag=team_abbrev,
                roster=struct_roster,
                teamColors=team_colors,
                uniforms=team_assets.generate_uniforms(team_colors),
                court=team_assets.generate_court(team_colors),
            )
            league_teams.append(t)

        logger.info(f"NCAA league generation complete: {len(league_teams)} teams, {len(players)} players")

        return structs.League(
            leagueName=f"NCAA {year}",
            shortName="NCAA",
            leagueType=1,
            settings=self._get_default_settings(),
            teams=league_teams,
            meta=structs.Meta(
                saveName=f"NCAA {year}",
                dataType=1,
                generatedCountries=[0],
            ),
        )

    def generate_draft_class(self, year: str) -> structs.League:
        """Generate draft class data."""
        logger.info(f"Generating draft class for year: {year}")

        # Fetch draft history
        try:
            logger.info(f"Fetching draft history for {year}...")
            df = self.repo.nba_client.get_draft_history(
                league_id="00", season_year=year
            )

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
                meta=structs.Meta(
                    saveName=f"{year} Draft Class",
                    dataType=2,  # 2 = Draft Class
                    generatedCountries=[0],
                ),
            )

        # Store draft picks in database
        draft_season = f"draft-{year}"

        for i, row in df_year.iterrows():
            pid = str(row["PERSON_ID"])
            p_name = row["PLAYER_NAME"]

            existing = (
                self.session.query(Player)
                .filter_by(source_id=pid, season=draft_season, league="NBA")
                .first()
            )
            if existing:
                continue

            player = Player(
                source_id=pid,
                league="NBA",
                season=draft_season,
                name=p_name,
                team_id="-1",
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

        # Fetch player career stats
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

            if "CAREER_EFF" in raw:
                continue

            if i % 10 == 0:
                logger.info(f"Processing draft pick {i+1}/{len(players)}...")

            time.sleep(0.8)

            try:
                stats_data = self.repo.nba_client.get_player_career_stats(pid)
                career_df = stats_data.get("career_totals")
                season_df = stats_data.get("season_totals")

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

        # Backfill appearance
        logger.info("Backfilling appearance data for draft picks...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, season=draft_season, league="NBA"
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # Refresh players
        players = (
            self.session.query(Player)
            .filter_by(season=draft_season, league="NBA")
            .all()
        )

        # Calculate Distribution
        all_raw_stats_dicts = [p.raw_stats if p.raw_stats else {} for p in players]
        all_derived = []
        for raw in all_raw_stats_dicts:
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
            if gp > 0:
                if eff > 26:
                    pot_val = 10
                elif eff > 20:
                    pot_val = 9
                elif eff > 16:
                    pot_val = 8
                elif eff > 12:
                    pot_val = 7
                elif eff > 8:
                    pot_val = 6
                elif eff > 4:
                    pot_val = 5
                elif gp > 100:
                    pot_val = 4
                else:
                    pot_val = 4
            else:
                if pick <= 5:
                    pot_val = 9
                elif pick <= 15:
                    pot_val = 7
                elif pick <= 30:
                    pot_val = 6
                else:
                    pot_val = 5

            # Calculate attributes
            base_attrs = {k: [3, pot_val] for k in [
                "LAY", "DNK", "INS", "MID", "TPT", "FTS",
                "DRB", "PAS", "ORE", "DRE", "STL", "BLK",
                "STR", "SPD", "STM"
            ]}

            if "ROOKIE_PPG" in raw:
                ppg = raw["ROOKIE_PPG"]
                rpg = raw.get("ROOKIE_RPG", 0)
                apg = raw.get("ROOKIE_APG", 0)
                spg = raw.get("ROOKIE_SPG", 0)
                bpg = raw.get("ROOKIE_BPG", 0)

                base_attrs["INS"] = [min(10, int(ppg / 2.5)), pot_val]
                base_attrs["MID"] = [min(10, int(ppg / 3.0)), pot_val]
                base_attrs["TPT"] = [min(10, int(ppg / 4.0)), pot_val]
                base_attrs["STL"] = [min(10, int(spg * 4)), pot_val]
                base_attrs["BLK"] = [min(10, int(bpg * 3)), pot_val]
                base_attrs["DRE"] = [min(10, int(rpg * 1.5)), pot_val]
                base_attrs["PAS"] = [min(10, int(apg * 2.0)), pot_val]

            avg_attr = sum(v[0] for v in base_attrs.values()) / 15
            rating_val = max(1.0, round(avg_attr, 1))

            # Appearance
            skin_val = app_data.get("skin_tone", 1)
            player_appearance = team_assets.generate_player_appearance(app_data, skin_val)
            player_accessories = team_assets.generate_player_accessories(skin_val)

            # Tendencies
            tends = tendencies.generate_player_tendencies(
                stats=raw,
                height=78,
                position=3,
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
                appearance=player_appearance,
                accessories=player_accessories,
                attributes=base_attrs,
                tendencies=tends,
                history=team_assets.generate_player_history(
                    draft_year=int(year),
                    draft_pk=pick,
                ),
            )
            draft_players.append(draft_player)

        draft_players.sort(key=lambda x: x.id)

        draft_team = structs.Team(
            id=-1,
            city="Draft",
            name="Class",
            shortName="DRF",
            tag="DRF",
            roster=draft_players,
            teamColors=["000000", "FFFFFF", "CC0000"],
        )

        logger.info(f"Draft class generation complete: {len(draft_players)} players")

        return structs.League(
            leagueName=f"NBA {year} Draft Class",
            shortName="Draft",
            settings=self._get_default_settings(),
            teams=[draft_team],
            meta=structs.Meta(
                saveName=f"{year} Draft Class",
                dataType=2,  # 2 = Draft Class
                generatedCountries=[0],
            ),
        )

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _year_to_season(self, year: str) -> str:
        try:
            y = int(year)
            return f"{y - 1}-{str(y)[2:]}"
        except:
            return year

    def _parse_age(self, stats: dict) -> int:
        try:
            age_val = stats.get("ROSTER_AGE", stats.get("AGE", 0))
            return int(float(age_val))
        except:
            return 0

    def _parse_height(self, stats: dict) -> int:
        h_str = stats.get("ROSTER_HEIGHT", stats.get("HEIGHT", ""))
        try:
            if not h_str or "-" not in str(h_str):
                return 72
            ft, inches = str(h_str).split("-")
            return int(ft) * 12 + int(inches)
        except:
            return 72

    def _parse_height_ncaa(self, stats: dict) -> int:
        h_str = stats.get("displayHeight", "")
        try:
            if not h_str:
                return 72
            h_str = str(h_str).replace('"', '').replace("'", '-')
            if '-' in h_str:
                parts = h_str.split('-')
                ft = int(parts[0].strip())
                inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                return ft * 12 + inches
            return 72
        except:
            return 72

    def _parse_weight(self, stats: dict) -> int:
        w_str = stats.get("ROSTER_WEIGHT", stats.get("WEIGHT", ""))
        try:
            return int(w_str)
        except:
            return 200

    def _parse_weight_ncaa(self, stats: dict) -> int:
        w_str = stats.get("displayWeight", "")
        try:
            if not w_str:
                return 200
            return int(str(w_str).split()[0])
        except:
            return 200

    def _parse_position(self, stats: dict) -> int:
        pos_str = stats.get("ROSTER_POSITION", stats.get("POSITION", ""))
        if not pos_str:
            return 1
        p = str(pos_str).upper()
        if "C" in p:
            return 5
        if "F" in p:
            return 4 if "G" not in p else 3
        return 1 if "G" in p else 1

    def _parse_position_ncaa(self, stats: dict) -> int:
        pos_data = stats.get("position", "")
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

    def _parse_country(self, stats: dict) -> int:
        c_str = stats.get("ROSTER_COUNTRY", "USA")
        if not c_str or c_str == "USA":
            return 0
        return 1

    def _get_default_settings(self) -> dict:
        return {
            "gameLength": 12,
            "difficulty": 2,
            "shotClock": 24,
            "overtimeLength": 5,
        }

    def _get_default_rules(self) -> dict:
        return {
            "foulsToFoulOut": 6,
            "threePointLine": True,
            "defensiveThreeSeconds": True,
        }

    def _get_default_conferences(self) -> list:
        return ["Eastern Conference", "Western Conference"]

    def _get_default_divisions(self) -> list:
        return ["Atlantic", "Central", "Southeast", "Pacific", "Northwest", "Southwest"]

    def to_json(self, league_obj: structs.League, filename: str):
        try:
            year = league_obj.leagueName.split(" ")[1]
        except:
            year = "unknown"
        output_dir = os.path.join("output", year)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        data = asdict(league_obj)
        save_compact_json(data, filepath)

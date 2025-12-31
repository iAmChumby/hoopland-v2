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
from ..data import historical_loader
from ..data import awards_loader
from ..data.college_client import CollegeClient
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
        self.college_client = CollegeClient()

    def generate_league(self, year: str, progress_callback=None) -> structs.League:
        """Generate NBA league data for a specific year."""
        if progress_callback:
            progress_callback(0, "Initializing...")
        logger.info(f"Generating NBA league for year: {year}")
        print(f"Generating NBA {year}...")

        # 1. Sync Data (Performance Stats)
        season_str = self._year_to_season(year)
        if progress_callback:
            progress_callback(5, "Syncing season stats...")
        try:
            self.repo.sync_nba_season_stats(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync stats: {e}")

        # 2. Sync Roster Metadata (Age, Ht, Wt, Pos, Country)
        if progress_callback:
            progress_callback(15, "Syncing roster metadata...")
        try:
            self.repo.sync_nba_roster_data(season=season_str)
        except Exception as e:
            logger.error(f"Failed to sync roster metadata: {e}")

        # 3. Backfill Appearance
        logger.info("Backfilling appearance data...")
        if progress_callback:
            progress_callback(25, "Processing player appearance...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance, season=season_str, league="NBA"
            )
        except Exception as e:
            logger.error(f"Failed to backfill appearance: {e}")

        # 4. Fetch Players from DB
        if progress_callback:
            progress_callback(35, "Fetching players...")
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
        if progress_callback:
            progress_callback(45, "Calculating player ratings...")
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

        print("Fetching stat leaders for award prioritization...")
        try:
            priority_player_ids = self.repo.nba_client.get_league_leaders(season_str)
            logger.info(
                f"Identified {len(priority_player_ids)} priority players for awards"
            )
        except Exception as e:
            logger.warning(f"Could not fetch league leaders: {e}")
            priority_player_ids = set()

        print("Building Teams...")
        if progress_callback:
            progress_callback(55, "Building teams...")
        player_awards_queue = []

        for tid, roster in team_map.items():
            current_team += 1
            if current_team % 5 == 0:
                print(f"Built {current_team}/{total_teams} teams...")
                if progress_callback:
                    pct = 55 + int((current_team / total_teams) * 25)  # 55% to 80%
                    progress_callback(
                        pct, f"Building Team {current_team}/{total_teams}..."
                    )

            # Get Team Info - use historical data for accurate names/cities
            tid_str = str(tid)
            historical_team = historical_loader.get_team_for_year(tid_str, year_int)

            if historical_team:
                city = historical_team.get("city", "Unknown")
                name = historical_team.get("name", f"Team {tid}")
                short_name = historical_team.get("tag", "TM")
                arena_name = historical_team.get("arena", "")
                team_colors = historical_team.get("colors", [])
                logo_url = historical_team.get("logoURL", "")
            else:
                team_info = self.repo.nba_client.get_team_by_id(int(tid))
                city = team_info.get("city", "Unknown") if team_info else "Unknown"
                name = (
                    team_info.get("nickname", f"Team {tid}")
                    if team_info
                    else f"Team {tid}"
                )
                short_name = team_info.get("abbreviation", "TM") if team_info else "TM"
                arena_name = team_assets.get_team_arena(tid_str)
                team_colors = team_assets.get_team_colors(tid_str)
                logo_url = ""

            # Get team assets from lookup
            target_id = team_assets.get_target_team_id(tid_str)
            if not team_colors:
                team_colors = team_assets.get_team_colors(tid_str)
            team_location = team_assets.get_team_location(tid_str)
            if not arena_name:
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
                # Convert from 1-20 scale to 0-10 scale, round UP to nearest 0.5
                pot_val = normalization.ceil_to_half(avg_potential / 2.0)
                pot_val = min(10.0, max(0.0, pot_val))

                # Appearance (full object)
                skin_val = app_data.get("skin_tone", 1)
                player_appearance = team_assets.generate_player_appearance(
                    app_data, skin_val
                )

                # Accessories (4 uniform-specific dicts)
                player_accessories = team_assets.generate_player_accessories(skin_val)

                # Suits
                player_suits = team_assets.generate_player_suits()

                # Tendencies
                tends = tendencies.generate_player_tendencies(
                    stats=raw_stats,
                    height=ht_val,
                    position=pos_val,
                    distribution=distribution,
                )

                # Skills/badges
                skills = team_assets.generate_skills(attributes, raw_stats)

                # Game status
                game_status = team_assets.generate_game_status()

                # Contract
                contract = team_assets.generate_contract(rating_val, age, pot_val)
                contract["tid"] = target_id
                contract["pid"] = p.id

                # Calculate years of experience from roster data (no API call needed)
                exp_val = raw_stats.get("ROSTER_EXP", "0")
                if exp_val == "R":
                    years_exp = 0
                elif str(exp_val).isdigit():
                    years_exp = int(exp_val)
                else:
                    years_exp = max(0, age - 22)

                source_id = raw_stats.get("PLAYER_ID", p.source_id)
                is_priority = (
                    int(source_id) in priority_player_ids if source_id else False
                )

                # History
                history = team_assets.generate_player_history(years_exp=years_exp)

                struct_player = structs.Player(
                    id=p.id,
                    tid=target_id,
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    tag="",
                    home="",
                    num=player_id_counter + 1,
                    age=age,
                    yrs=years_exp,
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
                    careerStats={
                        "season": [],
                        "playoffs": [],
                        "finals": [],
                        "highs": {},
                    },
                    awards=[],
                )
                struct_roster.append(struct_player)
                player_id_counter += 1

                if source_id:
                    player_awards_queue.append(
                        {
                            "player": struct_player,
                            "source_id": int(source_id),
                            "name": p.name,
                            "is_priority": is_priority,
                            "rating": rating_val,
                        }
                    )

            # Assign lineup positions based on minutes played
            roster_with_minutes = []
            for player in struct_roster:
                minutes = player.stats.get("MIN", 0) if player.stats else 0
                roster_with_minutes.append((player, minutes))

            # Sort by minutes descending
            roster_with_minutes.sort(key=lambda x: x[1], reverse=True)

            # Assign linePos: 0-4 for starters (top 5 by minutes), 5+ for bench
            starting_lineup_ids = []
            for idx, (player, _) in enumerate(roster_with_minutes):
                player.linePos = idx
                if idx < 5:
                    starting_lineup_ids.append(player.id)

            # Generate team assets
            front_office = team_assets.generate_front_office(
                target_id, name, tid_str, year_int
            )
            court = team_assets.generate_court(
                team_colors, logo_url, city, name, arena_name, current_team
            )
            uniforms = team_assets.generate_uniforms(team_colors)
            championships = team_assets.generate_championships(tid_str, year_int)
            draft_picks = team_assets.generate_draft_picks(target_id, year_int)

            t = structs.Team(
                id=target_id,
                city=city,
                name=name,
                shortName=short_name,
                tag=short_name,
                arenaName=arena_name,
                logoURL=logo_url,
                division=division,
                location=team_location,
                roster=struct_roster,
                teamColors=team_colors,
                frontOffice=front_office,
                inbox=[],
                uniforms=uniforms,
                court=court,
                startingLineup=starting_lineup_ids,
                currentLineup=starting_lineup_ids.copy(),
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

        # 8. Fetch awards for priority players first, then others if time permits
        print("Fetching player awards (prioritizing stat leaders)...")
        if progress_callback:
            progress_callback(80, "Fetching awards...")
        player_awards_queue.sort(key=lambda x: (not x["is_priority"], -x["rating"]))

        awards_start_time = time.time()
        MAX_AWARDS_TIME = 150
        awards_fetched = 0
        awards_skipped = 0

        for entry in player_awards_queue:
            if time.time() - awards_start_time >= MAX_AWARDS_TIME:
                if awards_skipped == 0:
                    logger.info(
                        f"Awards timeout reached after {awards_fetched} players"
                    )
                awards_skipped += 1
                continue

            try:
                priority_str = " [PRIORITY]" if entry["is_priority"] else ""
                logger.info(
                    f"Fetching awards for {entry['name']}{priority_str} ({awards_fetched + 1} fetched)"
                )
                awards_df = self.repo.nba_client.get_player_awards(entry["source_id"])
                player_awards = awards_loader.process_player_awards(awards_df, year_int)
                entry["player"].awards = player_awards
                awards_fetched += 1
                if progress_callback and awards_fetched % 5 == 0:
                    # Map loop progress to 80-95%
                    # We don't know exactly how many we will fetch due to timeout, but let's estimate based on queue
                    total_q = len(player_awards_queue)
                    if total_q > 0:
                        prog = 80 + int((awards_fetched / total_q) * 15)
                        progress_callback(
                            min(95, prog), f"Fetching awards ({awards_fetched})..."
                        )
                time.sleep(0.6)
            except Exception as e:
                logger.debug(f"Could not fetch awards for {entry['name']}: {e}")

        logger.info(
            f"Awards complete: {awards_fetched} fetched, {awards_skipped} skipped"
        )

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
            logoURL="https://hoopland-v2.luke-personal-account.workers.dev/logos/leagues/nba.png",
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

    def generate_ncaa_league(
        self, year: str, tournament_mode: bool = False
    ) -> structs.League:
        """Generate NCAA league data."""
        mode_str = "Tournament (64 teams)" if tournament_mode else "Full"
        logger.info(f"Generating NCAA league for year: {year} [{mode_str}]")

        # 1. Sync NCAA Data
        team_ids = []
        try:
            team_ids = self.repo.sync_ncaa_season_stats(
                season=year, tournament_only=tournament_mode
            )
        except Exception as e:
            logger.error(f"Failed to sync NCAA stats: {e}")

        # 2. Backfill Appearance
        logger.info("Backfilling appearance data for NCAA players...")
        try:
            self.repo.backfill_appearance(
                appearance.analyze_player_appearance,
                season=year,
                league="NCAA",
                team_ids=team_ids if tournament_mode else None,
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

        # Fetch Team Metadata with logos and arena info
        tid_to_meta = {}
        try:
            logger.info("Fetching NCAA team metadata (names, logos, arenas)...")
            all_teams = self.repo.espn_client.get_all_teams()
            for t in all_teams:
                tid = str(t.get("id"))
                logos = t.get("logos", [])
                logo_url = logos[0] if logos else ""
                venue = t.get("venue", {})
                arena_name = (
                    venue.get("fullName", "") if isinstance(venue, dict) else ""
                )
                tid_to_meta[tid] = {
                    "name": t.get("displayName", f"Team {tid}"),
                    "shortName": t.get("abbreviation", f"T{tid[-3:]}"),
                    "location": t.get("location", ""),
                    "logo": logo_url,
                    "arena": arena_name,
                    "color": t.get("color", ""),
                    "alternateColor": t.get("alternateColor", ""),
                }
        except Exception as e:
            logger.warning(f"Could not fetch team metadata: {e}")

        year_int = int(year)

        for tid, roster in team_map.items():
            current_team += 1
            if current_team % 50 == 0:
                logger.info(f"Building team {current_team}/{total_teams}...")

            tid_str = str(tid)
            meta = tid_to_meta.get(tid_str, {})
            espn_team_name = meta.get("name", f"Team {tid}")
            espn_abbrev = meta.get("shortName", f"T{str(tid)[-3:]}")

            ncaa_info = team_assets.get_ncaa_team_info(espn_team_name)

            # Allow all teams, regardless of conference
            # if not ncaa_info.get("conference"):
            #     logger.debug(f"Skipping {espn_team_name} - not in Power 6 conferences")
            #     continue

            school = ncaa_info.get("school", espn_team_name)
            mascot = ncaa_info.get("name", "Team")
            team_colors = ncaa_info.get("colors", ["CC0000", "FFFFFF", "000000"])
            team_tag = ncaa_info.get("tag", espn_abbrev)
            target_id = ncaa_info.get("target_id", int(tid) % 1000)

            if not ncaa_info.get("conference"):
                division = 6  # Independents
            else:
                division = ncaa_info.get("division", 0)

            struct_roster = []
            player_id_counter = 0
            for p in roster:
                raw = p.raw_stats if p.raw_stats else {}
                app_data = p.appearance if p.appearance else {}

                ht_val = self._parse_height_ncaa(raw)
                wt_val = self._parse_weight_ncaa(raw)
                pos_val = self._parse_position_ncaa(raw)

                skin_val = app_data.get("skin_tone", 1)
                player_appearance = team_assets.generate_player_appearance(
                    app_data, skin_val
                )
                player_accessories = team_assets.generate_player_accessories(skin_val)
                player_suits = team_assets.generate_player_suits()

                attributes = self._calculate_ncaa_attributes(raw, ht_val, wt_val)

                tends = tendencies.generate_player_tendencies(
                    stats=raw, height=ht_val, position=pos_val, distribution={}
                )

                skills = team_assets.generate_skills(attributes, raw)
                game_status = team_assets.generate_game_status()

                struct_player = structs.Player(
                    id=p.id,
                    tid=target_id,
                    fn=p.name.split(" ")[0] if " " in p.name else p.name,
                    ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                    num=player_id_counter + 1,
                    age=self._parse_age_ncaa(raw),
                    yrs=0,
                    ht=ht_val,
                    wt=wt_val,
                    pos=pos_val,
                    ctry=0,
                    rating=5.0,
                    pot=7,
                    appearance=player_appearance,
                    accessories=player_accessories,
                    suits=player_suits,
                    attributes=attributes,
                    tendencies=tends,
                    skills=skills,
                    gameStatus=game_status,
                    history=team_assets.generate_player_history(),
                )
                struct_roster.append(struct_player)
                player_id_counter += 1

            starting_lineup_ids = (
                [p.id for p in struct_roster[:5]]
                if len(struct_roster) >= 5
                else [p.id for p in struct_roster]
            )
            for idx, player in enumerate(struct_roster):
                player.linePos = idx

            logo_url = meta.get("logo", "")
            if not logo_url and tid:
                logo_url = f"https://a.espncdn.com/i/teamlogos/ncaa/500/{tid}.png"
            arena_name = meta.get("arena", "") or f"{school} Arena"

            front_office = team_assets.generate_ncaa_front_office(target_id, mascot)
            court = team_assets.generate_court(
                team_colors, "", school, mascot, arena_name, current_team
            )
            uniforms = team_assets.generate_ncaa_uniforms(team_colors)
            championships = team_assets.generate_ncaa_championships(school, year_int)

            t = structs.Team(
                id=target_id,
                city=school,
                name=mascot,
                shortName=team_tag,
                tag=team_tag,
                arenaName=arena_name,
                logoURL=logo_url,
                division=division,
                location={"x": 0, "y": 0},
                roster=struct_roster,
                teamColors=team_colors,
                frontOffice=front_office,
                inbox=[],
                uniforms=uniforms,
                court=court,
                startingLineup=starting_lineup_ids,
                currentLineup=starting_lineup_ids.copy(),
                lineupPreset=0,
                draftPicks=[],
                retiredNumbers=[],
                season=[],
                history={
                    "season": [],
                    "seasonHighs": {},
                    "playoffs": [],
                    "playoffHighs": {},
                    "finals": [],
                    "finalsHighs": {},
                },
                headToHeads={},
                scoringOptions={},
                quickPlays=[],
                coinFlip=0,
                status=0,
                rnk=current_team,
                championships=championships,
            )
            league_teams.append(t)

        logger.info(
            f"NCAA league generation complete: {len(league_teams)} teams, {len(players)} players"
        )

        return structs.League(
            leagueName="Men's College Basketball",
            shortName="NCAA",
            logoURL="https://i.imgur.com/MZbIqps.png",
            logoSize=256,
            leagueType=1,
            conferences=["Southern Conference", "Northern Conference"],
            divisions=["SEC", "XII", "WCC", "B1G", "Big East", "ACC", "Independents"],
            settings=self._get_default_settings(),
            teams=league_teams,
            meta=structs.Meta(
                saveName=f"NCAA {year}",
                dataType=1,
                generatedCountries=[0],
            ),
        )

    def generate_draft_class(self, year: str, progress_callback=None) -> structs.League:
        """Generate draft class data."""
        logger.info(f"Generating draft class for year: {year}")
        if progress_callback:
            progress_callback(0, "Initializing draft class...")

        # Fetch draft history
        try:
            logger.info(f"Fetching draft history for {year}...")
            if progress_callback:
                progress_callback(10, "Fetching draft history...")
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

        combine_data = {}
        try:
            logger.info(f"Fetching draft combine measurements for {year}...")
            if progress_callback:
                progress_callback(20, "Fetching combine measurements...")
            combine_data = self.repo.nba_client.get_draft_combine_measurements(
                int(year)
            )
            logger.info(f"Found combine data for {len(combine_data)} players")
        except Exception as e:
            logger.warning(f"Could not fetch combine data: {e}")

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

            org = row.get("ORGANIZATION", "") if "ORGANIZATION" in row.index else ""
            org_type = (
                row.get("ORGANIZATION_TYPE", "")
                if "ORGANIZATION_TYPE" in row.index
                else ""
            )

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
                    "ROUND_NUMBER": (
                        int(row["ROUND_NUMBER"]) if "ROUND_NUMBER" in row else 1
                    ),
                    "DRAFT_YEAR": year,
                    "ORGANIZATION": org,
                    "ORGANIZATION_TYPE": org_type,
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

        logger.info(
            f"Processing {len(players)} draft picks for stats and appearance..."
        )
        if progress_callback:
            progress_callback(30, "Processing players...")

        for i, p in enumerate(players):
            raw = p.raw_stats if p.raw_stats else {}
            pid = int(p.source_id)
            pick = raw.get("OVERALL_PICK", 60)

            if "CAREER_EFF" in raw:
                continue

            if i % 10 == 0:
                logger.info(f"Processing draft pick {i+1}/{len(players)}...")
                if progress_callback:
                    # 30% to 90%
                    pct = 30 + int((i / len(players)) * 60)
                    progress_callback(pct, f"Processing player {i+1}/{len(players)}...")

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

        logger.info("Fetching college stats for eligible players...")
        college_stats_count = 0
        players = (
            self.session.query(Player)
            .filter_by(season=draft_season, league="NBA")
            .all()
        )
        for i, p in enumerate(players):
            raw = p.raw_stats if p.raw_stats else {}
            if "COLLEGE_STATS" in raw:
                continue

            org = raw.get("ORGANIZATION", "")
            org_type = raw.get("ORGANIZATION_TYPE", "")

            if not team_assets.is_college_player(org_type):
                continue

            college_name = team_assets.normalize_college_name(org)
            if not college_name:
                continue

            try:
                college_stats = self.college_client.search_player_by_name(
                    player_name=p.name, college_name=college_name, draft_year=int(year)
                )
                if college_stats:
                    raw["COLLEGE_STATS"] = college_stats
                    raw["COLLEGE_NAME"] = college_name
                    p.raw_stats = raw
                    self.session.commit()
                    college_stats_count += 1
            except Exception as e:
                logger.debug(f"College stats not found for {p.name}: {e}")

            if i % 20 == 0:
                logger.info(
                    f"Processed college stats for {i+1}/{len(players)} players..."
                )

        logger.info(f"Found college stats for {college_stats_count} players")

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

        all_derived = []
        for p in players:
            raw = p.raw_stats if p.raw_stats else {}
            college_stats = raw.get("COLLEGE_STATS")
            if college_stats:
                tendency_input = tendencies.map_college_stats_to_tendency_input(
                    college_stats
                )
                all_derived.append(
                    tendencies.calculate_derived_stats(tendency_input, height=78)
                )
            else:
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
            base_attrs = {
                k: [3, pot_val]
                for k in [
                    "LAY",
                    "DNK",
                    "INS",
                    "MID",
                    "TPT",
                    "FTS",
                    "DRB",
                    "PAS",
                    "ORE",
                    "DRE",
                    "STL",
                    "BLK",
                    "STR",
                    "SPD",
                    "STM",
                ]
            }

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
            rating_val = max(1.0, normalization.ceil_to_half(avg_attr))

            # Appearance
            skin_val = app_data.get("skin_tone", 1)
            player_appearance = team_assets.generate_player_appearance(
                app_data, skin_val
            )
            player_accessories = team_assets.generate_player_accessories(skin_val)

            college_stats = raw.get("COLLEGE_STATS")
            if college_stats:
                tendency_input = tendencies.map_college_stats_to_tendency_input(
                    college_stats
                )
                tends = tendencies.generate_player_tendencies(
                    stats=tendency_input,
                    height=78,
                    position=3,
                    distribution=distribution,
                )
            else:
                tends = tendencies.generate_player_tendencies(
                    stats=raw, height=78, position=3, distribution=distribution
                )

            pid = int(p.source_id)
            player_combine = combine_data.get(pid, {})
            height_inches = 78
            weight_lbs = 210

            if player_combine.get("height_with_shoes"):
                try:
                    ht_str = str(player_combine["height_with_shoes"])
                    if "'" in ht_str:
                        parts = ht_str.replace('"', "").split("'")
                        feet = int(parts[0])
                        inches = float(parts[1]) if len(parts) > 1 and parts[1] else 0
                        height_inches = int(feet * 12 + inches)
                    else:
                        height_inches = int(float(ht_str))
                except (ValueError, TypeError):
                    pass
            if player_combine.get("weight"):
                try:
                    weight_lbs = int(float(player_combine["weight"]))
                except (ValueError, TypeError):
                    pass

            college_name = raw.get("COLLEGE_NAME", raw.get("ORGANIZATION", ""))
            round_num = raw.get("ROUND_NUMBER", 1)

            draft_player = structs.Player(
                id=pid,
                tid=-1,
                fn=p.name.split(" ")[0] if " " in p.name else p.name,
                ln=" ".join(p.name.split(" ")[1:]) if " " in p.name else "",
                age=20,
                yrs=0,
                ht=height_inches,
                wt=weight_lbs,
                pos=3,
                ctry=0,
                rating=rating_val,
                pot=pot_val,
                appearance=player_appearance,
                accessories=player_accessories,
                attributes=base_attrs,
                tendencies=tends,
                history=team_assets.generate_player_history(
                    college=college_name,
                    draft_year=int(year),
                    draft_rd=round_num,
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
            h_str = str(h_str).replace('"', "").replace("'", "-")
            if "-" in h_str:
                parts = h_str.split("-")
                ft = int(parts[0].strip())
                inches = (
                    int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                )
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
        abbrev = (
            pos_data.get("abbreviation", "")
            if isinstance(pos_data, dict)
            else str(pos_data)
        )
        abbrev = abbrev.upper()
        if "C" in abbrev:
            return 5
        if "F" in abbrev:
            return 4
        if "G" in abbrev:
            return 1 if "PG" in abbrev else 2
        return 3

    def _parse_age_ncaa(self, stats: dict) -> int:
        age_str = stats.get("age", "")
        try:
            if age_str:
                return int(age_str)
        except:
            pass
        exp = stats.get("experience", {})
        if isinstance(exp, dict):
            years = exp.get("years", 0)
            return 18 + int(years) if years else 20
        return 20

    def _calculate_ncaa_attributes(self, stats: dict, height: int, weight: int) -> dict:
        base = 5
        pot = 8

        spd = max(3, min(12, 15 - max(0, (height - 74))))
        strength = max(3, min(12, 6 + (weight - 180) // 15))

        attrs = {
            "LAY": [base, pot],
            "DNK": [max(3, min(10, base + max(0, (height - 76) // 2))), pot],
            "INS": [base, pot],
            "MID": [base, pot],
            "TPT": [base, pot],
            "FTS": [base, pot],
            "DRB": [base, pot],
            "PAS": [base, pot],
            "ORE": [max(3, min(10, base + max(0, (height - 76) // 3))), pot],
            "DRE": [max(3, min(10, base + max(0, (height - 74) // 2))), pot],
            "STL": [base, pot],
            "BLK": [max(3, min(10, base + max(0, (height - 78) // 2))), pot],
            "STR": [strength, pot],
            "SPD": [spd, pot],
            "STM": [base + 2, pot],
        }

        return attrs

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
        # Infer year from filename first, e.g. NCAA_2016_Tournament.txt
        year = "unknown"
        parts = filename.replace(".txt", "").split("_")
        for part in parts:
            if part.isdigit() and len(part) == 4:
                year = part
                break

        if year == "unknown":
            try:
                year = league_obj.leagueName.split(" ")[1]
            except:
                pass

        # Resolve project root from this file: src/hoopland/blocks/generator.py -> root
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        output_dir = os.path.join(project_root, "output", year)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        data = asdict(league_obj)

        # Save as human-readable JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

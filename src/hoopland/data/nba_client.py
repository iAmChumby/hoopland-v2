from nba_api.stats.endpoints import (
    commonteamroster,
    leaguedashplayerstats,
    drafthistory,
    playercareerstats,
    playerawards,
    leagueleaders,
    draftcombineplayeranthro,
)
from typing import Optional, Dict, Any
from nba_api.stats.static import teams
import pandas as pd


from .utils import retry_api_call


class NBAClient:
    def __init__(self):
        pass

    def get_team_id(self, team_name):
        nba_teams = teams.get_teams()
        for team in nba_teams:
            if team["full_name"].lower() == team_name.lower():
                return team["id"]
        return None

    def get_team_by_id(self, team_id):
        # nba_api returns dict like {'id': 1610612737, 'full_name': 'Atlanta Hawks', 'abbreviation': 'ATL', 'nickname': 'Hawks', 'city': 'Atlanta', 'state': 'Georgia', 'year_founded': 1949}
        return teams.find_team_name_by_id(team_id)

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_roster(self, team_id, season="2023-24"):
        # NBA API expects season in format '2023-24'
        # Adding timeout to requests implicitly by wrapping or hoping nba_api supports it
        # Actually nba_api uses requests. We can set a default timeout globally or per request if exposed.
        # Unfortunately nba_api wrappers don't easily expose timeout.
        # We will wrap the call in a manual timeout using signal or future if really needed,
        # but simpler is to set socket default timeout if possible.
        # Ideally, we just hope it returns. The hang might be rate limiting.
        # Let's try to just proceed but adds logging.
        roster = commonteamroster.CommonTeamRoster(
            team_id=team_id, season=season, timeout=10
        )
        return roster.get_data_frames()[0]

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_league_stats(self, season="2023-24"):
        stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season, timeout=10)
        return stats.get_data_frames()[0]

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_draft_history(self, league_id="00", season_year=None):
        draft = drafthistory.DraftHistory(
            league_id=league_id, season_year_nullable=season_year, timeout=10
        )
        return draft.get_data_frames()[0]

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_player_career_stats(self, player_id):
        career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=10)
        dfs = career.get_data_frames()
        return {
            "season_totals": dfs[0] if len(dfs) > 0 else pd.DataFrame(),
            "career_totals": dfs[1] if len(dfs) > 1 else pd.DataFrame(),
        }

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_player_awards(self, player_id: int) -> pd.DataFrame:
        awards = playerawards.PlayerAwards(player_id=player_id, timeout=10)
        dfs = awards.get_data_frames()
        if dfs and len(dfs) > 0:
            return dfs[0]
        return pd.DataFrame()

    def fetch_player_headshot_url(self, player_id, team_id=None, year=None):
        if team_id and year:
            return f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/{team_id}/{year}/260x190/{player_id}.png"
        return f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_coaches(self, team_id: int, season: str) -> Optional[pd.DataFrame]:
        roster = commonteamroster.CommonTeamRoster(
            team_id=team_id, season=season, timeout=10
        )
        dfs = roster.get_data_frames()
        if len(dfs) > 1:
            return dfs[1]
        return None

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_league_leaders(self, season: str) -> set:
        priority_ids = set()
        categories = [
            ("PTS", 25),
            ("REB", 20),
            ("AST", 20),
            ("STL", 15),
            ("BLK", 15),
        ]
        for stat_cat, top_n in categories:
            try:
                leaders = leagueleaders.LeagueLeaders(
                    season=season,
                    stat_category_abbreviation=stat_cat,
                    per_mode48="PerGame",
                    timeout=10,
                )
                df = leaders.get_data_frames()[0]
                top_ids = df.head(top_n)["PLAYER_ID"].tolist()
                priority_ids.update(top_ids)
            except Exception:
                pass
        return priority_ids

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_draft_combine_measurements(self, year: int) -> Dict[int, Dict[str, Any]]:
        combine = draftcombineplayeranthro.DraftCombinePlayerAnthro(
            season_year=year, timeout=10
        )
        df = combine.get_data_frames()[0]

        measurements = {}
        for _, row in df.iterrows():
            player_id = row.get("PLAYER_ID")
            if player_id is None:
                continue

            measurements[int(player_id)] = {
                "height_no_shoes": row.get("HEIGHT_WO_SHOES"),
                "height_with_shoes": row.get("HEIGHT_W_SHOES"),
                "weight": row.get("WEIGHT"),
                "wingspan": row.get("WINGSPAN"),
                "standing_reach": row.get("STANDING_REACH"),
                "body_fat_pct": row.get("BODY_FAT_PCT"),
                "hand_length": row.get("HAND_LENGTH"),
                "hand_width": row.get("HAND_WIDTH"),
            }

        return measurements

    def find_player_id_by_name(self, full_name: str) -> Optional[int]:
        """
        Find NBA player ID by full name using static players list.
        Useful for finding headshots for players who went pro.
        """
        from nba_api.stats.static import players

        matches = players.find_players_by_full_name(full_name)
        if matches:
            # Return the first exact match or just the first result
            # Ideally verify active status if needed, but for headshots any match is good
            return matches[0]["id"]
        return None

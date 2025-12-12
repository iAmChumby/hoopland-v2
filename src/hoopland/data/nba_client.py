from nba_api.stats.endpoints import (
    commonteamroster,
    leaguedashplayerstats,
    drafthistory,
    playercareerstats,
)
from nba_api.stats.static import teams
import pandas as pd


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

    def get_league_stats(self, season="2023-24"):
        stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season, timeout=10)
        return stats.get_data_frames()[0]

    def get_draft_history(self, league_id="00", season_year=None):
        draft = drafthistory.DraftHistory(
            league_id=league_id, season_year_nullable=season_year, timeout=10
        )
        return draft.get_data_frames()[0]

    def get_player_career_stats(self, player_id):
        # Fetches career stats summary
        career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=10)
        # 0: SeasonTotalsRegularSeason, 1: CareerTotalsRegularSeason, ...
        # We want SeasonTotals to find Rookie year, and CareerTotals for Potential.
        dfs = career.get_data_frames()
        return {
            "season_totals": dfs[0] if len(dfs) > 0 else pd.DataFrame(),
            "career_totals": dfs[1] if len(dfs) > 1 else pd.DataFrame(),
        }

    def fetch_player_headshot_url(self, player_id):
        return f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"

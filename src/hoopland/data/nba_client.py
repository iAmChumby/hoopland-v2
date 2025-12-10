from nba_api.stats.endpoints import commonteamroster, leaguedashplayerstats, drafthistory
from nba_api.stats.static import teams
import pandas as pd

class NBAClient:
    def __init__(self):
        pass

    def get_team_id(self, team_name):
        nba_teams = teams.get_teams()
        for team in nba_teams:
            if team['full_name'].lower() == team_name.lower():
                return team['id']
        return None

    def get_roster(self, team_id, season='2023-24'):
        # NBA API expects season in format '2023-24'
        roster = commonteamroster.CommonTeamRoster(team_id=team_id, season=season)
        return roster.get_data_frames()[0]

    def get_league_stats(self, season='2023-24'):
        stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season)
        return stats.get_data_frames()[0]

    def get_draft_history(self, league_id='00'):
        draft = drafthistory.DraftHistory(league_id=league_id)
        return draft.get_data_frames()[0]

    def fetch_player_headshot_url(self, player_id):
        return f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"

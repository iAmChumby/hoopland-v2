import requests


class ESPNClient:
    BASE_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

    def __init__(self):
        pass

    def get_team_roster(self, team_id_or_slug):
        # This is a simplification. The ESPN API often requires traversing from a list of teams.
        # For now, let's assume we can fetch by team ID if known, or we iterate teams.
        # The spec mentions: "Fetch team rosters which include player stats in the JSON payload."

        # Example: Fetching a specific team's roster
        url = f"{self.BASE_URL}/teams/{team_id_or_slug}/roster"
        resp = requests.get(url)
        if resp.status_code != 200:
            return None
        return resp.json()

    def get_all_teams(self):
        # Fetch list of teams to iterate
        url = f"{self.BASE_URL}/teams?limit=1000"
        resp = requests.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        teams = []
        if "sports" in data:
            for sport in data["sports"]:
                for league in sport["leagues"]:
                    for team in league["teams"]:
                        teams.append(team["team"])
        return teams

import requests
from typing import Dict, List, Any, Optional

from .utils import retry_api_call


class ESPNClient:
    BASE_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

    def __init__(self):
        pass

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_team_roster(self, team_id_or_slug):
        url = f"{self.BASE_URL}/teams/{team_id_or_slug}/roster"
        resp = requests.get(url)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_team_info(self, team_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/teams/{team_id}"
        resp = requests.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        team = data.get("team", {})
        return {
            "id": team.get("id"),
            "name": team.get("displayName", ""),
            "abbreviation": team.get("abbreviation", ""),
            "nickname": team.get("nickname", ""),
            "location": team.get("location", ""),
            "color": team.get("color", ""),
            "alternateColor": team.get("alternateColor", ""),
            "logos": [l.get("href") for l in team.get("logos", [])],
            "venue": team.get("franchise", {}).get("venue", {}).get("fullName", ""),
        }

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_team_statistics(self, team_id: str, season: str = None) -> Optional[Dict]:
        url = f"{self.BASE_URL}/teams/{team_id}/statistics"
        if season:
            url += f"?season={season}"
        resp = requests.get(url)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_player_stats(self, athlete_id: str) -> Optional[Dict]:
        url = f"http://site.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{athlete_id}/stats"
        resp = requests.get(url)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_all_teams(self) -> List[Dict]:
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
                        t = team["team"]
                        t["logos"] = [l.get("href") for l in t.get("logos", [])]
                        teams.append(t)
        return teams

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_rankings(self, season: str = None) -> List[Dict]:
        url = f"{self.BASE_URL}/rankings"
        if season:
            url += f"?season={season}"
        resp = requests.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        rankings = []
        for rank_list in data.get("rankings", []):
            if rank_list.get("type") == "ap":
                for r in rank_list.get("ranks", []):
                    team = r.get("team", {})
                    rankings.append({
                        "rank": r.get("current"),
                        "team_id": team.get("id"),
                        "team_name": team.get("name"),
                        "logo": team.get("logo"),
                    })
                break
        return rankings

    def get_tournament_teams(self, season: str = None, limit: int = 68) -> List[Dict]:
        rankings = self.get_rankings(season)
        if rankings:
            return rankings[:limit]
        teams = self.get_all_teams()
        return teams[:limit]

import requests
from typing import Dict, List, Any, Optional

from .utils import retry_api_call

REQUEST_TIMEOUT = 30  # seconds - timeout for all ESPN API requests


class ESPNClient:
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

    def __init__(self):
        pass

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_team_roster(self, team_id_or_slug, season: str = None):
        url = f"{self.BASE_URL}/teams/{team_id_or_slug}/roster"
        if season:
            url += f"?season={season}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_team_info(self, team_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/teams/{team_id}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
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
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_player_stats(self, athlete_id: str) -> Optional[Dict]:
        url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{athlete_id}/stats"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_all_teams(self) -> List[Dict]:
        url = f"{self.BASE_URL}/teams?limit=1000"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
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
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []
        data = resp.json()
        rankings = []
        for rank_list in data.get("rankings", []):
            if rank_list.get("type") == "ap":
                for r in rank_list.get("ranks", []):
                    team = r.get("team", {})
                    rankings.append(
                        {
                            "rank": r.get("current"),
                            "team_id": team.get("id"),
                            "team_name": team.get("name"),
                            "logo": team.get("logo"),
                        }
                    )
                break
        return rankings

    def get_tournament_teams(self, season: str = None, limit: int = 68) -> List[Dict]:
        # For 2016, use precise dates for First Round to ensure correct field
        if season == "2016":
            dates = ["20160317", "20160318"]
            teams_map = {}
            for date in dates:
                url = f"{self.BASE_URL}/scoreboard?dates={date}&limit=100"
                try:
                    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                    if resp.status_code == 200:
                        events = resp.json().get("events", [])
                        for event in events:
                            for competition in event.get("competitions", []):
                                for competitor in competition.get("competitors", []):
                                    team = competitor.get("team", {})
                                    tid = team.get("id")
                                    if tid and tid not in teams_map:
                                        # Normalize team object to match get_all_teams structure
                                        t_obj = {
                                            "id": tid,
                                            "displayName": team.get("displayName"),
                                            "abbreviation": team.get("abbreviation"),
                                            "shortDisplayName": team.get(
                                                "shortDisplayName"
                                            ),
                                            "location": team.get("location"),
                                            "color": team.get("color"),
                                            "alternateColor": team.get(
                                                "alternateColor"
                                            ),
                                            "logos": [
                                                l.get("href")
                                                for l in team.get("logos", [])
                                            ],
                                            "slug": (
                                                team.get("uid", "").split(":")[-1]
                                                if "uid" in team
                                                else tid
                                            ),
                                            "game_id": event.get("id"),
                                        }
                                        teams_map[tid] = t_obj
                except Exception:
                    pass

            if teams_map:
                print(f"DEBUG: Found {len(teams_map)} tournament teams via scoreboard dates.")
                return list(teams_map.values())

        # Fallback to rankings or all teams
        print(f"DEBUG: Falling back to rankings/all teams (season={season})")
        rankings = self.get_rankings(season)
        if rankings:
            return rankings[:limit]
        teams = self.get_all_teams()
        return teams[:limit]

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_athlete_bio(self, athlete_id: str) -> Optional[Dict]:
        """Fetch detailed athlete bio (height, weight, etc.) from common API."""
        url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{athlete_id}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_athlete_bio(self, athlete_id: str) -> Optional[Dict]:
        """Fetch detailed athlete bio (height, weight, etc.) from common API."""
        url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{athlete_id}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()

    @retry_api_call(max_retries=3, initial_backoff=10, backoff_factor=1.5)
    def get_game_roster(self, game_id: str, team_id: str) -> List[Dict]:
        """Fetch roster from a specific game boxscore."""
        url = f"{self.BASE_URL}/summary?event={game_id}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        data = resp.json()
        boxscore = data.get("boxscore", {})

        # Checking 'boxscore' -> 'players' structure in summary endpoint
        roster = []
        players_section = boxscore.get("players", [])
        for section in players_section:
            if str(section.get("team", {}).get("id")) == str(team_id):
                stats = section.get("statistics", [])
                if stats:
                    athletes = stats[0].get("athletes", [])
                    for ath in athletes:
                        ath_obj = ath.get("athlete", {})
                        if ath_obj:
                            roster.append(
                                {
                                    "id": ath_obj.get("id"),
                                    "fullName": ath_obj.get("displayName"),
                                    "displayName": ath_obj.get("displayName"),
                                    "position": ath_obj.get("position", {}).get(
                                        "abbreviation", "G"
                                    ),
                                    "jersey": ath_obj.get("jersey"),
                                    "height": ath_obj.get("displayHeight"),
                                    "weight": ath_obj.get("displayWeight"),
                                }
                            )
        return roster

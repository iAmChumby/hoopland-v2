import logging
from typing import Dict, List, Optional, Any
import pandas as pd

from .utils import retry_api_call

logger = logging.getLogger(__name__)

HOOPR_BASE_URL = "https://raw.githubusercontent.com/sportsdataverse/hoopR-mbb-data/main/mbb/player_box/parquet"


class CollegeClient:
    def __init__(self):
        self._cache: Dict[int, pd.DataFrame] = {}

    def _get_season_data(self, year: int) -> Optional[pd.DataFrame]:
        if year in self._cache:
            return self._cache[year]

        url = f"{HOOPR_BASE_URL}/player_box_{year}.parquet"
        try:
            df = pd.read_parquet(url)
            self._cache[year] = df
            return df
        except Exception as e:
            logger.warning(f"Failed to fetch college data for {year}: {e}")
            return None

    def get_player_season_stats(
        self, player_name: str, team_name: str, year: int
    ) -> Optional[Dict[str, Any]]:
        df = self._get_season_data(year)
        if df is None:
            return None

        name_lower = player_name.lower()
        team_lower = team_name.lower()

        matches = df[
            (df["athlete_display_name"].str.lower() == name_lower)
            | (df["athlete_display_name"].str.lower().str.contains(name_lower.split()[-1], na=False))
        ]

        if len(matches) == 0:
            return None

        if len(matches) > 1 and team_name:
            team_matches = matches[
                matches["team_display_name"].str.lower().str.contains(team_lower, na=False)
                | matches["team_name"].str.lower().str.contains(team_lower, na=False)
            ]
            if len(team_matches) > 0:
                matches = team_matches

        agg_stats = {
            "player_name": matches["athlete_display_name"].iloc[0],
            "team_name": matches["team_display_name"].iloc[0],
            "games_played": len(matches),
            "minutes": matches["minutes"].sum(),
            "field_goals_made": matches["field_goals_made"].sum(),
            "field_goals_attempted": matches["field_goals_attempted"].sum(),
            "three_point_field_goals_made": matches["three_point_field_goals_made"].sum(),
            "three_point_field_goals_attempted": matches["three_point_field_goals_attempted"].sum(),
            "free_throws_made": matches["free_throws_made"].sum(),
            "free_throws_attempted": matches["free_throws_attempted"].sum(),
            "offensive_rebounds": matches["offensive_rebounds"].sum(),
            "defensive_rebounds": matches["defensive_rebounds"].sum(),
            "rebounds": matches["rebounds"].sum(),
            "assists": matches["assists"].sum(),
            "steals": matches["steals"].sum(),
            "blocks": matches["blocks"].sum(),
            "turnovers": matches["turnovers"].sum(),
            "points": matches["points"].sum(),
            "position": matches["athlete_position_name"].iloc[0] if "athlete_position_name" in matches.columns else None,
            "headshot_url": matches["athlete_headshot_href"].iloc[0] if "athlete_headshot_href" in matches.columns else None,
        }

        return agg_stats

    def search_player_by_name(
        self, player_name: str, college_name: str, draft_year: int
    ) -> Optional[Dict[str, Any]]:
        for year_offset in range(4):
            search_year = draft_year - year_offset
            if search_year < 2003:
                break

            stats = self.get_player_season_stats(player_name, college_name, search_year)
            if stats and stats["games_played"] >= 5:
                stats["college_year"] = search_year
                return stats

        return None

    def get_player_college_career(
        self, player_name: str, college_name: str, draft_year: int, max_years: int = 4
    ) -> List[Dict[str, Any]]:
        career_stats = []

        for year_offset in range(max_years):
            search_year = draft_year - year_offset
            if search_year < 2003:
                break

            stats = self.get_player_season_stats(player_name, college_name, search_year)
            if stats and stats["games_played"] >= 5:
                stats["season"] = search_year
                career_stats.append(stats)

        return career_stats

    def aggregate_college_stats(self, career_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not career_stats:
            return {}

        totals = {
            "games_played": 0,
            "minutes": 0,
            "field_goals_made": 0,
            "field_goals_attempted": 0,
            "three_point_field_goals_made": 0,
            "three_point_field_goals_attempted": 0,
            "free_throws_made": 0,
            "free_throws_attempted": 0,
            "offensive_rebounds": 0,
            "defensive_rebounds": 0,
            "rebounds": 0,
            "assists": 0,
            "steals": 0,
            "blocks": 0,
            "turnovers": 0,
            "points": 0,
        }

        for season in career_stats:
            for key in totals:
                totals[key] += season.get(key, 0) or 0

        gp = totals["games_played"] or 1
        return {
            "career_totals": totals,
            "seasons": len(career_stats),
            "per_game": {
                "ppg": round(totals["points"] / gp, 1),
                "rpg": round(totals["rebounds"] / gp, 1),
                "apg": round(totals["assists"] / gp, 1),
                "spg": round(totals["steals"] / gp, 1),
                "bpg": round(totals["blocks"] / gp, 1),
                "mpg": round(totals["minutes"] / gp, 1),
            },
            "shooting": {
                "fg_pct": round(totals["field_goals_made"] / max(totals["field_goals_attempted"], 1) * 100, 1),
                "three_pct": round(totals["three_point_field_goals_made"] / max(totals["three_point_field_goals_attempted"], 1) * 100, 1),
                "ft_pct": round(totals["free_throws_made"] / max(totals["free_throws_attempted"], 1) * 100, 1),
            },
            "player_name": career_stats[0].get("player_name"),
            "team_name": career_stats[0].get("team_name"),
            "position": career_stats[0].get("position"),
        }

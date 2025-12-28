import os
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

_historical_teams_cache: Optional[Dict[str, Any]] = None


def _load_historical_teams() -> Dict[str, Any]:
    global _historical_teams_cache
    if _historical_teams_cache is not None:
        return _historical_teams_cache

    data_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(data_dir, "historical_teams.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _historical_teams_cache = json.load(f)
    except FileNotFoundError:
        logger.error(f"Historical teams file not found: {json_path}")
        _historical_teams_cache = {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse historical teams JSON: {e}")
        _historical_teams_cache = {}

    return _historical_teams_cache


def get_team_for_year(nba_team_id: str, year: int) -> Dict[str, Any]:
    historical_data = _load_historical_teams()
    team_id = str(nba_team_id)

    if team_id not in historical_data:
        return {}

    team_record = historical_data[team_id]
    history = team_record.get("history", [])

    for era in history:
        years = era.get("years", [])
        if len(years) < 2:
            continue

        start_year = years[0]
        end_year = years[1]

        if end_year is None:
            if year >= start_year:
                return {
                    "city": era.get("city", ""),
                    "name": era.get("name", ""),
                    "tag": era.get("tag", ""),
                    "arena": era.get("arena", ""),
                    "colors": era.get("colors", []),
                    "logoURL": era.get("logoURL", "")
                }
        else:
            if start_year <= year < end_year:
                return {
                    "city": era.get("city", ""),
                    "name": era.get("name", ""),
                    "tag": era.get("tag", ""),
                    "arena": era.get("arena", ""),
                    "colors": era.get("colors", []),
                    "logoURL": era.get("logoURL", "")
                }

    if history:
        latest = history[-1]
        return {
            "city": latest.get("city", ""),
            "name": latest.get("name", ""),
            "tag": latest.get("tag", ""),
            "arena": latest.get("arena", ""),
            "colors": latest.get("colors", []),
            "logoURL": latest.get("logoURL", "")
        }

    return {}


def get_team_logo_url(nba_team_id: str, year: int) -> str:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("logoURL", "")


def get_team_arena(nba_team_id: str, year: int) -> str:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("arena", "")


def get_team_colors(nba_team_id: str, year: int) -> List[str]:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("colors", [])


def get_team_city(nba_team_id: str, year: int) -> str:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("city", "")


def get_team_name(nba_team_id: str, year: int) -> str:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("name", "")


def get_team_tag(nba_team_id: str, year: int) -> str:
    team_data = get_team_for_year(nba_team_id, year)
    return team_data.get("tag", "")


def get_all_historical_team_ids() -> List[str]:
    historical_data = _load_historical_teams()
    return list(historical_data.keys())


def team_existed_in_year(nba_team_id: str, year: int) -> bool:
    historical_data = _load_historical_teams()
    team_id = str(nba_team_id)

    if team_id not in historical_data:
        return False

    team_record = historical_data[team_id]
    history = team_record.get("history", [])

    if not history:
        return False

    earliest_year = history[0].get("years", [9999])[0]
    return year >= earliest_year

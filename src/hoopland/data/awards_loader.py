import os
import json
import logging
import re
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

_AWARD_TYPES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "award_types.json")
_AWARD_TYPES_CACHE: Optional[Dict[str, Any]] = None


def _load_award_types() -> Dict[str, Any]:
    global _AWARD_TYPES_CACHE
    if _AWARD_TYPES_CACHE is not None:
        return _AWARD_TYPES_CACHE

    try:
        with open(_AWARD_TYPES_PATH, "r", encoding="utf-8") as f:
            _AWARD_TYPES_CACHE = json.load(f)
    except FileNotFoundError:
        logger.error(f"Award types file not found: {_AWARD_TYPES_PATH}")
        _AWARD_TYPES_CACHE = {"award_types": {}, "nba_api_description_map": {}, "all_nba_team_number_map": {}}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse award types JSON: {e}")
        _AWARD_TYPES_CACHE = {"award_types": {}, "nba_api_description_map": {}, "all_nba_team_number_map": {}}

    return _AWARD_TYPES_CACHE


def _extract_season_year(season_str: str) -> Optional[int]:
    if not season_str:
        return None

    match = re.match(r"(\d{4})", str(season_str))
    if match:
        return int(match.group(1)) + 1
    return None


def _map_award_description_to_id(description: str, all_nba_team_number: Optional[int] = None) -> Optional[int]:
    award_types = _load_award_types()
    api_map = award_types.get("nba_api_description_map", {})
    team_number_map = award_types.get("all_nba_team_number_map", {})

    if "All-NBA" in description and all_nba_team_number:
        return team_number_map.get(str(all_nba_team_number), 7)

    for key, award_id in api_map.items():
        if key.lower() in description.lower():
            return award_id

    return None


def process_player_awards(awards_df: pd.DataFrame, max_year: int) -> List[Dict[str, Any]]:
    if awards_df.empty:
        return []

    awards_by_id: Dict[int, Dict[str, Any]] = {}

    for _, row in awards_df.iterrows():
        description = row.get("DESCRIPTION", "")
        season_str = row.get("SEASON", "")
        all_nba_team_number = row.get("ALL_NBA_TEAM_NUMBER")

        if pd.isna(all_nba_team_number):
            all_nba_team_number = None
        else:
            all_nba_team_number = int(all_nba_team_number)

        award_year = _extract_season_year(season_str)

        if award_year is None or award_year > max_year:
            continue

        award_id = _map_award_description_to_id(description, all_nba_team_number)

        if award_id is None:
            continue

        if award_id not in awards_by_id:
            position = all_nba_team_number if all_nba_team_number else 0
            awards_by_id[award_id] = {
                "id": award_id,
                "league": 0,
                "yearsWon": [],
                "position": position,
            }

        if award_year not in awards_by_id[award_id]["yearsWon"]:
            awards_by_id[award_id]["yearsWon"].append(award_year)

    for award_data in awards_by_id.values():
        award_data["yearsWon"].sort()

    return list(awards_by_id.values())

"""
Team assets module for generating team-specific data.

Provides lookup data and generation functions for front office,
court designs, uniforms, and other team-specific assets.
"""

import json
import os
from typing import Dict, List, Any, Optional

# Load team data from JSON
_TEAM_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "team_data.json")
_TEAM_DATA: Dict[str, Dict] = {}

_NCAA_TEAM_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ncaa_team_data.json")
_NCAA_TEAM_DATA: Dict[str, Dict] = {}
_NCAA_TEAM_BY_ID: Dict[str, Dict] = {}

_CHAMPIONSHIPS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "championships.json")
_CHAMPIONSHIPS_DATA: Dict[str, Dict] = {}

_ANNOUNCERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "announcers.json")
_ANNOUNCERS_DATA: Dict[str, Any] = {}

_NCAA_CHAMPIONSHIPS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ncaa_championships.json")
_NCAA_CHAMPIONSHIPS_DATA: Dict[str, Any] = {}


def _load_team_data() -> Dict[str, Dict]:
    """Load team data from JSON file."""
    global _TEAM_DATA
    if not _TEAM_DATA:
        try:
            with open(_TEAM_DATA_PATH, "r") as f:
                _TEAM_DATA = json.load(f)
        except FileNotFoundError:
            _TEAM_DATA = {}
    return _TEAM_DATA


def _load_championships_data() -> Dict[str, Dict]:
    """Load championships data from JSON file."""
    global _CHAMPIONSHIPS_DATA
    if not _CHAMPIONSHIPS_DATA:
        try:
            with open(_CHAMPIONSHIPS_PATH, "r") as f:
                _CHAMPIONSHIPS_DATA = json.load(f)
        except FileNotFoundError:
            _CHAMPIONSHIPS_DATA = {}
    return _CHAMPIONSHIPS_DATA


def _load_announcers_data() -> Dict[str, Any]:
    """Load announcers data from JSON file."""
    global _ANNOUNCERS_DATA
    if not _ANNOUNCERS_DATA:
        try:
            with open(_ANNOUNCERS_PATH, "r") as f:
                _ANNOUNCERS_DATA = json.load(f)
        except FileNotFoundError:
            _ANNOUNCERS_DATA = {}
    return _ANNOUNCERS_DATA


def _load_ncaa_team_data() -> Dict[str, Dict]:
    """Load NCAA team data from JSON file."""
    global _NCAA_TEAM_DATA, _NCAA_TEAM_BY_ID
    if not _NCAA_TEAM_DATA:
        try:
            with open(_NCAA_TEAM_DATA_PATH, "r") as f:
                _NCAA_TEAM_DATA = json.load(f)
            for slug, data in _NCAA_TEAM_DATA.items():
                _NCAA_TEAM_BY_ID[str(data.get("target_id", ""))] = data
                _NCAA_TEAM_BY_ID[data.get("uuid", "")] = data
        except FileNotFoundError:
            _NCAA_TEAM_DATA = {}
    return _NCAA_TEAM_DATA


def get_ncaa_team_by_name(team_name: str) -> Optional[Dict]:
    """
    Look up NCAA team data by name or partial match.
    
    Args:
        team_name: Full team name, school name, or mascot (e.g., "Duke", "Duke Blue Devils")
    
    Returns:
        Team data dict or None if not found
    """
    data = _load_ncaa_team_data()
    team_name_lower = team_name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    
    if team_name_lower in data:
        return data[team_name_lower]
    
    for slug, team in data.items():
        if team.get("full_name", "").lower() == team_name.lower():
            return team
        if team.get("school", "").lower() == team_name.lower():
            return team
    
    for slug, team in data.items():
        if team_name_lower in slug:
            return team
    
    return None


def get_ncaa_team_by_espn_id(espn_id: str) -> Optional[Dict]:
    """
    Look up NCAA team data by ESPN team ID.
    
    Args:
        espn_id: ESPN API team ID
    
    Returns:
        Team data dict or None if not found
    """
    _load_ncaa_team_data()
    return _NCAA_TEAM_BY_ID.get(str(espn_id))


def get_ncaa_team_colors(team_name: str) -> List[str]:
    """Get NCAA team colors as array of 3 hex strings."""
    team = get_ncaa_team_by_name(team_name)
    if team:
        return team.get("colors", ["CC0000", "FFFFFF", "000000"])
    return ["CC0000", "FFFFFF", "000000"]


def get_ncaa_team_info(team_name: str) -> Dict[str, Any]:
    """
    Get full NCAA team info for generation.
    
    Args:
        team_name: Team name to look up
    
    Returns:
        Dict with school, name, tag, colors, target_id
    """
    team = get_ncaa_team_by_name(team_name)
    if team:
        return {
            "school": team.get("school", team_name),
            "name": team.get("name", "Team"),
            "full_name": team.get("full_name", team_name),
            "tag": team.get("tag", "TM"),
            "colors": team.get("colors", ["CC0000", "FFFFFF", "000000"]),
            "target_id": team.get("target_id", 0),
        }
    return {
        "school": team_name,
        "name": "Team",
        "full_name": team_name,
        "tag": team_name[:3].upper(),
        "colors": ["CC0000", "FFFFFF", "000000"],
        "target_id": 0,
    }


def _load_ncaa_championships_data() -> Dict[str, Any]:
    """Load NCAA championships data from JSON file."""
    global _NCAA_CHAMPIONSHIPS_DATA
    if not _NCAA_CHAMPIONSHIPS_DATA:
        try:
            with open(_NCAA_CHAMPIONSHIPS_PATH, "r") as f:
                _NCAA_CHAMPIONSHIPS_DATA = json.load(f)
        except FileNotFoundError:
            _NCAA_CHAMPIONSHIPS_DATA = {}
    return _NCAA_CHAMPIONSHIPS_DATA


def generate_ncaa_championships(school_name: str, current_year: int = 9999) -> Dict[str, Any]:
    """
    Generate championships object for an NCAA team.
    
    Args:
        school_name: School name to look up (e.g., "Duke", "North Carolina")
        current_year: Filter championships to years before this
    
    Returns:
        Championships dict with yearsWon list
    """
    data = _load_ncaa_championships_data()
    team_champs = data.get("team_championships", {})
    
    name_lower = school_name.lower()
    years_won = []
    
    for team, years in team_champs.items():
        if team.lower() == name_lower or name_lower in team.lower():
            years_won = [y for y in years if y < current_year]
            break
    
    return {
        "id": 1,
        "league": 1,
        "yearsWon": years_won,
        "position": 0,
    }


def generate_ncaa_front_office(team_id: int, team_name: str) -> Dict[str, Any]:
    """Generate front office structure for an NCAA team."""
    team_staff = [
        _generate_front_office_person(
            {"fn": "Head", "ln": "Coach", "age": 50, "appearance": _get_default_appearance()},
            team_id, 0, pos=1
        ),
        _generate_front_office_person(
            {"fn": "Assistant", "ln": "Coach", "age": 40, "appearance": _get_default_appearance()},
            team_id, 1, pos=2
        ),
    ]
    
    return {
        "coins": 0,
        "condition": 0,
        "morale": 0,
        "fans": 0,
        "facilities": [
            {"type": 0, "tier": 2, "upgrade": 0, "condition": 5},
            {"type": 1, "tier": 2, "upgrade": 0, "condition": 5},
        ],
        "staff": team_staff,
        "announcers": _get_default_announcers(team_id),
        "adsURL": "",
        "adSize": 0,
    }


def _get_announcers_for_year(
    nba_team_id: str, year: int = 2024, team_id: int = 0
) -> List[Dict[str, Any]]:
    """
    Get announcers for a team for a specific year as full person objects.

    Checks for historical data matching the year, falls back to current.

    Args:
        nba_team_id: NBA API team ID (e.g., "1610612752")
        year: Target year for announcer lookup
        team_id: Target schema team ID for the announcer's tid field

    Returns:
        List of full announcer person objects
    """
    announcers_data = _load_announcers_data()
    teams_data = announcers_data.get("teams", {})
    team_data = teams_data.get(str(nba_team_id), {})

    if not team_data:
        return _get_default_announcers(team_id)

    historical = team_data.get("historical", {})
    if str(year) in historical:
        era_data = historical[str(year)]
    else:
        era_data = team_data.get("current", {})

    if not era_data:
        return _get_default_announcers(team_id)

    announcers = []
    announcer_id = 0

    pbp = era_data.get("pbp", {})
    if pbp:
        pbp_data = {
            "fn": pbp.get("fn", "Play-by-Play"),
            "ln": pbp.get("ln", "Announcer"),
            "appearance": pbp.get("appearance", _get_default_appearance()),
        }
        announcers.append(
            _generate_front_office_person(pbp_data, team_id, announcer_id, pos=0)
        )
        announcer_id += 1

    color = era_data.get("color", {})
    if color:
        color_data = {
            "fn": color.get("fn", "Color"),
            "ln": color.get("ln", "Commentator"),
            "appearance": color.get("appearance", _get_default_appearance()),
        }
        announcers.append(
            _generate_front_office_person(color_data, team_id, announcer_id, pos=0)
        )

    return announcers if announcers else _get_default_announcers(team_id)


def _get_default_announcers(team_id: int = 0) -> List[Dict[str, Any]]:
    """Return default announcers when team data is not available."""
    pbp_data = {
        "fn": "Play-by-Play",
        "ln": "Announcer",
        "appearance": _get_default_appearance(),
    }
    color_data = {
        "fn": "Color",
        "ln": "Commentator",
        "appearance": _get_default_appearance(),
    }
    return [
        _generate_front_office_person(pbp_data, team_id, 0, pos=0),
        _generate_front_office_person(color_data, team_id, 1, pos=0),
    ]


def _generate_staff(
    team_id: int, nba_team_id: str = "", year: int = 2024
) -> List[Dict[str, Any]]:
    """Generate 4 staff members as full person objects with real names from NBA API."""
    from ..data.nba_client import NBAClient

    staff_defaults = [
        {"fn": "Head", "ln": "Coach", "pos": 1, "gender": 0, "age": 55, "is_assistant": 1},
        {"fn": "Assistant", "ln": "Coach", "pos": 2, "gender": 0, "age": 45, "is_assistant": 2},
        {"fn": "Team", "ln": "Trainer", "pos": 3, "gender": 0, "age": 50, "is_assistant": 3},
        {"fn": "Team", "ln": "Scout", "pos": 4, "gender": 0, "age": 45, "is_assistant": None},
    ]

    coaches_by_type: Dict[int, Dict[str, str]] = {}
    if nba_team_id:
        try:
            client = NBAClient()
            season_str = f"{year-1}-{str(year)[2:]}"
            coaches_df = client.get_coaches(int(nba_team_id), season_str)
            if coaches_df is not None and not coaches_df.empty:
                for is_asst in [1, 2, 3]:
                    matches = coaches_df[coaches_df["IS_ASSISTANT"] == is_asst]
                    if not matches.empty:
                        row = matches.iloc[0]
                        coaches_by_type[is_asst] = {
                            "fn": row["FIRST_NAME"],
                            "ln": row["LAST_NAME"],
                        }
        except Exception:
            pass

    staff = []
    for idx, role in enumerate(staff_defaults):
        is_asst = role["is_assistant"]
        if is_asst and is_asst in coaches_by_type:
            fn = coaches_by_type[is_asst]["fn"]
            ln = coaches_by_type[is_asst]["ln"]
        else:
            fn = role["fn"]
            ln = role["ln"]

        person_data = {
            "fn": fn,
            "ln": ln,
            "age": role["age"],
            "gender": role["gender"],
            "appearance": _get_default_appearance(),
        }
        person = _generate_front_office_person(
            person_data, team_id, person_id=idx, pos=role["pos"]
        )
        staff.append(person)

    return staff


def _get_default_appearance() -> Dict[str, Any]:
    """Return default appearance for announcers."""
    return {
        "skinC": "F0C8A0",
        "eyeC": "3B2D1A",
        "hair": "0040",
        "hairC": "808080",
        "fHair": "0000",
        "fHairC": "808080",
        "unibrow": False,
        "browC": "808080",
    }


def _generate_front_office_suits() -> List[Dict[str, Any]]:
    """Generate 4 suit variants for front office person."""
    base_suit = {
        "headAcc": "0000",
        "headAccC": "000000",
        "jacketC": "262539",
        "shirtC": "FFFFFF",
        "tieC": "800000",
        "pantC": "262539",
        "shoeC": "000000",
        "laceC": "",
        "soleC": "000000",
    }
    return [base_suit.copy() for _ in range(4)]


def _empty_front_office_career_stats() -> Dict[str, Any]:
    """Generate empty career stats block for front office person."""
    return {
        "tid": 0,
        "GP": 0,
        "GS": 0,
        "W": 0,
        "L": 0,
        "HOME": [0, 0],
        "AWAY": [0, 0],
        "DIV": [0, 0],
        "CONF": [0, 0],
        "STRK": 0,
        "L10": [],
        "PTS": 0,
        "OPP": 0,
        "FGM": 0,
        "FGA": 0,
        "TPM": 0,
        "TPA": 0,
        "FTM": 0,
        "FTA": 0,
        "REB": 0,
        "ORB": 0,
        "AST": 0,
        "STL": 0,
        "BLK": 0,
        "TO": 0,
        "PF": 0,
        "MIN": 0,
        "POS": 0,
    }


def _generate_front_office_person(
    person_data: Dict[str, Any], team_id: int, person_id: int = 0, pos: int = 0
) -> Dict[str, Any]:
    """Generate a full person object for front office (announcer or staff)."""
    appearance = dict(person_data.get("appearance", _get_default_appearance()))

    if "eyeC" not in appearance:
        appearance["eyeC"] = appearance.get("browC", "262539")
    if "unibrow" not in appearance:
        appearance["unibrow"] = False

    return {
        "id": person_id,
        "tid": team_id,
        "league": 0,
        "fn": person_data.get("fn", ""),
        "ln": person_data.get("ln", ""),
        "tag": "",
        "home": "",
        "ctry": "US",
        "loc": {"x": 0, "y": 0},
        "age": person_data.get("age", 50),
        "ht": 0,
        "wt": 0,
        "yrs": 0,
        "gender": person_data.get("gender", 0),
        "pos": pos,
        "arc": 0,
        "pri": 0,
        "sec": 0,
        "pot": 0,
        "appearance": appearance,
        "suits": _generate_front_office_suits(),
        "attributes": {
            "development": [0, 0],
            "motivation": [0, 0],
            "leadership": [0, 0],
        },
        "tendencies": {
            "offFocus": 0,
            "offTempo": 0,
            "offRebounding": 0,
            "defFocus": 0,
            "defAggression": 0,
            "defRebounding": 0,
            "benchDepth": 0,
            "benchUtilization": 0,
            "closingLineup": 0,
        },
        "career": {
            "season": _empty_front_office_career_stats(),
            "playoffs": _empty_front_office_career_stats(),
            "finals": _empty_front_office_career_stats(),
            "teamHistory": [],
        },
        "awards": [],
        "contract": {
            "tid": 0,
            "pid": 0,
            "type": 0,
            "yrs": 0,
            "sal": 0,
            "opt": 0,
            "noTrd": False,
            "canExt": True,
            "ext": {"yrs": 0, "sal": 0, "opt": 0, "noTrd": False},
        },
        "status": 0,
        "xp": 0,
        "ap": 0,
        "xpEarned": 0,
        "rp": 0,
        "rpEarned": 0,
        "gameHistory": {"GP": 0, "W": 0, "L": 0},
        "records": 0,
        "tradeRequested": False,
        "retiring": False,
        "yearRetired": 0,
        "following": False,
        "causeOfDeath": 0,
    }


def get_team_data(nba_team_id: str) -> Optional[Dict]:
    """Get team lookup data by NBA API team ID."""
    data = _load_team_data()
    return data.get(str(nba_team_id))


def get_target_team_id(nba_team_id: str) -> int:
    """Map NBA API team ID to target schema team ID."""
    team = get_team_data(nba_team_id)
    if team:
        return team.get("target_id", int(nba_team_id) % 100)
    return int(nba_team_id) % 100


def get_team_colors(nba_team_id: str) -> List[str]:
    """Get team colors as array of 3 hex strings."""
    team = get_team_data(nba_team_id)
    if team:
        return team.get("colors", ["CC0000", "FFFFFF", "000000"])
    return ["CC0000", "FFFFFF", "000000"]


def get_team_location(nba_team_id: str) -> Dict[str, int]:
    """Get team location coordinates for scheduling."""
    team = get_team_data(nba_team_id)
    if team:
        return team.get("location", {"x": 0, "y": 0})
    return {"x": 0, "y": 0}


def get_team_arena(nba_team_id: str) -> str:
    """Get team arena name."""
    team = get_team_data(nba_team_id)
    if team:
        return team.get("arena", "Arena")
    return "Arena"


def get_team_division(nba_team_id: str) -> int:
    """Get team division."""
    team = get_team_data(nba_team_id)
    if team:
        return team.get("division", 0)
    return 0


def generate_front_office(
    team_id: int, team_name: str, nba_team_id: str = "", year: int = 2024
) -> Dict[str, Any]:
    """Generate front office structure for a team."""
    team_announcers = _get_announcers_for_year(nba_team_id, year, team_id)
    team_staff = _generate_staff(team_id, nba_team_id, year)

    return {
        "coins": 0,
        "condition": 0,
        "morale": 0,
        "fans": 0,
        "facilities": [
            {"type": 0, "tier": 3, "upgrade": 0, "condition": 5},
            {"type": 1, "tier": 2, "upgrade": 0, "condition": 5},
            {"type": 2, "tier": 3, "upgrade": 0, "condition": 5},
            {"type": 3, "tier": 2, "upgrade": 0, "condition": 5},
        ],
        "staff": team_staff,
        "announcers": team_announcers,
        "adsURL": "",
        "adSize": 0,
    }


def generate_court(
    team_colors: List[str],
    overlay_url: str = "",
    city: str = "",
    team_name: str = "",
    arena_name: str = "",
    team_index: int = 0
) -> Dict[str, Any]:
    """Generate court design matching game format with variety across teams."""
    wood_patterns = ["lines", "tiled", "parque", "comb", "lines"]
    inner_patterns = ["lines", "tiled", "parque", "comb", "tiled"]
    pattern_idx = team_index % 5
    outer_wood = wood_patterns[pattern_idx]
    inner_wood = inner_patterns[pattern_idx]

    baseline_text = f"{city} {team_name}" if city else team_name

    return {
        "outerWood": outer_wood,
        "outerWoodC": "EEA160",
        "innerWood": inner_wood,
        "innerWoodC": "EEA160",
        "outerFT": outer_wood,
        "outerFTC": "EEA160",
        "innerFT": "flat",
        "innerFTC": "PRI",
        "outerKey": "flat",
        "outerKeyC": "PRI",
        "innerKey": "flat",
        "innerKeyC": "PRI",
        "outerBorder": "SEC",
        "innerBorder": "SEC",
        "outerFloor": "SEC",
        "mediaLines": "FFFFFF",
        "outerLine": "000000",
        "halfCourtLine": "000000",
        "threePointLine": 0,
        "threePointLineC": "000000",
        "outerFTCircle": "000000",
        "innerFTCircle": "000000",
        "outerKeyLine": "000000",
        "innerKeyLine": "000000",
        "logoSize": 200,
        "logoLayer": 2,
        "overlayURL": overlay_url,
        "overlayLayer": 1,
        "baseline1": baseline_text,
        "baseline1C": "FFFFFF",
        "baseline2": baseline_text,
        "baseline2C": "FFFFFF",
        "sideline1": arena_name,
        "sideline1C": "FFFFFF",
        "sideline2": arena_name,
        "sideline2C": "FFFFFF",
        "hoopBase": "PRI",
        "hoopPole": "SEC",
        "polePadding": "SEC",
        "hoopPadding": "PRI",
    }


def generate_uniforms(team_colors: List[str]) -> List[Dict[str, Any]]:
    """Generate 4 uniform designs (home, away, alt1, alt2) based on team colors."""
    primary = team_colors[0] if team_colors else "CC0000"
    secondary = team_colors[1] if len(team_colors) > 1 else "FFFFFF"
    accent = team_colors[2] if len(team_colors) > 2 else "000000"

    # Home uniform (white base)
    home = {
        "jerseyMain": "FFFFFF",
        "jerseySecondary": primary,
        "jerseyStripe": primary,
        "shortsMain": "FFFFFF",
        "shortsSecondary": primary,
        "shortsStripe": primary,
        "numberC": primary,
        "nameC": primary,
        "style": 0,
    }

    # Away uniform (primary color base)
    away = {
        "jerseyMain": primary,
        "jerseySecondary": "FFFFFF",
        "jerseyStripe": secondary,
        "shortsMain": primary,
        "shortsSecondary": "FFFFFF",
        "shortsStripe": secondary,
        "numberC": "FFFFFF",
        "nameC": "FFFFFF",
        "style": 0,
    }

    # Alternate 1 (secondary color base)
    alt1 = {
        "jerseyMain": secondary,
        "jerseySecondary": primary,
        "jerseyStripe": accent,
        "shortsMain": secondary,
        "shortsSecondary": primary,
        "shortsStripe": accent,
        "numberC": accent,
        "nameC": accent,
        "style": 0,
    }

    # Alternate 2 (accent/black base)
    alt2 = {
        "jerseyMain": accent,
        "jerseySecondary": primary,
        "jerseyStripe": secondary,
        "shortsMain": accent,
        "shortsSecondary": primary,
        "shortsStripe": secondary,
        "numberC": primary,
        "nameC": primary,
        "style": 0,
    }

    return [home, away, alt1, alt2]


def generate_player_appearance(app_data: Dict, skin_val: int = 1) -> Dict[str, Any]:
    """
    Generate full appearance object from appearance analysis data.

    Args:
        app_data: Dict with skin_tone, hair, facial_hair from CV analysis
        skin_val: Legacy skin value (1-5) as fallback

    Returns:
        Full appearance dict with hex colors and style IDs
    """
    skin_hex_map = {
        1: "FFE0C8",
        2: "F0C8A0",
        3: "D4A070",
        4: "B08050",
        5: "906848",
        6: "704030",
        7: "502818",
    }

    skin_tone = app_data.get("skin_tone", skin_val)
    skin_color = app_data.get("skinC", skin_hex_map.get(skin_tone, "C68040"))

    # Hair data
    hair_style = app_data.get("hair", "0000")
    hair_color = app_data.get("hairC", "1A1A1A")

    # Facial hair data
    facial_hair_style = app_data.get("facial_hair", 0)
    facial_hair_color = app_data.get("fHairC", "1A1A1A")

    return {
        "skinC": skin_color,
        "eyeC": app_data.get("eyeC", "3B2D1A"),
        "hair": str(hair_style).zfill(4),
        "hairC": hair_color,
        "fHair": str(facial_hair_style).zfill(4),
        "fHairC": facial_hair_color,
        "unibrow": app_data.get("unibrow", False),
        "browC": app_data.get("browC", hair_color),
    }


def generate_player_accessories(skin_val: int = 1) -> List[Dict[str, Any]]:
    """
    Generate 4 accessory configurations (one per uniform).

    Args:
        skin_val: Skin tone value for shoe color matching

    Returns:
        List of 4 accessory dicts
    """
    base_accessory = {
        "headAcc": 0,
        "L_Shoulder": 0,
        "R_Shoulder": 0,
        "L_Elbow": 0,
        "R_Elbow": 0,
        "L_Wrist": 0,
        "R_Wrist": 0,
        "L_Knee": 0,
        "R_Knee": 0,
        "L_Shin": 0,
        "R_Shin": 0,
        "shoeC1": "FFFFFF",
        "shoeC2": "000000",
        "shoeC3": "FF0000",
        "shoeType": 0,
    }

    # Return 4 copies (one for each uniform)
    return [base_accessory.copy() for _ in range(4)]


def generate_player_suits() -> List[Dict[str, Any]]:
    """Generate off-court formal attire."""
    return [
        {
            "headAcc": 0,
            "jacketC": "1A1A1A",
            "shirtC": "FFFFFF",
            "tieC": "7F1A1A",
            "pantC": "1A1A1A",
            "shoeC": "1A1A1A",
        }
    ]


def generate_contract(rating: float, age: int, pot: int = 5) -> Dict[str, Any]:
    """
    Synthesize a contract based on player rating and age.

    Args:
        rating: Player's current overall rating (0-10 scale)
        age: Player's age
        pot: Player's potential

    Returns:
        Contract dict with salary, years, options, etc.
    """
    # Salary and years based on rating
    if rating >= 8:
        sal = 10 + (rating - 8) * 2  # Max ~14
        yrs = 4 if age < 30 else 2
    elif rating >= 6:
        sal = 4 + (rating - 6) * 3  # Mid 4-10
        yrs = 3 if age < 32 else 1
    else:
        sal = 1 + rating / 2  # Minimum 1-3
        yrs = 2 if age < 28 else 1

    # Options based on rating
    opt = 0  # No option
    if rating >= 7:
        opt = 1  # Player option

    # No-trade clause for veterans with high ratings
    no_trd = age >= 30 and rating >= 8

    return {
        "tid": -1,  # Set by caller
        "pid": -1,  # Set by caller
        "type": 0,
        "yrs": int(yrs),
        "sal": round(sal, 2),
        "opt": opt,
        "noTrd": no_trd,
        "canExt": yrs <= 2,
        "ext": 0,
        "bir": True,  # Bird rights assumed
    }


def generate_skills(attributes: Dict[str, List[int]], stats: Dict) -> List[Dict]:
    """
    Assign badge/skills based on attributes and stats.

    Args:
        attributes: Dict of attribute name -> [current, potential]
        stats: Raw stats dict for context

    Returns:
        List of skill dicts
    """
    skills = []
    skill_id = 0

    # Check for shooting badges
    if attributes.get("TPT", [0])[0] >= 7:
        skills.append({"id": 1, "xp": 100, "level": 2, "equipped": True})  # Sharpshooter
        skill_id += 1

    if attributes.get("LAY", [0])[0] >= 7:
        skills.append({"id": 2, "xp": 100, "level": 2, "equipped": True})  # Slasher
        skill_id += 1

    if attributes.get("DNK", [0])[0] >= 8:
        skills.append({"id": 3, "xp": 100, "level": 3, "equipped": True})  # Posterizer
        skill_id += 1

    if attributes.get("PAS", [0])[0] >= 7:
        skills.append({"id": 4, "xp": 100, "level": 2, "equipped": True})  # Dimer
        skill_id += 1

    if attributes.get("DRE", [0])[0] >= 7:
        skills.append({"id": 5, "xp": 100, "level": 2, "equipped": True})  # Rim Protector
        skill_id += 1

    if attributes.get("STL", [0])[0] >= 7:
        skills.append({"id": 6, "xp": 100, "level": 2, "equipped": True})  # Pickpocket
        skill_id += 1

    return skills


def generate_game_status() -> Dict[str, Any]:
    """Generate default game status for a player."""
    return {
        "startPos": 0,
        "stamina": 100.0,
        "gradePoints": 0,
        "healthy": True,
        "injured": False,
        "injuryType": 0,
        "injuryGames": 0,
    }


def generate_empty_stats_block() -> Dict[str, Any]:
    """Generate empty stats block."""
    return {
        "GP": 0,
        "GS": 0,
        "W": 0,
        "L": 0,
        "MIN": 0.0,
        "PTS": 0.0,
        "AST": 0.0,
        "TRB": 0.0,
        "ORB": 0.0,
        "DRB": 0.0,
        "STL": 0.0,
        "BLK": 0.0,
        "TOV": 0.0,
        "FGM": 0.0,
        "FGA": 0.0,
        "FGP": 0.0,
        "TPM": 0.0,
        "TPA": 0.0,
        "TPP": 0.0,
        "FTM": 0.0,
        "FTA": 0.0,
        "FTP": 0.0,
        "PF": 0.0,
        "PER": 0.0,
    }


def generate_player_history(
    college: str = "",
    draft_year: int = 0,
    draft_rd: int = 0,
    draft_pk: int = 0,
    years_exp: int = 0,
) -> Dict[str, Any]:
    """Generate player history object."""
    return {
        "coll": college,
        "collegeStats": [],
        "draftYear": draft_year,
        "draftRd": draft_rd,
        "draftPk": draft_pk,
        "draftTid": -1,
        "yearsExp": years_exp,
        "injuries": [],
    }


def generate_championships(nba_team_id: str = "", current_year: int = 9999) -> Dict[str, Any]:
    """Generate championships object for a team, filtered to years before current_year."""
    championships_data = _load_championships_data()
    team_id = str(nba_team_id)

    team_champs = championships_data.get(team_id, {})
    all_years = team_champs.get("championships", [])

    years_won = [y for y in all_years if y < current_year]

    return {
        "id": 1,
        "league": 0,
        "yearsWon": years_won,
        "position": 0,
    }


def generate_draft_picks(team_id: int, year: int) -> List[Dict[str, Any]]:
    """Generate default draft picks for current and next year."""
    return [
        {"year": year, "round": 1, "original_tid": team_id, "current_tid": team_id},
        {"year": year, "round": 2, "original_tid": team_id, "current_tid": team_id},
        {"year": year + 1, "round": 1, "original_tid": team_id, "current_tid": team_id},
        {"year": year + 1, "round": 2, "original_tid": team_id, "current_tid": team_id},
    ]

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

_CHAMPIONSHIPS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "championships.json")
_CHAMPIONSHIPS_DATA: Dict[str, Dict] = {}

_ANNOUNCERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "announcers.json")
_ANNOUNCERS_DATA: Dict[str, List[str]] = {}


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


def _load_announcers_data() -> Dict[str, List[str]]:
    """Load announcers data from JSON file."""
    global _ANNOUNCERS_DATA
    if not _ANNOUNCERS_DATA:
        try:
            with open(_ANNOUNCERS_PATH, "r") as f:
                _ANNOUNCERS_DATA = json.load(f)
        except FileNotFoundError:
            _ANNOUNCERS_DATA = {}
    return _ANNOUNCERS_DATA


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


def generate_front_office(team_id: int, team_name: str, nba_team_id: str = "") -> Dict[str, Any]:
    """Generate front office structure for a team."""
    announcers_data = _load_announcers_data()
    team_announcers = announcers_data.get(str(nba_team_id), ["Home Announcer", "Color Commentator"])

    return {
        "coins": 1000000,
        "condition": 100.0,
        "morale": 75.0,
        "fans": 50000,
        "facilities": [
            {"type": 0, "tier": 1, "upgrade": 0, "condition": 100.0},
            {"type": 1, "tier": 1, "upgrade": 0, "condition": 100.0},
            {"type": 2, "tier": 1, "upgrade": 0, "condition": 100.0},
        ],
        "staff": [
            {"fn": "Head", "ln": "Coach", "rating": 70, "type": 0},
            {"fn": "Assistant", "ln": "Coach", "rating": 60, "type": 1},
            {"fn": "General", "ln": "Manager", "rating": 65, "type": 2},
        ],
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

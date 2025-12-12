from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Meta:
    saveName: str = "Hoopland File"
    buildVersion: str = "1.0"
    uPID: str = ""
    uTID: str = ""
    uGID: str = ""
    dataType: str = ""  # "League" or "Draft Class"
    countryGeneration: int = 0
    generatedCountries: int = 0
    gender: int = 0
    filesize: int = 0


@dataclass
class Award:
    id: int
    name: str
    shortName: str
    # Add other award fields as generic dict or specific fields if critical
    # For now, capturing key structure
    team: Optional[int] = None
    # ... potentially many other stats fields


@dataclass
class Player:
    id: int
    tid: int  # Team ID (-1 for free agent/draft)
    fn: str  # First Name
    ln: str  # Last Name
    # We will likely need a comprehensive set of fields here
    # For brevity in this initial pass, we'll map the essential ones
    # and maybe use a catch-all for the rest if strictly necessary,
    # but explicit is better for generation.

    # Biography
    age: int = 0
    ctry: int = 0  # Country
    ht: int = 0  # Height
    wt: int = 0  # Weight
    pos: int = 0

    # Ratings/Skills
    rating: int = 0
    pot: int = 0  # Potential

    # Appearance
    appearance: int = 0
    accessories: Optional[Dict] = field(default_factory=dict)

    # Attributes & Skills (Nested dicts in JSON, maybe flat or specific structs here)
    attributes: Dict[str, Any] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    tendencies: Dict[str, Any] = field(default_factory=dict)

    # Stats/History
    stats: Dict[str, Any] = field(default_factory=dict)
    careerStats: List[Any] = field(default_factory=list)
    awards: List[Any] = field(default_factory=list)

    # Contract
    contract: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Team:
    id: int
    city: str
    name: str
    shortName: str
    abbrev: str = ""  # Note: 'tag' in JSON? JSON analysis showed 'tag'

    # Roster
    roster: List[Player] = field(default_factory=list)

    # Details
    arenaName: str = ""
    logoURL: str = ""
    division: int = 0
    teamColors: Dict[str, str] = field(default_factory=dict)  # primary, secondary etc.

    # Lineups (simplified for now)
    startingLineup: List[int] = field(default_factory=list)

    # Properties
    championships: int = 0
    rnk: int = 0


@dataclass
class League:
    leagueName: str
    # Basic Info
    shortName: str = ""
    logoURL: str = ""
    logoSize: int = 0
    leagueType: int = 0

    # Metadata
    meta: Meta = field(default_factory=Meta)

    # Structure
    conferences: List[Dict] = field(default_factory=list)
    divisions: List[Dict] = field(default_factory=list)
    teams: List[Team] = field(default_factory=list)

    # Players
    freeAgents: List[Player] = field(default_factory=list)
    draftClass: List[Player] = field(default_factory=list)  # "draftClass" in JSON

    # Staff / Others
    coaches: List[Any] = field(default_factory=list)
    referee: Dict = field(default_factory=dict)
    commissioner: Dict = field(default_factory=dict)

    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)
    rules: Dict[str, Any] = field(default_factory=dict)
    sliders: Dict[str, Any] = field(default_factory=dict)

    # Season State
    season: Dict[str, Any] = field(default_factory=dict)

    # Game State
    currentGame: Optional[Dict] = None

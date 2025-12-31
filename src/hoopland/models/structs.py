"""
Core data structures for Hoopland league generation.

These dataclasses represent the main entities (Player, Team, League) matching
the nba0203.txt target schema format.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .schemas import (
    Appearance,
    Accessory,
    Suit,
    Contract,
    Award,
    Skill,
    GameStatus,
    CareerStats,
    PlayerHistory,
    FrontOffice,
    CourtDesign,
    UniformDesign,
    Championships,
    DraftPick,
    Person,
    GameSettings,
    SimulationSliders,
    Difficulty,
)


@dataclass
class Meta:
    """League metadata matching target schema."""

    saveName: str = "Hoopland File"
    buildVersion: str = "1.0"
    uPID: int = -1  # User-controlled player ID (int in target)
    uTID: int = -1  # User-controlled team ID (int in target)
    uGID: int = 0  # User game ID
    dataType: int = 1  # 1=League, 2=Draft Class (int in target)
    countryGeneration: int = 0
    generatedCountries: List[int] = field(default_factory=list)  # Array in target
    gender: int = 0
    filesize: int = 0


@dataclass
class Player:
    """
    Player entity matching target schema.

    Key changes from original:
    - appearance: Dict (was int)
    - accessories: List of 4 Dicts (was single Dict)
    - attributes: Dict[str, List[int]] with 15 keys (was 6)
    - Added: tag, home, num, league, gameStatus, skills, contract, history, etc.
    """

    id: int
    tid: int  # Team ID (-1 for free agent/draft)
    fn: str  # First Name
    ln: str  # Last Name

    # Identity
    tag: str = ""  # Nickname/tag
    home: str = ""  # Home city
    num: int = 0  # Jersey number
    gender: int = 0  # 0=male, 1=female
    league: int = 0  # League ID

    # Biography
    age: int = 0
    yrs: int = 0  # Years of experience
    ctry: int = 0  # Country code (int)
    ht: int = 0  # Height in inches
    wt: int = 0  # Weight in lbs
    pos: int = 0  # Position (0=PG, 1=SG, 2=SF, 3=PF, 4=C)

    # Team position info
    teamPos: int = 0  # Position on team roster
    posRnk: int = 0  # Position ranking
    linePos: int = 0  # Lineup position

    # Ratings
    rating: float = 0.0  # Overall rating (float in target)
    pot: float = 0.0  # Potential
    minutes: List[float] = field(default_factory=list)  # Minutes by position
    usage: float = 0.0
    pri: int = 0  # Primary position
    sec: int = 0  # Secondary position
    arc: int = 0  # Archetype
    regressionAge: int = 30  # Age at which regression begins

    # Appearance - Dict with hex colors and style IDs
    appearance: Dict[str, Any] = field(default_factory=dict)

    # Accessories - List of 4 dicts (one per uniform)
    accessories: List[Dict[str, Any]] = field(default_factory=list)

    # Suits - Off-court attire
    suits: List[Dict[str, Any]] = field(default_factory=list)

    # Attributes - 15 keys with [current, potential] arrays
    attributes: Dict[str, List[int]] = field(default_factory=dict)

    # Tendencies
    tendencies: Dict[str, Any] = field(default_factory=dict)

    # Skills/Badges
    skills: List[Dict[str, Any]] = field(default_factory=list)

    # Game status
    gameStatus: Dict[str, Any] = field(default_factory=dict)
    gameStats: Dict[str, Any] = field(default_factory=dict)

    # Season stats
    season: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    careerStats: Dict[str, Any] = field(default_factory=dict)

    # Awards
    awards: List[Dict[str, Any]] = field(default_factory=list)

    # History
    history: Dict[str, Any] = field(default_factory=dict)
    careerGoals: Dict[str, Any] = field(default_factory=dict)

    # Contract
    contract: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: int = 0  # 0=active, 1=injured, 2=retired
    records: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Team:
    """
    Team entity matching target schema.

    Key changes from original:
    - teamColors: List of 3 hex strings (was Dict)
    - Added: location, frontOffice, inbox, uniforms, court, draftPicks, etc.
    """

    id: int
    city: str
    name: str
    shortName: str
    tag: str = ""  # Abbreviation (e.g., "ATL")
    arenaName: str = ""
    logoURL: str = ""
    division: int = 0

    # Location for travel/scheduling
    location: Dict[str, int] = field(default_factory=dict)  # {x, y}

    # Roster
    roster: List[Player] = field(default_factory=list)

    # Colors - Array of 3 hex strings
    teamColors: List[str] = field(default_factory=list)

    # Front Office
    frontOffice: Dict[str, Any] = field(default_factory=dict)

    # Inbox/notifications
    inbox: List[Dict[str, Any]] = field(default_factory=list)

    # Uniforms - Array of 4 uniform designs
    uniforms: List[Dict[str, Any]] = field(default_factory=list)

    # Court design
    court: Dict[str, Any] = field(default_factory=dict)

    # Lineups
    startingLineup: List[int] = field(default_factory=list)
    currentLineup: List[int] = field(default_factory=list)
    lineupPreset: int = 0

    # Draft picks owned
    draftPicks: List[Dict[str, Any]] = field(default_factory=list)

    # Retired numbers
    retiredNumbers: List[Dict[str, Any]] = field(default_factory=list)

    # Season data
    season: List[Dict[str, Any]] = field(default_factory=list)

    # Historical data
    history: Dict[str, Any] = field(default_factory=dict)
    headToHeads: Dict[str, Any] = field(default_factory=dict)

    # Playbook
    scoringOptions: Dict[str, Any] = field(default_factory=dict)
    quickPlays: List[int] = field(default_factory=list)

    # Misc
    coinFlip: int = 0
    status: int = 0
    rnk: int = 0

    # Championships
    championships: Dict[str, Any] = field(default_factory=dict)


@dataclass
class League:
    """
    League entity matching target schema.

    Key changes from original:
    - meta.uPID/uTID/uGID as int, generatedCountries as array
    - Added: currentGame, commissioner, referee, starTeams, etc.
    """

    leagueName: str

    # Basic Info
    shortName: str = ""
    logoURL: str = ""
    logoSize: int = 0
    leagueType: int = 0  # 0=NBA, 1=NCAA, etc.

    # Metadata
    meta: Meta = field(default_factory=Meta)

    # Structure
    conferences: List[Dict[str, Any]] = field(default_factory=list)
    divisions: List[Dict[str, Any]] = field(default_factory=list)
    teams: List[Team] = field(default_factory=list)

    # Players
    freeAgents: List[Player] = field(default_factory=list)
    draftClass: List[Player] = field(default_factory=list)
    retirees: List[Player] = field(default_factory=list)
    hallOfFame: List[Dict[str, Any]] = field(default_factory=list)

    # Staff
    coaches: List[Dict[str, Any]] = field(default_factory=list)
    referee: Dict[str, Any] = field(default_factory=dict)
    commissioner: Dict[str, Any] = field(default_factory=dict)

    # Star/All-Star teams
    starTeams: List[Dict[str, Any]] = field(default_factory=list)

    # Media/presentation
    gameballs: List[Dict[str, Any]] = field(default_factory=list)
    media: Dict[str, Any] = field(default_factory=dict)
    threePointContestants: List[int] = field(default_factory=list)

    # Contracts/offers
    contractOffers: List[Dict[str, Any]] = field(default_factory=list)

    # Awards
    awards: List[Dict[str, Any]] = field(default_factory=list)

    # Records
    records: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)
    rules: Dict[str, Any] = field(default_factory=dict)
    sliders: Dict[str, Any] = field(default_factory=dict)

    # Difficulty/simulation
    difficulty: Dict[str, Any] = field(default_factory=dict)
    simulationSliders: Dict[str, Any] = field(default_factory=dict)
    optimization: Dict[str, Any] = field(default_factory=dict)
    coachSettings: Dict[str, Any] = field(default_factory=dict)

    # Career mode
    career: Dict[str, Any] = field(default_factory=dict)

    # Season State
    season: Dict[str, Any] = field(default_factory=dict)

    # Game State
    currentGame: Optional[Dict[str, Any]] = None

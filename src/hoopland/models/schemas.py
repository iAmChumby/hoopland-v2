"""
Schema definitions for complex nested objects in the target schema.

These dataclasses represent the detailed structures required by the nba0203.txt
format, including player appearance, accessories, contracts, front office, etc.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# =============================================================================
# Player-related schemas
# =============================================================================


@dataclass
class StatsBlock:
    """Reusable stat structure for game/season/career stats."""

    GP: int = 0  # Games Played
    GS: int = 0  # Games Started
    W: int = 0  # Wins
    L: int = 0  # Losses
    MIN: float = 0.0  # Minutes
    PTS: float = 0.0  # Points
    AST: float = 0.0  # Assists
    TRB: float = 0.0  # Total Rebounds
    ORB: float = 0.0  # Offensive Rebounds
    DRB: float = 0.0  # Defensive Rebounds
    STL: float = 0.0  # Steals
    BLK: float = 0.0  # Blocks
    TOV: float = 0.0  # Turnovers
    FGM: float = 0.0  # Field Goals Made
    FGA: float = 0.0  # Field Goals Attempted
    FGP: float = 0.0  # Field Goal Percentage
    TPM: float = 0.0  # Three Pointers Made
    TPA: float = 0.0  # Three Pointers Attempted
    TPP: float = 0.0  # Three Point Percentage
    FTM: float = 0.0  # Free Throws Made
    FTA: float = 0.0  # Free Throws Attempted
    FTP: float = 0.0  # Free Throw Percentage
    PF: float = 0.0  # Personal Fouls
    PER: float = 0.0  # Player Efficiency Rating


@dataclass
class CareerStats:
    """Career statistics structure with season/playoffs/finals breakdowns."""

    season: List[Dict[str, Any]] = field(default_factory=list)
    playoffs: List[Dict[str, Any]] = field(default_factory=list)
    finals: List[Dict[str, Any]] = field(default_factory=list)
    highs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameStatus:
    """In-game status for a player."""

    startPos: int = 0  # Starting position (1-5, 0 if bench)
    stamina: float = 100.0
    gradePoints: int = 0
    healthy: bool = True
    injured: bool = False
    injuryType: int = 0
    injuryGames: int = 0


@dataclass
class Appearance:
    """Player visual appearance settings."""

    skinC: str = "C68040"  # Skin color hex
    eyeC: str = "3B2D1A"  # Eye color hex
    hair: str = "0000"  # Hair style ID
    hairC: str = "1A1A1A"  # Hair color hex
    fHair: str = "0000"  # Facial hair style ID
    fHairC: str = "1A1A1A"  # Facial hair color hex
    unibrow: bool = False
    browC: str = "1A1A1A"  # Eyebrow color hex


@dataclass
class Accessory:
    """Player accessories for a single uniform variant."""

    headAcc: int = 0  # Headband, etc.
    L_Shoulder: int = 0  # Left shoulder accessory
    R_Shoulder: int = 0  # Right shoulder accessory
    L_Elbow: int = 0  # Left elbow sleeve
    R_Elbow: int = 0  # Right elbow sleeve
    L_Wrist: int = 0  # Left wristband
    R_Wrist: int = 0  # Right wristband
    L_Knee: int = 0  # Left knee brace
    R_Knee: int = 0  # Right knee brace
    L_Shin: int = 0  # Left shin guard
    R_Shin: int = 0  # Right shin guard
    shoeC1: str = "FFFFFF"  # Shoe primary color
    shoeC2: str = "000000"  # Shoe secondary color
    shoeC3: str = "FFFFFF"  # Shoe accent color
    shoeType: int = 0


@dataclass
class Suit:
    """Off-court formal attire for player."""

    headAcc: int = 0
    jacketC: str = "1A1A1A"
    shirtC: str = "FFFFFF"
    tieC: str = "7F1A1A"
    pantC: str = "1A1A1A"
    shoeC: str = "1A1A1A"


@dataclass
class Contract:
    """Player contract details."""

    tid: int = -1  # Team ID
    pid: int = -1  # Player ID
    type: int = 0  # Contract type (0=standard, 1=min, 2=max, etc.)
    yrs: int = 1  # Years remaining
    sal: float = 1.0  # Salary in millions
    opt: int = 0  # Option type (0=none, 1=player, 2=team)
    noTrd: bool = False  # No-trade clause
    canExt: bool = True  # Can extend
    ext: int = 0  # Extension years
    bir: bool = False  # Bird rights


@dataclass
class Award:
    """Player award entry."""

    id: int = 0  # Award type ID
    league: int = 0  # League ID (0=NBA, 1=NCAA, etc.)
    yearsWon: List[int] = field(default_factory=list)
    position: int = 0  # Position for all-star selections, etc.


@dataclass
class Skill:
    """Player skill/badge entry."""

    id: int = 0  # Skill/badge ID
    xp: int = 0  # Experience points toward next level
    level: int = 0  # Current level (0=none, 1=bronze, 2=silver, 3=gold)
    equipped: bool = False


@dataclass
class PlayerHistory:
    """Historical data for a player."""

    coll: str = ""  # College name
    collegeStats: List[Dict[str, Any]] = field(default_factory=list)
    draftYear: int = 0
    draftRd: int = 0  # Draft round
    draftPk: int = 0  # Draft pick
    draftTid: int = -1  # Team that drafted
    yearsExp: int = 0  # Years of experience
    injuries: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Team-related schemas
# =============================================================================


@dataclass
class Facility:
    """Team facility configuration."""

    type: int = 0  # Facility type
    tier: int = 1  # Upgrade tier
    upgrade: int = 0  # Upgrade progress
    condition: float = 100.0


@dataclass
class StaffMember:
    """Front office or coaching staff member."""

    fn: str = ""  # First name
    ln: str = ""  # Last name
    rating: int = 50
    contract: Optional[Contract] = None


@dataclass
class FrontOffice:
    """Team front office and infrastructure."""

    coins: int = 1000000
    condition: float = 100.0
    morale: float = 75.0
    fans: int = 50000
    facilities: List[Facility] = field(default_factory=list)
    staff: List[StaffMember] = field(default_factory=list)
    announcers: List[str] = field(default_factory=list)
    adsURL: str = ""
    adSize: int = 0


@dataclass
class CourtDesign:
    """Basketball court visual design matching game format."""

    outerWood: str = "lines"
    outerWoodC: str = "EEA160"
    innerWood: str = "lines"
    innerWoodC: str = "EEA160"
    outerFT: str = "lines"
    outerFTC: str = "EEA160"
    innerFT: str = "flat"
    innerFTC: str = "PRI"
    outerKey: str = "flat"
    outerKeyC: str = "PRI"
    innerKey: str = "flat"
    innerKeyC: str = "PRI"
    outerBorder: str = "SEC"
    innerBorder: str = "SEC"
    outerFloor: str = "SEC"
    mediaLines: str = "FFFFFF"
    outerLine: str = "000000"
    halfCourtLine: str = "000000"
    threePointLine: int = 0
    threePointLineC: str = "000000"
    outerFTCircle: str = "000000"
    innerFTCircle: str = "000000"
    outerKeyLine: str = "000000"
    innerKeyLine: str = "000000"
    logoSize: int = 0
    logoLayer: int = 0
    overlayURL: str = ""
    overlayLayer: int = 1
    baseline1: str = ""
    baseline1C: str = "FFFFFF"
    baseline2: str = ""
    baseline2C: str = "FFFFFF"
    sideline1: str = ""
    sideline1C: str = "FFFFFF"
    sideline2: str = ""
    sideline2C: str = "FFFFFF"
    hoopBase: str = "000000"
    hoopPole: str = "FFFFFF"
    polePadding: str = "000000"
    hoopPadding: str = "FF0000"


@dataclass
class UniformDesign:
    """Team uniform design for a single variant (home/away/alt/etc)."""

    jerseyMain: str = "FFFFFF"  # Jersey primary color
    jerseySecondary: str = "000000"  # Jersey secondary color
    jerseyStripe: str = "000000"  # Jersey stripe color
    shortsMain: str = "FFFFFF"  # Shorts primary color
    shortsSecondary: str = "000000"  # Shorts secondary color
    shortsStripe: str = "000000"  # Shorts stripe color
    numberC: str = "000000"  # Number color
    nameC: str = "000000"  # Name color
    style: int = 0  # Uniform style ID


@dataclass
class Championships:
    """Team championship history."""

    id: int = 0  # Championship type ID
    league: int = 0  # League ID
    yearsWon: List[int] = field(default_factory=list)
    position: int = 0


@dataclass
class DraftPick:
    """Draft pick asset."""

    year: int = 0
    round: int = 1
    original_tid: int = -1  # Team that originally owned the pick
    current_tid: int = -1  # Team that currently owns the pick


# =============================================================================
# League-related schemas
# =============================================================================


@dataclass
class Person:
    """Generic person (commissioner, referee, etc.)."""

    fn: str = ""
    ln: str = ""
    age: int = 50
    ctry: int = 0
    appearance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameSettings:
    """League game settings and rules."""

    quarterLength: int = 12
    shotClock: int = 24
    overtimeLength: int = 5
    foutsToFoulOut: int = 6
    threePointLine: bool = True
    defensiveThreeSeconds: bool = True
    challengeReviews: int = 1
    timeoutsFull: int = 4
    timeouts20: int = 2


@dataclass
class SimulationSliders:
    """Simulation sliders for gameplay adjustments."""

    paceOfPlay: int = 50
    threePointAttempts: int = 50
    freeThrowAttempts: int = 50
    reboundRate: int = 50
    turnoverRate: int = 50
    foulRate: int = 50
    injuryRate: int = 50
    homeAdvantage: int = 50


@dataclass
class Difficulty:
    """Difficulty settings."""

    level: int = 2  # 0=Rookie, 1=Pro, 2=All-Star, 3=Superstar, 4=HoF
    cpu_shooting: float = 1.0
    cpu_defense: float = 1.0
    player_shooting: float = 1.0
    player_defense: float = 1.0

"""
Pytest configuration and shared fixtures for the Hoopland test suite.
"""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    from hoopland.db import Base
    
    # Create temp file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session, path, engine
    
    # Cleanup - must close session and dispose engine before unlinking on Windows
    session.close()
    engine.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass  # Windows may still lock file briefly


@pytest.fixture
def db_session(temp_db):
    """Provide a database session for tests."""
    session, path, engine = temp_db
    yield session
    # Session cleanup handled by temp_db fixture


@pytest.fixture
def mock_player():
    """Create a mock Player database object."""
    from hoopland.db import Player
    return Player(
        source_id="12345",
        league="NBA",
        season="2023-24",
        name="Test Player",
        team_id="1610612737",
        raw_stats={
            "PTS": 20.5,
            "REB": 5.2,
            "AST": 4.1,
            "GP": 82,
            "ROSTER_HEIGHT": "6-6",
            "ROSTER_WEIGHT": 220,
            "ROSTER_AGE": 25.0,
            "ROSTER_POSITION": "SG"
        },
        appearance={"skin_tone": 3, "hair": 2, "facial_hair": 0}
    )


# ============================================================================
# API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_nba_client():
    """Mock the NBAClient for unit tests."""
    with patch('hoopland.data.nba_client.NBAClient') as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Setup common mock returns
        client.get_team_by_id.return_value = {
            "id": 1610612737,
            "full_name": "Atlanta Hawks",
            "abbreviation": "ATL",
            "nickname": "Hawks",
            "city": "Atlanta"
        }
        
        yield client


@pytest.fixture
def mock_espn_client():
    """Mock the ESPNClient for unit tests."""
    with patch('hoopland.data.espn_client.ESPNClient') as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Setup common mock returns
        client.get_all_teams.return_value = [
            {"id": "1", "displayName": "Team A", "slug": "team-a"},
            {"id": "2", "displayName": "Team B", "slug": "team-b"},
        ]
        
        yield client


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_raw_stats():
    """Sample NBA raw stats for testing."""
    return {
        "PLAYER_ID": 12345,
        "PLAYER_NAME": "Test Player",
        "TEAM_ID": 1610612737,
        "GP": 82,
        "PTS": 1800,
        "REB": 400,
        "AST": 350,
        "STL": 80,
        "BLK": 40,
        "FGM": 600,
        "FGA": 1200,
        "FG_PCT": 0.5,
        "FG3M": 150,
        "FG3A": 400,
        "FG3_PCT": 0.375,
        "FTM": 300,
        "FTA": 350,
        "FT_PCT": 0.857,
        "ROSTER_HEIGHT": "6-6",
        "ROSTER_WEIGHT": 220,
        "ROSTER_AGE": 25.0,
        "ROSTER_POSITION": "SG"
    }


@pytest.fixture
def sample_ncaa_athlete():
    """Sample ESPN NCAA athlete data."""
    return {
        "id": "4567890",
        "fullName": "College Star",
        "displayHeight": "6' 8\"",
        "displayWeight": "235 lbs",
        "position": {"abbreviation": "PF"},
        "headshot": {"href": "https://example.com/headshot.png"}
    }


# ============================================================================
# Generator Fixtures
# ============================================================================

@pytest.fixture
def generator():
    """Provide a Generator instance for integration tests."""
    from hoopland.blocks.generator import Generator
    return Generator()


# ============================================================================
# Test Markers Configuration
# ============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Include slow tests (integration/e2e tests that take a long time)"
    )

def pytest_configure(config):
    """Register custom markers and handle --slow flag."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "database: marks tests that require database access")
    
    # If --slow flag is passed, remove the default '-m not slow' filter
    if config.getoption("--slow"):
        # Override the marker expression to include slow tests
        config.option.markexpr = ""


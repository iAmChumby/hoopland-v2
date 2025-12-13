"""
Unit tests for core Hoopland functionality.
Tests normalization, DB operations, and repository initialization.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hoopland.db import Base, Player
from hoopland.stats.normalization import StatsConverter, normalize_rating
from hoopland.cv.appearance import get_skin_tone
from hoopland.data.repository import DataRepository


@pytest.fixture
def session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_normalization():
    """Test min/max normalization function."""
    assert normalize_rating(10, 0, 10) == 10
    assert normalize_rating(0, 0, 10) == 1
    assert normalize_rating(5, 0, 10) == 5
    assert normalize_rating(35, 0, 35) == 10
    assert normalize_rating(17.5, 0, 35) == 5


def test_stats_converter_15_attributes():
    """Test StatsConverter returns 15 target attributes."""
    raw = {
        "FG_PCT": 0.6,
        "FG3_PCT": 0.2,
        "STL": 2,
        "BLK": 1,
        "REB": 15,
        "AST": 6,
    }
    ratings = StatsConverter.calculate_ratings(raw)

    # Should have 15 attributes
    assert len(ratings) == 15

    # Check expected keys exist
    assert "INS" in ratings
    assert "TPT" in ratings
    assert "DRE" in ratings
    assert "PAS" in ratings

    # Each should be [current, potential] array
    assert isinstance(ratings["INS"], list)
    assert len(ratings["INS"]) == 2


def test_stats_converter_legacy():
    """Test StatsConverter legacy ratings for backward compatibility."""
    raw = {
        "FG_PCT": 0.6,
        "FG3_PCT": 0.2,
        "STL": 2,
        "BLK": 1,
        "REB": 15,
        "AST": 6,
    }
    ratings = StatsConverter.calculate_legacy_ratings(raw)

    # Should have 6 old-style attributes as integers
    assert "shooting_inside" in ratings
    assert "shooting_3pt" in ratings
    assert "rebounding" in ratings
    assert "passing" in ratings
    assert isinstance(ratings["shooting_inside"], int)


def test_db_operations(session):
    """Test database CRUD operations."""
    player = Player(
        source_id="123",
        league="NBA",
        season="2023-24",
        name="LeBron James",
        team_id="LAL",
        raw_stats={},
        appearance={},
    )
    session.add(player)
    session.commit()

    fetched = session.query(Player).first()
    assert fetched.name == "LeBron James"


def test_repository_init(session):
    """Test DataRepository initialization."""
    repo = DataRepository(session)
    assert repo.nba_client is not None


def test_skin_tone_fallback():
    """Test skin tone detection falls back to default on invalid URL."""
    tone = get_skin_tone("http://invalid.url/image.png")
    assert tone == 1

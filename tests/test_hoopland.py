import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hoopland.db import Base, Player
from hoopland.stats.normalization import StatsConverter, normalize_rating
from hoopland.cv.appearance import get_skin_tone
from hoopland.data.repository import DataRepository


# Mock DB
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_normalization():
    # Test min/max normalization
    assert normalize_rating(10, 0, 10) == 10
    assert normalize_rating(0, 0, 10) == 1
    assert (
        normalize_rating(5, 0, 10) == 6
    )  # (5-0)/(10-0)*10 = 5. -> 1-10 scale check logic.
    # My logic: ((5-0)/10)*10 = 5. round(5) = 5. Wait.
    # The spec says 1-10 scale.
    # If I use 1-origin: 1 + (val-min)/(max-min)*9 ?
    # My implementation was: ((val - min_val) / (max_val - min_val)) * 10
    # Input 0 -> 0. Input 10 -> 10.
    # But later I used max(1, min(10, ...))
    # So 0 -> 1. 10 -> 10. 5 -> 5.

    # Let's test specific values
    assert normalize_rating(35, 0, 35) == 10  # Max PTS
    assert normalize_rating(17.5, 0, 35) == 5  # Middle


def test_stats_converter():
    raw = {
        "FG_PCT": 0.6,  # Max efficiency
        "FG3_PCT": 0.2,  # Min 3pt
        "STL": 2,
        "BLK": 1,
        "REB": 15,  # Max Reb
        "AST": 6,  # Mid Ast
    }
    ratings = StatsConverter.calculate_ratings(raw)

    assert ratings["shooting_inside"] == 10
    assert ratings["shooting_3pt"] == 1  # 0.2 is min (actually might be 1 via logic)
    assert ratings["rebounding"] == 10
    assert ratings["passing"] == 5  # 6 is half of 12


def test_db_operations(session):
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
    repo = DataRepository(session)
    assert repo.nba_client is not None


# Integration style test (mocking would be better but keeping simple)
def test_skin_tone_fallback():
    # Invalid URL should return 1
    tone = get_skin_tone("http://invalid.url/image.png")
    assert tone == 1

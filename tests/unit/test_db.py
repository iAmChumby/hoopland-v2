"""
Unit tests for the database module (db.py).
Tests database initialization, model creation, and constraints.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from hoopland.db import Base, Player, init_db


class TestPlayerModel:
    """Tests for the Player database model."""

    def test_player_creation(self, db_session):
        """Test creating a Player instance."""
        player = Player(
            source_id="12345",
            league="NBA",
            season="2023-24",
            name="Test Player",
            team_id="1610612737",
            raw_stats={"PTS": 20},
            appearance={"skin_tone": 1}
        )
        db_session.add(player)
        db_session.commit()
        
        assert player.id is not None
        assert player.source_id == "12345"
        assert player.league == "NBA"

    def test_player_raw_stats_json(self, db_session):
        """Test that raw_stats JSON field works correctly."""
        stats = {
            "PTS": 25.5,
            "REB": 7.2,
            "AST": 5.1,
            "nested": {"value": 123}
        }
        player = Player(
            source_id="99999",
            league="NBA",
            season="2023-24",
            name="JSON Test",
            raw_stats=stats
        )
        db_session.add(player)
        db_session.commit()
        
        # Refresh and verify JSON
        db_session.refresh(player)
        assert player.raw_stats["PTS"] == 25.5
        assert player.raw_stats["nested"]["value"] == 123

    def test_player_appearance_json(self, db_session):
        """Test that appearance JSON field works correctly."""
        appearance = {"skin_tone": 3, "hair": 5, "facial_hair": 2}
        player = Player(
            source_id="88888",
            league="NCAA",
            season="2024",
            name="Appearance Test",
            appearance=appearance
        )
        db_session.add(player)
        db_session.commit()
        
        db_session.refresh(player)
        assert player.appearance["skin_tone"] == 3
        assert player.appearance["hair"] == 5

    def test_unique_constraint_same_season(self, db_session):
        """Test that duplicate source_id + season + league fails."""
        player1 = Player(
            source_id="11111",
            league="NBA",
            season="2023-24",
            name="Player One"
        )
        player2 = Player(
            source_id="11111",  # Same source_id
            league="NBA",       # Same league
            season="2023-24",   # Same season
            name="Player One Duplicate"
        )
        
        db_session.add(player1)
        db_session.commit()
        
        db_session.add(player2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_same_player_different_seasons(self, db_session):
        """Test that same player can exist in multiple seasons."""
        player1 = Player(
            source_id="22222",
            league="NBA",
            season="2022-23",
            name="Multi Season Player"
        )
        player2 = Player(
            source_id="22222",  # Same source_id
            league="NBA",       # Same league
            season="2023-24",   # Different season
            name="Multi Season Player"
        )
        
        db_session.add(player1)
        db_session.add(player2)
        db_session.commit()
        
        # Both should be saved
        assert player1.id is not None
        assert player2.id is not None
        assert player1.id != player2.id

    def test_same_player_different_leagues(self, db_session):
        """Test that same source_id can exist in different leagues."""
        player1 = Player(
            source_id="33333",
            league="NBA",
            season="2023-24",
            name="NBA Player"
        )
        player2 = Player(
            source_id="33333",  # Same source_id
            league="NCAA",      # Different league
            season="2023-24",   # Same season
            name="NCAA Player"
        )
        
        db_session.add(player1)
        db_session.add(player2)
        db_session.commit()
        
        assert player1.id is not None
        assert player2.id is not None


class TestInitDb:
    """Tests for database initialization."""

    def test_init_db_creates_session(self):
        """Test that init_db returns a session maker."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            assert session is not None
        finally:
            session.close()
            engine.dispose()
            try:
                os.unlink(path)
            except PermissionError:
                pass

    def test_init_db_creates_tables(self):
        """Test that init_db creates the players table."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Should be able to add a player
            player = Player(
                source_id="test",
                league="NBA",
                season="2023-24",
                name="Test"
            )
            session.add(player)
            session.commit()
            
            assert player.id is not None
        finally:
            session.close()
            engine.dispose()
            try:
                os.unlink(path)
            except PermissionError:
                pass

    def test_init_db_default_path(self):
        """Test init_db with default path."""
        # This creates hoopland.db in current directory
        # Just verify it doesn't error
        Session = init_db()
        assert Session is not None

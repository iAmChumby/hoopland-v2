"""
Integration tests for the data repository.
Tests real database operations and data flow.
"""

import pytest
import os
import tempfile

from hoopland.db import init_db, Player
from hoopland.data.repository import DataRepository


class TestRepositoryDatabaseIntegration:
    """Integration tests for repository database operations."""

    @pytest.fixture
    def repo_with_db(self):
        """Create a repository with a temp database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from hoopland.db import Base
        
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = DataRepository(session)
        
        yield repo
        
        session.close()
        engine.dispose()
        try:
            os.unlink(path)
        except PermissionError:
            pass

    def test_sync_and_retrieve_player(self, repo_with_db):
        """Test syncing and retrieving a player."""
        repo = repo_with_db
        
        # Manually add a player (simulating sync)
        player = Player(
            source_id="999",
            league="NBA",
            season="2023-24",
            name="Integration Test Player",
            team_id="100",
            raw_stats={"PTS": 20}
        )
        repo.session.add(player)
        repo.session.commit()
        
        # Retrieve using get_player
        result = repo.get_player("999", league="NBA", season="2023-24")
        assert result is not None
        assert result.name == "Integration Test Player"

    def test_player_raw_stats_persistence(self, repo_with_db):
        """Test that raw_stats JSON persists correctly."""
        repo = repo_with_db
        
        complex_stats = {
            "PTS": 25.5,
            "nested": {"inner": [1, 2, 3]},
            "list": [{"a": 1}, {"b": 2}]
        }
        
        player = Player(
            source_id="888",
            league="NBA",
            season="2023-24",
            name="JSON Test",
            raw_stats=complex_stats
        )
        repo.session.add(player)
        repo.session.commit()
        
        # Refresh and verify
        repo.session.refresh(player)
        assert player.raw_stats["nested"]["inner"] == [1, 2, 3]
        assert len(player.raw_stats["list"]) == 2

    def test_appearance_update_persistence(self, repo_with_db):
        """Test that appearance updates persist correctly."""
        repo = repo_with_db
        
        # Add player without appearance
        player = Player(
            source_id="777",
            league="NBA",
            season="2023-24",
            name="Appearance Test",
            appearance={}
        )
        repo.session.add(player)
        repo.session.commit()
        
        # Update appearance
        player.appearance = {"skin_tone": 5, "hair": 3, "facial_hair": 1}
        repo.session.commit()
        
        # Verify persistence
        repo.session.refresh(player)
        assert player.appearance["skin_tone"] == 5
        assert player.appearance["hair"] == 3


class TestMultiSeasonDataFlow:
    """Integration tests for multi-season data handling."""

    @pytest.fixture
    def repo_with_db(self):
        """Create a repository with a temp database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from hoopland.db import Base
        
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = DataRepository(session)
        
        yield repo
        
        session.close()
        engine.dispose()
        try:
            os.unlink(path)
        except PermissionError:
            pass

    def test_same_player_multiple_seasons(self, repo_with_db):
        """Test storing same player across multiple seasons."""
        repo = repo_with_db
        
        # Season 1
        player_s1 = Player(
            source_id="123",
            league="NBA",
            season="2022-23",
            name="Multi Season Player",
            raw_stats={"PTS": 20}
        )
        
        # Season 2
        player_s2 = Player(
            source_id="123",
            league="NBA",
            season="2023-24",
            name="Multi Season Player",
            raw_stats={"PTS": 25}  # Improved!
        )
        
        repo.session.add(player_s1)
        repo.session.add(player_s2)
        repo.session.commit()
        
        # Verify both exist
        s1 = repo.get_player("123", league="NBA", season="2022-23")
        s2 = repo.get_player("123", league="NBA", season="2023-24")
        
        assert s1 is not None
        assert s2 is not None
        assert s1.raw_stats["PTS"] == 20
        assert s2.raw_stats["PTS"] == 25

    def test_nba_and_ncaa_same_id(self, repo_with_db):
        """Test that same source_id can exist in different leagues."""
        repo = repo_with_db
        
        nba_player = Player(
            source_id="5000",
            league="NBA",
            season="2023-24",
            name="Pro Player"
        )
        
        ncaa_player = Player(
            source_id="5000",
            league="NCAA",
            season="2023-24",
            name="College Player"
        )
        
        repo.session.add(nba_player)
        repo.session.add(ncaa_player)
        repo.session.commit()
        
        # Both should exist
        nba = repo.get_player("5000", league="NBA", season="2023-24")
        ncaa = repo.get_player("5000", league="NCAA", season="2023-24")
        
        assert nba is not None
        assert ncaa is not None
        assert nba.name == "Pro Player"
        assert ncaa.name == "College Player"

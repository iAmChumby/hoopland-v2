"""
Unit tests for the data repository module.
Tests data syncing and appearance backfilling with mocked API clients.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd

from hoopland.data.repository import DataRepository
from hoopland.db import Player


class TestDataRepositoryInit:
    """Tests for DataRepository initialization."""

    def test_repository_init(self, db_session):
        """Test repository initialization."""
        repo = DataRepository(db_session)
        assert repo.session == db_session
        assert repo.nba_client is not None
        assert repo.espn_client is not None


class TestGetPlayer:
    """Tests for the get_player method."""

    def test_get_player_exists(self, db_session):
        """Test getting an existing player."""
        # Add a player
        player = Player(
            source_id="12345",
            league="NBA",
            season="2023-24",
            name="Test Player"
        )
        db_session.add(player)
        db_session.commit()
        
        repo = DataRepository(db_session)
        result = repo.get_player("12345", league="NBA", season="2023-24")
        
        assert result is not None
        assert result.name == "Test Player"

    def test_get_player_not_exists(self, db_session):
        """Test getting a non-existent player."""
        repo = DataRepository(db_session)
        result = repo.get_player("99999", league="NBA", season="2023-24")
        
        assert result is None

    def test_get_player_wrong_season(self, db_session):
        """Test getting player with wrong season."""
        player = Player(
            source_id="12345",
            league="NBA",
            season="2022-23",
            name="Test Player"
        )
        db_session.add(player)
        db_session.commit()
        
        repo = DataRepository(db_session)
        result = repo.get_player("12345", league="NBA", season="2023-24")
        
        assert result is None


class TestSyncNBASeasonStats:
    """Tests for NBA season stats syncing with mocks."""

    @patch('hoopland.data.repository.NBAClient')
    def test_sync_nba_season_stats_skips_if_cached(self, mock_client_class, db_session):
        """Test that sync skips if data already cached."""
        # Add 450 players to simulate cached data
        for i in range(450):
            player = Player(
                source_id=str(i),
                league="NBA",
                season="2023-24",
                name=f"Player {i}"
            )
            db_session.add(player)
        db_session.commit()
        
        repo = DataRepository(db_session)
        repo.sync_nba_season_stats("2023-24")
        
        # API should not be called since data exists
        repo.nba_client.get_league_stats.assert_not_called()

    @patch('hoopland.data.repository.NBAClient')
    def test_sync_nba_season_stats_fetches_new(self, mock_client_class, db_session):
        """Test that sync fetches if data not cached."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Return mock data
        mock_df = pd.DataFrame([
            {"PLAYER_ID": 1, "PLAYER_NAME": "Player 1", "TEAM_ID": 100, "PTS": 20},
            {"PLAYER_ID": 2, "PLAYER_NAME": "Player 2", "TEAM_ID": 100, "PTS": 15},
        ])
        mock_client.get_league_stats.return_value = mock_df
        
        repo = DataRepository(db_session)
        repo.nba_client = mock_client
        repo.sync_nba_season_stats("2023-24")
        
        mock_client.get_league_stats.assert_called_once_with(season="2023-24")


class TestSyncNCAASeasonStats:
    """Tests for NCAA season stats syncing with mocks."""

    @patch('hoopland.data.repository.ESPNClient')
    def test_sync_ncaa_tournament_mode(self, mock_espn_class, db_session):
        """Test NCAA sync in tournament mode limits to 64 teams."""
        mock_client = MagicMock()
        mock_espn_class.return_value = mock_client
        
        # Create 100 mock teams
        mock_teams = [{"id": str(i), "displayName": f"Team {i}", "slug": f"team-{i}"} for i in range(100)]
        mock_client.get_all_teams.return_value = mock_teams
        mock_client.get_team_roster.return_value = {"athletes": []}
        
        repo = DataRepository(db_session)
        repo.espn_client = mock_client
        team_ids = repo.sync_ncaa_season_stats("2024", tournament_only=True)
        
        # Should only return 64 team IDs
        assert len(team_ids) == 64

    @patch('hoopland.data.repository.ESPNClient')
    def test_sync_ncaa_full_mode(self, mock_espn_class, db_session):
        """Test NCAA sync in full mode gets all teams."""
        mock_client = MagicMock()
        mock_espn_class.return_value = mock_client
        
        mock_teams = [{"id": str(i), "displayName": f"Team {i}", "slug": f"team-{i}"} for i in range(100)]
        mock_client.get_all_teams.return_value = mock_teams
        mock_client.get_team_roster.return_value = {"athletes": []}
        
        repo = DataRepository(db_session)
        repo.espn_client = mock_client
        team_ids = repo.sync_ncaa_season_stats("2024", tournament_only=False)
        
        assert len(team_ids) == 100


class TestSyncNBARosterData:
    """Tests for NBA roster data syncing."""

    @patch('hoopland.data.repository.NBAClient')
    def test_sync_roster_data_adds_metadata(self, mock_client_class, db_session):
        """Test that roster sync adds height/weight metadata."""
        # Add a player without roster data
        player = Player(
            source_id="12345",
            league="NBA",
            season="2023-24",
            name="Test Player",
            team_id="100",
            raw_stats={"PTS": 20}
        )
        db_session.add(player)
        db_session.commit()
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock roster response
        mock_roster = pd.DataFrame([{
            "PLAYER_ID": 12345,
            "HEIGHT": "6-6",
            "WEIGHT": 220,
            "AGE": 25.0,
            "POSITION": "SG"
        }])
        mock_client.get_roster.return_value = mock_roster
        
        repo = DataRepository(db_session)
        repo.nba_client = mock_client
        repo.sync_nba_roster_data("2023-24")
        
        # Verify player was updated
        db_session.refresh(player)
        assert player.raw_stats.get("ROSTER_HEIGHT") == "6-6"
        assert player.raw_stats.get("ROSTER_WEIGHT") == 220


class TestBackfillAppearance:
    """Tests for appearance backfilling."""

    def test_backfill_skips_players_with_appearance(self, db_session):
        """Test that backfill skips players who already have appearance."""
        player = Player(
            source_id="12345",
            league="NBA",
            season="2023-24",
            name="Complete Player",
            appearance={"skin_tone": 3, "hair": 2}
        )
        db_session.add(player)
        db_session.commit()
        
        repo = DataRepository(db_session)
        mock_cv_func = MagicMock()
        
        repo.backfill_appearance(mock_cv_func, season="2023-24", league="NBA")
        
        # CV function should not be called since appearance exists
        mock_cv_func.assert_not_called()

    def test_backfill_filters_by_season(self, db_session):
        """Test that backfill only processes players from specified season."""
        player1 = Player(
            source_id="1",
            league="NBA",
            season="2022-23",
            name="Old Player",
            appearance={}
        )
        player2 = Player(
            source_id="2",
            league="NBA",
            season="2023-24",
            name="New Player",
            appearance={}
        )
        db_session.add_all([player1, player2])
        db_session.commit()
        
        repo = DataRepository(db_session)
        mock_cv_func = MagicMock(return_value={"skin_tone": 1})
        
        # Only backfill 2023-24
        repo.backfill_appearance(mock_cv_func, season="2023-24", league="NBA")
        
        # Should only process 2023-24 player (but may skip if no headshot URL)
        db_session.refresh(player1)
        assert player1.appearance == {}  # Old player not touched

    def test_backfill_filters_by_team_ids(self, db_session):
        """Test that backfill filters by team IDs when provided."""
        player1 = Player(
            source_id="1",
            league="NCAA",
            season="2024",
            name="Team A Player",
            team_id="100",
            appearance={}
        )
        player2 = Player(
            source_id="2",
            league="NCAA",
            season="2024",
            name="Team B Player",
            team_id="200",
            appearance={}
        )
        db_session.add_all([player1, player2])
        db_session.commit()
        
        repo = DataRepository(db_session)
        mock_cv_func = MagicMock(return_value={"skin_tone": 1})
        
        # Only backfill team 100
        repo.backfill_appearance(
            mock_cv_func, 
            season="2024", 
            league="NCAA", 
            team_ids=["100"]
        )
        
        db_session.refresh(player2)
        assert player2.appearance == {}  # Team 200 player not touched

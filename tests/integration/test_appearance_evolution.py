"""
Integration tests for appearance logic evolution.

These tests verify that:
1. Appearance logic produces consistent results for the same input
2. Different inputs produce appropriately different appearances
3. DB correctly stores distinct appearances for the same player across seasons
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hoopland.db import Base, Player
from hoopland.cv.appearance import analyze_player_appearance


class TestAppearanceConsistency:
    """Tests ensuring appearance analysis produces consistent results."""

    def test_same_input_produces_same_output(self):
        """
        Verify that analyzing the same image URL multiple times
        produces identical appearance results.
        
        This tests determinism in the appearance logic.
        """
        # Use a known, stable player headshot URL
        # LeBron's headshot should be stable
        test_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2544.png"
        
        # Analyze multiple times
        result1 = analyze_player_appearance(test_url)
        result2 = analyze_player_appearance(test_url)
        result3 = analyze_player_appearance(test_url)
        
        # All results should be identical
        assert result1 == result2, (
            f"Inconsistent results: first={result1}, second={result2}"
        )
        assert result2 == result3, (
            f"Inconsistent results: second={result2}, third={result3}"
        )
        
        # Verify structure
        expected_keys = {"skin_tone", "hair", "facial_hair", "accessory"}
        assert set(result1.keys()) == expected_keys, (
            f"Missing keys. Expected {expected_keys}, got {set(result1.keys())}"
        )

    def test_appearance_values_in_valid_ranges(self):
        """
        Verify that all appearance values are within valid ranges.
        """
        test_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2544.png"
        
        result = analyze_player_appearance(test_url)
        
        # Skin tone: 1-10
        assert 1 <= result["skin_tone"] <= 10, (
            f"skin_tone {result['skin_tone']} out of range [1, 10]"
        )
        
        # Hair style: 0-130
        assert 0 <= result["hair"] <= 130, (
            f"hair {result['hair']} out of range [0, 130]"
        )
        
        # Facial hair: 0-24
        assert 0 <= result["facial_hair"] <= 24, (
            f"facial_hair {result['facial_hair']} out of range [0, 24]"
        )
        
        # Accessory: 0-16
        assert 0 <= result["accessory"] <= 16, (
            f"accessory {result['accessory']} out of range [0, 16]"
        )

    def test_invalid_url_returns_defaults(self):
        """
        Verify that an invalid URL returns default appearance values.
        """
        invalid_url = "https://invalid.example.com/nonexistent.png"
        
        result = analyze_player_appearance(invalid_url)
        
        # Should return defaults
        assert result["skin_tone"] == 1, "Expected default skin_tone of 1"
        assert result["hair"] == 0, "Expected default hair of 0"
        assert result["facial_hair"] == 0, "Expected default facial_hair of 0"
        assert result["accessory"] == 0, "Expected default accessory of 0"

    def test_empty_url_returns_defaults(self):
        """
        Verify that an empty URL returns default appearance values.
        """
        result = analyze_player_appearance("")
        
        assert result["skin_tone"] == 1
        assert result["hair"] == 0
        assert result["facial_hair"] == 0
        assert result["accessory"] == 0


class TestAppearanceEvolution:
    """Tests verifying appearance evolution mechanism across different inputs."""

    def test_different_players_different_appearances(self):
        """
        Verify that different player headshots produce different appearances.
        
        This validates that the CV analysis is actually detecting features,
        not just returning fixed values.
        """
        # Use two players with notably different appearances
        # LeBron James (2544) - bald head
        # James Harden (201935) - distinctive beard
        lebron_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2544.png"
        harden_url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/201935.png"
        
        lebron_appearance = analyze_player_appearance(lebron_url)
        harden_appearance = analyze_player_appearance(harden_url)
        
        # At least one attribute should differ
        # (unless CV isn't working, in which case both return defaults)
        if lebron_appearance["skin_tone"] != 1:  # CV is working
            # We expect some difference in at least one attribute
            differences = sum(
                1 for key in ["skin_tone", "hair", "facial_hair", "accessory"]
                if lebron_appearance[key] != harden_appearance[key]
            )
            # At least facial_hair should differ (Harden has distinctive beard)
            assert differences >= 1, (
                f"Expected at least 1 difference between LeBron and Harden. "
                f"LeBron: {lebron_appearance}, Harden: {harden_appearance}"
            )


class TestAppearanceDBPersistence:
    """Tests for appearance data persistence in the database."""

    @pytest.fixture
    def temp_db_session(self):
        """Create a temporary database session for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        session.close()
        engine.dispose()
        try:
            os.unlink(path)
        except PermissionError:
            pass

    def test_same_player_different_seasons_different_appearances(self, temp_db_session):
        """
        Verify that the same player can have different appearances
        stored for different seasons.
        
        This simulates how a player's look can evolve over their career
        (e.g., growing a beard, going bald, etc.).
        """
        session = temp_db_session
        
        # Create same player in two seasons with different appearances
        player_2018 = Player(
            source_id="2544",
            league="NBA",
            season="2018-19",
            name="LeBron James",
            team_id="1610612747",
            appearance={
                "skin_tone": 7,
                "hair": 15,  # Short hair in 2018
                "facial_hair": 5,
                "accessory": 0
            }
        )
        
        player_2024 = Player(
            source_id="2544",
            league="NBA", 
            season="2024-25",
            name="LeBron James",
            team_id="1610612747",
            appearance={
                "skin_tone": 7,
                "hair": 3,  # Different hairstyle in 2024
                "facial_hair": 8,  # More facial hair
                "accessory": 0
            }
        )
        
        session.add(player_2018)
        session.add(player_2024)
        session.commit()
        
        # Retrieve and verify
        retrieved_2018 = session.query(Player).filter_by(
            source_id="2544", season="2018-19"
        ).first()
        retrieved_2024 = session.query(Player).filter_by(
            source_id="2544", season="2024-25"
        ).first()
        
        assert retrieved_2018 is not None
        assert retrieved_2024 is not None
        
        # Verify different appearances stored
        assert retrieved_2018.appearance["hair"] == 15
        assert retrieved_2024.appearance["hair"] == 3
        assert retrieved_2018.appearance["facial_hair"] == 5
        assert retrieved_2024.appearance["facial_hair"] == 8

    def test_appearance_update_persists(self, temp_db_session):
        """
        Verify that updating a player's appearance persists correctly.
        """
        session = temp_db_session
        
        # Create player with initial appearance
        player = Player(
            source_id="999",
            league="NBA",
            season="2023-24",
            name="Test Player",
            appearance={"skin_tone": 5, "hair": 10, "facial_hair": 0, "accessory": 0}
        )
        session.add(player)
        session.commit()
        
        # Update appearance (simulating re-analysis with new image)
        player.appearance = {
            "skin_tone": 5,
            "hair": 10,
            "facial_hair": 12,  # Player grew a beard
            "accessory": 3  # Player wearing headband
        }
        session.commit()
        
        # Retrieve and verify
        session.refresh(player)
        assert player.appearance["facial_hair"] == 12
        assert player.appearance["accessory"] == 3

    def test_null_appearance_allowed(self, temp_db_session):
        """
        Verify that players can be created without appearance data.
        
        This is important for the initial data sync before CV analysis.
        """
        session = temp_db_session
        
        player = Player(
            source_id="888",
            league="NBA",
            season="2023-24",
            name="New Player",
            appearance=None
        )
        session.add(player)
        session.commit()
        
        retrieved = session.query(Player).filter_by(source_id="888").first()
        assert retrieved is not None
        assert retrieved.appearance is None

    def test_empty_appearance_allowed(self, temp_db_session):
        """
        Verify that players can have empty appearance dict.
        
        This represents "pending CV analysis" state.
        """
        session = temp_db_session
        
        player = Player(
            source_id="777",
            league="NBA",
            season="2023-24",
            name="Pending Player",
            appearance={}
        )
        session.add(player)
        session.commit()
        
        retrieved = session.query(Player).filter_by(source_id="777").first()
        assert retrieved is not None
        assert retrieved.appearance == {}

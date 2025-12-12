"""
Integration tests for Hoopland CLI generation tools.
These tests verify end-to-end functionality of all generation modes.
"""

import os
import json
import pytest
from hoopland.blocks.generator import Generator


class TestNBALeagueGeneration:
    """Tests for NBA League generation."""

    @pytest.fixture
    def generator(self):
        return Generator()

    def test_generate_league_returns_valid_structure(self, generator):
        """Test that NBA league generation returns a valid League object."""
        year = "2016"  # Use a historical year with known data
        league = generator.generate_league(year)

        assert league is not None, "League generation returned None"
        assert hasattr(league, "leagueName"), "League missing leagueName"
        assert hasattr(league, "teams"), "League missing teams"
        assert league.leagueName == f"NBA {year}"

    def test_generate_league_has_teams(self, generator):
        """Test that generated league contains NBA teams."""
        year = "2016"
        league = generator.generate_league(year)

        assert len(league.teams) > 0, "League has no teams"
        # NBA should have 30 teams
        assert len(league.teams) == 30, f"Expected 30 teams, got {len(league.teams)}"

    def test_generate_league_players_have_metadata(self, generator):
        """Test that players have proper height/weight metadata (not defaults)."""
        year = "2016"
        league = generator.generate_league(year)

        # Sample players from first team
        first_team = league.teams[0]
        assert len(first_team.roster) > 0, "Team has no players"

        # Check that at least some players don't have default values
        non_default_heights = 0
        non_default_weights = 0

        for player in first_team.roster:
            if player.ht != 72:  # 72 is the default
                non_default_heights += 1
            if player.wt != 200:  # 200 is the default
                non_default_weights += 1

        # At least half should have real data
        min_required = len(first_team.roster) // 2
        assert non_default_heights >= min_required, (
            f"Too many players with default height: {non_default_heights}/{len(first_team.roster)}"
        )
        assert non_default_weights >= min_required, (
            f"Too many players with default weight: {non_default_weights}/{len(first_team.roster)}"
        )

    def test_generate_league_saves_to_file(self, generator):
        """Test that league can be saved to JSON file."""
        year = "2016"
        league = generator.generate_league(year)
        filename = f"NBA_{year}_League.txt"

        generator.to_json(league, filename)

        expected_path = os.path.join("output", year, filename)
        assert os.path.exists(expected_path), f"File not created at {expected_path}"

        with open(expected_path, "r") as f:
            content = json.load(f)
            assert "teams" in content, "JSON missing teams key"
            assert len(content["teams"]) > 0, "JSON has no teams"


class TestNCAALeagueGeneration:
    """Tests for NCAA League generation."""

    @pytest.fixture
    def generator(self):
        return Generator()

    def test_generate_ncaa_tournament_mode(self, generator):
        """Test NCAA generation in tournament mode (64 teams)."""
        year = "2024"
        league = generator.generate_ncaa_league(year, tournament_mode=True)

        assert league is not None, "NCAA league generation returned None"
        assert len(league.teams) == 64, f"Expected 64 teams, got {len(league.teams)}"

    def test_generate_ncaa_tournament_has_players(self, generator):
        """Test that NCAA tournament teams have players."""
        year = "2024"
        league = generator.generate_ncaa_league(year, tournament_mode=True)

        total_players = sum(len(team.roster) for team in league.teams)
        assert total_players > 500, f"Expected >500 players, got {total_players}"

    def test_generate_ncaa_players_have_positions(self, generator):
        """Test that NCAA players have position data."""
        year = "2024"
        league = generator.generate_ncaa_league(year, tournament_mode=True)

        first_team = league.teams[0]
        positions_found = set()

        for player in first_team.roster:
            positions_found.add(player.pos)

        # Should have variety of positions (1-5)
        assert len(positions_found) > 1, "All players have same position"

    def test_generate_ncaa_saves_to_file(self, generator):
        """Test that NCAA league can be saved to JSON file."""
        year = "2024"
        league = generator.generate_ncaa_league(year, tournament_mode=True)
        filename = f"NCAA_{year}_Tournament_League.txt"

        generator.to_json(league, filename)

        expected_path = os.path.join("output", year, filename)
        assert os.path.exists(expected_path), f"File not created at {expected_path}"


class TestDraftClassGeneration:
    """Tests for Draft Class generation."""

    @pytest.fixture
    def generator(self):
        return Generator()

    def test_generate_draft_class_returns_players(self, generator):
        """Test that draft class generation returns players."""
        year = "2003"
        league = generator.generate_draft_class(year)

        assert league is not None, "Draft class generation returned None"
        assert len(league.teams) == 1, "Draft class should have exactly 1 team container"

        draft_team = league.teams[0]
        assert len(draft_team.roster) > 0, "Draft class has no players"

    def test_generate_draft_class_has_expected_count(self, generator):
        """Test that draft class has expected number of picks."""
        year = "2003"
        league = generator.generate_draft_class(year)

        draft_team = league.teams[0]
        # 2003 draft had 58 picks
        assert len(draft_team.roster) >= 50, f"Expected ~58 players, got {len(draft_team.roster)}"

    def test_generate_draft_class_players_have_potential(self, generator):
        """Test that draft players have calculated potential ratings."""
        year = "2003"
        league = generator.generate_draft_class(year)

        draft_team = league.teams[0]

        # Check that potentials vary (not all defaults)
        potentials = set(player.pot for player in draft_team.roster)
        assert len(potentials) > 1, "All draft players have same potential"

    def test_generate_draft_class_saves_to_file(self, generator):
        """Test that draft class can be saved to JSON file."""
        year = "2003"
        league = generator.generate_draft_class(year)
        filename = f"NBA_{year}_Draft_Class.txt"

        generator.to_json(league, filename)

        expected_path = os.path.join("output", year, filename)
        assert os.path.exists(expected_path), f"File not created at {expected_path}"


class TestLoggingSystem:
    """Tests for the logging system."""

    def test_logging_creates_directory_structure(self):
        """Test that logging creates proper directory structure."""
        from hoopland.logger import setup_logger

        setup_logger(mode="TEST", year="2024")

        log_dir = os.path.join("logs", "TEST")
        assert os.path.exists(log_dir), f"Log directory not created: {log_dir}"

    def test_logging_creates_timestamped_file(self):
        """Test that logging creates timestamped log files."""
        from hoopland.logger import setup_logger
        import glob

        setup_logger(mode="TEST", year="2024")

        log_files = glob.glob(os.path.join("logs", "TEST", "TEST_2024_*.log"))
        assert len(log_files) > 0, "No timestamped log file created"


class TestPlayerDataIntegrity:
    """Tests for player data integrity across all generation modes."""

    @pytest.fixture
    def generator(self):
        return Generator()

    def test_player_names_are_valid(self, generator):
        """Test that player names are properly formatted."""
        year = "2016"
        league = generator.generate_league(year)

        for team in league.teams:
            for player in team.roster:
                assert player.fn, f"Player missing first name: {player}"
                # Last name can be empty for single-name players
                assert isinstance(player.fn, str), "First name is not a string"

    def test_player_ids_are_unique(self, generator):
        """Test that player IDs are unique within a league."""
        year = "2016"
        league = generator.generate_league(year)

        all_ids = []
        for team in league.teams:
            for player in team.roster:
                all_ids.append(player.id)

        assert len(all_ids) == len(set(all_ids)), "Duplicate player IDs found"

    def test_player_positions_are_valid(self, generator):
        """Test that player positions are in valid range (1-5)."""
        year = "2016"
        league = generator.generate_league(year)

        for team in league.teams:
            for player in team.roster:
                assert 1 <= player.pos <= 5, f"Invalid position {player.pos} for {player.fn} {player.ln}"

    def test_player_heights_are_reasonable(self, generator):
        """Test that player heights are within reasonable NBA range."""
        year = "2016"
        league = generator.generate_league(year)

        for team in league.teams:
            for player in team.roster:
                # NBA players: 5'3" (63in) to 7'7" (91in) historically
                if player.ht != 72:  # Skip defaults
                    assert 63 <= player.ht <= 96, (
                        f"Unreasonable height {player.ht} for {player.fn} {player.ln}"
                    )

    def test_player_weights_are_reasonable(self, generator):
        """Test that player weights are within reasonable NBA range."""
        year = "2016"
        league = generator.generate_league(year)

        for team in league.teams:
            for player in team.roster:
                # NBA players: ~140lbs to ~350lbs
                if player.wt != 200:  # Skip defaults
                    assert 130 <= player.wt <= 360, (
                        f"Unreasonable weight {player.wt} for {player.fn} {player.ln}"
                    )

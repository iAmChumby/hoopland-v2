"""
End-to-end tests for the Hoopland CLI.
Tests complete user workflows from command line to output files.
"""

import pytest
import subprocess
import os
import json
import glob


class TestCLINBAGeneration:
    """E2E tests for NBA league generation via CLI."""

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_nba_generation_historical(self):
        """Test full NBA generation for a historical year."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "nba", "--year", "2016"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0
        
        # Verify output file exists
        output_file = os.path.join("output", "2016", "NBA_2016_League.txt")
        assert os.path.exists(output_file)
        
        # Verify file content
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert "teams" in data
            assert len(data["teams"]) == 30

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_nba_creates_log_file(self):
        """Test that NBA generation creates appropriate log file."""
        subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "nba", "--year", "2016"],
            capture_output=True,
            timeout=300
        )
        
        # Verify log file created
        log_files = glob.glob(os.path.join("logs", "NBA", "NBA_2016_*.log"))
        assert len(log_files) > 0


class TestCLINCAAGeneration:
    """E2E tests for NCAA league generation via CLI."""

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_ncaa_tournament_mode(self):
        """Test NCAA tournament mode (64 teams)."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "ncaa", "--year", "2024", "--tournament"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0
        
        # Verify output file exists
        output_file = os.path.join("output", "2024", "NCAA_2024_Tournament_League.txt")
        assert os.path.exists(output_file)
        
        # Verify team count
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data["teams"]) == 64

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_ncaa_creates_log_file(self):
        """Test that NCAA generation creates appropriate log file."""
        subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "ncaa", "--year", "2024", "--tournament"],
            capture_output=True,
            timeout=300
        )
        
        # Verify log file created
        log_files = glob.glob(os.path.join("logs", "NCAA", "NCAA_2024_*.log"))
        assert len(log_files) > 0


class TestCLIDraftGeneration:
    """E2E tests for draft class generation via CLI."""

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_draft_generation(self):
        """Test draft class generation."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "draft", "--year", "2003"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0
        
        # Verify output file exists
        output_file = os.path.join("output", "2003", "NBA_2003_Draft_Class.txt")
        assert os.path.exists(output_file)
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert "teams" in data
            # Draft class has 1 "team" container
            assert len(data["teams"]) == 1
            # Should have players
            assert len(data["teams"][0]["roster"]) > 50

    @pytest.mark.slow
    @pytest.mark.network
    def test_cli_draft_creates_log_file(self):
        """Test that draft generation creates appropriate log file."""
        subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "draft", "--year", "2003"],
            capture_output=True,
            timeout=300
        )
        
        # Verify log file created
        log_files = glob.glob(os.path.join("logs", "DRAFT", "DRAFT_2003_*.log"))
        assert len(log_files) > 0


class TestCLIErrorHandling:
    """E2E tests for CLI error handling."""

    def test_cli_missing_year_argument(self):
        """Test that CLI fails gracefully without year argument."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "nba"],
            capture_output=True,
            text=True
        )
        
        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Should have error message about missing argument
        assert "year" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_cli_invalid_league_type(self):
        """Test that CLI rejects invalid league type."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "invalid", "--year", "2024"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0

    def test_cli_debug_mode(self):
        """Test that debug mode enables verbose logging."""
        result = subprocess.run(
            ["python", "-m", "src.hoopland.cli", "--league", "nba", "--year", "2016", "--debug"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Should succeed
        assert result.returncode == 0


class TestOutputFileIntegrity:
    """E2E tests for output file integrity."""

    @pytest.mark.slow
    def test_output_file_is_valid_json(self):
        """Test that all output files are valid JSON."""
        output_files = glob.glob(os.path.join("output", "*", "*.txt"))
        
        for filepath in output_files:
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in {filepath}")

    @pytest.mark.slow
    def test_output_files_have_required_fields(self):
        """Test that output files have required structure."""
        output_files = glob.glob(os.path.join("output", "*", "*_League.txt"))
        
        for filepath in output_files:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Required fields
                assert "leagueName" in data
                assert "teams" in data
                assert "meta" in data
                
                # Meta should have dataType
                assert "dataType" in data["meta"]

    @pytest.mark.slow
    def test_player_data_integrity_in_output(self):
        """Test that players in output have valid data."""
        output_file = os.path.join("output", "2016", "NBA_2016_League.txt")
        
        if not os.path.exists(output_file):
            pytest.skip("Output file not found")
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            
            for team in data["teams"]:
                for player in team["roster"]:
                    # Required fields
                    assert "id" in player
                    assert "fn" in player
                    assert "ln" in player
                    
                    # Position should be valid
                    assert 1 <= player.get("pos", 0) <= 5 or player.get("pos", 0) == 0

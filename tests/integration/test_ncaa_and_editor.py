import pytest
import os
import json
from unittest.mock import MagicMock, patch
from hoopland.blocks.generator import Generator
from hoopland.tui.screens.editor import EditorScreen
from pathlib import Path

# --- NCAA Generation Tests ---

@pytest.fixture
def mock_espn_client():
    with patch("hoopland.blocks.generator.repository.ESPNClient") as MockClient:
        client = MockClient.return_value
        # Mock get_all_teams return
        client.get_all_teams.return_value = [
            {"id": "1", "displayName": "Duke Blue Devils", "abbreviation": "DUKE"},
            {"id": "2", "displayName": "North Carolina Tar Heels", "abbreviation": "UNC"}
        ]
        yield client

def test_ncaa_generation_naming(mock_espn_client, tmp_path):
    # Setup generator with mocked repository
    gen = Generator()
    gen.repo.espn_client = mock_espn_client
    
    # Mock syncing to avoid actual API calls during generation logic
    gen.repo.sync_ncaa_season_stats = MagicMock(return_value=["1", "2"])
    gen.repo.backfill_appearance = MagicMock()
    
    # Mock session query to return dummy players
    # We need to mock the session.query().filter_by().all() chain
    mock_player1 = MagicMock()
    mock_player1.id = 101
    mock_player1.team_id = "1" # Duke
    mock_player1.name = "Player One"
    mock_player1.appearance = {}
    mock_player1.raw_stats = {}
    
    mock_player2 = MagicMock()
    mock_player2.id = 102
    mock_player2.team_id = "2" # UNC
    mock_player2.name = "Player Two"
    mock_player2.appearance = {}
    mock_player2.raw_stats = {}
    
    # This is a bit complex to mock completely given SqlAlchemy, 
    # so we might rely on the method using the mocked espn_client 
    # if we can inject data. 
    # Alternatively, we can verify the private naming logic if we extract it, 
    # but let's try to mock the DB return.
    
    with patch.object(gen.session, "query") as mock_query:
        mock_filter = mock_query.return_value.filter_by.return_value
        # Handle the query for Players
        # returning a list of players
        mock_filter.all.return_value = [mock_player1, mock_player2]

        # Run generation
        # We assume tournament_mode calls sync_ncaa_season_stats which we mocked
        league = gen.generate_ncaa_league("2024", tournament_mode=False)

        # Verify Teams
        duke = next((t for t in league.teams if t.id == 1), None)
        unc = next((t for t in league.teams if t.id == 2), None)
        
        assert duke is not None
        assert duke.name == "Duke Blue Devils"
        assert duke.shortName == "DUKE"
        
        assert unc is not None
        assert unc.name == "North Carolina Tar Heels"
        assert unc.shortName == "UNC"

# --- Editor Tests ---

@pytest.fixture
def sample_league_file(tmp_path):
    data = {
        "teams": [
            {
                "name": "Lakers",
                "city": "Los Angeles",
                "roster": [
                    {"id": 1, "fn": "LeBron", "ln": "James", "pos": 3}
                ]
            }
        ]
    }
    p = tmp_path / "test_league.txt"
    with open(p, "w") as f:
        json.dump(data, f)
    return str(p)

def test_editor_save(sample_league_file):
    # Initialize editor with file
    screen = EditorScreen(file_path=sample_league_file)
    
    # Mock the internal _app attribute
    mock_app = MagicMock()
    screen._app = mock_app
    
    # Mock query_one to return mock widgets
    mock_option_list = MagicMock()
    mock_data_table = MagicMock()
    mock_label = MagicMock()
    
    def query_one_side_effect(selector, type_hint=None):
        if "list" in selector:
            return mock_option_list
        if "table" in selector:
            return mock_data_table
        if "label" in selector:
            return mock_label
        return MagicMock()
        
    screen.query_one = MagicMock(side_effect=query_one_side_effect)
    
    # Mock notify
    screen.notify = MagicMock()
    
    # Load file
    screen._load_file(sample_league_file)
    
    # Verify data loaded
    assert screen.data is not None
    assert screen.data["teams"][0]["name"] == "Lakers"
    
    # Simulate update via player editor callback
    # Player ID 1 is at index 0 of team 0
    new_data = {"id": 1, "fn": "Bronny", "ln": "James", "pos": 1}
    screen.current_team_idx = 0
    
    # Find player index in roster
    # In real execution this is passed, but for test we can just say index 0
    screen._update_player(0, new_data)
    
    # Verify in-memory update
    assert screen.data["teams"][0]["roster"][0]["fn"] == "Bronny"
    assert screen.modified is True
    
    # Save file
    screen._save_file()
    
    # Verify file on disk
    with open(sample_league_file, "r") as f:
        saved_data = json.load(f)
    
    assert saved_data["teams"][0]["roster"][0]["fn"] == "Bronny"

"""
Integration tests for historical NBA data integrity.

These tests verify that specific players exist in specific historical seasons
with correct attributes, ensuring data population logic works correctly.
"""

import pytest
from hoopland.data.repository import DataRepository
from hoopland.data.nba_client import NBAClient

# Mark all tests in this module as slow (NBA API calls)
pytestmark = pytest.mark.slow


@pytest.fixture
def nba_client():
    """Provide an NBAClient instance for direct API testing."""
    return NBAClient()


class TestHistoricalNBAData:
    """Tests for verifying historical NBA player data integrity."""

    @pytest.mark.network
    def test_lebron_james_2006_07_season(self, nba_client):
        """
        Verify LeBron James exists in 2006-07 season with correct attributes.
        
        LeBron was in his 4th season, playing for Cleveland Cavaliers.
        He averaged 27.3 PPG that season (career high at that point).
        """
        # LeBron's NBA player ID
        lebron_id = 2544
        season = "2006-07"
        
        # Fetch league stats for that season
        df = nba_client.get_league_stats(season=season)
        
        # Find LeBron in the data
        lebron_row = df[df["PLAYER_ID"] == lebron_id]
        
        assert len(lebron_row) == 1, f"LeBron James not found in {season} data"
        
        row = lebron_row.iloc[0]
        
        # Verify team is Cleveland (team ID: 1610612739)
        cleveland_team_id = 1610612739
        assert row["TEAM_ID"] == cleveland_team_id, (
            f"Expected LeBron on Cleveland (ID: {cleveland_team_id}), "
            f"got team ID: {row['TEAM_ID']}"
        )
        
        # Verify name
        assert "LeBron" in row["PLAYER_NAME"], (
            f"Expected 'LeBron' in player name, got: {row['PLAYER_NAME']}"
        )
        
        # Verify high scoring - LeBron averaged 27.3 PPG in 2006-07
        # Calculate PPG from totals (PTS / GP)
        if row["GP"] > 0:
            ppg = row["PTS"] / row["GP"]
            assert ppg > 20.0, (
                f"Expected LeBron to average >20 PPG in {season}, got {ppg:.1f}"
            )

    @pytest.mark.network
    def test_lebron_james_2012_13_season(self, nba_client):
        """
        Verify LeBron James exists in 2012-13 season with correct attributes.
        
        LeBron was on Miami Heat, won MVP and Championship that season.
        He averaged 26.8 PPG, 8.0 RPG, 7.3 APG.
        """
        lebron_id = 2544
        season = "2012-13"
        
        df = nba_client.get_league_stats(season=season)
        lebron_row = df[df["PLAYER_ID"] == lebron_id]
        
        assert len(lebron_row) == 1, f"LeBron James not found in {season} data"
        
        row = lebron_row.iloc[0]
        
        # Verify team is Miami Heat (team ID: 1610612748)
        miami_team_id = 1610612748
        assert row["TEAM_ID"] == miami_team_id, (
            f"Expected LeBron on Miami (ID: {miami_team_id}), "
            f"got team ID: {row['TEAM_ID']}"
        )
        
        # Verify championship-level stats
        if row["GP"] > 0:
            ppg = row["PTS"] / row["GP"]
            rpg = row["REB"] / row["GP"]
            apg = row["AST"] / row["GP"]
            
            # LeBron was dominant - should have high stats across the board
            assert ppg > 20.0, f"Expected PPG > 20, got {ppg:.1f}"
            assert rpg > 5.0, f"Expected RPG > 5, got {rpg:.1f}"
            assert apg > 5.0, f"Expected APG > 5, got {apg:.1f}"

    @pytest.mark.network
    def test_lebron_different_teams_across_seasons(self, nba_client):
        """
        Verify the same player (LeBron) exists in multiple seasons with different teams.
        
        This tests that our data model correctly handles player movement.
        """
        lebron_id = 2544
        
        # Fetch multiple seasons
        seasons_teams = {
            "2006-07": 1610612739,  # Cleveland
            "2012-13": 1610612748,  # Miami  
            "2018-19": 1610612747,  # Lakers
        }
        
        for season, expected_team_id in seasons_teams.items():
            df = nba_client.get_league_stats(season=season)
            lebron_row = df[df["PLAYER_ID"] == lebron_id]
            
            assert len(lebron_row) == 1, f"LeBron not found in {season}"
            
            actual_team_id = lebron_row.iloc[0]["TEAM_ID"]
            assert actual_team_id == expected_team_id, (
                f"Season {season}: Expected team {expected_team_id}, "
                f"got {actual_team_id}"
            )

    @pytest.mark.network
    def test_role_player_derek_fisher_2009_10(self, nba_client):
        """
        Verify a non-star player exists in the correct season/team.
        
        Derek Fisher was on the Lakers in 2009-10 (championship year).
        Player ID: 965
        """
        fisher_id = 965
        season = "2009-10"
        
        df = nba_client.get_league_stats(season=season)
        fisher_row = df[df["PLAYER_ID"] == fisher_id]
        
        assert len(fisher_row) == 1, f"Derek Fisher not found in {season} data"
        
        row = fisher_row.iloc[0]
        
        # Lakers team ID: 1610612747
        lakers_team_id = 1610612747
        assert row["TEAM_ID"] == lakers_team_id, (
            f"Expected Fisher on Lakers (ID: {lakers_team_id}), "
            f"got team ID: {row['TEAM_ID']}"
        )
        
        # Verify player name
        assert "Fisher" in row["PLAYER_NAME"], (
            f"Expected 'Fisher' in player name, got: {row['PLAYER_NAME']}"
        )
        
        # Fisher was a role player - reasonable stats (he averaged ~7 PPG)
        if row["GP"] > 0:
            ppg = row["PTS"] / row["GP"]
            assert 3.0 < ppg < 15.0, (
                f"Expected role player PPG between 3-15, got {ppg:.1f}"
            )

    @pytest.mark.network
    def test_season_has_expected_player_count(self, nba_client):
        """
        Verify that a season has a reasonable number of players.
        
        NBA seasons typically have 400-550 players who see playing time.
        """
        season = "2016-17"
        df = nba_client.get_league_stats(season=season)
        
        player_count = len(df)
        
        assert player_count > 400, (
            f"Expected >400 players in {season}, got {player_count}"
        )
        assert player_count < 600, (
            f"Expected <600 players in {season}, got {player_count}"
        )

    @pytest.mark.network  
    def test_player_has_required_stat_columns(self, nba_client):
        """
        Verify that player data includes all required stat columns.
        
        These columns are needed for the generation logic.
        """
        season = "2020-21"
        df = nba_client.get_league_stats(season=season)
        
        required_columns = [
            "PLAYER_ID",
            "PLAYER_NAME", 
            "TEAM_ID",
            "GP",  # Games Played
            "PTS",  # Points
            "REB",  # Rebounds
            "AST",  # Assists
            "STL",  # Steals
            "BLK",  # Blocks
            "FG_PCT",  # Field Goal Percentage
            "FG3_PCT",  # 3-Point Percentage
            "FT_PCT",  # Free Throw Percentage
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

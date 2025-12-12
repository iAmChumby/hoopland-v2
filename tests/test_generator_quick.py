import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append("src")

from hoopland.blocks.generator import Generator
from hoopland.models import structs


class TestGeneratorQuick(unittest.TestCase):
    @patch("hoopland.blocks.generator.init_db")
    @patch("hoopland.blocks.generator.repository.DataRepository")
    def test_generate_league_flow(self, mock_repo_cls, mock_init_db):
        # Setup Mocks
        mock_session = MagicMock()
        mock_init_db.return_value = MagicMock(return_value=mock_session)

        mock_repo = mock_repo_cls.return_value

        # Mock Player Query
        mock_player = MagicMock()
        mock_player.id = 1
        mock_player.team_id = "101"
        mock_player.name = "LeBron James"
        mock_player.appearance = {"skin_tone": 8}
        mock_player.raw_stats = {"PTS": 25.0, "REB": 5.0, "AST": 6.0}

        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            mock_player
        ]

        # Mock Team Info lookup
        mock_repo.nba_client.get_team_by_id.return_value = {
            "city": "Cleveland",
            "nickname": "Cavaliers",
            "abbreviation": "CLE",
        }

        # Init Generator
        gen = Generator()

        # Run Generate
        year = "2004"
        league = gen.generate_league(year)

        # Verify Repo calls
        mock_repo.sync_nba_season_stats.assert_called_with(season="2003-04")
        mock_repo.backfill_appearance.assert_called()

        # Verify Output Structure
        self.assertIsInstance(league, structs.League)
        self.assertEqual(league.leagueName, "NBA 2004")
        self.assertEqual(len(league.teams), 1)
        self.assertEqual(league.teams[0].name, "Cavaliers")
        self.assertEqual(league.teams[0].roster[0].fn, "LeBron")

        # Verify File Save
        filename = "TEST_League.txt"
        gen.to_json(league, filename)

        expected_path = os.path.join("output", "2004", filename)
        self.assertTrue(os.path.exists(expected_path))
        print(f"Verified file created at {expected_path}")


if __name__ == "__main__":
    unittest.main()

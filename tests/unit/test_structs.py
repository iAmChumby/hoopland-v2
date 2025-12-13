"""
Unit tests for the models/structs module.
Tests dataclass creation and field defaults for the target schema format.
"""

import pytest
from hoopland.models.structs import Meta, Player, Team, League


class TestMetaDataclass:
    """Tests for the Meta dataclass."""

    def test_meta_default_values(self):
        """Test Meta has correct default values."""
        meta = Meta()
        assert meta.saveName == "Hoopland File"
        assert meta.buildVersion == "1.0"
        assert meta.dataType == 1  # Now an int (1=League)
        assert meta.uPID == -1
        assert meta.uTID == -1

    def test_meta_custom_values(self):
        """Test Meta with custom values."""
        meta = Meta(
            saveName="Custom Save",
            dataType=2,  # 2 = Draft Class
            countryGeneration=1,
            generatedCountries=[0, 1, 2]
        )
        assert meta.saveName == "Custom Save"
        assert meta.dataType == 2
        assert meta.countryGeneration == 1
        assert meta.generatedCountries == [0, 1, 2]


class TestPlayerDataclass:
    """Tests for the Player dataclass."""

    def test_player_required_fields(self):
        """Test Player with required fields."""
        player = Player(id=1, tid=10, fn="John", ln="Doe")
        assert player.id == 1
        assert player.tid == 10
        assert player.fn == "John"
        assert player.ln == "Doe"

    def test_player_default_values(self):
        """Test Player default values match target schema."""
        player = Player(id=1, tid=10, fn="Test", ln="Player")
        assert player.age == 0
        assert player.ht == 0
        assert player.wt == 0
        assert player.pos == 0
        assert player.rating == 0.0  # Now float
        assert player.pot == 0
        # Appearance is now a dict
        assert player.appearance == {}
        # Accessories is now a list
        assert player.accessories == []
        # Attributes is Dict[str, List[int]]
        assert player.attributes == {}
        assert player.stats == {}

    def test_player_full_data(self):
        """Test Player with full target schema data."""
        player = Player(
            id=12345,
            tid=8,  # Target schema team ID
            fn="LeBron",
            ln="James",
            tag="King",
            home="Akron",
            num=23,
            age=38,
            ht=81,  # 6'9"
            wt=250,
            pos=3,  # SF
            rating=9.5,
            pot=10,
            appearance={"skinC": "C68040", "hair": "0005", "hairC": "1A1A1A"},
            accessories=[{"headAcc": 0}, {"headAcc": 0}, {"headAcc": 0}, {"headAcc": 0}],
            attributes={"INS": [9, 9], "MID": [8, 8], "DRE": [7, 8]}
        )
        assert player.fn == "LeBron"
        assert player.ht == 81
        assert player.tag == "King"
        assert player.num == 23
        assert player.appearance["skinC"] == "C68040"
        assert len(player.accessories) == 4
        assert player.attributes["INS"] == [9, 9]

    def test_player_draft_class(self):
        """Test Player for draft class (tid=-1)."""
        player = Player(id=1, tid=-1, fn="Rookie", ln="Prospect")
        assert player.tid == -1


class TestTeamDataclass:
    """Tests for the Team dataclass."""

    def test_team_required_fields(self):
        """Test Team with required fields."""
        team = Team(id=8, city="Atlanta", name="Hawks", shortName="ATL")
        assert team.id == 8
        assert team.city == "Atlanta"
        assert team.name == "Hawks"
        assert team.shortName == "ATL"

    def test_team_default_values(self):
        """Test Team default values match target schema."""
        team = Team(id=1, city="Test", name="Team", shortName="TST")
        assert team.roster == []
        assert team.arenaName == ""
        assert team.logoURL == ""
        assert team.division == 0
        # teamColors is now a list
        assert team.teamColors == []
        # New fields
        assert team.location == {}
        assert team.frontOffice == {}
        assert team.uniforms == []
        assert team.court == {}

    def test_team_with_roster(self):
        """Test Team with players in roster."""
        player1 = Player(id=1, tid=10, fn="Player", ln="One")
        player2 = Player(id=2, tid=10, fn="Player", ln="Two")
        team = Team(
            id=10,
            city="Boston",
            name="Celtics",
            shortName="BOS",
            roster=[player1, player2],
            teamColors=["007A33", "BA9653", "FFFFFF"]
        )
        assert len(team.roster) == 2
        assert team.roster[0].fn == "Player"
        assert len(team.teamColors) == 3

    def test_team_championships(self):
        """Test Team with championships (now a dict)."""
        team = Team(
            id=28,
            city="Los Angeles",
            name="Lakers",
            shortName="LAL",
            championships={"id": 0, "league": 0, "yearsWon": [2000, 2001, 2002]}
        )
        assert team.championships["yearsWon"] == [2000, 2001, 2002]


class TestLeagueDataclass:
    """Tests for the League dataclass."""

    def test_league_required_fields(self):
        """Test League with required fields."""
        league = League(leagueName="NBA 2024")
        assert league.leagueName == "NBA 2024"

    def test_league_default_values(self):
        """Test League default values."""
        league = League(leagueName="Test League")
        assert league.shortName == ""
        assert league.teams == []
        assert league.freeAgents == []
        assert league.settings == {}
        assert isinstance(league.meta, Meta)
        # New fields
        assert league.retirees == []
        assert league.hallOfFame == []
        assert league.commissioner == {}
        assert league.referee == {}

    def test_league_with_teams(self):
        """Test League with teams."""
        team1 = Team(id=1, city="City", name="Team1", shortName="T1")
        team2 = Team(id=2, city="Town", name="Team2", shortName="T2")
        league = League(
            leagueName="Test League",
            teams=[team1, team2]
        )
        assert len(league.teams) == 2

    def test_league_with_meta(self):
        """Test League with custom Meta."""
        meta = Meta(saveName="NBA 2024 Season", dataType=1)
        league = League(
            leagueName="NBA 2024",
            meta=meta
        )
        assert league.meta.saveName == "NBA 2024 Season"
        assert league.meta.dataType == 1

    def test_league_draft_class_type(self):
        """Test League for draft class."""
        meta = Meta(dataType=2)  # 2 = Draft Class
        league = League(
            leagueName="2024 Draft Class",
            meta=meta
        )
        assert league.meta.dataType == 2

    def test_league_with_settings(self):
        """Test League with settings."""
        league = League(
            leagueName="Custom League",
            settings={"gameLength": 12, "difficulty": 3}
        )
        assert league.settings["gameLength"] == 12

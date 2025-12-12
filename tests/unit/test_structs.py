"""
Unit tests for the models/structs module.
Tests dataclass creation and field defaults.
"""

import pytest
from hoopland.models.structs import Meta, Award, Player, Team, League


class TestMetaDataclass:
    """Tests for the Meta dataclass."""

    def test_meta_default_values(self):
        """Test Meta has correct default values."""
        meta = Meta()
        assert meta.saveName == "Hoopland File"
        assert meta.buildVersion == "1.0"
        assert meta.dataType == ""

    def test_meta_custom_values(self):
        """Test Meta with custom values."""
        meta = Meta(
            saveName="Custom Save",
            dataType="League",
            countryGeneration=1
        )
        assert meta.saveName == "Custom Save"
        assert meta.dataType == "League"
        assert meta.countryGeneration == 1


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
        """Test Player default values."""
        player = Player(id=1, tid=10, fn="Test", ln="Player")
        assert player.age == 0
        assert player.ht == 0
        assert player.wt == 0
        assert player.pos == 0
        assert player.rating == 0
        assert player.pot == 0
        assert player.appearance == 0
        assert player.accessories == {}
        assert player.attributes == {}
        assert player.stats == {}

    def test_player_full_data(self):
        """Test Player with full data."""
        player = Player(
            id=12345,
            tid=1610612737,
            fn="LeBron",
            ln="James",
            age=38,
            ht=81,  # 6'9"
            wt=250,
            pos=3,  # SF
            rating=9,
            pot=10,
            appearance=3,
            accessories={"hair": 5, "beard": 2},
            attributes={"shooting_inside": 9, "defense": 8}
        )
        assert player.fn == "LeBron"
        assert player.ht == 81
        assert player.accessories["hair"] == 5
        assert player.attributes["shooting_inside"] == 9

    def test_player_draft_class(self):
        """Test Player for draft class (tid=-1)."""
        player = Player(id=1, tid=-1, fn="Rookie", ln="Prospect")
        assert player.tid == -1


class TestTeamDataclass:
    """Tests for the Team dataclass."""

    def test_team_required_fields(self):
        """Test Team with required fields."""
        team = Team(id=1, city="Atlanta", name="Hawks", shortName="ATL")
        assert team.id == 1
        assert team.city == "Atlanta"
        assert team.name == "Hawks"
        assert team.shortName == "ATL"

    def test_team_default_values(self):
        """Test Team default values."""
        team = Team(id=1, city="Test", name="Team", shortName="TST")
        assert team.roster == []
        assert team.arenaName == ""
        assert team.logoURL == ""
        assert team.division == 0
        assert team.teamColors == {}

    def test_team_with_roster(self):
        """Test Team with players in roster."""
        player1 = Player(id=1, tid=10, fn="Player", ln="One")
        player2 = Player(id=2, tid=10, fn="Player", ln="Two")
        team = Team(
            id=10,
            city="Boston",
            name="Celtics",
            shortName="BOS",
            roster=[player1, player2]
        )
        assert len(team.roster) == 2
        assert team.roster[0].fn == "Player"

    def test_team_championships(self):
        """Test Team with championships."""
        team = Team(
            id=1,
            city="Lakers",
            name="Los Angeles",
            shortName="LAL",
            championships=17
        )
        assert team.championships == 17


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
        meta = Meta(saveName="NBA 2024 Season", dataType="League")
        league = League(
            leagueName="NBA 2024",
            meta=meta
        )
        assert league.meta.saveName == "NBA 2024 Season"
        assert league.meta.dataType == "League"

    def test_league_draft_class_type(self):
        """Test League for draft class."""
        meta = Meta(dataType="Draft Class")
        league = League(
            leagueName="2024 Draft Class",
            meta=meta
        )
        assert league.meta.dataType == "Draft Class"

    def test_league_with_settings(self):
        """Test League with settings."""
        league = League(
            leagueName="Custom League",
            settings={"gameLength": 12, "difficulty": 3}
        )
        assert league.settings["gameLength"] == 12


class TestAwardDataclass:
    """Tests for the Award dataclass."""

    def test_award_required_fields(self):
        """Test Award with required fields."""
        award = Award(id=1, name="MVP", shortName="MVP")
        assert award.id == 1
        assert award.name == "MVP"
        assert award.shortName == "MVP"

    def test_award_with_team(self):
        """Test Award with team reference."""
        award = Award(id=2, name="DPOY", shortName="DPOY", team=1610612737)
        assert award.team == 1610612737

    def test_award_default_team(self):
        """Test Award default team is None."""
        award = Award(id=1, name="Test", shortName="T")
        assert award.team is None

import pytest
from src.hoopland.data import historical_loader
from src.hoopland.data import awards_loader
from src.hoopland.blocks import team_assets
import pandas as pd


class TestHistoricalLoader:
    def test_get_team_for_year_supersonics_2007(self):
        result = historical_loader.get_team_for_year("1610612760", 2007)
        assert result["city"] == "Seattle"
        assert result["name"] == "SuperSonics"
        assert result["tag"] == "SEA"

    def test_get_team_for_year_thunder_2010(self):
        result = historical_loader.get_team_for_year("1610612760", 2010)
        assert result["city"] == "Oklahoma City"
        assert result["name"] == "Thunder"
        assert result["tag"] == "OKC"

    def test_get_team_for_year_nets_new_jersey_2005(self):
        result = historical_loader.get_team_for_year("1610612751", 2005)
        assert result["city"] == "New Jersey"
        assert result["name"] == "Nets"
        assert result["tag"] == "NJN"

    def test_get_team_for_year_nets_brooklyn_2015(self):
        result = historical_loader.get_team_for_year("1610612751", 2015)
        assert result["city"] == "Brooklyn"
        assert result["name"] == "Nets"
        assert result["tag"] == "BKN"

    def test_get_team_for_year_grizzlies_vancouver_2000(self):
        result = historical_loader.get_team_for_year("1610612763", 2000)
        assert result["city"] == "Vancouver"
        assert result["name"] == "Grizzlies"
        assert result["tag"] == "VAN"

    def test_get_team_for_year_grizzlies_memphis_2005(self):
        result = historical_loader.get_team_for_year("1610612763", 2005)
        assert result["city"] == "Memphis"
        assert result["name"] == "Grizzlies"
        assert result["tag"] == "MEM"

    def test_get_team_for_year_warriors_san_francisco_1965(self):
        result = historical_loader.get_team_for_year("1610612744", 1965)
        assert result["city"] == "San Francisco"
        assert result["name"] == "Warriors"
        assert result["tag"] == "SFW"

    def test_get_team_for_year_warriors_golden_state_2020(self):
        result = historical_loader.get_team_for_year("1610612744", 2020)
        assert result["city"] == "Golden State"
        assert result["name"] == "Warriors"
        assert result["tag"] == "GSW"

    def test_get_team_for_year_hornets_charlotte_1995(self):
        result = historical_loader.get_team_for_year("1610612740", 1995)
        assert result["city"] == "Charlotte"
        assert result["name"] == "Hornets"
        assert result["tag"] == "CHH"

    def test_get_team_for_year_pelicans_2015(self):
        result = historical_loader.get_team_for_year("1610612740", 2015)
        assert result["city"] == "New Orleans"
        assert result["name"] == "Pelicans"
        assert result["tag"] == "NOP"

    def test_get_team_for_year_celtics_never_moved(self):
        result = historical_loader.get_team_for_year("1610612738", 2000)
        assert result["city"] == "Boston"
        assert result["name"] == "Celtics"
        assert result["tag"] == "BOS"

    def test_get_team_for_year_unknown_team(self):
        result = historical_loader.get_team_for_year("9999999", 2020)
        assert result == {}

    def test_get_team_city(self):
        city = historical_loader.get_team_city("1610612760", 2007)
        assert city == "Seattle"

    def test_get_team_name(self):
        name = historical_loader.get_team_name("1610612760", 2010)
        assert name == "Thunder"

    def test_get_team_tag(self):
        tag = historical_loader.get_team_tag("1610612751", 2020)
        assert tag == "BKN"

    def test_team_existed_in_year_true(self):
        assert historical_loader.team_existed_in_year("1610612760", 2000) is True

    def test_team_existed_in_year_false(self):
        assert historical_loader.team_existed_in_year("1610612760", 1950) is False


class TestChampionships:
    def test_generate_championships_lakers(self):
        result = team_assets.generate_championships("1610612747", 2005)
        assert 2000 in result["yearsWon"]
        assert 2001 in result["yearsWon"]
        assert 2002 in result["yearsWon"]
        assert 2009 not in result["yearsWon"]
        assert 2010 not in result["yearsWon"]
        assert 2020 not in result["yearsWon"]

    def test_generate_championships_bulls(self):
        result = team_assets.generate_championships("1610612741", 2000)
        assert 1991 in result["yearsWon"]
        assert 1998 in result["yearsWon"]
        assert len(result["yearsWon"]) == 6

    def test_generate_championships_celtics_recent(self):
        result = team_assets.generate_championships("1610612738", 2010)
        assert 2008 in result["yearsWon"]
        assert 2024 not in result["yearsWon"]

    def test_generate_championships_clippers_none(self):
        result = team_assets.generate_championships("1610612746", 2020)
        assert result["yearsWon"] == []


class TestAnnouncers:
    def test_generate_front_office_with_announcers(self):
        result = team_assets.generate_front_office(0, "Hawks", "1610612737")
        assert "Bob Rathbun" in result["announcers"]
        assert "Dominique Wilkins" in result["announcers"]

    def test_generate_front_office_celtics(self):
        result = team_assets.generate_front_office(0, "Celtics", "1610612738")
        assert "Mike Gorman" in result["announcers"]

    def test_generate_front_office_unknown_team(self):
        result = team_assets.generate_front_office(0, "Unknown", "9999999")
        assert "Home Announcer" in result["announcers"]


class TestAwardsLoader:
    def test_process_player_awards_empty_df(self):
        empty_df = pd.DataFrame()
        result = awards_loader.process_player_awards(empty_df, 2020)
        assert result == []

    def test_process_player_awards_with_mvp(self):
        awards_df = pd.DataFrame([
            {"DESCRIPTION": "NBA Most Valuable Player", "SEASON": "2002-03", "ALL_NBA_TEAM_NUMBER": None}
        ])
        result = awards_loader.process_player_awards(awards_df, 2010)
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert 2003 in result[0]["yearsWon"]

    def test_process_player_awards_filters_future_years(self):
        awards_df = pd.DataFrame([
            {"DESCRIPTION": "NBA Most Valuable Player", "SEASON": "2019-20", "ALL_NBA_TEAM_NUMBER": None}
        ])
        result = awards_loader.process_player_awards(awards_df, 2015)
        assert result == []

    def test_process_player_awards_all_nba_team(self):
        awards_df = pd.DataFrame([
            {"DESCRIPTION": "All-NBA", "SEASON": "2010-11", "ALL_NBA_TEAM_NUMBER": 1}
        ])
        result = awards_loader.process_player_awards(awards_df, 2015)
        assert len(result) == 1
        assert result[0]["id"] == 7

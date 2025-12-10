
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .screens.home import MainMenu
from .screens.league import LeagueConfig
from .screens.draft import DraftConfig

class HooplandApp(App):
    """A TUI for generating Hoopland V2 files."""

    CSS = """
    Screen {
        layout: vertical;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        width: 100%;
    }

    .main_menu_container {
        align: center middle;
    }

    .menu_buttons {
        width: 40;
        height: auto;
        border: solid $accent;
    }
    
    .form_container {
        width: 50;
        height: auto;
        border: solid $accent;
        padding: 1;
    }

    Button {
        width: 100%;
        margin: 1;
    }
    
    Input {
        margin: 1;
    }
    
    Label {
        margin: 1;
        text-align: center;
        width: 100%;
    }
    """

    SCREENS = {
        "league_config": LeagueConfig,
        "draft_config": DraftConfig,
    }

    def on_mount(self) -> None:
        self.push_screen(MainMenu())

if __name__ == "__main__":
    app = HooplandApp()
    app.run()

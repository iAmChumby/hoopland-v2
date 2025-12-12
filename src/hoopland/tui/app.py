from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .screens.home import MainMenu
from .screens.league import LeagueConfig
from .screens.draft import DraftConfig
import logging

# Configure logging
logging.basicConfig(
    filename="hoopland.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",
)


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
    

    
    .log_label {
        margin-top: 1;
        text-align: center;
        text-style: bold;
        width: 100%;
    }
    
    .log_box {
        height: 1fr;
        min-height: 10;
        width: 60;
        border: solid $accent;
        margin: 1;
        background: $surface;
        scrollbar-gutter: stable;
    }
    
    .copy_btn {
        margin: 1;
        width: 60;
        background: $panel;
        color: $text;
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

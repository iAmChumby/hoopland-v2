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

    /* Main Menu Styles */
    .main_menu_container {
        align: center middle;
        height: 100%;
    }

    .menu_buttons {
        width: 40%;
        min-width: 40;
        max-width: 80;
        height: auto;
        border: solid $accent;
    }

    /* Generation Screen Styles */
    .split-layout {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }

    .left-panel {
        width: 35%;
        height: 100%;
        border-right: solid $accent;
        padding: 2;
        align: center middle;
    }

    .right-panel {
        width: 65%;
        height: 100%;
        padding: 1;
    }
    
    .form_container {
        width: 100%;
        height: auto;
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
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    
    .log_box {
        width: 100%;
        height: 1fr;
        border: solid $accent;
        background: $surface;
        scrollbar-gutter: stable;
    }
    
    .copy_btn {
        margin-top: 1;
        width: 100%;
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

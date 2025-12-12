from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .screens.home import MainMenu
from .screens.league import LeagueConfig
from .screens.draft import DraftConfig
import logging

# Configure logging - Initial setup for TUI (no file yet)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[], # Handlers will be added by Textual or screens
)


class HooplandApp(App):
    """A TUI for generating Hoopland V2 files."""

    CSS = """
    Screen {
        layout: vertical;
    }
    
    /* ============================================
       Unified Theme Colors & Base Styles
       ============================================ */
    
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        width: 100%;
        margin-bottom: 1;
    }

    /* ============================================
       Main Menu Styles
       ============================================ */
    
    .main_menu_container {
        align: center middle;
        height: 100%;
        padding: 2;
    }

    .menu_buttons {
        width: auto;
        min-width: 30;
        max-width: 60;
        height: auto;
        padding: 2;
        border: solid $accent;
        background: $surface;
    }

    /* ============================================
       Responsive Split-Layout (Generation Screens)
       ============================================ */
    
    .split-layout {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }

    .left-panel {
        width: 1fr;
        min-width: 25;
        max-width: 45;
        height: 100%;
        border-right: solid $accent;
        padding: 2;
        align: center top;
    }

    .right-panel {
        width: 2fr;
        min-width: 35;
        height: 100%;
        padding: 1;
    }
    
    .form_container {
        width: 100%;
        height: auto;
        padding: 1;
    }

    /* ============================================
       Form Elements
       ============================================ */

    Button {
        width: 100%;
        margin: 1 0;
    }
    
    Input {
        margin: 1 0;
        width: 100%;
    }
    
    Label {
        margin: 1 0;
        text-align: center;
        width: 100%;
    }
    
    /* ============================================
       Log Panel Styles
       ============================================ */
    
    .log_label {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
        color: $text-muted;
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

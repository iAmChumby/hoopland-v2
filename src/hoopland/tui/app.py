from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .screens.home import MainMenu
from .screens.league import LeagueConfig
from .screens.draft import DraftConfig
from .screens.ncaa import NCAAConfig
from .screens.editor import EditorScreen
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

    /* ============================================
       Home Screen Layout
       ============================================ */
    
    .home-layout {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }
    
    .home-actions {
        width: 1fr;
        min-width: 25;
        max-width: 40;
        height: 100%;
        padding: 2;
        border-right: solid $accent;
    }
    
    .home-recent {
        width: 2fr;
        min-width: 35;
        height: 100%;
        padding: 2;
    }
    
    .recent-list {
        height: 1fr;
        border: solid $accent;
        background: $surface;
        margin: 1 0;
    }
    
    .section-header {
        text-style: bold;
        margin: 1 0;
        color: $text-muted;
    }
    
    .spacer {
        height: 1;
    }
    
    /* ============================================
       Switch/Toggle Styles
       ============================================ */
    
    .switch-row {
        height: auto;
        margin: 1 0;
        align: left middle;
    }
    
    .switch-label {
        margin-left: 1;
    }

    /* ============================================
       Editor Screen Layout
       ============================================ */
    
    .editor-layout {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }
    
    .editor-sidebar {
        width: 1fr;
        min-width: 25;
        max-width: 40;
        height: 100%;
        padding: 1;
        border-right: solid $accent;
    }
    
    .editor-main {
        width: 3fr;
        min-width: 50;
        height: 100%;
        padding: 1;
    }
    
    .file-list {
        height: auto;
        max-height: 10;
        border: solid $accent;
        background: $surface;
        margin: 1 0;
    }
    
    .team-list {
        height: 1fr;
        border: solid $accent;
        background: $surface;
        margin: 1 0;
    }
    
    .player-table {
        height: 1fr;
        border: solid $accent;
        background: $surface;
    }
    
    .editor-buttons {
        height: auto;
        margin-top: 1;
    }
    
    .editor-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    SCREENS = {
        "league_config": LeagueConfig,
        "draft_config": DraftConfig,
        "ncaa_config": NCAAConfig,
        "editor": EditorScreen,
    }

    def on_mount(self) -> None:
        self.push_screen(MainMenu())


def main():
    """Entry point for the hoopgen command."""
    app = HooplandApp()
    app.run()


if __name__ == "__main__":
    main()

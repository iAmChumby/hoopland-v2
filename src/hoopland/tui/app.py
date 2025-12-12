from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .screens.home import MainMenu
from .screens.league import LeagueConfig
from .screens.draft import DraftConfig
from .screens.ncaa import NCAAConfig
from .screens.editor import EditorScreen
from .screens.player_editor import PlayerEditorScreen
import logging

# ... (logging setup remains)

class HooplandApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    .main_menu_container {
        width: 100%;
        height: 100%;
        border: thick $background 80%;
        background: $surface;
    }
    .split-layout {
        width: 100%;
        height: 100%;
    }
    .left-panel {
        width: 35%;
        height: 100%;
        padding: 2;
    }
    .right-panel {
        width: 65%;
        height: 100%;
        border-left: solid $primary;
        padding: 2;
    }
    .left-panel Button {
        width: 100%;
        margin-bottom: 1;
    }
    .section-header, .log_label {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    .log_box {
        height: 1fr;
        border: solid $accent;
    }
    .copy_btn {
        width: 100%;
        margin-top: 1;
    }
    """

    SCREENS = {
        "league_config": LeagueConfig,
        "draft_config": DraftConfig,
        "ncaa_config": NCAAConfig,
        "editor": EditorScreen,
        "player_editor": PlayerEditorScreen,
    }

    def on_mount(self) -> None:
        self.push_screen(MainMenu())


def main():
    """Entry point for the hoopgen command."""
    app = HooplandApp()
    app.run()


if __name__ == "__main__":
    main()

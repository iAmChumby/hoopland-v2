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
    # ... (CSS remains)

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

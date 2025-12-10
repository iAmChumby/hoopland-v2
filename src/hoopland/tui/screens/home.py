
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Label
from textual.containers import Container, Vertical

class MainMenu(Screen):
    """The main menu screen."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Welcome to Hoopland V2", classes="title"),
            Vertical(
                Button("Generate League File", id="btn_league", variant="primary"),
                Button("Generate Draft Class", id="btn_draft", variant="primary"),
                Button("Exit", id="btn_exit", variant="error"),
                classes="menu_buttons"
            ),
            classes="main_menu_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_league":
            self.app.push_screen("league_config")
        elif event.button.id == "btn_draft":
            self.app.push_screen("draft_config")
        elif event.button.id == "btn_exit":
            self.app.exit()

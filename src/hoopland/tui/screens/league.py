
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Input, Label, Static
from textual.containers import Container, Vertical
from ...blocks.generator import Generator

class LeagueConfig(Screen):
    """Screen for configuring league generation."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Configuring League Generation", classes="title"),
            Vertical(
                Label("Enter Season Year (e.g., 2024):"),
                Input(placeholder="2024", id="input_year"),
                Button("Generate League", id="btn_generate", variant="success"),
                Button("Back", id="btn_back", variant="primary"),
                classes="form_container"
            ),
            classes="main_menu_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back":
            self.app.pop_screen()
        elif event.button.id == "btn_generate":
            year = self.query_one("#input_year", Input).value
            if not year:
                self.notify("Please enter a year.", severity="error")
                return
            
            self.notify(f"Generating League for {year}...", severity="information")
            try:
                # TODO: Run this in a worker to avoid freezing UI
                gen = Generator()
                league = gen.generate_league(year)
                
                # Save to file
                filename = f"NBA_{year}_League.txt"
                gen.to_json(league, filename)
                
                self.notify(f"Success! Saved to {filename}", severity="information")
            except Exception as e:
                self.notify(f"Error: {str(e)}", severity="error")

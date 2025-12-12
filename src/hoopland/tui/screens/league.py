from textual.app import ComposeResult
from textual.screen import Screen

from textual.widgets import Header, Footer, Button, Input, Label, Static, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual import work
from ...blocks.generator import Generator
from ..logging_handler import TextualLogHandler
from ...logger import setup_logger
import logging


class LeagueConfig(Screen):
    """Screen for configuring league generation."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Configuring League Generation", classes="title"),
            Horizontal(
                # Left Panel: Configuration
                Vertical(
                    Label("Enter Season Year (e.g., 2023):"),
                    Input(placeholder="2023", id="input_year"),
                    Button("Generate League", id="btn_generate", variant="success"),
                    Button("Back", id="btn_back", variant="primary"),
                    classes="left-panel",
                ),
                # Right Panel: Logs
                Vertical(
                    Label("Real-time Logs", classes="log_label"),
                    RichLog(highlight=True, markup=True, id="log_view", classes="log_box"),
                    Button("Copy Logs to Clipboard", id="btn_copy_logs", classes="copy_btn"),
                    classes="right-panel",
                ),
                classes="split-layout",
            ),
            classes="main_menu_container",
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

            self.query_one("#btn_generate", Button).disabled = True
            self.run_generation(year)

        elif event.button.id == "btn_copy_logs":
            log_view = self.query_one("#log_view", RichLog)
            content = "\n".join([line.text for line in log_view.lines])
            self.app.copy_to_clipboard(content)
            self.notify("Logs copied to clipboard!")

    @work(thread=True)
    def run_generation(self, year: str) -> None:
        self.app.call_from_thread(
            self.notify, f"Generating League for {year}...", title="Status"
        )
        try:
            # Setup logging for this run
            # Note: We need to ensure the textual handler stays attached or is re-added
            # The setup_logger clears FileHandlers but shouldn't touch StreamHandlers/Custom handlers attached to root
            # BUT TextualLogHandler is attached to root.
            # Let's import setup_logger inside the method or at top level
            setup_logger(mode="NBA", year=year)
            
            gen = Generator()
            league = gen.generate_league(year)


            # Save to file
            filename = f"NBA_{year}_League.txt"
            gen.to_json(league, filename)

            self.app.call_from_thread(
                self.notify, f"Success! Saved to {filename}", severity="information"
            )
        except Exception as e:
            logging.error(f"Generation failed: {e}")
            self.app.call_from_thread(self.notify, f"Error: {str(e)}", severity="error")
        finally:
            self.app.call_from_thread(self.enable_button)

    def enable_button(self) -> None:
        self.query_one("#btn_generate", Button).disabled = False

    def on_mount(self) -> None:
        # Setup logging handler
        log_view = self.query_one("#log_view", RichLog)

        # Clear existing logs for fresh view
        log_view.clear()

        self.handler = TextualLogHandler(log_view)
        logging.getLogger().addHandler(self.handler)
        logging.info("Real-time log viewer initialized.")

    def on_unmount(self) -> None:
        if hasattr(self, "handler"):
            logging.getLogger().removeHandler(self.handler)

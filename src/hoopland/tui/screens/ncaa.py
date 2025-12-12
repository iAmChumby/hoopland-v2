from textual.app import ComposeResult
from textual.screen import Screen

from textual.widgets import Header, Footer, Button, Input, Label, Static, RichLog, Switch
from textual.containers import Container, Vertical, Horizontal
from textual import work
from ...blocks.generator import Generator
from ..logging_handler import TextualLogHandler
from ...logger import setup_logger
import logging


class NCAAConfig(Screen):
    """Screen for configuring NCAA league generation with tournament mode option."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("NCAA League Generation", classes="title"),
            Horizontal(
                # Left Panel: Configuration
                Vertical(
                    Label("Enter Season Year (e.g., 2024):"),
                    Input(placeholder="2024", id="input_year"),
                    Label(""),
                    Horizontal(
                        Switch(value=True, id="tournament_mode"),
                        Label("Tournament Mode (64 teams)", classes="switch-label"),
                        classes="switch-row",
                    ),
                    Label(""),
                    Button("Generate NCAA League", id="btn_generate", variant="success"),
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

            tournament_mode = self.query_one("#tournament_mode", Switch).value
            self.query_one("#btn_generate", Button).disabled = True
            self.run_generation(year, tournament_mode)

        elif event.button.id == "btn_copy_logs":
            log_view = self.query_one("#log_view", RichLog)
            content = "\n".join([line.text for line in log_view.lines])
            self.app.copy_to_clipboard(content)
            self.notify("Logs copied to clipboard!")

    @work(thread=True)
    def run_generation(self, year: str, tournament_mode: bool) -> None:
        mode_label = "Tournament (64 teams)" if tournament_mode else "Full"
        self.app.call_from_thread(
            self.notify, f"Generating NCAA {year} [{mode_label}]...", title="Status"
        )
        try:
            setup_logger(mode="NCAA", year=year)
            gen = Generator()
            league = gen.generate_ncaa_league(year, tournament_mode=tournament_mode)

            # Save to file
            suffix = "_Tournament" if tournament_mode else ""
            filename = f"NCAA_{year}{suffix}_League.txt"
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
        log_view.clear()

        self.handler = TextualLogHandler(log_view)
        logging.getLogger().addHandler(self.handler)
        logging.info("NCAA generation ready. Tournament mode recommended for faster generation.")

    def on_unmount(self) -> None:
        if hasattr(self, "handler"):
            logging.getLogger().removeHandler(self.handler)

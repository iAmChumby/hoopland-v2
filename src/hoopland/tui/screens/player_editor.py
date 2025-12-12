from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static
from textual.containers import Container, Vertical, Horizontal, Grid
from dataclasses import dataclass

class PlayerEditorScreen(ModalScreen):
    """Screen for editing a single player's attributes."""

    CSS = """
    PlayerEditorScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    .label {
        padding: 1;
    }
    
    .input {
        width: 100%;
    }
    
    #buttons {
        column-span: 2;
        align: right bottom;
        height: auto;
    }
    
    Button {
        margin-left: 1;
    }
    """

    def __init__(self, player_data: dict, on_save=None, **kwargs):
        super().__init__(**kwargs)
        self.player_data = player_data
        self.on_save = on_save
        
        # Extract initial values
        self.initial_name = f"{player_data.get('fn', '')} {player_data.get('ln', '')}".strip()
        self.initial_pos = str(player_data.get('pos', '1'))
        self.initial_ht = str(player_data.get('ht', '72'))
        self.initial_wt = str(player_data.get('wt', '200'))

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label("Name:", classes="label")
            yield Input(value=self.initial_name, id="input_name", classes="input")
            
            yield Label("Position (1-5):", classes="label")
            yield Input(value=self.initial_pos, id="input_pos", classes="input")
            
            yield Label("Height (inches):", classes="label")
            yield Input(value=self.initial_ht, id="input_ht", classes="input")
            
            yield Label("Weight (lbs):", classes="label")
            yield Input(value=self.initial_wt, id="input_wt", classes="input")
            
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="btn_cancel")
                yield Button("Save", variant="success", id="btn_save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            self._save_changes()
        elif event.button.id == "btn_cancel":
            self.dismiss()

    def _save_changes(self) -> None:
        """Collect inputs and update player data."""
        name = self.query_one("#input_name", Input).value
        pos = self.query_one("#input_pos", Input).value
        ht = self.query_one("#input_ht", Input).value
        wt = self.query_one("#input_wt", Input).value
        
        # Split name strictly on first space for simplicity
        parts = name.split(" ", 1)
        fn = parts[0]
        ln = parts[1] if len(parts) > 1 else ""
        
        updated_data = self.player_data.copy()
        updated_data["fn"] = fn
        updated_data["ln"] = ln
        
        try:
            updated_data["pos"] = int(pos)
        except ValueError:
            pass # Keep original if invalid
            
        try:
            updated_data["ht"] = int(ht)
        except ValueError:
            pass

        try:
            updated_data["wt"] = int(wt)
        except ValueError:
            pass
            
        if self.on_save:
            self.on_save(updated_data)
            
        self.dismiss(updated_data)

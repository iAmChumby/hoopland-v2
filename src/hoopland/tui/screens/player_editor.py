
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TabbedContent, TabPane, Select, Static
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer, Grid
from textual.message import Message

from hoopland.cv import mapping_loader

class TendencyRow(Horizontal):
    """A row representing a single tendency with a remove button."""
    DEFAULT_CSS = """
    TendencyRow {
        height: auto;
        margin-bottom: 1;
        align: left middle;
    }
    TendencyRow Label {
        width: 40%;
        padding-top: 1;
    }
    TendencyRow Input {
        width: 30%;
    }
    TendencyRow Button {
        width: 20%;
        margin-left: 2;
        min-width: 4;
    }
    """

    class Remove(Message):
        """Message sent when the remove button is pressed."""
        def __init__(self, key: str) -> None:
            self.key = key
            super().__init__()

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.initial_value = value
        super().__init__()

    def compose(self) -> ComposeResult:
        # Title case the key for display, e.g. "offReb" -> "OffReb"
        yield Label(self.key[0].upper() + self.key[1:])
        yield Input(self.initial_value, id=f"tend_val_{self.key}")
        yield Button("X", variant="error", id=f"btn_remove_{self.key}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"btn_remove_{self.key}":
            event.stop()
            self.post_message(self.Remove(self.key))


class PlayerEditorScreen(ModalScreen):
    """Screen for editing a single player's attributes."""

    CSS = """
    PlayerEditorScreen {
        align: center middle;
    }

    #dialog {
        width: 80%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
    }
    
    TabbedContent {
        height: 1fr;
    }
    
    TabPane {
        padding: 1;
    }

    .label {
        padding-top: 1;
        width: 100%;
    }
    
    .input {
        width: 100%;
        margin-bottom: 1;
    }
    
    Select {
        width: 100%;
        margin-bottom: 1;
    }

    .grid-2 {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
    }

    #buttons {
        dock: bottom;
        height: auto;
        padding: 1;
        align: right bottom;
    }
    
    Button {
        margin-left: 1;
    }
    
    /* Tendency styling */
    #tendency_controls {
        height: auto;
        dock: top;
        padding-bottom: 1;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }
    
    #sel_new_tendency {
        width: 70%;
    }
    
    #btn_add_tendency {
        width: 25%;
        margin-left: 1;
    }

    #tendency_list {
        height: 1fr;
        padding: 1;
    }
    """

    def __init__(self, player_data: dict, on_save=None, **kwargs):
        super().__init__(**kwargs)
        self.player_data = player_data
        self.on_save = on_save
        
        # Helper to safely get value as str
        def get_val(d, k, default="0"):
            return str(d.get(k, default))

        # --- Bio ---
        self.bio = {
            "fn": get_val(player_data, "fn", ""),
            "ln": get_val(player_data, "ln", ""),
            "pos": get_val(player_data, "pos", "1"),
            "ht": get_val(player_data, "ht", "72"),
            "wt": get_val(player_data, "wt", "200"),
            "age": get_val(player_data, "age", "20"),
            "ctry": get_val(player_data, "ctry", "0"),
            "pot": get_val(player_data, "pot", "5"),
            "rating": get_val(player_data, "rating", "5"),
        }

        # --- attributes ---
        attrs = player_data.get("attributes", {})
        self.attributes = {
            "shooting_inside": get_val(attrs, "shooting_inside", "5"),
            "shooting_mid": get_val(attrs, "shooting_mid", "5"),
            "shooting_3pt": get_val(attrs, "shooting_3pt", "5"),
            "defense": get_val(attrs, "defense", "5"),
            "rebounding": get_val(attrs, "rebounding", "5"),
            "passing": get_val(attrs, "passing", "5"),
        }
        
        # --- Appearance ---
        acc = player_data.get("accessories", {})
        self.appearance = {
            "skin": int(get_val(player_data, "appearance", "1")),
            "hair": int(get_val(acc, "hair", "0")),
            "beard": int(get_val(acc, "beard", "0")),
            "accessories": int(get_val(acc, "headAcc", "0")) # Assuming headAcc is primary for now or using first index
        }
        
        # Load options from mapping loader
        # Format: List[Tuple[label, value]]
        self.hair_opts = [(f"#{s['index']} {s['description']}", s['index']) for s in mapping_loader.get_all_styles("hair")]
        self.beard_opts = [(f"#{s['index']} {s['description']}", s['index']) for s in mapping_loader.get_all_styles("facial_hair")]
        # Note: mapping keys are 'accessories' but stored as 'headAcc' often. 
        self.acc_opts = [(f"#{s['index']} {s['description']}", s['index']) for s in mapping_loader.get_all_styles("accessories")]
        
        # Skin tone 1-10 hardcoded for now as it's simple
        self.skin_opts = [(f"Tone {i}", i) for i in range(1, 11)]

        # --- Tendencies ---
        tends = player_data.get("tendencies", {})
        # List of all possible standard tendencies
        self.all_tendency_keys = [
            "threePoint", "twoPoint", "dunk", "post", "hook", "runPlay", 
            "pass", "lob", "offReb", "defReb", "stealOnBall", "stealOffBall", 
            "block", "cross", "pumpFake", "takeCharge", "floater", "fades", 
            "spin", "step"
        ]
        self.current_tendencies = {
            k: get_val(tends, k, "0") for k in tends if k in self.all_tendency_keys or k in tends # Keep existing even if not in standard list
        }

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            with TabbedContent():
                # --- Tab 1: Bio ---
                with TabPane("Bio", id="tab_bio"):
                    with ScrollableContainer():
                        with Grid(classes="grid-2"):
                            with Vertical():
                                yield Label("First Name:", classes="label")
                                yield Input(value=self.bio["fn"], id="inp_fn", classes="input")
                            with Vertical():
                                yield Label("Last Name:", classes="label")
                                yield Input(value=self.bio["ln"], id="inp_ln", classes="input")

                            with Vertical():
                                yield Label("Position (1:PG, 2:SG, 3:SF, 4:PF, 5:C):", classes="label")
                                yield Input(value=self.bio["pos"], id="inp_pos", classes="input")
                            with Vertical():
                                yield Label("Potential (1-10):", classes="label")
                                yield Input(value=self.bio["pot"], id="inp_pot", classes="input")
                            with Vertical():
                                yield Label("Rating (1-5 stars):", classes="label")
                                yield Input(value=self.bio["rating"], id="inp_rating", classes="input")
                            
                            with Vertical():
                                yield Label("Height (inches):", classes="label")
                                yield Input(value=self.bio["ht"], id="inp_ht", classes="input")
                            with Vertical():
                                yield Label("Weight (lbs):", classes="label")
                                yield Input(value=self.bio["wt"], id="inp_wt", classes="input")
                                
                            with Vertical():
                                yield Label("Age:", classes="label")
                                yield Input(value=self.bio["age"], id="inp_age", classes="input")
                            with Vertical():
                                yield Label("Country ID:", classes="label")
                                yield Input(value=self.bio["ctry"], id="inp_ctry", classes="input")

                # --- Tab 2: Attributes ---
                with TabPane("Attributes", id="tab_attrs"):
                    with ScrollableContainer():
                        with Grid(classes="grid-2"):
                            for k, v in self.attributes.items():
                                with Vertical():
                                    yield Label(f"{k.replace('_', ' ').title()} (1-10):", classes="label")
                                    yield Input(value=v, id=f"attr_{k}", classes="input")

                # --- Tab 3: Appearance ---
                with TabPane("Appearance", id="tab_app"):
                     with ScrollableContainer():
                         with Grid(classes="grid-2"):
                             with Vertical():
                                 yield Label("Skin Tone:", classes="label")
                                 yield Select(self.skin_opts, value=self.appearance["skin"], id="app_skin", allow_blank=False)
                             with Vertical():
                                 yield Label("Hair Style:", classes="label")
                                 yield Select(self.hair_opts, value=self.appearance["hair"], id="app_hair", allow_blank=False)
                             with Vertical():
                                 yield Label("Beard Style:", classes="label")
                                 yield Select(self.beard_opts, value=self.appearance["beard"], id="app_beard", allow_blank=False)
                             with Vertical():
                                 yield Label("Head Accessory:", classes="label")
                                 yield Select(self.acc_opts, value=self.appearance["accessories"], id="app_acc", allow_blank=False)

                # --- Tab 4: Tendencies ---
                with TabPane("Tendencies", id="tab_tends"):
                    # Controls to add new tendency
                    with Horizontal(id="tendency_controls"):
                        # Only show options that aren't already present? 
                        # For simplicity, show all, we handle duplicate check on add
                        yield Select(
                            [(k, k) for k in self.all_tendency_keys], 
                            prompt="Select Tendency to Add...", 
                            id="sel_new_tendency"
                        )
                        yield Button("Add", variant="primary", id="btn_add_tendency")
                    
                    # List of existing tendencies
                    with ScrollableContainer(id="tendency_list"):
                        for k, v in self.current_tendencies.items():
                            yield TendencyRow(k, v)

            # --- Footer Buttons ---
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="btn_cancel")
                yield Button("Save Changes", variant="success", id="btn_save")

    def on_tendency_row_remove(self, message: TendencyRow.Remove) -> None:
        # Remove the row from the DOM
        rows = self.query(TendencyRow)
        for row in rows:
            if row.key == message.key:
                row.remove()
                break

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            self._save_changes()
        elif event.button.id == "btn_cancel":
            self.dismiss()
        elif event.button.id == "btn_add_tendency":
            self._add_tendency()

    def _add_tendency(self) -> None:
        sel = self.query_one("#sel_new_tendency", Select)
        if sel.value == Select.BLANK:
            return
            
        key = sel.value
        
        # Check if already exists
        existing_rows = self.query(TendencyRow)
        for row in existing_rows:
            if row.key == key:
                # Already exists, just focus it or ignore
                return

        # Add new row
        list_container = self.query_one("#tendency_list", ScrollableContainer)
        list_container.mount(TendencyRow(key, "0"))
        
        # Reset selection
        sel.clear()

    def _save_changes(self) -> None:
        """Collect inputs and update player data completely."""
        updated = self.player_data.copy()
        
        # --- Bio ---
        updated["fn"] = self.query_one("#inp_fn", Input).value
        updated["ln"] = self.query_one("#inp_ln", Input).value
        
        for k in ["pos", "ht", "wt", "age", "ctry", "pot", "rating"]:
            try:
                val = self.query_one(f"#inp_{k}", Input).value
                updated[k] = int(val)
            except ValueError:
                pass

        # --- Attributes ---
        new_attrs = updated.get("attributes", {}).copy()
        for k in self.attributes.keys():
            try:
                val = self.query_one(f"#attr_{k}", Input).value
                new_attrs[k] = int(val)
            except ValueError:
                pass
        updated["attributes"] = new_attrs

        # --- Appearance ---
        # Select widgets return value as the type provided in options (int)
        val = self.query_one("#app_skin", Select).value
        if val != Select.BLANK:
             updated["appearance"] = val
            
        new_acc = updated.get("accessories", {}).copy()
        
        val = self.query_one("#app_hair", Select).value
        if val != Select.BLANK:
            new_acc["hair"] = val
            
        val = self.query_one("#app_beard", Select).value
        if val != Select.BLANK:
            new_acc["beard"] = val
            
        val = self.query_one("#app_acc", Select).value
        if val != Select.BLANK:
            new_acc["headAcc"] = val # using headAcc as primary accessory key based on inspection
            
        updated["accessories"] = new_acc

        # --- Tendencies ---
        new_tends = {}
        rows = self.query(TendencyRow)
        for row in rows:
            try:
                inp = row.query_one(f"#tend_val_{row.key}", Input)
                new_tends[row.key] = int(inp.value)
            except ValueError:
                pass # Skip invalid inputs
        
        updated["tendencies"] = new_tends

        if self.on_save:
            self.on_save(updated)
            
        self.dismiss(updated)

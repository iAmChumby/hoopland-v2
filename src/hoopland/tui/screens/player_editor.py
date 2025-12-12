
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TabbedContent, TabPane, Header, Footer
from textual.containers import Container, Vertical, Horizontal, Grid, ScrollableContainer
from dataclasses import dataclass

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
    
    .grid-2 {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
    }

    .grid-3 {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
    }
    
    .grid-4 {
        layout: grid;
        grid-size: 4;
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
    .tendency-item {
        height: auto;
        margin-bottom: 1;
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
            "skin": get_val(player_data, "appearance", "1"),
            "hair": get_val(acc, "hair", "0"),
            "beard": get_val(acc, "beard", "0"),
        }

        # --- Tendencies ---
        tends = player_data.get("tendencies", {})
        # List of all standard tendencies
        self.tendency_keys = [
            "threePoint", "twoPoint", "dunk", "post", "hook", "runPlay", 
            "pass", "lob", "offReb", "defReb", "stealOnBall", "stealOffBall", 
            "block", "cross", "pumpFake", "takeCharge", "floater", "fades", 
            "spin", "step"
        ]
        self.tendencies = {
            k: get_val(tends, k, "0") for k in self.tendency_keys
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
                                 yield Label("Skin Tone ID:", classes="label")
                                 yield Input(value=self.appearance["skin"], id="app_skin", classes="input")
                             with Vertical():
                                 yield Label("Hair Style ID:", classes="label")
                                 yield Input(value=self.appearance["hair"], id="app_hair", classes="input")
                             with Vertical():
                                 yield Label("Beard Style ID:", classes="label")
                                 yield Input(value=self.appearance["beard"], id="app_beard", classes="input")

                # --- Tab 4: Tendencies ---
                with TabPane("Tendencies", id="tab_tends"):
                    with ScrollableContainer():
                        with Grid(classes="grid-4"):
                            for k in self.tendency_keys:
                                val = self.tendencies.get(k, "0")
                                with Vertical(classes="tendency-item"):
                                    yield Label(k.title(), classes="label")
                                    yield Input(value=val, id=f"tend_{k}", classes="input")

            # --- Footer Buttons ---
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="btn_cancel")
                yield Button("Save Changes", variant="success", id="btn_save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            self._save_changes()
        elif event.button.id == "btn_cancel":
            self.dismiss()

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
        try:
            skin_val = self.query_one("#app_skin", Input).value
            updated["appearance"] = int(skin_val)
        except ValueError:
            pass
            
        new_acc = updated.get("accessories", {}).copy()
        try:
            hair_val = self.query_one("#app_hair", Input).value
            new_acc["hair"] = int(hair_val)
        except ValueError:
            pass
        try:
            beard_val = self.query_one("#app_beard", Input).value
            new_acc["beard"] = int(beard_val)
        except ValueError:
            pass
        updated["accessories"] = new_acc

        # --- Tendencies ---
        new_tends = updated.get("tendencies", {}).copy()
        for k in self.tendency_keys:
            try:
                val = self.query_one(f"#tend_{k}", Input).value
                new_tends[k] = int(val)
            except ValueError:
                pass
        updated["tendencies"] = new_tends

        if self.on_save:
            self.on_save(updated)
            
        self.dismiss(updated)

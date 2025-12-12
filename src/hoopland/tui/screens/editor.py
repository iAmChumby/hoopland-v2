from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Button, Static, Label, 
    DataTable, OptionList, Input
)
from .player_editor import PlayerEditorScreen
from .modals import TeamSelectModal, ConfirmationModal
from textual.widgets.option_list import Option
from textual.containers import Container, Vertical, Horizontal
from pathlib import Path
import json
import os
import copy


class EditorScreen(Screen):
    """Screen for viewing and editing generated league/draft files."""
    
    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+s", "save", "Save"),
    ]

    CSS = """
    EditorScreen {
        height: 100%;
        align: center middle;
    }
    .main_menu_container {
        width: 100%;
        height: 100%;
        border: thick $background 80%;
        background: $surface;
    }
    .editor-layout {
        width: 100%;
        height: 100%;
    }
    .editor-sidebar {
        width: 30%;
        height: 100%;
        padding-right: 1;
    }
    .editor-main {
        width: 70%;
        height: 100%;
        padding-left: 1;
    }
    .section-header {
        text-style: bold;
        padding-top: 1;
    }
    #file_list {
        height: 10;
        border: solid $primary;
    }
    #team_list {
        height: 1fr;
        border: solid $accent;
    }
    .player-table {
        height: 1fr;
        border: solid $primary;
    }
    #btn_sort_teams {
        width: 100%;
        margin-bottom: 1;
    }
    .roster-controls {
        height: auto;
        padding-top: 1;
        padding-bottom: 1;
    }
    .roster-controls Button {
        width: 1fr;
        margin-right: 1;
    }
    """

    def __init__(self, file_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.data = None
        self.current_team_idx = 0
        self.selected_player_idx = -1
        self.modified = False
        self.sort_reverse = False
        self.last_sort_col = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("League/Draft Editor", classes="title"),
            Horizontal(
                # Left Panel: File selector and team list
                Vertical(
                    Label("Select File:", classes="section-header"),
                    OptionList(id="file_list", classes="file-list"),
                    Label("Teams:", classes="section-header"),
                    Label("Teams:", classes="section-header"),
                    Button("Sort A-Z", id="btn_sort_teams", variant="default"),

                    OptionList(id="team_list", classes="team-list"),
                    classes="editor-sidebar",
                ),
                # Right Panel: Player table
                Vertical(
                    Label("Players", id="team_name_label", classes="section-header"),
                    DataTable(id="player_table", classes="player-table"),
                    Horizontal(
                        Button("Add Player", id="btn_add_player", variant="success"),
                        Button("Edit Player", id="btn_edit_player", variant="default", disabled=True),
                        Button("Move Player", id="btn_move_player", variant="primary", disabled=True),
                        Button("Delete Player", id="btn_del_player", variant="error", disabled=True),
                        classes="roster-controls"
                    ),
                    Horizontal(
                        Button("💾 Save Changes", id="btn_save", variant="success"),
                        Button("Back", id="btn_back", variant="primary"),
                        classes="editor-buttons",
                    ),
                    classes="editor-main",
                ),
                classes="editor-layout",
            ),
            classes="main_menu_container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the editor."""
        self._load_file_list()
        
        # Setup player table columns
        table = self.query_one("#player_table", DataTable)
        cols = ["Name", "Pos", "Age", "Ht", "Wt", "Pot", "Skin", "Hair", "Beard"]
        for col in cols:
            table.add_column(col, key=col)
        table.cursor_type = "row"
        
        # If file_path was provided, load it
        if self.file_path and os.path.exists(self.file_path):
            self._load_file(self.file_path)

    def _load_file_list(self) -> None:
        """Load list of available files from output directory."""
        file_list = self.query_one("#file_list", OptionList)
        file_list.clear_options()
        
        output_dir = Path("output")
        if not output_dir.exists():
            file_list.add_option(Option("No files found", id="empty"))
            return
        
        files = []
        for year_dir in output_dir.iterdir():
            if year_dir.is_dir():
                for f in year_dir.glob("*.txt"):
                    files.append({
                        "path": str(f),
                        "name": f"{year_dir.name}/{f.name}"
                    })
        
        files.sort(key=lambda x: x["name"], reverse=True)
        
        for f in files:
            file_list.add_option(Option(f["name"], id=f["path"]))
        
        if not files:
            file_list.add_option(Option("No files found", id="empty"))

    def _load_file(self, path: str) -> None:
        """Load a JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.file_path = path
            self.file_path = path
            self._populate_teams()
            self.notify(f"Loaded: {Path(path).name}")
            # Auto-focus the team list so user can scroll immediately
            self.set_focus(self.query_one("#team_list"))
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def _populate_teams(self) -> None:
        """Populate team list from loaded data."""
        team_list = self.query_one("#team_list", OptionList)
        team_list.clear_options()
        
        if not self.data or "teams" not in self.data:
            return
        
        for i, team in enumerate(self.data["teams"]):
            name = team.get("name", f"Team {i}")
            city = team.get("city", "")
            label = f"{city} {name}".strip() if city else name
            team_list.add_option(Option(label, id=str(i)))
        
        # Select first team
        if self.data["teams"]:
            self._show_team(0)

    def _show_team(self, idx: int) -> None:
        if not self.data or idx >= len(self.data["teams"]):
            return
        
        self.current_team_idx = idx
        self.selected_player_idx = -1
        self._update_button_states()
        team = self.data["teams"][idx]
        
        # Update header
        name_label = self.query_one("#team_name_label", Label)
        city = team.get("city", "")
        name = team.get("name", "Team")
        name_label.update(f"{city} {name}".strip())
        
        # Populate player table
        table = self.query_one("#player_table", DataTable)
        table.clear()
        
        roster = team.get("roster", [])
        for p in roster:
            fn = p.get("fn", "")
            ln = p.get("ln", "")
            name = f"{fn} {ln}".strip()
            
            pos = str(p.get("pos", "?"))
            age = str(p.get("age", "?"))
            ht = str(p.get("ht", "?"))
            wt = str(p.get("wt", "?"))
            pot = str(p.get("pot", "?"))
            
            # Appearance data
            skin = str(p.get("appearance", "?"))
            acc = p.get("accessories", {})
            hair = str(acc.get("hair", "?"))
            beard = str(acc.get("beard", "?"))
            
            table.add_row(name, pos, age, ht, wt, pot, skin, hair, beard, key=str(p.get("id", "")))

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle click on table header to sort players."""
        if not self.data:
            return

        col_key = event.column_key.value
        # If clicking same column, toggle reverse. Else default to Ascending.
        if self.last_sort_col == col_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.last_sort_col = col_key

        team = self.data["teams"][self.current_team_idx]
        roster = team.get("roster", [])

        # Helper to safely get value for sorting
        def get_sort_key(p):
            if col_key == "Name":
                return f"{p.get('fn', '')} {p.get('ln', '')}"
            elif col_key == "Pos":
                return p.get("pos", 0)
            elif col_key == "Age":
                return p.get("age", 0)
            elif col_key == "Ht":
                return p.get("ht", 0)
            elif col_key == "Wt":
                return p.get("wt", 0)
            elif col_key == "Pot":
                return p.get("pot", 0)
            elif col_key == "Skin":
                return p.get("appearance", 0)
            elif col_key == "Hair":
                return p.get("accessories", {}).get("hair", 0)
            elif col_key == "Beard":
                return p.get("accessories", {}).get("facial_hair", 0)
            return 0

        # Sort in-place
        roster.sort(key=get_sort_key, reverse=self.sort_reverse)
        
        # Refresh table
        self._show_team(self.current_team_idx)
        self.notify(f"Sorted by {col_key} ({'DESC' if self.sort_reverse else 'ASC'})")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection in option lists."""
        option_list = event.option_list
        
        if option_list.id == "file_list":
            path = str(event.option.id)
            if path != "empty" and os.path.exists(path):
                self._load_file(path)
        elif option_list.id == "team_list":
            try:
                idx = int(event.option.id)
                self._show_team(idx)
            except ValueError:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        row_key = event.row_key.value
        try:
            player_id = int(row_key)
        except ValueError:
            return

        team = self.data["teams"][self.current_team_idx]
        for i, p in enumerate(team.get("roster", [])):
            if p.get("id") == player_id:
                self.selected_player_idx = i
                self._update_button_states()
                break

    def _update_player(self, player_idx: int, new_data: dict) -> None:
        """Callback to update player data after editing."""
        if not self.data or self.current_team_idx >= len(self.data["teams"]):
            return
            
        team = self.data["teams"][self.current_team_idx]
        if player_idx < 0 or player_idx >= len(team.get("roster", [])):
            return
            
        # Update data in memory
        team["roster"][player_idx] = new_data
        self.modified = True
        
        # Refresh UI
        self._show_team(self.current_team_idx)
        self.notify(f"Updated {new_data.get('fn')} {new_data.get('ln')}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back":
            self.app.pop_screen()
        elif event.button.id == "btn_save":
            self._save_file()
        elif event.button.id == "btn_sort_teams":
            if self.data and "teams" in self.data:
                self.data["teams"].sort(key=lambda x: f"{x.get('city', '')} {x.get('name', '')}".strip())
                self._populate_teams()
                self.notify("Teams sorted A-Z")
        elif event.button.id == "btn_add_player":
            self._on_add_player()
        elif event.button.id == "btn_edit_player":
            self._on_edit_player()
        elif event.button.id == "btn_move_player":
            self._on_move_player()
        elif event.button.id == "btn_del_player":
            self._on_delete_player()

    def _update_button_states(self) -> None:
        """Enable/disable buttons based on selection."""
        has_sel = self.selected_player_idx >= 0
        self.query_one("#btn_edit_player", Button).disabled = not has_sel
        self.query_one("#btn_move_player", Button).disabled = not has_sel
        self.query_one("#btn_del_player", Button).disabled = not has_sel
        
        # Add is always enabled if a team is selected
        self.query_one("#btn_add_player", Button).disabled = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        row_key = event.row_key.value
        try:
            player_id = int(row_key)
        except ValueError:
            return

        team = self.data["teams"][self.current_team_idx]
        for i, p in enumerate(team.get("roster", [])):
            if p.get("id") == player_id:
                self.selected_player_idx = i
                self._update_button_states()
                break

    def _on_add_player(self):
        """Create a new player."""
        # Template for new player
        new_player = {
            "id": int(os.urandom(4).hex(), 16), # Random ID
            "fn": "New",
            "ln": "Player",
            "pos": "1",
            "age": "20",
            "ht": "78",
            "wt": "200",
            "pot": "5",
            "appearance": "1",
            "accessories": {"hair": "0", "beard": "0", "headAcc": "0"},
            "attributes": {},
            "tendencies": {}
        }
        
        def on_save(data):
            if not self.data: return
            team = self.data["teams"][self.current_team_idx]
            if "roster" not in team:
                team["roster"] = []
            team["roster"].append(data)
            self.modified = True
            self._show_team(self.current_team_idx)
            self.notify("Player added")

        self.app.push_screen(PlayerEditorScreen(new_player, on_save=on_save))

    def _on_edit_player(self):
        """Edit selected player."""
        if self.selected_player_idx < 0: return
        
        team = self.data["teams"][self.current_team_idx]
        player = team["roster"][self.selected_player_idx]
        
        self.app.push_screen(PlayerEditorScreen(
            player_data=player,
            on_save=lambda data: self._update_player(self.selected_player_idx, data)
        ))

    def _on_delete_player(self):
        """Delete selected player."""
        if self.selected_player_idx < 0: return

        def do_delete():
            team = self.data["teams"][self.current_team_idx]
            player = team["roster"].pop(self.selected_player_idx)
            self.modified = True
            
            # Reset selection
            self.selected_player_idx = -1
            self._update_button_states()
            
            self._show_team(self.current_team_idx)
            self.notify(f"Deleted {player.get('fn')} {player.get('ln')}")

        self.app.push_screen(ConfirmationModal("Are you sure you want to delete this player?", do_delete))

    def _on_move_player(self):
        """Move selected player to another team."""
        if self.selected_player_idx < 0: return
        
        def do_move(target_team_idx):
            if target_team_idx == self.current_team_idx: return
            
            # Remove from current
            source_team = self.data["teams"][self.current_team_idx]
            player = source_team["roster"].pop(self.selected_player_idx)
            
            # Add to target
            target_team = self.data["teams"][target_team_idx]
            if "roster" not in target_team:
                target_team["roster"] = []
            target_team["roster"].append(player)
            
            self.modified = True
            self.selected_player_idx = -1
            self._update_button_states()
            self._show_team(self.current_team_idx)
            
            target_name = target_team.get("name", "Target Team")
            self.notify(f"Moved player to {target_name}")

        self.app.push_screen(TeamSelectModal(
            teams=self.data["teams"],
            current_team_idx=self.current_team_idx,
            on_select=do_move
        ))
        
    def _save_file(self) -> None:
        """Save changes back to file."""
        if not self.file_path or not self.data:
            self.notify("No file loaded", severity="error")
            return
        
        try:
            from ...blocks.formatter import save_compact_json
            save_compact_json(self.data, self.file_path)
            self.modified = False
            self.notify(f"Saved: {Path(self.file_path).name}", severity="information")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def action_go_back(self) -> None:
        """Handle escape key."""
        self.app.pop_screen()

    def action_save(self) -> None:
        """Handle Ctrl+S."""
        self._save_file()

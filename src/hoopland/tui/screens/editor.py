from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Button, Static, Label, 
    DataTable, OptionList, Input
)
from textual.widgets.option_list import Option
from textual.containers import Container, Vertical, Horizontal
from pathlib import Path
import json
import os


class EditorScreen(Screen):
    """Screen for viewing and editing generated league/draft files."""
    
    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, file_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.data = None
        self.current_team_idx = 0
        self.modified = False

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
                    OptionList(id="team_list", classes="team-list"),
                    classes="editor-sidebar",
                ),
                # Right Panel: Player table
                Vertical(
                    Label("Players", id="team_name_label", classes="section-header"),
                    DataTable(id="player_table", classes="player-table"),
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
        table.add_columns("Name", "Pos", "Age", "Ht", "Wt", "Pot", "Skin", "Hair", "Beard")
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
            self._populate_teams()
            self.notify(f"Loaded: {Path(path).name}")
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
        """Display players for a team."""
        if not self.data or idx >= len(self.data["teams"]):
            return
        
        self.current_team_idx = idx
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back":
            self.app.pop_screen()
        elif event.button.id == "btn_save":
            self._save_file()

    def _save_file(self) -> None:
        """Save changes back to file."""
        if not self.file_path or not self.data:
            self.notify("No file loaded", severity="error")
            return
        
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
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

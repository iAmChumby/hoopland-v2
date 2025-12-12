from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Label, ListView, ListItem
from textual.containers import Container, Vertical, Horizontal
import os
from pathlib import Path


class MainMenu(Screen):
    """The main menu screen with actions and recent runs."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Hoopland V2 Generator", classes="title"),
            Horizontal(
                # Left Panel: Actions
                Vertical(
                    Label("Generate", classes="section-header"),
                    Button("🏀 NBA League", id="btn_league", variant="primary"),
                    Button("🎓 NCAA League", id="btn_ncaa", variant="primary"),
                    Button("📋 Draft Class", id="btn_draft", variant="primary"),
                    Label("", classes="spacer"),
                    Label("Tools", classes="section-header"),
                    Button("📝 Edit Files", id="btn_editor", variant="default"),
                    Label("", classes="spacer"),
                    Button("Exit", id="btn_exit", variant="error"),
                    classes="home-actions",
                ),
                # Right Panel: Recent Runs
                Vertical(
                    Label("Recent Generations", classes="section-header"),
                    ListView(id="recent_runs", classes="recent-list"),
                    Button("🔄 Refresh", id="btn_refresh", variant="default"),
                    classes="home-recent",
                ),
                classes="home-layout",
            ),
            classes="main_menu_container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load recent runs when screen mounts."""
        await self._load_recent_runs()

    async def _load_recent_runs(self) -> None:
        """Scan output directory for recent generations."""
        list_view = self.query_one("#recent_runs", ListView)
        await list_view.clear()
        
        output_dir = Path("output")
        if not output_dir.exists():
            await list_view.append(ListItem(Label("No generations yet"), id="empty"))
            return
        
        # Find all .txt files (generated leagues/drafts)
        files = []
        for year_dir in output_dir.iterdir():
            if year_dir.is_dir():
        for year_dir in output_dir.iterdir():
            if year_dir.is_dir():
                for f in year_dir.glob("*.txt"):
                    stat = f.stat()
                    files.append({
                        "path": str(f),
                        "name": f.name,
                        "year": year_dir.name,
                        "mtime": stat.st_mtime
                    })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["mtime"], reverse=True)
        
        # Show last 10
        for f in files[:10]:
            # Determine type from filename
            if "Draft" in f["name"]:
                icon = "📋"
                file_type = "Draft"
            elif "NCAA" in f["name"]:
                icon = "🎓"
                file_type = "NCAA"
            else:
                icon = "🏀"
                file_type = "League"
            
            label = f"{icon} {f['year']} {file_type}"
            # Sanitize ID - Textual IDs can't have dots or spaces
            # Include year to avoid collisions if same filename exists in different years
            safe_id = f"{f['year']}_{f['name']}".replace('.', '_').replace(' ', '_')
            item = ListItem(Label(label), id=f"file_{safe_id}")
            item.data = f["path"]  # Store path for later
            await list_view.append(item)
        
        if not files:
            await list_view.append(ListItem(Label("No generations yet"), id="empty"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_league":
            self.app.push_screen("league_config")
        elif event.button.id == "btn_ncaa":
            self.app.push_screen("ncaa_config")
        elif event.button.id == "btn_draft":
            self.app.push_screen("draft_config")
        elif event.button.id == "btn_editor":
            self.app.push_screen("editor")
        elif event.button.id == "btn_refresh":
            await self._load_recent_runs()
            self.notify("Refreshed recent runs")
        elif event.button.id == "btn_exit":
            self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle clicking a recent run to open in editor."""
        item = event.item
        if hasattr(item, "data") and item.data:
            # Push editor screen with file path
            self.app.push_screen("editor", {"file_path": item.data})

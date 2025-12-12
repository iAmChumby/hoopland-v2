from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList
from textual.containers import Container, Vertical, Horizontal
from textual.widgets.option_list import Option

class TeamSelectModal(ModalScreen):
    """Modal to select a target team."""
    
    CSS = """
    TeamSelectModal {
        align: center middle;
    }
    #dialog {
        width: 50%;
        height: 60%;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }
    .title {
        width: 100%;
        text-align: center;
        padding-bottom: 1;
    }
    #team_options {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }
    #buttons {
        height: auto;
        align: center bottom;
    }
    """

    def __init__(self, teams: list, current_team_idx: int, on_select):
        super().__init__()
        self.teams = teams
        self.current_team_idx = current_team_idx
        self.on_select = on_select

    def compose(self):
        yield Container(
            Label("Select Target Team", classes="title"),
            OptionList(id="team_options"),
            Horizontal(
                Button("Cancel", variant="error", id="btn_cancel"),
                id="buttons"
            ),
            id="dialog"
        )

    def on_mount(self):
        opts = self.query_one("#team_options", OptionList)
        for i, team in enumerate(self.teams):
            if i == self.current_team_idx:
                continue
            name = f"{team.get('city', '')} {team.get('name', '')}".strip()
            opts.add_option(Option(name, id=str(i)))

    def on_option_list_option_selected(self, event):
        idx = int(event.option.id)
        self.dismiss()
        self.on_select(idx)

    def on_button_pressed(self, event):
        if event.button.id == "btn_cancel":
            self.dismiss()


class ConfirmationModal(ModalScreen):
    """Modal to confirm an action."""
    
    CSS = """
    ConfirmationModal {
        align: center middle;
    }
    #confirm_dialog {
        width: 40%;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 2;
    }
    .message {
        width: 100%;
        text-align: center;
        padding-bottom: 2;
    }
    #confirm_buttons {
        width: 100%;
        align: center bottom;
    }
    Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str, on_confirm):
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm

    def compose(self):
        yield Container(
            Label(self.message, classes="message"),
            Horizontal(
                Button("Yes", variant="success", id="btn_yes"),
                Button("No", variant="error", id="btn_no"),
                id="confirm_buttons"
            ),
            id="confirm_dialog"
        )

    def on_button_pressed(self, event):
        if event.button.id == "btn_yes":
            self.dismiss()
            self.on_confirm()
        else:
            self.dismiss()

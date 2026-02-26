"""
app.py

Implements the `Textual` application, including layout, key bindings, styling, and startup behavior.
"""
from textual.binding import Binding
from textual.containers import Vertical
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, RichLog



class EnteliscriptTUI(App):
    """
    Enteliscript - Tools for Delta Controls & enteliWEB.
    """
    TITLE = "enteliscript TUI"
    SUB_TITLE = "v0.1"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    /* Header {
        background: #1e1e2e;
        color: #cdd6f4;
    } */

    /* HeaderTitle {
        text-style: italic;
        color: #89b4fa;
    } */

    #log {
        height: 1fr;
        border: round $surface;
        padding: 1;
        scrollbar-visibility: hidden;
    }

    #cmd {
        height: 3;
        border: round $surface;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RichLog(id="log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Type a command (e.g. help) ...", id="cmd")

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self.query_one(RichLog).write("[b]enteliscript[/b] is currently under development.\n")

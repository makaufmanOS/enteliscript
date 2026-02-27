"""
# enteliscript.tui.app

Implements the `TUI` class, the top-level Textual application for `enteliscript`.
Defines the app layout (header, scrollable log, command input), key bindings, and 
the full command submission pipeline: tokenizing raw input, dispatching to registered 
command handlers, running blocking commands off the main thread, and handling special 
post-command actions such as clearing the log or launching the site selection modal screen.
"""
import shlex
import asyncio
from pathlib import Path
from textual.binding import Binding
from textual.containers import Vertical
from .cmd.handler import CommandHandler
from ..enteliweb.api import EnteliwebAPI
from textual.app import App, ComposeResult
from .widgets import BlockableInput, SiteSelector
from textual.widgets import Header, RichLog, Input



class TUI(App):
    """
    The main `Textual` application for `enteliscript`.

    Manages the application layout, key bindings, and command dispatch loop.
    Renders a `RichLog` for output and a `BlockableInput` for command entry.
    Commands are parsed and routed to handler methods registered in `CommandHandler`.

    ## Bindings
    - `Ctrl+C` – Quit the application.
    """
    TITLE = "enteliscript TUI"
    SUB_TITLE = "v0.1"
    CSS_PATH = Path(__file__).parent / "style.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, enteliweb: EnteliwebAPI) -> None:
        """
        Initializes the TUI application and command dispatch table.

        Creates a `CommandHandler` instance and builds a lookup mapping of  
        command names/aliases to bound handler methods for runtime dispatch.

        ## Parameters
        - `enteliweb` ( *EnteliwebAPI* ) – Instance of the `EnteliwebAPI` client.
        """
        super().__init__()
        self.handler = CommandHandler(enteliweb)
        self.dispatch = self.handler.get_dispatch()
        self._input_placeholder = "Type a command (e.g. help) ..."

    
    def _log(self, text: str) -> None:
        """
        Appends a message to the `RichLog` output widget.

        ## Parameters
        - `text` ( *string* ) – Markup-capable message text to write to the log.
        """
        log = self.query_one(RichLog)
        log.write(text)


    def _clear_log(self) -> None:
        """
        Clears all content from the `RichLog` output widget.
        """
        self.query_one(RichLog).clear()


    def _show_site_selector(self, sites: list[str]) -> None:
        """
        Pushes the `SiteSelector` modal screen onto the screen stack.

        On dismissal, `_on_site_selected` is called with the result.

        ## Parameters
        - `sites` ( *list[string]* ) – The list of site names to display in the selector.
        """
        self.push_screen(SiteSelector(sites), callback=self._on_site_selected)


    def _on_site_selected(self, site: str | None) -> None:
        """
        Callback invoked when the `SiteSelector` modal is dismissed.

        Sets the active site on the handler and logs the result,
        or logs a cancellation message if no site was selected.
        Refocuses the command input after the modal closes.

        ## Parameters
        - `site` ( *string*, *optional* ) – The selected site name, or `None` if the user cancelled.
        """
        if site is None:
            self._log("[yellow]Site selection cancelled.[/yellow]\n")
        else:
            self.handler.sitename = site
            self._log(f"[green]Active site set to:[/green] [bold]{site}[/bold]\n")
        self.query_one(BlockableInput).focus()


    def compose(self) -> ComposeResult:
        """
        Builds the application layout.

        ## Yields
        - A `Header` widget.
        - A `RichLog` widget for displaying command output.
        - A `BlockableInput` widget for accepting command input.
        """
        yield Header()
        with Vertical():
            yield RichLog(id="log", wrap=True, highlight=True, markup=True)
            yield BlockableInput(placeholder=self._input_placeholder, id="cmd")
    

    def on_mount(self) -> None:
        """
        Focuses the command input and displays the welcome message on startup.
        """
        flow = [
            "[b]Logical flow:[/b]\n",
            "  → [cyan]setlogin[/cyan] [i](if first run)[/i]\n",
            "  → [cyan]login[/cyan] [i](to authenticate enteliWEB session)[/i]\n",
            "  → [cyan]setsite[/cyan] [i](to direct commands to a specific site)[/i]\n",
            "  → [i]other commands[/i]\n",
        ]
        self.query_one(BlockableInput).focus()
        self._log("".join(flow))
        self._log("Type [i]help[/i] to list commands and their usage.\n\n")
        

    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handles command submission from the `BlockableInput` widget.

        ## Processing Flow
            1. Strip and validate the raw input; ignore empty submissions.
            2. Push the command to the input history buffer.
            3. Echo the command to the log.
            4. Tokenize the input using `shlex.split` to support quoted arguments.
            5. Resolve shorthand help syntax — `<command>?` is treated as `help <command>`.
            6. Look up the command in the dispatch table.
            7. Coerce arguments to the types declared in the `CommandSpec`.
            8. Run blocking commands in a thread via `asyncio.to_thread`, showing a spinner.
            9. Handle special result actions: `clear_log` and `select_site`.
            10. Log success or error output from the command result.

        ## Parameters
        - `event` ( *Input.Submitted* ) – The Textual event carrying the submitted input text.
        """
        raw = event.value.strip()

        if not raw:
            event.input.value = ""
            return
        
        self.query_one(BlockableInput).push_history(raw)
        self._log(f"[cyan]>[/cyan] {raw}")

        try:
            parts: list[str] = shlex.split(raw)
        except ValueError as e:
            self._log(f"[red]Parse error:[/red] {e}\n")
            return
        
        if len(parts) == 1 and parts[0].endswith("?") and len(parts[0]) > 1:
            target = parts[0][:-1].lower()
            help_function = self.dispatch.get("help")
            if help_function is None:
                self._log("[red]Help command not available.[/red]\n")
                return
            result = help_function(target)
            if result.message:
                if result.ok:
                    self._log(f"{result.message}\n")
                else:
                    self._log(f"[red]{result.message}[/red]\n")
            return

        cmd, *args = parts
        function = self.dispatch.get(cmd.lower())
        if function is None:
            self._log(f"[red]Unknown command:[/red] {cmd!r} (try 'help')\n")
            return
        
        spec = getattr(function, "_command_spec", None)
        is_blocking = spec.blocking if spec else False

        if spec and spec.params:
            try:
                args = [t(v) for t, v in zip(spec.params, args)] + list(args[len(spec.params):])
            except (ValueError, TypeError) as e:
                self._log(f"[red]Argument error:[/red] {e}\n")
                return

        try:
            if is_blocking:
                self.query_one(BlockableInput).block(spec.blocking_msg)
                try:
                    result = await asyncio.to_thread(function, *args)
                finally:
                    self.query_one(BlockableInput).unblock()
            else:
                event.input.value = ""
                result = function(*args)

        except TypeError as e:
            self._log(f"[red]Usage error:[/red] {e}\n")
            return
        except Exception as e:
            self._log(f"[red]Command crashed:[/red] {type(e).__name__}: {e}\n")
            return
        
        if result.action == "clear_log":
            self._clear_log()
        elif result.action == "select_site":
            if result.message:
                self._log(f"{result.message}")
            self._show_site_selector(result.data)
            return

        if result.message:
            if result.ok:
                self._log(f"{result.message}\n")
            else:
                self._log(f"[red]{result.message}[/red]\n")

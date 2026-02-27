"""
# enteliscript.tui.widgets

Defines custom Textual widgets used by the `enteliscript` TUI.

`BlockableInput` – A subclass of `Input` that can be locked during blocking
operations. Suppresses text insertion, hides the cursor, and displays a spinner
animation while a background command is running. Also implements command history
navigation via the Up/Down arrow keys and input clearing via Escape.

`SiteSelector` – A modal `OptionList` screen that presents a list of enteliWEB
site names and returns the selection (or `None` on cancel) to the caller via `dismiss`.
"""
from textual.events import Key
from textual.widgets import Input
from textual.binding import Binding
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option



class BlockableInput(Input):
    """
    A subclass of `Input` that can be locked during blocking operations.

    Prevents text insertion and hides the cursor while in the *busy* state,
    ensuring the user cannot interact with the input field while a blocking
    command is running. Includes a built-in spinner animation for visual feedback.

    ## States
    - **Normal** – Accepts user input and displays the cursor as usual.
    - **Busy** – Suppresses input, hides the cursor, and animates a spinner in the placeholder.

    ## CSS Classes
    - `busy` – Applied while the widget is in the busy state. Used to suppress input
      and can be targeted for custom styling.
    """
    _SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the `BlockableInput` with history tracking and spinner state.

        ## Parameters
        - Accepts all positional and keyword arguments from `Input`.

        ## Keyword Arguments
        - `placeholder` ( *string*, *optional* ) – The placeholder text shown when the input is empty. Defaults to `"Type a command (e.g. help) ..."`.
        """
        # kwargs.setdefault("placeholder", "Type a command (e.g. help) ...")    # TODO: Review
        # self._default_placeholder: str = kwargs["placeholder"]                # TODO: Review
        
        super().__init__(*args, **kwargs)
        self._history: list[str] = []
        self._history_index: int = -1
        self._history_draft: str = ""   # preserves in-progress text when browsing history

        self._default_placeholder: str = kwargs.get("placeholder", "Type a command (e.g. help) ...")
        self._spinner_frame: int = 0
        self._spinner_label: str = ""
        self._spinner_timer = None


    def push_history(self, command: str) -> None:
        """
        Adds a command string to the history buffer.

        Duplicate consecutive entries are ignored.

        ## Parameters
        - `command` ( *string* ) – The raw command string to record.
        """
        if not command:
            return
        if not self._history or self._history[-1] != command:
            self._history.append(command)
        self._history_index = -1
        self._history_draft = ""


    def insert_text_at_cursor(self, text: str) -> None:
        """
        Inserts text at the current cursor position, unless the input is busy.

        Overrides the base implementation to suppress all text insertion
        while the widget has the `busy` CSS class applied.

        ## Parameters
        - `text` ( *string* ) – Text to insert at the current cursor position.
        """
        if not self.has_class("busy"):
            super().insert_text_at_cursor(text)


    def block(self, label: str = "Working") -> None:
        """
        Enters the busy state, preventing input and hiding the cursor.

        Clears the input value, applies the `busy` CSS class, disables cursor blinking,
        and starts the spinner animation in the placeholder.

        ## Parameters
        - `label` ( *string*, *optional* ) – The label to display alongside the spinner. Defaults to `"Working"`.
        """
        self._spinner_frame = 0
        self._spinner_label = label

        # Set placeholder BEFORE clearing value so no frame shows the default
        frame = self._SPINNER_FRAMES[0]
        self.placeholder = f"{frame} {label}"
        self.value = ""

        self.add_class("busy")
        self.cursor_blink = False
        self._cursor_visible = False

        self._spinner_timer = self.set_interval(1 / 12, self._tick_spinner)


    def _tick_spinner(self) -> None:
        """
        Advances the spinner animation by one frame.

        Called automatically on a fixed interval while the widget is in the busy state.
        Updates the placeholder text with the next spinner frame.
        """
        frame = self._SPINNER_FRAMES[self._spinner_frame % len(self._SPINNER_FRAMES)]
        self.placeholder = f"{frame} {self._spinner_label}"
        self._spinner_frame += 1


    def unblock(self) -> None:
        """
        Exits the busy state and restores normal input behavior.

        Stops the spinner timer, re-enables cursor blinking and visibility, then defers
        final cleanup via `call_after_refresh` to ensure any key events queued during
        the blocking operation are flushed before the widget accepts new input.
        """
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None
        
        self.cursor_blink = True
        self._cursor_visible = True
        self.call_after_refresh(self._finish_unblock)


    def _finish_unblock(self) -> None:
        """
        Completes the unblock sequence after a deferred refresh.

        Clears the input value, restores the default placeholder, and removes the `busy`
        CSS class. Should only be called via `call_after_refresh` from `unblock`.
        """
        self.value = ""
        self.placeholder = self._default_placeholder
        self.remove_class("busy")


    def on_key(self, event: Key) -> None:
        """
        Handles key events for command history navigation and input clearing.

        - `Escape` – Clears the input and resets history navigation state.
        - `Up Arrow` – Navigates backward through command history, loading previous commands into the input field.
        - `Down Arrow` – Navigates forward through command history, returning to more recent commands or a draft of the current input.

        ## Parameters
        - `event` ( *Key* ) – The key event to handle, containing information about the key pressed.
        """
        if event.key == "escape":
            # Clear the input and reset history navigation state
            self.value = ""
            self._history_index = -1
            self._history_draft = ""
            event.stop()

        elif event.key == "up":
            # Do nothing if there is no history to navigate
            if not self._history:
                event.stop()
                return
            # Save the current draft before entering history navigation
            if self._history_index == -1:
                self._history_draft = self.value
            # Advance toward the oldest entry, clamping at the end of history
            next_index = self._history_index + 1
            if next_index < len(self._history):
                self._history_index = next_index
                self.value = self._history[-(self._history_index + 1)]
                self.cursor_position = len(self.value)
            event.stop()

        elif event.key == "down":
            # Do nothing if not currently navigating history
            if self._history_index == -1:
                event.stop()
                return
            # Advance toward the most recent entry
            self._history_index -= 1
            if self._history_index == -1:
                # Reached the bottom — restore the in-progress draft
                self.value = self._history_draft
            else:
                self.value = self._history[-(self._history_index + 1)]
            self.cursor_position = len(self.value)
            event.stop()



class SiteSelector(ModalScreen[str]):
    """
    A modal screen that presents a list of sites for the user to select from.

    Displays an `OptionList` populated with the provided site names. The user
    can navigate with the arrow keys and confirm with `Enter`, or cancel with
    `Escape`. The selected site name is returned to the caller via `dismiss`.

    ## Parameters
    - `sites` ( *list[string]* ) – The list of site names to display in the selector.

    ## Returns
    - The selected site name ( *string* ) on confirmation, or `None` if cancelled.

    ## Bindings
    - `Escape` – Dismisses the modal with no selection.
    """
    DEFAULT_CSS = """
    SiteSelector {
        align: center middle;
    }

    SiteSelector > Vertical {
        width: 60;
        max-height: 80%;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }

    SiteSelector > Vertical > #site-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
        color: $text;
    }

    SiteSelector > Vertical > OptionList {
        height: auto;
        max-height: 20;
        border: round $surface-lighten-2;
    }

    SiteSelector > Vertical > #site-hint {
        text-align: center;
        padding-top: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, sites: list[str]) -> None:
        """
        Initializes the `SiteSelector` with the list of sites to display.

        ## Parameters
        - `sites` ( *list[string]* ) – The list of site names to populate the option list with.
        """
        super().__init__()
        self.sites = sites


    def compose(self) -> ComposeResult:
        """
        Builds the modal layout with a title, option list, and hint text.

        ## Yields
        - A `Static` widget displaying the modal title.
        - An `OptionList` populated with one `Option` per site.
        - A `Static` widget displaying keybinding hints.
        """
        with Vertical():
            yield Static("Select a Site", id="site-title")
            yield OptionList(
                *[Option(site, id=site) for site in self.sites],
                id="site-list",
            )
            yield Static("↑/↓ to browse  •  Enter to select  •  Esc to cancel", id="site-hint")


    def on_mount(self) -> None:
        """
        Focuses the `OptionList` when the modal is mounted so the user can
        navigate immediately without clicking.
        """
        option_list = self.query_one(OptionList)
        option_list.focus()


    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """
        Handles option selection and dismisses the modal with the chosen site name.

        ## Parameters
        - `event` ( *OptionList.OptionSelected* ) – The selection event containing the chosen option.
        """
        self.dismiss(event.option.prompt)


    def action_cancel(self) -> None:
        """
        Dismisses the modal with `None` when the user presses `Escape`.
        """
        self.dismiss(None)

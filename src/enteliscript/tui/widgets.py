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

"""
# enteliscript.tui.app

Implements the `TUI` class, the top-level Textual application for `enteliscript`.
Defines the app layout (header, scrollable log, command input), key bindings, and 
the full command submission pipeline: tokenizing raw input, dispatching to registered 
command handlers, running blocking commands off the main thread, and handling special 
post-command actions such as clearing the log or launching the site selection modal screen.
"""

"""
# enteliscript.tui.cmd

Command definition and dispatch package for the `enteliscript` TUI.

Exports the `CommandHandler` class, which combines command implementations (from `commands.py`) 
with a runtime registry (built in `handler.py`) to support command parsing, help generation, 
and execution. Command metadata is attached via the `@command` decorator defined in `base.py`.
"""
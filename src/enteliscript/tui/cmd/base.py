"""
# enteliscript.tui.cmd.base

Provides the `@command` decorator and supporting utilities for defining TUI commands. 
The `@command` decorator attaches a `CommandSpec` to any command handler function, 
storing its name, aliases, usage string, summary, blocking behavior, and expected parameter types. 
The `_get_command_spec` helper retrieves that metadata from a callable, and is used during registry
construction in `CommandHandler`.
"""

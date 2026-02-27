"""
# enteliscript.tui.cmd.handler

Provides the `CommandHandler` class, which serves as the central command dispatcher 
for the TUI application. It inherits command definitions from `Commands`, builds a 
runtime registry mapping command names and aliases to their handler methods and metadata, 
and exposes a dispatch table for use by the command loop.
"""

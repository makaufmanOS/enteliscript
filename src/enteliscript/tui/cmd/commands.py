"""
# enteliscript.tui.cmd.commands

Defines the `Commands` mixin class, which contains all user-facing TUI command implementations. 
Each method decorated with `@command` represents a single dispatchable command, complete with 
metadata (name, aliases, usage, and help text). Commands cover authentication, site/device/object 
querying, and BACnet property writes – delegating API calls to an injected `EnteliwebAPI` instance.
"""

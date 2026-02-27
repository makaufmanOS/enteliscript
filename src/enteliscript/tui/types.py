"""
# enteliscript.tui.types

Defines the shared dataclass types used across the `enteliscript` TUI.

`CommandResult` – The return type for all command handler methods. Carries a
success flag, a user-facing message, an optional action string for the app to
act on (e.g. `"clear_log"`, `"select_site"`), and an optional consumable data payload.

`CommandSpec` – Immutable metadata attached to each registered command via the
`@command` decorator. Stores the canonical name, aliases, usage string, summary,
blocking behavior, and expected parameter types used for dispatch and help generation.
"""
from typing import Any, Type
from dataclasses import dataclass



@dataclass
class CommandResult:
    """
    Represents the outcome of executing a command handler.

    ## Attributes
    - `ok` ( *bool* ) – Indicates whether the command completed successfully.
    - `message` ( *string* ) – User-facing output to display in the log.
    - `action` ( *string*, *optional* ) – Optional action to be performed by the TUI.
    - `data` ( *any*, *optional* ) – Optional payload for the TUI to consume (e.g. a list of sites).
    """
    ok: bool
    message: str = ""
    action: str | None = None
    data: Any = None


@dataclass(frozen=True)
class CommandSpec:
    """
    Defines immutable metadata for a registered command.

    Used by the command system for help text generation and dispatch table construction.

    ## Attributes
    - `name` ( *string* ) – Canonical command name used for primary lookup.
    - `usage` ( *string* ) – Usage text shown in help output.
    - `summary` ( *string* ) – Short one-line description of the command.
    - `aliases` ( *tuple[string]*, *optional* ) – Alternate names that map to the same command.
    - `blocking` ( *bool*, *optional* ) – Indicates if the command is blocking. Defaults to `False`.
    - `blocking_msg` ( *string*, *optional* ) – Message to display when a blocking command is running. Defaults to `"Working..."`.
    - `params` ( *tuple[Type]*, *optional* ) – Expected argument types for the command, in order. Defaults to an empty tuple.
    """
    name: str
    usage: str
    summary: str
    aliases: tuple[str, ...] = ()
    blocking: bool = False
    blocking_msg: str = "Working..."
    params: tuple[Type, ...] = ()

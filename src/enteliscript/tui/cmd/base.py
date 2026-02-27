"""
# enteliscript.tui.cmd.base

Provides the `@command` decorator and supporting utilities for defining TUI commands. 
The `@command` decorator attaches a `CommandSpec` to any command handler function, 
storing its name, aliases, usage string, summary, blocking behavior, and expected parameter types. 
The `_get_command_spec` helper retrieves that metadata from a callable, and is used during registry
construction in `CommandHandler`.
"""
from typing import Callable, Iterable
from ..types import CommandResult, CommandSpec



def command(
        name: str, 
        *, 
        usage: str | None = None, 
        summary: str = "", 
        aliases: Iterable[str] = (), 
        blocking: bool = False, 
        blocking_msg: str | None = "Working...", 
        params: Iterable[str] | None = None,
    ) -> Callable[[Callable[..., CommandResult]], Callable[..., CommandResult]]:
    """
    Creates a decorator that attaches CLI metadata to a command method.

    The decorator normalizes command metadata (lowercased name/aliases and
    default usage text) and stores it on the decorated function as `_command_spec`.

    ## Parameters
    - `name` ( *string* ) – Primary command name.
    - `usage` ( *string*, *optional* ) – Usage string shown in help output. Defaults to `name` if not provided.
    - `summary` ( *string*, *optional* ) – Short description for help listings.
    - `aliases` ( *tuple*/*list*, *optional* ) – Alternate names that dispatch to the same command.
    - `blocking` ( *bool*, *optional* ) – Indicates if the command is blocking. Defaults to `False`.
    - `blocking_msg` ( *string*, *optional* ) – Message to display when a blocking command is running. Defaults to `"Working..."`.
    - `params` ( *tuple*/*list*, *optional* ) – Expected parameter types for the command, in order - used for validation. Defaults to an empty tuple.
    
    ## Returns
    - A decorator that accepts a command function and returns that same function with an attached `CommandSpec`.
    """
    normalized_name = name.lower()
    normalized_usage = usage or normalized_name
    normalized_aliases = tuple(alias.lower() for alias in aliases)

    def decorator(function: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
        """
        Attaches a normalized `CommandSpec` to the target function.

        ## Parameters
        - `function` ( *Callable* ) – Command handler function to annotate.

        ## Returns
        - The same function instance with `_command_spec` metadata attached.
        """
        function._command_spec = CommandSpec(
            name    = normalized_name,
            usage   = normalized_usage,
            summary = summary,
            aliases = normalized_aliases,
            blocking = blocking,
            blocking_msg = blocking_msg or ("Working..." if blocking else ""),
            params = tuple(params) if params else (),
        )
        return function
    return decorator


def _get_command_spec(method: Callable) -> CommandSpec | None:
    """
    Fetches command metadata from a callable if present.

    ## Parameters
    - `method` ( *Callable* ) – Callable that may have command metadata attached.

    ## Returns
    - The `CommandSpec` attached to `method`, or `None` if the callable is not a registered command.
    """
    return getattr(method, "_command_spec", None)

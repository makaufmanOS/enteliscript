"""
# enteliscript.tui.cmd.handler

Provides the `CommandHandler` class, which serves as the central command dispatcher 
for the TUI application. It inherits command definitions from `Commands`, builds a 
runtime registry mapping command names and aliases to their handler methods and metadata, 
and exposes a dispatch table for use by the command loop.
"""
from typing import Callable
from .commands import Commands
from ..types import CommandSpec
from .base import _get_command_spec
from ...enteliweb.api import EnteliwebAPI



class CommandHandler(Commands):
    """
    Implements command business logic and exposes command metadata.

    Inherits from `Commands` to gain access to all `cmd_*` handler methods.
    Builds a registry mapping command names and aliases to their handlers and
    specifications, which is used for command dispatch and help output.

    ## Attributes
    - `enteliweb` ( *EnteliwebAPI* ) – The enteliWEB API instance used by command handlers.
    - `sitename` ( *str | None* ) – The currently active site name, or `None` if not set.
    """
    def __init__(self, enteliweb: EnteliwebAPI) -> None:
        """
        Initializes the `CommandHandler` with the provided API instance and builds the command registry.

        ## Parameters
        - `enteliweb` ( *EnteliwebAPI* ) – The enteliWEB API instance to use for command execution.
        """
        self.enteliweb = enteliweb
        self.sitename: str | None = None
        self._registry: dict[str, tuple[Callable, CommandSpec]] = self._build_registry()


    def _build_registry(self) -> dict[str, tuple[Callable, CommandSpec]]:
        """
        Scans all methods on this instance for command specifications and builds a registry.

        Iterates over all callable attributes, retrieves their `CommandSpec` via
        `_get_command_spec`, and maps each command name and alias to its handler and spec.

        ## Returns
        - A dictionary mapping command tokens (names and aliases) to a tuple of
        `(handler, CommandSpec)`.
        """
        registry: dict[str, tuple[Callable, CommandSpec]] = {}
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if not callable(method):
                continue
            spec = _get_command_spec(method)
            if spec is None:
                continue
            registry[spec.name] = (method, spec)
            for alias in spec.aliases:
                registry[alias] = (method, spec)
        return registry


    def get_dispatch(self) -> dict[str, Callable]:
        """
        Returns a flat dispatch table mapping command tokens to their handler methods.

        ## Returns
        - A dictionary mapping each command name and alias to its callable handler.
        """
        return {token: method for token, (method, _) in self._registry.items()}

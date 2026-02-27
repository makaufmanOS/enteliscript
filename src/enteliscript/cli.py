"""
# enteliscript.cli

Defines the `main` entry point for the `enteliscript` command-line application.
Loads stored credentials via `get_credentials`, constructs an `EnteliwebAPI` client, 
and launches the Textual `TUI` application. This module is referenced by the `project.scripts` 
entry point in `pyproject.toml`, making `enteliscript` available as a standalone terminal command after installation.
"""
from .tui.app import TUI
from .enteliweb.api import EnteliwebAPI
from .enteliweb.config import get_credentials



def main() -> None:
    username, password = get_credentials()
    enteliweb = EnteliwebAPI(username=username, password=password)
    TUI(enteliweb).run()

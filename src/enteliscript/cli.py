"""
# enteliscript.cli

Defines the `main` entry point for the `enteliscript` command-line application.
Loads stored credentials via `get_credentials`, constructs an `EnteliwebAPI` client, 
and launches the Textual `TUI` application. This module is referenced by the `project.scripts` 
entry point in `pyproject.toml`, making `enteliscript` available as a standalone terminal command after installation.
"""
from .app import EnteliscriptTUI



def main() -> None:
    app = EnteliscriptTUI()
    app.run()

"""
cli.py

Provides the command-line entry function (`main`) that creates and runs the `enteliscript` TUI.
"""
from .app import EnteliscriptTUI



def main() -> None:
    app = EnteliscriptTUI()
    app.run()

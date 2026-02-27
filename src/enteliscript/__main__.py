"""
# enteliscript.__main__

Enables `enteliscript` to be run as a module via `python -m enteliscript` / `enteliscript`.
Delegates immediately to `cli.main()`, keeping this file a thin entry point with no logic of its own.
"""
from .cli import main



if __name__ == "__main__":
    main()

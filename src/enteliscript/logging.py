"""
# enteliscript.logging

Configures a shared rotating file logger for the `enteliscript` package.
Log files are stored in the platform-appropriate log directory (via `platformdirs`).
Imports from anywhere in the codebase to record user actions, API calls, errors, and other events.
"""
import logging
from pathlib import Path
from platformdirs import user_log_dir
from logging.handlers import RotatingFileHandler


LOG_DIR = Path(user_log_dir("enteliscript", appauthor=False))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "enteliscript.log"


_formatter = logging.Formatter(
    datefmt = "%m-%d-%Y %H:%M:%S",
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


_handler = RotatingFileHandler(
    LOG_FILE,
    backupCount = 3,
    encoding = "utf-8",
    maxBytes = 10 * 1024 * 1024,  # 10 MB per file
)
_handler.setFormatter(_formatter)


logger = logging.getLogger("enteliscript")
logger.setLevel(logging.DEBUG)
logger.addHandler(_handler)


def get_log_path() -> Path:
    """
    Gets the active log file's path.

    ### Returns
    - `Path` – The absolute path to the current log file.
    """
    return LOG_FILE.resolve()

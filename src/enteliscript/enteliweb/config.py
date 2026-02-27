"""
# enteliscript.enteliweb.config

Handles persistent configuration storage for `enteliscript` using a JSON file
stored in the platform-appropriate user config directory (via `platformdirs`).
Provides typed accessors for enteliWEB credentials (`get_credentials`,
`set_credentials`) as well as generic key/value storage (`get_value`,
`set_value`) for any other settings that need to persist between/across sessions.
"""
import json
from pathlib import Path
from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("enteliscript", appauthor=False))
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    """
    Attempts to load the config file.

    ## Returns
    - *dict* – The loaded configuration, or an empty 
      dictionary if the file doesn't exist or is invalid.

    ## Raises
    - *OSError* – If there's an issue reading the file (e.g., permissions).
    - *json.JSONDecodeError* – If the file contents aren't valid JSON.
    """
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(config: dict) -> None:
    """
    Saves configuration to the disk, creating directories as needed.

    ## Parameters
    - `config` ( *dict* ) – The configuration dictionary to save.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_config_dir() -> Path:
    """
    Gets the config directory's path.

    ## Returns
    - *Path* – The absolute path to the config directory.
    """
    return CONFIG_DIR.resolve()


def get_config_path() -> Path:
    """
    Gets the config file's path.

    ## Returns
    - *Path* – The absolute path to the config file.
    """
    return CONFIG_FILE.resolve()


def set_credentials(username: str, password: str) -> None:
    """
    Stores enteliWEB login credentials in the config file.

    ## Parameters
    - `username` ( *str* ) – The enteliWEB username to store.
    - `password` ( *str* ) – The enteliWEB password to store.
    """
    config = _load_config()
    config["username"] = username
    config["password"] = password
    _save_config(config)


def get_credentials() -> tuple[str | None, str | None]:
    """
    Retrieves stored enteliWEB credentials.

    ## Returns
    - *tuple* – A tuple containing the username and password, or `None` for each if not set.
    """
    config = _load_config()
    return config.get("username"), config.get("password")


def set_value(key: str, value: str) -> None:
    """
    Stores an arbitrary config value.

    ## Parameters
    - `key` ( *str* ) – The configuration key to set.
    - `value` ( *str* ) – The value to associate with the key.
    """
    config = _load_config()
    config[key] = value
    _save_config(config)


def get_value(key: str, default: str | None = None) -> str | None:
    """
    Retrieves an arbitrary config value.

    ## Parameters
    - `key` ( *str* ) – The configuration key to retrieve.
    - `default` ( *str*, *optional* ) – The value to return if the key isn't found (default: `None`).

    ## Returns
    - *str* / *None* – The value associated with the key, or the default value if the key isn't found.
    """
    config = _load_config()
    return config.get(key, default)

"""
# enteliscript.enteliweb.config

Handles persistent configuration storage for `enteliscript` using a JSON file
stored in the platform-appropriate user config directory (via `platformdirs`).
Provides typed accessors for enteliWEB credentials (`get_credentials`,
`set_credentials`) as well as generic key/value storage (`get_value`,
`set_value`) for any other settings that need to persist between/across sessions.
"""

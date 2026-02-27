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

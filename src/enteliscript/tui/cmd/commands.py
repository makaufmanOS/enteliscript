"""
# enteliscript.tui.cmd.commands

Defines the `Commands` mixin class, which contains all user-facing TUI command implementations. 
Each method decorated with `@command` represents a single dispatchable command, complete with 
metadata (name, aliases, usage, and help text). Commands cover authentication, site/device/object 
querying, and BACnet property writes – delegating API calls to an injected `EnteliwebAPI` instance.
"""
import re
import os
from .base import command
from typing import Callable
from rich.markup import escape
from ...enteliweb.api import EnteliwebAPI
from ..types import CommandSpec, CommandResult
from ...enteliweb.config import get_credentials, set_credentials, get_config_dir



class Commands:
    """
    Collection of TUI command definitions.

    ## Commands
    - `clear` – Clear the output log.
    - `help` – Show command list or details for one command.
    - `login` – Authenticate the enteliWEB API.
    - `getlogin` – Show the currently saved username.
    - `setlogin` – Save enteliWEB credentials for this user.
    - `setsite` – List available sites and select one.
    - `getsite` – Show the currently selected site.
    - `getdevices` – List devices at the current site.
    - `getobjects` – List BACnet objects for a device.
    - `writeproperty` – Write a value to a property.
    - `writecsv` – Write BACnet properties from a CSV file.
    """
    sitename:  str
    enteliweb: EnteliwebAPI
    _registry: dict[str, tuple[Callable, CommandSpec]]


    @command(
        name    = "clear",
        usage   = "clear",
        summary = "Clear the output log."
    )
    def cmd_clear(self) -> CommandResult:
        """
        Clears the output log via injected callback.

        ## Returns
        - `CommandResult` with `action="clear_log"` to signal the TUI to clear the log.
        """
        return CommandResult(True, "", action="clear_log")
    

    @command(
        name    = "help",
        aliases = ("h", "?"),
        usage   = "help <command>",
        summary = "Show command list or details for one command.",
    )
    def cmd_help(self, command_name: str = "") -> CommandResult:
        """
        Shows general help or detailed help for a specific command.

        If `command_name` is empty, returns a formatted list of all commands.
        If provided, resolves by command name first, then by alias.

        ## Parameters
        - `command_name` ( *string* ) – Optional command/alias to inspect.

        ## Returns
        - A `CommandResult` containing either: detailed help for one command, 
        the full command listing, or an error message if the command is unknown.
        """
        name = command_name.strip().lower()

        seen = set()
        unique_specs = []
        hidden = {"clear", "help"}
        for token, (_, spec) in self._registry.items():
            if spec.name not in seen:
                seen.add(spec.name)
                if spec.name not in hidden:
                    unique_specs.append(spec)

        if name:
            entry = self._registry.get(name)
            if entry is None:
                return CommandResult(False, f"Unknown command {command_name!r}")
            _, spec = entry

            aliases = f" (aliases: {', '.join(spec.aliases)})" if spec.aliases else ""
            details = [
                f"{spec.name}{aliases}",
                f"  usage: {spec.usage}",
            ]
            if spec.summary:
                details.append(f"  {spec.summary}")
            return CommandResult(True, "\n".join(details))

        lines = ["Commands:"]
        entries = []
        for spec in sorted(unique_specs, key=lambda s: s.name):
            alias_text = f" [{', '.join(spec.aliases)}]" if spec.aliases else ""
            args_part = escape(spec.usage[len(spec.name):])  # escape <arg> brackets
            coloured_usage = f"[cyan]{spec.name}[/cyan]{args_part}"
            entries.append((coloured_usage, len(spec.usage) + len(alias_text), alias_text, spec.summary))

        max_usage_len = max(plain_len for _, plain_len, _, _ in entries)
        min_dots = 2

        for coloured_usage, plain_len, alias_text, summary in entries:
            dots = "[yellow]" + "." * (max_usage_len - plain_len + min_dots) + "[/yellow]"
            summary_text = f"  {summary}" if summary else ""
            lines.append(f"  {coloured_usage}{alias_text}  {dots}{summary_text}")

        return CommandResult(True, "\n".join(lines))
    

    @command(
        name    = "whereconfig",
        usage   = "whereconfig",
        summary = "Show the directory of the config and log files.",
    )
    def cmd_whereconfig(self) -> CommandResult:
        """
        Shows the directory for the config and log files.

        ## Returns
        - `CommandResult` with the path to the config directory, which is also where log files are stored.
        """
        config_dir = get_config_dir()
        return CommandResult(True, f"Config directory: {config_dir}")
    

    @command(
        name     = "login",
        usage    = "login",
        summary  = "Authenticate the enteliWEB API.",
        blocking = True,
        blocking_msg = "Logging in ..."
    )
    def cmd_login(self) -> CommandResult:
        """
        Authenticates the enteliWEB API client using stored credentials.
        If credentials are missing, returns an error result prompting the user to set them first.
        On success, includes an action for the TUI to proceed with site selection.

        ## Returns
        - `CommandResult` indicating success or failure of the login attempt, with an appropriate message.
        """
        if (self.enteliweb.username is None or self.enteliweb.password is None):
            return CommandResult(False, "Login failed. Login credentials must be set first.")

        success = self.enteliweb.login()
        if success:
            return CommandResult(True, "Login successful.")
        else:
            return CommandResult(False, "Login failed. Check credentials and/or server status.")

        # TODO: Implement below flow after successful login.
        # success = self.enteliweb.login()
        # if not success:
        #     return CommandResult(False, "Login failed. Check credentials and/or server status.")

        # # Automatically fetch sites after successful login
        # sites = self.enteliweb.get_sites()
        # if not sites:
        #     return CommandResult(True, "Login successful, but no sites were found.")

        # return CommandResult(
        #     True,
        #     f"Login successful. Found {len(sites)} site(s).",
        #     action="select_site",
        #     data=sites,
        # )
    

    @command(
        name    = "getlogin",
        usage   = "getlogin",
        summary = "Show the currently saved username."
    )
    def cmd_getlogin(self) -> CommandResult:
        """
        Shows the currently stored username (not the password).

        ## Returns
        - `CommandResult` with the stored username, or an error message if no credentials are stored.
        """
        username, password = get_credentials()
        
        if username is None or password is None:
            return CommandResult(False, "No credentials stored.")

        # Show only the first two and last two characters of the password, if it's long enough
        len_password = len(password)
        if len_password > 4:
            password_display = f"{password[:2]}{'*' * (len_password - 4)}{password[-2:]}"
        else:
            password_display = "*" * len_password
        
        return CommandResult(True, f"Username: {username!r}  |  Password: {password_display}")
    

    @command(
        name    = "setlogin",
        usage   = "setlogin <username> <password>",
        summary = "Save enteliWEB credentials for this user.",
        params  = (str, str)
    )
    def cmd_setlogin(self, username: str, password: str) -> CommandResult:
        """
        Sets enteliWEB login credentials.

        ## Parameters
        - `username` ( *string* ) – The enteliWEB username to save.
        - `password` ( *string* ) – The enteliWEB password to save.

        ## Returns
        - `CommandResult` indicating success or failure of the credential saving process, with an appropriate message.
        """
        # TODO: Consider keyring integration to avoid plaintext storage of credentials.
        if not username or not password:
            return CommandResult(False, "Usage: setlogin <username> <password>")
        
        set_credentials(username, password)
        self.enteliweb.set_username(username)
        self.enteliweb.set_password(password)
        return CommandResult(True, f"Credentials saved for username {username!r}.")
    

    @command(
        name     = "setsite",
        usage    = "setsite",
        summary  = "List available sites and select one.",
        blocking = True,
        blocking_msg = "Fetching sites ..."
    )
    def cmd_setsite(self) -> CommandResult:
        """
        Fetches available sites from enteliWEB and presents a selection menu.

        ## Returns
        - `CommandResult` containing a list of sites for selection, or an error message if no sites are found.
        """
        sites = self.enteliweb.get_sites()
        # sites = ["site1", "site2", "site3"]  # <-- temporary hardcoded for testing
        if not sites:
            return CommandResult(False, "No sites found (are you logged in?).")

        return CommandResult(
            True,
            f"Found {len(sites)} site(s).",
            action="select_site",
            data=sites,
        )
    

    @command(
        name    = "getsite",
        usage   = "getsite",
        summary = "Show the currently selected site.",
    )
    def cmd_getsite(self) -> CommandResult:
        """
        Shows the currently selected site name.

        ## Returns
        - `CommandResult` with the current site name, or an error message if no site is selected.
        """
        if self.sitename is not None:
            return CommandResult(True, f"Current site: [bold]{self.sitename}[/bold]")
        
        return CommandResult(False, "No site selected. Run [bold]login[/bold] or [bold]setsite[/bold] first.")
    

    @command(
        name    = "getdevices",
        usage   = "getdevices",
        summary = "List devices at the current site.",
        blocking = True,
        blocking_msg = "Fetching devices ..."
    )
    def cmd_getdevices(self) -> CommandResult:
        """
        Fetches and lists devices for the currently selected site.

        ## Returns
        - `CommandResult` containing a list of devices at the current site, or an error message if no site is selected or if no devices are found.
        """
        if self.sitename is None:
            return CommandResult(False, "No site selected. Run [bold]login[/bold] or [bold]setsite[/bold] first.")

        devices = self.enteliweb.get_devices(self.sitename)
        if not devices:
            return CommandResult(False, "No devices found at this site.")
        
        device_list = "\n".join(f"- {d}" for d in devices)
        return CommandResult(True, f"Devices at site '{self.sitename}':\n{device_list}")
    

    @command(
        name    = "getobjects",
        usage   = "getobjects <device>",
        summary = "List BACnet objects for a device.",
        blocking = True,
        blocking_msg = "Fetching objects ..."
    )
    def cmd_getobjects(self, device: str) -> CommandResult:
        """
        Fetches and lists BACnet objects for a specified device.

        ## Parameters
        - `device` ( *string* ) – The device address to query.

        ## Returns
        - `CommandResult` containing a list of objects for the device, or an error if no site is selected or the device is not found.
        """
        if self.sitename is None:
            return CommandResult(False, "No site selected. Run [bold]login[/bold] or [bold]setsite[/bold] first.")

        objects = self.enteliweb.get_objects(self.sitename, device)
        if not objects:
            return CommandResult(False, f"No objects found for device '{device}' at site '{self.sitename}'.")

        object_list = "\n".join(f"- {o}" for o in objects)
        return CommandResult(True, f"Objects for device '{device}' at site '{self.sitename}':\n{object_list}")


    @command(
        name    = "writeproperty",
        usage   = "writeproperty <device> <obj> <prop> <value>",
        summary = "Write a value to a property.",
        blocking = True,
        blocking_msg = "Writing property ..."
    )
    def cmd_writeproperty(self, device: str, obj: str, prop: str, value: str) -> CommandResult:
        """
        Writes a value to a specified property on the enteliWEB API.

        ## Parameters
        - `device` ( *string* ) – The device address that contains the target object.
        - `obj` ( *string* ) – The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.) + instance number (e.g., `AI1`/`AV3`).
        - `prop` ( *string* ) – The name of the property to write.
        - `value` ( *string* ) – The value to write to the property.

        ## Returns
        - `CommandResult` indicating success or failure of the write operation.
        """
        match = re.match(r'^([A-Za-z]+)(\d+)$', obj)
        if not match:
            return CommandResult(False, f"Invalid object format: {obj}. Expected e.g. 'AV1', 'AO3'.")

        obj_type = match.group(1).upper()
        instance = match.group(2)

        if self.sitename is None:
            return CommandResult(False, "No site selected. Run [bold]login[/bold] or [bold]setsite[/bold] first.")

        success = self.enteliweb.write_property(self.sitename, device, obj_type, instance, prop, value)
        if success:
            return CommandResult(True, f"Successfully wrote value {value!r} to {device}/{obj_type}/{instance}/{prop}.")
        else:
            return CommandResult(False, f"Failed to write property. Check device/object/instance/property names and try again.")
    

    @command(
        name    = "writecsv",
        usage   = "writecsv <csv_path>",
        summary = "Write BACnet properties from a CSV file.",
        blocking = True,
        blocking_msg = "Writing properties from CSV ..."
    )
    def cmd_writecsv(self, csv_path: str) -> CommandResult:
        """
        Writes BACnet property values from a CSV file.

        The CSV should have columns: `site_name`, `device`, `object_type`, `instance`, `property_name`, `property_value`.

        ## Parameters
        - `csv_path` ( *string* ) – Path to the CSV file.

        ## Returns
        - `CommandResult` summarizing how many writes succeeded and failed.
        """
        if not os.path.isfile(csv_path):
            return CommandResult(False, f"File not found: {csv_path!r}")

        results = []
        success_count = 0
        fail_count = 0

        for property_path, success in self.enteliweb.write_properties_from_csv(csv_path):
            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            results.append(f"  {status} {property_path}")
            if success:
                success_count += 1
            else:
                fail_count += 1

        if not results:
            return CommandResult(False, "No rows were processed from the CSV file.")

        summary = f"CSV write complete: {success_count} succeeded, {fail_count} failed."
        detail = "\n".join(results)
        return CommandResult(True, f"{summary}\n{detail}")

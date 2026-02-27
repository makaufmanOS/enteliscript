"""
# enteliscript.enteliweb.api

Provides the `EnteliwebAPI` class, a session-based HTTP client for interacting
with the enteliWEB REST API. Manages authentication (session ID and CSRF token),
and exposes methods for the full BACnet data hierarchy: sites, devices, objects,
and properties. Supports single and bulk property writes, including CSV-driven
batch operations. All requests are made over HTTP using the `requests` library,
with Rich console logging for visibility into each operation.
"""
import csv
import json
import socket
import requests
from typing import Generator
from ..logging import logger



class EnteliwebAPI:
    """
    Class for interacting with the `enteliWEB` API.

    ## Init Parameters
    - `username` ( *string* ) – The username for enteliWEB.
    - `password` ( *string* ) – The password for enteliWEB.
    - `server_ip` ( *string* ) – The IP address of the enteliWEB server. 
                                 If not provided, the local machine's IP will be used.
    """
    def __init__(self, username: str, password: str, server_ip: str | None = None) -> None:
        """
        Initializes the `EnteliwebAPI` instance with the provided credentials and server information.

        ## Parameters
        - `username` ( *string* ) – The username for enteliWEB.
        - `password` ( *string* ) – The password for enteliWEB.
        - `server_ip` ( *string* ) – The IP address of the enteliWEB server. 
                                     If not provided, the local machine's IP will be used.
        """
        self.username = username
        self.password = password
        self.server = (
            socket.gethostbyname(socket.gethostname()) 
            if (server_ip is None) else server_ip.split("://")[-1]
        )
        self.csrf_token = ""
        self.session_id: str | None = None
        self.session_key = "enteliWebID"
        self.csrf_token_key = "_csrfToken"
        self.base_url = "/enteliweb/api/.bacnet/"
        logger.info(f"EnteliwebAPI initialized for server {self.server} (user: {self.username})")


    def set_username(self, username: str) -> None:
        """
        Sets the username for the API instance.

        ## Parameters
        - `username` ( *string* ) – The new username to set.
        """
        self.username = username
        logger.info(f"Username updated to {username}")


    def set_password(self, password: str) -> None:
        """
        Sets the password for the API instance.

        ## Parameters
        - `password` ( *string* ) – The new password to set.
        """
        self.password = password
        logger.info(f"Password updated for user {self.username}")


    def login(self) -> bool:
        """
        *Endpoint:* `/api/auth/basiclogin`

        Retrieves the session ID and CSRF token and stores them for future requests.

        ## Returns
        - `True` if login was successful, `False` otherwise.
        """
        logger.info(f"Attempting login for user {self.username} at server {self.server}...")

        if (self.username is None or self.password is None):
            logger.warning("Login failed. Login credentials not set.")
            return False

        try:
            r = requests.get(
                url = f"http://{self.server}/enteliweb/api/auth/basiclogin?alt=JSON",
                auth = (self.username, self.password),
                headers = {'Content-Type': 'application/json'},
                timeout = 10,
            )
        except Exception as e:
            logger.error(f"Login request failed: {e}")
            return False

        if (r.status_code != requests.codes.ok):
            logger.warning(f"Login failed ({r.status_code}): {r.reason}")
            return False
        
        if (r.text.find('Cannot Connect') > -1):
            logger.warning(f"Login failed: {r.text}")
            return False
        
        if (not self.session_key in r.cookies.keys()):
            logger.warning(f"Login failed: {r.text}")
            return False
        
        result = r.json()
        self.session_id = r.cookies[self.session_key]
        self.csrf_token = result[self.csrf_token_key]

        logger.info("Login successful.")
        return True
    

    def create_object(self, site_name: str, device: str, object_type: str, instance: str, name: str, properties: dict | None = None) -> bool:
        """
        *Endpoint:* `/api/.bacnet/{site}/{device}`

        Creates a new BACnet object for a device.

        ## Parameters
        - `site_name` ( *string* ) – The site that contains the target device. 
        - `device` ( *string* ) – The device address in which to create the object.
        - `object_type` ( *string* ) – The name of BACnet object to create (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance` ( *string* ) – The instance number of the BACnet object.
        - `name` ( *string* ) – The desired name of the BACnet object.
        - `properties` ( *dict*, *optional* ) – A dictionary of additional properties to set on the BACnet object.

        ## Returns
        - `True` if the object was created successfully, `False` otherwise.
        """
        properties = properties or {}

        logger.info(f"Attempting to create object with name '{name}' and ID '{object_type},{instance}' in device '{device}' at site '{site_name}'...")

        if (self.session_id is None):
            logger.warning("Failed to create object: Not logged in.")
            return False

        data = {
            "$base": "Object",
            "object-identifier": {
                "$base": "ObjectIdentifier",
                "value": f"{object_type},{instance}"
            },
            "object-name": {
                "$base": "String",
                "value": name
            },
        }

        for property in properties:
            data[property] = { "$base": "String", "value": properties[property] }

        r = requests.post(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps(data),
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (not success or msg != "Created"):
            logger.warning(f"Failed to create object ({code}): {msg}")
            return False
        
        logger.info(f"Object created successfully.")
        return r.status_code == requests.codes.created
    

    def delete_object(self, site_name: str, device: str, object_type: str, instance: str) -> bool:
        """
        *Endpoint:* `/api/.bacnet/{site}/{device}/{object_type},{instance}`

        Deletes a BACnet object from a device.

        ## Parameters
        - `site_name` ( *string* ) – The site that contains the target device.
        - `device` ( *string* ) – The device address from which to delete the object.
        - `object_type` ( *string* ) – The name of the BACnet object to delete (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance` ( *string* ) – The instance number of the BACnet object.

        ## Returns
        - `True` if the object was deleted successfully, `False` otherwise.
        """
        logger.info(f"Attempting to delete object with ID '{object_type},{instance}' from device '{device}' at site '{site_name}'...")
        
        if (self.session_id is None):
            logger.warning("Unable to delete object: Not logged in.")
            return False
        
        r = requests.delete(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/{object_type},{instance}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (r.status_code != requests.codes.non_authoritative_info):
            logger.warning(f"Failed to delete object ({code}): {msg}")
            return False
        
        logger.info("Object deleted successfully.")
        return True
    

    def write_property(self, site_name: str, device: str, object_type: str, instance: str, property_name: str, value: str) -> bool:
        """
        *Endpoint:* `/api/.bacnet/<site>/<device>/<object_type>,<instance>/<property_name>`

        Writes a value to a BACnet object's property.

        ## Parameters
        - `site_name` ( *string* ) – The site that contains the target device.
        - `device` ( *string* ) – The device address that contains the target object.
        - `object_type` ( *string* ) – The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance` ( *string* ) – The instance number of the BACnet object.
        - `property_name` ( *string* ) – The name of the property to write.
        - `value` ( *string* ) – The value to write to the property.

        ## Returns
        - `True` if the property was written successfully, `False` otherwise.
        """
        logger.info(f"Attempting to write property '{property_name}' with value '{value}' to object '{object_type},{instance}' in device '{device}' at site '{site_name}'...")

        if (self.session_id is None):
            logger.warning("Unable to write property: Not logged in.")
            return False
        
        # Detect sub-property and array index
        property_name = property_name.replace('[', '.').replace(']', '').replace('.', '/')

        r = requests.put(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/{object_type},{instance}/{property_name}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
                "$base": "String",
                "value": value,
            }),
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (r.status_code != requests.codes.ok):
            logger.warning(f"Failed to write property ({code}): {msg}")
            return False
        
        logger.info("Property written successfully.")
        return True
    

    def write_properties(self, site_name: str, device: str, object_type: str, instance: str, properties: dict) -> bool:
        """
        *Endpoint:* `/api/.multi`

        Writes multiple properties to a BACnet object.

        ## Parameters
        - `site_name` ( *string* ) – The site that contains the target device.
        - `device` ( *string* ) – The device address that contains the target object.
        - `object_type` ( *string* ) – The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance` ( *string* ) – The instance number of the BACnet object.
        - `properties` ( *dict* ) – A dictionary of property names and values to write.

        ## Returns
        - `True` if all properties were written successfully, `False` otherwise.
        """
        logger.info(f"Attempting to write multiple properties to {object_type},{instance} on device {device} at site {site_name}...")
        
        if (self.session_id is None):
            logger.warning("Unable to write properties: Not logged in.")
            return False

        value_list = {
            "$base": "List",
        }

        for i, property in enumerate(properties, start=1):
            value_list[i] = {       # TODO: Consider `value_list[str(i)]` since JSON serialization converts to string anyways
                "$base": "String",
                "via": f"/.bacnet/{site_name}/{device}/{object_type},{instance}/{property}",
                "value": properties[property]
            }

        r = requests.post(
            url = f"http://{self.server}/enteliweb/api/.multi?alt=json&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
                "$base": "Struct",
                "values": value_list,
            }),
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (r.status_code != requests.codes.ok):
            logger.warning(f"Failed to write properties ({code}): {msg}")
            return False
        
        logger.info("Properties written successfully.")
        return True
    

    def write_properties_from_csv(self, csv_path: str) -> Generator[tuple[str, bool], None, None]:
        """
        *Endpoint:* `/api/.bacnet/<site>/<device>/<object_type>,<instance>/<property_name>`

        Writes values to BACnet objects' properties from a CSV file.

        ## Parameters
        - `csv_path` ( *string* ) – The file path to the CSV file containing the properties to write.  
        The CSV should have columns: `site_name`, `device`, `object_type`, `instance`, `property_name`, `property_value`.

        ## Yields
        - Tuples containing the property name and a boolean indicating success or failure for each property write.

        ## Usage
        ```python
        for property_name, success in api.write_properties_from_csv("data.csv"):
            # Display/update UI immediately for each result
            console.log(f"{property_name}: {'✓' if success else '✗'}")
        ```
        """
        logger.info(f"Attempting to write properties from CSV file {csv_path}...")

        if (self.session_id is None):
            logger.warning("Unable to write properties from CSV: Not logged in.")
            return
        
        try:
            with open(csv_path, mode='r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    site_name = row['site_name']
                    device = row['device']
                    object_type = row['object_type']
                    instance = row['instance']
                    property_name = row['property_name']
                    value = row['property_value']

                    success = self.write_property(site_name, device, object_type, instance, property_name, value)
                    logger.info(f"Write {'succeeded' if success else 'failed'} for {site_name}/{device}/{object_type},{instance}/{property_name}")
                    yield (f"{site_name}/{device}/{object_type},{instance}/{property_name}", success)
        
        except Exception as e:
            logger.error(f"Failed to write properties from CSV: {e}")
            return
        
    
    def get_sites(self) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet`

        Gets all sites for the current enteliWEB server.

        ## Returns
        - A list of sites, or an empty list if none are found.
        """
        logger.info("Attempting to get sites...")

        if (self.session_id is None):
            logger.warning("Unable to get sites: Not logged in.")
            return []

        r = requests.get(
            url = f"http://{self.server}{self.base_url}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (success is not True):
            logger.warning(f"Failed to get sites ({code}): {msg}")
            return []
        
        result = r.json()
        logger.info("Sites retrieved successfully.")
        return [
            key
            for key in sorted(result)
            if ("nodeType" in result[key] and result[key]["nodeType"] == "NETWORK")
        ]


    def get_devices(self, site_name: str) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet/<site_name>`

        Gets all devices for a given site.

        ## Parameters
        - `site_name` ( *string* ) – The name of the site to get devices for.

        ## Returns
        - A list of devices, or an empty list if none are found.
        """
        logger.info(f"Attempting to get devices for site {site_name}...")
        
        def custom_key(x):
            try: return int(x)
            except: return 0

        if (self.session_id is None):
            logger.warning("Unable to get devices: Not logged in.")
            return []

        r = requests.get(
            url = f"http://{self.server}{self.base_url}{site_name}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (success is not True):
            logger.warning(f"Failed to get devices for site {site_name} ({code}): {msg}")
            return []
        
        result = r.json()
        logger.info("Devices retrieved successfully.")
        return [
            f"{key} - {result[key]['displayName']}"
            for key in sorted(result, key=custom_key)
            if ("nodeType" in result[key] and result[key]["nodeType"] == "DEVICE")
        ]
    

    def get_objects(self, site_name: str, device: str) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet/<site_name>/<device>`

        Gets all BACnet objects for a given device on a specific site.

        ## Parameters
        - `site_name` ( *string* ) – The name of the site that contains the target device.
        - `device` ( *string* ) – The device address to get objects for.

        ## Returns
        - A list of BACnet objects, or an empty list if none are found.
        """
        logger.info(f"Attempting to get objects for device {device} on site {site_name}...")

        if (self.session_id is None):
            logger.warning("Unable to get objects: Not logged in.")
            return []

        r = requests.get(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (success is not True):
            logger.warning(f"Failed to get objects ({code}): {msg}")
            return []
        
        result = r.json()
        logger.info("Objects retrieved successfully.")
        return [
            key
            for key in sorted(result)
            if ("$base" in result[key] and result[key]["$base"] == "Object")
        ]
    

    def get_properties(self, site_name: str, device: str, object_type: str, instance: str) -> dict:
        """
        *Endpoint:* `/api/.bacnet/<site_name>/<device>/<object_type>,<instance>`

        Gets all properties for a given BACnet object on a specific device and site.

        ## Parameters
        - `site_name` ( *string* ) – The name of the site that contains the target device.
        - `device` ( *string* ) – The device address to get objects for.
        - `object_type` ( *string* ) – The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance` ( *string* ) – The instance identifier of the BACnet object.

        ## Returns
        - A dictionary of properties for the specified BACnet object, or an empty dictionary if none are found.
        """
        logger.info(f"Attempting to get properties for object {object_type},{instance} on device {device} at site {site_name}...")

        if (self.session_id is None):
            logger.warning("Unable to get properties: Not logged in.")
            return {}

        r = requests.get(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/{object_type},{instance}/?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            timeout = 10,
        )

        success, code, msg = self._check_error(r)
        if (success is not True):
            logger.warning(f"Failed to get properties ({code}): {msg}")
            return {}
        
        result = r.json()
        logger.info("Properties retrieved successfully.")

        def replace_base_key(obj: dict | list | str) -> dict:
            """
            Recursively replaces the `$base` key in a dictionary with `type` for better readability.
            """
            if isinstance(obj, dict):
                new_obj = {}
                for key, value in obj.items():
                    new_key = "type" if key == "$base" else key
                    new_obj[new_key] = replace_base_key(value)
                return new_obj
            elif isinstance(obj, list):
                return [replace_base_key(item) for item in obj]
            else:
                return obj

        return replace_base_key(result)
    

    def _check_error(self, response: requests.Response) -> tuple[bool, int, str]:
        """
        Checks a response for errors.

        ## Parameters
        - `response` ( *requests.Response* ) – The response object to check.

        ## Returns
        - `success` ( *bool* ) – `True` if the request was successful, `False` otherwise.
        - `code` ( *int* ) – The HTTP status code of the response.
        - `msg` ( *string* ) – The error message, if any.
        """
        result = response.json() if (response.status_code == requests.codes.ok) else {}

        if ("error" in result and result["error"] != "-1"):
            code    = result["error"]
            msg     = result["errorText"]
            success = False
        elif (response.status_code == requests.codes.non_authoritative_info):
            code    = str(response.status_code)
            msg     = "OK"
            success = True
        else:
            code    = str(response.status_code)
            msg     = response.reason
            success = (response.status_code == requests.codes.ok)

        return (success, code, msg)
    

    def _find_abbreviation(self, bacnet_object_name: str) -> str:
        """
        Resolves a BACnet object name (e.g., `analog-input`, `trend-log`, etc.) to its corresponding abbreviation.

        ## Parameters
        - `bacnet_object_name` ( *string* ) – The name of the BACnet object to resolve.

        ## Returns
        - `str` – The abbreviation of the BACnet object name if found, else an empty string.
        """
        object_name_map = {
            "ACC": "access-credential",         "EL": "event-log",
            "ACD": "access-door",               "FIL": "file",
            "ACP": "access-point",              "GGP": "global-group",
            "ACR": "access-rights",             "GR": "group",
            "ACU": "access-user",               "IV": "integer-value",
            "ACZ": "access-zone",               "LAV": "large-analog-value",
            "AC": "accumulator",                "ZP": "life-safety-point",
            "AIC": "aic",                       "ZN": "life-safety-zone",
            "AE": "alert-enrollment",           "LO": "lighting-output",
            "AI": "analog-input",               "LS": "load-control",
            "AO": "analog-output",              "CO": "loop",
            "AV": "analog-value",               "MIC": "mic",
            "AOC": "aoc",                       "MOC": "moc",
            "AT": "at",                         "MT": "mt",
            "AVG": "averaging",                 "MI": "multi-state-input",
            "BDC": "bdc",                       "MO": "multi-state-output",
            "BDE": "bde",                       "MV": "multi-state-value",
            "BI": "binary-input",               "NET": "net",
            "BO": "binary-output",              "NS": "network-security",
            "BV": "binary-value",               "EVC": "notification-class",
            "BSV": "bitstring-value",           "NF": "notification-forwarder",
            "BT": "bt",                         "OSV": "octetstring-value",
            "CAL": "calendar",                  "ORS": "ors",
            "CNL": "channel",                   "OS": "os",
            "CSV": "characterstring-value",     "PI": "pi",
            "CS": "command",                    "PIV": "positive-integer-value",
            "ACI": "credential-data-input",     "PG": "program",
            "DPValue": "date-pattern-value",    "PC": "pulse-converter",
            "DV": "date-value",                 "SCH": "schedule",
            "DTP": "datetime-pattern-value",    "SV": "structured-view",
            "DTV": "datetime-value",            "TPV": "time-pattern-value",
            "DES": "des",                       "TV": "time-value",
            "DEV": "device",                    "TL": "trend-log",
            "DRT": "drt",                       "TLM": "trend-log-multiple",
            "EV": "event-enrollment",           "Unassigned 1": "unassigned-1",
        }
        # TODO: Currently unused
        # TODO: Consider `return {v: k for k, v in object_name_map.items()}.get(bacnet_object_name, "")`
        for object_abbreviation, mapped_bacnet_object_name in object_name_map.items():
            if bacnet_object_name == mapped_bacnet_object_name:
                return object_abbreviation
        return ""

"""
# enteliscript.enteliweb.api

Provides the `EnteliwebAPI` class, a session-based HTTP client for interacting
with the enteliWEB REST API. Manages authentication (session ID and CSRF token),
and exposes methods for the full BACnet data hierarchy: sites, devices, objects,
and properties. Supports single and bulk property writes, including CSV-driven
batch operations. All requests are made over HTTP using the `requests` library,
with Rich console logging for visibility into each operation.
"""

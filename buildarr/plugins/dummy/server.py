# Copyright (C) 2024 Callum Dickinson
#
# Buildarr is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Buildarr is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Buildarr.
# If not, see <https://www.gnu.org/licenses/>.


"""
Dummy server Flask application.

This simulates an application that keeps state that can be modified via an API.

To run this application, run the following command:

```bash
$ BUILDARR_DUMMY_API_KEY="1a2b3c4d5e" flask --app buildarr.plugins.dummy.server run
```

This file is not required when creating a new plugin.

This is simply for convenience when testing, to give the Dummy plugin something
to communicate with for testing purposes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, cast

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import InternalServerError, NotFound, Unauthorized

from buildarr import __version__

if TYPE_CHECKING:
    from typing import Any, Dict, Tuple


__all__ = ["app"]

app = Flask("buildarr-dummy-server")

app.config.from_prefixed_env(prefix="BUILDARR_DUMMY")
if "API_ROOT" not in app.config:
    app.config["API_ROOT"] = "/api/v1"
if "API_FORCE_AUTH" not in app.config:
    app.config["API_FORCE_AUTH"] = False
if "API_SUPPORTS_INIT" not in app.config:
    app.config["API_SUPPORTS_INIT"] = False
if "API_REQUIRES_INIT" not in app.config:
    app.config["API_REQUIRES_INIT"] = False

_is_initialized: bool = not app.config["API_REQUIRES_INIT"]

_settings: Dict[str, Any] = {
    "isUpdated": False,  # bool
    "trashValue": None,  # Optional[float]
    "trashValue2": None,  # Optional[float]
    "instanceValue": None,  # Optional[str] (UUID)
}


@app.errorhandler(401)
def unauthorized(error: Unauthorized) -> Tuple[Response, int]:
    """
    Handle a `401 Unauthorized` error.

    Args:
        error (Unauthorized): Unauthorized exception object

    Returns:
        Error responses
    """

    return (jsonify({"message": "Unauthorized", "description": error.description}), 401)


@app.errorhandler(404)
def not_found(error: NotFound) -> Tuple[Response, int]:
    """
    Handle a `404 Not Found` error.

    Args:
        error (NotFound): Not found exception object

    Returns:
        Error responses
    """

    return (jsonify({"message": "Not Found", "description": error.description}), 404)


@app.errorhandler(500)
def internal_server_error(error: NotFound) -> Tuple[Response, int]:
    """
    Handle a `500 Internal Server Error` error.

    Args:
        error (InternalServerError): Internal server error exception object

    Returns:
        Error responses
    """

    return (
        jsonify({"message": "Internal Server Error", "description": error.description}),
        500,
    )


def check_api_key() -> None:
    """
    Check if a valid API key was supplied in the request headers.

    If invalid or not specified when required, raise an error to make
    Flask return a `401 Unauthorized` response.
    """

    if "API_KEY" not in app.config or not app.config["API_KEY"]:
        return

    if "X-Api-Key" not in request.headers:
        raise Unauthorized(description="API key required but not provided")

    if request.headers["X-Api-Key"] != app.config["API_KEY"]:
        raise Unauthorized(description="Incorrect API key")


def check_initialised() -> None:
    """
    Check if the Dummy server has been initialised.

    If not, return a 500 Internal Server Error.
    """

    if app.config["API_SUPPORTS_INIT"] and not _is_initialized:
        raise InternalServerError()


@app.get("/initialize.json")
def get_initialize_json() -> Tuple[Response, int]:
    """
    Return the Dummy API access metadata.

    ```bash
    $ curl http://localhost:5000/initialize.json
    {"apiRoot":"/api/v1","apiKey":"1a2b3c4d5e","version":"0.1.0"}
    ```

    Returns:
        Dummy API access metadata
    """

    res = {"apiRoot": app.config["API_ROOT"]}

    if app.config.get("API_SUPPORTS_INIT"):
        res["initialized"] = _is_initialized

    if _is_initialized:
        if app.config["API_FORCE_AUTH"]:
            check_api_key()
        if app.config.get("API_KEY"):
            res["apiKey"] = app.config["API_KEY"]
        res["version"] = __version__

    return (jsonify(res), 200)


@app.post(f"{app.config['API_ROOT']}/init")
def init() -> Tuple[Response, int]:
    """
    Initialise the Dummy server.

    If successful, the 200 OK status code will be set,
    and the previous initialized status will be returned in the response.

     ```bash
    $ curl http://localhost:5000/api/v1/init
    {"initialized":false}
    ```

    If initialisation is configured to not be supported, return a 404 Not Found error.

    Returns:
        Dummy server status
    """

    global _is_initialized  # noqa: PLW0603

    if not app.config.get("API_SUPPORTS_INIT"):
        raise NotFound()

    _old_is_initialized = _is_initialized
    _is_initialized = True

    return (jsonify({"initialized": _old_is_initialized}), 200)


@app.get(f"{app.config['API_ROOT']}/status")
def get_status() -> Tuple[Response, int]:
    """
    Return the Dummy server current status.

     ```bash
    $ curl -H "X-Api-Key: 1a2b3c4d5e" http://localhost:5000/api/v1/status
    {"version":"0.4.0"}
    ```

    Returns:
        Dummy server status
    """

    check_api_key()
    check_initialised()

    return (jsonify({"version": __version__}), 200)


@app.get(f"{app.config['API_ROOT']}/settings")
def get_settings() -> Tuple[Response, int]:
    """
    Return the current Dummy server settings.

    ```bash
    $ curl -H "X-Api-Key: 1a2b3c4d5e" http://localhost:5000/api/v1/settings
    {"isUpdated":false,"trashValue":null}
    ```

    Returns:
        Current Dummy server settings
    """

    check_api_key()
    check_initialised()

    return (jsonify(_settings), 200)


@app.route(f"{app.config['API_ROOT']}/settings", methods=["POST", "PUT"])
def update_settings() -> Tuple[Response, int]:
    """
    Update the Dummy server settings, and return a copy of the old settings.
    When a settings update is performed, `isUpdated` will be set to `True`.

    Only updated configuration values need to be specified.

    ```bash
    $ curl -X PUT http://localhost:5000/api/v1/settings \
           -H "X-Api-Key: 1a2b3c4d5e" \
           -H "Content-Type: application/json" \
           -d '{"trashValue":2.0}'
    {"isUpdated":false,"trashValue":null}
    ```

    Subsequent requests to get the server settings will return updated values.

    ```bash
    $ curl -H "X-Api-Key: 1a2b3c4d5e" http://localhost:5000/api/v1/settings
    {"isUpdated":true,"trashValue":2.0}
    ```

    Updated settings will be lost when the server shuts down.

    Returns:
        Old Dummy server settings
    """

    global _settings  # noqa: PLW0603

    check_api_key()
    check_initialised()

    old_settings = _settings
    _settings = merge_dicts(old_settings, cast(Mapping, request.json), {"isUpdated": True})
    return (jsonify(old_settings), 201)


def merge_dicts(*dicts: Mapping[Any, Any]) -> Dict[Any, Any]:
    """
    Recursively merge the specificed mappings into one dictionary structure.

    If the same key exists at the same level in more than one mapping,
    the last referenced one takes prcedence.

    Returns:
        Merged dictionary
    """

    merged_dict: Dict[Any, Any] = {}

    for d in dicts:
        for key, value in d.items():
            if key in merged_dict and isinstance(merged_dict[key], Mapping):
                merged_dict[key] = merge_dicts(merged_dict[key], value)
            elif isinstance(value, Mapping):
                merged_dict[key] = merge_dicts(value)
            else:
                merged_dict[key] = value

    return merged_dict

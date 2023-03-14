# Copyright (C) 2023 Callum Dickinson
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
Dummy plugin API functions.
"""


from __future__ import annotations

import re

from http import HTTPStatus
from typing import TYPE_CHECKING

import json5  # type: ignore[import]
import requests

from buildarr.logging import plugin_logger
from buildarr.state import state

from .exceptions import DummyAPIError

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from .secrets import DummySecrets


INITIALIZE_JS_RES_PATTERN = re.compile(r"(?s)^window\.Dummy = ({.*});$")


def get_initialize_js(host_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the Dummy session initialisation metadata, including the API key.

    Args:
        host_url (str): Dummy instance URL.
        api_key (str): Dummy instance API key, if required. Defaults to `None`.

    Returns:
        Session initialisation metadata
    """

    url = f"{host_url}/initialize.js"
    plugin_logger.debug("GET %s", url)
    res = requests.get(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.config.buildarr.request_timeout,
    )
    res_match = re.match(INITIALIZE_JS_RES_PATTERN, res.text)
    if not res_match:
        raise RuntimeError(f"No matches for initialize.js parsing: {res.text}")
    res_json = json5.loads(res_match.group(1))
    plugin_logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    return res_json


def api_get(secrets: DummySecrets, api_url: str) -> Any:
    """
    Send a `GET` request to a Dummy instance.

    Args:
        secrets (DummySecrets): Dummy secrets metadata
        api_url (str): Dummy API command

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("GET %s", url)
    res = requests.get(
        url,
        headers={"X-Api-Key": secrets.api_key.get_secret_value()},
        timeout=state.config.buildarr.request_timeout,
    )
    res_json = res.json()
    plugin_logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.OK:
        api_error(method="GET", url=url, response=res)
    return res_json


def api_post(secrets: DummySecrets, api_url: str, req: Any) -> Any:
    """
    Send a `POST` request to a Dummy instance.

    Args:
        secrets (DummySecrets): Dummy secrets metadata
        api_url (str): Dummy API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("POST %s <- req=%s", url, repr(req))
    res = requests.post(
        url,
        headers={"X-Api-Key": secrets.api_key.get_secret_value()},
        json=req,
        timeout=state.config.buildarr.request_timeout,
    )
    res_json = res.json()
    plugin_logger.debug("POST %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.CREATED:
        api_error(method="POST", url=url, response=res)
    return res_json


def api_put(secrets: DummySecrets, api_url: str, req: Any) -> Any:
    """
    Send a `PUT` request to a Dummy instance.

    Args:
        secrets (DummySecrets): Dummy secrets metadata
        api_url (str): Dummy API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("PUT %s <- req=%s", url, repr(req))
    res = requests.put(
        url,
        headers={"X-Api-Key": secrets.api_key.get_secret_value()},
        json=req,
        timeout=state.config.buildarr.request_timeout,
    )
    res_json = res.json()
    plugin_logger.debug("PUT %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.ACCEPTED:
        api_error(method="PUT", url=url, response=res)
    return res_json


def api_delete(secrets: DummySecrets, api_url: str) -> None:
    """
    Send a `DELETE` request to a Dummy instance.

    Args:
        secrets (DummySecrets): Dummy secrets metadata
        api_url (str): Dummy API command
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("DELETE %s", url)
    res = requests.delete(
        url,
        headers={"X-Api-Key": secrets.api_key.get_secret_value()},
        timeout=state.config.buildarr.request_timeout,
    )
    plugin_logger.debug("DELETE %s -> status_code=%i", url, res.status_code)
    if res.status_code != HTTPStatus.OK:
        api_error(method="DELETE", url=url, response=res, parse_response=False)


def api_error(
    method: str,
    url: str,
    response: requests.Response,
    parse_response: bool = True,
) -> None:
    """
    Process an error response from the Dummy API.

    Args:
        method (str): HTTP method.
        url (str): API command URL.
        response (requests.Response): Response metadata.
        parse_response (bool, optional): Parse response error JSON. Defaults to True.

    Raises:
        Dummy API exception
    """

    error_message = (
        f"Unexpected response with status code {response.status_code} from from '{method} {url}'"
    )
    if parse_response:
        res_json = response.json()
        try:
            error_message += f": {res_json['message']}\n{res_json['description']}"
        except KeyError:
            error_message += f": {res_json}"
    raise DummyAPIError(error_message, response=response)

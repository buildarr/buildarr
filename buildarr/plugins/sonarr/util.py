# -*- coding: utf-8 -*-


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
Sonarr plugin utility functions.
"""


from __future__ import annotations

import re

from typing import TYPE_CHECKING

import json5  # type: ignore[import]
import requests

from pydantic import Field, SecretStr
from typing_extensions import Annotated

from buildarr.logging import plugin_logger

from .exceptions import SonarrAPIError

if TYPE_CHECKING:
    from typing import Any, Dict, Union

    from .secrets import SonarrSecrets


SonarrApiKey = Annotated[SecretStr, Field(min_length=32, max_length=32)]


def get_initialize_js(host_url: Union[SonarrSecrets, str]) -> Dict[str, Any]:
    """
    Get the Sonarr session initialisation metadata, including the API key.

    Args:
        host_url (Union[SonarrSecrets, str]): Sonarr instance URL (or secrets metadata)

    Returns:
        Session initialisation metadata
    """

    # Avoid circular imports.
    from .secrets import SonarrSecrets

    if isinstance(host_url, SonarrSecrets):
        base_url = host_url.host_url
        api_key = host_url.api_key.get_secret_value()
    else:
        base_url = host_url
        api_key = None
    url = f"{base_url}/initialize.js"
    plugin_logger.debug("GET %s", url)
    res = requests.get(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
    )
    res_match = re.match(r"(?s)^window\.Sonarr = ({.*});$", res.text)
    assert res_match
    res_json = json5.loads(res_match.group(1))
    plugin_logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    return res_json


def api_get(sonarr_secrets: SonarrSecrets, api_url: str) -> Any:
    """
    Send a `GET` request to a Sonarr instance.

    Args:
        sonarr_secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command

    Returns:
        Response object
    """

    url = f"{sonarr_secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("GET %s", url)
    res = requests.get(url, headers={"X-Api-Key": sonarr_secrets.api_key.get_secret_value()})
    res_json = res.json()
    plugin_logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != 200:
        api_error(method="GET", url=url, response=res)
    return res_json


def api_post(sonarr_secrets: SonarrSecrets, api_url: str, req: Any) -> Any:
    """
    Send a `POST` request to a Sonarr instance.

    Args:
        sonarr_secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{sonarr_secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("POST %s <- req=%s", url, repr(req))
    res = requests.post(
        url,
        headers={"X-Api-Key": sonarr_secrets.api_key.get_secret_value()},
        json=req,
    )
    res_json = res.json()
    plugin_logger.debug("POST %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != 201:
        api_error(method="POST", url=url, response=res)
    return res_json


def api_put(sonarr_secrets: SonarrSecrets, api_url: str, req: Any) -> Any:
    """
    Send a `PUT` request to a Sonarr instance.

    Args:
        sonarr_secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{sonarr_secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("PUT %s <- req=%s", url, repr(req))
    res = requests.put(
        url,
        headers={"X-Api-Key": sonarr_secrets.api_key.get_secret_value()},
        json=req,
    )
    res_json = res.json()
    plugin_logger.debug("PUT %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != 202:
        api_error(method="PUT", url=url, response=res)
    return res_json


def api_delete(sonarr_secrets: SonarrSecrets, api_url: str) -> None:
    """
    Send a `DELETE` request to a Sonarr instance.

    Args:
        sonarr_secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
    """

    url = f"{sonarr_secrets.host_url}/{api_url.lstrip('/')}"
    plugin_logger.debug("DELETE %s", url)
    res = requests.delete(url, headers={"X-Api-Key": sonarr_secrets.api_key.get_secret_value()})
    plugin_logger.debug("DELETE %s -> status_code=%i", url, res.status_code)
    if res.status_code != 200:
        api_error(method="DELETE", url=url, response=res, parse_response=False)


def api_error(
    method: str,
    url: str,
    response: requests.Response,
    parse_response: bool = True,
) -> None:
    """
    Process an error response from the Sonarr API.

    Args:
        method (str): HTTP method.
        url (str): API command URL.
        response (requests.Response): Response metadata.
        parse_response (bool, optional): Parse response error JSON. Defaults to True.

    Raises:
        Sonarr API exception
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
    raise SonarrAPIError(error_message, response=response)

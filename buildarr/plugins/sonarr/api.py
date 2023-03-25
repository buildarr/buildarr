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
Sonarr plugin API functions.
"""


from __future__ import annotations

import json
import re

from datetime import datetime, timezone
from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import json5  # type: ignore[import]
import requests

from buildarr.state import state

from .exceptions import SonarrAPIError

if TYPE_CHECKING:
    from typing import Any, Dict, Mapping, Optional

    from .secrets import SonarrSecrets


logger = getLogger(__name__)

INITIALIZE_JS_RES_PATTERN = re.compile(r"(?s)^window\.Sonarr = ({.*});$")


def get_initialize_js(host_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the Sonarr session initialisation metadata, including the API key.

    Args:
        host_url (str): Sonarr instance URL.
        api_key (str): Sonarr instance API key, if required. Defaults to `None`.

    Returns:
        Session initialisation metadata
    """

    url = f"{host_url}/initialize.js"
    logger.debug("GET %s", url)
    res = requests.get(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.config.buildarr.request_timeout,
    )
    res_match = re.match(INITIALIZE_JS_RES_PATTERN, res.text)
    if not res_match:
        raise RuntimeError(f"No matches for initialize.js parsing: {res.text}")
    res_json = json5.loads(res_match.group(1))
    logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    return res_json


def api_get(secrets: SonarrSecrets, api_url: str) -> Any:
    """
    Send a `GET` request to a Sonarr instance.

    Args:
        secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    logger.debug("GET %s", url)
    res = requests.get(
        url,
        headers={"X-Api-Key": secrets.api_key.get_secret_value()},
        timeout=state.config.buildarr.request_timeout,
    )
    res_json = res.json()
    logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.OK:
        api_error(method="GET", url=url, response=res)
    return res_json


def api_post(secrets: SonarrSecrets, api_url: str, req: Any) -> Any:
    """
    Send a `POST` request to a Sonarr instance.

    Args:
        secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    logger.debug("POST %s <- req=%s", url, repr(req))
    headers = {"X-Api-Key": secrets.api_key.get_secret_value()}
    if not state.dry_run:
        res = requests.post(
            url,
            headers=headers,
            json=req,
            timeout=state.config.buildarr.request_timeout,
        )
    else:
        res = _create_dryrun_response("POST", url, content=json.dumps(req))
    res_json = res.json()
    logger.debug("POST %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.CREATED:
        api_error(method="POST", url=url, response=res)
    return res_json


def api_put(secrets: SonarrSecrets, api_url: str, req: Any) -> Any:
    """
    Send a `PUT` request to a Sonarr instance.

    Args:
        secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
        req (Any): Request (JSON-serialisable)

    Returns:
        Response object
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    logger.debug("PUT %s <- req=%s", url, repr(req))
    headers = {"X-Api-Key": secrets.api_key.get_secret_value()}
    if not state.dry_run:
        res = requests.put(
            url,
            headers=headers,
            json=req,
            timeout=state.config.buildarr.request_timeout,
        )
    else:
        res = _create_dryrun_response("PUT", url, content=json.dumps(req))
    res_json = res.json()
    logger.debug("PUT %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))
    if res.status_code != HTTPStatus.ACCEPTED:
        api_error(method="PUT", url=url, response=res)
    return res_json


def api_delete(secrets: SonarrSecrets, api_url: str) -> None:
    """
    Send a `DELETE` request to a Sonarr instance.

    Args:
        secrets (SonarrSecrets): Sonarr secrets metadata
        api_url (str): Sonarr API command
    """

    url = f"{secrets.host_url}/{api_url.lstrip('/')}"
    logger.debug("DELETE %s", url)
    headers = {"X-Api-Key": secrets.api_key.get_secret_value()}
    res = (
        requests.delete(
            url,
            headers=headers,
            timeout=state.config.buildarr.request_timeout,
        )
        if not state.dry_run
        else _create_dryrun_response("DELETE", url)
    )
    logger.debug("DELETE %s -> status_code=%i", url, res.status_code)
    if res.status_code != HTTPStatus.OK:
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
        f"Unexpected response with status code {response.status_code} from from '{method} {url}':"
    )
    if parse_response:
        res_json = response.json()
        try:
            error_message += f" {_api_error(res_json)}"
        except TypeError:
            for error in res_json:
                error_message += f"\n{_api_error(error)}"
        except KeyError:
            error_message += f" {res_json}"
    raise SonarrAPIError(error_message, response=response)


def _api_error(res_json: Any) -> str:
    """
    Generate an error message from a response object.

    Args:
        res_json (Any): Response object

    Returns:
        String containing one or more error messages
    """

    try:
        try:
            error_message = f"{res_json['propertyName']}: {res_json['errorMessage']}"
            try:
                error_message += f" (attempted value: {res_json['attemptedValue']})"
            except KeyError:
                pass
            return error_message
        except KeyError:
            pass
        try:
            return f"{res_json['message']}\n{res_json['description']}"
        except KeyError:
            pass
        return res_json["message"]
    except KeyError:
        return f"(Unsupported error JSON format) {res_json}"


def _create_dryrun_response(
    method: str,
    url: str,
    headers: Optional[Mapping[str, str]] = None,
    status_code: Optional[int] = None,
    content_type: str = "application/json",
    charset: str = "utf-8",
    content: str = "{}",
) -> requests.Response:
    """
    A utility function for generating `requests.Response` objects in dry-run mode.

    Args:
        method (str): HTTP method of the response to simulate.
        url (str): URL of the request.
        status_code (Optional[int], optional): Status code for the response. Default: auto-detect
        content_type (str, optional): MIME type of response content. Default: `application/json`
        charset (str, optional): Encoding of response content. Default: `utf-8`
        content (str, optional): Response content. Default: `{}`

    Raises:
        ValueError: When an unsupported HTTP method is used

    Returns:
        Generated `requests.Response` object
    """

    method = method.upper()

    response = requests.Response()
    response.url = url
    response.headers["Vary"] = "Accept"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Content-Type"] = f"{content_type}; charset={charset}"
    response.headers["Server"] = "Mono-HTTPAPI/1.0"
    response.headers["Date"] = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")
    response.headers["Transfer-Encoding"] = "chunked"
    if headers:
        response.headers.update(headers)
    if status_code is not None:
        response.status_code = status_code
    elif method == "POST":
        response.status_code = int(HTTPStatus.CREATED)
    elif method == "PUT":
        response.status_code = int(HTTPStatus.ACCEPTED)
    elif method == "DELETE":
        response.status_code = int(HTTPStatus.OK)
    else:
        raise ValueError(
            f"Unsupported HTTP method for creating dry-run response: {str(method)}",
        )
    response.encoding = charset
    if content is not None:
        response._content = content.encode("UTF-8")

    return response

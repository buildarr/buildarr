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

import json
import re

from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import json5  # type: ignore[import]
import requests

from buildarr.state import state

from .exceptions import DummyAPIError

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Union

    from .secrets import DummySecrets


logger = getLogger(__name__)

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

    logger.debug("GET %s", url)

    res = requests.get(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.config.buildarr.request_timeout,
        allow_redirects=False,
    )

    if res.status_code != HTTPStatus.OK:
        logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, res.text)
        if res.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FOUND):
            status_code: int = HTTPStatus.UNAUTHORIZED
            error_message = "Unauthorized"
        else:
            status_code = res.status_code
            error_message = f"Unexpected response with error code {res.status_code}: {res.text}"
        raise DummyAPIError(
            f"Unable to retrieve 'initialize.js': {error_message}",
            status_code=status_code,
        )

    res_match = re.match(INITIALIZE_JS_RES_PATTERN, res.text)
    if not res_match:
        raise RuntimeError(f"No matches for 'initialize.js' parsing: {res.text}")
    res_json = json5.loads(res_match.group(1))

    logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    return res_json


def api_get(
    secrets: Union[DummySecrets, str],
    api_url: str,
    session: Optional[requests.Session] = None,
    use_api_key: bool = True,
    expected_status_code: HTTPStatus = HTTPStatus.OK,
) -> Any:
    """
    Send a `GET` request to a Dummy instance.

    Args:
        secrets (Union[DummySecrets, str]): Dummy secrets metadata, or host URL.
        api_url (str): Dummy API command.
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.

    Returns:
        Response object
    """

    if isinstance(secrets, str):
        host_url = secrets
        api_key = None
    else:
        host_url = secrets.host_url
        api_key = secrets.api_key.get_secret_value() if use_api_key else None
    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("GET %s", url)

    if not session:
        session = requests.Session()
    res = session.get(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.request_timeout,
    )
    res_json = res.json()

    logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="GET", url=url, response=res)

    return res_json


def api_post(
    secrets: Union[DummySecrets, str],
    api_url: str,
    req: Any = None,
    session: Optional[requests.Session] = None,
    use_api_key: bool = True,
    expected_status_code: HTTPStatus = HTTPStatus.CREATED,
) -> Any:
    """
    Send a `POST` request to a Dummy instance.

    Args:
        secrets (Union[DummySecrets, str]): Dummy secrets metadata, or host URL.
        api_url (str): Dummy API command.
        req (Any): Request (JSON-serialisable).
        expected_status_code (HTTPStatus): Expected response status. Defaults to `201 Created`.

    Returns:
        Response object
    """

    if isinstance(secrets, str):
        host_url = secrets
        api_key = None
    else:
        host_url = secrets.host_url
        api_key = secrets.api_key.get_secret_value() if use_api_key else None
    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("POST %s <- req=%s", url, repr(req))

    if not session:
        session = requests.Session()
    res = session.post(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.request_timeout,
        **({"json": req} if req is not None else {}),
    )
    res_json = res.json()

    logger.debug("POST %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="POST", url=url, response=res)

    return res_json


def api_put(
    secrets: Union[DummySecrets, str],
    api_url: str,
    req: Any,
    session: Optional[requests.Session] = None,
    use_api_key: bool = True,
    expected_status_code: HTTPStatus = HTTPStatus.OK,
) -> Any:
    """
    Send a `PUT` request to a Dummy instance.

    Args:
        secrets (Union[DummySecrets, str]): Dummy secrets metadata, or host URL.
        api_url (str): Dummy API command.
        req (Any): Request (JSON-serialisable).
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.

    Returns:
        Response object
    """

    if isinstance(secrets, str):
        host_url = secrets
        api_key = None
    else:
        host_url = secrets.host_url
        api_key = secrets.api_key.get_secret_value() if use_api_key else None
    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("PUT %s <- req=%s", url, repr(req))

    if not session:
        session = requests.Session()
    res = session.put(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        json=req,
        timeout=state.request_timeout,
    )
    res_json = res.json()

    logger.debug("PUT %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="PUT", url=url, response=res)

    return res_json


def api_delete(
    secrets: Union[DummySecrets, str],
    api_url: str,
    session: Optional[requests.Session] = None,
    use_api_key: bool = True,
    expected_status_code: HTTPStatus = HTTPStatus.OK,
) -> None:
    """
    Send a `DELETE` request to a Dummy instance.

    Args:
        secrets (Union[DummySecrets, str]): Dummy secrets metadata, or host URL.
        api_url (str): Dummy API command.
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.
    """

    if isinstance(secrets, str):
        host_url = secrets
        api_key = None
    else:
        host_url = secrets.host_url
        api_key = secrets.api_key.get_secret_value() if use_api_key else None
    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("DELETE %s", url)

    if not session:
        session = requests.Session()
    res = session.delete(
        url,
        headers={"X-Api-Key": api_key} if api_key else None,
        timeout=state.request_timeout,
    )

    logger.debug("DELETE %s -> status_code=%i", url, res.status_code)

    if res.status_code != expected_status_code:
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
        error_message += ": "
        try:
            res_json = response.json()
            try:
                error_message += f"{res_json['message']}\n{res_json['description']}"
            except KeyError:
                try:
                    error_message += res_json["message"]
                except KeyError:
                    try:
                        error_message += res_json["error"]
                    except KeyError:
                        error_message += f"(Unsupported error JSON format) {res_json}"
        except json.JSONDecodeError:
            f"(Non-JSON error response)\n{response.text}"

    raise DummyAPIError(error_message, status_code=response.status_code)

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
Dummy2 plugin API functions.
"""

from __future__ import annotations

import json

from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import requests

from buildarr.state import state

from .exceptions import Dummy2APIError

if TYPE_CHECKING:
    from typing import Any, Optional, Union

    from .secrets import Dummy2Secrets


logger = getLogger(__name__)


def api_get(
    secrets: Union[Dummy2Secrets, str],
    api_url: str,
    *,
    expected_status_code: HTTPStatus = HTTPStatus.OK,
    session: Optional[requests.Session] = None,
) -> Any:
    """
    Send an API `GET` request.

    Args:
        secrets (Union[Dummy2Secrets, str]): Secrets metadata, or host URL.
        api_url (str): API command.
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.

    Returns:
        Response object
    """

    host_url = secrets if isinstance(secrets, str) else secrets.host_url

    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("GET %s", url)

    if not session:
        session = requests.Session()
    res = session.get(url, timeout=state.request_timeout)
    try:
        res_json = res.json()
    except requests.JSONDecodeError:
        api_error(method="GET", url=url, response=res)

    logger.debug("GET %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="GET", url=url, response=res)

    return res_json


def api_post(
    secrets: Union[Dummy2Secrets, str],
    api_url: str,
    req: Any,
    *,
    session: Optional[requests.Session] = None,
    expected_status_code: HTTPStatus = HTTPStatus.CREATED,
) -> Any:
    """
    Send a `POST` request to a Sonarr instance.

    Args:
        secrets (Union[Dummy2Secrets, str]): Secrets metadata, or host URL.
        api_url (str): API command.
        req (Any): Request (JSON-serialisable).
        expected_status_code (HTTPStatus): Expected response status. Defaults to `201 Created`.

    Returns:
        Response object
    """

    host_url = secrets if isinstance(secrets, str) else secrets.host_url

    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("POST %s <- req=%s", url, repr(req))

    if not session:
        session = requests.Session()
    res = session.post(
        url,
        timeout=state.request_timeout,
        **({"json": req} if req is not None else {}),
    )
    try:
        res_json = res.json()
    except requests.JSONDecodeError:
        api_error(method="POST", url=url, response=res)

    logger.debug("POST %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="POST", url=url, response=res)

    return res_json


def api_put(
    secrets: Union[Dummy2Secrets, str],
    api_url: str,
    req: Any,
    *,
    session: Optional[requests.Session] = None,
    expected_status_code: HTTPStatus = HTTPStatus.ACCEPTED,
) -> Any:
    """
    Send a `PUT` request to a Sonarr instance.

    Args:
        secrets (Union[Dummy2Secrets, str]): Secrets metadata, or host URL.
        api_url (str): API command.
        req (Any): Request (JSON-serialisable).
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.

    Returns:
        Response object
    """

    host_url = secrets if isinstance(secrets, str) else secrets.host_url

    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("PUT %s <- req=%s", url, repr(req))

    if not session:
        session = requests.Session()
    res = session.put(
        url,
        json=req,
        timeout=state.request_timeout,
    )
    try:
        res_json = res.json()
    except requests.JSONDecodeError:
        api_error(method="PUT", url=url, response=res)

    logger.debug("PUT %s -> status_code=%i res=%s", url, res.status_code, repr(res_json))

    if res.status_code != expected_status_code:
        api_error(method="PUT", url=url, response=res)

    return res_json


def api_delete(
    secrets: Union[Dummy2Secrets, str],
    api_url: str,
    *,
    session: Optional[requests.Session] = None,
    expected_status_code: HTTPStatus = HTTPStatus.OK,
) -> None:
    """
    Send a `DELETE` request to a Sonarr instance.

    Args:
        secrets (Union[Dummy2Secrets, str]): Secrets metadata, or host URL.
        api_url (str): API command.
        expected_status_code (HTTPStatus): Expected response status. Defaults to `200 OK`.
    """

    host_url = secrets if isinstance(secrets, str) else secrets.host_url

    url = f"{host_url}/{api_url.lstrip('/')}"

    logger.debug("DELETE %s", url)

    if not session:
        session = requests.Session()
    res = session.delete(url, timeout=state.request_timeout)

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
    Process an error response from the Dummy2 API.

    Args:
        method (str): HTTP method.
        url (str): API command URL.
        response (requests.Response): Response metadata.
        parse_response (bool, optional): Parse response error JSON. Defaults to True.

    Raises:
        Dummy2 API exception
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
        except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
            f"(Non-JSON error response)\n{response.text}"

    raise Dummy2APIError(error_message, status_code=response.status_code)

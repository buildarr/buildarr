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
Sonarr plugin type hints.
"""


from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from typing import Literal, Optional

from pydantic import SecretStr
from requests import Response

SonarrProtocol = Literal["http", "https"]


class SonarrApiKey(SecretStr):
    """
    Constrained secret string type for a Sonarr API key.
    """

    min_length = 32
    max_length = 32


def create_dryrun_response(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    content_type: str = "application/json",
    charset: str = "utf-8",
    content: str = "{}",
) -> Response:
    """
    A utility class for generating `requests.Response` objects in dry-run mode.

    _extended_summary_

    Args:
        Response (_type_): _description_
    """

    response = Response()
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

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
Sonarr plugin secrets file model.
"""


from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from buildarr.secrets import SecretsPlugin
from buildarr.types import NonEmptyStr, Port

from .api import api_get, get_initialize_js
from .exceptions import SonarrAPIError
from .types import SonarrApiKey, SonarrProtocol

if TYPE_CHECKING:
    from typing_extensions import Self

    from .config import SonarrConfig

    class _SonarrSecrets(SecretsPlugin[SonarrConfig]):
        ...

else:

    class _SonarrSecrets(SecretsPlugin):
        ...


class SonarrSecrets(_SonarrSecrets):
    """
    Sonarr API secrets.
    """

    hostname: NonEmptyStr
    port: Port
    protocol: SonarrProtocol
    api_key: SonarrApiKey

    @property
    def host_url(self) -> str:
        return f"{self.protocol}://{self.hostname}:{self.port}"

    @classmethod
    def from_url(cls, base_url: str, api_key: str) -> Self:
        url_obj = urlparse(base_url)
        hostname_port = url_obj.netloc.rsplit(":", 1)
        hostname = hostname_port[0]
        protocol = url_obj.scheme
        port = (
            int(hostname_port[1])
            if len(hostname_port) > 1
            else (443 if protocol == "https" else 80)
        )
        return cls(hostname=hostname, port=port, protocol=protocol, api_key=api_key)

    @classmethod
    def get(cls, config: SonarrConfig) -> Self:
        return cls(
            hostname=config.hostname,
            port=config.port,
            protocol=config.protocol,
            api_key=(
                config.api_key if config.api_key else get_initialize_js(config.host_url)["apiKey"]
            ),
        )

    def test(self) -> bool:
        try:
            api_get(self, "/api/v3/system/status")
            return True
        except SonarrAPIError as err:
            if err.response.status_code == HTTPStatus.UNAUTHORIZED:
                return False
            else:
                raise

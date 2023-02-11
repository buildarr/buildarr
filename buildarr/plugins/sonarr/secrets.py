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
Sonarr plugin secrets file model.
"""


from __future__ import annotations

from urllib.parse import urlparse

from buildarr.config import ConfigPlugin, NonEmptyStr, Port
from buildarr.secrets import SecretsPlugin

from .util import SonarrApiKey, get_initialize_js


class SonarrSecrets(SecretsPlugin):
    """
    Sonarr API secrets.
    """

    hostname: NonEmptyStr
    port: Port
    protocol: NonEmptyStr

    api_key: SonarrApiKey

    @property
    def host_url(self) -> str:
        return f"{self.protocol}://{self.hostname}:{self.port}"

    @classmethod
    def from_url(cls, base_url: str, api_key: str) -> SonarrSecrets:
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
    def get(cls, config: ConfigPlugin) -> SonarrSecrets:
        return cls(
            hostname=config.hostname,
            port=config.port,
            protocol=config.protocol,
            api_key=(
                config.api_key  # type: ignore[attr-defined]
                if config.api_key  # type: ignore[attr-defined]
                else get_initialize_js(config.host_url)["apiKey"]
            ),
        )

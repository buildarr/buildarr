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
Dummy plugin secrets file model.
"""


from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from buildarr.config import NonEmptyStr, Port
from buildarr.secrets import SecretsPlugin

from .api import get_initialize_js
from .util import DummyApiKey, DummyProtocol

# Allow Mypy to properly resolve configuration type declarations in secrets classes.
if TYPE_CHECKING:
    from typing_extensions import Self

    from .config import DummyConfig

    class _DummySecrets(SecretsPlugin[DummyConfig]):
        ...

else:

    class _DummySecrets(SecretsPlugin):
        ...


class DummySecrets(_DummySecrets):
    """
    Dummy API secrets.
    """

    hostname: NonEmptyStr
    port: Port
    protocol: DummyProtocol

    api_key: DummyApiKey

    @property
    def host_url(self) -> str:
        """
        Full host URL for the Dummy instance.
        """
        return f"{self.protocol}://{self.hostname}:{self.port}"

    @classmethod
    def from_url(cls, host_url: str, api_key: str) -> Self:
        """
        Generate a secrets object from its constituent host URL and API key.

        Args:
            host_url (str): Full host URL of the instance
            api_key (str): API key used to authenticate with the instance

        Returns:
            Secrets object
        """
        url_obj = urlparse(host_url)
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
    def get(cls, config: DummyConfig) -> Self:
        """
        Generate a secrets object from the given instance configuration,
        retrieving any necessary secrets in the process.

        Args:
            config (DummyConfig): Instance configuration

        Returns:
            Secrets object
        """
        return cls(
            hostname=config.hostname,
            port=config.port,
            protocol=config.protocol,
            api_key=(
                config.api_key if config.api_key else get_initialize_js(config.host_url)["apiKey"]
            ),
        )

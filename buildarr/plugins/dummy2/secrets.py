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
Dummy2 plugin secrets file model.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

from buildarr.secrets import SecretsPlugin
from buildarr.types import NonEmptyStr, Port

from .api import api_get
from .exceptions import Dummy2APIError, Dummy2SecretsUnauthorizedError
from .types import Dummy2ApiKey, Dummy2Protocol

# Allow Mypy to properly resolve configuration type declarations in secrets classes.
if TYPE_CHECKING:
    from typing_extensions import Self

    from .config import Dummy2Config

    class _Dummy2Secrets(SecretsPlugin[Dummy2Config]):
        pass

else:

    class _Dummy2Secrets(SecretsPlugin):
        pass


class Dummy2Secrets(_Dummy2Secrets):
    """
    Dummy2 API secrets.
    """

    hostname: NonEmptyStr
    port: Port
    protocol: Dummy2Protocol
    api_key: Optional[Dummy2ApiKey]
    version: NonEmptyStr

    @property
    def host_url(self) -> str:
        """
        Full host URL for the Dummy2 instance.
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
    def get(cls, config: Dummy2Config) -> Self:
        """
        Generate a secrets object from the given instance configuration,
        retrieving any necessary secrets in the process.

        Args:
            config (Dummy2Config): Instance configuration

        Returns:
            Secrets object
        """
        try:
            initialize_json = api_get(
                config.host_url,
                "/initialize.json",
                api_key=config.api_key.get_secret_value() if config.api_key else None,
            )
            return cls(
                hostname=config.hostname,
                port=config.port,
                protocol=config.protocol,
                api_key=(config.api_key if config.api_key else initialize_json.get("apiKey")),
                version=initialize_json["version"],
            )
        except Dummy2APIError as err:
            if err.status_code == HTTPStatus.UNAUTHORIZED:
                if config.api_key:
                    raise Dummy2SecretsUnauthorizedError(
                        (
                            "Unable to authenticate with the Dummy2 instance "
                            f"at '{config.host_url}': Incorrect API key"
                        ),
                    ) from None
                else:
                    raise Dummy2SecretsUnauthorizedError(
                        (
                            "Unable to retrieve the API key for the Dummy2 instance "
                            f"at '{config.host_url}': Authentication is enabled"
                        ),
                    ) from None
            else:
                raise

    def test(self) -> bool:
        """
        Test whether or not the secrets metadata is valid for connecting to the instance.

        Returns:
            `True` if the test was successful, otherwise `False`
        """
        try:
            api_get(self, "/api/v1/status")
            return True
        except Dummy2APIError as err:
            if err.status_code == HTTPStatus.UNAUTHORIZED:
                return False
            else:
                raise

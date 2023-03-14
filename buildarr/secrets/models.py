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
Buildarr plugin secrets metadata models.
"""


from __future__ import annotations

from typing import TYPE_CHECKING

from ..plugins import Config
from .base import SecretsBase

if TYPE_CHECKING:
    from typing import Dict

    from typing_extensions import Self


__all__ = ["SecretsPlugin"]


class SecretsPlugin(SecretsBase[Config]):
    """
    Buildarr plugin secrets metadata base class.

    The metadata stored in this object will be grouped with
    other instances' secrets metadata and stored unencrypted
    in a single secrets JSON file. This file should be stored
    in a secured directory where only the user that runs Buildarr
    has access.

    The secrets plugin is a Pydantic model, so
    class attributes and type hints are used to specify
    configuration field names and how they should be parsed.

    ```python
    from typing import TYPE_CHECKING, Literal
    from buildarr.secrets import SecretsPlugin
    from buildarr.types import NonEmptyStr, Port, Password

    if TYPE_CHECKING:
        from typing import Self
        from  .config import ExampleConfig
        class _ExampleSecrets(SecretsPlugin[ExampleConfig]):
            ...
    else:
        class _ExampleSecrets(SecretsPlugin):
            ...

    class ExampleSecrets(_ExampleSecrets):
        hostname: NonEmptyStr
        port: Port
        protocol: Literal["http", "https"]
        username: NonEmptyStr
        password: Password

        @classmethod
        def get(cls, config: ExampleConfig) -> Self:
            return cls(
                hostname=config.hostname,
                port=config.port,
                protocol=config.protocol,
                username=config.username,
                password=config.password,
            )
    ```
    """

    @classmethod
    def get(cls, config: Config) -> Self:
        """
        Generate the secrets metadata for the given instance-specific configuration.

        This class method must be overloaded and implemented.

        Args:
            config (Config): Instance-specific configuration

        Returns:
            Secrets metadata object for the instance
        """
        raise NotImplementedError()

    def test(self) -> bool:
        """
        Test whether or not the secrets metadata is valid for connecting to the instance.

        This method should be implemented by sending a lightweight `GET` request
        that requires authentication to the instance.

        Returns:
            `True` if the test was successful, otherwise `False`
        """
        raise NotImplementedError()


class SecretsType(SecretsBase):
    """
    Type hint for interacting with a dynamically generated secrets metadata model.
    """

    def __getattr__(self, name: str) -> Dict[str, SecretsPlugin]:
        """
        Plugin-specific secrets metadata.
        """
        raise NotImplementedError()

    def __setattr__(self, name: str, value: Dict[str, SecretsPlugin]) -> None:
        """
        Plugin-specific secrets metadata.
        """
        raise NotImplementedError()

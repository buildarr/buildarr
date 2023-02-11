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
Buildarr secrets file handling interface.
"""


from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Type

from pydantic import BaseModel, ConstrainedStr, SecretStr, create_model

from .logging import logger
from .state import plugins

if TYPE_CHECKING:
    from typing import Set

    from .config import ConfigPlugin


class NonEmptyStr(ConstrainedStr):
    """
    Constrained string type for non-empty strings.

    When validated in a Buildarr secrets object, empty strings
    or strings composed only of whitespace will fail validation.
    """

    min_length = 1
    strip_whitespace = True


class SecretsBase(BaseModel):
    """
    Secrets configuration section base class.

    When implementing nested sections in a secrets plugin, this class should be used.
    """

    pass


class SecretsPlugin(SecretsBase):
    """
    Buildarr plugin secrets metadata object base class.

    The metadata stored in this object will be grouped with
    other instances' secrets metadata and stored unencrypted
    in a single secrets JSON file. This file should be stored
    in a secured directory where only the user that runs Buildarr
    has access.

    The secrets plugin is a Pydantic model, so
    class attributes and type hints are used to specify
    configuration field names and how they should be parsed.

    ```python
    from typing import Literal
    from buildarr.config import NonEmptyStr, Port, Password
    from buildarr.secrets import SecretsPlugin

    class ExampleSecrets(SecretsPlugin):
        hostname: NonEmptyStr
        port: Port
        protocol: Literal["http", "https"]
        username: NonEmptyStr
        password: Password
    ```
    """

    @classmethod
    def get(cls, config: ConfigPlugin) -> SecretsPlugin:
        """
        Generate the secrets metadata for the given instance-specific configuration.

        This class method must be overloaded and implemented.

        Args:
            config (ConfigPlugin): Instance-specific configuration

        Returns:
            Secrets metadata object for the instance
        """
        raise NotImplementedError()


class SecretsImpl(SecretsBase):
    """
    Base class used internally to dynamically generate the secrets metadata model.
    """

    @classmethod
    def read(cls, path: Path) -> SecretsImpl:
        """
        Load the secrets metadata from a JSON file, and return the corresponding object.

        Args:
            path (Path): Secrets JSON file to read from

        Returns:
            Secrets metadata object
        """
        return cls.parse_file(path, content_type="json")

    def write(self, path: Path) -> None:
        """
        Serialise the secrets metadata object and write it to a JSON file.

        Args:
            path (Path): Secrets JSON file to write to
        """
        path.write_text(self.json())

    class Config:
        json_encoders = {SecretStr: lambda v: v.get_secret_value()}


def get_model(use_plugins: Set[str] = set()) -> Type[SecretsImpl]:
    """
    Create the secrets file model using the specified plugins.

    Args:
        load_plugins (Set[str], optional): Plugins to use. Use all if empty.

    Returns:
        Dynamically generated secrets file model
    """

    logger.debug("Creating secrets model")
    model = create_model(
        "Secrets",
        **{
            plugin_name: (
                Dict[NonEmptyStr, plugin.secrets],  # type: ignore
                {},
            )
            for plugin_name, plugin in plugins.items()
            if not use_plugins or plugin_name in use_plugins
        },
        __base__=SecretsImpl,
    )
    logger.debug("Finished creating secrets model")

    return model

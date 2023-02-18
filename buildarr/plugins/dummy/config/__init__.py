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
Dummy plugin configuration.
"""


from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from typing_extensions import Self

from buildarr.config import ConfigPlugin, NonEmptyStr, Port

from ..api import get_initialize_js
from ..secrets import DummySecrets
from ..util import DummyApiKey, DummyProtocol
from .settings import DummySettingsConfig

# Allow Mypy to properly resolve secrets type declarations in configuration classes.
if TYPE_CHECKING:

    class _DummyInstanceConfig(ConfigPlugin[DummySecrets]):
        ...

else:

    class _DummyInstanceConfig(ConfigPlugin):
        ...


class DummyInstanceConfig(_DummyInstanceConfig):
    """
    By default, Buildarr will look for a single instance at `http://dummy:5000`.
    Most configurations are different, and to accommodate those, you can configure
    how Buildarr connects to individual Dummy instances.

    Configuration of a single Dummy instance:

    ```yaml
    dummy:
      hostname: "localhost"
      port: 5000
      protocol: "http"
      settings:
        ...
    ```

    Configuration of multiple instances:

    ```yaml
    dummy:
      # Configuration and settings common to all instances.
      hostname: "localhost"
      protocol: "http"
      settings:
        ...
      instances:
        # Dummy instance 1-specific configuration.
        dummy1:
          port: 5000
          settings:
            ...
        # Dummy instance 2-specific configuration.
        dummy:
          port: 5001
          api_key: "..." # Explicitly define API key
          settings:
            ...
    ```
    """

    hostname: NonEmptyStr = "dummy"  # type: ignore[assignment]
    """
    Hostname of the Dummy instance to connect to.

    When defining a single instance using the global `dummy` configuration block,
    the default hostname is `dummy`.

    When using multiple instance-specific configurations, the default hostname
    is the name given to the instance in the `instances` attribute.

    ```yaml
    dummy:
      instances:
        dummy1: # <--- This becomes the default hostname
          ...
    ```
    """

    port: Port = 5000  # type: ignore[assignment]
    """
    Port number of the Dummy instance to connect to.
    """

    protocol: DummyProtocol = "http"  # type: ignore[assignment]
    """
    Communication protocol to use to connect to Dummy.

    Values:

    * `http`
    """

    api_key: Optional[DummyApiKey] = None
    """
    API key to use to authenticate with the Dummy instance.

    If undefined or set to `None`, automatically retrieve the API key.
    This can only be done on Dummy instances with authentication disabled.
    """

    version: Optional[str] = None
    """
    The expected version of the Dummy instance.
    If undefined or set to `None`, the version is auto-detected.

    At the moment this attribute is unused, and there is likely no need to explicitly set it.
    """

    settings: DummySettingsConfig = DummySettingsConfig()
    """
    Dummy settings.
    Configuration options for Dummy itself are set within this structure.
    """

    @property
    def uses_trash_metadata(self) -> bool:
        """
        A flag determining whether or not this instance configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return self.settings.uses_trash_metadata

    def render_trash_metadata(self, trash_metadata_dir: Path) -> Self:
        """
        Read TRaSH-Guides metadata, and return a configuration object with all templates rendered.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.

        Returns:
            Rendered configuration object
        """
        copy = self.copy(deep=True)
        copy._render_trash_metadata(trash_metadata_dir)
        return copy

    def _render_trash_metadata(self, trash_metadata_dir: Path) -> None:
        """
        Render configuration attributes obtained from TRaSH-Guides, in-place.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.
        """
        if self.settings.uses_trash_metadata:
            self.settings._render_trash_metadata(trash_metadata_dir)

    @classmethod
    def from_remote(cls, secrets: DummySecrets) -> Self:
        """
        Read configuration from a remote instance and return it as a configuration object.

        Args:
            secrets (DummySecrets): Instance host and secrets information

        Returns:
            Configuration object for remote instance
        """
        return cls(
            hostname=secrets.hostname,
            port=secrets.port,
            protocol=secrets.protocol,
            api_key=secrets.api_key,
            version=get_initialize_js(
                host_url=secrets.host_url,
                api_key=secrets.api_key.get_secret_value(),
            )["version"],
            settings=DummySettingsConfig.from_remote(secrets),
        )


class DummyConfig(DummyInstanceConfig):
    """
    Dummy plugin global configuration class.

    Subclasses the instance-specific configuration to allow
    attributes common to all instances to be defined in one place.
    """

    instances: Dict[str, DummyInstanceConfig] = {}
    """
    Instance-specific Dummy configuration.

    Can only be defined on the global `dummy` configuration block.

    Globally specified configuration values apply to all instances.
    Configuration values specified on an instance-level take precedence at runtime.
    """

    @property
    def uses_trash_metadata(self) -> bool:
        """
        A flag determining whether or not this configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        for instance in self.instances.values():
            if instance.uses_trash_metadata:
                return True
        return super().uses_trash_metadata

    def render_trash_metadata(self, trash_metadata_dir: Path) -> Self:
        """
        Read TRaSH-Guides metadata, and return a configuration object with all templates rendered.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.

        Returns:
            Rendered configuration object
        """
        copy = self.copy(deep=True)
        for instance in copy.instances.values():
            if instance.uses_trash_metadata:
                instance._render_trash_metadata(trash_metadata_dir)
        if self.uses_trash_metadata:
            copy._render_trash_metadata(trash_metadata_dir)
        return copy

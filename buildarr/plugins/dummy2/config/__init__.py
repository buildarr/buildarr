# Copyright (C) 2024 Callum Dickinson
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
Dummy2 plugin configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from typing_extensions import Self

from buildarr.config import ConfigPlugin
from buildarr.types import LocalPath, NonEmptyStr, Port

from ..types import Dummy2Protocol
from .settings import Dummy2SettingsConfig

if TYPE_CHECKING:
    from ..secrets import Dummy2Secrets


class Dummy2InstanceConfig(ConfigPlugin["Dummy2Secrets"]):
    """
    By default, Buildarr will look for a single instance at `http://dummy2:5000`.
    Most configurations are different, and to accommodate those, you can configure
    how Buildarr connects to individual Dummy2 instances.

    Configuration of a single Dummy2 instance:

    ```yaml
    dummy2:
      hostname: "localhost"
      port: 5000
      protocol: "http"
      settings:
        ...
    ```

    Configuration of multiple instances:

    ```yaml
    dummy2:
      # Configuration and settings common to all instances.
      hostname: "localhost"
      protocol: "http"
      settings:
        ...
      instances:
        # Dummy2 instance 1-specific configuration.
        dummy2-1:
          port: 5000
          settings:
            ...
        # Dummy2 instance 2-specific configuration.
        dummy2-2:
          port: 5001
          settings:
            ...
    ```
    """

    hostname: NonEmptyStr = "dummy2"
    """
    Hostname of the Dummy2 instance to connect to.

    When defining a single instance using the global `dummy2` configuration block,
    the default hostname is `dummy2`.

    When using multiple instance-specific configurations, the default hostname
    is the name given to the instance in the `instances` attribute.

    ```yaml
    dummy2:
      instances:
        dummy2-1: # <--- This becomes the default hostname
          ...
    ```
    """

    port: Port = 5000
    """
    Port number of the Dummy2 instance to connect to.
    """

    protocol: Dummy2Protocol = "http"
    """
    Communication protocol to use to connect to Dummy2.

    Values:

    * `http`
    """

    version: Optional[str] = None
    """
    The expected version of the Dummy2 instance.
    If undefined or set to `None`, the version is auto-detected.

    At the moment this attribute is unused, and there is likely no need to explicitly set it.
    """

    settings: Dummy2SettingsConfig = Dummy2SettingsConfig()
    """
    Dummy2 settings.
    Configuration options for Dummy2 itself are set within this structure.
    """

    local_path: LocalPath = LocalPath("test.yml")
    """
    Local path. Used for testing the type in functional testing.
    """

    optional_local_path: Optional[LocalPath] = None
    """
    Optional local path. Used for testing the type in functional testing.
    """

    @classmethod
    def from_remote(cls, secrets: Dummy2Secrets) -> Self:
        """
        Read configuration from a remote instance and return it as a configuration object.

        Args:
            secrets (DummySecrets): Instance host and secrets information

        Returns:
            Configuration object for remote instance
        """
        return cls(
            **{key: value for key, value in secrets},
            settings=Dummy2SettingsConfig.from_remote(secrets),
        )


class Dummy2Config(Dummy2InstanceConfig):
    """
    Dummy2 plugin global configuration class.

    Subclasses the instance-specific configuration to allow
    attributes common to all instances to be defined in one place.
    """

    instances: Dict[str, Dummy2InstanceConfig] = {}
    """
    Instance-specific Dummy2 configuration.

    Can only be defined on the global `dummy2` configuration block.

    Globally specified configuration values apply to all instances.
    Configuration values specified on an instance-level take precedence at runtime.
    """

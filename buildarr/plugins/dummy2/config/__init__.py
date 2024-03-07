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

from http import HTTPStatus
from typing import TYPE_CHECKING, Dict, Optional

from typing_extensions import Self

from buildarr.config import ConfigPlugin
from buildarr.types import NonEmptyStr, Port

from ..api import api_get, api_post
from ..exceptions import Dummy2APIError
from ..secrets import Dummy2Secrets
from ..types import Dummy2ApiKey, Dummy2Protocol
from .settings import Dummy2SettingsConfig

# Allow Mypy to properly resolve secrets type declarations in configuration classes.
if TYPE_CHECKING:

    class _Dummy2InstanceConfig(ConfigPlugin[Dummy2Secrets]): ...

else:

    class _Dummy2InstanceConfig(ConfigPlugin): ...


class Dummy2InstanceConfig(_Dummy2InstanceConfig):
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
          api_key: "..." # Explicitly define API key
          settings:
            ...
    ```
    """

    hostname: NonEmptyStr = "dummy2"  # type: ignore[assignment]
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

    port: Port = 5000  # type: ignore[assignment]
    """
    Port number of the Dummy2 instance to connect to.
    """

    protocol: Dummy2Protocol = "http"  # type: ignore[assignment]
    """
    Communication protocol to use to connect to Dummy2.

    Values:

    * `http`
    """

    api_key: Optional[Dummy2ApiKey] = None
    """
    API key to use to authenticate with the Dummy2 instance.

    If undefined or set to `None`, automatically retrieve the API key.
    This can only be done on Dummy2 instances with authentication disabled.
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

    def uses_trash_metadata(self) -> bool:
        """
        Return whether or not this instance configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return self.settings.uses_trash_metadata()

    def render(self) -> Self:
        """
        Render dynamic configuration attributes, and return the resulting configuration object.

        Returns:
            Rendered configuration object
        """
        if not self.settings.uses_trash_metadata():
            return self
        copy = self.copy(deep=True)
        copy._render()
        return copy

    def _render(self) -> None:
        """
        Render dynamic configuration attributes in place.
        """
        self.settings._render()

    def is_initialized(self) -> bool:
        """
        Return whether or not this instance needs to be initialised.

        This function runs after the instance configuration has been rendered,
        but before secrets are fetched.

        Configuration plugins should implement this function if initialisation is required
        for the application's API to become available.

        Returns:
            `True` if the instance is initialised, otherwise `False`

        Raises:
            NotImplementedError: When initialisation is not supported for the application type.
        """
        try:
            initialize_json = api_get(self.host_url, "/initialize.json")
            if "initialized" in initialize_json:
                return initialize_json["initialized"]
            else:
                raise NotImplementedError()
        except Dummy2APIError as err:
            if err.status_code == HTTPStatus.UNAUTHORIZED:
                return True
            else:
                raise

    def initialize(self, tree: str) -> None:
        """
        Initialise the instance, and make the main application API available for Buildarr
        to query against.

        This function runs after the instance configuration has been rendered,
        but before secrets are fetched.

        Configuration plugins should implement this function if initialisation is required
        for the application's API to become available.

        Args:
            tree (str): Configuration tree this instance falls under (for logging purposes).

        Raises:
            NotImplementedError: When initialisation is not supported for the application type.
        """
        try:
            api_post(
                self.host_url,
                "/api/v1/init",
                None,
                api_key=self.api_key.get_secret_value() if self.api_key else None,
                expected_status_code=HTTPStatus.OK,
            )
        except Dummy2APIError as err:
            if err.status_code == HTTPStatus.NOT_FOUND:
                raise NotImplementedError() from None
            else:
                raise

    @classmethod
    def from_remote(cls, secrets: Dummy2Secrets) -> Self:
        """
        Read configuration from a remote instance and return it as a configuration object.

        Args:
            secrets (Dummy2Secrets): Instance host and secrets information

        Returns:
            Configuration object for remote instance
        """
        return cls(
            hostname=secrets.hostname,
            port=secrets.port,
            protocol=secrets.protocol,
            api_key=secrets.api_key,
            version=secrets.version,
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

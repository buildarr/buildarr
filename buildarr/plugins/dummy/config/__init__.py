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

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional

from typing_extensions import Self

from buildarr import __version__
from buildarr.config import ConfigPlugin
from buildarr.state import state
from buildarr.types import NonEmptyStr, Port

from ..api import api_get, api_post
from ..exceptions import DummyAPIError
from ..secrets import DummySecrets
from ..types import DummyApiKey, DummyProtocol
from .settings import DummySettingsConfig

# Allow Mypy to properly resolve secrets type declarations in configuration classes.
if TYPE_CHECKING:

    class _DummyInstanceConfig(ConfigPlugin[DummySecrets]): ...

else:

    class _DummyInstanceConfig(ConfigPlugin): ...


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

    url_base: Optional[str] = None
    """
    The URL path the Dummy instance API is available under, if behind a reverse proxy.

    API URLs are rendered like this: `<protocol>://<hostname>:<port><url_base>/api/v3/...`

    When unset, the URL root will be used as the API endpoint
    (e.g. `<protocol>://<hostname>:<port>/api/v1/...`).
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

    use_service_volumes: bool = False
    """
    Whether or not to configure volumes when generating the Docker Compose service definition.

    Used in functional tests.
    """

    service_volumes_type: Literal[
        "dict",
        "list-tuple",
        "list-dict",
        "list-tuple-invalid",
    ] = "list-dict"
    """
    The type to use for the service volumes when generating the Docker Compose service definition.

    Used in functional tests.
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
        except DummyAPIError as err:
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
        except DummyAPIError as err:
            if err.status_code == HTTPStatus.NOT_FOUND:
                raise NotImplementedError() from None
            else:
                raise

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
            **{key: value for key, value in secrets},
            settings=DummySettingsConfig.from_remote(secrets),
        )

    def to_compose_service(self, compose_version: str, service_name: str) -> Dict[str, Any]:
        """
        Generate a Docker Compose service definition corresponding to this instance configuration.

        Plugins should implement this function to allow Docker Compose files to be generated from
        Buildarr configuration using the `buildarr compose` command.

        Args:
            compose_version (str): Version of the Docker Compose file.
            service_name (str): The unique name for the generated Docker Compose service.

        Returns:
            Docker Compose service definition dictionary
        """
        service: Dict[str, Any] = {
            "image": f"{state.config.buildarr.docker_image_uri}:{__version__}",
            "entrypoint": ["flask"],
            "command": ["--app", "buildarr.plugins.dummy.server:app", "run", "--debug"],
        }
        if self.use_service_volumes:
            if self.service_volumes_type == "list-dict":
                service["volumes"] = [
                    {
                        "type": "bind",
                        "source": str(state.config_files[0].parent),
                        "target": "/config",
                        "read_only": True,
                    },
                    {
                        "type": "volume",
                        "source": service_name,
                        "target": "/data",
                        "read_only": False,
                    },
                ]
            elif self.service_volumes_type == "list-tuple":
                service["volumes"] = [
                    (str(state.config_files[0].parent), "/config", ["ro"]),
                    (service_name, "/data"),
                ]
            elif self.service_volumes_type == "list-tuple-invalid":
                service["volumes"] = [
                    (str(state.config_files[0].parent), "/config", ["ro"], "invalid"),
                    (service_name),
                ]
            else:
                service["volumes"] = {
                    str(state.config_files[0].parent): "/config",
                    service_name: "/data",
                }
        return service


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

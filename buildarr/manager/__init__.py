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
Buildarr manager interface.
"""


from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Generic

from ..plugins import Config, Secrets
from ..state import state

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Set


logger = getLogger(__name__)


class ManagerPlugin(Generic[Config, Secrets]):
    """
    Buildarr plugin manager object base class.

    This class contains functions used by the Buildarr main routine to
    interact with a plugin's configuration and secrets interfaces.

    In most cases these do not need to be modified and plugins can
    subclass the default `ManagerPlugin` interface without any issues, but all
    hooks can be overloaded and reimplemented if desired.

    `ManagerPlugin` is a generic interface, so to create the manager class
    for your plugin, create a class with `ManagerPlugin` as the superclass,
    with the configuration and secrets classes for your plugin passed into
    the appropriate type parameters.

    ```python
    from buildarr.manager import ManagerPlugin
    from .config import ExampleConfig
    from .secrets import ExampleSecrets

    class ExampleManager(ManagerPlugin[ExampleConfig, ExampleSecrets]):
        pass
    ```

    If your plugin has distinct classes for global configuration and
    instance-specific configuration (e.g. `ExampleConfig` and `ExampleInstanceConfig`),
    pass `ExampleInstanceConfig` to `ExampleManager`.
    """

    def get_instance_config(self, config: Config, instance_name: str) -> Config:
        """
        Combine explicitly defined instance-local and global configuration,
        and return a fully qualified instance-specific plugin configuration object.

        Args:
            config (Config): Configuration object to read.
            instance_name (str): Name of the instance to get the configuration of.

        Returns:
            Fully qualified instance-specific configuration object
        """
        return config.get_instance_config(instance_name)

    def uses_trash_metadata(self, instance_config: Config) -> bool:
        """
        Returns whether or not the given instance configuration uses TRaSH-Guides metadata.

        Args:
            instance_config (Config): Instance configuration object to check.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return instance_config.uses_trash_metadata()

    def render(self, instance_config: Config) -> Config:
        """
        Render dynamically populated attributes on the given instance configuration.

        If the instance configuration returned `True` for `uses_trash_metadata`,
        the filepath to the downloaded metadata directory will be available as
        `state.trash_metadata_dir` in the global state.

        Args:
            instance_config (Config): Instance configuration object to render.

        Returns:
            Rendered configuration object
        """
        return instance_config.render()

    def is_initialized(self, instance_config: Config) -> bool:
        """
        Return whether or not this instance needs to be initialised.

        This function runs after the instance configuration has been rendered,
        but before secrets are fetched.

        Args:
            instance_config (Config): Instance configuration object to initialise.

        Raises:
            NotImplementedError: When initialisation is not required for the application type.

        Returns:
            `True` if the instance is initialised, otherwise `False`
        """
        return instance_config.is_initialized()

    def initialize(self, tree: str, instance_config: Config) -> None:
        """
        Initialise the instance, and make the main application API available for Buildarr
        to query against.

        This function runs after the instance configuration has been rendered,
        but before secrets are fetched.

        Args:
            tree (str): Configuration tree this instance falls under (for logging purposes).
            instance_config (Config): Instance configuration object to initialise.
        """
        instance_config.initialize(tree)

    def from_remote(self, instance_config: Config, secrets: Secrets) -> Config:
        """
        Get the active configuration for a remote instance, and return the resulting object.

        Args:
            instance_config (Config): Configuration object of the instance to connect to.
            secrets (Secrets): Remote instance host and secrets information.

        Returns:
            Remote instance configuration object
        """
        return instance_config.from_remote(secrets)

    def update_remote(
        self,
        tree: str,
        local_instance_config: Config,
        secrets: Secrets,
        remote_instance_config: Config,
    ) -> bool:
        """
        Compare the local configuration to a remote instance, and update the remote to match.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            local_instance_config (Config): Local instance configuration to compare to the remote.
            secrets (Secrets): Remote instance host and secrets information.
            remote_instance_config (Config): Currently active remote instance configuration.

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        return local_instance_config.update_remote(
            tree=tree,
            secrets=secrets,
            remote=remote_instance_config,
        )

    def delete_remote(
        self,
        tree: str,
        local_instance_config: Config,
        secrets: Secrets,
        remote_instance_config: Config,
    ) -> bool:
        """
        Compare the local configuration to a remote instance, and delete any resources
        that are unmanaged or unused on the remote, and allowed to be deleted.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            local_instance_config (Config): Local instance configuration to compare to the remote.
            secrets (Secrets): Remote instance host and secrets information.
            remote_instance_config (Config): Currently active remote instance configuration.

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        return local_instance_config.delete_remote(
            tree=tree,
            secrets=secrets,
            remote=remote_instance_config,
        )

    def to_compose_service(
        self,
        instance_config: Config,
        compose_version: str,
        service_name: str,
    ) -> Dict[str, Any]:
        """
        Generate a Docker Compose service definition corresponding to this instance configuration.

        Args:
            instance_config (Config): Instance configuration to generate a service for.
            compose_version (str): Version of the Docker Compose file.
            service_name (str): The unique name for the generated Docker Compose service.

        Returns:
            Docker Compose service definition dictionary
        """
        return instance_config.to_compose_service(
            compose_version=compose_version,
            service_name=service_name,
        )


def load_managers(use_plugins: Optional[Set[str]] = None) -> None:
    """
    Load the managers for each plugin to be used in this Buildarr run.

    Args:
        use_plugins (Optional[Set[str]]): Plugins to use. Default is to use all plugins.
    """

    managers: Dict[str, ManagerPlugin] = {}

    for plugin_name, plugin in state.plugins.items():
        if use_plugins and plugin_name not in use_plugins:
            continue
        if plugin_name not in state.config.__fields_set__:
            continue
        with state._with_context(plugin_name=plugin_name):
            logger.debug("Loading plugin manager")
            managers[plugin_name] = plugin.manager()
            logger.debug("Finished loading plugin manager")

    state.managers = managers

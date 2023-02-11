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
Buildarr manager interface functions.
"""


from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar

from ..config import ConfigPlugin
from ..secrets import SecretsPlugin

Config = TypeVar("Config", bound=ConfigPlugin)
Secrets = TypeVar("Secrets", bound=SecretsPlugin)


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
    from buildarr_example.config import ExampleConfig
    from buildarr_example.secrets import ExampleSecrets

    class ExampleManager(ManagerPlugin[ExampleConfig, ExampleSecrets]):
        pass
    ```
    """

    def uses_trash_metadata(self, config: Config) -> bool:
        """
        Returns whether or not the given configuration uses TRaSH-Guides metadata.

        Args:
            config (Config): Configuration object to check

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return config.uses_trash_metadata

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

    def render_trash_metadata(self, config: Config, trash_metadata_dir: Path) -> Config:
        """
        Read TRaSH-Guides metadata, and return a configuration object with all templates rendered.

        Args:
            config (Config): Configuration object to read.
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.

        Returns:
            Rendered configuration object
        """
        return config.render_trash_metadata(trash_metadata_dir)

    def from_remote(self, config: Config, secrets: Secrets) -> Config:
        """
        Get the remote instance configuration for this section, and return the resulting object.

        Args:
            config (Config): Configuration object to read.
            secrets (Secrets): Remote instance host and secrets information.

        Returns:
            Remote instance configuration object
        """
        return config.from_remote(secrets)

    def update_remote(
        self,
        tree: str,
        local_config: Config,
        secrets: Secrets,
        remote_config: Config,
    ) -> bool:
        """
        Compare this configuration to a remote instance's, and update the remote to match.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            local_config (Config): Local instance configuration to use when updating the remote.
            secrets (Secrets): Remote instance host and secrets information.
            remote_config (Config): Currently active remote instance configuration.

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        return local_config.update_remote(tree, secrets, remote_config)

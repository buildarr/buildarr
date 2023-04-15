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
Buildarr global runtime state.
"""


from __future__ import annotations

import os

from collections import defaultdict
from contextlib import contextmanager
from distutils.util import strtobool
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from typing import DefaultDict, FrozenSet, Generator, Mapping, Optional, Sequence, Set

    from .config import ConfigPlugin, ConfigType
    from .manager import ManagerPlugin
    from .plugins import Plugin
    from .secrets import SecretsPlugin, SecretsType


__all__ = ["state"]

PluginInstanceRef = Tuple[str, str]
"""
A type for plugin-instance references as used in Buildarr internal state.

The first string in the tuple is the plugin name, and the second string is the instance name.
"""


class State:
    """
    Active Buildarr state tracking class.

    If anything needs to be shared between plugins or different parts of Buildarr
    over the life of an update run, generally it goes here.
    """

    testing: bool = bool(strtobool(os.environ.get("BUILDARR_TESTING", "false")))
    """
    Whether Buildarr is in testing mode or not.
    """

    @property
    def dry_run(self) -> bool:
        """
        Whether Buildarr is in dry run mode or not.

        **Note: As of Buildarr v0.5.0, this mode is no longer available,
        and `state.dry_run` will always return `False`.**
        """
        return False

    @property
    def request_timeout(self) -> float:
        """
        Default timeout for HTTP requests, in seconds.

        If the Buildarr configuration is loaded, the value defined there is used.
        Otherwise, this is set to a default of 30 seconds.
        """
        if self.config is not None:
            return self.config.buildarr.request_timeout
        return 30.0

    plugins: Mapping[str, Plugin] = {}
    """
    The loaded Buildarr plugins, mapped to the plugin's unique name.
    """

    config: ConfigType = None  # type: ignore[assignment]
    """
    Currently loaded global configuration.

    This includes Buildarr configuration and configuration for enabled plugins.
    """

    config_files: Sequence[Path] = []
    """
    Currently loaded configuration files, in the order they were loaded.
    """

    managers: Mapping[str, ManagerPlugin[ConfigPlugin, SecretsPlugin]]
    """
    Manager objects for each currently loaded plugin.
    """

    instance_configs: Mapping[str, Mapping[str, ConfigPlugin]]
    """
    Fully qualified configuration objects for each instance, under each plugin.
    """

    active_plugins: FrozenSet[str]
    """
    A data structure containing the names of all the currently active plugins.
    """

    trash_metadata_dir: Path
    """
    TRaSH-Guides metadata directory.

    Only available if required by at least one instance configuration,
    during the render stage of a Buildarr run.
    """

    secrets: SecretsType
    """
    Currently loaded instance secrets.
    """

    _current_dir: Path = Path.cwd()
    """
    Current working directory for relative path resolution.

    This state attribute is internal, and shouldn't be accessed by plugins.
    """

    _current_plugin: str
    """
    The plugin being processed in the current context.

    This state attribute is internal, and shouldn't be accessed by plugins.
    """

    _current_instance: str
    """
    The current instance being processed in the current context.

    This state attribute is internal, and shouldn't be accessed by plugins.
    """

    _instance_dependencies: DefaultDict[
        PluginInstanceRef,  # source_plugin_instance
        Set[PluginInstanceRef],  # target_plugin_instances
    ]
    """
    The dependency tree for linked instances defined in the Buildarr configuration.

    This attribute is populated when instance name references get validated
    upon fetching instance-specific configurations.

    This state attribute is internal, and shouldn't be accessed by plugins.
    """

    _execution_order: Sequence[PluginInstanceRef]
    """
    A list of plugin-instance references in the order which operations
    should be performed on them.

    This attribute is generated based on the dependency tree for linked instances,
    after `state._instance_dependencies` has finished being populated.

    This state attribute is internal, and shouldn't be accessed by plugins.
    """

    def __init__(self) -> None:
        self._reset()

    def _reset(self) -> None:
        """
        Reset the runtime state generated during an individual Buildarr run.

        This is called in daemon mode to clean up after runs.

        This state function is internal, and shouldn't be used by plugins.
        """
        self.managers = None  # type: ignore[assignment]
        self.instance_configs = None  # type: ignore[assignment]
        self.active_plugins = None  # type: ignore[assignment]
        self.trash_metadata_dir = None  # type: ignore[assignment]
        self.secrets = None  # type: ignore[assignment]
        self._current_plugin = None  # type: ignore[assignment]
        self._current_instance = None  # type: ignore[assignment]
        self._instance_dependencies = defaultdict(set)  # type: ignore[assignment]
        self._execution_order = None  # type: ignore[assignment]

    @contextmanager
    def _with_current_dir(self, current_dir: Path) -> Generator[None, None, None]:
        """
        Set the current directory context within a code block.

        This state function is internal, and shouldn't be used by plugins.

        Args:
            current_dir (Path): Path to use as the current directory.
        """
        old_current_dir = self._current_dir
        self._current_dir = current_dir
        yield
        self._current_dir = old_current_dir

    @contextmanager
    def _with_context(
        self,
        plugin_name: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> Generator[None, None, None]:
        """
        Set the current plugin/instance context within a code block.

        This state function is internal, and shouldn't be used by plugins.

        Args:
            plugin_name (Optional[str], optional): Plugin name to set in the context.
            instance_name (Optional[str], optional): Instance name to set in the context.
        """
        if plugin_name:
            old_current_plugin = self._current_plugin
            self._current_plugin = plugin_name
        if instance_name:
            old_current_instance = self._current_instance
            self._current_instance = instance_name
        yield
        if plugin_name:
            self._current_plugin = old_current_plugin
        if instance_name:
            self._current_instance = old_current_instance


state = State()
"""
Global variable for tracking active Buildarr state.

If anything needs to be shared between plugins or different parts of Buildarr
over the life of an update run, generally it goes here.
"""

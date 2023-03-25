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
Buildarr plugin loading functions.
"""


from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from stevedore.extension import ExtensionManager  # type: ignore[import]

from ..state import state

if TYPE_CHECKING:
    from typing import Dict

    from importlib_metadata import EntryPoint

    from . import Plugin


logger = getLogger(__name__)


def load(namespace: str = "buildarr.plugins") -> None:
    """
    Load plugins from the given namespace.

    Args:
        namespace (str): Namespace (entry point) to load plugins from.
    """

    plugins: Dict[str, Plugin] = {}

    for plugin in ExtensionManager(
        namespace=namespace,
        invoke_on_load=True,
        on_load_failure_callback=_on_plugin_failure,
    ):
        # Do not load the built-in `buildarr-dummy` plugin
        # if Buildarr was not started in testing mode.
        if not state.testing and plugin.name == "dummy":
            continue
        if plugin.name not in plugins:
            plugins[plugin.name] = plugin.entry_point.load()

    state.plugins = plugins


def _on_plugin_failure(manager: ExtensionManager, entrypoint: EntryPoint, err: Exception) -> None:
    """
    Plugin load error handler.

    Args:
        manager (ExtensionManager): Extension manager used to load the plugin
        entrypoint (EntryPoint): Entry point metadata of the plugin
        err (Exception): Exception raised during loading
    """

    logger.error("An error occured while loading plugin '%s':", entrypoint.name)
    logger.exception(err)

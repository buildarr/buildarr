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
Buildarr runtime state.
"""


from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from stevedore.extension import ExtensionManager  # type: ignore[import]

from .logging import logger, plugin_logger

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint
    from typing import Dict, Generator

    from .plugins import Plugin


__all__ = ["plugins", "load_plugins", "plugin_context"]


plugins: Dict[str, Plugin] = {}


def load_plugins(namespace: str = "buildarr.plugins") -> None:
    """
    Load plugins from the given namespace.

    Args:
        namespace (str): Namespace (entry point) to load plugins from.

    Returns:
        Name-to-plugin dictionary
    """

    for plugin in ExtensionManager(
        namespace=namespace,
        invoke_on_load=True,
        on_load_failure_callback=_on_plugin_failure,
    ):
        if plugin.name not in plugins:
            plugins[plugin.name] = plugin.entry_point.load()


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


@contextmanager
def plugin_context(plugin_name: str, instance_name: str) -> Generator[None, None, None]:
    """
    Plugin context manager. Used internally to set the current plugin for logging purposes.

    Args:
        plugin_name (str): Name of the current plugin
        instance_name (str): Name of the instance being currently processed
    """

    old_plugin_name = plugin_logger.plugin_name
    old_instance_name = plugin_logger.instance_name
    try:
        plugin_logger.plugin_name = plugin_name
        plugin_logger.instance_name = instance_name
        yield
    finally:
        plugin_logger.plugin_name = old_plugin_name
        plugin_logger.instance_name = old_instance_name

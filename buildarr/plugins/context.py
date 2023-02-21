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
Buildarr plugin context functions.
"""


from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from ..logging import plugin_logger

if TYPE_CHECKING:
    from typing import Generator


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

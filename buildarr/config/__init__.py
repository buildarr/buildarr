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
Buildarr configuration interface.
"""


from .base import ConfigBase
from .exceptions import ConfigError, ConfigTrashIDNotFoundError
from .load import load
from .models import ConfigPlugin, ConfigPluginType, ConfigType
from .types import RemoteMapEntry

__all__ = [
    "ConfigError",
    "ConfigTrashIDNotFoundError",
    "ConfigBase",
    "ConfigPlugin",
    "ConfigType",
    "ConfigPluginType",
    "RemoteMapEntry",
    "load",
]

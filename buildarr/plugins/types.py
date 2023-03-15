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
Buildarr plugin type hints.
"""


from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..config import ConfigPlugin
    from ..secrets import SecretsPlugin


Config = TypeVar("Config", bound="ConfigPlugin")
"""
Type variable for the configuration object of a plugin.

When creating plugins, substitute `Config` for the implementing type.
"""

Secrets = TypeVar("Secrets", bound="SecretsPlugin")
"""
Type variable for a secrets module of a plugin.

When creating plugins, substitute `Secrets` for the implementing type.
"""

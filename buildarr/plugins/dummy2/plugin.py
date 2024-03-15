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
Dummy2 plugin interface.
"""

from __future__ import annotations

from buildarr import __version__
from buildarr.plugins import Plugin

from .config import Dummy2Config
from .manager import Dummy2Manager
from .secrets import Dummy2Secrets


class Dummy2Plugin(Plugin):
    """
    Dummy2 plugin class that Buildarr reads to process Dummy2 instances.
    """

    cli = None
    config = Dummy2Config
    manager = Dummy2Manager
    secrets = Dummy2Secrets
    version = __version__

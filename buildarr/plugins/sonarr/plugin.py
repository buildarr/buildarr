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
Sonarr plugin interface.
"""


from buildarr.plugins import Plugin

from .cli import sonarr
from .config import SonarrConfig
from .manager import SonarrManager
from .secrets import SonarrSecrets


class SonarrPlugin(Plugin):
    """
    Sonarr plugin class that Buildarr reads to process Sonarr instances.
    """

    cli = sonarr
    config = SonarrConfig
    manager = SonarrManager
    secrets = SonarrSecrets

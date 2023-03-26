#!/usr/bin/env python3

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
Buildarr CLI main routine.
"""


from __future__ import annotations

from ..plugins import load as load_plugins
from ..state import state
from . import cli as main
from .compose import compose
from .daemon import daemon
from .run import run
from .test_config import test_config

__all__ = ["main"]


# Load all installed plugins.
load_plugins()

# Load CLI modules for all installed plugins.
for plugin_name, plugin in state.plugins.items():
    if plugin.cli is not None:
        main.add_command(plugin.cli, name=plugin_name)

if __name__ == "__main__":
    main()

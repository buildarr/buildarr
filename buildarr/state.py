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
Buildarr global runtime state.
"""


from __future__ import annotations

import os

from distutils.util import strtobool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Mapping, Sequence

    from .config import ConfigType
    from .plugins import Plugin
    from .secrets import SecretsType


__all__ = ["state"]


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

    plugins: Mapping[str, Plugin] = {}
    """
    The loaded Buildarr plugins, mapped to the plugin's unique name.
    """

    config_files: Sequence[Path] = []
    """
    Currently loaded configuration files, in the order they were loaded.
    """

    config: ConfigType = None  # type: ignore[assignment]
    """
    Currently loaded global configuration.

    This includes Buildarr configuration and configuration for enabled plugins.
    """

    secrets: SecretsType = None  # type: ignore[assignment]
    """
    Currently loaded instance secrets.
    """


state = State()
"""
Global variable for tracking active Buildarr state.

If anything needs to be shared between plugins or different parts of Buildarr
over the life of an update run, generally it goes here.
"""

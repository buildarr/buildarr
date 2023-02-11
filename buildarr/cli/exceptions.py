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
Buildarr CLI exceptions.
"""


from ..exceptions import BuildarrError


class CLIError(BuildarrError):
    """
    Exception raised in the Buildarr command line interface.
    """

    pass


class DaemonError(BuildarrError):
    """
    Exception raised in the 'buildarr daemon' command.
    """

    pass


class RunError(DaemonError):
    """
    Exception raised in the 'buildarr run' command.
    """

    pass


class RunNoPluginsDefinedError(BuildarrError):
    """
    Exception raised when Buildarr is run without any plugin configuration defined.
    """

    pass

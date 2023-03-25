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


from __future__ import annotations

from ..exceptions import BuildarrError


class CLIError(BuildarrError):
    """
    Exception raised in the Buildarr command line interface.
    """

    pass


class ComposeError(CLIError):
    """
    Exception raised in the `buildarr compose` command.
    """

    pass


class DaemonError(CLIError):
    """
    Exception raised in the `buildarr daemon` command.

    This also includes exceptions raised in the `buildarr run` command,
    since it is a subset of this command.
    """

    pass


class RunError(DaemonError):
    """
    Exception raised in the `buildarr run` command.
    """

    pass


class TestConfigError(CLIError):
    """
    Exception raised in the `buildarr test-config` command.
    """

    pass


class ComposeInvalidHostnameError(ComposeError):
    """
    Exception raised when the hostname configuration for Docker Compose services is invalid.
    """

    pass


class ComposeNoPluginsDefinedError(ComposeError):
    """
    Exception raised when no plugin is configured or loaded when
    generating a Docker Compose environment.
    """

    pass


class ComposeNotSupportedError(ComposeError):
    """
    Exception raised when an unsupported plugin is used when trying to
    generate a Docker Compose file.
    """

    pass


class RunNoPluginsDefinedError(RunError):
    """
    Exception raised when Buildarr is run without any plugin configuration defined.
    """

    pass


class RunInstanceConnectionTestFailedError(RunError):
    """
    Exception raised when a connection test to an instance
    using Buildarr-fetched secrets failed.
    """

    pass


class TestConfigNoPluginsDefinedError(TestConfigError):
    """
    Configuration test error for when there is no configuration defined
    for the loaded plugins.
    """

    pass

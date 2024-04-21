# Copyright (C) 2024 Callum Dickinson
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
Plugin functional tests for the `buildarr compose` CLI command.
"""

from __future__ import annotations


def test_no_plugins_configured(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that an error is returned if `buildarr.yml` does not have any plugins configured.
    """

    result = buildarr_compose(buildarr_yml_factory({}))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_not_supported_by_plugin(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that an error is returned if a selected plugin does not support
    generating service configurations for Docker Compose.
    """

    result = buildarr_compose(buildarr_yml_factory({"dummy2": {"hostname": "dummy2"}}))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeNotSupportedError: "
        "Plugin 'dummy2' does not support Docker Compose "
        "service generation from instance configurations"
    )

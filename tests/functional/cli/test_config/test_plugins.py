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
Functional tests for the `buildarr run` CLI command.
"""

from __future__ import annotations


def test_no_plugins_configured(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that if `buildarr.yml` does not have any plugins configured,
    the appropriate error message is raised.
    """

    buildarr_yml = buildarr_yml_factory({})

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[ERROR] Checking configured plugins: FAILED" in result.stderr
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.TestConfigNoPluginsDefinedError: "
        "No configuration defined for any selected plugins"
    )

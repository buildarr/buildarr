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
Command line option functional tests for the `buildarr test-config` CLI command.
"""

from __future__ import annotations

import pytest


def test_config_path_undefined(instance_value, buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that the command loads `buildarr.yml` from the current directory
    if a file path is not explicitly provided on the command line.
    """

    buildarr_yml = buildarr_yml_factory(
        {"dummy": {"hostname": "dummy", "settings": {"instance_value": instance_value}}},
    )

    result = buildarr_test_config(cwd=buildarr_yml.parent)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


@pytest.mark.parametrize("opt", ["-p", "--plugin"])
def test_plugin(opt, instance_value, buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that if `--plugin` is used to define which plugin to use during the update run,
    only that plugin is actually used.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {"hostname": "dummy", "settings": {"instance_value": instance_value}},
            "dummy2": {"hostname": "dummy", "port": "invalid"},
        },
    )

    result = buildarr_test_config(buildarr_yml, opt, "dummy")

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")

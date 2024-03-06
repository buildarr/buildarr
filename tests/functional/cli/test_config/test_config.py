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


def test_instance_value(instance_value, buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "port": 9999,
                "settings": {"instance_value": instance_value},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}\n" in result.stdout
    assert "[INFO] Loading configuration: PASSED\n" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED\n" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED\n" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED\n" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED\n" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)\n" in result.stdout
    assert result.stdout.endswith("[INFO] Configuration test successful.\n")

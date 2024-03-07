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

from buildarr import __version__


def test_no_plugins_configured(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that if `buildarr.yml` does not have any plugins configured,
    the appropriate error message is raised.
    """

    buildarr_yml = buildarr_yml_factory({})

    result = buildarr_compose(buildarr_yml)

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_use_specific_plugin(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {"hostname": "dummy", "port": 9999},
            "dummy2": {"hostname": "dummy2", "port": 9999},
        },
    )

    result = buildarr_compose(buildarr_yml, "--plugin", "dummy")

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "---",
        "version: '3.7'",
        "services:",
        "  dummy_default:",
        f"    image: callum027/buildarr:{__version__}",
        "    entrypoint:",
        "    - flask",
        "    command:",
        "    - --app",
        "    - buildarr.plugins.dummy.server:app",
        "    - run",
        "    - --debug",
        "    hostname: dummy",
        "    restart: always",
        "  buildarr:",
        f"    image: callum027/buildarr:{__version__}",
        "    command:",
        "    - daemon",
        "    - /config/buildarr.yml",
        "    volumes:",
        "    - type: bind",
        f"      source: {buildarr_yml.parent}",
        "      target: /config",
        "      read_only: true",
        "    restart: always",
        "    depends_on:",
        "    - dummy_default",
    ]

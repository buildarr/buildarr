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

import itertools

import pytest

from buildarr import __version__

from .util import get_source

# TODO: Implement:
#   - test_config_path_undefined


@pytest.mark.parametrize("opt", ["-p", "--plugin"])
def test_plugin(opt, buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {"dummy": {"hostname": "dummy"}, "dummy2": {"hostname": "dummy2"}},
    )

    result = buildarr_compose(buildarr_yml, opt, "dummy")

    source = get_source(buildarr_yml)

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
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        "    restart: always",
        "    depends_on:",
        "    - dummy_default",
    ]


@pytest.mark.parametrize("opt", ["-V", "--compose-version"])
def test_compose_version(opt, buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory({"dummy": {"hostname": "dummy"}})

    result = buildarr_compose(buildarr_yml, opt, "3.4")

    source = get_source(buildarr_yml)

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "---",
        "version: '3.4'",
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
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        "    restart: always",
        "    depends_on:",
        "    - dummy_default",
    ]


@pytest.mark.parametrize(
    "opt,value",
    itertools.product(
        ["-r", "--restart"],
        ["always", "unless-stopped", "on-failure", "no"],
    ),
)
def test_restart(opt, value, buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory({"dummy": {"hostname": "dummy"}})

    result = buildarr_compose(buildarr_yml, opt, value)

    source = get_source(buildarr_yml)
    expected_value = "'no'" if value == "no" else value

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
        f"    restart: {expected_value}",
        "  buildarr:",
        f"    image: callum027/buildarr:{__version__}",
        "    command:",
        "    - daemon",
        "    - /config/buildarr.yml",
        "    volumes:",
        "    - type: bind",
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        f"    restart: {expected_value}",
        "    depends_on:",
        "    - dummy_default",
    ]


@pytest.mark.parametrize("opt", ["-H", "--ignore-hostnames"])
def test_ignore_hostnames(opt, buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory({"dummy": {"hostname": "192.0.2.1"}})

    result = buildarr_compose(buildarr_yml, opt)

    source = get_source(buildarr_yml)

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
        "    hostname: dummy-default",
        "    restart: always",
        "  buildarr:",
        f"    image: callum027/buildarr:{__version__}",
        "    command:",
        "    - daemon",
        "    - /config/buildarr.yml",
        "    volumes:",
        "    - type: bind",
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        "    restart: always",
        "    depends_on:",
        "    - dummy_default",
    ]

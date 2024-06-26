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
Configuration attribute functional tests for the `buildarr compose` CLI command.
"""

from __future__ import annotations

from buildarr import __version__

from .util import get_source


def test_buildarr_docker_image_uri_config(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that the `buildarr.docker_image_uri` configuration attribute works properly.
    """

    docker_image_uri = "testing/buildarr"

    buildarr_yml = buildarr_yml_factory(
        {
            "buildarr": {"docker_image_uri": docker_image_uri},
            "dummy": {"hostname": "dummy"},
        },
    )

    result = buildarr_compose(buildarr_yml)

    source = get_source(buildarr_yml)

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "---",
        "version: '3.7'",
        "services:",
        "  dummy_default:",
        f"    image: {docker_image_uri}:{__version__}",
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
        f"    image: {docker_image_uri}:{__version__}",
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


def test_buildarr_docker_image_uri_envvar(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that the `BUILDARR_DOCKER_IMAGE_URI` environment variable works properly.
    """

    docker_image_uri = "testing/buildarr"

    buildarr_yml = buildarr_yml_factory({"dummy": {"hostname": "dummy"}})

    result = buildarr_compose(buildarr_yml, BUILDARR_DOCKER_IMAGE_URI=docker_image_uri)

    source = get_source(buildarr_yml)

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "---",
        "version: '3.7'",
        "services:",
        "  dummy_default:",
        f"    image: {docker_image_uri}:{__version__}",
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
        f"    image: {docker_image_uri}:{__version__}",
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


def test_hostname_is_ip_address(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that IP addresses are rejected as hostname definitions
    when generating a Docker Compose file.
    """

    result = buildarr_compose(buildarr_yml_factory({"dummy": {"hostname": "192.0.2.1"}}))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeInvalidHostnameError: "
        "Invalid hostname '192.0.2.1' for dummy instance 'default': "
        "Expected hostname, got IP address"
    )


def test_hostname_is_localhost(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that `localhost` is rejected as a hostname definition
    when generating a Docker Compose file.
    """

    result = buildarr_compose(buildarr_yml_factory({"dummy": {"hostname": "localhost"}}))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeInvalidHostnameError: "
        "Invalid hostname 'localhost' for dummy instance 'default': "
        "Hostname must not be localhost for Docker Compose services"
    )


def test_hostname_overlap(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that an error is returned if instance hostnames overlap
    when generating a Docker Compose file.
    """

    result = buildarr_compose(
        buildarr_yml_factory(
            {
                "dummy": {
                    "instances": {
                        "dummy1": {"hostname": "dummy"},
                        "dummy2": {"hostname": "dummy"},
                    },
                },
            },
        ),
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeInvalidHostnameError: "
        "Invalid hostname 'dummy' for dummy instance 'dummy2': "
        "Hostname already used by dummy instance 'dummy1'"
    )


def test_instance_dependencies(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that instance dependencies are rendered correctly
    in the Docker Compose file using `depends_on` structures.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "instances": {
                    "dummy1": {"hostname": "dummy1"},
                    "dummy2": {"hostname": "dummy2", "settings": {"instance_name": "dummy1"}},
                },
            },
        },
    )

    result = buildarr_compose(buildarr_yml)

    source = get_source(buildarr_yml)

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "---",
        "version: '3.7'",
        "services:",
        "  dummy_dummy1:",
        f"    image: callum027/buildarr:{__version__}",
        "    entrypoint:",
        "    - flask",
        "    command:",
        "    - --app",
        "    - buildarr.plugins.dummy.server:app",
        "    - run",
        "    - --debug",
        "    hostname: dummy1",
        "    restart: always",
        "  dummy_dummy2:",
        f"    image: callum027/buildarr:{__version__}",
        "    entrypoint:",
        "    - flask",
        "    command:",
        "    - --app",
        "    - buildarr.plugins.dummy.server:app",
        "    - run",
        "    - --debug",
        "    hostname: dummy2",
        "    restart: always",
        "    depends_on:",
        "    - dummy_dummy1",
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
        "    - dummy_dummy1",
        "    - dummy_dummy2",
    ]


def test_volumes_dict(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that plugin-supplied volume definitions using the `dict`-type
    syntax are rendered correctly.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "dummy",
                "use_service_volumes": True,
                "service_volumes_type": "dict",
            },
        },
    )

    result = buildarr_compose(buildarr_yml)

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
        "    volumes:",
        "    - type: bind",
        f"      source: {source}",
        "      target: /config",
        "    - type: volume",
        "      source: dummy_default",
        "      target: /data",
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
        "volumes:",
        "- dummy_default",
    ]


def test_volumes_list_dict(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that plugin-supplied volume definitions using the `list`-of-`dict`-type
    syntax are rendered correctly.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "dummy",
                "use_service_volumes": True,
                "service_volumes_type": "list-dict",
            },
        },
    )

    result = buildarr_compose(buildarr_yml)

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
        "    volumes:",
        "    - type: bind",
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        "    - type: volume",
        "      source: dummy_default",
        "      target: /data",
        "      read_only: false",
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
        "volumes:",
        "- dummy_default",
    ]


def test_volumes_list_tuple(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that plugin-supplied volume definitions using the `list`-of-`tuple`-type
    syntax are rendered correctly.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "dummy",
                "use_service_volumes": True,
                "service_volumes_type": "list-tuple",
            },
        },
    )

    result = buildarr_compose(buildarr_yml)

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
        "    volumes:",
        "    - type: bind",
        f"      source: {source}",
        "      target: /config",
        "      read_only: true",
        "      bind:",
        "        create_host_path: true",
        "    - type: volume",
        "      source: dummy_default",
        "      target: /data",
        "      read_only: false",
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
        "volumes:",
        "- dummy_default",
    ]


def test_volumes_list_tuple_invalid(buildarr_yml_factory, buildarr_compose) -> None:
    """
    Check that an error is returned when an invalid tuple-type volume definition
    is returned by a plugin when generating a Docker Compose file.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "dummy",
                "use_service_volumes": True,
                "service_volumes_type": "list-tuple-invalid",
            },
        },
    )

    result = buildarr_compose(buildarr_yml)

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.ComposeInvalidVolumeDefinitionError: "
        "Invalid tuple volume definition for dummy instance 'default' "
        "(expecting a 2-tuple, or 3-tuple): "
        f"({str(buildarr_yml.parent)!r}, '/config', ['ro'], 'invalid')"
    )

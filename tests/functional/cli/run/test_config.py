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
Configuration attribute functional tests for the `buildarr run` CLI command.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_httpserver import HTTPServer


def test_invalid_type(buildarr_yml_factory, buildarr_run) -> None:
    """
    Check that an error is returned when the `buildarr.yml` YAML object
    is the incorrect type.
    """

    buildarr_yml = buildarr_yml_factory([])

    result = buildarr_run(buildarr_yml)

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        f"ValueError: Error while loading configuration file '{buildarr_yml}': "
        "Invalid configuration object type (got 'list', expected 'dict'): []"
    )


def test_null(buildarr_yml_factory, buildarr_run) -> None:
    """
    Check that an error is returned when the `buildarr.yml` YAML object
    is `null`.
    """

    result = buildarr_run(buildarr_yml_factory(None))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.RunNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_includes_relative_path(tmp_path: Path, httpserver: HTTPServer, buildarr_run) -> None:
    """
    Check that `includes` resolves paths relative to the configuration file
    the `includes` block was defined in.
    """

    buildarr_yml = tmp_path / "buildarr.yml"
    dummy_yml = tmp_path / "dummy.yml"

    with buildarr_yml.open("w") as f:
        f.write("---\nincludes:\n  - dummy.yml\nbuildarr:\n  watch_config: true\n")

    with dummy_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"message": "Test Error"},
        status=500,
    )

    result = buildarr_run(buildarr_yml)

    httpserver.check_assertions()
    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.plugins.dummy.exceptions.DummyAPIError: Unexpected response "
        f"with status code 500 from 'GET {httpserver.url_for('/initialize.json')}': "
        "Test Error"
    )


def test_includes_invalid_type(buildarr_yml_factory, buildarr_run) -> None:
    """
    Check `includes` error handling for an invalid type.
    """

    buildarr_yml = buildarr_yml_factory({"includes": {}})

    result = buildarr_run(buildarr_yml)

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        f"ValueError: Error while loading configuration file '{buildarr_yml}': "
        "Invalid value type for 'includes' (got 'dict', expected 'list'): {}"
    )


def test_instance_value_changed(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check updating the remote instance for a value that was changed in the Buildarr configuration.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
    )
    # Update instance configuration.
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "trashValue2": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )
    # Get instance configuration for deleting resources.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": True,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "settings": {"instance_value": instance_value},
                },
            },
        ),
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout


def test_instance_value_unchanged(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check that the remote instance is not updated when
    the local and remote configuration are the same.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": False,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": False,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "settings": {"instance_value": instance_value},
                },
            },
        ),
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert (
        f"[DEBUG] <dummy> (default) dummy.settings.instance_value: {instance_value!r} (up to date)"
        in result.stderr
    )
    assert "[INFO] <dummy> (default) Remote configuration is up to date" in result.stdout


def test_trash_value_changed(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check loading values from TRaSH metadata, and updating the remote instance with loaded values.
    """

    api_root = "/api/v1"
    version = "1.0.0"
    # 'anime' quality definitions profile for Sonarr.
    trash_id = "387e6278d8e06083d813358762e0ac63"
    # Bluray-1080p min value.
    trash_value = 5.0

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": False,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={
            "trashValue": trash_value,
            "trashValue2": trash_value,
            "instanceValue": instance_value,
        },
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": True,
            "trashValue": trash_value,
            "trashValue2": trash_value,
            "instanceValue": instance_value,
        },
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "settings": {"instance_value": instance_value, "trash_id": trash_id},
                },
            },
        ),
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert (
        f"[INFO] <dummy> (default) dummy.settings.trash_value: None -> {trash_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout


def test_trash_value_unchanged(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check loading values from TRaSH metadata, and that the remote instance is not updated
    if the resolved and remote values are that the same.
    """

    api_root = "/api/v1"
    version = "1.0.0"
    # 'anime' quality definitions profile for Sonarr.
    trash_id = "387e6278d8e06083d813358762e0ac63"
    # Bluray-1080p min value.
    trash_value = 5.0

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": False,
            "trashValue": trash_value,
            "trashValue2": trash_value,
            "instanceValue": instance_value,
        },
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": False,
            "trashValue": trash_value,
            "trashValue2": trash_value,
            "instanceValue": instance_value,
        },
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "settings": {"instance_value": instance_value, "trash_id": trash_id},
                },
            },
        ),
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert (
        f"[DEBUG] <dummy> (default) dummy.settings.trash_value: {trash_value!r} (up to date)"
        in result.stderr
    )
    assert "[INFO] <dummy> (default) Remote configuration is up to date" in result.stdout


@pytest.mark.parametrize("suffix", ["", "/"])
def test_url_base(
    suffix,
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check that the instance configuration `url_base` attribute works properly.
    """

    url_base = "/dummy"
    api_root = "/api/v1"
    version = "1.0.0"

    # Check if the server is initialised.
    httpserver.expect_ordered_request(
        f"{url_base}/initialize.json",
        method="GET",
    ).respond_with_json(
        {"apiRoot": f"{url_base}{api_root}", "initialized": False},
    )
    # Initialise the server (if supported).
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/init",
        method="POST",
    ).respond_with_json(
        {"initialized": True},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request(
        f"{url_base}/initialize.json",
        method="GET",
    ).respond_with_json(
        {"apiRoot": f"{url_base}{api_root}", "version": version, "initialized": True},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/status",
        method="GET",
    ).respond_with_json(
        {"version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/settings",
        method="GET",
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
    )
    # Update instance configuration.
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/settings",
        method="POST",
        json={"trashValue": None, "trashValue2": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )
    # Get instance configuration for deleting resources.
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/settings",
        method="GET",
    ).respond_with_json(
        {
            "isUpdated": True,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "url_base": f"{url_base}{suffix}",
                    "settings": {"instance_value": instance_value},
                },
            },
        ),
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout

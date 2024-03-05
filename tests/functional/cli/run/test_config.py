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

from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer


def test_instance_value_changed(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
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
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )
    # Update instance configuration.
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
    # Get instance configuration for deleting resources.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": True, "trashValue": None, "instanceValue": instance_value},
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
    Check that a value that already has the correct value is not touched,
    with Buildarr reporting that the instance was already up to date.
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
        {"isUpdated": False, "trashValue": None, "instanceValue": instance_value},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": instance_value},
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
    Check that a value was fetched from TRaSH-Guides metadata,
    and used to set the correct value on a remote instance.
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
        {"isUpdated": False, "trashValue": None, "instanceValue": instance_value},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": trash_value, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": True, "trashValue": trash_value, "instanceValue": instance_value},
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
    Check that a value was fetched from TRaSH-Guides metadata,
    and the value on the remote instance does not change if it is the same as this value.
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
        {"isUpdated": False, "trashValue": trash_value, "instanceValue": instance_value},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": trash_value, "instanceValue": instance_value},
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

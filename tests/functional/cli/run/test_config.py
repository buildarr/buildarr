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
    Perform a standard Buildarr run, and check that a value that is not up to date
    on the remote instance is updated, with Buildarr reporting that the instance was updated.
    """

    api_root = "/api/v1"
    version = "1.0.0"
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
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

    assert (
        f"<dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "Remote configuration successfully updated" in result.stdout


def test_instance_value_unchanged(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Perform a standard Buildarr run, and check that a value that already has the correct value
    is not touched, with Buildarr reporting that the instance was already up to date.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
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

    assert (
        f"<dummy> (default) dummy.settings.instance_value: {instance_value!r} (up to date)"
        in result.stderr
    )
    assert "Remote configuration is up to date" in result.stdout


def test_trash_value_changed(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Perform a standard Buildarr run with a TRaSH-Guides ID defined, and check that
    a value was fetched from the metadata, and used to set the correct value on a remote instance.
    """

    api_root = "/api/v1"
    version = "1.0.0"
    # 'anime' quality definitions profile for Sonarr.
    trash_id = "387e6278d8e06083d813358762e0ac63"
    # Bluray-1080p min value.
    trash_value = 5.0

    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
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

    assert f"<dummy> (default) dummy.settings.trash_value: None -> {trash_value!r}" in result.stdout
    assert "Remote configuration successfully updated" in result.stdout


def test_trash_value_unchanged(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Perform a standard Buildarr run with a TRaSH-Guides ID defined, and check that
    a value was fetched from the metadata, and used to set the correct value on a remote instance.
    """

    api_root = "/api/v1"
    version = "1.0.0"
    # 'anime' quality definitions profile for Sonarr.
    trash_id = "387e6278d8e06083d813358762e0ac63"
    # Bluray-1080p min value.
    trash_value = 5.0

    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
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

    assert (
        f"<dummy> (default) dummy.settings.trash_value: {trash_value!r} (up to date)"
        in result.stderr
    )
    assert "Remote configuration is up to date" in result.stdout

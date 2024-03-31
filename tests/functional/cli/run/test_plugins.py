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


def test_no_plugins_found(buildarr_yml_factory, buildarr_run) -> None:
    """
    Check that if there are no non-testing Buildarr plugins installed,
    it is reflected in the logs.
    """

    result = buildarr_run(buildarr_yml_factory({}), testing=False)

    assert result.returncode == 1
    assert "[INFO] Loaded plugins: (no plugins found)" in result.stdout
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.RunNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_no_plugins_configured(buildarr_yml_factory, buildarr_run) -> None:
    """
    Check that if `buildarr.yml` does not have any plugins configured,
    the appropriate error message is raised.
    """

    result = buildarr_run(buildarr_yml_factory({}))

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.RunNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_initialize(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Test that the instance initialisation process works for standard plugins.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "initialized": False},
    )
    # Initialise the server (if supported).
    httpserver.expect_ordered_request(f"{api_root}/init", method="POST").respond_with_json(
        {"initialized": True},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version, "initialized": True},
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
    assert "[INFO] <dummy> (default) Instance has not been initialised" in result.stdout
    assert "[INFO] <dummy> (default) Initialising instance" in result.stdout
    assert "[INFO] <dummy> (default) Finished initialising instance" in result.stdout
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout


def test_already_initialized(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Test that if an instance is already initialised, Buildarr does not
    try to re-run the initialisation function.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Check if the server is initialised.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version, "initialized": True},
    )
    # Fetch API key (if available).
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version, "initialized": True},
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
        "[DEBUG] <dummy> (default) Instance is initialised and ready for configuration updates"
        in result.stderr
    )
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout


def test_multiple_plugins(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Test that the instance initialisation process works for standard plugins.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Check (and initialise) the dummy instance.
    httpserver.expect_ordered_request("/dummy/initialize.json", method="GET").respond_with_json(
        {"apiRoot": f"/dummy{api_root}", "initialized": False},
    )
    httpserver.expect_ordered_request(f"/dummy{api_root}/init", method="POST").respond_with_json(
        {"initialized": True},
    )

    # Fetch API key (if available) from the dummy instance.
    httpserver.expect_ordered_request("/dummy/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version, "initialized": True},
    )
    # Get dummy instance status in the connection test.
    httpserver.expect_ordered_request(f"/dummy{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )

    # Fetch dummy2 instance metadata in the connection test.
    httpserver.expect_ordered_request("/dummy2/initialize.json", method="GET").respond_with_json(
        {"apiRoot": f"/dummy2{api_root}", "version": version},
    )
    # Get dummy2 instance status in the connection test.
    httpserver.expect_ordered_request(f"/dummy2{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )

    # Get dummy instance configuration for updating.
    httpserver.expect_ordered_request(f"/dummy{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
    )
    # Update dummy instance configuration.
    httpserver.expect_ordered_request(
        f"/dummy{api_root}/settings",
        method="POST",
        json={"trashValue": None, "trashValue2": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )

    # Get dummy2 instance configuration for updating.
    httpserver.expect_ordered_request(
        f"/dummy2{api_root}/settings",
        method="GET",
    ).respond_with_json(
        {"isUpdated": False, "instanceValue": None},
    )
    # Update dummy2 instance configuration.
    httpserver.expect_ordered_request(
        f"/dummy2{api_root}/settings",
        method="POST",
        json={"instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "instanceValue": None},
        status=201,
    )

    # Get instance configuration for deleting dummy2 instance resources.
    httpserver.expect_ordered_request(
        f"/dummy2{api_root}/settings",
        method="GET",
    ).respond_with_json(
        {"isUpdated": True, "instanceValue": instance_value},
    )

    # Get instance configuration for deleting dummy2 instance resources.
    httpserver.expect_ordered_request(f"/dummy{api_root}/settings", method="GET").respond_with_json(
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
                    "url_base": "/dummy",
                    "settings": {"instance_value": instance_value},
                },
                "dummy2": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "url_base": "/dummy2",
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
    assert (
        f"[INFO] <dummy2> (default) dummy2.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy2> (default) Remote configuration successfully updated" in result.stdout


def test_render_unsupported(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Test that the instance initialisation process works for standard plugins.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch server metadata.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get status in the connection test.
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "instanceValue": None},
    )
    # Update instance configuration.
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "instanceValue": None},
        status=201,
    )
    # Get instance configuration for deleting resources.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": True, "instanceValue": instance_value},
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy2": {
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
        "[DEBUG] <dummy2> (default) Skipped performing pre-initialisation configuration rendering "
        "(not supported by plugin)"
    ) in result.stderr
    assert (
        f"[INFO] <dummy2> (default) dummy2.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy2> (default) Remote configuration successfully updated" in result.stdout

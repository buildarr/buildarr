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


def test_api_key_fetch(
    httpserver: HTTPServer,
    api_key,
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
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/status",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "instanceValue": instance_value},
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
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


def test_api_key_in_config(
    httpserver: HTTPServer,
    api_key,
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

    httpserver.expect_ordered_request(
        "/initialize.json",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/status",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"version": version},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "instanceValue": instance_value},
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"isUpdated": True, "trashValue": None, "instanceValue": instance_value},
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "api_key": api_key,
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


def test_api_key_in_config_incorrect(
    httpserver: HTTPServer,
    api_key,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Perform a standard Buildarr run, and check that a value that is not up to date
    on the remote instance is updated, with Buildarr reporting that the instance was updated.
    """

    port = urlparse(httpserver.url_for("")).port

    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"message": "Unauthorized", "description": "Incorrect API key"},
        status=401,
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": port,
                    "api_key": api_key,
                },
            },
        ),
        check=False,
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.plugins.dummy.exceptions.DummySecretsUnauthorizedError: "
        f"Unable to authenticate with the Dummy instance at 'http://localhost:{port}': "
        "Incorrect API key"
    )


def test_api_key_test_fail(
    httpserver: HTTPServer,
    api_key,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Perform a standard Buildarr run, and check that a value that is not up to date
    on the remote instance is updated, with Buildarr reporting that the instance was updated.
    """

    port = urlparse(httpserver.url_for("")).port
    api_root = "/api/v1"
    version = "1.0.0"
    incorrect_api_key = "foobar"

    httpserver.expect_ordered_request(
        "/initialize.json",
        method="GET",
    ).respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    httpserver.expect_ordered_request(f"{api_root}/status", method="GET").respond_with_json(
        {"message": "Unauthorized", "description": "Incorrect API key"},
        status=401,
    )

    result = buildarr_run(
        buildarr_yml_factory(
            {
                "dummy": {
                    "hostname": "localhost",
                    "port": port,
                    "api_key": incorrect_api_key,
                },
            },
        ),
        check=False,
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.RunInstanceConnectionTestFailedError: "
        "Connection test failed for instance 'default': "
        "hostname='localhost'"
        f" port={port}"
        " protocol='http'"
        " api_key=SecretStr('**********')"
        f" version={version!r}"
    )

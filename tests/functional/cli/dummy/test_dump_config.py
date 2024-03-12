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
Functional tests for the `buildarr dummy dump-config` CLI command.
"""

from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from pexpect import spawn

if TYPE_CHECKING:
    from typing import Callable

    from pytest_httpserver import HTTPServer


@pytest.fixture
def buildarr_dummy_dump_config(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_dummy_dump_config(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("dummy", "dump-config", *opts, **kwargs)

    return _buildarr_dummy_dump_config


@pytest.fixture
def buildarr_dummy_dump_config_interactive(
    buildarr_interactive_command,
) -> Callable[..., spawn]:
    def _buildarr_dummy_dump_config_interactive(
        *opts: str,
        **kwargs,
    ) -> spawn:
        return buildarr_interactive_command("dummy", "dump-config", *opts, **kwargs)

    return _buildarr_dummy_dump_config_interactive


def test_api_key_no_auth_required(
    httpserver: HTTPServer,
    buildarr_dummy_dump_config_interactive,
) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch secrets metadata.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )

    child: spawn = buildarr_dummy_dump_config_interactive(httpserver.url_for(""), redirect_tty=True)
    child.expect(r"Dummy instance API key \(or leave blank to auto-fetch\): ")
    child.sendline("")
    child.wait()
    child.read()

    expected_value = [
        "hostname: localhost",
        f"port: {urlparse(httpserver.url_for('')).port}",
        "protocol: http",
        "url_base: null",
        "api_key: null",
        f"version: {version}",
        "settings:",
        "  trash_id: null",
        "  trash_value: null",
        "  instance_value: null",
    ]

    httpserver.check_assertions()
    assert child.exitstatus == 0
    assert child.logfile.getvalue().decode().splitlines()[-len(expected_value) :] == expected_value


def test_api_key_autofetch(
    httpserver: HTTPServer,
    api_key,
    buildarr_dummy_dump_config_interactive,
) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch secrets metadata.
    httpserver.expect_ordered_request("/initialize.json", method="GET").respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )

    child: spawn = buildarr_dummy_dump_config_interactive(httpserver.url_for(""), redirect_tty=True)
    child.expect(r"Dummy instance API key \(or leave blank to auto-fetch\): ")
    child.sendline("")
    child.wait()
    child.read()

    expected_value = [
        "hostname: localhost",
        f"port: {urlparse(httpserver.url_for('')).port}",
        "protocol: http",
        "url_base: null",
        f"api_key: {api_key}",
        f"version: {version}",
        "settings:",
        "  trash_id: null",
        "  trash_value: null",
        "  instance_value: null",
    ]

    httpserver.check_assertions()
    assert child.exitstatus == 0
    assert child.logfile.getvalue().decode().splitlines()[-len(expected_value) :] == expected_value


def test_api_key_interactive(
    httpserver: HTTPServer,
    api_key,
    buildarr_dummy_dump_config_interactive,
) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch secrets metadata.
    httpserver.expect_ordered_request(
        "/initialize.json",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )

    child: spawn = buildarr_dummy_dump_config_interactive(httpserver.url_for(""), redirect_tty=True)
    child.expect(r"Dummy instance API key \(or leave blank to auto-fetch\): ")
    child.sendline(api_key)
    child.wait()
    child.read()

    expected_value = [
        "hostname: localhost",
        f"port: {urlparse(httpserver.url_for('')).port}",
        "protocol: http",
        "url_base: null",
        f"api_key: {api_key}",
        f"version: {version}",
        "settings:",
        "  trash_id: null",
        "  trash_value: null",
        "  instance_value: null",
    ]

    httpserver.check_assertions()
    assert child.exitstatus == 0
    assert child.logfile.getvalue().decode().splitlines()[-len(expected_value) :] == expected_value


@pytest.mark.parametrize("opt", ["-k", "--api-key"])
def test_api_key_opt(opt, httpserver: HTTPServer, api_key, buildarr_dummy_dump_config) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
    """

    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch secrets metadata.
    httpserver.expect_ordered_request(
        "/initialize.json",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )

    result = buildarr_dummy_dump_config(httpserver.url_for(""), opt, api_key)

    httpserver.check_assertions()
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "hostname: localhost",
        f"port: {urlparse(httpserver.url_for('')).port}",
        "protocol: http",
        "url_base: null",
        f"api_key: {api_key}",
        f"version: {version}",
        "settings:",
        "  trash_id: null",
        "  trash_value: null",
        "  instance_value: null",
    ]


@pytest.mark.parametrize("suffix", ["", "/"])
def test_url_base(suffix, httpserver: HTTPServer, api_key, buildarr_dummy_dump_config) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
    """

    url_base = "/dummy"
    api_root = "/api/v1"
    version = "1.0.0"

    # Fetch secrets metadata.
    httpserver.expect_ordered_request(
        f"{url_base}/initialize.json",
        method="GET",
        headers={"X-Api-Key": api_key},
    ).respond_with_json(
        {"apiRoot": api_root, "apiKey": api_key, "version": version},
    )
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(
        f"{url_base}{api_root}/settings",
        method="GET",
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )

    result = buildarr_dummy_dump_config(
        httpserver.url_for(f"{url_base}{suffix}"),
        "--api-key",
        api_key,
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "hostname: localhost",
        f"port: {urlparse(httpserver.url_for('')).port}",
        "protocol: http",
        f"url_base: {url_base}",
        f"api_key: {api_key}",
        f"version: {version}",
        "settings:",
        "  trash_id: null",
        "  trash_value: null",
        "  instance_value: null",
    ]

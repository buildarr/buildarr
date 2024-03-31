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

import pytest

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer


def test_config_path_undefined(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check that if `--plugin` is used to define which plugin to use during the update run,
    only that plugin is actually used.
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
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "trashValue2": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {
            "isUpdated": True,
            "trashValue": None,
            "trashValue2": None,
            "instanceValue": instance_value,
        },
    )

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "port": urlparse(httpserver.url_for("")).port,
                "settings": {"instance_value": instance_value},
            },
        },
    )

    result = buildarr_run(cwd=buildarr_yml.parent)

    httpserver.check_assertions()
    assert result.returncode == 0
    assert f"[INFO] Loading configuration file '{buildarr_yml}'" in result.stdout
    assert "[INFO] Running with plugins: dummy" in result.stdout
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout


@pytest.mark.parametrize("opt", ["-p", "--plugin"])
def test_plugin(
    opt,
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_run,
) -> None:
    """
    Check that if `--plugin` is used to define which plugin to use during the update run,
    only that plugin is actually used.
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
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
    )
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "trashValue2": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "trashValue2": None, "instanceValue": None},
        status=201,
    )
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
                "dummy2": {
                    "hostname": "localhost",
                    "port": urlparse(httpserver.url_for("")).port,
                    "settings": {"instance_value": instance_value},
                },
            },
        ),
        opt,
        "dummy",
    )

    httpserver.check_assertions()
    assert result.returncode == 0
    assert "[INFO] Running with plugins: dummy" in result.stdout
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in result.stdout
    assert (
        f"[INFO] <dummy2> (default) dummy2.settings.instance_value: None -> {instance_value!r}"
        not in result.stdout
    )
    assert (
        "[INFO] <dummy2> (default) Remote configuration successfully updated" not in result.stdout
    )

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

import uuid

from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer


def test_no_plugins_configured(buildarr_yml_factory, buildarr_run) -> None:
    result = buildarr_run(
        buildarr_yml_factory({}),
        check=False,
        BUILDARR_TESTING="false",
    )
    assert result.returncode == 1
    assert result.stderr.splitlines()[-1] == (
        "buildarr.cli.exceptions.RunNoPluginsDefinedError: "
        "No loaded plugins configured in Buildarr"
    )


def test_value_change(httpserver: HTTPServer, buildarr_yml_factory, buildarr_run) -> None:
    api_root = "/api/v1"
    version = "1.0.0"
    instance_value = str(uuid.uuid4())
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
                    "settings": {
                        "instance_value": instance_value,
                    },
                },
            },
        ),
    )
    assert (
        f"<dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in result.stdout
    )
    assert "Remote configuration successfully updated" in result.stdout

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

import json

from io import BytesIO
from typing import TYPE_CHECKING
from zipfile import ZipFile

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_httpserver import HTTPServer


def test_invalid_config_file(tmp_path, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml: Path = tmp_path / "buildarr.yml"

    with buildarr_yml.open("w") as f:
        f.write("%")

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[ERROR] Loading configuration: FAILED" in result.stderr
    assert result.stderr.splitlines()[-4:] == [
        "yaml.scanner.ScannerError: while scanning a directive",
        f'  in "{buildarr_yml}", line 1, column 1',
        "expected alphabetic or numeric character, but found '\\x00'",
        f'  in "{buildarr_yml}", line 1, column 2',
    ]


def test_instance_value(instance_value, buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "port": 9999,
                "settings": {"instance_value": instance_value},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_instance_dependency_cycle(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "instances": {
                    "dummy1": {
                        "port": 9998,
                        "settings": {"instance_name": "dummy2"},
                    },
                    "dummy2": {
                        "port": 9999,
                        "settings": {"instance_name": "dummy1"},
                    },
                },
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[ERROR] Resolving instance dependencies: FAILED" in result.stderr
    assert result.stderr.splitlines()[-4:] == [
        "ValueError: Detected dependency cycle in configuration for instance references:",
        "  1. dummy.instances['dummy1']",
        "  2. dummy.instances['dummy2']",
        "  3. dummy.instances['dummy1']",
    ]


def test_instance_dependency_plugin_not_configured(
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy2": {
                "hostname": "localhost",
                "settings": {"instance_name": "dummy"},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[ERROR] Loading instance configurations: FAILED" in result.stderr
    assert result.stderr.splitlines()[-3:] == [
        "pydantic.error_wrappers.ValidationError: 1 validation error for Dummy2InstanceConfig",
        "settings -> instance_name",
        "  target instance 'dummy' not defined in plugin 'dummy' configuration (type=value_error)",
    ]


def test_instance_dependency_plugin_not_installed(
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy2": {
                "hostname": "localhost",
                "settings": {"nonexistent_plugin_instance": "dummy3"},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[ERROR] Loading configuration: FAILED" in result.stderr
    assert result.stderr.splitlines()[-3:] == [
        "pydantic.error_wrappers.ValidationError: 1 validation error for Config",
        "dummy2 -> settings -> nonexistent_plugin_instance",
        "  target plugin 'dummy3' not installed (type=value_error)",
    ]


def test_trash_id(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "port": 9999,
                # 'anime' quality definitions profile for Sonarr.
                "settings": {"trash_id": "387e6278d8e06083d813358762e0ac63"},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: PASSED" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_id_invalid(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    trash_id = "387e6278d8e06083d813358762e00000"

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "port": 9999,
                "settings": {"trash_id": trash_id},
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: PASSED" in result.stdout
    assert "[ERROR] Pre-initialisation configuration render: FAILED" in result.stderr
    assert result.stderr.splitlines()[-1] == (
        "buildarr.config.exceptions.ConfigTrashIDNotFoundError: "
        f"Unable to find Sonarr quality definition file with trash ID {trash_id!r}"
    )


def test_trash_metadata_download_url(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    trash_id = "387e6278d8e06083d813358762e00000"
    trash_metadata_download_url = httpserver.url_for("/master.zip")
    trash_metadata_dir_prefix = "Guides-master"

    with BytesIO() as f:
        with ZipFile(f, mode="w") as g:
            g.writestr(
                f"{trash_metadata_dir_prefix}/docs/json/sonarr/quality-size/anime.json",
                json.dumps(
                    {
                        "trash_id": trash_id,
                        "qualities": [{"quality": "Bluray-1080p", "min": 50.0}],
                    },
                ),
            )
        httpserver.expect_ordered_request("/master.zip", method="GET").respond_with_data(
            f.getvalue(),
            content_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="master.zip"'},
        )

    buildarr_yml = buildarr_yml_factory(
        {
            "buildarr": {
                "trash_metadata_download_url": trash_metadata_download_url,
                # Do not specify trash_metadata_dir_prefix here,
                # to make sure the default value is correct.
            },
            "dummy": {"settings": {"trash_id": trash_id}},
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "trash_value: 50.0" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: PASSED" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_dir_prefix_null(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    trash_id = "387e6278d8e06083d813358762e00000"
    trash_metadata_download_url = httpserver.url_for("/master.zip")

    with BytesIO() as f:
        with ZipFile(f, mode="w") as g:
            g.writestr(
                "docs/json/sonarr/quality-size/anime.json",
                json.dumps(
                    {
                        "trash_id": trash_id,
                        "qualities": [{"quality": "Bluray-1080p", "min": 50.0}],
                    },
                ),
            )
        httpserver.expect_ordered_request("/master.zip", method="GET").respond_with_data(
            f.getvalue(),
            content_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="master.zip"'},
        )

    buildarr_yml = buildarr_yml_factory(
        {
            "buildarr": {
                "trash_metadata_download_url": trash_metadata_download_url,
                "trash_metadata_dir_prefix": None,
            },
            "dummy": {"settings": {"trash_id": trash_id}},
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "trash_value: 50.0" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: PASSED" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_dir_prefix_custom(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    trash_id = "387e6278d8e06083d813358762e00000"
    trash_metadata_download_url = httpserver.url_for("/master.zip")
    trash_metadata_dir_prefix = "custom-prefix"

    with BytesIO() as f:
        with ZipFile(f, mode="w") as g:
            g.writestr(
                f"{trash_metadata_dir_prefix}/docs/json/sonarr/quality-size/anime.json",
                json.dumps(
                    {
                        "trash_id": trash_id,
                        "qualities": [{"quality": "Bluray-1080p", "min": 50.0}],
                    },
                ),
            )
        httpserver.expect_ordered_request("/master.zip", method="GET").respond_with_data(
            f.getvalue(),
            content_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="master.zip"'},
        )

    buildarr_yml = buildarr_yml_factory(
        {
            "buildarr": {
                "trash_metadata_download_url": trash_metadata_download_url,
                "trash_metadata_dir_prefix": trash_metadata_dir_prefix,
            },
            "dummy": {"settings": {"trash_id": trash_id}},
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "trash_value: 50.0" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: PASSED" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_download_fail(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    trash_metadata_download_url = httpserver.url_for("/master.zip")

    buildarr_yml = buildarr_yml_factory(
        {
            "buildarr": {
                "trash_metadata_download_url": trash_metadata_download_url,
            },
            "dummy": {"settings": {"trash_id": "387e6278d8e06083d813358762e00000"}},
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[ERROR] Fetching TRaSH-Guides metadata: FAILED" in result.stderr
    assert result.stderr.splitlines()[-1] == (
        "urllib.error.HTTPError: HTTP Error 500: INTERNAL SERVER ERROR"
    )

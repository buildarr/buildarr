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
Configuration attribute functional tests for the `buildarr test-config` CLI command.
"""

from __future__ import annotations

import json

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_httpserver import HTTPServer


def test_invalid_config_file(tmp_path, buildarr_test_config) -> None:
    """
    Check error handling when the provided configuration file is not a valid YAML file.
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
    Check parsing a valid instance configuration, with a value defined.
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
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_instance_dependency_multiple(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that instance dependency resolution is working properly
    for multiple instance dependencies.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "instances": {
                    "dummy1": {"port": 9997},
                    "dummy2": {"port": 9998, "settings": {"instance_name": "dummy1"}},
                    "dummy3": {"port": 9999, "settings": {"instance_name": "dummy1"}},
                },
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
    assert "[DEBUG] Execution order:" in result.stderr
    assert "[DEBUG]   1. dummy.instances['dummy1']" in result.stderr
    assert "[DEBUG]   2. dummy.instances['dummy2']" in result.stderr
    assert "[DEBUG]   3. dummy.instances['dummy3']" in result.stderr
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_instance_dependency_cycle(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that an error is returned when an instance dependency cycle is found.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "hostname": "localhost",
                "instances": {
                    "dummy1": {"port": 9998, "settings": {"instance_name": "dummy2"}},
                    "dummy2": {"port": 9999, "settings": {"instance_name": "dummy1"}},
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
    Check that an error is returned when an instance dependency is defined
    that references a plugin that is not configured.
    """

    buildarr_yml = buildarr_yml_factory(
        {"dummy2": {"hostname": "localhost", "settings": {"instance_name": "dummy"}}},
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[ERROR] Loading instance configurations: FAILED" in result.stderr
    assert result.stderr.splitlines()[-3:-1] == [
        "settings.instance_name",
        (
            "  Value error, target instance 'dummy' not defined in plugin 'dummy' configuration "
            "[type=value_error, input_value='dummy', input_type=str]"
        ),
    ]


def test_instance_dependency_plugin_not_installed(
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that an error is returned when an instance dependency is defined
    that references a plugin that is not installed.
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
    assert result.stderr.splitlines()[-3:-1] == [
        "dummy2.settings.nonexistent_plugin_instance",
        (
            "  Value error, target plugin 'dummy3' not installed "
            "[type=value_error, input_value='dummy3', input_type=str]"
        ),
    ]


def test_trash_id(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check fetching the TRaSH-Guides metadata, and rendering dynamically
    defined values, when a TRaSH ID is defined in the instance configuration.
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
    assert "[INFO] Cleaning up TRaSH-Guides metadata: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_id_invalid(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that an error is returned when the provided TRaSH ID is invalid.
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
    Check that the `buildarr.trash_metadata_download_url` configuration attribute
    works properly.
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
    assert "[INFO] Cleaning up TRaSH-Guides metadata: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_dir_prefix_null(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that the `buildarr.trash_metadata_dir_prefix` configuration attribute
    can be set to `null`.
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
    assert "[INFO] Cleaning up TRaSH-Guides metadata: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_dir_prefix_custom(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that the `buildarr.trash_metadata_dir_prefix` configuration attribute
    can be set to a custom value.
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
    assert "[INFO] Cleaning up TRaSH-Guides metadata: PASSED" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_trash_metadata_download_fail(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that an error is returned when downloading the TRaSH metadata fails.
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


def test_local_path(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that a relative path on a `LocalPath` type attribute defined in the
    main `buildarr.yml` file is resolved relative to the `buildarr.yml` file.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy2": {
                "hostname": "localhost",
                "port": 9999,
                "local_path": "test.yml",
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert f"local_path: {buildarr_yml.parent / 'test.yml'}" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_local_path_includes(tmp_path, buildarr_test_config) -> None:
    """
    Check that a relative path on a `LocalPath` type attribute defined in an
    included configuration file is resolved relative that file, *not* the main
    `buildarr.yml` file.
    """

    child_dir = tmp_path / "child-dir"
    buildarr_yml = tmp_path / "buildarr.yml"
    dummy2_yml = child_dir / "dummy2.yml"

    child_dir.mkdir()
    with buildarr_yml.open("w") as f:
        f.write(f"---\nincludes:\n  - {Path('child-dir') / 'dummy2.yml'}")
    with dummy2_yml.open("w") as g:
        g.write("---\ndummy2:\n  hostname: localhost\n  port: 9999\n  local_path: test.yml")

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert f"local_path: {child_dir / 'test.yml'}" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_optional_local_path_null(buildarr_yml_factory, buildarr_test_config) -> None:
    """
    Check that a `LocalPath` type attribute that can be set to `null`
    is handled correctly when it is set to `null`.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy2": {
                "hostname": "localhost",
                "port": 9999,
                "optional_local_path": None,
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert "optional_local_path: null" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_optional_local_path_defined(tmp_path, buildarr_test_config) -> None:
    """
    Check that a `LocalPath` type attribute that can be set to `null`
    is parsed and resolved correctly when it is set to a path.
    """

    child_dir = tmp_path / "child-dir"
    buildarr_yml = tmp_path / "buildarr.yml"
    dummy2_yml = child_dir / "dummy2.yml"

    child_dir.mkdir()
    with buildarr_yml.open("w") as f:
        f.write(f"---\nincludes:\n  - {Path('child-dir') / 'dummy2.yml'}")
    with dummy2_yml.open("w") as g:
        g.write(
            "---\ndummy2:\n  hostname: localhost\n  port: 9999\n  optional_local_path: test.yml",
        )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 0
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[INFO] Loading configuration: PASSED" in result.stdout
    assert "[INFO] Loading plugin managers: PASSED" in result.stdout
    assert "[INFO] Loading instance configurations: PASSED" in result.stdout
    assert f"optional_local_path: {child_dir / 'test.yml'}" in result.stderr
    assert "[INFO] Checking configured plugins: PASSED" in result.stdout
    assert "[INFO] Resolving instance dependencies: PASSED" in result.stdout
    assert "[INFO] Fetching TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert "[INFO] Pre-initialisation configuration render: PASSED" in result.stdout
    assert "[INFO] Cleaning up TRaSH-Guides metadata: SKIPPED (not required)" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("[INFO] Configuration test successful.")


def test_instance_named_default(
    buildarr_yml_factory,
    buildarr_test_config,
) -> None:
    """
    Check that an error is returned when a defined instance is named 'default'.
    """

    buildarr_yml = buildarr_yml_factory(
        {
            "dummy": {
                "instances": {
                    "default": {"hostname": "localhost", "settings": {"instance_name": "dummy"}},
                },
            },
        },
    )

    result = buildarr_test_config(buildarr_yml)

    assert result.returncode == 1
    assert f"[INFO] Testing configuration file: {buildarr_yml}" in result.stdout
    assert "[ERROR] Loading configuration: FAILED" in result.stderr
    assert result.stderr.splitlines()[-3:-1] == [
        "dummy",
        (
            "  Value error, "
            "there is an instance named 'default' defined for this plugin, "
            "the instance name 'default' is reserved within Buildarr, "
            "please choose a different name for this instance "
            "[type=value_error"
            ", input_value={'instances': {'default':...tance_name': 'dummy'}}}}"
            ", input_type=dict]"
        ),
    ]

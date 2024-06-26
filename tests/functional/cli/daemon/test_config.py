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
Configuration attribute functional tests for the `buildarr daemon` CLI command.
"""

from __future__ import annotations

import re
import signal
import sys

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from .util import next_hour

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

    from pexpect import spawn
    from pytest_httpserver import HTTPServer


def test_update_days(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that defining a single value for the `buildarr.update_days` configuration attribute
    works properly.
    """

    update_time = next_hour()

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": [update_time], "update_days": ["Monday"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert f"[INFO]    - Monday {update_time}" in output
    for day in ("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} {update_time}" not in output


def test_update_days_multiple(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that defining multiple values for the `buildarr.update_days` configuration attribute
    works properly.
    """

    update_time = next_hour()

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": [update_time], "update_days": ["Monday", "Tuesday"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday"):
        assert f"[INFO]    - {day} {update_time}" in output
    for day in ("Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} {update_time}" not in output


def test_update_days_change_on_config_reload(
    tmp_path: Path,
    httpserver: HTTPServer,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that upon changing the `buildarr.update_days` configuration attribute
    on reload, the update run schedule is updated accordingly.
    """

    update_time = next_hour()

    buildarr_yml = tmp_path / "buildarr.yml"

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  watch_config: true\n"
                "  update_times:\n"
                f"    - '{update_time}'\n"
                "  update_days:\n"
                "    - Sunday\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\]  - Update at:")
    child.expect(f"\\[INFO\\]    - Sunday {update_time}")
    child.expect(r"\[INFO\] Buildarr ready.")

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  watch_config: true\n"
                "  update_times:\n"
                f"    - '{update_time}'\n"
                "  update_days:\n"
                "    - Tuesday\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\]  - Update at:")
    child.expect(f"\\[INFO\\]    - Tuesday {update_time}")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert output.count(f"[INFO]    - Sunday {update_time}") == 1
    assert output.count(f"[INFO]    - Tuesday {update_time}") == 1


def test_update_days_invalid(buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that an error is returned when an invalid value is supplied for
    `buildarr.update_days`.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"buildarr": {"update_days": ["invalid"]}, "dummy": {}}),
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-3:-1] == [
        "buildarr.update_days.0",
        (
            "  Value error, Invalid DayOfWeek name or value: invalid "
            "[type=value_error, input_value='invalid', input_type=str]"
        ),
    ]


def test_update_times(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that defining a single value for the `buildarr.update_times` configuration attribute
    works properly.
    """

    update_time = next_hour()

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": [update_time]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} {update_time}" in output


def test_update_times_multiple(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that defining multiple values for the `buildarr.update_times` configuration attribute
    works properly.
    """

    next_hour_1 = next_hour()
    next_hour_2 = next_hour(2)

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": [next_hour_1, next_hour_2]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} {next_hour_1}" in output
        assert f"[INFO]    - {day} {next_hour_2}" in output


def test_update_times_change_on_config_reload(
    tmp_path: Path,
    httpserver: HTTPServer,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that upon changing the `buildarr.update_times` configuration attribute
    on reload, the update run schedule is updated accordingly.
    """

    update_time_1 = next_hour()
    update_time_2 = next_hour(2)

    buildarr_yml = tmp_path / "buildarr.yml"

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  watch_config: true\n"
                "  update_times:\n"
                f"    - '{update_time_1}'\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\]  - Update at:")
    child.expect(f"\\[INFO\\]    - Monday {update_time_1}")
    child.expect(r"\[INFO\] Buildarr ready.")

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  watch_config: true\n"
                "  update_times:\n"
                f"    - '{update_time_2}'\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\]  - Update at:")
    child.expect(f"\\[INFO\\]    - Monday {update_time_2}")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert output.count(f"[INFO]    - Monday {update_time_1}") == 1
    assert output.count(f"[INFO]    - Monday {update_time_2}") == 1


def test_update_times_invalid(buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that an error is returned when an invalid value is supplied for
    `buildarr.update_times`.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"buildarr": {"update_times": ["invalid"]}, "dummy": {}}),
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-3:-1] == [
        "buildarr.update_times.0",
        (
            "  Input should be in a valid time format, invalid character in hour "
            "[type=time_parsing, input_value='invalid', input_type=str]"
        ),
    ]


def test_watch_config_enabled(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that configuration file watching works when the
    `buildarr.watch_config` configuration attribute is enabled.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"update_times": [next_hour()], "watch_config": True},
            "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
        },
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Finished reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0


def test_watch_config_disabled(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that configuration file watching is not performed when the
    `buildarr.watch_config` configuration attribute is disabled.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"update_times": [next_hour()], "watch_config": False},
            "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
        },
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert f"[INFO] Config file '{buildarr_yml}' has been modified" not in output
    assert "[INFO] Reloading config" not in output
    assert "[INFO] Finished reloading config" not in output


def test_watch_config_multiple_files(
    tmp_path: Path,
    httpserver: HTTPServer,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that configuration file watching works correctly for all configuratin files
    when more than one are loaded via `includes`.
    """

    buildarr_yml = tmp_path / "buildarr.yml"
    dummy_yml = tmp_path / "dummy.yml"

    with buildarr_yml.open("w") as f:
        f.write(
            (
                f"---\n"
                "includes:\n"
                f"  - {dummy_yml}\n"
                "buildarr:\n"
                "  update_times:\n"
                f"    - '{next_hour()}'\n"
                "  watch_config: true\n"
            ),
        )

    with dummy_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    for config_file in (buildarr_yml, dummy_yml):
        config_file.touch()
        child.expect(f"\\[INFO\\] Config file '{re.escape(str(config_file))}' has been modified")
        child.expect(r"\[INFO\] Reloading config")
        child.expect(r"\[INFO\] Finished reloading config")
        child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0


def test_watch_config_parent_dir_modified(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that the configuration is *not* reloaded when
    the configuration file's parent directory is modified.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"update_times": [next_hour()], "watch_config": True},
            "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
        },
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.parent.touch()
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert f"[INFO] Config file '{buildarr_yml}' has been modified" not in output
    assert f"[INFO] Config file '{buildarr_yml.parent}' has been modified" not in output
    assert "[INFO] Reloading config" not in output
    assert "[INFO] Finished reloading config" not in output


@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")
def test_watch_config_disabled_to_enabled(
    tmp_path: Path,
    httpserver: HTTPServer,
    buildarr_daemon_interactive,
) -> None:
    """
    Check enabling configuration file watching in a running daemon,
    by enabling `buildarr.watch_config` in the configuration file
    and signalling a reload using `SIGHUP`.

    Not run on Windows because `SIGHUP` is not supported.
    """

    buildarr_yml = tmp_path / "buildarr.yml"

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  update_times:\n"
                f"    - '{next_hour()}'\n"
                "  watch_config: false\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Config file monitoring is already disabled")
    child.expect(r"\[INFO\] Buildarr ready.")

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  watch_config: true\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child.kill(signal.SIGHUP)  # type: ignore[attr-defined]
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Enabling config file monitoring")
    child.expect(r"\[INFO\] Finished enabling config file monitoring")
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Config file monitoring is already enabled")
    child.expect(r"\[INFO\] Finished reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0


def test_watch_config_enabled_to_disabled(
    tmp_path: Path,
    httpserver: HTTPServer,
    buildarr_daemon_interactive,
) -> None:
    """
    Check disabling configuration file watching in a running daemon,
    by disabling `buildarr.watch_config` in the configuration file.

    On Windows, some additional testing that makes sure this is working correctly
    is not performed, due to the lack of `SIGHUP` support.
    """

    buildarr_yml = tmp_path / "buildarr.yml"

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  update_times:\n"
                f"    - '{next_hour()}'\n"
                "  watch_config: true\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Enabling config file monitoring")
    child.expect(r"\[INFO\] Finished enabling config file monitoring")
    child.expect(r"\[INFO\] Buildarr ready.")

    with buildarr_yml.open("w") as f:
        f.write(
            (
                "---\n"
                "buildarr:\n"
                "  update_times:\n"
                f"    - '{next_hour()}'\n"
                "  watch_config: false\n"
                "dummy:\n"
                "  hostname: localhost\n"
                f"  port: {urlparse(httpserver.url_for('')).port}\n"
            ),
        )

    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Disabling config file monitoring")
    child.expect(r"\[INFO\] Finished disabling config file monitoring")
    child.expect(r"\[INFO\] Finished reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")

    buildarr_yml.touch()

    # Do extra testing on non-Windows platforms to make sure this is working as expected.
    # Unfortunately we cannot do this on Windows because SIGHUP is not supported.
    if sys.platform != "win32":
        child.kill(signal.SIGHUP)
        child.expect(r"\[INFO\] Reloading config")
        child.expect(r"\[INFO\] Config file monitoring is already disabled")
        child.expect(r"\[INFO\] Finished reloading config")
        child.expect(r"\[INFO\] Buildarr ready.")

    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert output.count(f"[INFO] Config file '{buildarr_yml}' has been modified") == 1


def test_watch_config_error_handler(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check error handling during a configuration reload triggered by
    the configuration watching thread.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"update_times": [next_hour()], "watch_config": True},
            "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
        },
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    with buildarr_yml.open("w") as f:
        f.write("%")
    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(
        (
            r"\[ERROR\] Unexpected exception occurred while handling config file event: "
            "while scanning a directive"
        ),
    )
    child.expect(r"yaml\.scanner\.ScannerError: while scanning a directive")
    child.expect(r"\[WARNING\] Aborted reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0

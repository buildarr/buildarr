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
Functional tests for the `buildarr daemon` CLI command.
"""

from __future__ import annotations

import re
import signal

from typing import TYPE_CHECKING
from urllib.parse import urlparse

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
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_days": ["Monday"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Monday 03:00" in output
    for day in ("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} 03:00" not in output


def test_update_days_multiple(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_days": ["Monday", "Tuesday"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday"):
        assert f"[INFO]    - {day} 03:00" in output
    for day in ("Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} 03:00" not in output


def test_update_days_invalid(buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"buildarr": {"update_days": ["invalid"]}, "dummy": {}}),
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-3:] == [
        "pydantic.error_wrappers.ValidationError: 1 validation error for Config",
        "buildarr -> update_days -> 0",
        "  Invalid DayOfWeek name or value: invalid (type=value_error)",
    ]


def test_update_times(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": ["06:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} 06:00" in output
        assert f"[INFO]    - {day} 03:00" not in output


def test_update_times_multiple(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    child: spawn = buildarr_daemon_interactive(
        buildarr_yml_factory(
            {
                "buildarr": {"update_times": ["06:00", "09:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
        assert f"[INFO]    - {day} 06:00" in output
        assert f"[INFO]    - {day} 09:00" in output
        assert f"[INFO]    - {day} 03:00" not in output


def test_update_times_invalid(buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"buildarr": {"update_times": ["invalid"]}, "dummy": {}}),
    )

    assert result.returncode == 1
    assert result.stderr.splitlines()[-3:] == [
        "pydantic.error_wrappers.ValidationError: 1 validation error for Config",
        "buildarr -> update_times -> 0",
        "  invalid time format (type=value_error.time)",
    ]


def test_watch_config_enabled(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"watch_config": True},
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
    child.kill(signal.SIGTERM)
    child.wait()

    assert child.exitstatus == 0


def test_watch_config_disabled(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {
            "buildarr": {"watch_config": False},
            "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
        },
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

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
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml = tmp_path / "buildarr.yml"
    dummy_yml = tmp_path / "dummy.yml"

    with buildarr_yml.open("w") as f:
        f.write("---\nincludes:\n  - dummy.yml\nbuildarr:\n  watch_config: true\n")

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
    child.kill(signal.SIGTERM)
    child.wait()


# TODO:
#  - test_update_days_change_live (should work)
#  - test_update_times_change_live (should work)
#  - test_watch_config_enable_live (should work)
#  - test_watch_config_disable_live (should work)
#  - test_watch_config_parent_dir_update (should not cause an update run)

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

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

    from pexpect import spawn
    from pytest_httpserver import HTTPServer


@pytest.mark.parametrize("opt", ["-d", "--update-day"])
def test_update_day(
    opt,
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
                "buildarr": {"update_days": ["Sunday"], "update_times": ["03:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
        opt,
        "Monday",
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Monday 03:00" in output
    assert "[INFO]    - Sunday 03:00" not in output


@pytest.mark.parametrize("opt", ["-d", "--update-day"])
def test_update_day_multiple(
    opt,
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
                "buildarr": {"update_days": ["Sunday"], "update_times": ["03:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
        opt,
        "Monday",
        opt,
        "Tuesday",
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Monday 03:00" in output
    assert "[INFO]    - Tuesday 03:00" in output
    assert "[INFO]    - Sunday 03:00" not in output


@pytest.mark.parametrize("opt", ["-d", "--update-day"])
def test_update_day_invalid(opt, buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"dummy": {}}),
        opt,
        "invalid",
    )

    assert result.returncode == 2  # noqa: PLR2004
    assert result.stderr.splitlines()[-1] == (
        "Error: Invalid value for '-d' / '--update-day': 'invalid' is not one of "
        "'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'."
    )


@pytest.mark.parametrize("opt", ["-t", "--update-time"])
def test_update_time(
    opt,
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
                "buildarr": {"update_days": ["Sunday"], "update_times": ["03:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
        opt,
        "09:00",
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Sunday 09:00" in output
    assert "[INFO]    - Sunday 03:00" not in output


@pytest.mark.parametrize("opt", ["-t", "--update-time"])
def test_update_time_multiple(
    opt,
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
                "buildarr": {"update_days": ["Sunday"], "update_times": ["03:00"]},
                "dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port},
            },
        ),
        opt,
        "09:00",
        opt,
        "12:00",
    )
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Sunday 09:00" in output
    assert "[INFO]    - Sunday 12:00" in output
    assert "[INFO]    - Sunday 03:00" not in output


@pytest.mark.parametrize("opt", ["-t", "--update-time"])
def test_update_time_invalid(opt, buildarr_yml_factory, buildarr_daemon) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    result: CompletedProcess = buildarr_daemon(
        buildarr_yml_factory({"dummy": {}}),
        opt,
        "invalid",
    )

    assert result.returncode == 2  # noqa: PLR2004
    assert result.stderr.splitlines()[-1] == (
        "Error: Invalid value for '-t' / '--update-time': invalid"
    )


@pytest.mark.parametrize("opt", ["-w", "--watch"])
def test_watch(
    opt,
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

    child: spawn = buildarr_daemon_interactive(buildarr_yml, opt)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.expect(f"\\[INFO\\] Config file '{re.escape(str(buildarr_yml))}' has been modified")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Finished reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0


@pytest.mark.parametrize("opt", ["-W", "--no-watch"])
def test_no_watch(
    opt,
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

    child: spawn = buildarr_daemon_interactive(buildarr_yml, opt)
    child.expect(r"\[INFO\] Buildarr ready.")
    buildarr_yml.touch()
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    assert child.exitstatus == 0
    assert f"[INFO] Config file '{buildarr_yml}' has been modified" not in output
    assert "[INFO] Reloading config" not in output
    assert "[INFO] Finished reloading config" not in output

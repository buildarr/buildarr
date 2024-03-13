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

import signal
import sys

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from pexpect import spawn
    from pytest_httpserver import HTTPServer


@pytest.mark.parametrize(
    "signal_name",
    # `SIGINT` is not practical to test on Windows right now, because
    # the only way to trigger it is to send the `CTRL_C_EVENT` signal,
    # which interrupts every process in the process tree (including the test suite).
    # It works when you run it manually, so it should be fine to not test here.
    ["SIGBREAK"] if sys.platform == "win32" else ["SIGTERM", "SIGINT"],
)
def test_signal_terminate(
    signal_name,
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {"dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port}},
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(getattr(signal, signal_name))
    child.expect(f"\\[INFO\\] {signal_name} received")
    child.expect(r"\[INFO\] Stopping daemon")
    child.expect(r"\[INFO\] Stopping config file observer")
    child.expect(r"\[INFO\] Finished stopping config file observer")
    child.expect(r"\[INFO\] Clearing update job schedule")
    child.expect(r"\[INFO\] Finished clearing update job schedule")
    child.expect(r"\[INFO\] Finished stopping daemon")
    child.wait()

    assert child.exitstatus == 0


@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")
def test_sighup(
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    buildarr_yml: Path = buildarr_yml_factory(
        {"dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port}},
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(signal.SIGHUP)  # type: ignore[attr-defined]
    child.expect(r"\[INFO\] SIGHUP received")
    child.expect(r"\[INFO\] Reloading config")
    child.expect(r"\[INFO\] Finished reloading config")
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    assert child.exitstatus == 0


def test_initial_run_success(
    httpserver: HTTPServer,
    instance_value,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that a value that is not up to date on the remote instance is updated,
    with Buildarr reporting that the instance was updated.
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
    # Get instance configuration for updating.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
    )
    # Update instance configuration.
    httpserver.expect_ordered_request(
        f"{api_root}/settings",
        method="POST",
        json={"trashValue": None, "instanceValue": instance_value},
    ).respond_with_json(
        {"isUpdated": False, "trashValue": None, "instanceValue": None},
        status=201,
    )
    # Get instance configuration for deleting resources.
    httpserver.expect_ordered_request(f"{api_root}/settings", method="GET").respond_with_json(
        {"isUpdated": True, "trashValue": None, "instanceValue": instance_value},
    )

    child: spawn = buildarr_daemon_interactive(
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
    child.expect(r"\[INFO\] Buildarr ready.")
    child.terminate()
    child.wait()

    output: str = child.logfile.getvalue().decode()

    httpserver.check_assertions()
    assert child.exitstatus == 0
    assert "[INFO] Applying initial configuration" in output
    assert (
        f"[INFO] <dummy> (default) dummy.settings.instance_value: None -> {instance_value!r}"
        in output
    )
    assert "[INFO] <dummy> (default) Remote configuration successfully updated" in output
    assert "[INFO] Finished applying initial configuration" in output


# TODO:
#  - test_initial_run_fail
#  - test_scheduled_run_success
#  - test_scheduled_run_fail

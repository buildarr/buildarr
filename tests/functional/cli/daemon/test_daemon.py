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
    "sig",
    ["SIGTERM", "SIGINT"] if sys.platform == "win32" else ["SIGBREAK", "CTRL_C_EVENT"],
)
def test_signal_terminate(
    sig,
    httpserver: HTTPServer,
    buildarr_yml_factory,
    buildarr_daemon_interactive,
) -> None:
    """
    Check that `buildarr test-config` passes on a configuration
    with a single instance value defined.
    """

    child_sig_name = "SIGINT" if sig == "CTRL_C_EVENT" else sig

    buildarr_yml: Path = buildarr_yml_factory(
        {"dummy": {"hostname": "localhost", "port": urlparse(httpserver.url_for("")).port}},
    )

    child: spawn = buildarr_daemon_interactive(buildarr_yml)
    child.expect(r"\[INFO\] Buildarr ready.")
    child.kill(getattr(signal, sig))
    child.expect(f"\\[INFO\\] {child_sig_name} received")
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


# TODO:
#  - test_initial_run_success
#  - test_initial_run_fail
#  - test_scheduled_run_success
#  - test_scheduled_run_fail

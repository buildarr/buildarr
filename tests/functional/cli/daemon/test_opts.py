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

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

if TYPE_CHECKING:
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
    child.kill(signal.SIGTERM)
    child.wait()

    output = child.before.decode() + child.read().decode()

    assert child.exitstatus == 0
    assert "[INFO]  - Update at:" in output
    assert "[INFO]    - Monday 03:00" in output
    assert "[INFO]    - Sunday 03:00" not in output

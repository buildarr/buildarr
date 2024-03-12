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


from __future__ import annotations

import os
import random
import shutil
import signal
import string
import subprocess
import sys
import uuid

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
import yaml

from pexpect.popen_spawn import PopenSpawn as PopenSpawnBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable, Dict, Mapping, Optional

    from pexpect import spawn


BUILDARR_COMMAND = shutil.which("buildarr") or ""

if not BUILDARR_COMMAND:
    raise RuntimeError("'buildarr' command not found on the command line")


class PopenSpawn(PopenSpawnBase):
    def terminate(self) -> None:
        self.kill(
            (
                signal.SIGBREAK  # type: ignore[attr-defined]
                if sys.platform == "win32"
                else signal.SIGTERM
            ),
        )


@pytest.fixture
def buildarr_yml_factory(tmp_path) -> Callable[..., Path]:
    def _buildarr_yml_factory(
        config: Mapping[str, Any],
        file_name: str = "buildarr.yml",
    ) -> Path:
        buildarr_yml: Path = tmp_path / file_name
        with buildarr_yml.open("w") as f:
            yaml.safe_dump(config, f, default_flow_style=False)
        return buildarr_yml

    return _buildarr_yml_factory


@pytest.fixture
def buildarr_command() -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_command(
        *opts: str,
        stdin: Optional[str] = None,
        check: bool = False,
        testing: Optional[bool] = True,
        log_level: Optional[str] = "DEBUG",
        **env: str,
    ) -> subprocess.CompletedProcess[str]:
        _env = _get_env(env=env, testing=testing, log_level=log_level)
        return subprocess.run(
            args=[BUILDARR_COMMAND, *opts],
            input=stdin,
            env=_env,
            check=check,
            capture_output=True,
            text=True,
        )

    return _buildarr_command


@pytest.fixture
def buildarr_interactive_command() -> Callable[..., spawn]:
    def _buildarr_interactive_command(
        *opts: str,
        testing: Optional[bool] = True,
        log_level: Optional[str] = "DEBUG",
        redirect_tty: bool = False,
        **env: str,
    ) -> spawn:
        _env = _get_env(env=env, testing=testing, log_level=log_level)

        # Allows for /dev/tty redirection using a pseudo-terminal (PTY),
        # but not supported on Windows.
        if redirect_tty:
            if sys.platform == "win32":
                pytest.skip(reason="Not supported on Windows")

            from pexpect import spawn as ptyspawn

            return ptyspawn(
                BUILDARR_COMMAND,
                args=[str(opt) for opt in opts],
                env=_env,
                logfile=BytesIO(),
            )

        # Cross-platform, but does not support commands that directly
        # interact with /dev/tty.
        return PopenSpawn(
            [BUILDARR_COMMAND, *opts],
            env=_env,
            logfile=BytesIO(),
        )

    return _buildarr_interactive_command


@pytest.fixture
def buildarr_compose(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_compose(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("compose", *opts, **kwargs)

    return _buildarr_compose


@pytest.fixture
def buildarr_daemon(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_daemon(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("daemon", *opts, **kwargs)

    return _buildarr_daemon


@pytest.fixture
def buildarr_daemon_interactive(buildarr_interactive_command) -> Callable[..., spawn]:
    def _buildarr_daemon_interactive(
        *opts: str,
        **kwargs,
    ) -> spawn:
        return buildarr_interactive_command("daemon", *opts, **kwargs)

    return _buildarr_daemon_interactive


@pytest.fixture
def buildarr_run(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_run(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("run", *opts, **kwargs)

    return _buildarr_run


@pytest.fixture
def buildarr_test_config(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_test_config(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("test-config", *opts, **kwargs)

    return _buildarr_test_config


@pytest.fixture
def instance_value() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def api_key() -> str:
    return "".join(
        random.choices(string.ascii_lowercase + string.digits, k=32),  # noqa: S311
    )


def _get_env(
    env: Mapping[str, str],
    testing: Optional[bool],
    log_level: Optional[str],
) -> Dict[str, str]:
    _env = {**os.environ}
    if testing is not None:
        _env["BUILDARR_TESTING"] = str(testing).lower()
    if log_level:
        _env["BUILDARR_LOG_LEVEL"] = log_level
    _env.update(env)
    return _env

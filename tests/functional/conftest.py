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
    from typing import Any, Callable, Dict, Generator, List, Mapping, Optional

    from pexpect import spawn


BUILDARR_COMMAND = shutil.which("buildarr") or ""

if not BUILDARR_COMMAND:
    raise RuntimeError("'buildarr' command not found on the command line")


class PopenSpawn(PopenSpawnBase):
    """
    The `pexpect.popen_spawn.PopenSpawn` class, subclassed to add
    a `terminate` method to emulate the method of the same name
    in the `pexpect.spawn` class.
    """

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
    """
    A factory fixture for creating `buildarr.yml`, for passing
    to Buildarr command runs.

    Simply supply the Buildarr configuration as a dictionary,
    and a file named `buildarr.yml` will be created in a temporary
    directory.

    This temporary file will be automatically cleaned up after the test completes.

    Example usage:

    ```python
    def test_sometest(buildarr_yml_factory):
        buildarr_yml: pathlib.Path = buildarr_yml_factory({"buildarr": {}})
    ```
    """

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
    """
    A fixture for running an arbitrary `buildarr` command, non-interactively.

    The test run will block until the command finishes executing.
    A `subprocess.CompletedProcess` object will be returned by the fixture
    function.

    Fixture function args:
        \\*opts (str): `buildarr` command arguments and options.
        cwd (Optional[str], optional): Set a working directory to run the command under.
        stdin (Optional[str], optional): Pass a string as standard input to the command.
        check (bool, optional): Fail if the return code is non-zero. Defaults to `False`.
        testing (Optional[bool], optional): Enable testing mode in Buildarr. Defaults to `True`.
        log_level (Optional[str], optional): Log level in Buildarr. Defaults to `DEBUG`.
        \\*\\*env (str): Environment variables to set when running the command.
    """

    def _buildarr_command(
        *opts: str,
        cwd: Optional[str] = None,
        stdin: Optional[str] = None,
        check: bool = False,
        testing: Optional[bool] = True,
        log_level: Optional[str] = "DEBUG",
        **env: str,
    ) -> subprocess.CompletedProcess[str]:
        _env = _get_env(env=env, testing=testing, log_level=log_level)
        return subprocess.run(
            args=[BUILDARR_COMMAND, *opts],
            cwd=cwd,
            input=stdin,
            env=_env,
            check=check,
            capture_output=True,
            text=True,
        )

    return _buildarr_command


@pytest.fixture
def buildarr_interactive_command() -> Generator[Callable[..., spawn], None, None]:
    """
    A fixture for running an arbitrary `buildarr` command interactively.

    The fixture function will return a Pexpect `spawn`-like object once the
    process is running. This can be used to interact with the running process.

    When the test finishes the fixture will attempt to clean up any started processes
    that are still running, but ultimately it is the responsibility of the caller
    to make sure any started processes are cleaned up.

    Note that the `redirect_tty` argument is not supported on Windows.
    If this function is called on Windows with `redirect_tty` set to `True`,
    the test will be skipped.

    Fixture function args:
        \\*opts (str): `buildarr` command arguments and options.
        cwd (Optional[str], optional): Set a working directory to run the command under.
        testing (Optional[bool], optional): Enable testing mode in Buildarr. Defaults to `True`.
        log_level (Optional[str], optional): Log level in Buildarr. Defaults to `DEBUG`.
        redirect_tty (bool, optional): Enable pseudo-terminal TTY redirection. Defaults to `False`.
        \\*\\*env (str): Environment variables to set when running the command.
    """

    children: List[spawn] = []

    def _buildarr_interactive_command(
        *opts: str,
        cwd: Optional[str] = None,
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

            child = ptyspawn(
                BUILDARR_COMMAND,
                args=[str(opt) for opt in opts],
                cwd=cwd,
                env=_env,
                logfile=BytesIO(),
            )
        # Cross-platform, but does not support commands that directly
        # interact with /dev/tty.
        else:
            child = PopenSpawn(
                [BUILDARR_COMMAND, *opts],
                cwd=cwd,
                env=_env,
                logfile=BytesIO(),
            )
        children.append(child)
        return child

    try:
        yield _buildarr_interactive_command
    finally:
        for child in children:
            if not getattr(child, "terminated", False):
                child.kill(signal.SIGKILL)
                child.wait()


@pytest.fixture
def buildarr_compose(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    """
    Fixture for running `buildarr compose`.

    For more information on running non-interactive commands,
    check the `buildarr_command` fixture.

    Run the command like so:

    ```python
    def test_sometest(buildarr_yml_factory, buildarr_compose):
        result = buildarr_compose(buildarr_yml_factory({...}), ...)
    ```
    """

    def _buildarr_compose(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("compose", *opts, **kwargs)

    return _buildarr_compose


@pytest.fixture
def buildarr_daemon(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    """
    Fixture for running `buildarr daemon`.

    For more information on running non-interactive commands,
    check the `buildarr_command` fixture.

    Run the command like so:

    ```python
    def test_sometest(buildarr_yml_factory, buildarr_daemon):
        result = buildarr_daemon(buildarr_yml_factory({...}), ...)
    ```
    """

    def _buildarr_daemon(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("daemon", *opts, **kwargs)

    return _buildarr_daemon


@pytest.fixture
def buildarr_daemon_interactive(buildarr_interactive_command) -> Callable[..., spawn]:
    """
    Fixture for running `buildarr daemon` as an interactive command.

    For more information on running interactive commands,
    check the `buildarr_interactive_command` fixture.

    Run the command like so:

    ```python
    def test_sometest(buildarr_yml_factory, buildarr_daemon_interactive):
        child = buildarr_daemon_interactive(buildarr_yml_factory({...}), ...)
    ```
    """

    def _buildarr_daemon_interactive(
        *opts: str,
        **kwargs,
    ) -> spawn:
        return buildarr_interactive_command("daemon", *opts, **kwargs)

    return _buildarr_daemon_interactive


@pytest.fixture
def buildarr_run(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    """
    Fixture for running `buildarr run`.

    For more information on running non-interactive commands,
    check the `buildarr_command` fixture.

    Run the command like so:

    ```python
    def test_sometest(buildarr_yml_factory, buildarr_run):
        result = buildarr_run(buildarr_yml_factory({...}), ...)
    ```
    """

    def _buildarr_run(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("run", *opts, **kwargs)

    return _buildarr_run


@pytest.fixture
def buildarr_test_config(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    """
    Fixture for running `buildarr test-config`.

    For more information on running non-interactive commands,
    check the `buildarr_command` fixture.

    Run the command like so:

    ```python
    def test_sometest(buildarr_yml_factory, buildarr_test_config):
        result = buildarr_test_config(buildarr_yml_factory({...}), ...)
    ```
    """

    def _buildarr_test_config(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("test-config", *opts, **kwargs)

    return _buildarr_test_config


@pytest.fixture
def instance_value() -> str:
    """
    Fixture for generating a random UUID suitable for use as a Dummy instance value.

    Returns:
        Dummy instance value
    """
    return str(uuid.uuid4())


@pytest.fixture
def api_key() -> str:
    """
    Fixture for generating a random Dummy API key.

    Returns:
        Dummy API key
    """

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

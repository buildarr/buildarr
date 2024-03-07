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
import string
import subprocess
import uuid

from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable, Mapping, Optional


BUILDARR_COMMAND = shutil.which("buildarr") or ""

if not BUILDARR_COMMAND:
    raise RuntimeError("'buildarr' command not found on the command line")


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
        check: bool = False,
        testing: Optional[bool] = True,
        log_level: Optional[str] = "DEBUG",
        **env: str,
    ) -> subprocess.CompletedProcess[str]:
        _env = {**os.environ}
        if testing is not None:
            _env["BUILDARR_TESTING"] = str(testing).lower()
        if log_level:
            _env["BUILDARR_LOG_LEVEL"] = log_level
        _env.update(env)
        return subprocess.run(
            args=[BUILDARR_COMMAND, *opts],
            env=_env,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    return _buildarr_command


@pytest.fixture
def buildarr_compose(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_compose(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("compose", *opts, **kwargs)

    return _buildarr_compose


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

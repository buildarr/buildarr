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
import shutil
import subprocess

from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable, Mapping


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
        check: bool = True,
        **env: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args=[BUILDARR_COMMAND, *opts],
            env={**os.environ, "BUILDARR_TESTING": "true", **env},
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    return _buildarr_command


@pytest.fixture
def buildarr_run(buildarr_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    def _buildarr_run(*opts: str, **kwargs) -> subprocess.CompletedProcess[str]:
        return buildarr_command("run", *opts, **kwargs)

    return _buildarr_run

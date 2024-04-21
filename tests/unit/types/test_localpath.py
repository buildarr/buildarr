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
Test the `LocalPath` configuration attribute type.
"""

from __future__ import annotations

from buildarr.config import ConfigBase
from buildarr.state import state
from buildarr.types import LocalPath


class Settings(ConfigBase):
    test_attr: LocalPath


def test_validate_absolute(tmp_path) -> None:
    """
    Check validation of an absolute path.
    """

    test_attr = tmp_path / "hello-world.txt"

    assert Settings(test_attr=str(test_attr)).test_attr == test_attr


def test_validate_relative(tmp_path) -> None:
    """
    Check that validation of a relative path resolves the path relative to the
    Buildarr global state's internal field for the current directory context,
    and *not* the current working directory of the process.
    """

    test_attr = tmp_path / "hello-world.txt"

    old_current_dir = state._current_dir
    try:
        state._current_dir = test_attr.parent
        settings = Settings(test_attr=test_attr.name)
    finally:
        state._current_dir = old_current_dir

    assert settings.test_attr == test_attr

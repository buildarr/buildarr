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
Test decoding remote attributes using configuration attribute types
on the `ConfigBase.get_local_attrs` class method.
"""

from __future__ import annotations

from typing import Optional

import pytest

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_attr: Optional[str] = None


def test_optional_true() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {"optional": True})],
                remote_attrs={},
            ),
        ).test_attr
        is None
    )


def test_optional_false() -> None:
    with pytest.raises(KeyError):
        Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {"optional": False})],
            remote_attrs={},
        )


def test_optional_default() -> None:
    with pytest.raises(KeyError):
        Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={},
        )

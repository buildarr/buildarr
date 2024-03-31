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

from typing import Dict, List, Optional, Set, Union

import pytest

from buildarr.config import ConfigBase
from buildarr.types import BaseEnum


class Enum(BaseEnum):
    zero = 0
    one = 1
    two = 2
    three = 3


class Settings(ConfigBase):
    test_bool: bool = False
    test_int: int = 0
    test_float: float = 0
    test_str: str = ""
    test_list_int: List[int] = []
    test_list_str: List[str] = []
    test_set_int: Set[int] = set()
    test_set_str: Set[str] = set()
    test_dict_int_str: Dict[int, str] = {}
    test_enum: Enum = Enum.zero
    test_union_int_str_liststr: Union[int, str, List[str]] = 0
    test_optional_str: Optional[str] = None


def test_decode_bool() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_bool", "testAttr", {})],
                remote_attrs={"testAttr": True},
            ),
        ).test_bool
        is True
    )


def test_decode_int() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_int", "testAttr", {})],
                remote_attrs={"testAttr": 123},
            ),
        ).test_int
        == 123  # noqa: PLR2004
    )


def test_decode_float() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_float", "testAttr", {})],
                remote_attrs={"testAttr": 123.456},
            ),
        ).test_float
        == 123.456  # noqa: PLR2004
    )


def test_decode_str() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_str", "testAttr", {})],
                remote_attrs={"testAttr": "Hello, world!"},
            ),
        ).test_str
        == "Hello, world!"
    )


def test_decode_list_int() -> None:
    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_list_int", "testAttr", {})],
            remote_attrs={"testAttr": [1, 2, 3]},
        ),
    ).test_list_int == [1, 2, 3]


def test_decode_list_str() -> None:
    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_list_str", "testAttr", {})],
            remote_attrs={"testAttr": ["Hello", "World", "Buildarr"]},
        ),
    ).test_list_str == ["Hello", "World", "Buildarr"]


def test_decode_set_int() -> None:
    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_set_int", "testAttr", {})],
            remote_attrs={"testAttr": [1, 2, 3]},
        ),
    ).test_set_int == {1, 2, 3}


def test_decode_set_str() -> None:
    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_set_str", "testAttr", {})],
            remote_attrs={"testAttr": ["Hello", "World", "Buildarr"]},
        ),
    ).test_set_str == {"Hello", "World", "Buildarr"}


def test_decode_dict_int_str() -> None:
    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_dict_int_str", "testAttr", {})],
            remote_attrs={"testAttr": {1: "Hello, world!"}},
        ),
    ).test_dict_int_str == {1: "Hello, world!"}


def test_decode_enum() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_enum", "testAttr", {})],
                remote_attrs={"testAttr": 1},
            ),
        ).test_enum
        == Enum.one
    )


@pytest.mark.parametrize("test_value", [1, "Hello, world!", ["Hello", "world!"]])
def test_decode_union_int_str_liststr(test_value) -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_union_int_str_liststr", "testAttr", {})],
                remote_attrs={"testAttr": test_value},
            ),
        ).test_union_int_str_liststr
        == test_value
    )


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_decode_optional_str(test_value) -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_optional_str", "testAttr", {})],
                remote_attrs={"testAttr": test_value},
            ),
        ).test_optional_str
        == test_value
    )
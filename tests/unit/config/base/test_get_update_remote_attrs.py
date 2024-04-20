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
Test encoding remote attributes using configuration attribute types
on the `ConfigBase.get_update_remote_attrs` method.
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


def test_unmanaged() -> None:
    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            ("test_bool", "testBool", {}),
            ("test_int", "testInt", {}),
            ("test_float", "testFloat", {}),
            ("test_str", "testStr", {}),
            ("test_list_int", "testListInt", {}),
            ("test_list_str", "testListStr", {}),
            ("test_set_int", "testSetInt", {}),
            ("test_set_str", "testSetStr", {}),
            ("test_dict_int_str", "testDictIntStr", {}),
            ("test_enum", "testEnum", {}),
            ("test_union_int_str_liststr", "testUnionIntStrListstr", {}),
            ("test_optional_str", "testOptionalStr", {}),
        ],
    ) == (False, {})


def test_set_unchanged() -> None:
    assert Settings(
        test_bool=False,
        test_int=0,
        test_float=0,
        test_str="",
        test_list_int=[],
        test_list_str=[],
        test_set_int=set(),
        test_set_str=set(),
        test_dict_int_str={},
        test_enum=Enum.zero,
        test_union_int_str_liststr=0,
        test_optional_str=None,
    ).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            ("test_bool", "testBool", {}),
            ("test_int", "testInt", {}),
            ("test_float", "testFloat", {}),
            ("test_str", "testStr", {}),
            ("test_list_int", "testListInt", {}),
            ("test_list_str", "testListStr", {}),
            ("test_set_int", "testSetInt", {}),
            ("test_set_str", "testSetStr", {}),
            ("test_dict_int_str", "testDictIntStr", {}),
            ("test_enum", "testEnum", {}),
            ("test_union_int_str_liststr", "testUnionIntStrListstr", {}),
            ("test_optional_str", "testOptionalStr", {}),
        ],
    ) == (False, {})


def test_encode_bool() -> None:
    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
    ) == (True, {"testAttr": True})


def test_encode_int() -> None:
    assert Settings(test_int=123).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_int", "testAttr", {})],
    ) == (True, {"testAttr": 123})


def test_encode_float() -> None:
    assert Settings(test_float=123.456).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_float", "testAttr", {})],
    ) == (True, {"testAttr": 123.456})


def test_encode_str() -> None:
    assert Settings(test_str="Hello, world!").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_str", "testAttr", {})],
    ) == (True, {"testAttr": "Hello, world!"})


def test_encode_list_int() -> None:
    assert Settings(test_list_int=[1, 2, 3]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_list_int", "testAttr", {})],
    ) == (True, {"testAttr": [1, 2, 3]})


def test_encode_list_str() -> None:
    assert Settings(test_list_str=["Hello", "World", "Buildarr"]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_list_str", "testAttr", {})],
    ) == (True, {"testAttr": ["Hello", "World", "Buildarr"]})


def test_encode_set_int() -> None:
    changed, remote_attrs = Settings(test_set_int=[1, 2, 3]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_set_int", "testAttr", {})],
    )
    assert changed
    assert "testAttr" in remote_attrs
    assert isinstance(remote_attrs["testAttr"], list)
    assert sorted(remote_attrs["testAttr"]) == [1, 2, 3]


def test_encode_set_str() -> None:
    changed, remote_attrs = Settings(test_set_str=["Str1", "Str2", "Str3"]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_set_str", "testAttr", {})],
    )
    assert changed
    assert "testAttr" in remote_attrs
    assert isinstance(remote_attrs["testAttr"], list)
    assert sorted(remote_attrs["testAttr"]) == ["Str1", "Str2", "Str3"]


def test_encode_dict_int_str() -> None:
    assert Settings(test_dict_int_str={1: "Hello, world!"}).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_dict_int_str", "testAttr", {})],
    ) == (True, {"testAttr": {1: "Hello, world!"}})


def test_encode_enum() -> None:
    assert Settings(test_enum=Enum.one).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_enum", "testAttr", {})],
    ) == (True, {"testAttr": 1})


@pytest.mark.parametrize("test_value", [1, "Hello, world!", ["Hello", "world!"]])
def test_encode_union_int_str_liststr(test_value) -> None:
    assert Settings(test_union_int_str_liststr=test_value).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_union_int_str_liststr", "testAttr", {})],
    ) == (True, {"testAttr": test_value})


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_encode_optional_str(test_value) -> None:
    assert Settings(test_optional_str=test_value).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_optional_str=None if test_value else "Hello, world!"),
        remote_map=[("test_optional_str", "testAttr", {})],
    ) == (True, {"testAttr": test_value})


def test_check_unmanaged_true() -> None:
    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {})],
        check_unmanaged=True,
    ) == (True, {"testAttr": False})


def test_check_unmanaged_false() -> None:
    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
        check_unmanaged=False,
    ) == (False, {})


def test_set_unchanged_true() -> None:
    assert Settings(test_bool=False).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=True,
    ) == (False, {"testAttr": False})


def test_set_unchanged_true_unmanaged() -> None:
    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=True,
    ) == (False, {"testAttr": True})


def test_set_unchanged_false() -> None:
    assert Settings(test_bool=False).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=False,
    ) == (False, {})


def test_is_field() -> None:
    assert Settings(test_bool=True, test_int=123).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            ("test_bool", "testBool", {"is_field": True}),
            ("test_int", "testInt", {"is_field": True}),
        ],
    ) == (
        True,
        {"fields": [{"name": "testBool", "value": True}, {"name": "testInt", "value": 123}]},
    )

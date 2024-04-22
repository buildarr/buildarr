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

import logging

from typing import Dict, List, Optional, Set, Union

import pytest

from buildarr.config import ConfigBase


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
    test_union_int_str_liststr: Union[int, str, List[str]] = 0
    test_optional_str: Optional[str] = None


def test_unmanaged() -> None:
    """
    Check that unmanaged values are not considered when looking for differences
    between the local and remote instance configuration.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(
            test_bool=True,
            test_int=123,
            test_float=123.456,
            test_str="Hello, world!",
            test_list_int=[123],
            test_list_str=["Hello, world!"],
            test_set_int={123},
            test_set_str={"Hello, world!"},
            test_dict_int_str={1: "Hello, world!"},
            test_union_int_str_liststr=123,
            test_optional_str="Hello, world!",
        ),
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
            ("test_union_int_str_liststr", "testUnionIntStrListstr", {}),
            ("test_optional_str", "testOptionalStr", {}),
        ],
    ) == (False, {})


def test_unchanged() -> None:
    """
    Check that no changes are found when the local and remote instances are identical.
    """

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
            ("test_union_int_str_liststr", "testUnionIntStrListstr", {}),
            ("test_optional_str", "testOptionalStr", {}),
        ],
    ) == (False, {})


def test_encode_bool() -> None:
    """
    Check that encoding a `bool` attribute works properly
    using the default encoder.
    """

    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
    ) == (True, {"testAttr": True})


def test_encode_int() -> None:
    """
    Check that encoding an `int` attribute works properly
    using the default encoder.
    """

    assert Settings(test_int=123).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_int", "testAttr", {})],
    ) == (True, {"testAttr": 123})


def test_encode_float() -> None:
    """
    Check that encoding a `float` attribute works properly
    using the default encoder.
    """

    assert Settings(test_float=123.456).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_float", "testAttr", {})],
    ) == (True, {"testAttr": 123.456})


def test_encode_str() -> None:
    """
    Check that encoding an `str` attribute works properly
    using the default encoder.
    """

    assert Settings(test_str="Hello, world!").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_str", "testAttr", {})],
    ) == (True, {"testAttr": "Hello, world!"})


def test_encode_list_int() -> None:
    """
    Check that encoding a `list[int]` attribute works properly
    using the default encoder.
    """

    assert Settings(test_list_int=[1, 2, 3]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_list_int", "testAttr", {})],
    ) == (True, {"testAttr": [1, 2, 3]})


def test_encode_list_str() -> None:
    """
    Check that encoding a `list[str]` attribute works properly
    using the default encoder.
    """

    assert Settings(test_list_str=["Hello", "World", "Buildarr"]).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_list_str", "testAttr", {})],
    ) == (True, {"testAttr": ["Hello", "World", "Buildarr"]})


def test_encode_set_int() -> None:
    """
    Check that encoding a `set[int]` attribute works properly
    using the default encoder.
    """

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
    """
    Check that encoding a `set[str]` attribute works properly
    using the default encoder.
    """

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
    """
    Check that encoding a `dict[int, str]` attribute works properly
    using the default encoder.
    """

    assert Settings(test_dict_int_str={1: "Hello, world!"}).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_dict_int_str", "testAttr", {})],
    ) == (True, {"testAttr": {1: "Hello, world!"}})


@pytest.mark.parametrize("test_value", [1, "Hello, world!", ["Hello", "world!"]])
def test_encode_union_int_str_liststr(test_value) -> None:
    """
    Check that encoding a `int | str | list[str]` attribute works properly
    using the default encoder.
    """

    assert Settings(test_union_int_str_liststr=test_value).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_union_int_str_liststr", "testAttr", {})],
    ) == (True, {"testAttr": test_value})


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_encode_optional_str(test_value) -> None:
    """
    Check that encoding an `str | None` attribute works properly
    using the default encoder.
    """

    assert Settings(test_optional_str=test_value).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_optional_str=None if test_value else "Hello, world!"),
        remote_map=[("test_optional_str", "testAttr", {})],
    ) == (True, {"testAttr": test_value})


def test_check_unmanaged_true() -> None:
    """
    Check that when `check_unmanaged` is set to `True`,
    unmanaged attributes are considered when comparing
    local vs remote instance configuration.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {})],
        check_unmanaged=True,
    ) == (True, {"testAttr": False})


def test_check_unmanaged_false() -> None:
    """
    Check that when `check_unmanaged` is explicitly set to `False`,
    unmanaged attributes are **not** considered when comparing
    local vs remote instance configuration.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
        check_unmanaged=False,
    ) == (False, {})


def test_set_unchanged_true() -> None:
    """
    Check that when `set_unchanged` is set to `True`,
    unchanged attributes are included in the output remote attributes.
    """

    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=True,
    ) == (False, {"testAttr": True})


def test_set_unchanged_true_unmanaged() -> None:
    """
    Check that when `set_unchanged` is set to `True`,
    unmanaged attributes are also included in the output remote attributes,
    and that the returned value is the one from the remote.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=True,
    ) == (False, {"testAttr": True})


def test_set_unchanged_false() -> None:
    """
    Check that when `set_unchanged` is explicitly set to `False`,
    unchanged values are **not** included in the output remote attributes.
    """

    assert Settings(test_bool=False).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {})],
        set_unchanged=False,
    ) == (False, {})


def test_encoder() -> None:
    """
    Check that configuring a custom encoder using the `encoder`
    remote map entry parameter works properly.
    """

    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            ("test_bool", "testAttr", {"encoder": lambda v: "Hello, world!" if v else None}),
        ],
    ) == (True, {"testAttr": "Hello, world!"})


def test_root_encoder() -> None:
    """
    Check that configuring a root encoder using the `root_encoder`
    remote map entry parameter works properly.
    """

    assert Settings(test_bool=True, test_int=123).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            (
                "test_bool",
                "testAttr",
                {
                    "root_encoder": lambda vs: (
                        f"test_bool={vs.test_bool}, test_int={vs.test_int}"
                    ),
                },
            ),
        ],
    ) == (True, {"testAttr": "test_bool=True, test_int=123"})


def test_formatter(caplog) -> None:
    """
    Check that configuring a custom logging formatter using the `formatter`
    remote map entry parameter works properly.
    """

    caplog.set_level(logging.DEBUG)
    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[
            ("test_bool", "testAttr", {"formatter": lambda v: "Yes" if v else "No"}),
        ],
    ) == (True, {"testAttr": True})
    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_bool: 'No' -> 'Yes'"


@pytest.mark.parametrize("test_value", [False, True])
def test_set_if(test_value) -> None:
    """
    Check that the `set_if` remote map entry parameter works properly.
    """

    assert Settings(test_bool=test_value).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=not test_value),
        remote_map=[
            ("test_bool", "testAttr", {"set_if": lambda v: not v}),
        ],
    ) == (True, ({"testAttr": False} if not test_value else {}))


def test_is_field() -> None:
    """
    Check that the `is_field` remote map entry parameter works properly.
    """

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


def test_remote_map_entry_check_unmanaged_true() -> None:
    """
    Check that when the `check_unmanaged` remote map entry parameter is set to `True`,
    unmanaged attributes are considered when comparing
    local vs remote instance configuration,
    and the method argument of the same name is overridden.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {"check_unmanaged": True})],
        check_unmanaged=False,
    ) == (True, {"testAttr": False})


def test_remote_map_entry_check_unmanaged_false() -> None:
    """
    Check that when the `check_unmanaged` remote map entry parameter is set to `False`,
    unmanaged attributes are **not** considered when comparing
    local vs remote instance configuration,
    and the method argument of the same name is overridden.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {"check_unmanaged": False})],
        check_unmanaged=True,
    ) == (False, {})


def test_remote_map_entry_set_unchanged_true() -> None:
    """
    Check that when the `set_unchanged` remote map entry parameter is set to `True`,
    unchanged attributes are included in the output remote attributes,
    and the method argument of the same name is overridden.
    """

    assert Settings(test_bool=True).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=True),
        remote_map=[("test_bool", "testAttr", {"set_unchanged": True})],
        set_unchanged=False,
    ) == (False, {"testAttr": True})


def test_remote_map_entry_set_unchanged_true_unmanaged() -> None:
    """
    Check that when the `set_unchanged` remote map entry parameter is set to `True`,
    unmanaged attributes are also included in the output remote attributes,
    and that the returned value is the one from the remote.
    """

    assert Settings().get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_bool=False),
        remote_map=[("test_bool", "testAttr", {"set_unchanged": True})],
        set_unchanged=False,
    ) == (False, {"testAttr": False})


def test_remote_map_entry_set_unchanged_false() -> None:
    """
    Check that when the `set_unchanged` remote map entry parameter is set to `False`,
    unchanged attributes are **not** included in the output remote attributes,
    and the method argument of the same name is overridden.
    """

    assert Settings(test_bool=False).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_bool", "testAttr", {"set_unchanged": False})],
        set_unchanged=True,
    ) == (False, {})

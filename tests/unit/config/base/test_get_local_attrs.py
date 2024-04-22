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
Test the `ConfigBase.get_local_attrs` class method.
"""

from __future__ import annotations

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


def test_decode_bool() -> None:
    """
    Check that decoding a `bool` attribute works properly
    using the default decoder.
    """

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
    """
    Check that decoding an `int` attribute works properly
    using the default decoder.
    """

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
    """
    Check that decoding a `float` attribute works properly
    using the default decoder.
    """

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
    """
    Check that decoding an `str` attribute works properly
    using the default decoder.
    """

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
    """
    Check that decoding a `list[int]` attribute works properly
    using the default decoder.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_list_int", "testAttr", {})],
            remote_attrs={"testAttr": [1, 2, 3]},
        ),
    ).test_list_int == [1, 2, 3]


def test_decode_list_str() -> None:
    """
    Check that decoding a `list[str]` attribute works properly
    using the default decoder.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_list_str", "testAttr", {})],
            remote_attrs={"testAttr": ["Hello", "World", "Buildarr"]},
        ),
    ).test_list_str == ["Hello", "World", "Buildarr"]


def test_decode_set_int() -> None:
    """
    Check that decoding a `set[int]` attribute works properly
    using the default decoder.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_set_int", "testAttr", {})],
            remote_attrs={"testAttr": [1, 2, 3]},
        ),
    ).test_set_int == {1, 2, 3}


def test_decode_set_str() -> None:
    """
    Check that decoding a `set[str]` attribute works properly
    using the default decoder.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_set_str", "testAttr", {})],
            remote_attrs={"testAttr": ["Hello", "World", "Buildarr"]},
        ),
    ).test_set_str == {"Hello", "World", "Buildarr"}


def test_decode_dict_int_str() -> None:
    """
    Check that decoding a `dict[int, str]` attribute works properly
    using the default decoder.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_dict_int_str", "testAttr", {})],
            remote_attrs={"testAttr": {1: "Hello, world!"}},
        ),
    ).test_dict_int_str == {1: "Hello, world!"}


@pytest.mark.parametrize("test_value", [1, "Hello, world!", ["Hello", "world!"]])
def test_decode_union_int_str_liststr(test_value) -> None:
    """
    Check that decoding a `int | str | list[str]` attribute works properly
    using the default decoder.
    """

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
    """
    Check that decoding an `str | None` attribute works properly
    using the default decoder.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_optional_str", "testAttr", {})],
                remote_attrs={"testAttr": test_value},
            ),
        ).test_optional_str
        == test_value
    )


def test_decoder() -> None:
    """
    Check that configuring a custom decoder using the `decoder`
    remote map entry parameter works properly.
    """

    assert (
        ConfigBase.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {"decoder": lambda v: v == "hello"})],
            remote_attrs={"testAttr": "hello"},
        )["test_attr"]
        is True
    )


def test_root_decoder() -> None:
    """
    Check that configuring a root decoder using the `root_decoder`
    remote map entry parameter works properly.
    """

    assert (
        ConfigBase.get_local_attrs(
            remote_map=[
                (
                    "test_attr",
                    "testAttr",
                    {"root_decoder": lambda vs: vs["testAttr"] == "hello"},
                ),
            ],
            remote_attrs={"testAttr": "hello"},
        )["test_attr"]
        is True
    )


def test_optional_true() -> None:
    """
    Check that the `optional` remote map entry parameter
    works properly when set to `True` for standard attributes.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_str", "testAttr", {"optional": True})],
                remote_attrs={},
            ),
        ).test_str
        == ""
    )


def test_optional_false() -> None:
    """
    Check that the `optional` remote map entry parameter
    raises an error when set to `False`, and a value for the attribute
    was not found in the remote configuration.
    """

    with pytest.raises(KeyError):
        Settings.get_local_attrs(
            remote_map=[("test_str", "testAttr", {"optional": False})],
            remote_attrs={},
        )


def test_optional_default() -> None:
    """
    Check that the default behaviour for the `optional` remote map entry parameter
    is `False`.
    """

    with pytest.raises(KeyError):
        Settings.get_local_attrs(
            remote_map=[("test_str", "testAttr", {})],
            remote_attrs={},
        )


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_field_decode(test_value) -> None:
    """
    Check decoding an Arr API field-style remote attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_optional_str", "testAttr", {"is_field": True})],
                remote_attrs={"fields": [{"name": "testAttr", "value": test_value}]},
            ),
        ).test_optional_str
        == test_value
    )


def test_field_unused_fields() -> None:
    """
    Check that unused fields do not affect parsing field attributes that
    are used.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_str", "testAttr", {"is_field": True})],
                remote_attrs={
                    "fields": [
                        {"name": "testAttr2"},
                        {"name": "testAttr", "value": "Hello, world!"},
                    ],
                },
            ),
        ).test_str
        == "Hello, world!"
    )


def test_field_optional() -> None:
    """
    Check that the `optional` remote map entry parameter works properly
    with field-style attributes.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_str", "testAttr", {"is_field": True, "optional": True})],
                remote_attrs={"fields": []},
            ),
        ).test_str
        == ""
    )


def test_field_default() -> None:
    """
    Check that the `field_default` remote map entry parameter works properly.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[
                    (
                        "test_str",
                        "testAttr",
                        {"is_field": True, "field_default": "Goodbye, world!"},
                    ),
                ],
                remote_attrs={"fields": [{"name": "testAttr"}]},
            ),
        ).test_str
        == "Goodbye, world!"
    )


def test_field_optional_default() -> None:
    """
    Check that an error is raised when a field value is not found,
    and neither `optional` nor `field_default` are defined.
    """

    with pytest.raises(ValueError, match="Remote field 'testAttr' not found"):
        Settings.get_local_attrs(
            remote_map=[("test_str", "testAttr", {"is_field": True})],
            remote_attrs={"fields": []},
        )


def test_field_default_undefined() -> None:
    """
    Check that an error is raised when a field is found, but a value
    was not found in it, and `field_default` is not provided in the
    remote map entry.
    """

    with pytest.raises(
        ValueError,
        match=(
            "'value' attribute not included for remote field 'testAttr' "
            "and 'field_default' not defined in local attribute"
        ),
    ):
        Settings.get_local_attrs(
            remote_map=[("test_str", "testAttr", {"is_field": True})],
            remote_attrs={"fields": [{"name": "testAttr"}]},
        )


# TODO: Make sure 'optional' also works for test_field_default_undefined's use case.

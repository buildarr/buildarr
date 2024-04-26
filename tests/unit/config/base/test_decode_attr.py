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
Test the `ConfigBase._decode_attr` class method.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Union

import pytest

from pydantic import Field
from typing_extensions import Annotated

from buildarr.config import ConfigBase


class ListSettings(ConfigBase):
    test_attr: List[str]


class SetSettings(ConfigBase):
    test_attr: Set[str]


class DictSettings(ConfigBase):
    test_attr: Dict[int, Set[str]]


class OptionalSettings(ConfigBase):
    test_attr: Optional[str]


class UnionSettings(ConfigBase):
    test_attr: Union[int, float, str]


class AnnotatedSettings(ConfigBase):
    test_attr: Annotated[Set[str], Field(alias="t_a")]


@pytest.mark.parametrize("test_value", [[], ["Hello, world!"]])
def test_list(test_value):
    """
    Check decoding a `list` type attribute.
    """

    assert ListSettings._decode_attr("test_attr", test_value) == test_value


@pytest.mark.parametrize("test_value", [[], ["Hello, world!"]])
def test_set(test_value):
    """
    Check decoding a `set` type attribute.
    """

    assert SetSettings._decode_attr("test_attr", test_value) == set(test_value)


def test_dict_empty():
    """
    Check encoding an empty `dict` type attribute.
    """

    assert DictSettings._decode_attr("test_attr", {}) == {}


def test_dict_nested():
    """
    Check encoding a `dict` type attribute with a nested data structure.
    """

    assert DictSettings._decode_attr("test_attr", {123: ["Hello, world!"]}) == {
        123: {"Hello, world!"}
    }


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_optional(test_value):
    """
    Check decoding optional attribute (an attribute that can also be `None`).
    """

    assert OptionalSettings._decode_attr("test_attr", test_value) == test_value


@pytest.mark.parametrize("test_value", [123, 123.456, "Hello, world!"])
def test_union(test_value):
    """
    Check decoding a union type attribute.
    """

    assert UnionSettings._decode_attr("test_attr", test_value) == test_value


def test_annotated():
    """
    Check decoding an attribute with annotations defined.
    """

    assert AnnotatedSettings._decode_attr("test_attr", ["Hello, world!"]) == {"Hello, world!"}

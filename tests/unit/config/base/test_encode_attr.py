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
Test the `ConfigBase._encode_attr` class method.
"""

from __future__ import annotations

import pytest

from buildarr.config import ConfigBase


@pytest.mark.parametrize("test_value", [[], ["Hello, world!"]])
def test_list(test_value):
    """
    Check encoding a `list` type value.
    """

    assert ConfigBase._encode_attr(test_value) == test_value


@pytest.mark.parametrize("test_value", [set(), {"Hello, world!"}])
def test_set(test_value):
    """
    Check encoding a `set` type value.
    """

    assert ConfigBase._encode_attr(test_value) == list(test_value)


def test_dict_empty():
    """
    Check encoding an empty `dict` type value.
    """

    assert ConfigBase._encode_attr({}) == {}


def test_dict_nested():
    """
    Check encoding a `dict` type value with a nested data structure.
    """

    assert ConfigBase._encode_attr({123: {"Hello, world!"}}) == {123: ["Hello, world!"]}

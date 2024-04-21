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
Test the `BaseEnum` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from buildarr.config import ConfigBase
from buildarr.types import BaseEnum


class SingleValueEnum(BaseEnum):
    zero = 0
    one = 1
    two = 2
    three = 3


class MultiValueEnum(BaseEnum):
    ZERO = (0, "zero")
    ONE = (1, "one")
    TWO = (2, "two")
    THREE = (3, "three")


class Settings(ConfigBase):
    test_single_value: SingleValueEnum = SingleValueEnum.zero
    test_multi_value: MultiValueEnum = MultiValueEnum.ZERO


def test_single_value_decode() -> None:
    """
    Check decoding a single-value enumeration attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_single_value", "testAttr", {})],
                remote_attrs={"testAttr": 1},
            ),
        ).test_single_value
        == SingleValueEnum.one
    )


def test_single_value_create_encode() -> None:
    """
    Check encoding a single-value enumeration attribute
    during resource creation.
    """

    assert Settings(test_single_value=SingleValueEnum.one).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_single_value", "testAttr", {})],
    ) == {"testAttr": 1}


def test_single_value_create_format(caplog) -> None:
    """
    Check logging formatting of a single-value enumeration attribute value
    during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_single_value=SingleValueEnum.one).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_single_value", "testAttr", {})],
    ) == {"testAttr": 1}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_single_value: 'one' -> (created)"


def test_single_value_update_encode() -> None:
    """
    Check encoding a single-value enumeration attribute
    during resource updates.
    """

    assert Settings(test_single_value=SingleValueEnum.one).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_single_value", "testAttr", {})],
    ) == (True, {"testAttr": 1})


@pytest.mark.parametrize("test_value", [1, "one"])
def test_multi_value_decode(test_value) -> None:
    """
    Check decoding a multi-value enumeration attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_multi_value", "testAttr", {})],
                remote_attrs={"testAttr": test_value},
            ),
        ).test_multi_value
        == MultiValueEnum.ONE
    )


def test_multi_value_create_encode() -> None:
    """
    Check encoding a multi-value enumeration attribute
    during resource creation.
    """

    assert Settings(test_multi_value=MultiValueEnum.ONE).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_multi_value", "testAttr", {})],
    ) == {"testAttr": 1}


def test_multi_value_create_format(caplog) -> None:
    """
    Check that for multi-value enums, the first str-type value provided
    in the list of values is used when formatting for logging output,
    **not** the enumeration name on the class.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_multi_value=MultiValueEnum.ONE).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_multi_value", "testAttr", {})],
    ) == {"testAttr": 1}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_multi_value: 'one' -> (created)"


def test_multi_value_update_encode() -> None:
    """
    Check encoding a multi-value enumeration attribute
    during resource updates.
    """

    assert Settings(test_multi_value=MultiValueEnum.ONE).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(),
        remote_map=[("test_multi_value", "testAttr", {})],
    ) == (True, {"testAttr": 1})

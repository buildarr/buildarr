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
Test the `NonEmptyStr` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from pydantic import ValidationError

from buildarr.config import ConfigBase
from buildarr.types import NonEmptyStr


class Settings(ConfigBase):
    test_attr: NonEmptyStr


def test_decode() -> None:
    """
    Check decoding a local attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {})],
                remote_attrs={"testAttr": "Hello, world!"},
            ),
        ).test_attr
        == "Hello, world!"
    )


def test_create_encode() -> None:
    """
    Check encoding a remote attribute during resource creation.
    """

    assert Settings(test_attr="Hello, world!").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "Hello, world!"}


def test_create_format(caplog) -> None:
    """
    Check logging formatting of an attribute value during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr="Hello, world!").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "Hello, world!"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 'Hello, world!' -> (created)"


def test_update_encode() -> None:
    """
    Check encoding a remote attribute during resource updates.
    """

    assert Settings(test_attr="Hello, world!").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="Goodbye, world!"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "Hello, world!"})


def test_empty() -> None:
    """
    Check that an error is returned when an empty string is supplied.
    """

    with pytest.raises(
        ValidationError,
        match=(
            "String should have at least 1 character "
            r"\[type=string_too_short, input_value='', input_type=str\]"
        ),
    ):
        Settings(test_attr="")

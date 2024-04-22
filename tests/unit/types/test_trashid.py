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
Test the `TrashID` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from pydantic import ValidationError

from buildarr.config import ConfigBase
from buildarr.types import TrashID


class Settings(ConfigBase):
    test_attr: TrashID


@pytest.mark.parametrize(
    "test_attr",
    ["387e6278d8e06083d813358762e0ac63", "387E6278D8E06083D813358762E0AC63"],
)
def test_decode(test_attr) -> None:
    """
    Check decoding a local attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {})],
                remote_attrs={"testAttr": test_attr},
            ),
        ).test_attr
        == "387e6278d8e06083d813358762e0ac63"
    )


@pytest.mark.parametrize(
    "test_attr",
    ["387e6278d8e06083d813358762e0ac63", "387E6278D8E06083D813358762E0AC63"],
)
def test_create_encode(test_attr) -> None:
    """
    Check encoding a remote attribute during resource creation.
    """

    assert Settings(test_attr=test_attr).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "387e6278d8e06083d813358762e0ac63"}


@pytest.mark.parametrize(
    "test_attr",
    ["387e6278d8e06083d813358762e0ac63", "387E6278D8E06083D813358762E0AC63"],
)
def test_create_format(test_attr, caplog) -> None:
    """
    Check logging formatting of an attribute value during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr=test_attr).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "387e6278d8e06083d813358762e0ac63"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == (
        "test.settings.test_attr: '387e6278d8e06083d813358762e0ac63' -> (created)"
    )


@pytest.mark.parametrize(
    "test_attr",
    ["387e6278d8e06083d813358762e0ac63", "387E6278D8E06083D813358762E0AC63"],
)
def test_update_encode(test_attr) -> None:
    """
    Check encoding a remote attribute during resource updates.
    """

    assert Settings(test_attr=test_attr).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="949c16fe0a8147f50ba82cc2df9411c9"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "387e6278d8e06083d813358762e0ac63"})


def test_empty() -> None:
    """
    Check that an error is returned when an empty string is provided.
    """

    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.any_str\.min_length; limit_value=32",
    ):
        Settings(test_attr="")


def test_too_short() -> None:
    """
    Check that an error is returned when the provided string is too short.
    """

    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.any_str\.min_length; limit_value=32",
    ):
        Settings(test_attr="387e6278d8e06083d813358762e0ac6")


def test_too_long() -> None:
    """
    Check that an error is returned when the provided string is too long.
    """

    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.any_str\.max_length; limit_value=32",
    ):
        Settings(test_attr="387e6278d8e06083d813358762e0ac630")


def test_invalid_characters() -> None:
    """
    Check that an error is returned when the provided string is not a valid TRaSH ID.
    """

    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.str\.regex",
    ):
        Settings(test_attr="387e6278d8e06083d813358762e0ac6z")

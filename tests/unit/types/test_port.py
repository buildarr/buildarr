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
Test the `Port` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from pydantic import ValidationError

from buildarr.config import ConfigBase
from buildarr.types import Port


class Settings(ConfigBase):
    test_attr: Port


def test_decode() -> None:
    """
    Check decoding a local attribute.
    """

    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {})],
                remote_attrs={"testAttr": 8989},
            ),
        ).test_attr
        == 8989  # noqa: PLR2004
    )


def test_create_encode() -> None:
    """
    Check encoding a remote attribute during resource creation.
    """

    assert Settings(test_attr=8989).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": 8989}


def test_create_format(caplog) -> None:
    """
    Check logging formatting of an attribute value during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr=8989).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": 8989}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 8989 -> (created)"


def test_update_encode() -> None:
    """
    Check encoding a remote attribute during resource updates.
    """

    assert Settings(test_attr=8989).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr=7878),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": 8989})


@pytest.mark.parametrize("test_value", [0, -8989])
def test_less_than_valid(test_value) -> None:
    """
    Check that an error is returned when the provided integer is less than
    than the range of a valid port number.
    """

    with pytest.raises(
        ValidationError,
        match=(
            "Input should be greater than or equal to 1 "
            r"\[type=greater_than_equal"
            f", input_value={test_value!r}"
            r", input_type=int\]"
        ),
    ):
        Settings(test_attr=test_value)


def test_greater_than_valid() -> None:
    """
    Check that an error is returned when the provided integer is greater than
    than the range of a valid port number.
    """

    with pytest.raises(
        ValidationError,
        match=(
            "Input should be less than or equal to 65535 "
            r"\[type=less_than_equal, input_value=65536, input_type=int\]"
        ),
    ):
        Settings(test_attr=65536)


def test_serialization() -> None:
    """
    Check serialising a local attribute value to YAML.
    """

    assert Settings(test_attr=8989).model_dump_yaml() == "test_attr: 8989\n"

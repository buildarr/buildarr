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
    assert Settings(test_attr=8989).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": 8989}


def test_create_format(caplog) -> None:
    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr=8989).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": 8989}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 8989 -> (created)"


def test_update_encode() -> None:
    assert Settings(test_attr=8989).get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr=7878),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": 8989})


@pytest.mark.parametrize("test_value", [0, -8989])
def test_lower_than_valid(test_value) -> None:
    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.number\.not_ge; limit_value=1",
    ):
        Settings(test_attr=test_value)


def test_higher_than_valid() -> None:
    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.number\.not_le; limit_value=65535",
    ):
        Settings(test_attr=65536)

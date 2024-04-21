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
Test the `RssUrl` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from pydantic import ValidationError

from buildarr.config import ConfigBase
from buildarr.types import RssUrl


class Settings(ConfigBase):
    test_attr: RssUrl


@pytest.mark.parametrize("test_value", ["rss://rss.example.com", "rss://127.0.0.1"])
def test_decode(test_value) -> None:
    test_attr = Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={"testAttr": test_value},
        ),
    ).test_attr
    assert isinstance(test_attr, RssUrl)
    assert test_attr.scheme == "rss"
    assert str(test_attr) == test_value


def test_create_encode() -> None:
    assert Settings(test_attr="rss://rss.example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "rss://rss.example.com"}


def test_create_format(caplog) -> None:
    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr="rss://rss.example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "rss://rss.example.com"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 'rss://rss.example.com' -> (created)"


def test_update_encode() -> None:
    assert Settings(test_attr="rss://rss.example.com").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="rss://127.0.0.1"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "rss://rss.example.com"})


def test_empty() -> None:
    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.any_str\.min_length; limit_value=1",
    ):
        Settings(test_attr="")


@pytest.mark.parametrize("scheme", ["http", "https", "file"])
def test_invalid_scheme(scheme) -> None:
    with pytest.raises(
        ValidationError,
        match=r"type=value_error\.url\.scheme; allowed_schemes={'rss'}",
    ):
        Settings(test_attr=f"{scheme}://www.example.com")

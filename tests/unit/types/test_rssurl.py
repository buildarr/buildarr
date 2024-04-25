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

from pydantic import AnyUrl, ValidationError

from buildarr.config import ConfigBase
from buildarr.types import RssUrl


class Settings(ConfigBase):
    test_attr: RssUrl


@pytest.mark.parametrize("test_value", ["rss://rss.example.com", "rss://127.0.0.1"])
def test_decode(test_value) -> None:
    """
    Check decoding a local attribute.
    """

    test_attr = Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={"testAttr": test_value},
        ),
    ).test_attr
    assert isinstance(test_attr, AnyUrl)
    assert test_attr.scheme == "rss"
    assert str(test_attr) == test_value


def test_create_encode() -> None:
    """
    Check encoding a remote attribute during resource creation.
    """

    assert Settings(test_attr="rss://rss.example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "rss://rss.example.com"}


def test_create_format(caplog) -> None:
    """
    Check logging formatting of an attribute value during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr="rss://rss.example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "rss://rss.example.com"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 'rss://rss.example.com' -> (created)"


def test_update_encode() -> None:
    """
    Check encoding a remote attribute during resource updates.
    """

    assert Settings(test_attr="rss://rss.example.com").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="rss://127.0.0.1"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "rss://rss.example.com"})


def test_empty() -> None:
    """
    Check that an error is returned when an empty string is supplied.
    """

    with pytest.raises(
        ValidationError,
        match=(
            "Input should be a valid URL, input is empty "
            r"\[type=url_parsing, input_value='', input_type=str\]"
        ),
    ):
        Settings(test_attr="")


@pytest.mark.parametrize("scheme", ["http", "https", "file"])
def test_invalid_scheme(scheme) -> None:
    """
    Check that an error is returned when the provided URL uses the incorrect scheme.
    """

    with pytest.raises(
        ValidationError,
        match=(
            "URL scheme should be 'rss' "
            r"\[type=url_scheme"
            f", input_value='{scheme}://www.example.com'"
            r", input_type=str\]"
        ),
    ):
        Settings(test_attr=f"{scheme}://www.example.com")


def test_serialization() -> None:
    """
    Check serialising a local attribute value to YAML.
    """

    assert (
        Settings(test_attr="rss://rss.example.com").model_dump_yaml()
        == "test_attr: rss://rss.example.com\n"
    )

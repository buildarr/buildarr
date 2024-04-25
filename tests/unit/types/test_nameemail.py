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
Test the `NameEmail` configuration attribute type.
"""

from __future__ import annotations

import logging

import pytest

from pydantic import NameEmail, ValidationError

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_attr: NameEmail


def test_decode_email() -> None:
    """
    Check decoding a standard email address.
    """

    test_attr = Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={"testAttr": "test@example.com"},
        ),
    ).test_attr
    assert isinstance(test_attr, NameEmail)
    assert test_attr.name == "test"
    assert test_attr.email == "test@example.com"


def test_decode_name_email() -> None:
    """
    Check decoding an RFC-5322 formatted mailbox address.
    """

    test_attr = Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={"testAttr": "Test Example <test@example.com>"},
        ),
    ).test_attr
    assert isinstance(test_attr, NameEmail)
    assert test_attr.name == "Test Example"
    assert test_attr.email == "test@example.com"


def test_create_encode_email() -> None:
    """
    Check encoding a standard email address during resource creation.
    """

    assert Settings(test_attr="test@example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "test <test@example.com>"}


def test_create_encode_name_email() -> None:
    """
    Check encoding an RFC-5322 formatted mailbox address during resource creation.
    """

    assert Settings(test_attr="Test Example <test@example.com>").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "Test Example <test@example.com>"}


def test_create_format_email(caplog) -> None:
    """
    Check logging formatting of a standard email address during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr="test@example.com").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "test <test@example.com>"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_attr: 'test <test@example.com>' -> (created)"


def test_create_format_name_email(caplog) -> None:
    """
    Check logging formatting of an RFC-5322 formatted mailbox address during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    assert Settings(test_attr="Test Example <test@example.com>").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "Test Example <test@example.com>"}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == (
        "test.settings.test_attr: 'Test Example <test@example.com>' -> (created)"
    )


def test_update_encode_email() -> None:
    """
    Check encoding a standard email address during resource updates.
    """

    assert Settings(test_attr="test@example.com").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="production@example.com"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "test <test@example.com>"})


def test_update_encode_name_email() -> None:
    """
    Check encoding an RFC-5322 formatted mailbox address during resource updates.
    """

    assert Settings(test_attr="Test Example <test@example.com>").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="Production Example <production@example.com>"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "Test Example <test@example.com>"})


@pytest.mark.parametrize("test_attr", ["", "test"])
def test_invalid_email_address(test_attr) -> None:
    """
    Check that an error is returned when an invalid email address is provided.
    """

    with pytest.raises(
        ValidationError,
        match=(
            r"value is not a valid email address: The email address is not valid\. "
            r"It must have exactly one @-sign\. "
            r"\[type=value_error"
            f", input_value={test_attr!r}"
            r", input_type=str\]"
        ),
    ):
        Settings(test_attr=test_attr)

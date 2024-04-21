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
Test the `ConfigBase.log_delete_remote_attrs` method.
"""

from __future__ import annotations

import logging

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_bool: bool = False
    test_int: int = 0


def test_delete_false(caplog) -> None:
    """
    Check that when `delete` is set to `False`, the correct `DEBUG` logging messages
    for an unmanaged resource are output.
    """

    caplog.set_level(logging.DEBUG)
    Settings().log_delete_remote_attrs(
        tree="test.settings",
        remote_map=[("test_bool", "testBool", {}), ("test_int", "testInt", {})],
        delete=False,
    )
    test_bool_record = caplog.records[0]
    test_int_record = caplog.records[1]
    assert test_bool_record.levelname == "DEBUG"
    assert test_bool_record.message == "test.settings.test_bool: False (unmanaged)"
    assert test_int_record.levelname == "DEBUG"
    assert test_int_record.message == "test.settings.test_int: 0 (unmanaged)"


def test_delete_true(caplog) -> None:
    """
    Check that when `delete` is set to `False`, the correct `INFO` logging messages
    for a deleted resource are output.
    """

    caplog.set_level(logging.DEBUG)
    Settings().log_delete_remote_attrs(
        tree="test.settings",
        remote_map=[("test_bool", "testBool", {}), ("test_int", "testInt", {})],
        delete=True,
    )
    test_bool_record = caplog.records[0]
    test_int_record = caplog.records[1]
    assert test_bool_record.levelname == "INFO"
    assert test_bool_record.message == "test.settings.test_bool: False -> (deleted)"
    assert test_int_record.levelname == "INFO"
    assert test_int_record.message == "test.settings.test_int: 0 -> (deleted)"


def test_delete_false_formatter(caplog) -> None:
    """
    Check that the `formatter` remote map entry parameter works properly
    when a resource is unmanaged.
    """

    caplog.set_level(logging.DEBUG)
    Settings().log_delete_remote_attrs(
        tree="test.settings",
        remote_map=[
            ("test_bool", "testAttr", {"formatter": lambda v: "Yes" if v else "No"}),
        ],
        delete=False,
    )
    record = caplog.records[0]
    assert record.levelname == "DEBUG"
    assert record.message == "test.settings.test_bool: 'No' (unmanaged)"


def test_delete_true_formatter(caplog) -> None:
    """
    Check that the `formatter` remote map entry parameter works properly
    when a resource is deleted.
    """

    caplog.set_level(logging.DEBUG)
    Settings().log_delete_remote_attrs(
        tree="test.settings",
        remote_map=[
            ("test_bool", "testAttr", {"formatter": lambda v: "Yes" if v else "No"}),
        ],
        delete=True,
    )
    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == "test.settings.test_bool: 'No' -> (deleted)"

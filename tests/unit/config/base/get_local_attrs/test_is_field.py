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
Test decoding remote attributes using configuration attribute types
on the `ConfigBase.get_local_attrs` class method.
"""

from __future__ import annotations

from typing import Optional

import pytest

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_attr: Optional[str] = None


@pytest.mark.parametrize("test_value", [None, "Hello, world!"])
def test_field_decode(test_value) -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {"is_field": True})],
                remote_attrs={"fields": [{"name": "testAttr", "value": test_value}]},
            ),
        ).test_attr
        == test_value
    )


def test_field_unused_fields() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {"is_field": True})],
                remote_attrs={
                    "fields": [
                        {"name": "testAttr2"},
                        {"name": "testAttr", "value": "Hello, world!"},
                    ],
                },
            ),
        ).test_attr
        == "Hello, world!"
    )


def test_field_optional() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[("test_attr", "testAttr", {"is_field": True, "optional": True})],
                remote_attrs={"fields": []},
            ),
        ).test_attr
        is None
    )


def test_field_default() -> None:
    assert (
        Settings(
            **Settings.get_local_attrs(
                remote_map=[
                    (
                        "test_attr",
                        "testAttr",
                        {"is_field": True, "field_default": "Goodbye, world!"},
                    ),
                ],
                remote_attrs={"fields": [{"name": "testAttr"}]},
            ),
        ).test_attr
        == "Goodbye, world!"
    )


def test_field_optional_default() -> None:
    with pytest.raises(ValueError, match="Remote field 'testAttr' not found"):
        Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {"is_field": True})],
            remote_attrs={"fields": []},
        )


def test_field_default_undefined() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "'value' attribute not included for remote field 'testAttr' "
            "and 'field_default' not defined in local attribute"
        ),
    ):
        Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {"is_field": True})],
            remote_attrs={"fields": [{"name": "testAttr"}]},
        )

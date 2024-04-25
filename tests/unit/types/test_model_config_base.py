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

import pytest

from pydantic import Field, ValidationError

from buildarr.config import ConfigBase
from buildarr.types import NonEmptyStr


class Settings(ConfigBase):
    test_attr: NonEmptyStr = Field(alias="alias_attr")


def test_serialization_field_name() -> None:
    """
    Check serialising an attribute value, referred to by its field name,to YAML.
    """

    assert Settings(test_attr="Hello, world!").model_dump_yaml() == "test_attr: Hello, world!\n"


def test_serialization_alias() -> None:
    """
    Check that serialising an attribute value, referred to by an alias, to YAML
    results in the actual field name being used, instead of the alias.
    """

    assert Settings(alias_attr="Hello, world!").model_dump_yaml() == "test_attr: Hello, world!\n"


def test_validation_error_field_name() -> None:
    """
    Check that when an error is railed on an attribute that has an alias defined,
    if the value is set using the actual field name, the field name is logged
    in the error message.
    """

    with pytest.raises(ValidationError, match="test_attr"):
        Settings(test_attr="")


def test_validation_error_alias() -> None:
    """
    Check that when an error is railed on an attribute set using an alias,
    the alias is logged in the error message.
    """

    with pytest.raises(ValidationError, match="alias_attr"):
        Settings(alias_attr="")

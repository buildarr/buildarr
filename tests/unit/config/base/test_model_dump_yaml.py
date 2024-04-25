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
Test the `ConfigBase.model_dump_yaml` method.
"""

from __future__ import annotations

from typing import Optional

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_attr: int
    optional_attr: Optional[int] = None


def test_default() -> None:
    """
    Check that the output using the default options is correct.
    """

    assert Settings(test_attr=8989).model_dump_yaml() == "test_attr: 8989\noptional_attr: null\n"


def test_exclude_unset() -> None:
    """
    Check that when the `exclude_unset` option is enabled,
    fields that are not explicitly set are not included in the output.
    """

    assert Settings(test_attr=8989).model_dump_yaml(exclude_unset=True) == "test_attr: 8989\n"


def test_yaml() -> None:
    """
    Check that the `ConfigBase.yaml` alias method works.
    """

    assert Settings(test_attr=8989).yaml() == "test_attr: 8989\noptional_attr: null\n"


def test_yaml_args() -> None:
    """
    Check that arguments are passed from the `ConfigBase.yaml` alias
    to the `ConfigBase.model_dump_yaml` method.
    """

    assert Settings(test_attr=8989).yaml(exclude_unset=True) == "test_attr: 8989\n"

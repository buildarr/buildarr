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
Test the `root_decoder` remote map entry optional parameter functionality
on the `ConfigBase.get_local_attrs` class method.
"""

from __future__ import annotations

from buildarr.config import ConfigBase
from buildarr.util import str_to_bool


def test_root_decoder() -> None:
    assert (
        ConfigBase.get_local_attrs(
            remote_map=[
                (
                    "test_attr",
                    "testAttr",
                    {"root_decoder": lambda vs: str_to_bool(vs["testAttr"])},
                ),
            ],
            remote_attrs={"testAttr": "true"},
        )["test_attr"]
        is True
    )

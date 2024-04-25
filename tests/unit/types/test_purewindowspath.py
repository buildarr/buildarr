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
Test the `PurePosixPath` configuration attribute type.
"""

from __future__ import annotations

import logging

from pathlib import PureWindowsPath

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_attr: PureWindowsPath


def test_decode() -> None:
    """
    Check decoding a local attribute.
    """

    assert Settings(
        **Settings.get_local_attrs(
            remote_map=[("test_attr", "testAttr", {})],
            remote_attrs={"testAttr": "C:\\Users\\buildarr\\buildarr.yml"},
        ),
    ).test_attr == PureWindowsPath("C:\\Users\\buildarr\\buildarr.yml")


def test_create_encode() -> None:
    """
    Check encoding a remote attribute during resource creation.
    """

    assert Settings(test_attr="C:\\Users\\buildarr\\buildarr.yml").get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": "C:\\Users\\buildarr\\buildarr.yml"}


def test_create_format(caplog) -> None:
    """
    Check logging formatting of an attribute value during resource creation.
    """

    caplog.set_level(logging.DEBUG)

    test_attr = "C:\\Users\\buildarr\\buildarr.yml"

    assert Settings(test_attr=test_attr).get_create_remote_attrs(
        tree="test.settings",
        remote_map=[("test_attr", "testAttr", {})],
    ) == {"testAttr": test_attr}

    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.message == f"test.settings.test_attr: {test_attr!r} -> (created)"


def test_update_encode() -> None:
    """
    Check encoding a remote attribute during resource updates.
    """

    assert Settings(test_attr="C:\\Users\\buildarr\\buildarr.yml").get_update_remote_attrs(
        tree="test.settings",
        remote=Settings(test_attr="C:\\Users\\buildarr\\sonarr.yml"),
        remote_map=[("test_attr", "testAttr", {})],
    ) == (True, {"testAttr": "C:\\Users\\buildarr\\buildarr.yml"})


def test_serialization() -> None:
    """
    Check serialising a local attribute value to YAML.
    """

    assert (
        Settings(test_attr="C:\\Users\\buildarr\\buildarr.yml").model_dump_yaml()
        == "test_attr: C:\\Users\\buildarr\\buildarr.yml\n"
    )

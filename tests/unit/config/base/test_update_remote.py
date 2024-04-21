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
Test the `ConfigBase.delete_remote` method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from buildarr.config import ConfigBase

if TYPE_CHECKING:
    from typing import List


class Settings(ConfigBase):
    updated_value: bool = False
    check_unmanaged_value: bool = False

    def update_remote(self, tree, secrets, remote, check_unmanaged):
        assert tree == "general.settings"
        secrets.append(True)
        assert check_unmanaged == self.check_unmanaged_value
        return remote.updated_value


class GeneralSettings(ConfigBase):
    settings: Settings = Settings()
    general_value: bool = False


def test_nested_config_unchanged() -> None:
    secrets: List[bool] = []
    assert not GeneralSettings().update_remote(
        tree="general",
        secrets=secrets,
        remote=GeneralSettings(),
    )
    assert secrets == [True]


def test_nested_config_changed() -> None:
    secrets: List[bool] = []
    assert GeneralSettings().update_remote(
        tree="general",
        secrets=secrets,
        remote=GeneralSettings(settings=Settings(updated_value=True)),
    )
    assert secrets == [True]


def test_secrets() -> None:
    secrets: List[bool] = []
    assert not GeneralSettings(secrets_value=True).update_remote(
        tree="general",
        secrets=secrets,
        remote=GeneralSettings(),
    )
    assert secrets == [True]


@pytest.mark.parametrize("test_value", [False, True])
def test_check_unmanaged(test_value) -> None:
    secrets: List[bool] = []
    assert not GeneralSettings(settings=Settings(check_unmanaged_value=test_value)).update_remote(
        tree="general",
        secrets=secrets,
        remote=GeneralSettings(),
        check_unmanaged=test_value,
    )
    assert secrets == [True]

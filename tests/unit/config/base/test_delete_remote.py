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

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    settings_value: bool = False

    def delete_remote(self, tree, secrets, remote):
        assert tree == "general.settings"
        assert remote.settings_value
        return secrets


class GeneralSettings(ConfigBase):
    settings: Settings = Settings()
    general_value: bool = False


def test_nested_config_unchanged() -> None:
    """
    Check that running `delete_remote` on a nested configuration object
    works, and that if `delete_remote` returns `False`, it is propagated
    back up to the caller.
    """

    assert not GeneralSettings().delete_remote(
        tree="general",
        secrets=False,
        remote=GeneralSettings(settings=Settings(settings_value=True)),
    )


def test_nested_config_changed() -> None:
    """
    Check that running `delete_remote` on a nested configuration object
    works, and that if `delete_remote` returns `True`, it is propagated
    back up to the caller.
    """

    assert GeneralSettings().delete_remote(
        tree="general",
        secrets=True,
        remote=GeneralSettings(settings=Settings(settings_value=True)),
    )

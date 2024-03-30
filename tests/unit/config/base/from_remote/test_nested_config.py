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
Test the `ConfigBase.from_remote` class method's handling of nested configuration attributes.
"""

from __future__ import annotations

from buildarr.config.base import ConfigBase


class TestSettings(ConfigBase):
    test_value: bool = False

    @classmethod
    def from_remote(cls, secrets):
        assert secrets == "Hello, world!"
        return TestSettings(test_value=True)


class GeneralSettings(ConfigBase):
    test: TestSettings = TestSettings()
    general_value: bool = False


def test_nested_config() -> None:
    general_settings = GeneralSettings.from_remote(secrets="Hello, world!")
    assert general_settings.test.test_value is True
    assert general_settings.general_value is False

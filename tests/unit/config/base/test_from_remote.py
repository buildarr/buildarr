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
Test the `ConfigBase.from_remote` class method.
"""

from __future__ import annotations

from typing import Optional

from buildarr.config import ConfigBase


class Settings(ConfigBase):
    test_value: bool = False
    secret_value: Optional[str] = None

    @classmethod
    def from_remote(cls, secrets):
        return Settings(test_value=True, secret_value=secrets)


class GeneralSettings(ConfigBase):
    test: Settings = Settings()
    general_value: bool = False


def test_nested_config() -> None:
    secrets = "Hello, world!"
    general_settings = GeneralSettings.from_remote(secrets=secrets)
    assert general_settings.test.test_value is True
    assert general_settings.test.secret_value == secrets
    assert general_settings.general_value is False

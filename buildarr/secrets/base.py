# Copyright (C) 2023 Callum Dickinson
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
Buildarr secrets metadata base class.
"""


from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from pydantic import BaseModel, SecretStr

from ..plugins import Config

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self


class SecretsBase(BaseModel, Generic[Config]):
    """
    Secrets metadata section base class.

    When implementing nested sections in a secrets plugin, this class should be used.
    """

    @classmethod
    def read(cls, path: Path) -> Self:
        """
        Load the secrets metadata from a JSON file, and return the corresponding object.

        Args:
            path (Path): Secrets JSON file to read from

        Returns:
            Secrets metadata object
        """
        return cls.parse_file(path, content_type="json")

    def write(self, path: Path) -> None:
        """
        Serialise the secrets metadata object and write it to a JSON file.

        Args:
            path (Path): Secrets JSON file to write to
        """
        path.write_text(self.json())

    class Config:
        validate_assignment = True
        json_encoders = {SecretStr: lambda v: v.get_secret_value()}

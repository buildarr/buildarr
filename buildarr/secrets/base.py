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

from typing import Generic

from pydantic import BaseModel

from ..plugins import Config
from ..types import ModelConfigBase


class SecretsBase(BaseModel, Generic[Config]):
    """
    Secrets metadata section base class.

    When implementing nested sections in a secrets plugin, this class should be used.
    """

    class Config(ModelConfigBase):
        """
        Buildarr secrets model class settings.

        Sets some required parameters for serialisation,
        parsing and validation to work correctly.

        To set additional parameters in your implementing class, subclass this class:

        ```python
        from __future__ import annotations

        from typing import TYPE_CHECKING
        from buildarr.secrets import SecretsBase

        if TYPE_CHECKING:
            from .config import ExampleConfig
            class _ExampleSecrets(SecretsBase[ExampleSecrets]):
                ...
        else:
            class _ExampleSecrets(SecretsBase):
                ...

        class ExampleSecrets(_ExampleSecrets):
            ...

            class Config(_ExampleSecrets.Config):
                ...  # Add model configuration attributes here.
        ```
        """

        pass

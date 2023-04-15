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
Dummy plugin configuration utility classes and functions.
"""


from __future__ import annotations

from typing import TYPE_CHECKING

from buildarr.config import ConfigBase

# Define the base class for Dummy configuration classes.
# Subclassing this conditionally-created class allows Mypy to
# properly resolve secrets type declarations.
if TYPE_CHECKING:
    from ..secrets import DummySecrets

    class DummyConfigBase(ConfigBase[DummySecrets]):
        pass

else:

    class DummyConfigBase(ConfigBase):
        pass

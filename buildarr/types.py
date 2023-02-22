# -*- coding: utf-8 -*-

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
Buildarr general purpose type hints, used in plugin models.
"""


from __future__ import annotations

import re

from enum import Enum, IntEnum
from typing import Any, Callable, Generator

from pydantic import AnyUrl, ConstrainedInt, ConstrainedStr, Field, SecretStr
from typing_extensions import Annotated, Self

Password = Annotated[SecretStr, Field(min_length=1)]
"""
Constrained secrets string type for password fields. Required to be non-empty.
"""


class RssUrl(AnyUrl):
    """
    Constrained URL type for RSS URLs.

    ```python
    from typing import TYPE_CHECKING
    from buildarr.config import ConfigBase, RssUrl

    if TYPE_CHECKING:
        from .secrets import ExampleSecrets
        class ExampleConfigBase(ConfigBase[ExampleSecrets]):
            ...
    else:
        class ExampleConfigBase(ConfigBase):
            ...

    class ExampleConfig(ExampleConfigBase):
        rss_url: RssUrl
    ```
    """

    allowed_schemes = ["rss"]


class Port(ConstrainedInt):
    """
    Constrained integer type for TCP/UDP port numbers.

    Valid ports range from 1 to 65535 (a 16-bit integer).

    ```python
    from typing import TYPE_CHECKING
    from buildarr.config import ConfigBase, NonEmptyStr, Port

    if TYPE_CHECKING:
        from .secrets import ExampleSecrets
        class ExampleConfigBase(ConfigBase[ExampleSecrets]):
            ...
    else:
        class ExampleConfigBase(ConfigBase):
            ...

    class ExampleConfig(ExampleConfigBase):
        host: NonEmptyStr
        port: Port
    ```
    """

    ge = 1
    le = 65535


class NonEmptyStr(ConstrainedStr):
    """
    Constrained string type for non-empty strings.

    When validated in a Buildarr configuration, empty strings
    or strings composed only of whitespace will fail validation.

    ```python
    from buildarr.config import ConfigBase, NonEmptyStr, Port

    class ExampleConfig(ConfigBase):
        host: NonEmptyStr
        port: Port
    ```
    """

    min_length = 1
    strip_whitespace = True


class TrashID(ConstrainedStr):
    """
    Constrained string type for TRaSH-Guides resource IDs.

    Accepts any valid TRaSH-Guides ID, and is case-insensitive,
    converting to lower case internally.

    ```python
    from typing import TYPE_CHECKING
    from buildarr.config import ConfigBase, TrashID

    if TYPE_CHECKING:
        from .secrets import ExampleSecrets
        class ExampleConfigBase(ConfigBase[ExampleSecrets]):
            ...
    else:
        class ExampleConfigBase(ConfigBase):
            ...

    class ExampleConfig(ExampleConfigBase):
        trash_id: TrashID
    ```
    """

    regex = re.compile("[A-Fa-f0-9]+")
    min_length = 32
    max_length = 32
    to_lower = True


class BaseEnum(Enum):
    """
    Enumeration base class for use in Buildarr configurations.

    In the Buildarr configurations, either the enumeration's value or
    the corresponding name can be specified. The name parsing is case-insensitive.
    """

    @classmethod
    def from_name_str(cls, name_str: str) -> Self:
        """
        Get the enumeration object corresponding to the given name case-insensitively.

        Args:
            name_str (str): Name of the enumeration value (case insensitive).

        Raises:
            KeyError: When the enumeration name is invalid (does not exist).

        Returns:
            The enumeration object for the given name
        """
        name = name_str.lower().replace("-", "_")
        for obj in cls:
            if obj.name.lower() == name:
                return obj
        raise KeyError(repr(name))

    def to_name_str(self) -> str:
        """
        Return the name for this enumaration object.

        Returns:
            Enumeration name
        """
        return self.name.replace("_", "-")

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Self], None, None]:
        """
        Pass class validation functions to Pydantic.

        Yields:
            Validation class functions
        """
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        """
        Validate and coerce the given value to an enumeration object.

        Args:
            value (Any): Object to validate and coerce

        Raises:
            ValueError: If a enumeration object corresponding with the value cannot be found

        Returns:
            Enumeration object corresponding to the given value
        """
        try:
            return cls(value)
        except ValueError:
            try:
                try:
                    return cls(str(value))
                except ValueError:
                    return cls.from_name_str(value)
            except (TypeError, KeyError):
                raise ValueError(f"Invalid {cls.__name__} name or value: {value}")


class BaseIntEnum(IntEnum):
    """
    Integer numeration base class for use in Buildarr configurations.

    Like `BaseEnum`, but as the enumeration values are guaranteed to be integer type,
    it natively supports sorting functions such as `sorted`.
    """

    @classmethod
    def from_name_str(cls, name_str: str) -> Self:
        """
        Get the enumeration object corresponding to the given name case-insensitively.

        Args:
            name_str (str): Name of the enumeration value (case insensitive).

        Raises:
            KeyError: When the enumeration name is invalid (does not exist).

        Returns:
            The enumeration object for the given name
        """
        name = name_str.lower().replace("-", "_")
        for obj in cls:
            if obj.name.lower() == name:
                return obj
        raise KeyError(repr(name))

    def to_name_str(self) -> str:
        """
        Return the name for this enumaration object.

        Returns:
            Enumeration name
        """
        return self.name.replace("_", "-")

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Self], None, None]:
        """
        Pass class validation functions to Pydantic.

        Yields:
            Validation class functions
        """
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        """
        Validate and coerce the given value to an enumeration object.

        Args:
            value (Any): Object to validate and coerce

        Raises:
            ValueError: If a enumeration object corresponding with the value cannot be found

        Returns:
            Enumeration object corresponding to the given value
        """
        try:
            return cls(value)
        except ValueError:
            try:
                return cls.from_name_str(value)
            except (TypeError, KeyError):
                raise ValueError(f"Invalid {cls.__name__} name or value: {value}")


class DayOfWeek(BaseIntEnum):
    """
    Sortable eumeration for the days in the week (Monday to Sunday).

    Values (in ascending order):

    * `monday` (Monday)
    * `tuesday` (Tuesday)
    * `wednesday` (Wednesday)
    * `thursday` (Thursday)
    * `friday` (Friday)
    * `saturday` (Saturday)
    * `sunday` (Sunday)
    """

    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6

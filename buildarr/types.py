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
from pathlib import Path
from typing import Any, Callable, Generator

from pydantic import AnyUrl, ConstrainedInt, ConstrainedStr, Field, SecretStr
from pydantic.fields import ModelField
from typing_extensions import Annotated, Self

from .state import state
from .util import get_absolute_path

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
                raise ValueError(f"Invalid {cls.__name__} name or value: {value}") from None


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
                raise ValueError(f"Invalid {cls.__name__} name or value: {value}") from None


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


class InstanceName(str):
    """
    A type for creating references to an instance in another plugin.

    When loading the instance-specific configurations, Buildarr will dereference
    defined instance references, and order the execution of updates so that
    instances used by another instance get updated first.

    This ensures that all instances are in the state expected by the user
    when the instance gets processed.

    When defining `InstanceName`, a Pydantic `Field` needs to be defined
    with the special `plugin` argument passed to tell Buildarr what plugin
    to search for the linked instance under.

    ```python
    from typing import TYPE_CHECKING, Optional
    from pydantic import Field
    from buildarr.config import ConfigBase, RssUrl

    if TYPE_CHECKING:
        from .secrets import ExampleSecrets
        class ExampleConfigBase(ConfigBase[ExampleSecrets]):
            ...
    else:
        class ExampleConfigBase(ConfigBase):
            ...

    class ExampleConfig(ExampleConfigBase):
        instance_name: Optional[InstanceName] = Field(None, plugin="example")
    ```

    The user will then be able to specify the name of the target instance in
    the Buildarr configuration.

    ```yaml
    example:
      instances:
        instance-1:
          ...
        instance-2:
          instance_name: "instance-1"
          ...
    ```
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[str, ModelField], str], None, None]:
        """
        Pass the defined validation functions to Pydantic.
        """
        yield cls.validate

    @classmethod
    def validate(cls, value: str, field: ModelField) -> Self:
        """
        Validate the type of the instance name reference,
        evaluate the reference and add the link to the dependency tree structure.

        _extended_summary_

        Args:
            value (str): Instance name reference.
            field (ModelField): Field metadata. Used to get the linked plugin name.

        Raises:
            ValueError: If the target plugin is not defined as field metadata

        Returns:
            Instance name object (string-compatible)
        """
        NonEmptyStr.validate(value)
        try:
            plugin_name: str = field.field_info.extra["plugin"]
            instance_name = value
            if plugin_name not in state.plugins:
                raise ValueError(f"Target plugin '{plugin_name}' not installed")
            if state.config:
                if instance_name not in getattr(state.config, plugin_name).instances:
                    raise ValueError(
                        f"Target instance '{instance_name}' "
                        f"not defined in plugin '{plugin_name}' configuration",
                    )
                if state._current_plugin and state._current_instance:
                    state._instance_dependencies[
                        (state._current_plugin, state._current_instance)
                    ].add(
                        (plugin_name, instance_name),
                    )
        except KeyError as err:
            if err.args[0] == "plugin":
                raise ValueError(
                    "Target plugin not defined in instance name metadata, "
                    "make sure the default value is set to `Field(None, plugin='<plugin-name>')`",
                ) from None
            else:
                raise
        return cls(value)


class LocalPath(type(Path()), Path):  # type: ignore[misc]
    """
    Model type for a local path.

    If the supplied path is relative, it is parsed as an absolute path
    relative to the configuration file it was defined in.

    For example, suppose a configuration file located at `/path/to/buildarr.yml`
    was created with the following attributes:

    ```yaml
    ---

    buildarr:
      secrets_file_path: "../secrets/buildarr.json"
    ```

    Even when executing Buildarr from a different folder e.g. `/opt/buildarr`,
    the `buildarr.secrets_file_path` attribute would be evaluated as
    `/path/secrets/buildarr.json`, *not* `/opt/secrets/buildarr.json`.
    """

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
        Validate the local path value, and return an absolute path.

        Args:
            value (Any): Object to validate and coerce

        Returns:
            Absolute local path
        """
        path = cls(value)
        if not path.is_absolute():
            return cls(get_absolute_path(state._current_dir / path))
        return path

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
Buildarr general purpose type hints, used in plugin models.
"""

from __future__ import annotations

from functools import total_ordering
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Type

from pydantic import (
    AfterValidator,
    AnyUrl,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PlainSerializer,
    SecretStr as PydanticSecretStr,
    StringConstraints,
    UrlConstraints,
)
from pydantic_core import core_schema
from typing_extensions import Annotated, Self

from .state import state
from .util import get_absolute_path

if TYPE_CHECKING:
    from enum import Enum

    from .config.models import ConfigPlugin

    # Trickery to make Mypy work properly with MultiValueEnum. Not actually used.
    class MultiValueEnum(Enum):
        values: Sequence[Any]

else:
    # This gets imported when actually running.
    from aenum import MultiValueEnum  # type: ignore[import-untyped]


SecretStr = Annotated[
    PydanticSecretStr,
    PlainSerializer(lambda v: v.get_secret_value(), return_type=str),
]
"""
A type for storing string values that contain sensitive information,
and must be obfuscated when output in logging.

This type is **not** the same as the `pydantic.SecretStr` type,
as this one has a custom serialiser defined on it to allow
Buildarr configuration objects to be serialised and dumped.

When defining secret string attributes in Buildarr,
**this `SecretStr` class must be used.**
"""


Password = Annotated[SecretStr, StringConstraints(min_length=1)]
"""
Constrained secret string type for password fields. Required to be non-empty.
"""


RssUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["rss"])]
"""
Constrained URL type for RSS URLs.

```python
from typing import TYPE_CHECKING
from buildarr.config import ConfigBase, RssUrl

if TYPE_CHECKING:
    from .secrets import ExampleSecrets

    class ExampleConfigBase(ConfigBase[ExampleSecrets]): ...
else:

    class ExampleConfigBase(ConfigBase): ...


class ExampleConfig(ExampleConfigBase):
    rss_url: RssUrl
```
"""


Port = Annotated[int, Field(ge=1, le=65535)]
"""
Constrained integer type for TCP/UDP port numbers.

Valid ports range from 1 to 65535 (a 16-bit integer).

```python
from typing import TYPE_CHECKING
from buildarr.config import ConfigBase, NonEmptyStr, Port

if TYPE_CHECKING:
    from .secrets import ExampleSecrets

    class ExampleConfigBase(ConfigBase[ExampleSecrets]): ...
else:

    class ExampleConfigBase(ConfigBase): ...


class ExampleConfig(ExampleConfigBase):
    host: NonEmptyStr
    port: Port
```
"""


NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""
Constrained string type for non-empty strings.

When validated in a Buildarr configuration, empty strings
or strings composed only of whitespace will fail validation.

Values are also stripped of whitespace at the start and the end
of the strings.

```python
from buildarr.config import ConfigBase, NonEmptyStr, Port


class ExampleConfig(ConfigBase):
    host: NonEmptyStr
    port: Port
```
"""


LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
"""
Constrained string type for lower-case strings.

When validated in a Buildarr configuration,
all upper-case characters in the value will be converted to lower-case.

```python
from buildarr.config import LowerCaseStr


class ExampleConfig(ConfigBase):
    lowercase_name: LowerCaseStr
```
"""


LowerCaseNonEmptyStr = Annotated[
    LowerCaseStr,
    StringConstraints(min_length=1, strip_whitespace=True),
]
"""
Constrained string type for non-empty lower-case strings.

This is a combination of `LowerCaseStr` and `NonEmptyStr`,
with the validations of both types applying to the value.

```python
from buildarr.config import LowerCaseNonEmptyStr


class ExampleConfig(ConfigBase):
    lowercase_name: LowerCaseNonEmptyStr
```
"""


UpperCaseStr = Annotated[str, StringConstraints(to_upper=True)]
"""
Constrained string type for upper-case strings.

When validated in a Buildarr configuration,
all lower-case characters in the value will be converted to upper-case.

```python
from buildarr.config import ConfigBase
from buildarr.types import UpperCaseStr


class ExampleConfig(ConfigBase):
    uppercase_name: UpperCaseStr
```
"""


UpperCaseNonEmptyStr = Annotated[
    UpperCaseStr,
    StringConstraints(min_length=1, strip_whitespace=True),
]


TrashID = Annotated[
    LowerCaseStr,
    StringConstraints(min_length=32, max_length=32, pattern="^[A-Fa-f0-9]+$"),
]
"""
Constrained string type for TRaSH-Guides resource IDs.

Accepts any valid TRaSH-Guides ID, and is case-insensitive,
converting to lower case internally.

```python
from typing import TYPE_CHECKING
from buildarr.config import ConfigBase, TrashID

if TYPE_CHECKING:
    from .secrets import ExampleSecrets

    class ExampleConfigBase(ConfigBase[ExampleSecrets]): ...
else:

    class ExampleConfigBase(ConfigBase): ...


class ExampleConfig(ExampleConfigBase):
    trash_id: TrashID
```
"""


class BaseEnum(MultiValueEnum):
    """
    Enumeration base class for use in Buildarr configurations.

    When configurating an enumeration-type attribute in the Buildarr configuration,
    the user will be able to specify either the name of the enumeration,
    or any of the possible values. Parsing of enumerations is case-insensitive.

    For example, given the following example:

    ```python
    from buildarr.config import ConfigBase
    from buildarr.types import BaseEnum


    class Animal(BaseEnum):
        value_1 = 0
        value_2 = 1


    class ExampleConfig(ConfigBase):
        animal: Animal
    ```

    The user would be able to configure it in the Buildarr configuration like so:

    ```yaml
    ---

    example:
      animal: value-1  # value-1, VALUE_1 or 0 can also be specified here.
    ```

    This class also supports specifying multiple values for an enumeration,
    by passing a `tuple` containing all the possible values.

    ```python
    from buildarr.types import BaseEnum

    class Animal(BaseEnum):
        value_1 = (0, "dog")
        value_2 = (1, "cat")
    ```

    When an enumeration is serialised for a remote instance,
    the first provided value will be used. In the above examples,
    the remote instance API will receive `0` and `1` as the values.

    When exporting the Buildarr configuration to a file, the first `str`-type value
    will be used when serialising multi-value enumerations.

    ```yaml
    ---

    example:
      animal: dog
    ```

    If the numeration is a single-value enumeration, or there are no
    `str`-type values in the multi-value enumeration, the enumeration name
    itself is used.

    ```yaml
    ---

    example:
      animal: value-1
    ```
    """

    @classmethod
    def from_name_str(cls, name_str: str) -> Self:
        """
        Get the enumeration object corresponding to the given name case-insensitively.

        Args:
            name_str (str): Name of the enumeration value, or its remote representation.

        Raises:
            KeyError: When the enumeration name is invalid (does not exist).

        Returns:
            The enumeration object for the given name
        """
        name = name_str.lower().replace("/", "_").replace("-", "_")
        for obj in cls:  # type: ignore[attr-defined]
            if obj.name.lower() == name:
                return obj
            for value in obj.values:
                if (
                    isinstance(value, str)
                    and value.lower().replace("/", "_").replace("-", "_") == name
                ):
                    return obj
        raise KeyError(repr(name))

    def to_name_str(self) -> str:
        """
        Return the name for this enumeration object.

        Returns:
            First `str`-type value in list of values (if available),
            otherwise the enumeration name.
        """
        if len(self.values) > 1:
            for value in self.values:
                if isinstance(value, str):
                    return value
        return self.name.replace("_", "-")

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            function=cls.validate,
            schema=core_schema.enum_schema(
                cls,
                list(cls.__members__.values()),
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda v: v.to_name_str(),
                    return_schema=core_schema.str_schema(),
                ),
            ),
        )

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


@total_ordering
class DayOfWeek(BaseEnum):
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

    def __eq__(self, other: Any) -> bool:
        """
        Reimplement the `a == b` operator for `DayOfWeek`, so integers
        of the same value also get evaluated as equal.

        Args:
            other (Any): Object to check is equal to this object.

        Returns:
            `True` if this object is equal to `other`, otherwise `False`
        """
        try:
            other_obj = DayOfWeek(other)
        except ValueError:
            raise NotImplementedError() from None
        return self.value == other_obj.value

    def __hash__(self) -> int:
        """
        Implement the hash method for `DayOfWeek`.

        Simply return the enumeration value, since it is an integer and always unique.

        Returns:
            `DayOfWeek` hash
        """
        return self.value

    def __lt__(self, other: Any) -> bool:
        """
        Implement the `a < b` operator for `DayOfWeek`.

        The `total_ordering` decorator will declare the rest.

        Args:
            other (Any): Object to check is greater than this object.

        Returns:
            `True` if this object is less than `other`, otherwise `False`
        """
        try:
            other_obj = DayOfWeek(other)
        except ValueError:
            raise NotImplementedError() from None
        return self.value < other_obj.value


def InstanceReference(plugin_name: str) -> AfterValidator:  # noqa: N802
    """
    A validator generator for creating references to an instance in another plugin.

    When loading the instance-specific configurations, Buildarr will dereference
    defined instance references, and order the execution of updates so that
    instances used by another instance get updated first.

    This ensures that all instances are in the state expected by the user
    when the instance gets processed.

    Instances references are defined by using `Annotated`, as shown below:

    ```python
    from typing import TYPE_CHECKING, Optional

    from buildarr.config import ConfigBase
    from buildarr.types import InstanceReference
    from pydantic import Field
    from typing_extensions import

    from .config import ExampleConfigBase

    class ExampleConfig(ExampleConfigBase):
        instance_name: Annotated[Optional[str], InstanceReference(plugin_name="example")] = None
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

    Args:
        plugin_name (str): Name of the plugin to create an instance reference for.

    Returns:
        AfterValidator: Validator annotation for the instance reference processing.
    """

    return AfterValidator(
        lambda instance_name: _instance_reference(
            plugin_name=plugin_name,
            instance_name=instance_name,
        ),
    )


def _instance_reference(plugin_name: str, instance_name: Optional[str]) -> Optional[str]:
    if not instance_name:
        return None

    if plugin_name not in state.plugins:
        raise ValueError(f"target plugin '{plugin_name}' not installed")

    if not state.config:
        return instance_name

    instances: Mapping[str, ConfigPlugin] = getattr(state.config, plugin_name).instances

    if instance_name == "default":
        if instances:
            raise ValueError(
                (
                    "unable to use default instance as the target instance, "
                    "instance-specific configurations are defined "
                    f"in plugin '{plugin_name}' configuration ("
                    f"available instances: {', '.join(repr(i) for i in instances.keys())}"
                    ")"
                ),
            )
    elif instance_name not in instances:
        raise ValueError(
            (
                f"target instance '{instance_name}' "
                f"not defined in plugin '{plugin_name}' configuration"
            ),
        )

    if state._current_plugin and state._current_instance:
        state._instance_dependencies[(state._current_plugin, state._current_instance)].add(
            (plugin_name, instance_name),
        )

    return instance_name


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
      # Removed in v0.7.0, but still useful as an example in developer docs.
      secrets_file_path: "../secrets/buildarr.json"
    ```

    Even when executing Buildarr from a different folder e.g. `/opt/buildarr`,
    the `buildarr.secrets_file_path` attribute would be evaluated as
    `/path/secrets/buildarr.json`, *not* `/opt/buildarr/buildarr.json`.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

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


model_config_base: ConfigDict = {
    # When aliases are defined, allow attributes to be referenced by their
    # internal name, as well as the alias.
    "populate_by_name": True,
    # Validate model default values.
    # This is necessary because the default attributes sometimes need to
    # be validated for correctness in non-default contexts.
    # (For example, a normally optional attribute becoming required due to
    # another attribute being enabled.)
    "validate_default": True,
    # Validate any values that have been modified in-place, to ensure the model
    # still fits the constraints.
    "validate_assignment": True,
    # Expose model attribute docstrings as field descriptions.
    "use_attribute_docstrings": True,
}
"""
Buildarr model configuration base class.

Sets some required configuration parameters for parsing and validation to work correctly.
"""

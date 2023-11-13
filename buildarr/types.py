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

from functools import total_ordering
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, Mapping, Sequence, Type

from pydantic import AnyUrl, ConstrainedInt, ConstrainedStr, SecretStr
from pydantic.fields import ModelField
from typing_extensions import Self

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


class Password(SecretStr):
    """
    Constrained secrets string type for password fields. Required to be non-empty.
    """

    min_length = 1


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

    Values are also stripped of whitespace at the start and the end
    of the strings.

    ```python
    from buildarr.config import ConfigBase, NonEmptyStr, Port

    class ExampleConfig(ConfigBase):
        host: NonEmptyStr
        port: Port
    ```
    """

    min_length = 1
    strip_whitespace = True


class LowerCaseStr(ConstrainedStr):
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

    to_lower = True


class LowerCaseNonEmptyStr(LowerCaseStr):
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

    min_length = 1
    strip_whitespace = True


class UpperCaseStr(ConstrainedStr):
    """
    Constrained string type for upper-case strings.

    When validated in a Buildarr configuration,
    all lower-case characters in the value will be converted to upper-case.

    ```python
    from buildarr.config import UpperCaseStr

    class ExampleConfig(ConfigBase):
        uppercase_name: UpperCaseStr
    ```
    """

    to_upper = True


class UpperCaseNonEmptyStr(UpperCaseStr):
    """
    Constrained string type for non-empty lower-case strings.

    This is a combination of `UpperCaseStr` and `NonEmptyStr`,
    with the validations of both types applying to the value.

    ```python
    from buildarr.config import UpperCaseNonEmptyStr

    class ExampleConfig(ConfigBase):
        uppercase_name: UpperCaseNonEmptyStr
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
        Return the name for this enumaration object.

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
                instances: Mapping[str, ConfigPlugin] = getattr(
                    state.config,
                    plugin_name,
                ).instances
                if instance_name == "default":
                    if instances:
                        raise ValueError(
                            "unable to use default instance as the target instance, "
                            "instance-specific configurations are defined "
                            f"in plugin '{plugin_name}' configuration ("
                            f"available instances: {', '.join(repr(i) for i in instances.keys())}"
                            ")",
                        )
                elif instance_name not in instances:
                    raise ValueError(
                        f"target instance '{instance_name}' "
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
      # Removed in v0.7.0, but still useful as an example in developer docs.
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


config_encoders: Dict[Type[Any], Callable[[Any], Any]] = {
    BaseEnum: lambda v: v.to_name_str(),
    PurePosixPath: str,
    PureWindowsPath: str,
    SecretStr: lambda v: v.get_secret_value(),
}
"""
The canonical data structure Buildarr uses to serialise custom Python types
to a type serialisable into JSON and YAML.

When using a custom type that Buildarr does not automatically support
in plugins, add the required type to this structure, as shown in this example:

```python
from buildarr.types import config_encoders

class CustomType:
    ...
    def __str__(self) -> str:
        ...

config_encoders[CustomType] = lambda v: str(v)
```
"""


class ModelConfigBase:
    """
    Buildarr model configuration base class.

    Sets some required configuration parameters for
    serialisation, parsing and validation to work correctly.
    """

    # Mapping between custom type and encoding function to pass to `json.dumps`.
    # When adding custom types to encode, **do not override this attribute**,
    # as it will have no effect.
    # Instead, add the custom type to `buildarr.types:config_encoders`.
    json_encoders = config_encoders

    # Required to avoid coersion with same-name but different-typed fields
    # in objects for which there are multiple types that can be defined.
    smart_union = True

    # When aliases are defined, allow attributes to be referenced by their
    # internal name, as well as the alias.
    allow_population_by_field_name = True

    # Validate all configuration attributes, even the default ones.
    # This is necessary because the default attributes sometimes need to
    # be validated for correctness in non-default contexts.
    # (For example, a normally optional attribute becoming required due to
    # another attribute being enabled.)
    validate_all = True

    # Validate any values that have been modified in-place, to ensure the model
    # still fits the constraints.
    validate_assignment = True

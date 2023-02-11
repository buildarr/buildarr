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
Buildarr configuration interface classes and functions.
"""


from __future__ import annotations

import json
import re

from datetime import time
from enum import Enum, IntEnum
from pathlib import Path, PurePosixPath
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    get_args as get_type_args,
    get_origin as get_type_origin,
)

import yaml

from pydantic import (
    AnyUrl,
    BaseModel,
    ConstrainedInt,
    ConstrainedStr,
    Field,
    HttpUrl,
    SecretStr,
    create_model,
    root_validator,
)
from pydantic.validators import _VALIDATORS
from typing_extensions import Annotated, Self

from ..logging import logger, plugin_logger
from ..state import plugins
from .util import merge_dicts

if TYPE_CHECKING:
    from ..secrets import SecretsPlugin


Password = Annotated[SecretStr, Field(min_length=1)]
"""
Constrained secrets string type for password fields. Required to be non-empty.
"""

RemoteMapEntry = Tuple[str, str, Mapping[str, Any]]
"""
Helper type hint for defining parameters for the `remote_map` argument
in some `ConfigBase` attribute handling functions.

It is used as a specification to define how local and remote equivalents
of an attribute should be encoded and decoded.

It is a 3-tuple composed of the following elements:

* `local_attr` (`str`) - the local attribute name
* `remote_attr` (`str`) - the remote attribute name
* `params` (`Mapping[str, Any]`) - option parameters that define how to convert
   between local and remote attributes (for more details, check the handling function)

```python
from typing import Any, Dict, List, Optional
from buildarr.config import ConfigBase, RemoteMapEntry

class ExampleConfig(ConfigBase):
    local_attr_1: bool
    local_attr_2: Optional[str] = None

    _remote_map: List[RemoteMapEntry] = [
        ("local_attr_1", "remoteAttr1", {}),
        (
            "local_attr_2",
            "remoteAttr2",
            {
                "is_field": True,
                "decoder": lambda v: v or None,
                "encoder": lambda v: v or "",
            },
        ),
    ]
```
"""


class RssUrl(AnyUrl):
    """
    Constrained URL type for RSS URLs.

    ```python
    from buildarr.config import ConfigBase, RssUrl

    class ExampleConfig(ConfigBase):
        rss_url: RssUrl
    ```
    """

    allowed_schemes = ["rss"]


class Port(ConstrainedInt):
    """
    Constrained integer type for TCP/UDP port numbers.

    Valid ports range from 1 to 65535 (a 16-bit integer).

    ```python
    from buildarr.config import ConfigBase, NonEmptyStr, Port

    class ExampleConfig(ConfigBase):
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
    from buildarr.config import ConfigBase, TrashID

    class ExampleConfig(ConfigBase):
        trash_id: TrashID
    ```
    """

    regex = re.compile("[A-Fa-f0-9]+")
    min_length = 32
    max_length = 32
    to_lower = True


class ConfigEnum(Enum):
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


class ConfigIntEnum(IntEnum):
    """
    Integer numeration base class for use in Buildarr configurations.

    Like `ConfigEnum`, but as the enumeration values are guaranteed to be integer type,
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


class UpdateDay(ConfigIntEnum):
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


class ConfigBase(BaseModel):
    """
    Base class for Buildarr configuration sections.

    Contains a number of helper methods and configuration options
    to make fetching from remote instances and updating them as boilerplate-free as possible.
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> Self:
        """
        Get the remote instance configuration for this section, and return the resulting object.

        This function should be overloaded by implementing classes with values that need
        to be fetched from a remote instance, as the base function simply implements
        traversing the configuration tree to call child section functions.

        Args:
            secrets (SecretsPlugin): Remote instance host and secrets information.

        Returns:
            Remote instance configuration object
        """
        fields: Dict[str, ConfigBase] = {}
        for field_name, field in cls.__fields__.items():
            if issubclass(field.type_, ConfigBase):
                fields[field_name] = field.type_.from_remote(secrets)
        return cls(**fields)

    @classmethod
    def get_local_attrs(
        cls,
        remote_map: Iterable[RemoteMapEntry],
        remote_attrs: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse remote instance attributes and return their local equivalents.

        Designed to be used in overloaded versions of `from_remote`.

        It takes in a list of `RemoteMapEntry` objects determining
        what values should be parsed, and how, along with a `dict`-like object
        storing the remote versions of the key-value pairs.

        It parses the inputs and returns a `dict` storing key-value pairs
        of the local equivalents, suitable for being passed as arguments
        to Buildarr configuration class constructors.

        ```python
        from typing import Any, Dict, List, Optional
        from typing_extensions import Self
        from buildarr.config import ConfigBase, RemoteMapEntry
        from buildarr.secrets import SecretsPlugin

        class ExampleConfig(ConfigBase):
            local_attr_1: bool
            local_attr_2: Optional[str] = None

            _remote_map: List[RemoteMapEntry] = [
                ("local_attr_1", "remoteAttr1", {}),
                (
                    "local_attr_2",
                    "remoteAttr2",
                    {
                        "is_field": True,
                        "decoder": lambda v: v or None,
                        "encoder": lambda v: v or "",
                    },
                ),
            ]

            @classmethod
            def _api_get(cls, secrets: SecretsPlugin) -> Dict[str, Any]:
                ...

            @classmethod
            def from_remote(cls, secrets: SecretsPlugin) -> Self:
                return cls(
                    **cls.get_local_attrs(
                        remote_map=cls._remote_map,
                        remote_attrs=cls._api_get(secrets),
                    ),
                )
        ```

        Supported `RemoteMapEntry` optional parameters:

        * `decoder` (`Callable[[Any], Any]`, default: (use internal function))
            * Callable function for parsing the remote value to its local equivalent
        * `root_decoder` (`Callable[[Mapping[str, Any]], Any]`, default: (undefined))
            * Similar to `decoder`, but `remote_attrs` is passed instead of just the value
                being parsed, to give access to the full remote configuration context
        * `optional` (`bool`, default: `False`)
            * If set to `True` and the remote attribute cannot be found,
                return the default value for the local attribute
            * If set to `False`, raise an error instead
        * `is_field` (`bool`, default: `False`)
            * Denotes whether the remote value is stored in an *Arr API-style field
                for remote value reading purposes
        * `field_value` (`Any`, default: (raise `ValueError`))
            * Default value for when the *Arr API-style field corresponding to the
            local attribute is found, but no value was supplied (e.g. password fields)

        Args:
            remote_map (Iterable[RemoteMapEntry]): Remote map entries for the fields to parse
            remote_attrs (Mapping[str, Any]): Remote attribute key-value `dict`-like structure

        Raises:
            ValueError: When an *Arr API-style remote field is found but no value is supplied
            ValueError: When the remote field is not found

        Returns:
            Local field and value dictionary
        """
        local_attrs: Dict[str, Any] = {}
        for attr_name, remote_attr_name, attr_metadata in remote_map:
            # If a root decoder was defined, call it to get the local value.
            # As the remote attributes are passed as-is to the root decoders,
            # no extra work is necessary.
            if "root_decoder" in attr_metadata:
                local_attrs[attr_name] = attr_metadata["root_decoder"](remote_attrs)
            # Search for the remote value using the other defined parameters,
            # and parse it using either the caller-supplied standard decoder,
            # or using the default decoder.
            else:
                decoder: Callable[[Any], Any] = attr_metadata.get(
                    "decoder",
                    lambda v: cls._decode_attr(attr_name, v),
                )
                # If the remote attribute is an *Arr API-style field,
                # parse the field structure for the remote value.
                if attr_metadata.get("is_field", False):
                    field_default_set = False
                    for remote_field in remote_attrs["fields"]:
                        if remote_field["name"] == remote_attr_name:
                            try:
                                remote_attr = remote_field["value"]
                            except KeyError:
                                # If the field was found but no value was supplied with it,
                                # check if a special "field default" was included in the
                                # remote map parameters.
                                # If so, set the local attribute to be that value and continue,
                                # otherwise raise an error.
                                if "field_default" in attr_metadata:
                                    local_attrs[attr_name] = attr_metadata["field_default"]
                                    field_default_set = True
                                else:
                                    raise ValueError(
                                        "'value' attribute not included "
                                        f"for remote field '{remote_attr_name}'"
                                        "and 'field_default' not defined in local attribute",
                                    )
                            break
                    else:
                        if attr_metadata.get("optional", False):
                            local_attrs[attr_name] = cls.__fields__[attr_name].default
                            continue
                        else:
                            raise ValueError(f"Remote field '{remote_attr_name}' not found")
                    # If the local attribute was set to the field default value,
                    # we're done with this attribute. Move onto the next one.
                    if field_default_set:
                        continue
                # If the remote attribute is a regular key, get the value directly.
                else:
                    try:
                        remote_attr = remote_attrs[remote_attr_name]
                    except KeyError:
                        if attr_metadata.get("optional", False):
                            local_attrs[attr_name] = cls.__fields__[attr_name].default
                            continue
                        else:
                            raise
                # If we got to this point, the remote value has been retrieved.
                # Decode to get the local value, and add it to the results.
                local_attrs[attr_name] = decoder(remote_attr)
        # Return a dictionary containing all parsed local attributes.
        return local_attrs

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        """
        Compare this configuration to a remote instance's, and update the remote to match.

        This function should be overloaded by implementing classes with values that need
        to be fetched from a remote instance, as the base function simply implements
        traversing the configuration tree to call child section functions.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            secrets (SecretsPlugin): Remote instance host and secrets information.
            remote (Self): Remote instance configuration for the current section.
            check_unmanaged (bool, optional): Set unmanaged fields to defaults (default `False`).

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        changed = False
        for field_name, field in self:
            if isinstance(field, ConfigBase) and field.update_remote(
                f"{tree}.{field_name}",
                secrets,
                getattr(remote, field_name),
                check_unmanaged=check_unmanaged,
            ):
                changed = True
        return changed

    def get_create_remote_attrs(
        self,
        tree: str,
        remote_map: Iterable[RemoteMapEntry],
        set_unmanaged: bool = True,
    ) -> Dict[str, Any]:
        """
        Parse configuration local attributes and return their remote equivalents
        for creating a resource on the remote instance.

        Designed to be used in overloaded versions of `update_remote`,
        where a resource is being created using `POST` requests.

        It takes in a list of `RemoteMapEntry` objects determining
        what values should be parsed. The configuration object's values
        are then parsed, returning a `dict` storing key-value pairs
        of the remote equivalents, suitable for being parsed into
        JSON objects to be sent in `POST` requests to the remote server.

        ```python
        from typing import Any, List, Mapping, Optional
        from buildarr.config import ConfigBase, RemoteMapEntry
        from buildarr.secrets import SecretsPlugin

        class ExampleObj(ConfigBase):
            obj_attr1: int
            obj_attr2: Optional[str] = None

            _remote_map: List[RemoteMapEntry] = [
                ("obj_attr_1", "objAttr1", {}),
                (
                    "obj_attr_2",
                    "objAttr2",
                    {
                        "is_field": True,
                        "decoder": lambda v: v or None,
                        "encoder": lambda v: v or "",
                    },
                ),
            ]

            @classmethod
            def _api_post(cls, secrets: SecretsPlugin, obj: Mapping[str, Any]) -> None:
                ...

            def _exists_on_remote(self, secrets: SecretsPlugin) -> bool:
                ...

            def _create_remote(self, secrets: SecretsPlugin) -> None:
                self._api_post(
                    secrets,
                    self.get_create_remote_attrs(  # <--- Used here
                        tree=tree,
                        remote_map=self._remote_map,
                    ),
                )

        class ExampleConfig(ConfigBase):
            local_objs: Dict[str, ExampleObj]

            def update_remote(
                self,
                tree: str,
                secrets: SecretsPlugin,
                remote: Self,
                check_unmanaged: bool = False,
            ) -> bool:
                for obj in self.local_objs:
                    if not obj.exists_on_remote(secrets):
                        obj._create_remote(secrets)
        ```

        Supported `RemoteMapEntry` optional parameters:

        * `encoder` (`Callable[[Any], Any]`, default: (use internal function))
            * Callable function for parsing the local value to its remote equivalent
        * `root_encoder` (`Callable[[Self], Any]`, default: (undefined))
            * Similar to `encoder` but `self` is passed instead of just the value
              being parsed, to give access to the full local configuration context
        * `formatter` (`Callable[[Any], str]`, default: (use internal function))
            * Function to convert the local value to a string, used in logging
        * `set_if` (`Callable[[Any], bool]`, default: (always set))
            * Optional function to enable/disable setting the remote field
              based on the local value
        * `is_field` (`bool`, default: `False`)
            * Denotes whether the remote value is stored in an *Arr API-style field
              for remote value writing purposes
        * `set_unmanaged` (`bool`, default: (function-supplied value))
            * Remote map entry-supplied override for the function-supplied
              `set_unmanaged` parameter

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            remote_map (Iterable[RemoteMapEntry]): Remote map entries for the fields to parse.
            set_unmanaged (bool, optional): Explicitly set unmanaged fields. Defaults to `True`.

        Returns:
            Remote instance field and value dictionary
        """
        remote_attrs: Dict[str, Any] = {}
        already_logged: Set[str] = set()
        for attr_name, remote_attr_name, attr_metadata in remote_map:
            # Determine the correct attribute formatter function used in logging.
            formatter: Callable[[Any], str] = lambda v: repr(
                attr_metadata.get("formatter", self._format_attr)(v),
            )
            # Determine whether or not the attribute should be set in
            # the remote attribute dictonary.
            if (
                attr_metadata.get("set_unmanaged", set_unmanaged)
                or attr_name in self.__fields_set__
            ):
                set_value = True
                value = getattr(self, attr_name)
                if attr_name not in already_logged:
                    plugin_logger.info(
                        "%s.%s: %s -> (created)",
                        tree,
                        attr_name,
                        formatter(value),
                    )
                    already_logged.add(attr_name)
            else:
                set_value = False
                if attr_name not in already_logged:
                    plugin_logger.info("%s.%s: (unmanaged)", tree, attr_name)
                    already_logged.add(attr_name)
            # If the attribute should be set, encode the value and add it
            # to the remote attribute structure in the correct format.
            if set_value and attr_metadata.get("set_if", lambda v: True)(value):
                encoded_value = (
                    attr_metadata["root_encoder"](self)
                    if "root_encoder" in attr_metadata
                    else attr_metadata.get("encoder", self._encode_attr)(value)
                )
                # If the remote attribute is supposed to be an *Arr API-style field,
                # add it to the field list. Otherwise, directly add it to the
                # remote attribute structure as a dictionary key.
                if "is_field" in attr_metadata:
                    if "fields" not in remote_attrs:
                        remote_attrs["fields"] = []
                    remote_attrs["fields"].append(
                        {"name": remote_attr_name, "value": encoded_value},
                    )
                else:
                    remote_attrs[remote_attr_name] = encoded_value
        # Return the completed remote attribute dictionary structure.
        return remote_attrs

    def get_update_remote_attrs(
        self,
        tree: str,
        remote: Self,
        remote_map: Iterable[RemoteMapEntry],
        check_unmanaged: bool = False,
        set_unchanged: bool = False,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Parse configuration local attributes and return their remote equivalents
        for updating an existing resource on the remote instance.

        Designed to be used in overloaded versions of `update_remote`,
        where a resource is being updated in-place using `PUT` requests.

        It takes in a list of `RemoteMapEntry` objects determining
        what values should be parsed. The configuration object's values
        are then parsed, returning a `dict` storing key-value pairs
        of the remote equivalents, suitable for being parsed into
        JSON objects to be sent in `PUT` requests to the remote server.

        The function returns a 2-tuple containing:

        * A flag that is `True` if the local and remote configuration are different
        * The updated remote instance attributes as a `dict`

        ```python
        from typing import Any, List, Mapping, Optional
        from buildarr.config import ConfigBase, RemoteMapEntry
        from buildarr.secrets import SecretsPlugin

        class ExampleConfig(ConfigBase):
            local_attr_1: bool
            local_attr_2: Optional[str] = None

            _remote_map: List[RemoteMapEntry] = [
                ("local_attr_1", "remoteAttr1", {}),
                (
                    "local_attr_2",
                    "remoteAttr2",
                    {
                        "is_field": True,
                        "decoder": lambda v: v or None,
                        "encoder": lambda v: v or "",
                    },
                ),
            ]

            @classmethod
            def _api_put(cls, secrets: SecretsPlugin, obj: Mapping[str, Any]) -> None:
                ...

            def update_remote(
                self,
                tree: str,
                secrets: SecretsPlugin,
                remote: Self,
                check_unmanaged: bool = False,
            ) -> bool:
                changed, remote_attrs = self.get_update_remote_attrs(
                    tree=tree,
                    remote=remote,
                    remote_map=self._remote_map,
                    check_unmanaged=check_unmanaged,
                    set_unchanged=True,
                )
                if changed:
                    self._api_put(secrets, remote_attrs)
                return changed
        ```

        Supported `RemoteMapEntry` optional parameters:

        * `encoder` (`Callable[[Any], Any]`, default: (use internal function))
            * Callable function for parsing the local value to its remote equivalent
        * `root_encoder` (`Callable[[Self], Any]`, default: (undefined))
            * Similar to `encoder`, but `self` is passed instead of just the value
              being parsed, to give access to the full local configuration context
        * `formatter` (`Callable[[Any], str]`, default: (use internal function))
            * Function to convert the local value to a string, used in logging
        * `set_if` (`Callable[[Any], bool]`, default: (always set))
            * Optional function to enable/disable setting the remote field
              based on the local value
        * `is_field` (`bool`, default: `False`)
            * Denotes whether the remote value is stored in an *Arr API-style field
              for remote value writing purposes
        * `set_unchanged` (`bool`, default: (function-supplied value))
            * Remote map entry-supplied override for the function-supplied
              `set_unchanged` parameter

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            remote (Self): Remote instance configuration object.
            remote_map (Iterable[RemoteMapEntry]): Remote map entries for the fields to parse.
            check_unmanaged (bool, optional): Check and set unmanaged fields. Defaults to `False`.
            set_unchanged (bool, optional): Include unchanged field values. Defaults to `False`.

        Returns:
            2-tuple with a "resource changed" flag, and the remote field and value dictionary
        """
        changed = False
        remote_attrs: Dict[str, Any] = {}
        already_logged: Set[str] = set()
        for attr_name, remote_attr_name, attr_metadata in remote_map:
            #
            set_value = False
            #
            formatter: Callable[[Any], str] = lambda v: repr(
                attr_metadata.get("formatter", self._format_attr)(v),
            )
            #
            remote_value = getattr(remote, attr_name)
            # Handle the case where the attribute is managed, either
            # by virtue of it being explicitly set in the Buildarr config,
            # or check_unmanaged is set to True.
            if check_unmanaged or attr_name in self.__fields_set__:
                local_value = getattr(self, attr_name)
                # If the local and remote attributes are set to the same
                # value, unless set_unchanged is set to True, do nothing.
                if local_value == remote_value:
                    if attr_name not in already_logged:
                        plugin_logger.debug(
                            "%s.%s: %s (up to date)",
                            tree,
                            attr_name,
                            formatter(remote_value),
                        )
                        already_logged.add(attr_name)
                    if attr_metadata.get("set_unchanged", set_unchanged):
                        set_value = True
                        value = local_value
                # If the local and remote attributes have different values,
                # update the remote value to reflect the changes.
                else:
                    if attr_name not in already_logged:
                        plugin_logger.info(
                            "%s.%s: %s -> %s",
                            tree,
                            attr_name,
                            formatter(remote_value),
                            formatter(local_value),
                        )
                        already_logged.add(attr_name)
                        changed = True
                    set_value = True
                    value = local_value
            # The attribute is unmanaged and unmanaged values should not be
            # set to the Buildarr default values.
            # If set_unchanged is True, forward the current remote attribute value
            # to the structure unchanged.
            # If set_unchanged is False, do nothing.
            else:
                if attr_name not in already_logged:
                    plugin_logger.debug(
                        "%s.%s: %s (unmanaged)",
                        tree,
                        attr_name,
                        formatter(remote_value),
                    )
                    already_logged.add(attr_name)
                if attr_metadata.get("set_unchanged", set_unchanged):
                    set_value = True
                    value = remote_value
            # If the current field should be set, encode the value and add it
            # to the remote attribute structure in the correct format.
            if set_value and attr_metadata.get("set_if", lambda v: True)(value):
                encoded_value = (
                    attr_metadata["root_encoder"](self)
                    if "root_encoder" in attr_metadata
                    else attr_metadata.get("encoder", self._encode_attr)(value)
                )
                # If the remote attribute is supposed to be an *Arr API-style field,
                # add it to the field list. Otherwise, directly add it to the
                # remote attribute structure as a dictionary key.
                if attr_metadata.get("is_field", False):
                    if "fields" not in remote_attrs:
                        remote_attrs["fields"] = []
                    remote_attrs["fields"].append(
                        {"name": remote_attr_name, "value": encoded_value},
                    )
                else:
                    remote_attrs[remote_attr_name] = encoded_value
        # Return the completed remote attribute dictionary structure.
        return (changed, remote_attrs)

    @classmethod
    def _format_attr(cls, value: Any) -> Any:
        """
        Default configuration value formatting function.

        Args:
            value (Any): Value to format

        Returns:
            The value to pass to the logging function
        """
        if isinstance(value, ConfigEnum):
            return value.to_name_str()
        elif isinstance(value, SecretStr):
            return str(value)
        elif isinstance(value, Path):
            return str(value)
        elif isinstance(value, list):
            return [cls._format_attr(v) for v in value]
        elif isinstance(value, set):
            return set(cls._format_attr(v) for v in value)
        return value

    @classmethod
    def _decode_attr(cls, attr_name: str, value: Any) -> Any:
        """
        Default remote-to-local instance attribute decoding function.

        Args:
            attr_name (str): Name of attribute to decode
            value (Any): Remote attribute value

        Returns:
            Local attribute value
        """
        return cls._decode_attr_(cls.__fields__[attr_name].type_, value)

    @classmethod
    def _decode_attr_(cls, attr_type: Type[Any], value: Any) -> Any:
        if get_type_origin(attr_type) is list:
            return [cls._decode_attr_(get_type_args(attr_type)[0], v) for v in value]
        elif get_type_origin(attr_type) is set:
            return set(cls._decode_attr_(get_type_args(attr_type)[0], v) for v in value)
        elif get_type_origin(attr_type) is Union:
            attr_union_types = get_type_args(attr_type)
            #
            if len(attr_union_types) == 2 and type(None) in attr_union_types and value is not None:
                return cls._decode_attr(
                    [t for t in attr_union_types if t is not type(None)][0],  # noqa: E721
                    value,
                )
        elif issubclass(attr_type, ConfigEnum):
            return attr_type(value)
        return value

    @classmethod
    def _encode_attr(cls, value: Any) -> Any:
        """
        Default local-to-remote instance attribute encoding function.

        Args:
            value (Any): Local attribute value

        Returns:
            Remote attribute value
        """
        if isinstance(value, ConfigEnum):
            return value.value
        elif isinstance(value, SecretStr):
            return value.get_secret_value()
        elif isinstance(value, (list, set)):
            return [cls._encode_attr(v) for v in value]
        return value

    def yaml(self, *args, **kwargs) -> str:
        """
        Generate a YAML representation of the model.

        Internally this uses the Pydantic JSON generation function, with all arguments
        forwarded to `BaseModel.json()`. The JSON output is then re-processed using PyYAML.

        Returns:
            YAML representation of the model
        """
        return yaml.safe_dump(json.loads(self.json(*args, **kwargs)))

    class Config:
        # Add default JSON encoders for custom, non-default and otherwise non-specified
        # classes so serialisation can work.
        json_encoders = {
            ConfigEnum: lambda v: v.to_name_str(),
            ConfigIntEnum: lambda v: v.to_name_str(),
            PurePosixPath: str,
            SecretStr: lambda v: v.get_secret_value(),
        }
        # Required to avoid coersion with same-name but different-typed fields
        # in objects for which there are multiple types that can be defined.
        smart_union = True


class ConfigPlugin(ConfigBase):
    """
    Buildarr plugin configuration object base class.

    The configuration plugin is a Pydantic model, so
    class attributes and type hints are used to specify
    configuration field names and how they should be parsed.

    Note that the `instances` attribute is not directly defined by `ConfigPlugin`,
    but it MUST be defined on the implementing class.

    ```python
    from typing import Literal
    from buildarr.config import ConfigPlugin, NonEmptyStr, Port

    class ExampleConfig(ConfigPlugin):
        # Required configuration overrides from `ConfigPlugin`
        hostname: NonEmptyStr = "example"
        port: Port = 1234
        protocol: Literal["http", "https"] = "http"

        # Custom configuration options go here
        local_value_1: bool = False
        local_value_2: str = "local"

        # Required `instances` definition
        instances: Dict[str, ExampleConfig] = {}
    ```

    The resulting configuration is defined in `buildarr.yml` like so:

    ```yaml
    ---

    buildarr:
      ...

    example:
      local_value_1: true
      local_value_2: "value"
      instances:
        example1:
          ...
        example2:
          ...
    ```
    """

    hostname: NonEmptyStr
    """
    Hostname of the instance to connect to.

    For instance-specific configurations, the instance name as defined in
    the `instances` attribute is used.

    Implementing configuration classes should override this with a default value.
    """

    port: Port
    """
    Port number of the instance to connect to.

    Implementing configuration classes should override this with a default value.
    """

    protocol: NonEmptyStr
    """
    Remote instance communication protocol.

    Implementing configuration classes should override this with a default value.
    """

    # `instances` is not defined here, but it MUST be defined on the implementing class.

    @property
    def host_url(self) -> str:
        """
        Fully qualified URL for the instance.
        """
        return f"{self.protocol}://{self.hostname}:{self.port}"

    @property
    def uses_trash_metadata(self) -> bool:
        """
        A flag determining whether or not this configuration uses TRaSH-Guides metadata.

        Configuration plugins should implement this property if TRaSH-Guides metadata is used.

        This property is checked by the `ManagerPlugin.uses_trash_metadata()` function.
        """
        return False

    def get_instance_config(self, instance_name: str) -> Self:
        """
        Combine explicitly defined instance-local and global configuration,
        and return a fully qualified instance-specific plugin configuration object.

        This function should not need to be overloaded by implementing classes in most cases.

        Args:
            instance_name (str): Name of the instance to get the configuration of.

        Returns:
            Fully qualified instance-specific configuration object
        """
        global_config = self.dict(exclude=set(["instances"]), exclude_unset=True)
        if instance_name == "default":
            return self.__class__(**global_config)
        return self.__class__(
            **merge_dicts(
                #
                global_config,
                #
                {"hostname": instance_name},
                #
                self.instances[instance_name].dict(  # type: ignore[attr-defined]
                    exclude=set(["instances"]),
                    exclude_unset=True,
                ),
            ),
        )

    def render_trash_metadata(self, trash_metadata_dir: Path) -> Self:
        """
        Read TRaSH-Guides metadata, and return a configuration object with all templates rendered.

        Configuration plugins should implement this function if TRaSH-Guides metadata is used.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.

        Returns:
            Rendered configuration object
        """
        return self

    @root_validator
    def _set_default_hostname(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the default value for `hostname` on child instance configuration objects.

        The `instances` value on the global (default instance) configuration is left alone.

        Args:
            values (Dict[str, Any]): Input values for all local fields

        Returns:
            Dict[str, Any]: Changed field structure
        """
        if "instances" in values:
            for instance_name, instance in cast(
                Dict[str, ConfigPlugin],
                values["instances"],
            ).items():
                if "hostname" not in instance.__fields_set__:
                    instance.hostname = instance_name  # type: ignore[assignment]
        else:
            plugin_logger.warning(
                "'instances' not found from %s in ConfigPlugin._set_default_hostname",
                cls.__name__,  # type: ignore[attr-defined]
            )
        return values


class BuildarrConfig(ConfigBase):
    """
    The `buildarr` configuration section is used to configure the behaviour of Buildarr itself.

    Some of the configuration options set here may be overridden on the command line.

    Note that the log level cannot be set within `buildarr.yml`,
    as logging starts before the configuration is loaded.
    The log level can be set using the `$BUILDARR_LOG_LEVEL` environment variable,
    or using the `--log-level` command line argument.

    ```yaml
    ---

    buildarr:
      watch_config: true
      update_days:
        - "monday"
        - "tuesday"
        - "wednesday"
        - "thursday"
        - "friday"
        - "saturday"
        - "sunday"
      update_times:
        - "03:00"
      secrets_file_path: "secrets.json"
    ```
    """

    watch_config: bool = False
    """
    When set to `true`, the Buildarr daemon will watch the loaded configuration files for changes,
    and reload them and update remote instances if they are changed.

    Sending `SIGHUP` to the Buildarr daemon process on supported operating systems
    will also perform this operation, whether `watch_config` is enabled or not.

    This configuration option can be overridden using the `--watch-config` command line argument.
    """

    update_days: Set[UpdateDay] = set(day for day in UpdateDay)
    """
    The days Buildarr daemon will run update operations on.

    By default, updates are scheduled to run every day.

    Days are specified as a list of case-insensitive strings, in English.
    The days do not need to be in order.

    ```yaml
    buildarr:
      update_days:
        - "monday"
        - "wednesday"
        - "friday"
    ```

    This configuration option can be overridden using the `--update-days` command line argument.
    """

    update_times: Set[time] = {time(hour=3)}
    """
    The times Buildarr daemon will run update operations on each scheduled day.

    By default, updates are scheduled to run at 3:00am local time.

    Times are specified in the `HH:MM` format, in 24-hour time.
    The times do not need to be in order.

    Days are specified as a list of case-insensitive strings, in English.
    The days do not need to be in order.

    ```yaml
    buildarr:
      update_times:
        - "06:00"
        - "12:00"
        - "18:00"
        - "00:00"
    ```

    This configuration option can be overridden using the `--update-times` command line argument.
    """

    # TODO: Make this relative to the configuration file, not local to the current directory.
    secrets_file_path: Path = Path("secrets.json")
    """
    Path to store the Buildarr instance secrets file.
    """

    trash_metadata_download_url: HttpUrl = (
        "https://github.com/TRaSH-/Guides/archive/refs/heads/master.zip"  # type: ignore[assignment]
    )
    """
    URL to download the latest TRaSH-Guides metadata from.
    """

    trash_metadata_dir_prefix: Path = Path("Guides-master")
    """
    Metadata directory name within the downloaded ZIP file.
    """


def load(use_plugins: Set[str], path: Union[str, Path]) -> Tuple[List[Path], ConfigBase]:
    """
    Load a configuration file using the given plugins.

    Args:
        use_plugins (Set[str]): Plugins to use. Default is to use all plugins.
        path (Union[str, Path]): Buildarr configuration file.

    Returns:
        2-tuple of the list of files loaded and the global configuration object
    """

    # Get the absolute path to the Buildarr configuration file.
    path = Path(path).absolute().resolve()

    logger.info("Loading configuration file '%s'", path)

    logger.debug("Building configuration model")
    Config = create_model(  # type: ignore[call-overload]
        "Config",
        __base__=ConfigBase,
        buildarr=BuildarrConfig(),
        **{
            plugin_name: plugin.config()
            for plugin_name, plugin in plugins.items()
            if not use_plugins or plugin_name in use_plugins
        },
    )
    logger.debug("Finished building configuration model")

    logger.debug("Loading configuration file tree")
    files, configs = _get_files_and_configs(path)
    logger.debug("Finished loading configuration file tree")

    logger.debug("Merging configuration objects in order of file predecence:")
    for file in files:
        logger.debug("  - %s", file)
    config = merge_dicts(*configs)
    logger.debug("Finished merging configuration objects")

    logger.info("Finished loading configuration file")
    return (files, Config(**config))


def _get_files_and_configs(path: Path) -> Tuple[List[Path], List[Dict[str, Any]]]:
    # Load a configuration file.
    # If other files are included using the `includes` list structure,
    # load them as well, and return a 2-tuple of
    # the lists of file paths and configuration dictionaries,
    # in the order they were loaded.

    files = [path]
    configs: List[Dict[str, Any]] = []

    # First, parse the original configuration file.
    # If None is returned by the YAML parser, it means the file is empty,
    # so treat it as an empty configuration.
    with open(path, "r") as f:
        config: Optional[Dict[str, Any]] = yaml.safe_load(f)
        if config is None:
            config = {}
        configs.append(config)

    # Check if the YAML object loaded is the correct type.
    if not isinstance(config, dict):
        raise ValueError(
            "Invalid configuration object type "
            f"(got '{type(config).__name__}', expected 'dict'): {config}",
        )

    # If other files were included using the `includes` list structure,
    # recursively load them and add them to the list of files and objects.
    # Make sure the `includes` structure is removed from the config objects.
    if "includes" in config:
        includes = config["includes"]
        del config["includes"]
        if not isinstance(includes, list):
            raise ValueError(
                "Invalid value type for 'includes' "
                f"(got '{type(includes).__name__}', expected 'list'): {includes}",
            )
        for include in includes:
            ip = Path(include)
            include_path = (ip if ip.is_absolute() else (path.parent / ip)).resolve()
            _files, _configs = _get_files_and_configs(include_path)
            files.extend(_files)
            configs.extend(_configs)

    return (files, configs)


def _validate_pure_posix_path(v: Any) -> PurePosixPath:
    """
    PurePosixPath default object validator for Pydantic.

    Args:
        v (Any): Value to validate

    Returns:
        PurePosixPath object
    """

    return PurePosixPath(v)


# Add the PurePosixPath validator to the list of Pyadantic validators.
_VALIDATORS.append((PurePosixPath, [_validate_pure_posix_path]))

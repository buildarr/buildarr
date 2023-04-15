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
Buildarr configuration base class.
"""


from __future__ import annotations

import json

from logging import getLogger
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args as get_type_args,
    get_origin as get_type_origin,
)
from uuid import UUID

import yaml

from pydantic import AnyUrl, BaseModel, SecretStr
from pydantic.validators import _VALIDATORS
from typing_extensions import Self

from ..plugins import Secrets
from ..types import BaseEnum, ModelConfigBase
from .types import RemoteMapEntry

logger = getLogger(__name__)

OPTIONAL_TYPE_UNION_SIZE = 2


class ConfigBase(BaseModel, Generic[Secrets]):
    """
    Base class for Buildarr configuration sections.

    Contains a number of helper methods and configuration options
    to make fetching from remote instances and updating them as boilerplate-free as possible.
    """

    @classmethod
    def from_remote(cls, secrets: Secrets) -> Self:
        """
        Get the remote instance configuration for this section, and return the resulting object.

        This function should be overloaded by implementing classes with values that need
        to be fetched from a remote instance, as the base function simply implements
        traversing the configuration tree to call child section functions.

        Args:
            secrets (Secrets): Remote instance host and secrets information.

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
        from __future__ import annotations

        from typing import TYPE_CHECKING, Any, Dict, List, Optional
        from typing_extensions import Self
        from buildarr.config import ConfigBase, RemoteMapEntry

        if TYPE_CHECKING:
            from .secrets import ExampleSecrets
            class ExampleConfigBase(ConfigBase[ExampleSecrets]):
                ...
        else:
            class ExampleConfigBase(ConfigBase):
                ...

        class ExampleConfig(ExampleConfigBase):
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
            def _api_get(cls, secrets: ExampleSecrets) -> Dict[str, Any]:
                ...

            @classmethod
            def from_remote(cls, secrets: ExampleSecrets) -> Self:
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
                                        f"for remote field '{remote_attr_name}' "
                                        "and 'field_default' not defined in local attribute",
                                    ) from None
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
        secrets: Secrets,
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
            secrets (Secrets): Remote instance host and secrets information.
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
        from typing import TYPE_CHECKING, Any, List, Mapping, Optional
        from buildarr.config import ConfigBase, RemoteMapEntry
        from buildarr.secrets import Secrets

        if TYPE_CHECKING:
            from .secrets import ExampleSecrets
            class ExampleConfigBase(ConfigBase[ExampleSecrets]):
                ...
        else:
            class ExampleConfigBase(ConfigBase):
                ...

        class ExampleObj(ExampleConfigBase):
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
            def _api_post(cls, secrets: ExampleSecrets, obj: Mapping[str, Any]) -> None:
                ...

            def _exists_on_remote(self, secrets: ExampleSecrets) -> bool:
                ...

            def _create_remote(self, secrets: ExampleSecrets) -> None:
                self._api_post(
                    secrets,
                    self.get_create_remote_attrs(  # <--- Used here
                        tree=tree,
                        remote_map=self._remote_map,
                    ),
                )

        class ExampleConfig(ExampleConfigBase):
            local_objs: Dict[str, ExampleObj]

            def update_remote(
                self,
                tree: str,
                secrets: ExampleSecrets,
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
            def formatter(v: Any) -> str:
                nonlocal attr_metadata
                return repr(attr_metadata.get("formatter", self._format_attr)(v))

            # Determine whether or not the attribute should be set in
            # the remote attribute dictonary.
            if (
                attr_metadata.get("set_unmanaged", set_unmanaged)
                or attr_name in self.__fields_set__
            ):
                set_value = True
                value = getattr(self, attr_name)
                if attr_name not in already_logged:
                    logger.info("%s.%s: %s -> (created)", tree, attr_name, formatter(value))
                    already_logged.add(attr_name)
            else:
                set_value = False
                if attr_name not in already_logged:
                    logger.info("%s.%s: (unmanaged)", tree, attr_name)
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
        from __future__ import annotations

        from typing import TYPE_CHECKING, Any, List, Mapping, Optional
        from buildarr.config import ConfigBase, RemoteMapEntry
        from buildarr.secrets import Secrets

        if TYPE_CHECKING:
            from .secrets import ExampleSecrets
            class ExampleConfigBase(ConfigBase[ExampleSecrets]):
                ...
        else:
            class ExampleConfigBase(ConfigBase):
                ...

        class ExampleConfig(ExampleConfigBase):
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
            def _api_put(cls, secrets: Secrets, obj: Mapping[str, Any]) -> None:
                ...

            def update_remote(
                self,
                tree: str,
                secrets: Secrets,
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

        * `equals` (`Callable[[Any, Any], bool], default: (use `a == b`))
            * Callable function for comparing the local and remote values,
              and return if they are equal or not, with `True` being returned
              if they are equal, and `False` if not
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
        * `check_unmanaged` (`bool`, default: (function-supplied value))
            * Remote map entry-supplied override for the function-supplied
              `check_unmanaged` parameter
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
            def equals(a: Any, b: Any) -> bool:
                return a == b

            def formatter(v: Any) -> str:
                return repr(attr_metadata.get("formatter", self._format_attr)(v))

            #
            remote_value = getattr(remote, attr_name)
            # Handle the case where the attribute is managed, either
            # by virtue of it being explicitly set in the Buildarr config,
            # or check_unmanaged is set to True.
            if (
                attr_metadata.get("check_unmanaged", check_unmanaged)
                or attr_name in self.__fields_set__
            ):
                local_value = getattr(self, attr_name)
                # If the local and remote attributes are set to the same
                # value, unless set_unchanged is set to True, do nothing.
                if attr_metadata.get("equals", equals)(local_value, remote_value):
                    if attr_name not in already_logged:
                        logger.debug(
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
                        logger.info(
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
                    logger.debug("%s.%s: %s (unmanaged)", tree, attr_name, formatter(remote_value))
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

    def delete_remote(
        self,
        tree: str,
        secrets: Secrets,
        remote: Self,
    ) -> bool:
        """
        Compare the local configuration to a remote instance, and delete any resources
        that are unmanaged or unused on the remote, and allowed to be deleted.

        This function should be overloaded by implementing classes with resources that
        may need to be deleted from a remote instance if it is unmanaged by Buildarr
        or simply unused.

        The base function simply implements traversing the configuration tree
        to call child section functions.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            secrets (Secrets): Remote instance host and secrets information.
            remote (Self): Remote instance configuration for the current section.

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        changed = False
        for field_name, field in self:
            if isinstance(field, ConfigBase) and field.delete_remote(
                f"{tree}.{field_name}",
                secrets,
                getattr(remote, field_name),
            ):
                changed = True
        return changed

    @classmethod
    def _format_attr(cls, value: Any) -> Any:
        """
        Default configuration value formatting function.

        Args:
            value (Any): Value to format

        Returns:
            The value to pass to the logging function
        """
        if isinstance(value, BaseEnum):
            return value.to_name_str()
        elif isinstance(value, AnyUrl):
            return str(value)
        elif isinstance(value, SecretStr):
            return str(value)
        elif isinstance(value, Path):
            return str(value)
        elif isinstance(value, UUID):
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
        return cls._decode_attr_(cls.__fields__[attr_name].outer_type_, value)

    @classmethod
    def _decode_attr_(cls, attr_type: Type[Any], value: Any) -> Any:
        type_tree: List[Type[Any]] = [attr_type]
        while get_type_origin(type_tree[-1]) is not None:
            origin_type = get_type_origin(type_tree[-1])
            if origin_type is not None:
                type_tree.append(origin_type)
        if type_tree[-1] is list:
            return [cls._decode_attr_(get_type_args(type_tree[-2])[0], v) for v in value]
        elif type_tree[-1] is set:
            return set(cls._decode_attr_(get_type_args(type_tree[-2])[0], v) for v in value)
        elif type_tree[-1] is Union:
            attr_union_types = get_type_args(type_tree[-2])
            #
            if (
                len(attr_union_types) == OPTIONAL_TYPE_UNION_SIZE
                and type(None) in attr_union_types
                and value is not None
            ):
                return cls._decode_attr(
                    [t for t in attr_union_types if t is not type(None)][0],
                    value,
                )
        elif issubclass(type_tree[-1], BaseEnum):
            return type_tree[-1](value)
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
        if isinstance(value, BaseEnum):
            return value.value
        elif isinstance(value, AnyUrl):
            return str(value)
        elif isinstance(value, SecretStr):
            return value.get_secret_value()
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, (list, set)):
            return [cls._encode_attr(v) for v in value]
        return value

    def yaml(
        self,
        *args,
        sort_keys: bool = False,
        yaml_kwargs: Optional[Mapping[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Generate a YAML representation of the model.

        Internally this uses the Pydantic JSON generation function, with all arguments
        forwarded to `BaseModel.json()`. The JSON output is then re-processed using PyYAML.

        Args:
            sort_keys (bool, optional): Sort keys in the output YAML file. Defaults to `False`.
            yaml_kwargs (Optional[Mapping[str, Any]], optional): YAML encoder keyword args.

        Returns:
            YAML representation of the model
        """
        return yaml.safe_dump(  # type: ignore[call-overload]
            json.loads(self.json(*args, **kwargs)),
            **{**(yaml_kwargs or {}), "sort_keys": sort_keys},
        )

    class Config(ModelConfigBase):
        """
        Buildarr configuration model class settings.

        Sets some required parameters for serialisation,
        parsing and validation to work correctly.

        To set additional parameters in your implementing class, subclass this class:

        ```python
        from __future__ import annotations

        from typing import TYPE_CHECKING
        from buildarr.config import ConfigBase

        if TYPE_CHECKING:
            from .secrets import ExampleSecrets
            class _ExampleConfig(ConfigBase[ExampleSecrets]):
                ...
        else:
            class _ExampleConfig(ConfigBase):
                ...

        class ExampleConfig(_ExampleConfig):
            ...

            class Config(_ExampleConfig.Config):
                ...  # Add model configuration attributes here.
        ```
        """

        pass


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

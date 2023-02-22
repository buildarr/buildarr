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
Buildarr plugin configuration object models.
"""


from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type, cast

from pydantic import root_validator
from typing_extensions import Self

from ..plugins import Secrets
from ..types import NonEmptyStr, Port
from ..util import merge_dicts
from .base import ConfigBase
from .buildarr import BuildarrConfig


class ConfigPlugin(ConfigBase[Secrets]):
    """
    Buildarr plugin configuration object base class.

    The configuration plugin is a Pydantic model, so
    class attributes and type hints are used to specify
    configuration field names and how they should be parsed.

    Note that the `instances` attribute is not directly defined by `ConfigPlugin`,
    but it MUST be defined on the implementing class.

    ```python
    from __future__ import annotations

    from typing import TYPE_CHECKING, Literal
    from buildarr.config import ConfigPlugin, NonEmptyStr, Port

    if TYPE_CHECKING:
        from .secrets import ExampleSecrets
        class _ExampleInstanceConfig(ConfigPlugin[ExampleSecrets]):
            ...
    else:
        class _ExampleInstanceConfig(ConfigPlugin):
            ...

    class ExampleInstanceConfig(_ExampleInstanceConfig):
        # Required configuration overrides from `ConfigPlugin`
        hostname: NonEmptyStr = "example"
        port: Port = 1234
        protocol: Literal["http", "https"] = "http"

        # Custom configuration options go here
        local_value_1: bool = False
        local_value_2: str = "local"

    class ExampleConfig(ExampleInstanceConfig):
        # Inherit all configuration attributes from the instance-specific config.
        # This is the class to specify in the plugin's `Plugin` interface definition.

        # Required `instances` definition
        instances: Dict[str, ExampleInstanceConfig] = {}
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

    @property
    def has_instance_configs(self) -> bool:
        """
        Whether or not this plugin has instance-specific configurations defined.

        This property should not need to be overloaded in most cases.
        """
        return bool(
            "instances" in self.__fields_set__ and self.instances,  # type: ignore[attr-defined]
        )

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
        instance_config_class: Type[Self] = self.__fields__["instances"].type_
        if instance_name == "default":
            return instance_config_class(**self.dict(exclude={"instances"}, exclude_unset=True))
        return instance_config_class(
            **merge_dicts(
                # Merge attribute values in order of priority (lowest to highest).
                #
                # Lowest priority are global configuration attribute defaults,
                # which are defined in the class attributes.
                #
                # Next are instance-specific configuration attribute defaults.
                {"hostname": instance_name},
                # Explicitly defined global configuration attributes.
                self.dict(exclude=set(["instances"]), exclude_unset=True),
                # Explicitly defined instance-specific attributes.
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
        Set the default value for `hostname` on instance-specific configurations.

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
        return values


class ConfigPluginType(ConfigPlugin):
    """
    Basic type hint containing the attributes and functions Buildarr
    (and plugins referring to other plugins) should use to interface
    with a global plugin configuration.
    """

    instances: Dict[str, ConfigPlugin]


class ConfigType(ConfigBase):
    """
    Type hint for interacting with a dynamically generated Buildarr configuration model.
    """

    buildarr: BuildarrConfig
    """
    Buildarr configuration settings.
    """

    def __getattr__(self, name: str) -> ConfigPluginType:
        """
        Dynamically-loaded plugin configuration.
        """
        raise NotImplementedError()

    def __setattr__(self, __name: str, __value: ConfigPluginType) -> None:
        """
        Dynamically-loaded plugin configuration.
        """
        raise NotImplementedError()

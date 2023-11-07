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
Buildarr configuration loading function.
"""


from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Type,
    Union,
    cast,
    get_args as get_type_args,
    get_origin as get_type_origin,
)

import yaml

from pydantic import create_model

from ..state import state
from ..types import LocalPath
from ..util import get_absolute_path, merge_dicts
from .base import ConfigBase
from .buildarr import BuildarrConfig
from .models import ConfigType

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Set, Tuple

    from .models import ConfigPlugin, ConfigPluginType

logger = getLogger(__name__)

OPTIONAL_TYPE_UNION_SIZE = 2


def load_config(path: Path, use_plugins: Optional[Set[str]] = None) -> None:
    """
    Load a configuration file using the given plugins.

    Args:
        use_plugins (Optional[Set[str]]): Plugins to use. Default is to use all plugins.
        path (Union[str, PathLike]): Buildarr configuration file.

    Returns:
        2-tuple of the list of files loaded and the global configuration object
    """

    logger.debug("Building configuration model")
    model = cast(
        Type[ConfigType],
        create_model(  # type: ignore[call-overload]
            "Config",
            __base__=ConfigBase,
            buildarr=BuildarrConfig(),
            **{
                plugin_name: plugin.config()
                for plugin_name, plugin in state.plugins.items()
                if not use_plugins or plugin_name in use_plugins
            },
        ),
    )
    logger.debug("Finished building configuration model")

    logger.debug("Loading configuration file tree")
    files, configs = _get_files_and_configs(model, path)
    logger.debug("Finished loading configuration file tree")

    logger.debug("Merging configuration objects in order of file predecence:")
    for file in files:
        logger.debug("  - %s", file)
    config = merge_dicts(*configs)
    logger.debug("Finished merging configuration objects")

    logger.debug("Parsing and validating configuration")
    with state._with_current_dir(path.parent):
        state.config = model(**config)
    logger.debug("Finished parsing and validating configuration")

    state.config_files = files


def _get_files_and_configs(
    model: Type[ConfigType],
    path: Path,
) -> Tuple[List[Path], List[Dict[str, ConfigPlugin]]]:
    # Load a configuration file.
    # If other files are included using the `includes` list structure,
    # load them as well, and return a 2-tuple of
    # the lists of file paths and configuration dictionaries,
    # in the order they were loaded.

    files = [path]
    configs: List[Dict[str, Any]] = []

    # First, parse and validate the current configuration file.
    #
    # An initial validation pass is done before any merging is done,
    # so any relative `LocalPath` type attributes are evaluated into
    # absolute paths relative to the actual folder the configuration file is in.
    #
    # After creating the configuration object, turn it back into a dictionary
    # so it can be merged with other loaded configuration files.
    #
    # If None is returned by the YAML parser when parsing the file,
    # it means the file is empty, so treat it as an empty configuration.
    with path.open(mode="r") as f:
        config: Optional[Dict[str, Any]] = yaml.safe_load(f)
        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise ValueError(
                f"Error while loading configuration file '{path}': "
                "Invalid configuration object type "
                f"(got '{type(config).__name__}', expected 'dict'): {config}",
            )
        configs.append(
            _expand_relative_paths(
                config_dir=path.parent,
                value_type=model,
                value={k: v for k, v in config.items() if k != "includes"},
            ),
        )

    from pprint import pprint

    pprint(configs)

    # If other files were included using the `includes` list structure,
    # recursively load them and add them to the list of files and objects.
    # Make sure the `includes` structure is removed from the config objects.
    if "includes" in config:
        includes = config["includes"]
        if not isinstance(includes, list):
            raise ValueError(
                f"Error while loading configuration file '{path}': "
                "Invalid value type for 'includes' "
                f"(got '{type(includes).__name__}', expected 'list'): {includes}",
            )
        for include in includes:
            ip = Path(include)
            if ip.is_absolute():
                include_path = ip
            else:
                include_path = get_absolute_path(path.parent / ip)
                logger.debug("Expanding relative local path '%s' into '%s'", ip, include_path)
            _files, _configs = _get_files_and_configs(model, include_path)
            files.extend(_files)
            configs.extend(_configs)

    return (files, configs)


def _expand_relative_paths(
    config_dir: Path,
    value_type: Type[Any],
    value: Any,
) -> Any:
    # Recursively expand any `LocalPath` type field values in the configuration dictionary
    # that are relative paths, and return the modified configuration dictionary.
    type_tree: List[Type[Any]] = [value_type]
    while get_type_origin(type_tree[-1]) is not None:
        origin_type = get_type_origin(type_tree[-1])
        if origin_type is not None:
            type_tree.append(origin_type)
    if type_tree[-1] is LocalPath:
        local_path = Path(value)
        if local_path.is_absolute():
            return value
        else:
            absolute_path = get_absolute_path(config_dir / local_path)
            logger.debug("Expanding relative local path '%s' into '%s'", local_path, absolute_path)
            return str(absolute_path)
    elif type_tree[-1] is Union:
        attr_union_types = get_type_args(type_tree[-2])
        if (
            len(attr_union_types) == OPTIONAL_TYPE_UNION_SIZE
            and type(None) in attr_union_types
            and value is not None
        ):
            return _expand_relative_paths(
                config_dir=config_dir,
                value_type=next(t for t in attr_union_types if t is not type(None)),
                value=value,
            )
    if type_tree[-1] in (list, set):
        element_type = get_type_args(type_tree[-2])[0]
        return [
            _expand_relative_paths(
                config_dir=config_dir,
                value_type=element_type,
                value=v,
            )
            for v in value
        ]
    if type_tree[-1] is dict:
        dict_key_type, dict_value_type = get_type_args(type_tree[-2])
        return {
            _expand_relative_paths(
                config_dir=config_dir,
                value_type=dict_key_type,
                value=dict_key,
            ): _expand_relative_paths(
                config_dir=config_dir,
                value_type=dict_value_type,
                value=dict_value,
            )
            for dict_key, dict_value in value.items()
        }
    try:
        is_subclass = issubclass(type_tree[-1], ConfigBase)
    except TypeError:
        is_subclass = False
    if is_subclass:
        return {
            key: _expand_relative_paths(
                config_dir=config_dir,
                value_type=field.outer_type_,
                value=value[key],
            )
            for key, field in type_tree[-1].__fields__.items()
            if key in value
        }
    return value


def load_instance_configs(use_plugins: Optional[Set[str]] = None) -> None:
    """
    Parse fully-qualified configuration for each instance under each selected plugin.

    This will also cause the `state._instance_dependencies` dependency tree structure
    to be populated through validation of any `InstanceName` attributes present
    in each instance-specific configuration.

    Args:
        use_plugins (Optional[Set[str]]): Plugins to use. Default is to use all plugins.
    """

    configs: Dict[str, Dict[str, ConfigPlugin]] = {}
    active_plugins: Set[str] = set()

    for plugin_name in state.plugins.keys():
        if use_plugins and plugin_name not in use_plugins:
            continue
        if plugin_name not in state.config.__fields_set__:
            continue
        plugin_manager = state.managers[plugin_name]
        plugin_config: ConfigPluginType = getattr(state.config, plugin_name)
        active_plugins.add(plugin_name)
        configs[plugin_name] = {}
        for instance_name in (
            plugin_config.instances.keys() if plugin_config.instances else ["default"]
        ):
            # Load the instance-specific configuration under aninstance-specific context,
            # so that when the configuration gets evaluated by the parser,
            # `InstanceName` references are properly validated and dependencies get added
            # to `state._instance_dependencies`.
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                instance_config = plugin_manager.get_instance_config(
                    plugin_config,
                    instance_name,
                )
                configs[plugin_name][instance_name] = instance_config

    # Update global application state with the fully qualified instance configurations.
    state.instance_configs = configs
    state.active_plugins = frozenset(active_plugins)

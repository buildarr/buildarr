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

from pathlib import Path
from typing import TYPE_CHECKING, Type, cast

import yaml

from pydantic import create_model

from ..logging import logger
from ..state import state
from ..util import get_absolute_path, merge_dicts
from .base import ConfigBase
from .buildarr import BuildarrConfig
from .models import ConfigType

if TYPE_CHECKING:
    from os import PathLike
    from typing import Any, Dict, List, Optional, Set, Tuple, Union

    from .models import ConfigPlugin


def load(path: Union[str, PathLike], use_plugins: Optional[Set[str]] = None) -> None:
    """
    Load a configuration file using the given plugins.

    Args:
        use_plugins (Set[str]): Plugins to use. Default is to use all plugins.
        path (Union[str, PathLike]): Buildarr configuration file.

    Returns:
        2-tuple of the list of files loaded and the global configuration object
    """

    path = get_absolute_path(path)

    logger.info("Loading configuration file '%s'", path)

    logger.debug("Building configuration model")
    Config = cast(
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
    files, configs = _get_files_and_configs(path)
    logger.debug("Finished loading configuration file tree")

    logger.debug("Merging configuration objects in order of file predecence:")
    for file in files:
        logger.debug("  - %s", file)
    config = merge_dicts(*configs)
    logger.debug("Finished merging configuration objects")

    logger.info("Finished loading configuration file")
    state.config_files = files
    state.config = Config(**config)


def _get_files_and_configs(path: Path) -> Tuple[List[Path], List[Dict[str, ConfigPlugin]]]:
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
    with path.open(mode="r") as f:
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

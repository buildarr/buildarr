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
Buildarr TRaSH-Guides metadata functions.
"""


from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from pathlib import Path
from shutil import move
from typing import TYPE_CHECKING
from urllib.request import urlretrieve
from zipfile import ZipFile

from .state import state
from .util import create_temp_dir

if TYPE_CHECKING:
    from typing import DefaultDict, Dict

    from .config import ConfigPlugin


logger = getLogger(__name__)


def trash_metadata_used() -> bool:
    """
    Read configuration for all loaded instances in the global state, and determine
    whether or not any of them use TRaSH-Guides metadata.

    Returns:
        `True` if TRaSH-Guides metadata is used by any instance configuration, otherwise `False`
    """

    for plugin_name in state.active_plugins:
        for instance_name, instance_config in state.instance_configs[plugin_name].items():
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                if state.managers[plugin_name].uses_trash_metadata(instance_config):
                    return True

    return False


def fetch_trash_metadata(trash_metadata_dir: Path) -> None:
    """
    Download the TRaSH-Guides metadata from the URL specified in the Buildarr config
    to the given local directory.

    Args:
        metadata_dir (Path): The local folder to extract the metadata to.
    """

    logger.debug("Creating TRaSH metadata download temporary directory")
    with create_temp_dir() as temp_dir:
        logger.debug("Finished creating TRaSH metadata download temporary directory")

        trash_metadata_filename = temp_dir / "trash-metadata.zip"

        logger.debug("Downloading TRaSH metadata")
        urlretrieve(state.config.buildarr.trash_metadata_download_url, trash_metadata_filename)
        logger.debug("Finished downloading TRaSH metadata")

        logger.debug("Extracting TRaSH metadata")
        with ZipFile(trash_metadata_filename) as zip_file:
            zip_file.extractall(path=temp_dir / "trash-metadata")
        logger.debug("Finished extracting TRaSH metadata")

        logger.debug("Moving TRaSH metadata files to target directory")
        for subfile in (
            temp_dir / "trash-metadata" / state.config.buildarr.trash_metadata_dir_prefix
        ).iterdir():
            move(str(subfile), trash_metadata_dir)
        logger.debug("Finished moving TRaSH metadata files to target directory")

        # Temporary directory will be deleted when the with block is exited.


def render_trash_metadata(trash_metadata_dir: Path) -> None:
    """
    Render TRaSH-Guides metadata on any instance configurations where used,
    and update the global state.

    Plugins will parse the TRaSH-Guides metadata files in the given directory
    and return new configuration objects with attributes populated from the metadata.

    Instances that do not use TRaSH-Guides metadata will be left unchanged.

    Args:
        trash_metadata_dir (Path): Local folder containing TRaSH-Guides metadata files.
    """

    instance_configs: DefaultDict[str, Dict[str, ConfigPlugin]] = defaultdict(dict)

    for plugin_name, instance_name in state._execution_order:
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            if manager.uses_trash_metadata(instance_config):
                logger.debug("Rendering TRaSH-Guides metadata")
                instance_configs[plugin_name][instance_name] = manager.render_trash_metadata(
                    instance_config,
                    trash_metadata_dir,
                )
                logger.debug("Finished rendering TRaSH-Guides metadata")
            else:
                logger.debug("Skipping rendering TRaSH-Guides metadata (not used)")
                instance_configs[plugin_name][instance_name] = instance_config

    state.instance_configs = instance_configs

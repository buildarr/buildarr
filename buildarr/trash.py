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

from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from shutil import move, rmtree
from typing import TYPE_CHECKING
from urllib.request import urlretrieve
from zipfile import ZipFile

from .state import state
from .util import create_temp_dir

if TYPE_CHECKING:
    from typing import Generator


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


@contextmanager
def fetch_trash_metadata() -> Generator[Path, None, None]:
    """
    Download the TRaSH-Guides metadata from the URL specified in the Buildarr config
    to a temporary directory.

    The temporary path gets added to the Buildarr global state, in addition to
    being yielded to the caller.

    Yields:
        The temporary folder containing TRaSH-Guides metadata
    """

    logger.debug("Creating TRaSH metadata download temporary directory")
    with create_temp_dir() as temp_dir:
        logger.debug("Finished creating TRaSH metadata download temporary directory")

        trash_metadata_filename = temp_dir / "trash-metadata.zip"

        logger.debug("Downloading TRaSH metadata")
        urlretrieve(  # noqa: S310  # `trash_metadata_download_url` is constrained to HTTP URLs.
            state.config.buildarr.trash_metadata_download_url,
            trash_metadata_filename,
        )
        logger.debug("Finished downloading TRaSH metadata")

        logger.debug("Extracting TRaSH metadata")
        with ZipFile(trash_metadata_filename) as zip_file:
            zip_file.extractall(path=temp_dir / "__trash-metadata__")
        trash_metadata_filename.unlink()
        logger.debug("Finished extracting TRaSH metadata")

        logger.debug("Moving TRaSH metadata files to target directory")
        for subfile in (
            temp_dir / "__trash-metadata__" / state.config.buildarr.trash_metadata_dir_prefix
        ).iterdir():
            move(str(subfile), temp_dir)
        rmtree(temp_dir / "__trash-metadata__")
        logger.debug("Finished moving TRaSH metadata files to target directory")

        state.trash_metadata_dir = temp_dir
        yield temp_dir
        state.trash_metadata_dir = None  # type: ignore[assignment]

        logger.debug("Deleting TRaSH metadata download temporary directory")
    logger.debug("Finished deleting TRaSH metadata download temporary directory")

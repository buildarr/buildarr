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

from pathlib import Path
from shutil import move
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
from zipfile import ZipFile

from .logging import logger
from .state import state


def fetch(download_dir: Path) -> None:
    """
    Download the TRaSH-Guides metadata from the URL specified in the Buildarr config
    to the given local directory.

    Args:
        download_dir (Path): Local folder to download the file to
    """

    logger.info("Fetching TRaSH metadata")

    logger.debug("Creating TRaSH metadata download temporary directory")
    with TemporaryDirectory(prefix="buildarr.") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        trash_metadata_filename = temp_dir / "trash-metadata.zip"

        logger.debug("Downloading TRaSH metadata")
        urlretrieve(state.config.buildarr.trash_metadata_download_url, trash_metadata_filename)
        logger.debug("Finished downloading TRaSH metadata")

        logger.debug("Extracting TRaSH metadata")
        with ZipFile(trash_metadata_filename) as zip_file:
            zip_file.extractall(path=temp_dir / "trash-metadata")
        logger.debug("Finished extracting TRaSH metadata")

        logger.debug("Moving TRaSH metadata files to download directory")
        for subfile in (
            temp_dir / "trash-metadata" / state.config.buildarr.trash_metadata_dir_prefix
        ).iterdir():
            move(str(subfile), download_dir)
        logger.debug("Finished moving TRaSH metadata files to download directory")

        # Temporary directory will be deleted when the with block is exited.

    logger.info("Finished fetching TRaSH metadata")

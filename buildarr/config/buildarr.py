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
Buildarr settings configuration.
"""

from __future__ import annotations

import os

from datetime import time
from pathlib import Path
from typing import Optional, Set

from pydantic import AnyHttpUrl, PositiveFloat

from ..types import DayOfWeek, NonEmptyStr
from .base import ConfigBase


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
        - "Monday"
        - "Tuesday"
        - "Wednesday"
        - "Thursday"
        - "Friday"
        - "Saturday"
        - "Sunday"
      update_times:
        - "03:00"
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

    update_days: Set[DayOfWeek] = set(day for day in DayOfWeek)
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

    request_timeout: PositiveFloat = 30  # seconds
    """
    The timeout for any API requests Buildarr makes (in seconds).

    If the timeout is reached, an error will occur and Buildarr will stop the update process.

    *New in version 0.3.0.*
    """

    trash_metadata_download_url: AnyHttpUrl = AnyHttpUrl(
        "https://github.com/TRaSH-/Guides/archive/refs/heads/master.zip"
    )
    """
    URL to download the latest TRaSH-Guides metadata from.
    """

    trash_metadata_dir_prefix: Optional[Path] = Path("Guides-master")
    """
    Metadata directory name within the downloaded ZIP file.

    *Changed in version 0.8.0*: Now can be set to `null` if the metadata directories
    are located in the root of the ZIP file.
    """

    docker_image_uri: NonEmptyStr = os.environ.get(
        "BUILDARR_DOCKER_IMAGE_URI",
        "callum027/buildarr",
    )
    """
    Default image URI to use for the Buildarr service when generating Docker Compose files.

    If undefined in the configuration file, use the value defined in the
    `$BUILDARR_DOCKER_IMAGE_URI` environment variable. This allows third-party
    Docker images to customise the version of Buildarr used in the command.

    If no environment variable is found, use `callum027/buildarr` (the official Docker image).

    *New in version 0.4.0.*
    """

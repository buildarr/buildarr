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
buildarr/cli/__init__.py
Buildarr command line interface (CLI) global group.
"""


from __future__ import annotations

import os

import click

from ..logging import setup_logger


@click.group(
    help=(
        "Construct and configure Arr PVR stacks.\n\n"
        "Can be run as a daemon or as an ad-hoc command.\n\n"
        "Supports external plugins to allow for adding support for multiple types of instances."
    ),
)
@click.option(
    "-l",
    "--log-level",
    "log_level",
    type=click.Choice(["ERROR", "WARNING", "INFO", "DEBUG"], case_sensitive=False),
    default=os.environ.get("BUILDARR_LOG_LEVEL", "INFO").upper(),
    help=(
        "Buildarr logging system log level. "
        "Can also be set using the `$BUILDARR_LOG_LEVEL' environment variable."
    ),
    show_default=True,
)
def cli(log_level: str) -> None:
    """
    Buildarr command line interface (CLI) global group.

    Global initialistation functions are run here, before any command runs.

    Args:
        log_level (str): Logging verbosity level
    """

    # Setup the Buildarr logging module.
    setup_logger(log_level)

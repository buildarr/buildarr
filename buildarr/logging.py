#!/usr/bin/env python3
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
Buildarr logging functions and objects.
"""


from __future__ import annotations

import logging
import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Mapping, MutableMapping, Optional, Tuple


__all__ = ["logger", "plugin_logger"]


class StdoutFilter(logging.Filter):
    """
    Filter for logging records that should only go to standard output.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.INFO


class StderrFilter(logging.Filter):
    """
    Filter for logging records that should only go to standard error.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno != logging.INFO


class BuildarrLoggerAdapter(logging.LoggerAdapter):
    """
    Buildarr logger adapter object.

    Gets wrapped around the standard logger object to provide additional output processing.

    Args:
        lg (Logger): Standard Python logger object
    """

    plugin_name: Optional[str] = None
    instance_name: Optional[str] = None

    @property
    def log_level(self) -> str:
        return logging.getLevelName(self.logger.level)

    def __init__(self, lg: logging.Logger) -> None:
        super().__init__(lg, {})

    def process(self, msg: str, kwargs: Mapping[str, Any]) -> Tuple[str, MutableMapping[str, Any]]:
        return (
            msg,
            {
                **kwargs,
                "extra": {
                    "plugincontext": (
                        (
                            f"buildarr.plugins.{self.plugin_name} "
                            + (f"{self.instance_name} " if self.instance_name else "")
                        )
                        if self.plugin_name
                        else "buildarr.main "
                    ),
                },
            },
        )


_base_logger = logging.getLogger("buildarr")

logger = BuildarrLoggerAdapter(_base_logger)
plugin_logger = BuildarrLoggerAdapter(_base_logger)


def setup_logger(log_level: str = "DEBUG") -> None:
    """
    Setup the Buildarr logger. Can be run multiple times.

    Args:
        log_level (str, optional): Logging level (passed from config). Defaults to `DEBUG`.
    """

    formatter = logging.Formatter(
        "%(asctime)s %(name)s:%(process)d %(plugincontext)s[%(levelname)s] %(message)s",
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(StdoutFilter())
    stdout_handler.setFormatter(formatter)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.addFilter(StderrFilter())
    stderr_handler.setFormatter(formatter)

    _base_logger.handlers = []
    _base_logger.addHandler(stdout_handler)
    _base_logger.addHandler(stderr_handler)
    _base_logger.setLevel(logging.getLevelName(log_level))

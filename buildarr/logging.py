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
Buildarr logging functions.
"""


from __future__ import annotations

import logging

from pathlib import Path
from sys import argv, stderr, stdout

from .state import state

log_record_factory = logging.getLogRecordFactory()


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


def buildarr_log_record_factory(*args, **kwargs) -> logging.LogRecord:
    """
    Factory function for adding Buildarr state information to a new log record.

    All parameters are passed to the parent log record factory function.

    Returns:
        Created log record
    """

    record = log_record_factory(*args, **kwargs)
    record.plugin = f" <{state._current_plugin}>" if state._current_plugin else ""
    record.instance = f" ({state._current_instance})" if state._current_instance else ""
    return record


def setup_logger(log_level: str = "DEBUG") -> None:
    """
    Setup the Buildarr logger. Can be run multiple times.

    Args:
        log_level (str, optional): Logging level (passed from config). Defaults to `DEBUG`.
    """

    formatter = logging.Formatter(
        f"%(asctime)s {Path(argv[0]).name.split('.')[0]}:%(process)d %(name)s [%(levelname)s]"
        "%(plugin)s%(instance)s %(message)s",
    )

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.addFilter(StdoutFilter())
    stdout_handler.setFormatter(formatter)
    stderr_handler = logging.StreamHandler(stderr)
    stderr_handler.addFilter(StderrFilter())
    stderr_handler.setFormatter(formatter)

    logging.setLogRecordFactory(buildarr_log_record_factory)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.filters = []
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)
    root_logger.setLevel(log_level.upper())


def get_log_level() -> str:
    """
    Get the currently set log level for Buildarr.

    Returns:
        Log level name
    """

    return logging.getLevelName(logging.getLogger().level)

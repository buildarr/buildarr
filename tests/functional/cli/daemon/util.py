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
Helper functions for the `buildarr daemon` CLI command functional tests.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def next_hour(hours: int = 1) -> str:
    """
    Get the timestamp for `hours` hours in the future from the current system time.

    Args:
        hours (int, optional): The amount of hours in the future. Defaults to 1.

    Returns:
        Future time, in `HH:MM` format
    """

    return (datetime.now() + timedelta(hours=hours)).strftime("%H:%M")

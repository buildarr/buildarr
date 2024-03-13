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
Utility functions for the `buildarr compose` CLI command functional tests.
"""

from __future__ import annotations

import sys

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def get_source(path: Path) -> str:
    source_dir = path.parent

    return str(
        (
            PurePosixPath(
                f"/{source_dir.drive.rstrip(':').lower()}",
            ).joinpath(*source_dir.parts[1:])
            if sys.platform == "win32"
            else source_dir
        ),
    )

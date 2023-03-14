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
Buildarr general utility functions.
"""


from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from os import PathLike
    from typing import Any, Dict, Union


__all__ = ["get_absolute_path", "merge_dicts"]


def get_absolute_path(path: Union[str, PathLike]) -> Path:
    """
    Return the absolute, fully resolved version of the given path.

    Args:
        path (Union[str, PathLike]): Path to resolve

    Returns:
        Fully resolved absolute path
    """

    return Path(path).absolute().resolve()


def merge_dicts(*dicts: Mapping[Any, Any]) -> Dict[Any, Any]:
    """
    Recursively merge the specificed mappings into one dictionary structure.

    If the same key exists at the same level in more than one mapping,
    the last referenced one takes prcedence.

    Returns:
        Merged dictionary
    """

    merged_dict: Dict[Any, Any] = {}

    for d in dicts:
        for key, value in d.items():
            if key in merged_dict and isinstance(merged_dict[key], Mapping):
                merged_dict[key] = merge_dicts(merged_dict[key], value)
            elif isinstance(value, Mapping):
                merged_dict[key] = merge_dicts(value)
            else:
                merged_dict[key] = value

    return merged_dict

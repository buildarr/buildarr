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

import os

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from typing import Any, Dict, Generator, Union


__all__ = ["get_absolute_path", "merge_dicts"]


def get_absolute_path(path: Union[str, os.PathLike]) -> Path:
    """
    Return the absolute version of the given path, *without* resolving symbolic links.

    The reason why, in some cases, we don't want to resolve symbolic links is because
    in long lived applications such as daemons, the link target could have changed while the
    file was not being accessed, therefore making our stored reference to the file invalid.

    Symbolic links should only be resolved when actually accessing the file,
    without caching the result.

    Notes:

    * `Path.absolute` does not expand `.` and `..`.
    * `Path.resolve` resolves symbolic links, and has no way to disable it.
    * Using the old `os.path` functions does what we want, so use them.

    Args:
        path (Union[str, os.PathLike]): Path to make absolute.

    Returns:
        Absolute path
    """

    return Path(os.path.abspath(os.path.expanduser(path)))  # noqa: PTH100 PTH111


def get_resolved_path(path: Union[str, os.PathLike]) -> Path:
    """
    Return the absolute version of the given path, resolving symbolic links.

    This is more useful in ad-hoc runs, where the file will need to be resolved regardless.
    Do it once so we know exactly what hard file we're operating on.

    Unlike `Path.resolve`, this returns an absolute path even if the actual path doesn't exist.

    Notes:

    * `Path.resolve(strict=True)` raises an error when the path doesn't exist.
    * `Path.resolve(strict=False)` does not (or does not completely) resolve the path
      if it doesn't exist.
    * Using the old `os.path` functions does what we want, so use them.

    Args:
        path (Union[str, os.PathLike]): Path to resolve.

    Returns:
        Absolute resolved path
    """

    return Path(os.path.realpath(os.path.expanduser(path)))  # noqa: PTH111


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


@contextmanager
def create_temp_dir(prefix: str = "buildarr.", **kwargs) -> Generator[Path, None, None]:
    """
    Create a temporary directory, give access to it for the executing context,
    and clean up the directory upon exit from the context.

    Any additional parameters are passed to `tempfile.TemporaryDirectory`.

    Args:
        prefix (str, optional): Temporary directory name prefix. Defaults to `buildarr.`.

    Yields:
        Temporary directory path
    """

    with TemporaryDirectory(prefix=prefix, **kwargs) as temp_dir_str:
        yield Path(temp_dir_str)

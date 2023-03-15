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
Buildarr secrets metadata loading function.
"""


from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from pydantic import create_model

from ..logging import logger
from ..state import state
from ..types import NonEmptyStr
from ..util import get_absolute_path
from .base import SecretsBase

if TYPE_CHECKING:
    from os import PathLike
    from typing import Optional, Set, Union


def load(path: Union[str, PathLike], use_plugins: Optional[Set[str]] = None) -> None:
    """
    Create the secrets file model using the specified plugins.

    Args:
        load_plugins (Set[str], optional): Plugins to use. Use all if empty.

    Returns:
        Dynamically generated secrets file model
    """

    path = get_absolute_path(path)

    logger.debug("Creating secrets model")
    model = create_model(
        "Secrets",
        **{
            plugin_name: (
                Dict[NonEmptyStr, plugin.secrets],  # type: ignore
                {},
            )
            for plugin_name, plugin in state.plugins.items()
            if not use_plugins or plugin_name in use_plugins
        },
        __base__=SecretsBase,
    )
    logger.debug("Finished creating secrets model")

    logger.info("Loading secrets file from '%s'", path)
    try:
        state.secrets = model.read(path)
        logger.info("Finished loading secrets file")
    except FileNotFoundError:
        logger.info("Secrets file does not exist, will create new file")
        state.secrets = model()

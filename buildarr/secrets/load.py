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

from logging import getLogger
from typing import TYPE_CHECKING, Dict

from pydantic import create_model

from ..state import state
from ..types import NonEmptyStr
from .base import SecretsBase

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Set

logger = getLogger(__name__)


def load_secrets(path: Path, use_plugins: Optional[Set[str]] = None) -> bool:
    """
    Create the secrets file model using the specified plugins,
    and load the secrets file into global state if it exists.

    If the file doesn't exist, create an empty model structure instead.

    Args:
        path (Path): The secrets file to load, if it exists.
        use_plugins (Optional[Set[str]]): Plugins to use. Default is to use all plugins.

    Returns:
        `True` if a secrets file was loaded, otherwise `False`
    """

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

    try:
        logger.debug("Loading secrets from file '%s'", path)
        state.secrets = model.read(path)
        logger.debug("Finished loading secrets from file")
        return True
    except FileNotFoundError:
        logger.debug("Secrets file not found, initialising empty secrets metadata")
        state.secrets = model()
        logger.debug("Finished initialising empty secrets metadata")
        return False

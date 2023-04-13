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
Buildarr configuration rendering function.
"""


from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import TYPE_CHECKING

from ..state import state

if TYPE_CHECKING:
    from typing import DefaultDict, Dict

    from .models import ConfigPlugin

logger = getLogger(__name__)


def render_instance_configs() -> None:
    """
    Render dynamically populated attributes on instance configurations,
    and update the global state.

    If an instance configuration returned `True` for `uses_trash_metadata`,
    the filepath to the downloaded metadata directory will be available as
    `state.trash_metadata_dir` in the global state.
    """

    instance_configs: DefaultDict[str, Dict[str, ConfigPlugin]] = defaultdict(dict)

    for plugin_name, instance_name in state._execution_order:
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            logger.debug("Rendering dynamic configuration attributes")
            instance_configs[plugin_name][instance_name] = manager.render(instance_config)
            logger.debug("Finished dynamic configuration attributes")

    state.instance_configs = instance_configs

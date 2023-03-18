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
Buildarr configuration instance-to-instance dependency resolution functions.
"""


from __future__ import annotations

from typing import TYPE_CHECKING

from ..state import state

if TYPE_CHECKING:
    from typing import List, Optional, Set

    from ..state import PluginInstanceRef


def resolve_instance_dependencies() -> None:
    """
    Generate a list of plugin-instance references in the order which
    operations should be performed on them, and store it as `state._execution_order`.

    This function requires `config.load_instance_configs` to be run first,
    as that function populates `state._instance_dependencies`, which this function uses.

    A depth-first search on the `state._instance_dependencies` dependency tree structure
    is performed, which is generated using instance name references defined within
    Buildarr instance configurations.
    """

    added_plugin_instances: Set[PluginInstanceRef] = set()
    execution_order: List[PluginInstanceRef] = []

    for plugin_name, instance_configs in state.instance_configs.items():
        for instance_name in instance_configs.keys():
            instance = (plugin_name, instance_name)
            if instance in added_plugin_instances:
                continue
            _resolve_instance_dependencies(
                added_plugin_instances=added_plugin_instances,
                execution_order=execution_order,
                plugin_name=plugin_name,
                instance_name=instance_name,
            )

    state._execution_order = execution_order


def _resolve_instance_dependencies(
    added_plugin_instances: Set[PluginInstanceRef],
    execution_order: List[PluginInstanceRef],
    plugin_name: str,
    instance_name: str,
    dependency_tree: Optional[List[PluginInstanceRef]] = None,
) -> None:
    """
    Recursive depth-first search function for `resolve_instance_dependencies`.

    Args:
        added_plugin_instances (Set[PluginInstanceRef]): Structure to avoid re-evaluating branches.
        execution_order (List[PluginInstanceRef]): Final data structure, appended to in-place.
        plugin_name (str): Name of the plugin the current instance being evaluated is under.
        instance_name (str): Name of the instance to evaluate dependencies for.
        dependency_tree (List[PluginInstanceRef], optional): Tree used to find dependency cycles.

    Raises:
        ValueError: When a plugin used in an instance reference is not installed
        ValueError: When a plugin used in an instance reference is disabled or not configured
        ValueError: When a dependency cycle is detected
    """

    if not dependency_tree:
        dependency_tree = []

    plugin_instance: PluginInstanceRef = (plugin_name, instance_name)

    if plugin_name not in state.instance_configs:
        error_message = 'Unable to resolve instance dependency "'
        try:
            previous_pi = dependency_tree[-1]
            error_message += f"{previous_pi[0]}.instances[{repr(previous_pi[1])}] -> "
        except IndexError:
            # Shouldn't happen because dependency keys are generated from
            # instance configuration, but handle it just in case.
            pass
        error_message += f'{plugin_name}.instances[{repr(instance_name)}]": '
        if plugin_name not in state.plugins:
            error_message += f"Plugin '{plugin_name}' not installed"
        else:
            error_message += f"Plugin '{plugin_name}' disabled, or no configuration defined for it"
        raise ValueError(error_message)

    if plugin_instance in dependency_tree:
        raise ValueError(
            (
                "Detected dependency cycle in configuration for instance references:\n"
                + "\n".join(
                    f"  {i}. {pname}.instances[{repr(iname)}]"
                    for i, (pname, iname) in enumerate([*dependency_tree, plugin_instance], 1)
                )
            ),
        )

    if plugin_instance in state._instance_dependencies:
        for target_plugin_instance in state._instance_dependencies[plugin_instance]:
            if target_plugin_instance not in added_plugin_instances:
                target_plugin, target_instance = target_plugin_instance
                _resolve_instance_dependencies(
                    added_plugin_instances=added_plugin_instances,
                    execution_order=execution_order,
                    plugin_name=target_plugin,
                    instance_name=target_instance,
                    dependency_tree=[*dependency_tree, plugin_instance],
                )

    added_plugin_instances.add(plugin_instance)
    execution_order.append(plugin_instance)

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
'buildarr run' CLI command.
"""


from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Mapping, Optional, Set

import click

from importlib_metadata import version as package_version

from ..config import ConfigPlugin, ConfigPluginType, load as load_config
from ..logging import logger, plugin_logger
from ..manager import ManagerPlugin
from ..secrets import SecretsPlugin, load as load_secrets
from ..state import PluginInstanceRef, state
from ..trash import fetch as trash_fetch
from . import cli
from .exceptions import RunInstanceConnectionTestFailedError, RunNoPluginsDefinedError


@cli.command(
    help=(
        "Configure instances defined in the Buildarr config file, and exit.\n\n"
        "If CONFIG-PATH is not defined, use `buildarr.yml' from the current directory."
    ),
)
@click.argument(
    "config_path",
    metavar="[CONFIG-PATH]",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=Path.cwd() / "buildarr.yml",
)
@click.option(
    "-p",
    "--plugin",
    "use_plugins",
    metavar="PLUGIN",
    type=str,
    callback=lambda ctx, params, plugins: set(plugins),
    multiple=True,
    help=(
        "Use only the specified Buildarr plugin. Default is to use all installed plugins. "
        "(can be defined multiple times)"
    ),
)
def run(config_path: Path, use_plugins: Set[str]) -> None:
    """
    'buildarr run' main routine.

    Args:
        config_path (Path): Configuration file to load.
        plugins (Set[str]): Plugins to load. If empty, use all plugins.
    """

    logger.info(
        "Buildarr version %s (log level: %s)",
        package_version("buildarr"),
        logger.log_level,
    )

    # Load and validate the Buildarr configuration.
    load_config(path=config_path, use_plugins=use_plugins)

    # Run the instance update main function.
    _run(use_plugins)


def _run(use_plugins: Optional[Set[str]] = None) -> None:
    """
    Buildarr instance update routine.

    For each defined instance, cache required secrets, get the active remote configuration
    and push updates as required according to the current local configuration.

    Args:
        use_plugins (Set[str], optional): Plugins to use. If empty or unset, load all plugins.
    """

    if not use_plugins:
        use_plugins = set()

    # Dump the currently active Buildarr configuration file to the debug log.
    logger.debug("Buildarr configuration:\n%s", state.config.yaml(exclude_unset=True))

    # List of plugins with which to run the Buildarr update process.
    # Only plugins with explicitly defined configurations get run.
    run_plugins: List[str] = []

    # Output the currently loaded plugins to the logs.
    logger.info(
        "Plugins loaded: %s",
        ", ".join(sorted(state.plugins.keys())) if state.plugins else "(no plugins found)",
    )

    # Fetch fully-qualified configurations for each instance under each selected plugin
    # (or all plugins if `use_plugins` is empty).
    # The above action is done in an instance-specific context, so that
    # when the instance-specific configuration gets evaluated by the configuration parser,
    # instance name references are processed and dependencies get added
    # to `state._instance_dependencies`.
    configs: Dict[str, Dict[str, ConfigPlugin]] = {}
    managers: Dict[str, ManagerPlugin] = {}
    for plugin_name, plugin in state.plugins.items():
        if use_plugins and plugin_name not in use_plugins:
            continue
        if plugin_name in state.config.__fields_set__:
            run_plugins.append(plugin_name)
            plugin_manager = plugin.manager()
            plugin_config: ConfigPluginType = getattr(state.config, plugin_name)
            managers[plugin_name] = plugin_manager
            configs[plugin_name] = {}
            for instance_name in (
                plugin_config.instances.keys() if plugin_config.instances else ["default"]
            ):
                with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                    configs[plugin_name][instance_name] = plugin_manager.get_instance_config(
                        plugin_config,
                        instance_name,
                    )

    # If no plugins are configured to run, there is nothing more we can do.
    # Stop here.
    if not run_plugins:
        raise RunNoPluginsDefinedError("No loaded plugins configured in Buildarr")

    # Log the plugins being executed in this Buildarr run.
    logger.info("Running with plugins: %s", ", ".join(run_plugins))

    # Traverse the instance dependency chain structure to determine
    # the instance update execution order.
    execution_order = _get_execution_order(configs)

    # Load the secrets file if it exists, and initialise the secrets metadata.
    # If `use_plugins` is undefined, load using all plugins available
    # to preserve cached secrets metadata that isn't used.
    load_secrets(path=state.config.buildarr.secrets_file_path, use_plugins=use_plugins)

    # Generate the secrets structure for each plugin and instance,
    # using the old structure cached from file as a base, and
    # fetching them from the remote instance if they don't exist.
    for plugin_name in run_plugins:
        plugin_secrets: Dict[str, SecretsPlugin] = getattr(state.secrets, plugin_name)
        for instance_name, instance_config in configs[plugin_name].items():
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                plugin_logger.info("Checking secrets")
                try:
                    instance_secrets = plugin_secrets[instance_name]
                except KeyError:
                    instance_secrets = None
                if instance_secrets and instance_secrets.test():
                    plugin_logger.info("Connection test successful using cached secrets")
                    plugin_secrets[instance_name] = instance_secrets
                else:
                    plugin_logger.info(
                        "Connection test failed using cached secrets (or not cached), "
                        "fetching secrets",
                    )
                    instance_secrets = state.plugins[plugin_name].secrets.get(instance_config)
                    if instance_secrets.test():
                        plugin_logger.info("Connection test successful using fetched secrets")
                        plugin_secrets[instance_name] = instance_secrets
                    else:
                        raise RunInstanceConnectionTestFailedError(
                            "Connection test failed using fetched secrets "
                            f"for instance '{instance_name}': {instance_secrets}",
                        )
                plugin_logger.info("Finished checking secrets")

    # Save the latest secrets file to disk.
    logger.info("Saving updated secrets file to '%s'", state.config.buildarr.secrets_file_path)
    state.secrets.write(state.config.buildarr.secrets_file_path)
    logger.info("Finished saving updated secrets file")

    # Check if any instances are configured to get metadata from TRaSH-Guides.
    uses_trash_metadata = False
    for plugin_name in run_plugins:
        manager = managers[plugin_name]
        for instance_config in configs[plugin_name].values():
            if manager.uses_trash_metadata(instance_config):
                uses_trash_metadata = True
                break
        if uses_trash_metadata:
            break

    # Create a temporary directory for Buildarr to use.
    logger.debug("Creating runtime directory")
    with TemporaryDirectory(prefix="buildarr.") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        logger.debug("Finished creating runtime directory")

        # If the TRaSH metadata is required, download it
        # and save it to a folder.
        if uses_trash_metadata:
            logger.debug("Creating TRaSH metadata directory")
            trash_metadata_dir = temp_dir / "trash"
            trash_metadata_dir.mkdir()
            logger.debug("Finished creating TRaSH metadata directory")
            trash_fetch(trash_metadata_dir)
        else:
            logger.debug("TRaSH metadata not required")

        # Update all instances in the determined execution order.
        for plugin_name, instance_name in execution_order:
            manager = managers[plugin_name]
            instance_config = configs[plugin_name][instance_name]
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                # Get the instance's secrets object.
                instance_secrets = getattr(state.secrets, plugin_name)[instance_name]

                # Add actual parameters to resource definitions where
                # TRaSH IDs are referenced.
                if manager.uses_trash_metadata(instance_config):
                    plugin_logger.info("Rendering TRaSH-Guides metadata")
                    instance_config = manager.render_trash_metadata(
                        instance_config,
                        trash_metadata_dir,
                    )
                    plugin_logger.info("Finished rendering TRaSH-Guides metadata")

                # Fetch the current active configuration from the remote instance,
                # so they can be configured.
                plugin_logger.info("Getting remote configuration")
                remote_instance_config = manager.from_remote(instance_config, instance_secrets)
                plugin_logger.info("Finished getting remote configuration")
                plugin_logger.debug(
                    "Remote configuration:\n%s",
                    remote_instance_config.yaml(exclude_unset=True),
                )

                # Push the updated state to the instance.
                plugin_logger.info("Updating remote configuration")
                plugin_logger.info(
                    (
                        "Remote configuration successfully updated"
                        if manager.update_remote(
                            plugin_name,
                            instance_config,
                            instance_secrets,
                            remote_instance_config,
                        )
                        else "Remote configuration is up to date"
                    ),
                )
                plugin_logger.info("Finished updating remote configuration")

                # TODO: Re-fetch the remote configuration and test that it
                #       now matches the local configuration.
                # print("Re-fetching remote config")
                # new_active_config = manager.get_active_config(
                #     instance_config,
                #     getattr(secrets, manager_name),
                # )
                # print(
                #     "Active configuration for instance name "
                #     f'{instance_name}' after update:\n"
                #     f"{pformat(new_active_config.dict(exclude_unset=True))}",
                # )


def _get_execution_order(
    configs: Mapping[str, Mapping[str, ConfigPlugin]],
) -> List[PluginInstanceRef]:
    """
    Return a list of plugin-instance references in the order which
    operations should be performed on them.

    This performs a depth-first search on the dependency tree structure
    stored in `state._instance_dependencies`, which is generated using
    instance name references defined within Buildarr instance configurations.

    Args:
        configs (Mapping[str, Mapping[str, ConfigPlugin]]): Plugin and instance configuration.

    Returns:
        Execution order of instances specified as a list of (plugin, instance) tuples
    """

    added_plugin_instances: Set[PluginInstanceRef] = set()
    execution_order: List[PluginInstanceRef] = []

    logger.info("Resolving instance dependencies")
    logger.debug("Execution order:")

    for plugin_name, instance_configs in configs.items():
        for instance_name in instance_configs.keys():
            instance = (plugin_name, instance_name)
            if instance in added_plugin_instances:
                continue
            __get_execution_order(
                configs=configs,
                added_plugin_instances=added_plugin_instances,
                execution_order=execution_order,
                plugin_name=plugin_name,
                instance_name=instance_name,
            )

    logger.info("Finished resolving instance dependencies")

    return execution_order


def __get_execution_order(
    configs: Mapping[str, Mapping[str, ConfigPlugin]],
    added_plugin_instances: Set[PluginInstanceRef],
    execution_order: List[PluginInstanceRef],
    plugin_name: str,
    instance_name: str,
    dependency_tree: Optional[List[PluginInstanceRef]] = None,
) -> None:
    """
    Recursive depth-first search function for `get_execution_order`.

    Args:
        configs (Mapping[str, Mapping[str, ConfigPlugin]]): Plugin and instance configuration.
        added_plugin_instances (Set[PluginInstanceRef]): Structure to avoid re-evaluating branches.
        execution_order (List[PluginInstanceRef]): Final data structure, appended to in-place.
        plugin_name (str): Plugin the current instance being evaluated is under.
        instance_name (str): Name of instance to evaluate dependencies for.
        dependency_tree (List[PluginInstanceRef], optional): Tree used to find dependency cycles.

    Raises:
        ValueError: When a plugin used in an instance reference is not installed
        ValueError: When a plugin used in an instance reference is disabled or not configured
        ValueError: When a dependency cycle is detected
    """

    if not dependency_tree:
        dependency_tree = []

    plugin_instance: PluginInstanceRef = (plugin_name, instance_name)

    if plugin_name not in configs:
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
                __get_execution_order(
                    configs=configs,
                    added_plugin_instances=added_plugin_instances,
                    execution_order=execution_order,
                    plugin_name=target_plugin,
                    instance_name=target_instance,
                    dependency_tree=[*dependency_tree, plugin_instance],
                )

    added_plugin_instances.add(plugin_instance)
    execution_order.append(plugin_instance)
    logger.debug("%i. %s.instances[%s]", len(execution_order), plugin_name, repr(instance_name))

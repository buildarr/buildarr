# -*- coding: utf-8 -*-

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


from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Set

import click

from importlib_metadata import version as package_version

from ..config import ConfigPlugin, ConfigPluginType, load as load_config
from ..logging import logger, plugin_logger
from ..manager import ManagerPlugin
from ..plugins import plugin_context
from ..secrets import SecretsPlugin, load as load_secrets
from ..state import state
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
        plugins (Set[str]): Plugins to load. If empty, load all plugins.
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


def _run(use_plugins: Set[str] = set()) -> None:
    """
    Buildarr instance update routine.

    For each defined instance, cache required secrets, get the active remote configuration
    and push updates as required according to the current local configuration.

    Args:
        plugins (Set[str], optional): Plugins to load. If empty or unset, load all plugins.
    """

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

    # Generate instance-specific configs for each plugin, with all
    # instance-specific and plugin-global fields resolved.
    # If a config for the plugin is not explicitly defined within
    # the Buildarr configuration, make sure it is not run.
    configs: Dict[str, Dict[str, ConfigPlugin]] = {}
    managers: Dict[str, ManagerPlugin] = {}
    for plugin_name, plugin in state.plugins.items():
        if plugin_name in state.config.__fields_set__:
            run_plugins.append(plugin_name)
            plugin_manager = plugin.manager()
            plugin_config: ConfigPluginType = getattr(state.config, plugin_name)
            managers[plugin_name] = plugin_manager
            configs[plugin_name] = {
                instance_name: plugin_manager.get_instance_config(plugin_config, instance_name)
                for instance_name in (
                    plugin_config.instances.keys() if plugin_config.instances else ["default"]
                )
            }

    # If no plugins are configured to run, there is nothing more we can do.
    # Stop hjere.
    if not run_plugins:
        raise RunNoPluginsDefinedError("No loaded plugins configured in Buildarr")

    # Log the plugins being executed in this Buildarr run.
    logger.info("Running with plugins: %s", ", ".join(run_plugins))

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
            with plugin_context(plugin_name, instance_name):
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
                        plugin_logger.info("Connection test uccessful using fetched secrets")
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

        # Update all instances.
        # TODO: Define execution order of all instances across plugins,
        # because in the future, some will depend on others to be configured
        # properly to function. (e.g. Prowlarr depending on Sonarr/Radarr)
        for plugin_name in run_plugins:
            manager = managers[plugin_name]
            for instance_name, instance_config in configs[plugin_name].items():
                with plugin_context(plugin_name, instance_name):
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

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
`buildarr run` CLI command.
"""


from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Set

import click

from importlib_metadata import version as package_version

from ..config import load_config, load_instance_configs, resolve_instance_dependencies
from ..logging import logger, plugin_logger
from ..manager import load_managers
from ..secrets import SecretsPlugin, load_secrets
from ..state import state
from ..trash import fetch as trash_fetch
from ..util import create_temp_dir, get_absolute_path
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
    callback=lambda ctx, params, path: get_absolute_path(path),
)
@click.option(
    "-D",
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Enable dry-run mode. Update runs are executed, but instances are not modified.",
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
def run(config_path: Path, dry_run: bool, use_plugins: Set[str]) -> None:
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

    if dry_run:
        logger.info(
            "Dry-run mode enabled: executing update runs, but will not modify instances",
        )
        state.dry_run = True

    logger.info("Loading configuration file '%s'", config_path)
    load_config(path=config_path, use_plugins=use_plugins)
    logger.info("Finished loading configuration file")

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

    # Output the currently loaded plugins to the logs.
    logger.info(
        "Plugins loaded: %s",
        ", ".join(sorted(state.plugins.keys())) if state.plugins else "(no plugins found)",
    )

    # Load the manager object for each plugin into global state.
    logger.debug("Loading plugin managers")
    load_managers(use_plugins)
    logger.debug("Finished loading plugin managers")

    # Parse and validate the instance-specific configurations under each plugin,
    # and load them into global state.
    logger.info("Loading instance configurations")
    load_instance_configs(use_plugins)
    logger.info("Finished loading instance configurations")

    # If no plugins are configured to run, there is nothing more we can do.
    # Stop here.
    if not state.active_plugins:
        raise RunNoPluginsDefinedError("No loaded plugins configured in Buildarr")

    # Log the plugins being executed in this Buildarr run.
    logger.info("Running with plugins: %s", ", ".join(state.active_plugins))

    # Resolve the instance dependencies fetched from the instance-specific configuration,
    # and load the determined execution order into global state.
    logger.info("Resolving instance dependencies")
    resolve_instance_dependencies()
    logger.debug("Execution order:")
    for i, (plugin_name, instance_name) in enumerate(state._execution_order, 1):
        logger.debug("%i. %s.instances[%s]", i, plugin_name, repr(instance_name))
    logger.info("Finished resolving instance dependencies")

    # Load the secrets file if it exists, and initialise the secrets metadata.
    # If `use_plugins` is undefined, load using all plugins available
    # to preserve cached secrets metadata that isn't used.
    secrets_file_path = state.config.buildarr.secrets_file_path
    logger.info("Loading secrets file from '%s'", secrets_file_path)
    if load_secrets(path=secrets_file_path, use_plugins=use_plugins):
        logger.info("Finished loading secrets file")
    else:
        logger.info("Secrets file does not exist, will create new file")

    # Generate the secrets structure for each plugin and instance,
    # using the old structure cached from file as a base, and
    # fetching them from the remote instance if they don't exist.
    for plugin_name in state.active_plugins:
        plugin_secrets: Dict[str, SecretsPlugin] = getattr(state.secrets, plugin_name)
        for instance_name, instance_config in state.instance_configs[plugin_name].items():
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                plugin_logger.info("Checking secrets")
                try:
                    try_instance_secrets = plugin_secrets[instance_name]
                except KeyError:
                    try_instance_secrets = None
                if try_instance_secrets and try_instance_secrets.test():
                    plugin_logger.info("Connection test successful using cached secrets")
                    plugin_secrets[instance_name] = try_instance_secrets
                else:
                    plugin_logger.info(
                        "Connection test failed using cached secrets (or not cached), "
                        "fetching secrets",
                    )
                    instance_secrets: SecretsPlugin = state.plugins[plugin_name].secrets.get(
                        instance_config,
                    )
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
    logger.info("Saving updated secrets file to '%s'", secrets_file_path)
    state.secrets.write(secrets_file_path)
    logger.info("Finished saving updated secrets file")

    # Check if any instances are configured to get metadata from TRaSH-Guides.
    uses_trash_metadata = False
    for plugin_name in state.active_plugins:
        for instance_config in state.instance_configs[plugin_name].values():
            if state.managers[plugin_name].uses_trash_metadata(instance_config):
                uses_trash_metadata = True
                break
        if uses_trash_metadata:
            break

    # Create a temporary directory for Buildarr to use.
    logger.debug("Creating runtime directory")
    with create_temp_dir() as temp_dir:
        logger.debug("Finished creating runtime directory")

        # If the TRaSH metadata is required, download it
        # and save it to a folder.
        if uses_trash_metadata:
            logger.debug("Creating TRaSH metadata directory")
            trash_metadata_dir = temp_dir / "trash"
            trash_metadata_dir.mkdir()
            logger.debug("Finished creating TRaSH metadata directory")
            logger.info("Fetching TRaSH metadata")
            trash_fetch(trash_metadata_dir)
            logger.info("Finished fetching TRaSH metadata")
        else:
            logger.debug("TRaSH metadata not required")

        # Update all instances in the determined execution order.
        for plugin_name, instance_name in state._execution_order:
            manager = state.managers[plugin_name]
            instance_config = state.instance_configs[plugin_name][instance_name]
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

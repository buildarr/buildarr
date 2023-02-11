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
from typing import Dict, List, Set, cast

import click

from .. import __version__ as buildarr_version
from ..config import BuildarrConfig, ConfigBase, ConfigPlugin, load as load_config
from ..logging import logger, plugin_logger
from ..manager import ManagerPlugin
from ..secrets import SecretsPlugin, get_model
from ..state import plugin_context, plugins
from ..trash import fetch as trash_fetch
from . import cli
from .exceptions import RunNoPluginsDefinedError


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

    logger.info("Buildarr version %s (log level: %s)", buildarr_version, logger.log_level)

    # Load and validate the Buildarr configuration.
    files, config = load_config(use_plugins, config_path)

    # Run the instance update main function.
    _run(config, use_plugins)


def _run(config: ConfigBase, use_plugins: Set[str] = set()) -> None:
    """
    Buildarr instance update routine.

    For each defined instance, cache required secrets, get the active remote configuration
    and push updates as required according to the current local configuration.

    Args:
        config (ConfigBase): Configuration file to load.
        plugins (Set[str], optional): Plugins to load. If empty or unset, load all plugins.
    """

    # Dump the currently active Buildarr configuration file to the debug log.
    logger.debug("Buildarr configuration:\n%s", config.yaml(exclude_unset=True))

    # Get Buildarr-specific configuration from the global config.
    buildarr_config = cast(BuildarrConfig, config.buildarr)  # type: ignore[attr-defined]

    # List of plugins with which to run the Buildarr update process.
    # Only plugins with explicitly defined configurations get run.
    run_plugins: List[str] = []

    # Output the currently loaded plugins to the logs.
    logger.info(
        "Plugins loaded: %s",
        ", ".join(sorted(plugins.keys())) if plugins else "(no plugins found)",
    )

    # Generate instance-specific configs for each plugin, with all
    # instance-specific and plugin-global fields resolved.
    # If a config for the plugin is not explicitly defined within
    # the Buildarr configuration, make sure it is not run.
    configs: Dict[str, Dict[str, ConfigPlugin]] = {}
    managers: Dict[str, ManagerPlugin] = {}
    for plugin_name, plugin in plugins.items():
        if plugin_name in config.__fields_set__:
            run_plugins.append(plugin_name)
            plugin_manager = plugin.manager()
            plugin_config = getattr(config, plugin_name)
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

    # Log the plugins being used in this Buildarr run.
    logger.info("Using plugins: %s", ", ".join(run_plugins))

    # Load the secrets plugins, and the model used to load and save the secrets file.
    secrets_model = get_model(set(run_plugins))

    # Load the current secrets file. This will be used as a cache
    # to help generate the new secrets file which will be used this run.
    logger.info("Loading secrets file from '%s'", buildarr_config.secrets_file_path)
    try:
        old_secrets_obj = secrets_model.read(buildarr_config.secrets_file_path)
        logger.info("Finished loading secrets file")
    except FileNotFoundError:
        logger.info("Secrets file does not exist, will create new file")
        old_secrets_obj = secrets_model()

    # Generate the secrets structure for each plugin and instance,
    # using the old structure cached from file as a base, and
    # fetching them from the remote instance if they don't exist.
    secrets: Dict[str, Dict[str, SecretsPlugin]] = {}
    for plugin_name in run_plugins:
        if plugin_name not in secrets:
            secrets[plugin_name] = {}
        for instance_name, instance_config in configs[plugin_name].items():
            with plugin_context(plugin_name, instance_name):
                plugin_logger.info("Checking and fetching secrets")
                # TODO: Test currently cached secrets to see if they are still valid,
                #       and use those instead of getting new secrets every time.
                try:
                    instance_secrets = getattr(old_secrets_obj, plugin_name)[instance_name]
                except KeyError:
                    instance_secrets = plugins[plugin_name].secrets.get(instance_config)
                secrets[plugin_name][instance_name] = instance_secrets
                plugin_logger.info("Finished checking and fetching secrets")

    # Save the latest secrets file to disk.
    logger.info("Saving updated secrets file to '%s'", buildarr_config.secrets_file_path)
    secrets_model(**secrets).write(buildarr_config.secrets_file_path)
    logger.info("Finished saving updated secrets file")

    # Check if any plugins are configured to get metadata from TRaSH-Guides.
    for plugin_name in run_plugins:
        if managers[plugin_name].uses_trash_metadata(getattr(config, plugin_name)):
            uses_trash_metadata = True
            break
    else:
        uses_trash_metadata = False

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
            trash_fetch(buildarr_config, trash_metadata_dir)
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
                    instance_secrets = secrets[plugin_name][instance_name]

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

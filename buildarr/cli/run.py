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

from logging import getLogger
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING

import click

from .. import __version__
from ..config import (
    load_config,
    load_instance_configs,
    render_instance_configs,
    resolve_instance_dependencies,
)
from ..logging import get_log_level
from ..manager import load_managers
from ..secrets import load_secrets
from ..state import state
from ..trash import fetch_trash_metadata, trash_metadata_used
from ..util import get_resolved_path
from . import cli
from .exceptions import RunInstanceConnectionTestFailedError, RunNoPluginsDefinedError

if TYPE_CHECKING:
    from typing import Dict, Optional, Set

    from ..secrets import SecretsPlugin

logger = getLogger(__name__)


@cli.command(
    help=(
        "Update configured instances, and exit.\n\n"
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
        path_type=Path,
    ),
    default=Path.cwd() / "buildarr.yml",
    # Get absolute path and resolve symlinks in ad-hoc runs.
    callback=lambda ctx, params, path: get_resolved_path(path),
)
@click.option(
    "-s",
    "--secrets-file",
    "secrets_file_path",
    metavar="SECRETS-JSON",
    type=click.Path(
        # The secrets file does not need to exist (it will be created in that case).
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    default=None,
    # Get absolute path and resolve symlinks in ad-hoc runs.
    callback=lambda ctx, params, path: get_resolved_path(path) if path else None,
    help=(
        "Read secrets metadata from (and write back to) the specified JSON file. "
        "If unspecified, use the value from the configuration file, "
        "and if undefined there, default to `secrets.json'."
    ),
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
def run(
    config_path: Path,
    secrets_file_path: Optional[Path],
    use_plugins: Set[str],
) -> None:
    """
    `buildarr run` main routine.

    Args:
        config_path (Path): Configuration file to load.
        plugins (Set[str]): Plugins to load. If empty, use all plugins.
    """

    logger.info("Buildarr version %s (log level: %s)", __version__, get_log_level())

    logger.info("Loading configuration file '%s'", config_path)
    load_config(path=config_path, use_plugins=use_plugins)
    logger.info("Finished loading configuration file")

    if not secrets_file_path:
        secrets_file_path = state.config.buildarr.secrets_file_path

    # Run the instance update main function.
    _run(secrets_file_path, use_plugins)


def _run(secrets_file_path: Path, use_plugins: Optional[Set[str]] = None) -> None:
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
    logger.debug("Buildarr configuration:")
    for config_line in state.config.yaml(exclude_unset=True).splitlines():
        logger.debug(indent(config_line, "  "))

    # Output the currently loaded plugins to the logs.
    plugin_strs = [f"{pn} ({state.plugins[pn].version})" for pn in sorted(state.plugins.keys())]
    logger.info(
        "Loaded plugins: %s",
        ", ".join(plugin_strs) if plugin_strs else "(no plugins found)",
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
        logger.debug("  %i. %s.instances[%s]", i, plugin_name, repr(instance_name))
    logger.info("Finished resolving instance dependencies")

    # Render dynamically populated attributes in instance configurations,
    # with the TRaSH-Guides metadata directory available in the global state
    # only if at least one instance configuration requires it.
    if trash_metadata_used():
        logger.info("Fetching TRaSH metadata")
        with fetch_trash_metadata():
            logger.info("Finished fetching TRaSH metadata")
            logger.info("Rendering instance configuration dynamic attributes")
            render_instance_configs()
            logger.info("Finished rendering instance configuration dynamic attributes")
    else:
        logger.info("Rendering instance configuration dynamic attributes")
        render_instance_configs()
        logger.info("Finished rendering instance configuration dynamic attributes")

    # Initialise any instances that have not been initialised yet.
    # For applicable instances, this needs to be done before the main API can be queried,
    # or secrets can even be checked.
    for plugin_name, instance_name in state._execution_order:
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            logger.debug("Checking if the instance is initialised")
            try:
                is_initialized = manager.is_initialized(instance_config)
            except NotImplementedError:
                logger.debug("Initialisation is not required for this instance type")
                continue
            if is_initialized:
                logger.debug("Instance is initialised and ready for configuration updates")
            else:
                logger.info("Instance has not been initialised")
                logger.info("Initialising instance")
                manager.initialize(
                    (
                        plugin_name
                        if instance_name == "default"
                        else f"{plugin_name}.instances[{repr(instance_config)}]"
                    ),
                    instance_config,
                )
                logger.info("Finished initialising instance")

    # Load the secrets file if it exists, and initialise the secrets metadata.
    # If `use_plugins` is undefined, load using all plugins available
    # to preserve cached secrets metadata that isn't used.
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
                logger.info("Checking secrets")
                try:
                    try_instance_secrets = plugin_secrets[instance_name]
                except KeyError:
                    try_instance_secrets = None
                if try_instance_secrets and try_instance_secrets.test():
                    logger.info("Connection test successful using cached secrets")
                    plugin_secrets[instance_name] = try_instance_secrets
                else:
                    logger.info(
                        "Connection test failed using cached secrets (or not cached), "
                        "fetching secrets",
                    )
                    instance_secrets: SecretsPlugin = state.plugins[plugin_name].secrets.get(
                        instance_config,
                    )
                    if instance_secrets.test():
                        logger.info("Connection test successful using fetched secrets")
                        plugin_secrets[instance_name] = instance_secrets
                    else:
                        raise RunInstanceConnectionTestFailedError(
                            "Connection test failed using fetched secrets "
                            f"for instance '{instance_name}': {instance_secrets}",
                        )
                logger.info("Finished checking secrets")

    # Save the latest secrets file to disk.
    logger.info("Saving updated secrets file to '%s'", secrets_file_path)
    state.secrets.write(secrets_file_path)
    logger.info("Finished saving updated secrets file")

    # Update all instances in the determined execution order.
    logger.info("Updating configuration on remote instances")
    for plugin_name, instance_name in state._execution_order:
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            instance_secrets = getattr(state.secrets, plugin_name)[instance_name]
            logger.info("Fetching remote configuration to check if updates are required")
            remote_instance_config = manager.from_remote(instance_config, instance_secrets)
            logger.info("Finished fetching remote configuration")
            for config_type, config in (
                ("Local", instance_config),
                ("Remote", remote_instance_config),
            ):
                logger.debug("%s configuration:", config_type)
                for config_line in config.yaml(exclude_unset=True).splitlines():
                    logger.debug(indent(config_line, "  "))
            logger.info("Updating remote configuration")
            logger.info(
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
            logger.info("Finished updating remote configuration")
    logger.info("Finished updating configuration on remote instances")

    # After all configuration and resources have been created/updated on
    # the remote instances, make another pass and remove any unmanaged or
    # unused resources slated for deletion.
    # The execution order is the reverse of the normal order, to ensure
    # any resources on source instances that depend on resources on
    # target instances (via instance links) are removed first.
    logger.info("Deleting unmanaged/unused resources on remote instances")
    for plugin_name, instance_name in reversed(state._execution_order):
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            instance_secrets = getattr(state.secrets, plugin_name)[instance_name]
            logger.info("Refetching remote configuration to delete unused resources")
            remote_instance_config = manager.from_remote(instance_config, instance_secrets)
            logger.info("Finished refetching remote configuration")
            for config_type, config in (
                ("Local", instance_config),
                ("Remote", remote_instance_config),
            ):
                logger.debug("%s configuration:", config_type)
                for config_line in config.yaml(exclude_unset=True).splitlines():
                    logger.debug(indent(config_line, "  "))
            logger.info("Deleting unmanaged/unused resources on the remote instance")
            logger.info(
                (
                    "Unused resources successfully deleted"
                    if manager.delete_remote(
                        plugin_name,
                        instance_config,
                        instance_secrets,
                        remote_instance_config,
                    )
                    else "Remote configuration is clean"
                ),
            )
            logger.info("Finished deleting unmanaged/unused resources on the remote instance")
    logger.info("Finished deleting unmanaged/unused resources on remote instances")

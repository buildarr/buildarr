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
`buildarr test-config` CLI command.
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
from ..state import state
from ..trash import fetch_trash_metadata
from ..util import get_resolved_path
from . import cli
from .exceptions import TestConfigNoPluginsDefinedError

if TYPE_CHECKING:
    from typing import Set


logger = getLogger(__name__)


@cli.command(
    help=(
        "Test a Buildarr configuration file for correctness.\n\n"
        "This loads the configuration file and performs a number of checks on it. "
        "If all tests pass, the file is pretty much guaranteed to work properly "
        "in a Buildarr run, incorrect values for a remote instance notwithstanding.\n\n"
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
def test_config(config_path: Path, use_plugins: Set[str]) -> None:
    """
    `buildarr test-config` main routine.

    Args:
        config_path (Path): Configuration file to load.
        use_plugins (Set[str]): Plugins to load. If empty, use all plugins.
    """

    logger.info("Buildarr version %s (log level: %s)", __version__, get_log_level())
    plugin_strs = [f"{pn} ({state.plugins[pn].version})" for pn in sorted(state.plugins.keys())]
    logger.info(
        "Loaded plugins: %s",
        ", ".join(plugin_strs) if plugin_strs else "(no plugins found)",
    )
    logger.info("Testing configuration file: %s", str(config_path))

    # Load and validate the Buildarr configuration.
    try:
        load_config(path=config_path, use_plugins=use_plugins)
    except Exception:
        logger.error("Loading configuration: FAILED")
        raise
    else:
        logger.debug("Buildarr configuration:")
        for config_line in state.config.yaml(exclude_unset=True).splitlines():
            logger.debug(indent(config_line, "  "))
        logger.info("Loading configuration: PASSED")

    # Load the manager objects for the selected plugins.
    try:
        load_managers(use_plugins)
    except Exception:
        logger.error("Loading plugin managers: FAILED")
        raise
    else:
        logger.debug("Managers loaded for the following plugins:")
        for plugin_name in state.managers.keys():
            logger.debug("  - %s", plugin_name)
        logger.info("Loading plugin managers: PASSED")

    # Parse and validate the instance-specific configurations under each plugin.
    try:
        load_instance_configs(use_plugins)
    except Exception:
        logger.error("Loading instance configurations: FAILED")
        raise
    else:
        for plugin_name, instance_configs in state.instance_configs.items():
            for instance_name, instance_config in instance_configs.items():
                with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                    logger.debug("Instance configuration:")
                    for config_line in instance_config.yaml(exclude_unset=True).splitlines():
                        logger.debug(indent(config_line, "  "))
        logger.info("Loading instance configurations: PASSED")

    # Check if configuration was found for any selected plugins.
    if state.active_plugins:
        logger.debug("Running with plugins: %s", ", ".join(state.active_plugins))
        logger.info("Checking configured plugins: PASSED")
    else:
        logger.error("Checking configured plugins: FAILED")
        raise TestConfigNoPluginsDefinedError("No configuration defined for any selected plugins")

    # Resolve the instance dependencies fetched from the instance-specific configuration.
    try:
        resolve_instance_dependencies()
    except Exception:
        logger.error("Resolving instance dependencies: FAILED")
        raise
    else:
        logger.debug("Execution order:")
        for i, (plugin_name, instance_name) in enumerate(state._execution_order, 1):
            logger.debug("  %i. %s.instances[%s]", i, plugin_name, repr(instance_name))
        logger.info("Resolving instance dependencies: PASSED")

    # Check if any instances are configured to get metadata from TRaSH-Guides.
    uses_trash_metadata = False
    for plugin_name in state.active_plugins:
        for instance_config in state.instance_configs[plugin_name].values():
            if state.managers[plugin_name].uses_trash_metadata(instance_config):
                uses_trash_metadata = True
                break
        if uses_trash_metadata:
            break

    # Test rendering the instance configuration.
    # If the TRaSH-Guides metadata is required by the configuration, run the rendering
    # with the TRaSH-Guides metadata available.
    # If the configuration reports that TRaSH-Guides metadata is not required,
    # run the test without fetching it.
    if uses_trash_metadata:
        fetching_metadata = True
        try:
            logger.debug("Fetching TRaSH metadata")
            with fetch_trash_metadata():
                logger.debug("Finished fetching TRaSH metadata")
                logger.info("Fetching TRaSH-Guides metadata: PASSED")
                fetching_metadata = False
                try:
                    logger.debug("Rendering instance configuration dynamic attributes")
                    render_instance_configs()
                    logger.debug("Finished rendering instance configuration dynamic attributes")
                except Exception:
                    logger.error("Rendering instance configuration dynamic attributes: FAILED")
                    raise
                else:
                    logger.info("Rendering instance configuration dynamic attributes: PASSED")
        except Exception:
            if fetching_metadata:
                logger.error("Fetching TRaSH-Guides metadata: FAILED")
            raise
    else:
        logger.info("Fetching TRaSH-Guides metadata: SKIPPED (not required)")
        try:
            logger.debug("Rendering instance configuration dynamic attributes")
            render_instance_configs()
            logger.debug("Finished rendering instance configuration dynamic attributes")
        except Exception:
            logger.error("Rendering instance configuration dynamic attributes: FAILED")
            raise
        else:
            logger.info("Rendering instance configuration dynamic attributes: PASSED")
    for plugin_name, instance_configs in state.instance_configs.items():
        for instance_name, instance_config in instance_configs.items():
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                if state.managers[plugin_name].uses_trash_metadata(instance_config):
                    logger.debug("Rendered instance configuration:")
                    for config_line in instance_config.yaml(exclude_unset=True).splitlines():
                        logger.debug(indent(config_line, "  "))

    # If we get to this point, this configuration is pretty much guaranteed to be valid.
    # Incorrect values for a remote application instance notwithstanding, it should
    # work properly in a real Buildarr run.
    logger.info("Configuration test successful.")

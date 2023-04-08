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
`buildarr compose` CLI command.
"""


from __future__ import annotations

from ipaddress import ip_address
from logging import getLogger
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING, cast

import click
import yaml

from .. import __version__
from ..config import load_config, load_instance_configs, resolve_instance_dependencies
from ..logging import get_log_level
from ..manager import load_managers
from ..state import state
from ..util import get_resolved_path
from . import cli
from .exceptions import (
    ComposeInvalidHostnameError,
    ComposeNoPluginsDefinedError,
    ComposeNotSupportedError,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Set


logger = getLogger(__name__)


@cli.command(
    help=(
        "Generate a Docker Compose file from a Buildarr configuration.\n\n"
        "This reads instance configurations from a Buildarr configuration file, "
        "generates a Docker Compose file that could be used to bootstrap the instances, "
        "and outputs the file to standard output.\n\n"
        "There are a few additional limitations on the instance configurations: "
        "instance hostnames must not be set to IP addresses, and all instances "
        "must have unique hostnames, unless the `--ignore-hostnames' option "
        "is set.\n\n"
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
@click.option(
    "-V",
    "--compose-version",
    "compose_version",
    metavar="VERSION",
    type=str,
    default="3.7",
    help="Version of the generated Docker Compose file. Default is `3.7'.",
)
@click.option(
    "-r",
    "--restart",
    "compose_restart",
    type=click.Choice(["always", "unless-stopped", "on-failure", "no"], case_sensitive=False),
    default="always",
    help="Restart policy for services. Default is `always'.",
)
@click.option(
    "-H",
    "--ignore-hostnames",
    "ignore_hostnames",
    is_flag=True,
    default=False,
    help=(
        "Ignore defined hostnames on instances, "
        "and automatically generate unique hostnames when creating the compose file. "
        "Note that the hostnames will no longer match the Buildarr configuration file."
    ),
)
def compose(
    config_path: Path,
    use_plugins: Set[str],
    compose_version: str,
    compose_restart: str,
    ignore_hostnames: bool,
) -> None:
    """
    `buildarr compose` main routine.

    Args:
        config_path (Path): Configuration file to load.
        use_plugins (Set[str]): Plugins to load. If empty, use all plugins.
    """

    logger.debug("Buildarr version %s (log level: %s)", __version__, get_log_level())
    plugin_strs = [f"{pn} ({state.plugins[pn].version})" for pn in sorted(state.plugins.keys())]
    logger.debug(
        "Loaded plugins: %s",
        ", ".join(plugin_strs) if plugin_strs else "(no plugins found)",
    )
    logger.debug(
        "Creating Docker Compose file from configuration file: %s",
        str(config_path),
    )

    logger.debug("Loading configuration file '%s'", config_path)
    load_config(path=config_path, use_plugins=use_plugins)
    logger.debug("Finished loading configuration file")
    logger.debug("Buildarr configuration:")
    for config_line in state.config.yaml(exclude_unset=True).splitlines():
        logger.debug(indent(config_line, "  "))

    logger.debug("Loading plugin managers")
    load_managers(use_plugins)
    logger.debug("Finished loading plugin managers")
    logger.debug("Managers loaded for the following plugins:")
    for plugin_name in state.managers.keys():
        logger.debug("  - %s", plugin_name)

    logger.debug("Loading instance configurations")
    load_instance_configs(use_plugins)
    logger.debug("Finished loading instance configurations")
    for plugin_name, instance_configs in state.instance_configs.items():
        for instance_name, instance_config in instance_configs.items():
            with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
                logger.debug("Instance configuration:")
                for config_line in instance_config.yaml(exclude_unset=True).splitlines():
                    logger.debug(indent(config_line, "  "))

    if not state.active_plugins:
        raise ComposeNoPluginsDefinedError("No loaded plugins configured in Buildarr")

    logger.debug("Resolving instance dependencies")
    resolve_instance_dependencies()
    logger.debug("Finished resolving instance dependencies")
    logger.debug("Execution order:")
    for i, (plugin_name, instance_name) in enumerate(state._execution_order, 1):
        logger.debug("  %i. %s.instances[%s]", i, plugin_name, repr(instance_name))

    compose_obj: Dict[str, Any] = {"version": compose_version, "services": {}}
    hostnames: Dict[str, str] = {}
    volumes: Set[str] = set()

    for plugin_name, instance_name in state._execution_order:
        manager = state.managers[plugin_name]
        instance_config = state.instance_configs[plugin_name][instance_name]
        with state._with_context(plugin_name=plugin_name, instance_name=instance_name):
            service_name = f"{plugin_name}_{instance_name}"
            logger.debug("Generating Docker Compose configuration for service '%s'", service_name)
            hostname = cast(
                str,
                service_name.replace("_", "-") if ignore_hostnames else instance_config.hostname,
            )
            logger.debug("Validating service hostname '%s'", hostname)
            try:
                ip_address(hostname)  # type: ignore[arg-type]
                raise ComposeInvalidHostnameError(
                    f"Invalid hostname '{hostname}' for {plugin_name} instance '{instance_name}': "
                    "Expected hostname, got IP address",
                )
            except ValueError:
                pass
            if hostname == "localhost":
                raise ComposeInvalidHostnameError(
                    f"Invalid hostname '{hostname}' for {plugin_name} instance '{instance_name}': "
                    "Hostname must not be localhost for Docker Compose services",
                )
            if hostname in hostnames:
                raise ComposeInvalidHostnameError(
                    f"Invalid hostname '{hostname}' for {plugin_name} instance '{instance_name}': "
                    f"Hostname already used by service '{hostnames[hostname]}'",
                )
            hostnames[hostname] = service_name
            logger.debug("Finished validating service hostname")
            try:
                logger.debug("Generating service-specific configuration")
                service: Dict[str, Any] = {
                    **manager.to_compose_service(
                        instance_config=instance_config,
                        compose_version=compose_version,
                        service_name=service_name,
                    ),
                    "hostname": hostname,
                    "restart": compose_restart,
                }
                logger.debug("Finished generating service-specific configuration")
            except NotImplementedError:
                raise ComposeNotSupportedError(
                    f"Plugin '{plugin_name}' does not support Docker Compose "
                    "service generation from instance configurations",
                ) from None
            if (plugin_name, instance_name) in state._instance_dependencies:
                depends_on: Set[str] = set()
                logger.debug("Generating service dependencies")
                for target_plugin, target_instance in state._instance_dependencies[
                    (plugin_name, instance_name)
                ]:
                    target_service = f"{target_plugin}_{target_instance}"
                    logger.debug("Adding dependency to service '%s'", target_service)
                    depends_on.add(target_service)
                service["depends_on"] = list(depends_on)
                logger.debug("Finished generating service dependencies")
            # TODO: Handle more types of volume definitions
            # (e.g. volume lists, modern-style mount definitions).
            for volume_name in service.get("volumes", {}).keys():
                if "/" not in volume_name and "\\" not in volume_name:
                    logger.debug(
                        "Adding named volume '%s' to the list of internal volumes",
                        volume_name,
                    )
                    volumes.add(volume_name)
                else:
                    logger.debug(
                        (
                            "Volume '%s' determined to likely be a bind mount, "
                            "not adding to the list of internal volumes"
                        ),
                        volume_name,
                    )
            compose_obj["services"][service_name] = service
            logger.debug("Finished generating Docker Compose service configuration")

    logger.debug("Generating Docker Compose configuration for service 'buildarr'")
    compose_obj["services"]["buildarr"] = {
        "image": f"{state.config.buildarr.docker_image_uri}:{__version__}",
        "command": ["daemon", f"/config/{state.config_files[0].name}"],
        "volumes": [
            {"type": "bind", "source": str(state.config_files[0].parent), "target": "/config"},
        ],
        "restart": compose_restart,
        "depends_on": [
            f"{plugin_name}_{instance_name}"
            for plugin_name, instance_name in state._execution_order
        ],
    }
    logger.debug("Finished generating Docker Compose configuration for service 'buildarr'")

    if volumes:
        compose_obj["volumes"] = list(volumes)

    click.echo(yaml.safe_dump(compose_obj, explicit_start=True, sort_keys=False))

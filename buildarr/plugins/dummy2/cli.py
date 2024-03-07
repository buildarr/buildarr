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
Dummy2 plugin CLI commands.
"""

from __future__ import annotations

import functools

from getpass import getpass
from urllib.parse import urlparse

import click
import click_params  # type: ignore[import]

from .config import Dummy2InstanceConfig
from .manager import Dummy2Manager
from .secrets import Dummy2Secrets

HOSTNAME_PORT_TUPLE_LENGTH = 2


@click.group(help="Dummy2 instance ad-hoc commands.")
def dummy2():
    """
    Dummy2 instance ad-hoc commands.
    """

    pass


@dummy2.command(
    help=(
        "Dump configuration from a remote Dummy2 instance.\n\n"
        "The configuration is dumped to standard output in Buildarr-compatible YAML format."
    ),
)
@click.argument("url", type=click_params.URL)
@click.option(
    "-k",
    "--api-key",
    "api_key",
    metavar="API-KEY",
    default=functools.partial(getpass, "Dummy2 instance API key: "),
    help="API key of the Dummy2 instance. The user will be prompted if undefined.",
)
def dump_config(url: str, api_key: str) -> int:
    """
    Dump configuration from a remote Dummy2 instance.
    The configuration is dumped to standard output in Buildarr-compatible YAML format.
    """

    # Parse the specified instance URL to get its constituent components.
    url_obj = urlparse(url)
    protocol = url_obj.scheme
    hostname_port = url_obj.netloc.split(":", 1)
    hostname = hostname_port[0]
    port = (
        int(hostname_port[1])
        if len(hostname_port) == HOSTNAME_PORT_TUPLE_LENGTH
        else (443 if protocol == "https" else 80)
    )

    # Create a default configuration object for the Dummy2 instance,
    # storing the connection information.
    dummy2_config = Dummy2InstanceConfig(hostname=hostname, port=port, protocol=protocol)

    # Generate the secrets metadata for the Dummy2 instance.
    dummy2_secrets = Dummy2Secrets(
        hostname=hostname,
        port=port,
        protocol=protocol,
        api_key=api_key,
    )

    # Pull the remote Dummy2 instance configuration, and create the configuration object.
    dummy2_config = Dummy2Manager().from_remote(
        instance_config=dummy2_config,
        secrets=dummy2_secrets,
    )

    # Serialise the Dummy2 instance configuration into YAML, and write it to standard output.
    click.echo(dummy2_config.yaml())

    return 0

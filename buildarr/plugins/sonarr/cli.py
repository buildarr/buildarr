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
Sonarr plugin CLI commands.
"""


from __future__ import annotations

import functools

from getpass import getpass
from urllib.parse import urlparse

import click
import click_params  # type: ignore[import]

from .config import SonarrInstanceConfig
from .manager import SonarrManager
from .secrets import SonarrSecrets

HOSTNAME_PORT_TUPLE_LENGTH = 2


@click.group(help="Sonarr instance ad-hoc commands.")
def sonarr():
    """
    Sonarr instance ad-hoc commands.
    """

    pass


@sonarr.command(
    help=(
        "Dump configuration from a remote Sonarr instance.\n\n"
        "The configuration is dumped to standard output in Buildarr-compatible YAML format."
    ),
)
@click.argument("url", type=click_params.URL)
@click.option(
    "-k",
    "--api-key",
    "api_key",
    metavar="API-KEY",
    default=functools.partial(getpass, "Sonarr instance API key: "),
    help="API key of the Sonarr instance. The user will be prompted if undefined.",
)
def dump_config(url: str, api_key: str) -> int:
    """
    Dump configuration from a remote Sonarr instance.
    The configuration is dumped to standard output in Buildarr-compatible YAML format.
    """

    url_obj = urlparse(url)
    protocol = url_obj.scheme
    hostname_port = url_obj.netloc.split(":", 1)
    hostname = hostname_port[0]
    port = (
        int(hostname_port[1])
        if len(hostname_port) == HOSTNAME_PORT_TUPLE_LENGTH
        else (443 if protocol == "https" else 80)
    )

    click.echo(
        SonarrManager()
        .from_remote(
            instance_config=SonarrInstanceConfig(hostname=hostname, port=port, protocol=protocol),
            secrets=SonarrSecrets(
                hostname=hostname,
                port=port,
                protocol=protocol,
                api_key=api_key,
            ),
        )
        .yaml(exclude_unset=True),
    )

    return 0

# Copyright (C) 2024 Callum Dickinson
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
Dummy plugin CLI commands.
"""

from __future__ import annotations

import functools

from getpass import getpass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import click

from .config import DummyInstanceConfig
from .manager import DummyManager
from .secrets import DummySecrets

if TYPE_CHECKING:
    from urllib.parse import ParseResult as Url

HOSTNAME_PORT_TUPLE_LENGTH = 2


@click.group(help="Dummy instance ad-hoc commands.")
def dummy():
    """
    Dummy instance ad-hoc commands.
    """

    pass


@dummy.command(
    help=(
        "Dump configuration from a remote Dummy instance.\n\n"
        "The configuration is dumped to standard output in Buildarr-compatible YAML format."
    ),
)
@click.argument("url", type=urlparse)
@click.option(
    "-k",
    "--api-key",
    "api_key",
    metavar="API-KEY",
    default=functools.partial(
        getpass,
        "Dummy instance API key (or leave blank to auto-fetch): ",
    ),
    help="API key of the Dummy instance. The user will be prompted if undefined.",
)
def dump_config(url: Url, api_key: str) -> int:
    """
    Dump configuration from a remote Dummy instance.
    The configuration is dumped to standard output in Buildarr-compatible YAML format.
    """

    protocol = url.scheme
    hostname_port = url.netloc.split(":", 1)
    hostname = hostname_port[0]
    port = (
        int(hostname_port[1])
        if len(hostname_port) == HOSTNAME_PORT_TUPLE_LENGTH
        else (443 if protocol == "https" else 80)
    )
    url_base = url.path

    instance_config = DummyInstanceConfig(
        **{  # type: ignore[arg-type]
            "hostname": hostname,
            "port": port,
            "protocol": protocol,
            "url_base": url_base,
        },
    )

    click.echo(
        (
            DummyManager()
            .from_remote(
                instance_config=instance_config,
                secrets=DummySecrets.get_from_url(
                    hostname=hostname,
                    port=port,
                    protocol=protocol,
                    url_base=url_base,
                    api_key=api_key if api_key else None,
                ),
            )
            .model_dump_yaml(exclude_unset=True)
        ),
        nl=False,
    )

    return 0

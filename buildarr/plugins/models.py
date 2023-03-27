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
Buildarr plugin models.
"""


from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Type

    from click import Group as ClickGroup

    from ..config import ConfigPlugin
    from ..manager import ManagerPlugin
    from ..secrets import SecretsPlugin


class Plugin:
    """
    Buildarr plugin definition.

    To create a Buildarr plugin, set the appropriate
    plugin classes as class attributes to an implementation of this class.

    ```python
    from buildarr.plugins import Plugin
    from buildarr_example.cli import example
    from buildarr_example.config import ExampleConfig
    from buildarr_example.secrets import ExampleSecrets

    class ExamplePlugin(Plugin):
        cli = example
        config = ExampleConfig
        secrets = ExampleSecrets
    ```

    Then, set this class as the entry point for the plugin in your
    Python package configuration.

    Setuptools `setup.py` entry point definition example:
    ```python
    from setuptools import setup

    setup(
        # ...,
        entry_points={
            "buildarr.plugins": [
                "example = buildarr_example.plugin:ExamplePlugin",
            ],
        },
    )
    ```

    Setuptools `setup.cfg` entry point definition example:
    ```ini
    [options.entry_points]
    buildarr.plugins =
        example = buildarr_example.plugin:ExamplePlugin
    ```

    Setuptools `pyproject.toml` entry point definition example:
    ```toml
    [project.entry-points."buildarr.plugins"]
    "example" = "buildarr_example.plugin:ExamplePlugin"
    ```

    Poetry plugin definition example:
    ```toml
    [tool.poetry.plugins."buildarr.plugins"]
    "example" = "buildarr_example.plugin:ExamplePlugin"
    ```
    """

    cli: Optional[ClickGroup] = None
    """
    CLI command group for the plugin.

    This attribute is optional.

    If you would like to add custom commands for your plugin to the Buildarr CLI,
    create a `@click.group` function with the commands defined, and set this attribute
    to the group function.
    """

    config: Type[ConfigPlugin]
    """
    Configuration model for the plugin.

    Buildarr uses this to parse configuration for the plugin defined in the Buildarr
    configuration file. Most of the actual methods for interacting with the configuration
    and remote instances will also be defined in the model structure.
    """

    manager: Type[ManagerPlugin]
    """
    Manager class for the plugin.

    Buildarr instantiates an object of this class without any arguments, and
    runs operations on configurations and secrets metadata through the methods
    defined in this class.
    """

    secrets: Type[SecretsPlugin]
    """
    Secrets metadata model for the plugin.

    Buildarr uses this to parse and create secrets metadata objects that the plugin can use.
    """

    version: str
    """
    The version of the plugin package.

    Gets output to the Buildarr logs so the user knows what version of the plugin
    is installed.
    """

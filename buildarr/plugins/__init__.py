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
Buildarr plugin specification.
"""


from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type

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

    cli: ClickGroup
    config: Type[ConfigPlugin]
    manager: Type[ManagerPlugin]
    secrets: Type[SecretsPlugin]

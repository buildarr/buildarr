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
Sonarr plugin tags settings configuration.
"""


from __future__ import annotations

from typing import Dict, List, cast

from buildarr.config import ConfigBase, NonEmptyStr
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_get, api_post


class SonarrTagsSettingsConfig(ConfigBase):
    """
    Tags are used to associate media files with certain resources (e.g. release profiles).

    ```yaml
    sonarr:
      settings:
        tags:
          definitions:
            - "example1"
            - "example2"
    ```

    To be able to use those tags in Buildarr, they need to be defined
    in this configuration section.
    """

    delete_unused: bool = False
    """
    Delete tags that are not used by any resource in Buildarr.

    Note that tags not being used in Buildarr are not necessarily
    unused by Sonarr, so be careful about when to use this option.

    Sonarr appears to periodically clean up unused tags,
    so in most cases there is no need to enable this option.
    """

    definitions: List[NonEmptyStr] = []
    """
    Define tags that are used within Buildarr here.

    If they are not defined here, you may get errors resulting from non-existent
    tags from either Buildarr or Sonarr.
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrTagsSettingsConfig:
        return cls(
            definitions=[
                tag["label"] for tag in api_get(cast(SonarrSecrets, secrets), "/api/v3/tag")
            ],
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrTagsSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        # This only does creations and updates.
        # Deletes (and empty tag list prints) are done AFTER all other modifications are made.
        # TODO: Implement tag deletions.
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        current_tags: Dict[str, int] = {
            tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")
        }
        if self.definitions:
            for i, tag in enumerate(self.definitions):
                if tag in current_tags:
                    plugin_logger.debug("%s.definitions[%i]: %s (exists)", tree, i, repr(tag))
                else:
                    plugin_logger.info("%s.definitions[%i]: %s -> (created)", tree, i, repr(tag))
                    api_post(sonarr_secrets, "/api/v3/tag", {"label": tag})
                    changed = True
        return changed

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
Sonarr plugin quality settings configuration object.
"""


from __future__ import annotations

import json

from pathlib import Path
from typing import Dict, Optional, cast

from pydantic import Field
from typing_extensions import Annotated

from buildarr.config import ConfigBase, NonEmptyStr, TrashID
from buildarr.config.exceptions import ConfigTrashIDNotFoundError
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_get, api_put


class QualityDefinition(ConfigBase):
    """
    Manually set quality definitions can have the following parameters.
    """

    title: Optional[NonEmptyStr] = None
    """
    The name of the quality in the GUI.

    If unset, set to an empty string or `None`, it will always be set to the
    name of the quality itself. (e.g. For the `Bluray-480p` quality, the GUI title
    will also be `Bluray-480p`)
    """

    # max: None -> no limit
    # TODO: min must be at least 1 less than max
    min: float = Field(..., ge=0, le=399)
    """
    The minimum Megabytes per Minute (MB/min) a quality can have.
    Must be set at least 1MB/min lower than `max`.
    """

    # Note: No 'pref' field like in Radarr until V4

    max: Optional[Annotated[float, Field(ge=1, lt=400)]]
    """
    The maximum Megabytes per Minute (MB/min) a quality can have.
    Must be set at least 1MB/min higher than `min`.

    If set to `None`, the maximum bit rate will be unlimited.
    """


class SonarrQualitySettingsConfig(ConfigBase):
    """
    Quality definitions are used to set the permitted bit rates for each quality level.

    These can either be set manually within Buildarr, or pre-made profiles can be
    imported from TRaSH-Guides.

    ```yaml
    sonarr:
      settings:
        quality:
          trash_id: "bef99584217af744e404ed44a33af589" # series
          definitions:
            Bluray-480p: # "Quality" column name (not "Title")
              min: 2
              max: 100
            # Add additional override quality definitions here
    ```

    Quality definition profiles retrieved from TRaSH-Guides are automatically
    kept up to date by Buildarr, with the latest values being pushed to Sonarr
    on an update run.

    For more information, refer to the guides from
    [WikiArr](https://wiki.servarr.com/sonarr/settings#quality-1)
    and [TRaSH-Guides](https://trash-guides.info/Sonarr/Sonarr-Quality-Settings-File-Size/).
    """

    # When defined, all explicitly defined quality definitions override the Trash version.
    trash_id: Optional[TrashID] = None
    """
    Trash ID of the TRaSH-Guides quality definition profile to load default values from.

    If there is an update in the profile, the quality definitions will be updated accordingly.
    """

    definitions: Dict[str, QualityDefinition] = {}
    """
    Explicitly set quality definitions here.

    The key of the definition is the "Quality" column of the Quality Definitions page
    in Sonarr, **not** "Title".

    If `trash_id` is set, any values set here will override the default values provided
    from the TRaSH-Guides quality definition profile.

    If `trash_id` is not set, only explicitly defined quality definitions are managed,
    and quality definitions not set within Buildarr are left unmodified.
    """

    def render_trash_metadata(self, sonarr_metadata_dir: Path) -> SonarrQualitySettingsConfig:
        if not self.trash_id:
            return self
        for quality_file in (sonarr_metadata_dir / "quality-size").iterdir():
            with quality_file.open() as f:
                quality_json = json.load(f)
                if cast(str, quality_json["trash_id"]).lower() == self.trash_id:
                    definitions: Dict[str, QualityDefinition] = {}
                    #
                    for definition_json in quality_json["qualities"]:
                        definitions[definition_json["quality"]] = QualityDefinition(
                            title=None,
                            min=definition_json["min"],
                            max=None if definition_json["max"] >= 400 else definition_json["max"],
                        )
                    #
                    for name, definition in self.definitions.items():
                        definitions[name] = definition
                    return SonarrQualitySettingsConfig(definitions=definitions)
        raise ConfigTrashIDNotFoundError(
            f"Unable to find Sonarr quality definition file with trash ID '{self.trash_id}'",
        )

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrQualitySettingsConfig:
        return SonarrQualitySettingsConfig(
            definitions={
                definition["quality"]["name"]: QualityDefinition(
                    title=(
                        definition["title"]
                        if definition["title"] != definition["quality"]["name"]
                        else None
                    ),
                    min=definition["minSize"],
                    max=definition.get("maxSize", None),
                )
                for definition in api_get(
                    cast(SonarrSecrets, secrets),
                    "/api/v3/qualitydefinition",
                )
            }
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrQualitySettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        definition_ids: Dict[str, int] = {
            definition_json["quality"]["name"]: definition_json["id"]
            for definition_json in api_get(sonarr_secrets, "/api/v3/qualitydefinition")
        }
        for definition_name, local_definition in self.definitions.items():
            updated, remote_attrs = local_definition.get_update_remote_attrs(
                f"{tree}[{repr(definition_name)}]",
                cast(SonarrQualitySettingsConfig, remote).definitions[definition_name],
                [
                    ("title", "title", {"encoder": lambda v: v or definition_name}),
                    ("min", "minSize", {}),
                    ("max", "maxSize", {}),
                ],
            )
            if updated:
                api_put(
                    sonarr_secrets,
                    f"/api/v3/qualitydefinition/{definition_ids[definition_name]}",
                    remote_attrs,
                )
                changed = True
        return changed

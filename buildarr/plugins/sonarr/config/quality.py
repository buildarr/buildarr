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
from typing import Any, Dict, Mapping, Optional, cast

from pydantic import Field, validator
from typing_extensions import Self

from buildarr.config import ConfigBase
from buildarr.config.exceptions import ConfigTrashIDNotFoundError
from buildarr.types import TrashID

from ..api import api_get, api_put
from ..secrets import SonarrSecrets
from .types import SonarrConfigBase

QUALITYDEFINITION_MAX = 400
"""
The upper bound for the maximum quality allowed in a quality definition.
"""


class QualityDefinition(SonarrConfigBase):
    """
    Manually set quality definitions can have the following parameters.
    """

    title: Optional[str] = None
    """
    The name of the quality in the GUI.

    If unset, set to an empty string or `None`, it will always be set to the
    name of the quality itself. (e.g. For the `Bluray-480p` quality, the GUI title
    will also be `Bluray-480p`)
    """

    min: float = Field(..., ge=0, le=QUALITYDEFINITION_MAX - 1)
    """
    The minimum Megabytes per Minute (MB/min) a quality can have.
    Must be set at least 1MB/min lower than `max`.

    The minimum value is `0`, and the maximum value is `399`.
    """

    # Note: No 'pref' field like in Radarr until V4

    max: Optional[float] = Field(..., ge=1, le=QUALITYDEFINITION_MAX)
    """
    The maximum Megabytes per Minute (MB/min) a quality can have.
    Must be set at least 1MB/min higher than `min`.

    If set to `None` or `400`, the maximum bit rate will be unlimited.

    If not set to `None`, the minimum value is `1`, and the maximum value is `400`.
    """

    @validator("max")
    def validate_min_max(
        cls,
        value: Optional[float],
        values: Mapping[str, Any],
    ) -> Optional[float]:
        quality_max = value
        quality_max_val = (
            min(quality_max, QUALITYDEFINITION_MAX)
            if quality_max is not None
            else QUALITYDEFINITION_MAX
        )
        try:
            quality_min: float = values["min"]
            if quality_max_val - quality_min < 1:
                raise ValueError(
                    f"'max' ({quality_max_val}) is not "
                    f"at least 1 greater than 'min' ({quality_min})",
                )
        except KeyError:
            # `min` only doesn't exist when it failed type validation.
            # If it doesn't exist, skip validation that uses it.
            pass
        if quality_max_val >= QUALITYDEFINITION_MAX:
            return None
        return quality_max


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

    @property
    def uses_trash_metadata(self) -> bool:
        """
        A flag determining whether or not this configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return bool(self.trash_id)

    def _render_trash_metadata(self, trash_metadata_dir: Path) -> None:
        """
        Render configuration attributes obtained from TRaSH-Guides, in-place.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.
        """
        if not self.trash_id:
            return
        for quality_file in (
            trash_metadata_dir / "docs" / "json" / "sonarr" / "quality-size"
        ).iterdir():
            with quality_file.open() as f:
                quality_json = json.load(f)
                if cast(str, quality_json["trash_id"]).lower() == self.trash_id:
                    for definition_json in quality_json["qualities"]:
                        definition_name = definition_json["quality"]
                        if definition_name not in self.definitions:
                            self.definitions[definition_name] = QualityDefinition(
                                title=None,
                                min=definition_json["min"],
                                max=definition_json["max"],
                            )
                    return
        raise ConfigTrashIDNotFoundError(
            f"Unable to find Sonarr quality definition file with trash ID '{self.trash_id}'",
        )

    @classmethod
    def from_remote(cls, secrets: SonarrSecrets) -> Self:
        return cls(
            definitions={
                definition_json["quality"]["name"]: QualityDefinition(
                    title=(
                        definition_json["title"]
                        if definition_json["title"] != definition_json["quality"]["name"]
                        else None
                    ),
                    min=definition_json["minSize"],
                    max=definition_json.get("maxSize", None),
                )
                for definition_json in api_get(secrets, "/api/v3/qualitydefinition")
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        changed = False
        remote_definitions_json = {
            definition_json["id"]: definition_json
            for definition_json in api_get(secrets, "/api/v3/qualitydefinition")
        }
        definition_ids: Dict[str, int] = {
            definition_json["quality"]["name"]: definition_id
            for definition_id, definition_json in remote_definitions_json.items()
        }
        for definition_name, local_definition in self.definitions.items():
            updated, remote_attrs = local_definition.get_update_remote_attrs(
                tree=f"{tree}[{repr(definition_name)}]",
                remote=remote.definitions[definition_name],
                remote_map=[
                    ("title", "title", {"encoder": lambda v: v or definition_name}),
                    ("min", "minSize", {}),
                    ("max", "maxSize", {}),
                ],
            )
            if updated:
                definition_id = definition_ids[definition_name]
                api_put(
                    secrets,
                    f"/api/v3/qualitydefinition/{definition_id}",
                    {**remote_definitions_json[definition_id], **remote_attrs},
                )
                changed = True
        return changed

    # Tell Pydantic to validate in-place assignments of attributes.
    # This ensures that any validators that parse attributes to consistent values run.
    class Config(SonarrConfigBase.Config):
        validate_assignment = True

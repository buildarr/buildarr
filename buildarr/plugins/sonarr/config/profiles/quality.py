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
Sonarr plugin quality profile configuration.
"""


from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union, cast

from pydantic import Field, root_validator
from typing_extensions import Annotated, Self

from buildarr.config import ConfigBase, NonEmptyStr, RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ...secrets import SonarrSecrets
from ...util import api_delete, api_get, api_post, api_put


class QualityGroup(ConfigBase):
    """
    Quality group.

    Allows groups of quality definitions to be given the same prorioty in qualtity profiles.
    """

    name: NonEmptyStr
    members: List[NonEmptyStr] = Field(..., min_items=1)

    def encode(self, group_id: int, quality_definitions: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "id": group_id,
            "name": self.name,
            "allowed": True,
            "items": [
                _encode_quality_str(quality_definitions, member, True) for member in self.members
            ],
        }


class QualityProfile(ConfigBase):
    """
    The main things to consider when creating a quality profile are
    what quality settings to enable, and how to prioritise each.

    ```yaml
    ...
      quality_profiles:
        SDTV:
          upgrades_allowed: true
          upgrade_until: "Bluray-1080p"
          qualities:
          - "Bluray-480p"
          - "DVD"
          - name: "WEB 480p"
            members:
              - "WEBDL-480p"
              - "WEBRip-480p"
          - "SDTV"
    ```

    In Buildarr, the quality listed first (at the top) is given the highest priority, with
    subsequent qualities given lower priority. Qualities not explicitly defined are
    disabled (not downloaded).

    Sonarr supports grouping multiple qualities together to give them the same priority.
    In Buildarr, these are expressed by giving a `name` to the group, and listing the qualities
    under the `members` attribute.

    For more insight into reasonable values for quality profiles,
    refer to these guides from [WikiArr](https://wiki.servarr.com/sonarr/settings#quality-profiles)
    and TRaSH-Guides ([WEB-DL](https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx/),
    [anime](https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx-Anime/)).
    """

    upgrades_allowed: bool = False
    """
    Enable automatic upgrading if a higher quality version of the media file becomes available.

    If disabled, media files will not be upgraded after they have been downloaded.
    """

    upgrade_until: Optional[NonEmptyStr] = None
    """
    The maximum quality level to upgrade an episode to.
    For a quality group, specify the group name.

    Once this quality is reached Sonarr will no longer download episodes.

    This attribute is required if `upgrades_allowed` is set to `True`.
    """

    qualities: Annotated[List[Union[str, QualityGroup]], Field(min_items=1)]
    """
    The qualities to enable downloading episodes for. The order determines the priority
    (highest priority first, lowest priority last).

    Individual qualities can be specified using the name (e.g. `Bluray-480p`).

    Qualities can also be grouped together in a structure to give them the same
    priority level. A new version of the episode will not be downloaded if it is
    at least one of the qualities listed in the group, until a higher quality
    version is found.

    ```yaml
    ...
      qualities:
        - name: "WEB 480p"
          members:
            - "WEBDL-480p"
            - "WEBRip-480p"
    ```

    At least one quality must be specified.
    """

    # TODO: validate that there are no duplicate quality definitions in qualities

    @root_validator
    def required_if_upgrades_allowed(cls, values):
        if values["upgrades_allowed"] and not values["upgrade_until"]:
            raise ValueError("'upgrade_until' is required if 'upgrades_allowed' is True")
        return values

    @classmethod
    def _get_remote_map(
        cls,
        quality_definitions: Mapping[str, Mapping[str, Any]] = {},
        group_ids: Mapping[str, int] = {},
    ) -> List[RemoteMapEntry]:
        return [
            ("upgrades_allowed", "upgradeAllowed", {}),
            (
                "upgrade_until",
                "cutoff",
                {
                    "root_decoder": lambda vs: next(
                        (
                            quality["name"]
                            for quality in ((q if "id" in q else q["quality"]) for q in vs["items"])
                            if quality["id"] == vs["cutoff"]
                        ),
                        None,
                    ),
                    "encoder": lambda v: (
                        (group_ids[v] if v in group_ids else quality_definitions[v]["id"])
                        if v is not None
                        else 0
                    ),
                },
            ),
            (
                "qualities",
                "items",
                {
                    "decoder": lambda v: _decode_qualities(v),
                    "encoder": lambda v: _encode_qualities(quality_definitions, group_ids, v),
                },
            ),
        ]

    @classmethod
    def _from_remote(cls, remote_attrs: Mapping[str, Any]) -> Self:
        return cls(**cls.get_local_attrs(cls._get_remote_map(), remote_attrs))

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        profile_name: str,
        quality_definitions: Mapping[str, Mapping[str, Any]],
    ) -> None:
        group_ids: Dict[str, int] = {
            quality_group.name: (1000 + i)
            for i, quality_group in enumerate(
                [q for q in self.qualities if isinstance(q, QualityGroup)],
                1,
            )
        }
        api_post(
            sonarr_secrets,
            "/api/v3/qualityprofile",
            {
                "name": profile_name,
                **self.get_create_remote_attrs(
                    tree,
                    self._get_remote_map(quality_definitions, group_ids),
                ),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: QualityProfile,
        profile_id: int,
        profile_name: str,
        quality_definitions: Mapping[str, Mapping[str, Any]],
    ) -> bool:
        group_ids: Dict[str, int] = {
            quality_group.name: (1000 + i)
            for i, quality_group in enumerate(
                [q for q in self.qualities if isinstance(q, QualityGroup)],
                1,
            )
        }
        changed, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_remote_map(quality_definitions, group_ids),
            check_unmanaged=True,
            set_unchanged=True,
        )
        if changed:
            api_put(
                sonarr_secrets,
                f"/api/v3/qualityprofile/{profile_id}",
                {"id": profile_id, "name": profile_name, **remote_attrs},
            )
            return True
        return False

    def _delete_remote(self, tree: str, sonarr_secrets: SonarrSecrets, profile_id: int) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets, f"/api/v3/qualityprofile/{profile_id}")


class SonarrQualityProfilesSettingsConfig(ConfigBase):
    """
    Configuration parameters for controlling how Buildarr handles quality profiles.
    """

    delete_unmanaged: bool = False
    """
    Automatically delete quality profiles not defined in Buildarr.

    Out of the box Sonarr provides some pre-defined quality profiles.
    Take care when enabling this option, as those will also be deleted.
    """

    definitions: Dict[str, QualityProfile] = {}
    """
    Define quality profiles to configure on Sonarr here.

    If there are no quality profiles defined and `delete_unmanaged` is `False`,
    Buildarr will not modify existing quality profiles, but if `delete_unmanaged` is `True`,
    **Buildarr will delete all existing profiles. Be careful when using `delete_unmanaged`.**
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrQualityProfilesSettingsConfig:
        return SonarrQualityProfilesSettingsConfig(
            definitions={
                profile["name"]: QualityProfile._from_remote(profile)
                for profile in api_get(cast(SonarrSecrets, secrets), "/api/v3/qualityprofile")
            }
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrQualityProfilesSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        #
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        #
        profile_ids: Dict[str, int] = {
            profile_json["name"]: profile_json["id"]
            for profile_json in api_get(sonarr_secrets, "/api/v3/qualityprofile")
        }
        quality_definitions: Dict[str, Dict[str, Any]] = {
            quality_json["title"]: quality_json["quality"]
            for quality_json in sorted(
                api_get(sonarr_secrets, "/api/v3/qualitydefinition"),
                key=lambda q: q["weight"],
                reverse=True,
            )
        }
        #
        for profile_name, profile in self.definitions.items():
            profile_tree = f"{tree}.definitions[{repr(profile_name)}]"
            #
            if profile_name not in remote.definitions:
                profile._create_remote(
                    profile_tree,
                    sonarr_secrets,
                    profile_name,
                    quality_definitions,
                )
                changed = True
            #
            else:
                if profile._update_remote(
                    profile_tree,
                    sonarr_secrets,
                    remote.definitions[profile_name],
                    profile_ids[profile_name],
                    profile_name,
                    quality_definitions,
                ):
                    changed = True
        #
        for profile_name, profile in remote.definitions.items():
            if profile_name not in self.definitions:
                profile_tree = f"{tree}.definitions[{repr(profile_name)}]"
                if self.delete_unmanaged:
                    profile._delete_remote(
                        profile_tree,
                        sonarr_secrets,
                        profile_ids[profile_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", profile_tree)
        #
        return changed


def _decode_qualities(value: Sequence[Mapping[str, Any]]) -> List[Union[str, QualityGroup]]:
    return [
        (
            QualityGroup(
                name=quality["name"],
                members=[member["quality"]["name"] for member in quality["items"]],
            )
            if quality["items"]
            else quality["quality"]["name"]
        )
        for quality in reversed(value)
        if quality["allowed"]
    ]


def _encode_qualities(
    quality_definitions: Mapping[str, Mapping[str, Any]],
    group_ids: Mapping[str, int],
    qualities: List[Union[str, QualityGroup]],
) -> List[Dict[str, Any]]:
    qualities_json: List[Dict[str, Any]] = []
    enabled_qualities: Set[str] = set()

    for quality in qualities:
        if isinstance(quality, QualityGroup):
            qualities_json.append(quality.encode(group_ids[quality.name], quality_definitions))
            for member in quality.members:
                enabled_qualities.add(member)
        else:
            qualities_json.append(_encode_quality_str(quality_definitions, quality, True))
            enabled_qualities.add(quality)

    for quality_name in quality_definitions.keys():
        if quality_name not in enabled_qualities:
            qualities_json.append(_encode_quality_str(quality_definitions, quality_name, False))

    return list(reversed(qualities_json))


def _encode_quality_str(
    quality_definitions: Mapping[str, Mapping[str, Any]],
    quality_name: str,
    allowed: bool,
) -> Dict[str, Any]:
    return {"quality": quality_definitions[quality_name], "items": [], "allowed": allowed}

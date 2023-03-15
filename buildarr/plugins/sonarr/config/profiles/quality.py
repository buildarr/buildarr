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

from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union

from pydantic import Field, root_validator
from typing_extensions import Annotated, Self

from buildarr.config import RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.types import NonEmptyStr

from ...api import api_delete, api_get, api_post, api_put
from ...secrets import SonarrSecrets
from ..types import SonarrConfigBase


class QualityGroup(SonarrConfigBase):
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


class QualityProfile(SonarrConfigBase):
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

    qualities: Annotated[List[Union[NonEmptyStr, QualityGroup]], Field(min_items=1)]
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

    @root_validator
    def validate_qualityprofile(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the quality profile against required constraints.

        Args:
            values (Dict[str, Any]): Parsed values

        Raises:
            ValueError: If `upgrade_until` is not defined when `upgrades_allowed` is `True`
            ValueError: If duplicate allowed quality entries are defined
            ValueError: If `upgrade_until` is set to a disabled quality name

        Returns:
            Validated/modified values
        """
        try:
            upgrades_allowed: bool = values["upgrades_allowed"]
            upgrade_until: str = values["upgrade_until"]
            qualities: Sequence[Union[str, QualityGroup]] = values["qualities"]
        except KeyError as err:
            raise ValueError(
                f"required attribute undefined or unable to be parsed: {str(err)}",
            ) from None
        # `upgrade_until` checks.
        if upgrades_allowed:
            if not upgrade_until:
                raise ValueError("'upgrade_until' is required if 'upgrades_allowed' is True")
            for quality in qualities:
                quality_name = quality.name if isinstance(quality, QualityGroup) else quality
                if upgrade_until == quality_name:
                    break
            else:
                raise ValueError("'upgrade_until' must be set to an allowed quality name")
        else:
            # If `upgrades_allowed` is `False`, set `upgrade_until` to `None`
            # to make sure Buildarr ignores whatever it is currently set to
            # on the remote instance.
            values["upgrade_until"] = None
        # `qualities` checks.
        quality_names: Set[str] = set()
        for quality in qualities:
            quality_name = quality.name if isinstance(quality, QualityGroup) else quality
            if quality_name in quality_names:
                raise ValueError(f"Duplicate entries of quality name '{quality_name}' exist")
            else:
                quality_names.add(quality_name)
        # Return validated/modified values.
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
                    "root_decoder": lambda vs: cls._upgrade_until_decoder(
                        items=vs["items"],
                        cutoff=vs["cutoff"],
                    ),
                    "root_encoder": lambda vs: cls._upgrade_until_encoder(
                        quality_definitions=quality_definitions,
                        group_ids=group_ids,
                        qualities=vs.qualities,
                        upgrade_until=vs.upgrade_until,
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
    def _upgrade_until_decoder(
        cls,
        items: Sequence[Mapping[str, Any]],
        cutoff: int,
    ) -> str:
        for quality_item in items:
            quality: Mapping[str, Any] = (
                quality_item  # Quality group
                if "id" in quality_item
                else quality_item["quality"]  # Quality definition (singular)
            )
            if quality["id"] == cutoff:
                return quality["name"]
        raise RuntimeError(
            "Inconsistent Sonarr instance state: "
            f"'cutoff' quality ID {cutoff} not found in 'items': {items}",
        )

    @classmethod
    def _upgrade_until_encoder(
        cls,
        quality_definitions: Mapping[str, Mapping[str, Any]],
        group_ids: Mapping[str, int],
        qualities: Sequence[Union[str, QualityGroup]],
        upgrade_until: Optional[str],
    ) -> int:
        if not upgrade_until:
            quality = qualities[0]
            return (
                group_ids[quality.name]
                if isinstance(quality, QualityGroup)
                else quality_definitions[quality]["id"]
            )
        return (
            group_ids[upgrade_until]
            if upgrade_until in group_ids
            else quality_definitions[upgrade_until]["id"]
        )

    @classmethod
    def _from_remote(cls, remote_attrs: Mapping[str, Any]) -> Self:
        return cls(**cls.get_local_attrs(cls._get_remote_map(), remote_attrs))

    def _create_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
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
            secrets,
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
        secrets: SonarrSecrets,
        remote: Self,
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
                secrets,
                f"/api/v3/qualityprofile/{profile_id}",
                {"id": profile_id, "name": profile_name, **remote_attrs},
            )
            return True
        return False

    def _delete_remote(self, tree: str, secrets: SonarrSecrets, profile_id: int) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(secrets, f"/api/v3/qualityprofile/{profile_id}")


class SonarrQualityProfilesSettingsConfig(SonarrConfigBase):
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
    def from_remote(cls, secrets: SonarrSecrets) -> Self:
        return cls(
            definitions={
                profile["name"]: QualityProfile._from_remote(profile)
                for profile in api_get(secrets, "/api/v3/qualityprofile")
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        #
        changed = False
        #
        profile_ids: Dict[str, int] = {
            profile_json["name"]: profile_json["id"]
            for profile_json in api_get(secrets, "/api/v3/qualityprofile")
        }
        quality_definitions: Dict[str, Dict[str, Any]] = {
            quality_json["title"]: quality_json["quality"]
            for quality_json in sorted(
                api_get(secrets, "/api/v3/qualitydefinition"),
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
                    tree=profile_tree,
                    secrets=secrets,
                    profile_name=profile_name,
                    quality_definitions=quality_definitions,
                )
                changed = True
            #
            elif profile._update_remote(
                tree=profile_tree,
                secrets=secrets,
                remote=remote.definitions[profile_name],
                profile_id=profile_ids[profile_name],
                profile_name=profile_name,
                quality_definitions=quality_definitions,
            ):
                changed = True
        #
        for profile_name, profile in remote.definitions.items():
            if profile_name not in self.definitions:
                profile_tree = f"{tree}.definitions[{repr(profile_name)}]"
                if self.delete_unmanaged:
                    profile._delete_remote(
                        tree=profile_tree,
                        secrets=secrets,
                        profile_id=profile_ids[profile_name],
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

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
Sonarr plugin delay profile configuration.
"""


from __future__ import annotations

from typing import Any, Dict, List, Mapping, Set, cast

from pydantic import Field
from typing_extensions import Self

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ...secrets import SonarrSecrets
from ...util import api_delete, api_get, api_post, api_put


class PreferredProtocol(ConfigEnum):
    """
    Enumeration for enabled and preferred protocols in delay profiles.
    """

    usenet_prefer = 0
    torrent_prefer = 1
    usenet_only = 2
    torrent_only = 3

    @classmethod
    def get_from_params(
        cls,
        usenet_enabled: bool,
        torrent_enabled: bool,
        preferred_protocol: str,
    ) -> PreferredProtocol:
        return {
            (True, True, "usenet"): PreferredProtocol.usenet_prefer,
            (True, True, "unknown"): PreferredProtocol.usenet_prefer,
            (True, True, "torrent"): PreferredProtocol.torrent_prefer,
            (True, False, "usenet"): PreferredProtocol.usenet_only,
            (True, False, "unknown"): PreferredProtocol.usenet_only,
            (False, True, "torrent"): PreferredProtocol.torrent_only,
            (False, True, "unknown"): PreferredProtocol.torrent_only,
        }[(usenet_enabled, torrent_enabled, preferred_protocol)]

    @property
    def usenet_enabled(self) -> bool:
        return self in (
            PreferredProtocol.usenet_only,
            PreferredProtocol.usenet_prefer,
            PreferredProtocol.torrent_prefer,
        )

    @property
    def torrent_enabled(self) -> bool:
        return self in (
            PreferredProtocol.torrent_only,
            PreferredProtocol.torrent_prefer,
            PreferredProtocol.usenet_prefer,
        )

    @property
    def preferred_protocol(self) -> str:
        return (
            "torrent"
            if self in (PreferredProtocol.torrent_prefer, PreferredProtocol.torrent_only)
            else "usenet"
        )


class DelayProfile(ConfigBase):
    """
    Delay profiles are defined as an ordered list of objects.

    A preferred protocol must be specified for all delay profiles.
    Tags must be defined on all except the final profile (the default profile),
    where tags must not be defined.

    ```yaml
    ...
      delay_profiles:
        definitions:
          # Ordered in priority, highest priority first.
          - preferred_protocol: "usenet-prefer" # Required
            usenet_delay: 0
            torrent_delay: 0
            bypass_if_highest_quality: true
            tags:
              - "tv-shows"
            # Add additional delay profiles here as needed.
            ...
            # Default delay profile goes last, and MUST be defined
            # if you have defined any other delay profiles.
            - preferred_protocol: "torrent-prefer" # Required
              usenet_delay: 1440
              torrent_delay: 1440
              bypass_if_highest_quality: false
              # Tags will be ignored for default delay profile.
    ```
    """

    preferred_protocol: PreferredProtocol
    """
    Choose which protocol(s) to use and which one is preferred
    when choosing between otherwise equal releases.

    Values:

    * `usenet-prefer` (Prefer Usenet)
    * `torrent-prefer` (Prefer Torrent)
    * `usenet-only` (Only Usenet)
    * `torrent-only` (Only Torrent)
    """

    usenet_delay: int = Field(0, ge=0)  # minutes
    """
    Delay (in minutes) to wait before grabbing a release from Usenet.
    """

    torrent_delay: int = Field(0, ge=0)  # minutes
    """
    Delay (in minutes) to wait before grabbing a torrent.
    """

    bypass_if_highest_quality: bool = False
    """
    Bypass the delay if a found release is the highest quality allowed
    in the quality profile that applies to it, and uses the preferred protocol
    as defined in this delay profile.
    """

    tags: Set[NonEmptyStr] = set()
    """
    Tags to assign to this delay profile.

    This delay profile will apply to series with at least one matching tag.
    """

    @classmethod
    def _get_remote_map(
        cls,
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return [
            (
                "preferred_protocol",
                "enableUsenet",
                {
                    "root_decoder": lambda vs: PreferredProtocol.get_from_params(
                        usenet_enabled=vs["enableUsenet"],
                        torrent_enabled=vs["enableTorrent"],
                        preferred_protocol=vs["preferredProtocol"],
                    ),
                    "encoder": lambda v: v.usenet_enabled,
                },
            ),
            (
                "preferred_protocol",
                "enableTorrent",
                {
                    "root_decoder": lambda vs: PreferredProtocol.get_from_params(
                        usenet_enabled=vs["enableUsenet"],
                        torrent_enabled=vs["enableTorrent"],
                        preferred_protocol=vs["preferredProtocol"],
                    ),
                    "encoder": lambda v: v.torrent_enabled,
                },
            ),
            (
                "preferred_protocol",
                "preferredProtocol",
                {
                    "root_decoder": lambda vs: PreferredProtocol.get_from_params(
                        usenet_enabled=vs["enableUsenet"],
                        torrent_enabled=vs["enableTorrent"],
                        preferred_protocol=vs["preferredProtocol"],
                    ),
                    "encoder": lambda v: v.preferred_protocol,
                },
            ),
            ("usenet_delay", "usenetDelay", {}),
            ("torrent_delay", "torrentDelay", {}),
            ("bypass_if_highest_quality", "bypassIfHighestQuality", {}),
            (
                "tags",
                "tags",
                {
                    "decoder": lambda v: set(
                        (tag for tag, tag_id in tag_ids.items() if tag_id in v),
                    ),
                    "encoder": lambda v: sorted(tag_ids[tag] for tag in v),
                },
            ),
        ]

    @classmethod
    def _from_remote(
        cls,
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> Self:
        return cls(
            **cls.get_local_attrs(cls._get_remote_map(tag_ids), remote_attrs),
        )

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        tag_ids: Mapping[str, int],
        order: int,
    ) -> None:
        api_post(
            sonarr_secrets,
            "/api/v3/delayprofile",
            {
                "order": order,
                **self.get_create_remote_attrs(tree, self._get_remote_map(tag_ids)),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: DelayProfile,
        tag_ids: Mapping[str, int],
        profile_id: int,
        order: int,
    ) -> bool:
        changed, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_remote_map(tag_ids),
            check_unmanaged=True,
            set_unchanged=True,
        )
        if changed:
            api_put(
                sonarr_secrets,
                f"/api/v3/delayprofile/{profile_id}",
                {"id": profile_id, "order": order, **remote_attrs},
            )
            return True
        return False

    def _delete_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        profile_id: int,
    ) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets, f"/api/v3/delayprofile/{profile_id}")


class SonarrDelayProfilesSettingsConfig(ConfigBase):
    """
    Configuration parameters for controlling how Buildarr handles delay profiles.
    """

    delete_unmanaged = False
    """
    Controls how Buildarr manages existing delay profiles in Sonarr when no delay profiles
    are defined in Buildarr.

    When set to `True` and there are no delay profiles defined in Buildarr,
    delete all delay profiles except the default delay profile (which can't be deleted).

    When set to `False` and there are no delay profiles defined in Buildarr,
    do not modify the existing delay profiles in Sonarr at all.

    Due to the unique way delay profiles are structured, when they are defined in Buildarr,
    they always overwrite the existing delay profiles on the remote Sonarr instance
    and configure it exactly as laid out in Buildarr, irrespective of this value.

    If unsure, leave this value set to `False`.
    """

    definitions: List[DelayProfile] = []
    """
    Define delay profiles to configure on Sonarr here.

    The final delay profile in the list is assumed to be the default delay profile.
    """

    # TODO: add a validator that checks that all definitions except the last one have tags,
    #       and the last one has no tags.

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrDelayProfilesSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        profiles: List[Dict[str, Any]] = sorted(
            api_get(sonarr_secrets, "/api/v3/delayprofile"),
            key=lambda p: p["order"],
            reverse=True,
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(profile["tags"] for profile in profiles)
            else {}
        )
        return SonarrDelayProfilesSettingsConfig(
            definitions=[DelayProfile._from_remote(tag_ids, profile) for profile in profiles],
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrDelayProfilesSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        if not self.delete_unmanaged and "definitions" not in self.__fields_set__:
            # TODO: printcurrent delay profile structure
            if remote.definitions:
                plugin_logger.debug("%s.definitions: [...] (unmanaged)", tree)
            else:
                plugin_logger.debug("%s.definitions: [] (unmanaged)", tree)
            return False
        #
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        #
        profile_ids: Dict[int, int] = {
            profile["order"]: profile["id"]
            for profile in api_get(sonarr_secrets, "/api/v3/delayprofile")
        }
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(profile.tags for profile in self.definitions)
            or any(profile.tags for profile in remote.definitions)
            else {}
        )
        #
        # Order: update already exist -> create/delete
        for order in range(max(len(self.definitions), len(remote.definitions))):
            local_index = len(self.definitions) - 1 - order
            remote_index = len(remote.definitions) - 1 - order
            # If the index is negative, then there are more delay profiles
            # on the remote than there are defined in the local configuration.
            # Delete those extra delay profiles from the remote.
            if local_index < 0:
                remote.definitions[remote_index]._delete_remote(
                    f"{tree}.definitions[{local_index}]",
                    sonarr_secrets,
                    profile_id=profile_ids[order],
                )
                changed = True
            # If the current index (order) is one that does not exist on the remote, create it.
            elif remote_index < 0:
                self.definitions[local_index]._create_remote(
                    f"{tree}.definitions[{local_index}]",
                    sonarr_secrets,
                    tag_ids=tag_ids,
                    order=order,
                )
                changed = True
            # If none of the above conditions checked out, then the current index exists
            # in both the local configuration and the remote.
            # Check and update those delay profiles.
            else:
                if self.definitions[local_index]._update_remote(
                    f"{tree}.definitions[{local_index}]",
                    sonarr_secrets,
                    remote.definitions[remote_index],
                    tag_ids=tag_ids,
                    profile_id=profile_ids[order],
                    order=order,
                ):
                    changed = True
        #
        return changed

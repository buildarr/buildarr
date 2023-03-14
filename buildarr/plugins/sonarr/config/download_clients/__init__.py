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
Sonarr plugin download client settings.
"""


from __future__ import annotations

from typing import Dict, List, Mapping, Union

from pydantic import Field
from typing_extensions import Annotated, Self

from buildarr.config import RemoteMapEntry
from buildarr.logging import plugin_logger

from ...api import api_get, api_put
from ...secrets import SonarrSecrets
from ..types import SonarrConfigBase
from .download_clients import (
    DOWNLOADCLIENT_TYPE_MAP,
    Aria2DownloadClient,
    DelugeDownloadClient,
    DownloadstationTorrentDownloadClient,
    DownloadstationUsenetDownloadClient,
    FloodDownloadClient,
    HadoukenDownloadClient,
    NzbgetDownloadClient,
    NzbvortexDownloadClient,
    PneumaticDownloadClient,
    QbittorrentDownloadClient,
    RtorrentDownloadClient,
    SabnzbdDownloadClient,
    TorrentBlackholeDownloadClient,
    TransmissionDownloadClient,
    UsenetBlackholeDownloadClient,
    UtorrentDownloadClient,
    VuzeDownloadClient,
)
from .remote_path_mappings import SonarrRemotePathMappingsSettingsConfig

DownloadClientType = Union[
    DownloadstationUsenetDownloadClient,
    NzbgetDownloadClient,
    NzbvortexDownloadClient,
    PneumaticDownloadClient,
    SabnzbdDownloadClient,
    UsenetBlackholeDownloadClient,
    Aria2DownloadClient,
    DelugeDownloadClient,
    DownloadstationTorrentDownloadClient,
    FloodDownloadClient,
    HadoukenDownloadClient,
    QbittorrentDownloadClient,
    RtorrentDownloadClient,
    TorrentBlackholeDownloadClient,
    TransmissionDownloadClient,
    UtorrentDownloadClient,
    VuzeDownloadClient,
]


class SonarrDownloadClientsSettingsConfig(SonarrConfigBase):
    """
    Download clients retrieve media files being tracked by Sonarr,
    and store them in a location Sonarr can access to manage the
    downloaded files.

    Download clients that use Usenet or BitTorrent can be configured,
    as well as remote path mappings and other related options.

    ```yaml
    ---

    sonarr:
      settings:
        download_clients:
          enable_completed_download_handling: true
          redownload_failed: true
          delete_unmanaged: true
          definitions:
            Transmission:
              type: "transmission"
              host: "transmission"
              port: 9091
            ...
          remote_path_mappings:
            definitions:
              - host: "transmission"
                remote_path: "/remote/path"
                local_path: "/local/path"
              ...
    ```
    """

    enable_completed_download_handling: bool = True
    """
    Automatically import completed downloads from download clients.
    """

    redownload_failed: bool = True
    """
    Automatically search for and attempt to download a different release.
    """

    delete_unmanaged: bool = False
    """
    Automatically delete download clients not defined in Buildarr.
    """

    definitions: Dict[str, Annotated[DownloadClientType, Field(discriminator="type")]] = {}
    """
    Download client definitions, for connecting with external media downloaders.
    """

    remote_path_mappings = SonarrRemotePathMappingsSettingsConfig()
    """
    Configuration for mapping paths on download client hosts to their counterparts
    on this Sonarr instance.

    For more information, refer to "Configuring remote path mappings".
    """

    _remote_map: List[RemoteMapEntry] = [
        ("enable_completed_download_handling", "enableCompletedDownloadHandling", {}),
        ("redownload_failed", "autoRedownloadFailed", {}),
    ]

    @classmethod
    def from_remote(cls, secrets: SonarrSecrets) -> Self:
        downloadclient_config = api_get(secrets, "/api/v3/config/downloadclient")
        downloadclients = api_get(secrets, "/api/v3/downloadclient")
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(secrets, "/api/v3/tag")}
            if any(downloadclient["tags"] for downloadclient in downloadclients)
            else {}
        )
        return cls(
            **cls.get_local_attrs(cls._remote_map, downloadclient_config),
            definitions={
                dc["name"]: DOWNLOADCLIENT_TYPE_MAP[dc["implementation"]]._from_remote(
                    tag_ids=tag_ids,
                    remote_attrs=dc,
                )
                for dc in downloadclients
            },
            remote_path_mappings=SonarrRemotePathMappingsSettingsConfig._from_remote(
                secrets=secrets,
            ),
        )

    def update_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        # Update download client-related configuration options.
        config_updated, config_remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._remote_map,
            check_unmanaged=check_unmanaged,
        )
        if config_updated:
            remote_config = api_get(secrets, "/api/v3/config/downloadclient")
            api_put(
                secrets,
                f"/api/v3/config/downloadclient/{remote_config['id']}",
                {
                    "id": remote_config["id"],
                    "downloadClientWorkingFolders": remote_config["downloadClientWorkingFolders"],
                    **config_remote_attrs,
                },
            )
        # Update download clients.
        definitions_updated = self._update_remote_definitions(
            tree=f"{tree}.definitions",
            secrets=secrets,
            local=self.definitions,
            remote=remote.definitions,
            check_unmanaged=check_unmanaged,
        )
        # Update remote path mappings.
        rpms_updated = self.remote_path_mappings._update_remote(
            tree=f"{tree}.remote_path_mappings",
            secrets=secrets,
            remote=remote.remote_path_mappings,
        )
        #
        return any([config_updated, definitions_updated, rpms_updated])

    def _update_remote_definitions(
        self,
        tree: str,
        secrets: SonarrSecrets,
        local: Mapping[str, DownloadClientType],
        remote: Mapping[str, DownloadClientType],
        check_unmanaged: bool,
    ) -> bool:
        changed = False
        downloadclient_ids: Dict[str, int] = {
            downloadclient_json["name"]: downloadclient_json["id"]
            for downloadclient_json in api_get(secrets, "/api/v3/downloadclient")
        }
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(secrets, "/api/v3/tag")}
            if any(downloadclient.tags for downloadclient in local.values())
            or any(downloadclient.tags for downloadclient in remote.values())
            else {}
        )
        # Create download clients that don't exist yet on the remote,
        # and update in-place ones that do.
        for downloadclient_name, downloadclient in local.items():
            downloadclient_tree = f"{tree}[{repr(downloadclient_name)}]"
            if downloadclient_name not in remote:
                downloadclient._create_remote(
                    tree=downloadclient_tree,
                    secrets=secrets,
                    tag_ids=tag_ids,
                    downloadclient_name=downloadclient_name,
                )
                changed = True
            elif downloadclient._update_remote(
                tree=downloadclient_tree,
                secrets=secrets,
                remote=remote[downloadclient_name],  # type: ignore[arg-type]
                tag_ids=tag_ids,
                downloadclient_id=downloadclient_ids[downloadclient_name],
                downloadclient_name=downloadclient_name,
            ):
                changed = True
        # If `delete_unmanaged` is `True`, remove any download clients on the remote
        # that aren't managed by Buildarr.
        # Otherwise, just log them.
        for downloadclient_name, downloadclient in remote.items():
            if downloadclient_name not in local:
                downloadclient_tree = f"{tree}[{repr(downloadclient_name)}]"
                if self.delete_unmanaged:
                    downloadclient._delete_remote(
                        tree=downloadclient_tree,
                        secrets=secrets,
                        downloadclient_id=downloadclient_ids[downloadclient_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", downloadclient_tree)
        # Return the resource changed status.
        return changed

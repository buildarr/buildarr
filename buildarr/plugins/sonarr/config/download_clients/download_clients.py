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
Sonarr plugin download client definition.
"""


from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, Optional, Set, Tuple, Type

from typing_extensions import Self

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, Password, Port, RemoteMapEntry
from buildarr.logging import plugin_logger

from ...secrets import SonarrSecrets
from ...util import api_delete, api_post, api_put


class NzbgetPriority(ConfigEnum):
    """
    NZBGet media priority.

    Values:

    * `verylow` (Very Low)
    * `low` (Low)
    * `normal` (Normal)
    * `high` (High)
    * `veryhigh` (Very High)
    * `force` (Force)
    """

    verylow = -100
    low = -50
    normal = 0
    high = 50
    veryhigh = 100
    force = 900


class NzbvortexPriority(ConfigEnum):
    """
    NZBVortex media priority.

    Values:

    * `low` (Low)
    * `normal` (Normal)
    * `high` (High)
    """

    low = -1
    normal = 0
    high = 1


class SabnzbdPriority(ConfigEnum):
    """
    SABnzbd media priority.

    Values:

    * `default` (Default)
    * `paused` (Paused)
    * `low` (Low)
    * `normal` (Normal)
    * `high` (High)
    * `force` (Force)
    """

    default = -100
    paused = -2
    low = -1
    normal = 0
    high = 1
    force = 2


class DelugePriority(ConfigEnum):
    """
    Deluge queue priority.

    Values:

    * `last` (Last)
    * `first` (First)
    """

    last = 0
    first = 1


class FloodMediaTag(ConfigEnum):
    """
    Type of tag to set on media within Flood.

    Multiple can be specified at a time.

    Values:

    * `title-slug` (Title Slug)
    * `quality` (Quality)
    * `language` (Language)
    * `release-group` (Release Group)
    * `year` (Year)
    * `indexer` (Indexer)
    * `network` (Network)
    """

    title_slug = 0
    quality = 1
    language = 2
    release_group = 3
    year = 4
    indexer = 5
    network = 6


class QbittorrentPriority(ConfigEnum):
    """
    qBittorrent queue priority.

    Values:

    * `last` (Last)
    * `first` (First)
    """

    last = 0
    first = 1


class QbittorrentState(ConfigEnum):
    """
    qBittorrent initial state.

    Values:

    * `start` (Start)
    * `force-start` (Force Start)
    * `pause` (Pause)
    """

    start = 0
    force_start = 1
    pause = 2


class RtorrentPriority(ConfigEnum):
    """
    RTorrent media priority.

    Values:

    * `verylow` (Very Low)
    * `low` (Low)
    * `normal` (Normal)
    * `high` (High)
    """

    verylow = 0
    low = 1
    normal = 2
    high = 3


class TransmissionPriority(ConfigEnum):
    """
    Transmission queue priority.

    Values:

    * `last` (Last)
    * `first` (First)
    """

    last = 0
    first = 1


class UtorrentPriority(ConfigEnum):
    """
    uTorrent queue priority.

    Values:

    * `last` (Last)
    * `first` (First)
    """

    last = 0
    first = 1


class UtorrentState(ConfigEnum):
    """
    uTorrent initial state.

    Values:

    * `start` (Start)
    * `force-start` (Force Start)
    * `pause` (Pause)
    * `stop` (Stop)
    """

    start = 0
    force_start = 1
    pause = 2
    stop = 3


class DownloadClient(ConfigBase):
    """
    Download clients are defined using the following format.
    Here is an example of a Transmission download client being configured.

    ```yaml
    ---

    sonarr:
      settings:
        download_clients:
          definitions:
            Transmission: # Name of the download client
              type: "transmission" # Type of download client
              enable: true # Enable the download client in Sonarr
              host: "transmission"
              port: 9091
              category: "sonarr"
              # Define any other type-specific or global
              # download client attributes as needed.
    ```

    Every download client definition must have the correct `type` value defined,
    to tell Buildarr what type of download client to configure.
    The name of the download client definition is just a name, and has no meaning.

    `enable` can be set to `False` to keep the download client configured on Sonarr,
    but disabled so that it is inactive.

    The below attributes can be defined on any type of download client.
    """

    enable: bool = True
    """
    When `True`, this download client is active and Sonarr is able to send requests to it.
    """

    priority: int = 1
    """
    Download client priority.

    Clients with a lower value are prioritised.
    Round-robin is used for clients with the same priority.
    """

    remove_completed_downloads: bool = True
    """
    Remove completed downloads from the download client history.

    For torrents, this happens once seeding is complete.
    """

    remove_failed_downloads: bool = True
    """
    Remove failed downloads from the download client history. (Usenet clients only)
    """

    tags: Set[NonEmptyStr] = set()
    """
    Sonarr tags to assign to the download clients.
    Only media under those tags will be assigned to this client.

    If no tags are assigned, all media can use the client.
    """

    _implementation_name: str
    _implementation: str
    _config_contract: str
    _remote_map: List[RemoteMapEntry]

    @classmethod
    def _get_base_remote_map(cls, tag_ids: Mapping[str, int]) -> List[RemoteMapEntry]:
        return [
            ("enable", "enable", {}),
            ("priority", "priority", {}),
            ("remove_completed_downloads", "removeCompletedDownloads", {}),
            ("remove_failed_downloads", "removeFailedDownloads", {}),
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
        sonarr_secrets: SonarrSecrets,
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> Self:
        return cls(
            **cls.get_local_attrs(
                cls._get_base_remote_map(tag_ids) + cls._remote_map,
                remote_attrs,
            ),
        )

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        tag_ids: Mapping[str, int],
        downloadclient_name: str,
    ) -> None:
        api_post(
            sonarr_secrets,
            "/api/v3/downloadclient",
            {
                "name": downloadclient_name,
                "implementation": self._implementation,
                "implementationName": self._implementation_name,
                "configContract": self._config_contract,
                **self.get_create_remote_attrs(
                    tree,
                    self._get_base_remote_map(tag_ids) + self._remote_map,
                ),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: Self,
        tag_ids: Mapping[str, int],
        downloadclient_id: int,
        downloadclient_name: str,
    ) -> bool:
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_base_remote_map(tag_ids) + self._remote_map,
            set_unchanged=True,
            # TODO: Should we also enable check_unmanaged here?
        )
        if updated:
            api_put(
                sonarr_secrets,
                f"/api/v3/downloadclient/{downloadclient_id}",
                {
                    "id": downloadclient_id,
                    "name": downloadclient_name,
                    "implementation": self._implementation,
                    "implementationName": self._implementation_name,
                    "configContract": self._config_contract,
                    **remote_attrs,
                },
            )
            return True
        return False

    def _delete_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        downloadclient_id: int,
    ) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets, f"/api/v3/downloadclient/{downloadclient_id}")


class UsenetDownloadClient(DownloadClient):
    """
    Usenet-based download client.
    """

    pass


class TorrentDownloadClient(DownloadClient):
    """
    Torrent-based download client.
    """

    pass


class DownloadstationUsenetDownloadClient(UsenetDownloadClient):
    """
    Download client which uses Usenet via Download Station.
    """

    type: Literal["downloadstation-usenet"] = "downloadstation-usenet"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Download Station host name.
    """

    port: Port = 5000  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.
    Creates a `[category]` subdirectory in the output directory.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    directory: Optional[str] = None
    """
    Optional shared folder to put downloads into.

    Leave blank, set to `null` or undefined to use the default download client location.
    """

    _implementation_name: str = "Download Station"
    _implementation: str = "UsenetDownloadStation"
    _config_contract: str = "DownloadStationSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "category",
            "tvDirectory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class NzbgetDownloadClient(UsenetDownloadClient):
    """
    NZBGet download client.
    """

    type: Literal["nzbget"] = "nzbget"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    NZBGet host name.
    """

    port: Port = 5000  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the NZBGet url, e.g. `http://[host]:[port]/[url_base]/jsonrpc`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    recent_priority: NzbgetPriority = NzbgetPriority.normal
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: NzbgetPriority = NzbgetPriority.normal
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    add_paused: bool = False
    """
    Add media to the download client in the paused state.

    This option requires NZBGet version 16.0 or later.
    """

    _implementation_name: str = "NZBGet"
    _implementation: str = "Nzbget"
    _config_contract: str = "NzbgetSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("add_paused", "addPaused", {"is_field": True}),
    ]


class NzbvortexDownloadClient(UsenetDownloadClient):
    """
    NZBVortex download client.
    """

    type: Literal["nzbvortex"] = "nzbvortex"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    NZBVortex host name.
    """

    port: Port = 4321  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the NZBVortex url, e.g. `http://[host]:[port]/[url_base]/api`.
    """

    api_key: Password
    """
    API key to use to authenticate with the download client.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    recent_priority: NzbvortexPriority = NzbvortexPriority.normal
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: NzbvortexPriority = NzbvortexPriority.normal
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    _implementation_name: str = "NZBVortex"
    _implementation: str = "NzbVortex"
    _config_contract: str = "NzbVortexSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("api_key", "apiKey", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
    ]


class PneumaticDownloadClient(UsenetDownloadClient):
    """
    Download client for the Pneumatic NZB add-on for Kodi/XMBC.
    """

    type: Literal["pneumatic"] = "pneumatic"
    """
    Type value associated with this kind of download client.
    """

    nzb_folder: NonEmptyStr
    """
    Folder in which Sonarr will store `.nzb` files.

    This folder will need to be reachable from Kodi/XMBC.
    """

    strm_folder: NonEmptyStr
    """
    Folder from which `.strm` files will be imported by Drone.
    """

    _implementation_name: str = "Pneumatic"
    _implementation: str = "Pneumatic"
    _config_contract: str = "PneumaticSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("nzb_folder", "nzbFolder", {"is_field": True}),
        ("strm_folder", "strmFolder", {"is_field": True}),
    ]


class SabnzbdDownloadClient(UsenetDownloadClient):
    """
    SABnzbd download client.
    """

    type: Literal["sabnzbd"] = "sabnzbd"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    SABnzbd host name.
    """

    port: Port = 4321  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the SABnzbd URL, e.g. `http://[host]:[port]/[url_base]/api/`.
    """

    api_key: Password
    """
    API key to use to authenticate with the download client.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    recent_priority: SabnzbdPriority = SabnzbdPriority.default
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: SabnzbdPriority = SabnzbdPriority.default
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    _implementation_name: str = "SABnzbd"
    _implementation: str = "Sabnzbd"
    _config_contract: str = "SabnzbdSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("api_key", "apiKey", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
    ]


class UsenetBlackholeDownloadClient(UsenetDownloadClient):
    """
    Usenet Blackhole download client.
    """

    type: Literal["usenet-blackhole"] = "usenet-blackhole"
    """
    Type value associated with this kind of download client.
    """

    nzb_folder: NonEmptyStr
    """
    Folder in which Sonarr will store `.nzb` files.
    """

    watch_folder: NonEmptyStr
    """
    Folder from which Sonarr should import completed downloads.
    """

    _implementation_name: str = "Usenet Blackhole"
    _implementation: str = "UsenetBlackhole"
    _config_contract: str = "UsenetBlackholeSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("nzb_folder", "nzbFolder", {"is_field": True}),
        ("watch_folder", "watchFolder", {"is_field": True}),
    ]


class Aria2DownloadClient(TorrentDownloadClient):
    """
    Aria2 download client.
    """

    type: Literal["aria2"] = "aria2"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Aria2 host name.
    """

    port: Port = 6800  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    rpc_path: NonEmptyStr = "/rpc"  # type: ignore[assignment]
    """
    XML RPC path in the Aria2 client URL.
    """

    secret_token: Password
    """
    Secret token to use to authenticate with the download client.
    """

    _implementation_name: str = "Aria2"
    _implementation: str = "Aria2"
    _config_contract: str = "Aria2Settings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("rpc_path", "rpcPath", {"is_field": True}),
        ("secret_token", "secretToken", {"is_field": True}),
    ]


class DelugeDownloadClient(TorrentDownloadClient):
    """
    Deluge download client.
    """

    type: Literal["deluge"] = "deluge"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Deluge host name.
    """

    port: Port = 8112  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the Deluge JSON URL, e.g. `http://[host]:[port]/[url_base]/json`.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = "tv-sonarr"
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    postimport_category: Optional[str] = None
    """
    Category for Sonarr to set after it has imported the download.

    Sonarr will not remove torrents in that category even if seeding has finished.
    Leave blank, set to `null` or undefined to keep the same category.
    """

    recent_priority: DelugePriority = DelugePriority.last
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: DelugePriority = DelugePriority.last
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    _implementation_name: str = "Deluge"
    _implementation: str = "Deluge"
    _config_contract: str = "DelugeSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "postimport_category",
            "tvImportedCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
    ]


class DownloadstationTorrentDownloadClient(TorrentDownloadClient):
    """
    Download client which uses torrents via Download Station.
    """

    type: Literal["downloadstation-torrent"] = "downloadstation-torrent"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Download Station host name.
    """

    port: Port = 5000  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.
    Creates a `[category]` subdirectory in the output directory.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    directory: Optional[str] = None
    """
    Optional shared folder to put downloads into.

    Leave blank, set to `null` or undefined to use the default download client location.
    """

    _implementation_name: str = "Download Station"
    _implementation: str = "TorrentDownloadStation"
    _config_contract: str = "DownloadStationSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "category",
            "tvDirectory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class FloodDownloadClient(TorrentDownloadClient):
    """
    Flood download client.
    """

    type: Literal["flood"] = "flood"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Flood host name.
    """

    port: Port = 3000  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Optionally adds a prefix to Flood API, such as `[protocol]://[host]:[port]/[url_base]api`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    destination: Optional[str] = None
    """
    Manually specified download destination.
    """

    flood_tags: Set[NonEmptyStr] = {"sonarr"}  # type: ignore[arg-type]
    """
    Initial tags of a download within Flood.

    To be recognized, a download must have all initial tags.
    This avoids conflicts with unrelated downloads.
    """

    postimport_tags: Set[NonEmptyStr] = set()
    """
    Tags to append within Flood after a download has been imported into Sonarr.
    """

    additional_tags: Set[FloodMediaTag] = set()
    """
    Adds properties of media as tags within Flood.
    """

    start_on_add: bool = True
    """
    Immediately start download once the media has been added to the client.
    """

    _implementation_name: str = "Flood"
    _implementation: str = "Flood"
    _config_contract: str = "FloodSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "destination",
            "destination",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("flood_tags", "tags", {"is_field": True, "encoder": sorted}),
        ("postimport_tags", "postImportTags", {"is_field": True, "encoder": sorted}),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        (
            "additional_tags",
            "additionalTags",
            {
                "is_field": True,
                "decoder": lambda v: set(FloodMediaTag(t) for t in v),
                "encoder": lambda v: sorted(t.value for t in v),
            },
        ),
        ("start_on_add", "startOnAdd", {"is_field": True}),
    ]


class HadoukenDownloadClient(TorrentDownloadClient):
    """
    Hadouken download client.
    """

    type: Literal["hadouken"] = "hadouken"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    Hadouken host name.
    """

    port: Port = 7070  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the Hadouken url, e.g. `http://[host]:[port]/[url_base]/api`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: NonEmptyStr = "sonarr-tv"  # type: ignore[assignment]
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    _implementation_name: str = "Hadouken"
    _implementation: str = "Hadouken"
    _config_contract: str = "HadoukenSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        ("category", "category", {"is_field": True}),
    ]


class QbittorrentDownloadClient(TorrentDownloadClient):
    """
    qBittorrent download client.
    """

    type: Literal["qbittorrent"] = "qbittorrent"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    qBittorrent host name.
    """

    port: Port = 8080  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the qBittorrent URL, e.g. `http://[host]:[port]/[url_base]/api`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = "tv-sonarr"
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    postimport_category: Optional[str] = None
    """
    Category for Sonarr to set after it has imported the download.

    Sonarr will not remove torrents in that category even if seeding has finished.
    Leave blank, set to `null` or undefined to keep the same category.
    """

    recent_priority: QbittorrentPriority = QbittorrentPriority.last
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: QbittorrentPriority = QbittorrentPriority.last
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    initial_state: QbittorrentState = QbittorrentState.start
    """
    Initial state for torrents added to qBittorrent.

    Note that forced torrents do not abide by seed restrictions.
    """

    sequential_order: bool = False
    """
    Download files in sequential order.

    This option requires qBittorrent version 4.1.0 or later.
    """

    first_and_last_first: bool = False
    """
    Download first and last pieces of a file first.

    This option requires qBittorrent version 4.1.0 or later.
    """

    _implementation_name: str = "qBittorrent"
    _implementation: str = "QBittorrent"
    _config_contract: str = "QBittorrentSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "postimport_category",
            "tvImportedCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("initial_state", "initialState", {"is_field": True}),
        ("sequential_order", "sequentialOrder", {"is_field": True}),
        ("first_and_last_first", "firstAndLast", {"is_field": True}),
    ]


class RtorrentDownloadClient(TorrentDownloadClient):
    """
    RTorrent (ruTorrent) download client.
    """

    type: Literal["rtorrent", "rutorrent"] = "rtorrent"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    RTorrent host name.
    """

    port: Port = 8080  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: NonEmptyStr = "RPC2"  # type: ignore[assignment]
    """
    Path to the XMLRPC endpoint, e.g. `http(s)://[host]:[port]/[url_base]`.

    When using RTorrent this usually is `RPC2` or `plugins/rpc/rpc.php`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = "tv-sonarr"
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    postimport_category: Optional[str] = None
    """
    Category for Sonarr to set after it has imported the download.

    Sonarr will not remove torrents in that category even if seeding has finished.
    Leave blank, set to `null` or undefined to keep the same category.
    """

    directory: Optional[str] = None
    """
    Optional shared folder to put downloads into.

    Leave blank, set to `null` or undefined to use the default download client location.
    """

    recent_priority: RtorrentPriority = RtorrentPriority.normal
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: RtorrentPriority = RtorrentPriority.normal
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    add_stopped: bool = False
    """
    Enabling will add torrents and magnets to RTorrent in a stopped state.

    This may break magnet files.
    """

    _implementation_name: str = "rTorrent"
    _implementation: str = "RTorrent"
    _config_contract: str = "RTorrentSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("url_base", "urlBase", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "postimport_category",
            "tvImportedCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "directory",
            "tvDirectory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("add_stopped", "addStopped", {"is_field": True}),
    ]


class TorrentBlackholeDownloadClient(TorrentDownloadClient):
    """
    Torrent Blackhole download client.
    """

    type: Literal["torrent-blackhole"] = "torrent-blackhole"
    """
    Type value associated with this kind of download client.
    """

    torrent_folder: NonEmptyStr
    """
    Folder in which Sonarr will store `.torrent` files.
    """

    watch_folder: NonEmptyStr
    """
    Folder from which Sonarr should import completed downloads.
    """

    save_magnet_files: bool = False
    """
    Save the magnet link if no `.torrent` file is available.

    Only useful if the download client supports magnets saved to a file.
    """

    magnet_file_extension: NonEmptyStr = ".magnet"  # type: ignore[assignment]
    """
    Extension to use for magnet links.
    """

    read_only: bool = True
    """
    Instead of moving files, this will instruct Sonarr to copy or hard link
    (depending on settings/system configuration).
    """

    _implementation_name: str = "Torrent Blackhole"
    _implementation: str = "TorrentBlackhole"
    _config_contract: str = "TorrentBlackholeSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("url_base", "urlBase", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "postimport_category",
            "tvImportedCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "directory",
            "tvDirectory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("add_stopped", "addStopped", {"is_field": True}),
    ]


class TransmissionDownloadClientBase(TorrentDownloadClient):
    """
    Configuration options common to both Transmission and Vuze download clients:
    """

    host: NonEmptyStr
    """
    Transmission/Vuze host name.
    """

    port: Port = 9091  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: NonEmptyStr = "/transmission/"  # type: ignore[assignment]
    """
    Adds a prefix to the Transmission/Vuze RPC url, e.g.`http://[host]:[port][url_base]rpc`.

    This is set by default in most clients to `/transmission/`.
    """

    username: Optional[str] = None
    """
    User name to use when authenticating with the download client, if required.
    """

    password: Optional[Password] = None
    """
    Password to use to authenticate the download client user, if required.
    """

    category: Optional[str] = None
    """
    Associate media from Sonarr with a category.
    Creates a `[category]` subdirectory in the output directory.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    directory: Optional[str] = None
    """
    Optional shared folder to put downloads into.

    Leave blank, set to `null` or undefined to use the default download client location.
    """

    recent_priority: TransmissionPriority = TransmissionPriority.last
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: TransmissionPriority = TransmissionPriority.last
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    add_paused: bool = False
    """
    Add media to the download client in the Paused state.
    """

    _config_contract: str = "TransmissionSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("url_base", "urlBase", {"is_field": True}),
        (
            "username",
            "username",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("password", "password", {"is_field": True, "field_default": None}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "directory",
            "tvDirectory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("add_paused", "addPaused", {"is_field": True}),
    ]


class TransmissionDownloadClient(TransmissionDownloadClientBase):
    """
    Tramsmission download client.
    """

    type: Literal["transmission"] = "transmission"
    """
    Type value associated with this kind of download client.
    """

    _implementation_name: str = "Transmission"
    _implementation: str = "Transmission"


class VuzeDownloadClient(TransmissionDownloadClientBase):
    """
    Vuze download client.
    """

    type: Literal["vuze"] = "vuze"
    """
    Type value associated with this kind of download client.
    """

    _implementation_name: str = "Vuze"
    _implementation: str = "Vuze"


class UtorrentDownloadClient(TorrentDownloadClient):
    """
    uTorrent download client.
    """

    type: Literal["utorrent"] = "utorrent"
    """
    Type value associated with this kind of download client.
    """

    host: NonEmptyStr
    """
    uTorrent host name.
    """

    port: Port = 8080  # type: ignore[assignment]
    """
    Download client access port.
    """

    use_ssl: bool = False
    """
    Use a secure connection when connecting to the download client.
    """

    url_base: Optional[str] = None
    """
    Adds a prefix to the uTorrent URL, e.g. `http://[host]:[port]/[url_base]/api`.
    """

    username: NonEmptyStr
    """
    User name to use when authenticating with the download client.
    """

    password: Password
    """
    Password to use to authenticate the download client user.
    """

    category: Optional[str] = "tv-sonarr"
    """
    Associate media from Sonarr with a category.

    Adding a category specific to Sonarr avoids conflicts with unrelated non-Sonarr downloads.
    Using a category is optional, but strongly recommended.
    """

    postimport_category: Optional[str] = None
    """
    Category for Sonarr to set after it has imported the download.

    Sonarr will not remove torrents in that category even if seeding has finished.
    Leave blank, set to `null` or undefined to keep the same category.
    """

    recent_priority: UtorrentPriority = UtorrentPriority.last
    """
    Priority to use when grabbing episodes that aired within the last 14 days.
    """

    older_priority: UtorrentPriority = UtorrentPriority.last
    """
    Priority to use when grabbing episodes that aired over 14 days ago.
    """

    initial_state: UtorrentState = UtorrentState.start
    """
    Initial state for torrents added to uTorrent.
    """

    _implementation_name: str = "uTorrent"
    _implementation: str = "UTorrent"
    _config_contract: str = "UTorrentSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        (
            "url_base",
            "urlBase",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        (
            "category",
            "tvCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "postimport_category",
            "tvImportedCategory",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recent_priority", "recentTvPriority", {"is_field": True}),
        ("older_priority", "olderTvPriority", {"is_field": True}),
        ("initial_state", "initialState", {"is_field": True}),
    ]


DOWNLOADLCLIENT_TYPES: Tuple[Type[DownloadClient], ...] = (
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
)
DOWNLOADCLIENT_TYPE_MAP: Dict[str, Type[DownloadClient]] = {
    downloadclient_type._implementation: downloadclient_type
    for downloadclient_type in DOWNLOADLCLIENT_TYPES
}

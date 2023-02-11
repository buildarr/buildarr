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
Sonarr plugin media management settings configuration.
"""


from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from pydantic import Field

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_delete, api_get, api_post, api_put


class MultiEpisodeStyle(ConfigEnum):
    """
    Multi-episode style enumeration.
    """

    extend = 0
    duplicate = 1
    repeat = 2
    scene = 3
    range = 4
    prefixed_range = 5


class EpisodeTitleRequired(ConfigEnum):
    """
    Episode title required enumeration.
    """

    always = "always"
    bulk_season_releases = "bulkSeasonReleases"
    never = "never"


class PropersAndRepacks(ConfigEnum):
    """
    Propers and repacks configuration enumeration.
    """

    prefer_and_upgrade = "preferAndUpgrade"
    do_not_upgrade_automatically = "doNotUpgrade"
    do_not_prefer = "doNotPrefer"


class RescanSeriesFolderAfterRefresh(ConfigEnum):
    """
    Enumeration for rescan series folder after refresh.
    """

    always = "always"
    after_manual_refresh = "afterManual"
    never = "never"


class ChangeFileDate(ConfigEnum):
    """
    Change file date settings enumeration.
    """

    none = "none"
    local_air_date = "localAirDate"
    utc_air_date = "utcAirDate"


class ChmodFolder(ConfigEnum):
    """
    Read-write permissions for media folders.
    """

    drwxr_xr_x = "755"
    drwxrwxr_x = "775"
    drwxrwx___ = "770"
    drwxr_x___ = "750"
    drwxrwxrwx = "777"

    @classmethod
    def validate(cls, v: Any) -> ChmodFolder:
        """
        Ensure that octal and decimal integers are both read properly by Buildarr.
        """
        try:
            return cls(oct(v)[2:] if isinstance(v, int) else v)
        except ValueError:
            try:
                return cls[v.replace("-", "_")]
            except (TypeError, KeyError):
                raise ValueError(f"Invalid {cls.__name__} name or value: {v}")


class SonarrMediaManagementSettingsConfig(ConfigBase):
    """
    Naming, file management and root folder configuration.

    ```yaml
    sonarr:
      settings:
        media_management:
          ...
    ```

    For more information on how to configure these options correctly,
    refer to these guides from
    [WikiArr](https://wiki.servarr.com/sonarr/settings#media-management)
    and [TRaSH-Guides](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme).
    """

    # Episode Naming
    rename_episodes: bool = False
    """
    Rename imported files to the defined standard format.

    Sonarr will use the existing file name if renaming is disabled.
    """

    replace_illegal_characters: bool = True
    """
    Replace illegal characters within the file name.

    If set to `False`, Sonarr will remove them instead.
    """

    standard_episode_format: NonEmptyStr = (
        "{Series TitleYear} - "  # type: ignore[assignment]
        "S{season:00}E{episode:00} - "
        "{Episode CleanTitle} "
        "[{Preferred Words }{Quality Full}]"
        "{[MediaInfo VideoDynamicRangeType]}"
        "{[Mediainfo AudioCodec}{ Mediainfo AudioChannels]}"
        "{MediaInfo AudioLanguages}"
        "{[MediaInfo VideoCodec]}"
        "{-Release Group}"
    )
    """
    File renaming format for a standard episode file.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    daily_episode_format: NonEmptyStr = (
        "{Series TitleYear} - "  # type: ignore[assignment]
        "{Air-Date} - "
        "{Episode CleanTitle} "
        "[{Preferred Words }{Quality Full}]"
        "{[MediaInfo VideoDynamicRangeType]}"
        "{[Mediainfo AudioCodec}{ Mediainfo AudioChannels]}"
        "{MediaInfo AudioLanguages}"
        "{[MediaInfo VideoCodec]}"
        "{-Release Group}"
    )
    """
    File renaming format for a daily episode file.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    anime_episode_format: NonEmptyStr = (
        "{Series TitleYear} - "  # type: ignore[assignment]
        "S{season:00}E{episode:00} - "
        "{absolute:000} - "
        "{Episode CleanTitle} "
        "[{Preferred Words }{Quality Full}]"
        "{[MediaInfo VideoDynamicRangeType]}"
        "[{MediaInfo VideoBitDepth}bit]"
        "{[MediaInfo VideoCodec]}"
        "[{Mediainfo AudioCodec} { Mediainfo AudioChannels}]"
        "{MediaInfo AudioLanguages}"
        "{-Release Group}"
    )
    """
    File renaming format for an anime episode file.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    series_folder_format: NonEmptyStr = "{Series TitleYear}"  # type: ignore[assignment]
    """
    Renaming format for a series folder.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    season_folder_format: NonEmptyStr = "Season {season:00}"  # type: ignore[assignment]
    """
    Renaming format for a season folder of a series.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    specials_folder_format: NonEmptyStr = "Specials"  # type: ignore[assignment]
    """
    Renaming format for a specials folder of a series.

    The default specified here is the current TRaSH-Guides recommended format,
    but it will not be applied to the Sonarr instance unless it is explicitly
    defined in the configuration file.
    """

    multiepisode_style: MultiEpisodeStyle = MultiEpisodeStyle.range
    """
    Formatting style for the episode numbers of a multi-episode media file.
    """

    # Folders
    create_empty_series_folders: bool = False
    """
    Create missing series folders during disk scan.
    """

    delete_empty_folders: bool = False
    """
    Delete empty series and season folders during disk scan and when
    episode files are deleted.
    """

    # Importing
    episode_title_required: EpisodeTitleRequired = EpisodeTitleRequired.always
    """
    Prevent importing for up to 48 hours if the episode title
    is in the naming format and the episode title is TBA.

    Values:

    * `always`
    * `bulk-season-releases`
    * `never`

    ```yaml
    sonarr:
      settings:
        media_management:
          episode_title_required: "always"
    ```
    """

    skip_free_space_check: bool = False
    """
    Skip the free space check for the series root folder.

    Only enable when Sonarr is unable to detect free space from your series root folder.
    """

    minimum_free_space: int = Field(100, ge=0)  # MB
    """
    Prevent import if it would leave less than the specified
    amount of disk space (in megabytes) available.
    """

    use_hardlinks: bool = True
    """
    Use hard links when trying to copy files from torrents that are still being seeded.

    Occasionally, file locks may prevent renaming files that are being seeded.
    You may temporarily disable seeding and use Sonarr's rename function as a work around.
    """

    import_extra_files: bool = False
    """
    Import matching extra files (subtitles, `.nfo` file, etc) after importing an episode file.
    """

    # File Management
    unmonitor_deleted_episodes: bool = False
    """
    Episodes deleted from disk are automatically unmonitored in Sonarr.
    """

    propers_and_repacks: PropersAndRepacks = PropersAndRepacks.do_not_prefer
    """
    Whether or not to automatically upgrade to Propers/Repacks.

    Values:

    * `prefer-and-upgrade`
    * `do-not-upgrade-automatically`
    * `do-not-prefer`

    ```yaml
    sonarr:
      settings:
        media_management:
          propers_and_repacks: "do-not-prefer"
    ```

    Use 'Do not Prefer' to sort by preferred word score over propers/repacks.
    Use 'Prefer and Upgrade' for automatic upgrades to propers/repacks.
    """

    analyze_video_files: bool = True
    """
    Extract video information such as resolution, runtime and codec information
    from files.

    This requires Sonarr to read parts of the file, which may cause high disk
    or network activity during scans.
    """

    rescan_series_folder_after_refresh: RescanSeriesFolderAfterRefresh = (
        RescanSeriesFolderAfterRefresh.always
    )
    """
    Rescan the series folder after refreshing the series.

    Values:

    * `always`
    * `after_manual_refresh`
    * `never`

    ```yaml
    sonarr:
      settings:
        media_management:
          rescan_series_folder_after_refresh: "always"
    ```

    NOTE: Sonarr will not automatically detect changes to files
    if this option is not set to `always`.
    """

    change_file_date: ChangeFileDate = ChangeFileDate.none
    """
    Change file date on import/rescan.

    Values:

    * `none`
    * `local-air-date`
    * `utc-air-date`

    ```yaml
    sonarr:
      settings:
        media_management:
          change_file_date: "none"
    ```
    """

    recycling_bin: Optional[NonEmptyStr] = None
    """
    Episode files will go here when deleted instead of being permanently deleted.
    """

    recycling_bin_cleanup: int = Field(7, ge=0)  # days
    """
    Files in the recycle bin older than the selected number of days
    will be cleaned up automatically.

    Set to 0 to disable automatic cleanup.
    """

    # Permissions
    set_permissions: bool = False
    """
    Set whether or not `chmod` should run when files are imported/renamed.

    If you're unsure what this and the `chmod`/`chown` series of attributes do,
    do not alter them.
    """

    chmod_folder: ChmodFolder = ChmodFolder.drwxr_xr_x
    """
    Permissions to set on media folders and files during import/rename.
    File permissions are set without execute bits.

    This only works if the user running Sonarr is the owner of the file.
    It's better to ensure the download client sets the permissions properly.

    Values:

    * `drwxr-xr-x`/`755`
    * `drwxrwxr-x`/`775`
    * `drwxrwx---`/`770`
    * `drwxr-x---`/`750`
    * `drwxrwxrwx`/`777`

    ```yaml
    sonarr:
      settings:
        media_management:
          chmod_folder: "drwxr-xr-x"
    ```
    """

    chown_group: Optional[NonEmptyStr] = None
    """
    Group name or gid. Use gid for remote file systems.

    This only works if the user running Sonarr is the owner of the file.
    It's better to ensure the download client uses the same group as Sonarr.
    """

    root_folders: List[NonEmptyStr] = []
    """
    This allows you to create a root path for a place to either
    place new imported downloads, or to allow Sonarr to scan existing media.

    ```yaml
    sonarr:
      settings:
        media_management:
          root_folders:
            - "/path/to/rootfolder"
    ```
    """

    _naming_remote_map: List[RemoteMapEntry] = [
        # Episode Naming
        ("rename_episodes", "renameEpisodes", {}),
        ("replace_illegal_characters", "replaceIllegalCharacters", {}),
        ("standard_episode_format", "standardEpisodeFormat", {}),
        ("daily_episode_format", "dailyEpisodeFormat", {}),
        ("anime_episode_format", "animeEpisodeFormat", {}),
        ("series_folder_format", "seriesFolderFormat", {}),
        ("season_folder_format", "seasonFolderFormat", {}),
        ("specials_folder_format", "specialsFolderFormat", {}),
        ("multiepisode_style", "multiEpisodeStyle", {}),
    ]
    _mediamanagement_remote_map: List[RemoteMapEntry] = [
        # Folders
        ("create_empty_series_folders", "createEmptySeriesFolders", {}),
        ("delete_empty_folders", "deleteEmptyFolders", {}),
        # Importing
        ("episode_title_required", "episodeTitleRequired", {}),
        ("skip_free_space_check", "skipFreeSpaceCheckWhenImporting", {}),
        ("minimum_free_space", "minimumFreeSpaceWhenImporting", {}),
        ("use_hardlinks", "copyUsingHardlinks", {}),
        ("import_extra_files", "importExtraFiles", {}),
        # File Management
        ("propers_and_repacks", "downloadPropersAndRepacks", {}),
        ("analyze_video_files", "enableMediaInfo", {}),
        ("rescan_series_folder_after_refresh", "rescanAfterRefresh", {}),
        ("change_file_date", "fileDate", {}),
        (
            "recycling_bin",
            "recycleBin",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("recycling_bin_cleanup", "recycleBinCleanupDays", {}),
        # Permissions
        ("set_permissions", "setPermissionsLinux", {}),
        ("chmod_folder", "chmodFolder", {}),
        (
            "chown_group",
            "chownGroup",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrMediaManagementSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        return cls(
            # Episode Naming
            **cls.get_local_attrs(
                cls._naming_remote_map,
                api_get(sonarr_secrets, "/api/v3/config/naming"),
            ),
            # All other sections except Root Folders
            **cls.get_local_attrs(
                cls._mediamanagement_remote_map,
                api_get(sonarr_secrets, "/api/v3/config/mediamanagement"),
            ),
            # Root Folders
            root_folders=[rf["path"] for rf in api_get(sonarr_secrets, "/api/v3/rootfolder")],
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrMediaManagementSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        return any(
            [
                # Episode Naming
                self._update_remote_naming(
                    tree,
                    sonarr_secrets,
                    remote,
                    check_unmanaged=check_unmanaged,
                ),
                # All other sections except Root Folders
                self._update_remote_mediamanagement(
                    tree,
                    sonarr_secrets,
                    remote,
                    check_unmanaged=check_unmanaged,
                ),
                # Root Folders
                self._update_remote_rootfolder(
                    tree,
                    sonarr_secrets,
                    remote,
                    check_unmanaged=check_unmanaged,
                ),
            ],
        )

    def _update_remote_naming(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: SonarrMediaManagementSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._naming_remote_map,
            check_unmanaged=check_unmanaged,
        )
        if updated:
            api_put(
                sonarr_secrets,
                f"/api/v3/config/naming/{api_get(sonarr_secrets, '/api/v3/config/naming')['id']}",
                remote_attrs,
            )
            return True
        return False

    def _update_remote_mediamanagement(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: SonarrMediaManagementSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._mediamanagement_remote_map,
            check_unmanaged=check_unmanaged,
        )
        if updated:
            api_put(
                sonarr_secrets,
                (
                    "/api/v3/config/mediamanagement/"
                    f"{api_get(sonarr_secrets, '/api/v3/config/mediamanagement')['id']}"
                ),
                remote_attrs,
            )
            return True
        return False

    def _update_remote_rootfolder(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: SonarrMediaManagementSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        changed = False
        current_root_folders: Dict[str, int] = {
            rf["path"]: rf["id"] for rf in api_get(sonarr_secrets, "/api/v3/rootfolder")
        }
        expected_root_folders = set(self.root_folders)
        # TODO: change root_folders so that you can set check_unmanaged specifically for it
        #       e.g. "delete_unmanaged"
        if check_unmanaged:
            for root_folder, root_folder_id in current_root_folders.items():
                if root_folder not in expected_root_folders:
                    plugin_logger.info("%s: %s -> (deleted)", tree, repr(str(root_folder)))
                    api_delete(sonarr_secrets, f"/api/v3/rootfolder/{root_folder_id}")
                    changed = True
        for i, root_folder in enumerate(self.root_folders):
            if root_folder in current_root_folders:
                plugin_logger.debug("%s[%i]: %s (exists)", tree, i, repr(str(root_folder)))
            else:
                plugin_logger.info("%s[%i]: %s -> (created)", tree, i, repr(str(root_folder)))
                api_post(sonarr_secrets, "/api/v3/rootfolder", {"path": str(root_folder)})
                changed = True
        return changed

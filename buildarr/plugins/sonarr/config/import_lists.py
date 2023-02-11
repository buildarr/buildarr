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
Sonarr plugin import list settings configuration.
"""


from __future__ import annotations

import re

from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional, Set, Tuple, Type, Union, cast

from pydantic import ConstrainedStr, HttpUrl, PositiveInt
from typing_extensions import Self

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, Password, RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_delete, api_get, api_post, api_put
from .util import TraktAuthUser, trakt_expires_encoder


class YearRange(ConstrainedStr):
    """
    Constrained string type for a singular year or range of years.
    """

    regex = re.compile(r"[0-9]+(?:-[0-9]+)?")

    # TODO: validate that the end year is higher than the start year


class Monitor(ConfigEnum):
    """
    Enumeration for what kind of monitoring should be done in an import list.
    """

    all_episodes = "all"
    future_episodes = "future"
    missing_episodes = "missing"
    existing_episodes = "existing"
    pilot_episode = "pilot"
    first_season = "firstSeason"
    only_latest_season = "latestSeason"
    none = "none"


class SeriesType(ConfigEnum):
    """
    Series type to classify media from an import list.
    """

    standard = "standard"
    daily = "daily"
    anime = "anime"


class TraktPopularListType(ConfigEnum):
    """
    Types of popularity list in Trakt.
    """

    trending = 0
    popular = 1
    anticipated = 2
    top_watched_by_week = 3
    top_watched_by_month = 4
    top_watched_by_year = 5
    top_watched_by_alltime = 6
    recommended_by_week = 7
    recommended_by_month = 8
    recommended_by_year = 9
    recommended_by_alltime = 10


class TraktUserListType(ConfigEnum):
    """
    Types of user list in Trakt.
    """

    user_watch_list = 0
    user_watched_list = 1
    user_collection_list = 2


class ImportList(ConfigBase):
    """
    For more information on how an import list should be setup,
    refer to this guide on [WikiArr](https://wiki.servarr.com/en/sonarr/settings#import-lists).

    All import list types can have the following attributes configured.
    """

    enable_automatic_add: bool = True
    """
    Automatically add series to Sonarr upon syncing.
    """

    monitor: Monitor = Monitor.all_episodes
    """
    Define how Sonarr should monitor existing and new episodes of series.

    Values:

    * `all-episodes` - Monitor all episodes except specials
    * `future-episodes` - Monitor episodes that have not aired yet
    * `missing-episodes` - Monitor episodes that do not have files or have not aired yet
    * `existing-episodes` - Monitor episodes that have files or have not aired yet
    * `pilot-episode` - Monitor only the pilot episode of a series
    * `first-season` - Monitor all episodes of the first season (all other seasons will be ignored)
    * `only-latest-season` - Monitor all episodes of the latest season and future seasons
    * `none` - No episodes will be monitored
    """

    root_folder: Optional[str] = None
    """
    Add list items to the specified root folder.
    """

    quality_profile: Optional[str] = None
    """
    The name of the quality profile list items will be added with.

    If unset, blank or set to `None`, use any quality profile.
    """

    language_profile: Optional[str] = None
    """
    The name of the language profile list items will be added with.

    If unset, blank or set to `None`, use any language profile.
    """

    series_type: SeriesType = SeriesType.standard
    """
    The type of series that get imported from this import list.
    This option affects how Sonarr handles the media, such as renaming.

    Values:

    * `standard` - Episodes released with an `SxxEyy` pattern
    * `daily` - Episodes released daily or less frequently that use year-month-day (2017-05-25)
    * `anime` - Episodes released using an absolute episode number
    """

    season_folder: bool = True
    """
    Use a season folder for series imported from this import list.
    """

    tags: Set[NonEmptyStr] = set()
    """
    Tags to assign to items imported from this import list.
    """

    _implementation_name: str
    _implementation: str
    _config_contract: str
    _remote_map: List[RemoteMapEntry]

    @classmethod
    def _get_base_remote_map(
        cls,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return [
            ("enable_automatic_add", "enableAutomaticAdd", {}),
            ("monitor", "shouldMonitor", {}),
            (
                "root_folder",
                "rootFolderPath",
                {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
            ),
            (
                "quality_profile",
                "qualityProfileId",
                {
                    "decoder": lambda v: next(
                        (ind for ind, ind_id in quality_profile_ids.items() if ind_id == v),
                        None,
                    ),
                    "encoder": lambda v: quality_profile_ids[v] if v else 0,
                },
            ),
            (
                "language_profile",
                "languageProfileId",
                {
                    "decoder": lambda v: next(
                        (ind for ind, ind_id in language_profile_ids.items() if ind_id == v),
                        None,
                    ),
                    "encoder": lambda v: language_profile_ids[v] if v else 0,
                },
            ),
            ("series_type", "seriesType", {}),
            ("season_folder", "seasonFolder", {}),
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
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> ImportList:
        return cls(
            **cls.get_local_attrs(
                (
                    cls._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids)
                    + cls._remote_map
                ),
                remote_attrs,
            ),
        )

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        importlist_name: str,
    ) -> None:
        api_post(
            sonarr_secrets,
            "/api/v3/importlist",
            {
                "name": importlist_name,
                "implementation": self._implementation,
                "implementationName": self._implementation_name,
                "configContract": self._config_contract,
                **self.get_create_remote_attrs(
                    tree,
                    (
                        self._get_base_remote_map(
                            quality_profile_ids,
                            language_profile_ids,
                            tag_ids,
                        )
                        + self._remote_map
                    ),
                ),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: Self,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        importlist_id: int,
        importlist_name: str,
    ) -> bool:
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids)
            + self._remote_map,
            # TODO: check if check_unmanaged and/or set_unchanged are required (probably are)
        )
        if updated:
            api_put(
                sonarr_secrets,
                f"/api/v3/importlist/{importlist_id}",
                {
                    "id": importlist_id,
                    "name": importlist_name,
                    "implementation": self._implementation,
                    "implementationName": self._implementation_name,
                    "configContract": self._config_contract,
                    **remote_attrs,
                },
            )
            return True
        return False

    def _delete_remote(self, tree: str, sonarr_secrets: SonarrSecrets, importlist_id: int) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets, f"/api/v3/importlist/{importlist_id}")


class ProgramImportList(ImportList):
    """
    Base class for program-based import lists.
    """

    pass


class PlexImportList(ImportList):
    """
    Base class for import lists based on Plex.
    """

    pass


class TraktImportList(ImportList):
    """
    Import added media from a list on the Trakt media tracker.

    !!! note

        Sonarr directly authenticates with Trakt to generate tokens for it to use.
        At the moment, the easiest way to generate the tokens for Buildarr
        is to do it using the GUI within Sonarr, and use the following
        shell command to retrieve the generated configuration.

        ```bash
        $ curl -X "GET" "<sonarr-url>/api/v3/notification" -H "X-Api-Key: <api-key>"
        ```

    The following parameters are common to all Trakt import list types.
    The authenticated-related parameters (`access_token`, `refresh_token`, `expires`, `auth_user`)
    are required.
    """

    # Base class for import lists based on Trakt.

    # FIXME: Determine easier procedure for getting access tokens and test.

    access_token: Password
    """
    Access token for Sonarr from Trakt.
    """

    refresh_token: Password
    """
    Refresh token for Sonarr from Trakt.
    """

    expires: datetime
    """
    Expiry date-time of the access token, preferably in ISO-8601 format and in UTC.

    Example: `2023-05-10T15:34:08.117451Z`
    """

    auth_user: TraktAuthUser
    """
    The username being authenticated in Trakt.
    """

    # rating
    # TODO: constraints
    rating: NonEmptyStr = "0-100"  # type: ignore[assignment]
    """
    Filter series by rating range, with a maximum range of 0-100.
    """

    username: Optional[str] = None
    """
    Username for the list to import from.

    Leave undefined, empty or set to `None` to use the auth user.
    """

    genres: Set[NonEmptyStr] = set()
    """
    Filter series by Trakt genre slug.
    """

    years: Optional[YearRange] = None
    """
    Filter series by year or year range. (e.g. `2009` or `2009-2015`)
    """

    limit: PositiveInt = 100
    """
    Limit the number of series to get.
    """

    trakt_additional_parameters: Optional[str] = None
    """
    Additional parameters to send to the Trakt API.
    """

    @classmethod
    def _get_base_remote_map(
        cls,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return super()._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids) + [
            ("access_token", "accessToken", {"is_field": True}),
            ("refresh_token", "refreshToken", {"is_field": True}),
            ("expires", "expires", {"is_field": True, "encoder": trakt_expires_encoder}),
            ("auth_user", "authUser", {"is_field": True}),
            ("rating", "rating", {"is_field": True}),
            (
                "username",
                "username",
                {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
            ),
            (
                "genres",
                "genres",
                {
                    "is_field": True,
                    "decoder": lambda v: set(v.split(",")) if v else set(),
                    "encoder": lambda v: ",".join(sorted(v)) if v else "",
                },
            ),
            (
                "years",
                "years",
                {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
            ),
            ("limit", "limit", {"is_field": True}),
            ("trakt_additional_parameters", "traktAdditionalParameters", {"is_field": True}),
        ]


class SonarrImportList(ProgramImportList):
    """
    Import items from another Sonarr instance.

    The Sonarr instance preferably should be the same version as this Sonarr instance.
    """

    type: Literal["sonarr"] = "sonarr"
    """
    Type value associated with this kind of import list.
    """

    # TODO:
    #   * Read the peer Sonarr instance for quality profile, language profile and tag metadata,
    #     so all the user needs to put in is the names of each, instead of IDs.
    #   * Add instance support. Specify the name of the other Sonarr instance
    #     as defined in Buildarr, and have Buildarr fill in the rest of the details.

    full_url: HttpUrl
    """
    URL that this Sonarr instance will use to connect to the source Sonarr instance.
    """

    api_key: Password
    """
    API key used to access the remote instance.
    """

    source_quality_profile_ids: Set[PositiveInt] = set()
    """
    IDs of the Quality Profiles from the source instance to import from.
    """

    source_language_profile_ids: Set[PositiveInt] = set()
    """
    IDs of the Language Profiles from the source instance to import from.
    """

    source_tag_ids: Set[PositiveInt] = set()
    """
    IDs of the tags from the source instance to import from.
    """

    _implementation_name: str = "Sonarr"
    _implementation: str = "SonarrImport"
    _config_contract: str = "SonarrSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("full_url", "baseUrl", {"is_field": True}),
        ("api_key", "apiKey", {"is_field": True}),
        ("source_quality_profile_ids", "profileIds", {"is_field": True}),
        ("language_profile_ids", "languageProfileIds", {"is_field": True}),
        ("source_tags", "tagIds", {"is_field": True}),
    ]


class PlexWatchlistImportList(PlexImportList):
    """
    Import items from a Plex watchlist.
    """

    type: Literal["plex-watchlist"] = "plex-watchlist"
    """
    Type value associated with this kind of import list.
    """

    access_token: Password
    """
    Plex authentication token.

    If unsure on where to find this token,
    [follow this guide from Plex.tv][PATH].
    [PATH]: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token
    """

    _implementation_name: str = "Plex Watchlist"
    _implementation: str = "PlexImport"
    _config_contract: str = "PlexListSettings"
    _remote_map: List[RemoteMapEntry] = [("access_token", "accessToken", {"is_field": True})]


class TraktListImportList(TraktImportList):
    """
    Import an arbitrary list from Trakt into Sonarr.
    """

    type: Literal["trakt-list"] = "trakt-list"
    """
    Type value associated with this kind of import list.
    """

    list_name: NonEmptyStr
    """
    Name of the list to import.

    The list must be public, or you must have access to the list.
    """

    _implementation_name: str = "Trakt List"
    _implementation: str = "TraktListImport"
    _config_contract: str = "TraktListSettings"
    _remote_map: List[RemoteMapEntry] = [("list_name", "listName", {"is_field": True})]


class TraktPopularlistImportList(TraktImportList):
    """
    Import media according to popularity-based lists on Trakt.
    """

    type: Literal["trakt-popularlist"] = "trakt-popularlist"
    """
    Type value associated with this kind of import list.
    """

    list_type: TraktPopularListType = TraktPopularListType.popular
    """
    Popularity-based list to import.

    Values:

    * `trending`
    * `popular`
    * `anticipated`
    * `top_watched_by_week`
    * `top_watched_by_month`
    * `top_watched_by_year`
    * `top_watched_by_alltime`
    * `recommended_by_week`
    * `recommended_by_month`
    * `recommended_by_year`
    * `recommended_by_alltime`
    """

    _implementation_name: str = "Trakt Popular List"
    _implementation: str = "TraktPopularImport"
    _config_contract: str = "TraktPopularSettings"
    _remote_map: List[RemoteMapEntry] = [("list_type", "traktListType", {"is_field": True})]


class TraktUserImportList(TraktImportList):
    """
    Import a user-level list from Trakt.
    """

    type: Literal["trakt-user"] = "trakt-user"
    """
    Type value associated with this kind of import list.
    """

    list_type: TraktUserListType = TraktUserListType.user_watch_list
    """
    User list type to import.

    Values:

    * `user_watch_list`
    * `user_watched_list`
    * `user_collection_list`
    """

    _implementation_name: str = "Trakt User"
    _implementation: str = "TraktUserImport"
    _config_contract: str = "TraktUserSettings"
    _remote_map: List[RemoteMapEntry] = [("list_type", "traktListType", {"is_field": True})]


IMPORTLIST_TYPES: Tuple[Type[ImportList], ...] = (
    SonarrImportList,
    PlexWatchlistImportList,
    TraktListImportList,
    TraktPopularlistImportList,
    TraktUserImportList,
)
IMPORTLIST_TYPE_MAP: Dict[str, Type[ImportList]] = {
    importlist_type._implementation: importlist_type for importlist_type in IMPORTLIST_TYPES
}


class SonarrImportListsSettingsConfig(ConfigBase):
    """
    Using import lists, Sonarr can monitor and import episodes from external sources.

    ```yaml
    sonarr:
      settings:
        import_lists:
          delete_unmanaged: False # Default is `false`
          delete_unmanaged_exclusions: true # Default is `false`
          definitions:
            Plex: # Name of import list definition
              type: "plex-watchlist" # Type of import list to use
              # Attributes common to all watch list types
              enable_automatic_add: true
              monitor: "all-episodes"
              series_type: "standard"
              season_folder: true
              tags:
                - "example"
              # Plex-specific attributes
              access_token: "..."
            # Add more import lists here.
          exclusions:
            72662: "Teletubbies" # TVDB ID is key, set an artibrary title as value
    ```

    Media can be queued on the source, and Sonarr will automatically import them,
    look for suitable releases, and download them.

    Media that you don't want to import can be ignored using the `exclusions`
    attribute.
    """

    delete_unmanaged: bool = False
    """
    Automatically delete import lists not defined in Buildarr.
    """

    delete_unmanaged_exclusions: bool = False
    """
    Automatically delete import list excusions not defined in Buildarr.
    """

    # TODO: Set minimum Python version to 3.11 and subscript IMPORTLIST_TYPES here.
    definitions: Dict[
        str,
        Union[
            SonarrImportList,
            PlexWatchlistImportList,
            TraktListImportList,
            TraktPopularlistImportList,
            TraktUserImportList,
        ],
    ] = {}
    """
    Import list definitions go here.
    """

    exclusions: Dict[PositiveInt, NonEmptyStr] = {}
    """
    Dictionary of TV series that should be excluded from being imported.

    The key is the TVDB ID of the series to exclude, the value is
    a title to give the series in the Sonarr UI.
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrImportListsSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        importlists = api_get(sonarr_secrets, "/api/v3/importlist")
        quality_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(sonarr_secrets, "/api/v3/qualityprofile")}
            if any(importlist["qualityProfileId"] for importlist in importlists)
            else {}
        )
        language_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(sonarr_secrets, "/api/v3/languageprofile")}
            if any(importlist["languageProfileId"] for importlist in importlists)
            else {}
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(importlist["tags"] for importlist in importlists)
            else {}
        )
        return cls(
            definitions={
                importlist["name"]: IMPORTLIST_TYPE_MAP[importlist["implementation"]]._from_remote(
                    sonarr_secrets,
                    quality_profile_ids,
                    language_profile_ids,
                    tag_ids,
                    importlist,
                )
                for importlist in importlists
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrImportListsSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        #
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        #
        importlist_ids: Dict[str, int] = {
            importlist_json["name"]: importlist_json["id"]
            for importlist_json in api_get(sonarr_secrets, "/api/v3/importlist")
        }
        quality_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(sonarr_secrets, "/api/v3/qualityprofile")}
            if any(importlist.quality_profile for importlist in self.definitions.values())
            or any(importlist.quality_profile for importlist in remote.definitions.values())
            else {}
        )
        language_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(sonarr_secrets, "/api/v3/languageprofile")}
            if any(importlist.language_profile for importlist in self.definitions.values())
            or any(importlist.language_profile for importlist in remote.definitions.values())
            else {}
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(importlist.tags for importlist in self.definitions.values())
            or any(importlist.tags for importlist in remote.definitions.values())
            else {}
        )
        #
        for importlist_name, importlist in self.definitions.items():
            importlist_tree = f"{tree}.definitions[{repr(importlist_name)}]"
            #
            if importlist_name not in remote.definitions:
                importlist._create_remote(
                    importlist_tree,
                    sonarr_secrets,
                    quality_profile_ids,
                    language_profile_ids,
                    tag_ids,
                    importlist_name,
                )
                changed = True
            #
            else:
                if importlist._update_remote(
                    importlist_tree,
                    sonarr_secrets,
                    remote.definitions[importlist_name],  # type: ignore[arg-type]
                    quality_profile_ids,
                    language_profile_ids,
                    tag_ids,
                    importlist_ids[importlist_name],
                    importlist_name,
                ):
                    changed = True
        #
        for importlist_name, importlist in remote.definitions.items():
            if importlist_name not in self.definitions:
                importlist_tree = f"{tree}.definitions[{repr(importlist_name)}]"
                if self.delete_unmanaged:
                    importlist._delete_remote(
                        importlist_tree,
                        sonarr_secrets,
                        importlist_ids[importlist_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", importlist_tree)
        #
        return changed

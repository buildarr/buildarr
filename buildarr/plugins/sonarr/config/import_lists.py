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
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from pydantic import AnyHttpUrl, ConstrainedStr, Field, PositiveInt, validator
from typing_extensions import Annotated, Self

from buildarr.config import RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.state import state
from buildarr.types import BaseEnum, InstanceName, NonEmptyStr, Password

from ..api import api_delete, api_get, api_post, api_put
from ..secrets import SonarrSecrets
from ..types import SonarrApiKey
from .types import SonarrConfigBase, TraktAuthUser
from .util import trakt_expires_encoder


class YearRange(ConstrainedStr):
    """
    Constrained string type for a singular year or range of years.
    """

    regex = re.compile(r"[0-9]+(?:-[0-9]+)?")

    # TODO: validate that the end year is higher than the start year


class Monitor(BaseEnum):
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


class SeriesType(BaseEnum):
    """
    Series type to classify media from an import list.
    """

    standard = "standard"
    daily = "daily"
    anime = "anime"


class TraktPopularListType(BaseEnum):
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


class TraktUserListType(BaseEnum):
    """
    Types of user list in Trakt.
    """

    user_watch_list = 0
    user_watched_list = 1
    user_collection_list = 2


class ImportList(SonarrConfigBase):
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

    root_folder: NonEmptyStr
    """
    The root folder to add list items to.

    This attribute is required.
    """

    quality_profile: NonEmptyStr
    """
    The name of the quality profile list items will be added with.

    This attribute is required.
    """

    language_profile: NonEmptyStr
    """
    The name of the language profile list items will be added with.

    This attribute is required.
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
        """
        Return the remote map for the base import list attributes.

        Args:
            quality_profile_ids (Mapping[str, int]): Quality profile ID mapping on the remote.
            language_profile_ids (Mapping[str, int]): Language profile ID mapping on the remote.
            tag_ids (Mapping[str, int]): Tag ID mapping on the remote.

        Returns:
            Remote map (as a list of entries)
        """
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
                    ),
                    "encoder": lambda v: quality_profile_ids[v],
                },
            ),
            (
                "language_profile",
                "languageProfileId",
                {
                    "decoder": lambda v: next(
                        (ind for ind, ind_id in language_profile_ids.items() if ind_id == v),
                    ),
                    "encoder": lambda v: language_profile_ids[v],
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
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> Self:
        """
        Parse an import list object from the remote Sonarr instance,
        and return its internal representation.

        Args:
            quality_profile_ids (Mapping[str, int]): Quality profile ID mapping on the remote.
            language_profile_ids (Mapping[str, int]): Language profile ID mapping on the remote.
            tag_ids (Mapping[str, int]): Tag ID mapping on the remote.
            remote_attrs (Mapping[str, Any]): Remote instance import list object.

        Returns:
            Internal import list object
        """
        return cls(
            **cls.get_local_attrs(
                (
                    cls._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids)
                    + cls._remote_map
                ),
                remote_attrs,
            ),
        )

    def _resolve(self, name: str, ignore_nonexistent_ids: bool = False) -> Self:
        """
        Resolve any instance references on this import list, and
        return an object with fully qualified attribute values.

        Args:
            name (str): Name associated with this import list.
            ignore_nonexistent_ids (bool, optional): Ignore invalid IDs on the target instance.

        Returns:
            Fully qualified import list object
        """
        return self._resolve_from_local(
            name=name,
            local=self,
            ignore_nonexistent_ids=ignore_nonexistent_ids,
        )

    def _resolve_from_local(
        self,
        name: str,
        local: Self,
        ignore_nonexistent_ids: bool = False,
    ) -> Self:
        """
        Resolve this import list using instance references from the given object,
        and return an object with fully qualified attribute values.

        Used to fully qualify import list objects read from a remote Sonarr instance,
        using its corresponding local configuration.

        Args:
            name (str): Name associated with this import list.
            local (Self): Import list object to use for instance referencing.
            ignore_nonexistent_ids (bool, optional): Ignore invalid IDs on the target instance.

        Returns:
            Fully qualified import list object
        """
        return self

    def _create_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        importlist_name: str,
    ) -> None:
        """
        Create this import list on the remote Sonarr instance.

        Args:
            tree (str): Configuration tree. Used for logging.
            secrets (SonarrSecrets): Secrets metadata for the remote instance.
            quality_profile_ids (Mapping[str, int]): Quality profile ID mapping on the remote.
            language_profile_ids (Mapping[str, int]): Language profile ID mapping on the remote.
            tag_ids (Mapping[str, int]): Tag ID mapping on the remote.
            importlist_name (str): Name associated with this import list.
        """
        api_post(
            secrets,
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
        secrets: SonarrSecrets,
        remote: Self,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        importlist_id: int,
        importlist_name: str,
    ) -> bool:
        """
        Compare this import list to the currently active one the remote Sonarr instance,
        and update it in-place if there are differences.

        Args:
            tree (str): Configuration tree. Used for logging.
            secrets (SonarrSecrets): Secrets metadata for the remote instance.
            remote (Self): Active import list confiuration on the remote instance.
            quality_profile_ids (Mapping[str, int]): Quality profile ID mapping on the remote.
            language_profile_ids (Mapping[str, int]): Language profile ID mapping on the remote.
            tag_ids (Mapping[str, int]): Tag ID mapping on the remote.
            importlist_id (int): ID associated with this import list on the remote instance.
            importlist_name (str): Name associated with this import list.

        Returns:
            `True` if the import list was updated, otherwise `False`
        """
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids)
            + self._remote_map,
            check_unmanaged=True,
            set_unchanged=True,
        )
        if updated:
            api_put(
                secrets,
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

    def _delete_remote(self, tree: str, secrets: SonarrSecrets, importlist_id: int) -> None:
        """
        Delete this import list from the remote Sonarr instance.

        Args:
            tree (str): Configuration tree. Used for logging.
            secrets (SonarrSecrets): Secrets metadata for the remote instance.
            importlist_id (int): ID associated with this import list on the remote instance.
        """
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(secrets, f"/api/v3/importlist/{importlist_id}")


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
        return [
            *super()._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids),
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

    The linked Sonarr instance must be the same major version as this defined Sonarr instance.
    For example, a Sonarr V3 instance cannot connect with a Sonarr V4 instance, and vice versa.

    ```yaml
    ...
      import_lists:
        definitions:
          Sonarr:
            type: "sonarr"
            # Global import list options.
            root_folder: "/path/to/videos"
            quality_profile: "HD/SD"
            language_profile: "English"
            # Sonarr import list-specific options.
            full_url: "http://sonarr:8989"
            api_key: "1a2b3c4d5e1a2b3c4d5e1a2b3c4d5e1a"
            source_quality_profiles:
              - 11
              ...
            source_language_profiles:
              - 22
              ...
            source_tags:
              - 33
              ...
    ```

    This import list supports instance references to another Buildarr-defined Sonarr instance
    using `instance_name`.

    In this mode, you can specify `instance_name` in place of `api_key`,
    and use actual names for the source language profiles, quality profiles and tags,
    instead of IDs which are subject to change.

    Here is an example of one Sonarr instance (`sonarr-4k`) referencing
    another instance (`sonarr-hd`), using it as an import list.

    ```yaml
    sonarr:
      instances:
        sonarr-hd:
          hostname: "localhost"
          port: 8989
        sonarr-4k:
          hostname: "localhost"
          port: 8990
          settings:
            import_lists:
              definitions:
                Sonarr (HD):
                  type: "sonarr"
                  # Global import list options.
                  root_folder: "/path/to/videos"
                  quality_profile: "4K"
                  language_profile: "English"
                  # Sonarr import list-specific options.
                  full_url: "http://sonarr:8989"
                  instance_name: "sonarr-hd"
                  source_quality_profiles:
                    - "HD/SD"
                  source_language_profiles:
                    - "English"
                  source_tags:
                    - "shows"
    ```

    An important thing to keep in mind is that unless Buildarr is on the same network
    as the rest of the *Arr stack, the hostnames and ports may differ to what the
    Sonarr instances will use to communicate with each other. `full_url` should be
    set to what the Sonarr instance itself will use to link to the target instance.
    """

    type: Literal["sonarr"] = "sonarr"
    """
    Type value associated with this kind of import list.
    """

    instance_name: Optional[InstanceName] = Field(None, plugin="sonarr")
    """
    The name of the Sonarr instance within Buildarr, if linking this Sonarr instance
    with another Buildarr-defined Sonarr instance.

    *Added in version 0.3.0.*
    """

    full_url: AnyHttpUrl
    """
    The URL that this Sonarr instance will use to connect to the source Sonarr instance.
    """

    api_key: Optional[SonarrApiKey] = None
    """
    API key used to access the source Sonarr instance.

    If a Sonarr instance managed by Buildarr is not referenced using `instance_name`,
    this attribute is required.
    """

    source_quality_profiles: Set[Union[PositiveInt, NonEmptyStr]] = Field(
        set(),
        alias="source_quality_profile_ids",
    )
    """
    List of IDs (or names) of the quality profiles on the source instance to import from.

    Quality profile names can only be used if `instance_name` is used to
    link to a Buildarr-defined Sonarr instance.
    If linking to a Sonarr instance outside Buildarr, IDs must be used.

    *Changed in version 0.3.0: Renamed from `source_quality_profile_ids`
    (which is still valid as an alias), and add support for quality profile names.*
    """

    source_language_profiles: Set[Union[PositiveInt, NonEmptyStr]] = Field(
        set(),
        alias="source_language_profile_ids",
    )
    """
    List of IDs (or names) of the language profiles on the source instance to import from.

    Language profile names can only be used if `instance_name` is used to
    link to a Buildarr-defined Sonarr instance.
    If linking to a Sonarr instance outside Buildarr, IDs must be used.

    *Changed in version 0.3.0: Renamed from `source_language_profile_ids`
    (which is still valid as an alias), and add support for language profile names.*
    """

    source_tags: Set[Union[PositiveInt, NonEmptyStr]] = Field(set(), alias="source_tag_ids")
    """
    List of IDs (or names) of the tags on the source instance to import from.

    Tag names can only be used if `instance_name` is used to
    link to a Buildarr-defined Sonarr instance.
    If linking to a Sonarr instance outside Buildarr, IDs must be used.

    *Changed in version 0.3.0: Renamed from `source_tag_ids`
    (which is still valid as an alias), and add support for tag names.*
    """

    _implementation_name: str = "Sonarr"
    _implementation: str = "SonarrImport"
    _config_contract: str = "SonarrSettings"
    _remote_map: List[RemoteMapEntry] = []

    @classmethod
    def _get_base_remote_map(
        cls,
        quality_profile_ids: Mapping[str, int],
        language_profile_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return [
            *super()._get_base_remote_map(quality_profile_ids, language_profile_ids, tag_ids),
            ("full_url", "baseUrl", {"is_field": True}),
            ("api_key", "apiKey", {"is_field": True}),
            (
                "source_quality_profiles",
                "profileIds",
                {
                    "is_field": True,
                    "root_encoder": lambda vs: cls._encode_source_resources(
                        instance_name=vs.instance_name,
                        resources=vs.source_quality_profiles,
                        resource_type="qualityprofile",
                    ),
                },
            ),
            (
                "source_language_profiles",
                "languageProfileIds",
                {
                    "is_field": True,
                    "root_encoder": lambda vs: cls._encode_source_resources(
                        instance_name=vs.instance_name,
                        resources=vs.source_language_profiles,
                        resource_type="languageprofile",
                    ),
                },
            ),
            (
                "source_tags",
                "tagIds",
                {
                    "is_field": True,
                    "root_encoder": lambda vs: cls._encode_source_resources(
                        instance_name=vs.instance_name,
                        resources=vs.source_tags,
                        resource_type="tag",
                        name_key="label",
                    ),
                },
            ),
        ]

    @classmethod
    def _get_secrets(cls, instance_name: str) -> SonarrSecrets:
        """
        Fetch the secrets metadata for the given Sonarr instance from the Buildarr state.

        Args:
            instance_name (str): Name of Sonarr instance to get the secrets for.

        Returns:
            Sonarr instance secrets metadata
        """
        return cast(SonarrSecrets, state.secrets.sonarr[instance_name])

    @classmethod
    def _get_resources(cls, instance_name: str, resource_type: str) -> List[Dict[str, Any]]:
        """
        Make an API request to Sonarr to get the list of resources of the requested type.

        Args:
            instance_name (str): Name of Sonarr instance to get the resources from.
            profile_type (str): Name of the resource to get in the Sonarr API.

        Returns:
            List of resource API objects
        """
        return api_get(cls._get_secrets(instance_name), f"/api/v3/{resource_type}")

    @validator("api_key", always=True)
    def validate_api_key(
        cls,
        value: Optional[SonarrApiKey],
        values: Mapping[str, Any],
    ) -> Optional[SonarrApiKey]:
        """
        Validate the `api_key` attribute after parsing.

        Args:
            value (Optional[str]): `api_key` value.
            values (Mapping[str, Any]): Currently parsed attributes. `instance_name` is checked.

        Raises:
            ValueError: If `api_key` is undefined when `instance_name` is also undefined.

        Returns:
            Validated `api_key` value
        """
        if not values.get("instance_name", None) and not value:
            raise ValueError("required if 'instance_name' is undefined")
        return value

    @validator(
        "source_quality_profiles",
        "source_language_profiles",
        "source_tags",
        each_item=True,
    )
    def validate_source_resource_ids(
        cls,
        value: Union[int, str],
        values: Dict[str, Any],
    ) -> Union[int, str]:
        """
        Validate that all resource references are IDs (integers) if `instance_name` is undefined.

        Args:
            value (Union[int, str]): Resource reference (ID or name).
            values (Mapping[str, Any]): Currently parsed attributes. `instance_name` is checked.

        Raises:
            ValueError: If the resource reference is a name and `instance_name` is undefined.

        Returns:
            Validated resource reference
        """
        if not values.get("instance_name", None) and not isinstance(value, int):
            raise ValueError(
                "values must be IDs (not names) if 'instance_name' is undefined",
            )
        return value

    @classmethod
    def _encode_source_resources(
        cls,
        instance_name: Optional[str],
        resources: Iterable[Union[str, int]],
        resource_type: str,
        name_key: str = "name",
    ) -> List[int]:
        """
        Encode a collection of resource IDs/names into a list of resource IDs
        from the target Sonarr instance.

        Args:
            instance_name (Optional[str]): Target Sonarr instance to get resource IDs from.
            resources (Iterable[Union[str, int]]): Resource names/IDs to encode.
            resource_type (str): Type of resource to encode into IDs.
            name_key (str, optional): Key for the name of the resource. Defaults to `name`.

        Returns:
            List of resource IDs for the target Sonarr instance
        """
        resource_ids: Set[int] = set()
        if not instance_name:
            for resource in resources:
                if not isinstance(resource, int):
                    raise RuntimeError(
                        f"{resource_type} reference should be of type int here: {resource}",
                    )
                resource_ids.add(resource)
            return sorted(resource_ids)
        source_resource_ids: Optional[Dict[str, int]] = None
        for resource in resources:
            if isinstance(resource, int):
                resource_ids.add(resource)
            else:
                if source_resource_ids is None:
                    source_resource_ids = {
                        p[name_key]: p["id"]
                        for p in cls._get_resources(
                            instance_name,
                            resource_type,
                        )
                    }
                resource_ids.add(source_resource_ids[resource])
        return sorted(resource_ids)

    def _resolve_from_local(
        self,
        name: str,
        local: Self,
        ignore_nonexistent_ids: bool = False,
    ) -> Self:
        instance_name = local.instance_name
        if not instance_name:
            return self
        api_key = self._get_secrets(instance_name).api_key
        source_quality_profiles = self._resolve_resources(
            name=name,
            instance_name=instance_name,
            source_resources=self.source_quality_profiles,
            resource_type="qualityprofile",
            resource_description="quality profile",
            ignore_nonexistent_ids=ignore_nonexistent_ids,
        )
        source_language_profiles = self._resolve_resources(
            name=name,
            instance_name=instance_name,
            source_resources=self.source_language_profiles,
            resource_type="languageprofile",
            resource_description="language profile",
            ignore_nonexistent_ids=ignore_nonexistent_ids,
        )
        source_tags = self._resolve_resources(
            name=name,
            instance_name=instance_name,
            source_resources=self.source_tags,
            resource_type="tag",
            resource_description="tag",
            ignore_nonexistent_ids=ignore_nonexistent_ids,
            name_key="label",
        )
        return self.copy(
            update={
                "instance_name": instance_name,
                "api_key": api_key,
                "source_quality_profiles": source_quality_profiles,
                "source_language_profiles": source_language_profiles,
                "source_tags": source_tags,
            },
        )

    def _resolve_resources(
        self,
        name: str,
        instance_name: str,
        source_resources: Iterable[Union[int, str]],
        resource_type: str,
        resource_description: str,
        ignore_nonexistent_ids: bool,
        name_key: str = "name",
    ) -> Set[Union[int, str]]:
        """
        Resolve target Sonarr instance resource IDs/names into resource names.

        If `ignore_nonexistent_ids` is `True` and a resource ID was not found
        on the Sonarr instance, it is returned as-is.
        This will prompt Buildarr to remove the offending ID from Sonarr,
        so a warning is output to the logs to notify the user.

        Args:
            name (str): Name associated with this import list.
            instance_name (str): Target Sonarr instance name in Buildarr.
            source_resources (Iterable[Union[int, str]]):
            resource_type (str): Type of resource to resolve IDs for names.
            resource_description (str): Description of the resource type for logging.
            ignore_nonexistent_ids (bool): If `True`, remove non-existent IDs from the remote.
            name_key (str, optional): _description_. Defaults to "name".

        Raises:
            ValueError: If a non-existent ID was found and `ignore_nonexistent_ids` is `False`.
            ValueError: If a resource name was not found on the target Sonarr instance.

        Returns:
            List of resolved source resource names (and invalid IDs)
        """
        resolved_source_resources: Set[Union[int, str]] = set()
        if not source_resources:
            return resolved_source_resources
        remote_resources = self._get_resources(instance_name, resource_type)
        resource_ids = {r[name_key]: r["id"] for r in remote_resources}
        resource_names = {r["id"]: r[name_key] for r in remote_resources}
        for resource in source_resources:
            if isinstance(resource, int):
                try:
                    resolved_source_resources.add(resource_names[resource])
                except KeyError:
                    if ignore_nonexistent_ids:
                        plugin_logger.warning(
                            (
                                "Source %s ID %i referenced by remote Sonarr instance "
                                "not found on target instance '%s', removing"
                            ),
                            resource_description,
                            resource,
                            instance_name,
                        )
                        resolved_source_resources.add(resource)
                    else:
                        raise ValueError(
                            f"Source {resource_description} ID {resource} "
                            f"not found on target instance '{instance_name}",
                        ) from None
            elif resource in resource_ids:
                resolved_source_resources.add(resource)
            else:
                raise ValueError(
                    f"Source %s '{resource}' "
                    f"not found on target Sonarr instance '{instance_name}' "
                    f"in import list '{name}' "
                    "(available language profiles: "
                    f"{', '.join(repr(p) for p in resource_ids.keys())})",
                )
        return resolved_source_resources

    class Config(SonarrConfigBase.Config):
        # Ensure in-place assignments of attributes are always validated,
        # since this class performs such modifications in certain cases.
        validate_assignment = True


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

ImportListType = Union[
    SonarrImportList,
    PlexWatchlistImportList,
    TraktListImportList,
    TraktPopularlistImportList,
    TraktUserImportList,
]


class SonarrImportListsSettingsConfig(SonarrConfigBase):
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

    definitions: Dict[str, Annotated[ImportListType, Field(discriminator="type")]] = {}
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
    def from_remote(cls, secrets: SonarrSecrets) -> Self:
        importlists = api_get(secrets, "/api/v3/importlist")
        quality_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(secrets, "/api/v3/qualityprofile")}
            if any(importlist["qualityProfileId"] for importlist in importlists)
            else {}
        )
        language_profile_ids: Dict[str, int] = (
            {pro["name"]: pro["id"] for pro in api_get(secrets, "/api/v3/languageprofile")}
            if any(importlist["languageProfileId"] for importlist in importlists)
            else {}
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(secrets, "/api/v3/tag")}
            if any(importlist["tags"] for importlist in importlists)
            else {}
        )
        return cls(
            definitions={
                importlist["name"]: IMPORTLIST_TYPE_MAP[importlist["implementation"]]._from_remote(
                    quality_profile_ids=quality_profile_ids,
                    language_profile_ids=language_profile_ids,
                    tag_ids=tag_ids,
                    remote_attrs=importlist,
                )
                for importlist in importlists
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SonarrSecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        # Flag for whether or not the import list configuration was updated or not.
        changed = False
        # Get required resource ID references from the remote Sonarr instance.
        importlist_ids: Dict[str, int] = {
            importlist_json["name"]: importlist_json["id"]
            for importlist_json in api_get(secrets, "/api/v3/importlist")
        }
        quality_profile_ids: Dict[str, int] = {
            pro["name"]: pro["id"] for pro in api_get(secrets, "/api/v3/qualityprofile")
        }
        language_profile_ids: Dict[str, int] = {
            pro["name"]: pro["id"] for pro in api_get(secrets, "/api/v3/languageprofile")
        }
        tag_ids: Dict[str, int] = {
            tag["label"]: tag["id"] for tag in api_get(secrets, "/api/v3/tag")
        }
        # Evaluate locally defined import lists against the currently active ones
        # on the remote instance.
        for importlist_name, importlist in self.definitions.items():
            importlist = importlist._resolve(importlist_name)  # noqa: PLW2901
            importlist_tree = f"{tree}.definitions[{repr(importlist_name)}]"
            # If a locally defined import list does not exist on the remote, create it.
            if importlist_name not in remote.definitions:
                importlist._create_remote(
                    tree=importlist_tree,
                    secrets=secrets,
                    quality_profile_ids=quality_profile_ids,
                    language_profile_ids=language_profile_ids,
                    tag_ids=tag_ids,
                    importlist_name=importlist_name,
                )
                changed = True
            # Since there is an import list with the same name on the remote,
            # update it in-place.
            elif importlist._update_remote(
                tree=importlist_tree,
                secrets=secrets,
                remote=remote.definitions[importlist_name]._resolve_from_local(
                    name=importlist_name,
                    local=importlist,  # type: ignore[arg-type]
                    ignore_nonexistent_ids=True,
                ),
                quality_profile_ids=quality_profile_ids,
                language_profile_ids=language_profile_ids,
                tag_ids=tag_ids,
                importlist_id=importlist_ids[importlist_name],
                importlist_name=importlist_name,
            ):
                changed = True
        # Find import list definitions on the remote that aren't configured locally.
        # If `delete_unmanaged` is `True`, delete them. If not, just log them as unmanaged.
        for importlist_name, importlist in remote.definitions.items():
            if importlist_name not in self.definitions:
                importlist_tree = f"{tree}.definitions[{repr(importlist_name)}]"
                if self.delete_unmanaged:
                    importlist._delete_remote(
                        tree=importlist_tree,
                        secrets=secrets,
                        importlist_id=importlist_ids[importlist_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", importlist_tree)
        # We're done!
        return changed

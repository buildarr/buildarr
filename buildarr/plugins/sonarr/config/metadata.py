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
Sonarr plugin metadata settings configuration.
"""


from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, cast

from typing_extensions import Self

from buildarr.config import ConfigBase, RemoteMapEntry
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_get, api_put


class Metadata(ConfigBase):
    """
    Metadata definition base class.
    """

    enable: bool = False
    """
    When set to `True`, enables creating metadata files in the given format.
    """

    _implementation_name: str
    _implementation: str
    _config_contract: str
    _base_remote_map: List[RemoteMapEntry] = [("enable", "enable", {})]
    _remote_map: List[RemoteMapEntry]

    @classmethod
    def _from_remote(cls, sonarr_secrets: SonarrSecrets, metadata: Dict[str, Any]) -> Metadata:
        return cls(**cls.get_local_attrs(cls._base_remote_map + cls._remote_map, metadata))

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: Self,
        metadata: Mapping[str, Any],
        check_unmanaged: bool = False,
    ) -> bool:
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._base_remote_map + self._remote_map,
            check_unmanaged=check_unmanaged,
            set_unchanged=True,
        )
        if updated:
            api_put(
                sonarr_secrets,
                f"/api/v3/metadata/{metadata['id']}",
                {
                    "id": metadata["id"],
                    "name": self._implementation_name,
                    "implementationName": self._implementation_name,
                    "implementation": self._implementation,
                    "configContract": self._config_contract,
                    **remote_attrs,
                },
            )
            return True
        return False


class KodiEmbyMetadata(Metadata):
    """
    Output metadata files in a format suitable for Kodi (XBMC) or Emby.

    ```yaml
    sonarr:
      settings:
        metadata:
          kodi_emby:
            enable: true
            series_metadata: true
            series_metadata_url: true
            episode_metadata: true
            series_images: true
            season_images: true
            episode_images: true
    ```
    """

    series_metadata: bool = False
    """
    Create `tvshow.nfo` with full series metadata.
    """

    series_metadata_url: bool = False
    """
    Add the TVDB show URL to `tvshow.nfo`. Can be combined with `series_metadata`.
    """

    episode_metadata: bool = False
    """
    Create episode-specific metadata as `<filename>.nfo`.
    """

    series_images: bool = False
    """
    Save series images to `fanart.jpg`, `poster.jpg` and `banner.jpg`.
    """

    season_images: bool = False
    """
    Save season images to `season##-poster.jpg`/`season-specials-poster.jpg`
    and `season##-banner.jpg`/`season-specials-banner.jpg`.
    """

    episode_images: bool = False
    """
    Save episode images to `<filename>-thumb.jpg`.
    """

    _implementation_name: str = "Kodi (XBMC) / Emby"
    _implementation: str = "XbmcMetadata"
    _config_contract: str = "XbmcMetadataSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("series_metadata", "seriesMetadata", {"is_field": True}),
        ("series_metadata_url", "seriesMetadataUrl", {"is_field": True}),
        ("episode_metadata", "episodeMetadata", {"is_field": True}),
        ("series_images", "seriesImages", {"is_field": True}),
        ("season_images", "seasonImages", {"is_field": True}),
        ("episode_images", "episodeImages", {"is_field": True}),
    ]


class RoksboxMetadata(Metadata):
    """
    Output metadata files in a format suitable for Roksbox.

    ```yaml
    sonarr:
      settings:
        metadata:
          roksbox:
            enable: true
            episode_metadata: true
            series_images: true
            season_images: true
            episode_images: true
    ```
    """

    episode_metadata: bool = False
    """
    Create episode-specific metadata as `Season##/<filename>.xml`.
    """

    series_images: bool = False
    """
    Save series images to `<Series Title>.jpg`.
    """

    season_images: bool = False
    """
    Save season images to `Season ##.jpg`.
    """

    episode_images: bool = False
    """
    Save episode images to `Season##/<filename>.jpg`.
    """

    _implementation_name: str = "Roksbox"
    _implementation: str = "RoksboxMetadata"
    _config_contract: str = "RoksboxMetadataSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("episode_metadata", "episodeMetadata", {"is_field": True}),
        ("series_images", "seriesImages", {"is_field": True}),
        ("season_images", "seasonImages", {"is_field": True}),
        ("episode_images", "episodeImages", {"is_field": True}),
    ]


class WdtvMetadata(Metadata):
    """
    Output metadata files in a format suitable for WDTV.

    ```yaml
    sonarr:
      settings:
        metadata:
          wdtv:
            enable: true
            episode_metadata: true
            series_images: true
            season_images: true
            episode_images: true
    ```
    """

    episode_metadata: bool = False
    """
    Create episode-specific metadata as `<filename>.nfo`.
    """

    series_images: bool = False
    """
    Save series images to `fanart.jpg`, `poster.jpg` and `banner.jpg`.
    """

    season_images: bool = False
    """
    Save as images to `season##-poster.jpg`/`season-specials-poster.jpg`
    and `season##-banner.jpg`/`season-specials-banner.jpg`.
    """

    episode_images: bool = False
    """
    Save episode images to `<filename>-thumb.jpg`.
    """

    _implementation_name: str = "WDTV"
    _implementation: str = "WdtvMetadata"
    _config_contract: str = "WdtvMetadataSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("episode_metadata", "episodeMetadata", {"is_field": True}),
        ("series_images", "seriesImages", {"is_field": True}),
        ("season_images", "seasonImages", {"is_field": True}),
        ("episode_images", "episodeImages", {"is_field": True}),
    ]


METADATA_TYPES: Tuple[Type[Metadata], ...] = (KodiEmbyMetadata, RoksboxMetadata, WdtvMetadata)
METADATA_TYPE_MAP: Dict[str, Type[Metadata]] = {
    metadata_type._implementation: metadata_type for metadata_type in METADATA_TYPES
}


class SonarrMetadataSettingsConfig(ConfigBase):
    """
    Sonarr metadata settings.
    Implementation wise each metadata is a unique object, updated using separate requests.
    """

    kodi_emby = KodiEmbyMetadata()
    roksbox = RoksboxMetadata()
    wdtv = WdtvMetadata()

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrMetadataSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        kodi_emby_metadata: Optional[Dict[str, Any]] = None
        roksbox_metadata: Optional[Dict[str, Any]] = None
        wdtv_metadata: Optional[Dict[str, Any]] = None
        for metadata in api_get(sonarr_secrets, "/api/v3/metadata"):
            if metadata["implementation"] == KodiEmbyMetadata._implementation:
                kodi_emby_metadata = metadata
            elif metadata["implementation"] == RoksboxMetadata._implementation:
                roksbox_metadata = metadata
            elif metadata["implementation"] == WdtvMetadata._implementation:
                wdtv_metadata = metadata
        if kodi_emby_metadata is None:
            raise RuntimeError(
                "Unable to find Kodi (XBMC)/Emby metadata on Sonarr, database might be corrupt",
            )
        if roksbox_metadata is None:
            raise RuntimeError(
                "Unable to find Roksbox metadata on Sonarr, database might be corrupt",
            )
        if wdtv_metadata is None:
            raise RuntimeError(
                "Unable to find WDTV metadata on Sonarr, database might be corrupt",
            )
        return cls(
            kodi_emby=KodiEmbyMetadata._from_remote(sonarr_secrets, kodi_emby_metadata),
            roksbox=RoksboxMetadata._from_remote(sonarr_secrets, roksbox_metadata),
            wdtv=WdtvMetadata._from_remote(sonarr_secrets, wdtv_metadata),
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrMetadataSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        kodi_emby_metadata: Optional[Dict[str, Any]] = None
        roksbox_metadata: Optional[Dict[str, Any]] = None
        wdtv_metadata: Optional[Dict[str, Any]] = None
        for metadata in api_get(sonarr_secrets, "/api/v3/metadata"):
            if metadata["implementation"] == KodiEmbyMetadata._implementation:
                kodi_emby_metadata = metadata
            elif metadata["implementation"] == RoksboxMetadata._implementation:
                roksbox_metadata = metadata
            elif metadata["implementation"] == WdtvMetadata._implementation:
                wdtv_metadata = metadata
        if kodi_emby_metadata is None:
            raise RuntimeError(
                "Unable to find Kodi (XBMC)/Emby metadata on Sonarr, database might be corrupt",
            )
        if roksbox_metadata is None:
            raise RuntimeError(
                "Unable to find Roksbox metadata on Sonarr, database might be corrupt",
            )
        if wdtv_metadata is None:
            raise RuntimeError(
                "Unable to find WDTV metadata on Sonarr, database might be corrupt",
            )
        return any(
            [
                self.kodi_emby._update_remote(
                    tree,
                    sonarr_secrets,
                    remote.kodi_emby,
                    kodi_emby_metadata,
                    check_unmanaged=check_unmanaged,
                ),
                self.roksbox._update_remote(
                    tree,
                    sonarr_secrets,
                    remote.roksbox,
                    roksbox_metadata,
                    check_unmanaged=check_unmanaged,
                ),
                self.wdtv._update_remote(
                    tree,
                    sonarr_secrets,
                    remote.wdtv,
                    wdtv_metadata,
                    check_unmanaged=check_unmanaged,
                ),
            ]
        )

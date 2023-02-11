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
Sonarr plugin configuration.
"""


from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal, Optional, cast

from typing_extensions import Self

from buildarr.config import ConfigBase, ConfigPlugin, NonEmptyStr, Port
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import SonarrApiKey, get_initialize_js
from .connect import SonarrConnectSettingsConfig
from .download_clients import SonarrDownloadClientsSettingsConfig
from .general import SonarrGeneralSettingsConfig
from .import_lists import SonarrImportListsSettingsConfig
from .indexers import SonarrIndexersSettingsConfig
from .media_management import SonarrMediaManagementSettingsConfig
from .metadata import SonarrMetadataSettingsConfig
from .profiles import SonarrProfilesSettingsConfig
from .quality import SonarrQualitySettingsConfig
from .tags import SonarrTagsSettingsConfig
from .ui import SonarrUISettingsConfig


class SonarrSettingsConfig(ConfigBase):
    """
    Sonarr settings, used to configure a remote Sonarr instance.
    """

    #: Media management settings.
    media_management = SonarrMediaManagementSettingsConfig()

    #: Profile settings (quality, language, delay, release profiles).
    profiles = SonarrProfilesSettingsConfig()

    #: Quality definition settings.
    quality = SonarrQualitySettingsConfig()

    #: Usenet/BitTorrent indexer settings.
    indexers = SonarrIndexersSettingsConfig()

    #: Usenet/BitTorrent download client settings.
    download_clients = SonarrDownloadClientsSettingsConfig()

    #: Import list settings.
    import_lists = SonarrImportListsSettingsConfig()

    #: Notification connection settings.
    connect = SonarrConnectSettingsConfig()

    #: Metadata file settings.
    metadata = SonarrMetadataSettingsConfig()

    #: Tag settings.
    tags = SonarrTagsSettingsConfig()

    #: General instance settings.
    general = SonarrGeneralSettingsConfig()

    #: User interface settings.
    ui = SonarrUISettingsConfig()

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        # Overload base function to guarantee execution order of section updates.
        # 1. Tags must be created before everything else, and destroyed after they
        #    are no longer referenced elsewhere.
        # 2. Qualities must be updated before quality profiles.
        # 3. Indexers must be created before release profiles, and destroyed after they
        #    are no longer referenced by them.
        return any(
            [
                self.tags.update_remote(
                    f"{tree}.tags",
                    secrets,
                    remote.tags,
                    check_unmanaged=check_unmanaged,
                ),
                self.quality.update_remote(
                    f"{tree}.quality",
                    secrets,
                    remote.quality,
                    check_unmanaged=check_unmanaged,
                ),
                self.indexers.update_remote(
                    f"{tree}.indexers",
                    secrets,
                    remote.indexers,
                    check_unmanaged=check_unmanaged,
                ),
                self.media_management.update_remote(
                    f"{tree}.media_management",
                    secrets,
                    remote.media_management,
                    check_unmanaged=check_unmanaged,
                ),
                self.profiles.update_remote(
                    f"{tree}.profiles",
                    secrets,
                    remote.profiles,
                    check_unmanaged=check_unmanaged,
                ),
                self.download_clients.update_remote(
                    f"{tree}.download_clients",
                    secrets,
                    remote.download_clients,
                    check_unmanaged=check_unmanaged,
                ),
                self.import_lists.update_remote(
                    f"{tree}.import_lists",
                    secrets,
                    remote.import_lists,
                    check_unmanaged=check_unmanaged,
                ),
                self.connect.update_remote(
                    f"{tree}.connect",
                    secrets,
                    remote.connect,
                    check_unmanaged=check_unmanaged,
                ),
                self.metadata.update_remote(
                    f"{tree}.metadata",
                    secrets,
                    remote.metadata,
                    check_unmanaged=check_unmanaged,
                ),
                self.general.update_remote(
                    f"{tree}.general",
                    secrets,
                    remote.general,
                    check_unmanaged=check_unmanaged,
                ),
                self.ui.update_remote(
                    f"{tree}.ui",
                    secrets,
                    remote.ui,
                    check_unmanaged=check_unmanaged,
                ),
                # TODO: destroy indexers
                # TODO: destroy tags
            ],
        )


class SonarrConfig(ConfigPlugin):
    """
    By default, Buildarr will look for a single instance at `http://sonarr:8989`.
    Most configurations are different, and to accommodate those, you can configure
    how Buildarr connects to individual Sonarr instances.

    Configuration of a single Sonarr instance:

    ```yaml
    sonarr:
      hostname: "sonarr.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...
    ```

    Configuration of multiple instances:

    ```yaml
    sonarr:
      # Configuration and settings common to all instances.
      port: 8989
      settings:
        ...
      instances:
        # Sonarr instance 1-specific configuration.
        sonarr1:
          hostname: "sonarr1.example.com"
          settings:
            ...
        # Sonarr instance 2-specific configuration.
        sonarr2:
          hostname: "sonarr2.example.com"
          api_key: "..." # Explicitly define API key
          settings:
            ...
    ```
    """

    hostname: NonEmptyStr = "sonarr"  # type: ignore[assignment]
    """
    Hostname of the Sonarr instance to connect to.

    When defining a single instance using the global `sonarr` configuration block,
    the default hostname is `sonarr`.

    When using multiple instance-specific configurations, the default hostname
    is the name given to the instance in the `instances` attribute.

    ```yaml
    sonarr:
      instances:
        sonarr1: # <--- This becomes the default hostname
          ...
    ```
    """

    port: Port = 8989  # type: ignore[assignment]
    """
    Port number of the Sonarr instance to connect to.
    """

    protocol: Literal["http", "https"] = "http"  # type: ignore[assignment]
    """
    Communication protocol to use to connect to Sonarr.
    """

    api_key: Optional[SonarrApiKey] = None
    """
    API key to use to authenticate with the Sonarr instance.

    If undefined or set to `None`, automatically retrieve the API key.
    This can only be done on Sonarr instances with authentication disabled.
    """

    version: Optional[str] = None
    """
    The expected version of the Sonarr instance.
    If undefined or set to `None`, the version is auto-detected.

    At the moment this attribute is unused, and there is likely no need to explicitly set it.
    """

    settings: SonarrSettingsConfig = SonarrSettingsConfig()
    """
    Sonarr settings.
    Configuration options for Sonarr itself are set within this structure.
    """

    instances: Dict[str, SonarrConfig] = {}
    """
    Instance-specific Sonarr configuration.

    Can only be defined on the global `sonarr` configuration block.

    Globally specified configuration values apply to all instances.
    Configuration values specified on an instance-level take precedence at runtime.
    """

    @property
    def uses_trash_metadata(self) -> bool:
        """
        A flag determining whether or not this configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return self._uses_trash_metadata(nested=False)

    def _uses_trash_metadata(self, nested: bool = False) -> bool:
        if not nested:
            for instance in self.instances.values():
                if instance._uses_trash_metadata(nested=True):
                    return True
        if self.settings.quality.trash_id:
            return True
        for release_profile in self.settings.profiles.release_profiles.definitions.values():
            if release_profile.trash_id:
                return True
        return False

    def render_trash_metadata(self, trash_metadata_dir: Path) -> Self:
        """
        Read TRaSH-Guides metadata, and return a configuration object with all templates rendered.

        Args:
            trash_metadata_dir (Path): TRaSH-Guides metadata directory.

        Returns:
            Rendered configuration object
        """
        copy = self.copy(deep=True)
        copy._render_trash_metadata(trash_metadata_dir / "docs" / "json" / "sonarr")
        return copy

    def _render_trash_metadata(self, sonarr_metadata_dir: Path, nested: bool = False) -> None:
        if not nested:
            for instance in self.instances.values():
                instance._render_trash_metadata(sonarr_metadata_dir, nested=True)
        self.settings.profiles.release_profiles.definitions = {
            rp_name: rp.render_trash_metadata(sonarr_metadata_dir)
            for rp_name, rp in self.settings.profiles.release_profiles.definitions.items()
        }
        self.settings.quality = self.settings.quality.render_trash_metadata(sonarr_metadata_dir)

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> Self:
        """
        Read configuration from a remote instance and return it as a configuration object.

        Args:
            secrets (SecretsPlugin): Instance host and secrets information

        Returns:
            Configuration object for remote instance
        """
        sonarr_secrets = cast(SonarrSecrets, secrets)
        return cls(
            hostname=sonarr_secrets.hostname,
            port=sonarr_secrets.port,
            protocol=sonarr_secrets.protocol,
            api_key=sonarr_secrets.api_key,
            version=get_initialize_js(sonarr_secrets)["version"],
            settings=SonarrSettingsConfig.from_remote(secrets),
        )

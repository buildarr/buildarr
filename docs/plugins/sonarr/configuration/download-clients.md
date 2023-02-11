# Download Clients

##### ::: buildarr.plugins.sonarr.config.download_clients.SonarrDownloadClientsSettingsConfig
    options:
      members:
        - enable_completed_download_handling
        - redownload_failed
        - delete_unmanaged
        - definitions
        - remote_path_mappings
      show_root_heading: false
      show_source: false

!!! note

    Before Sonarr can send requests to download clients, at least one Usenet or
    torrent [indexer](indexers.md) will need to be configured.
    Sonarr will then send download requests to a compatible client,
    or the download client the indexer has been assigned to.

## Configuring download clients

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.DownloadClient
    options:
      members:
        - enable
        - priority
        - remove_completed_downloads
        - remove_failed_downloads
        - tags
      show_root_heading: false
      show_source: false

## Usenet download clients

These download clients retrieve media using the popular [Usenet](https://en.wikipedia.org/wiki/Usenet) discussion and content delivery system.

## Download Station

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.DownloadstationUsenetDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - username
        - password
        - category
        - directory
      show_root_heading: false
      show_source: false

## NZBGet

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.NzbgetDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - category
        - recent_priority
        - older_priority
        - add_paused
      show_root_heading: false
      show_source: false

## NZBVortex

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.NzbvortexDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - api_key
        - category
        - recent_priority
        - older_priority
      show_root_heading: false
      show_source: false

## Pneumatic

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.PneumaticDownloadClient
    options:
      members:
        - type
        - nzb_folder
        - strm_folder
      show_root_heading: false
      show_source: false

## SABnzbd

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.SabnzbdDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - api_key
        - category
        - recent_priority
        - older_priority
      show_root_heading: false
      show_source: false

## Usenet Blackhole

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.UsenetBlackholeDownloadClient
    options:
      members:
        - type
        - nzb_folder
        - watch_folder
      show_root_heading: false
      show_source: false

## Torrent download clients

These download clients use the [BitTorrent](https://en.wikipedia.org/wiki/BitTorrent)
peer-to-peer file sharing protocol to retrieve media files.

## Aria2

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.Aria2DownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - rpc_path
        - secret_token
      show_root_heading: false
      show_source: false

## Deluge

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.DelugeDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - password
        - category
        - postimport_category
        - recent_priority
        - older_priority
      show_root_heading: false
      show_source: false

## Download Station

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.DownloadstationTorrentDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - username
        - password
        - category
        - directory
      show_root_heading: false
      show_source: false

## Flood

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.FloodDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - destination
        - flood_tags
        - postimport_tags
        - additional_tags
        - start_on_add
      show_root_heading: false
      show_source: false

## Hadouken

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.HadoukenDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - category
      show_root_heading: false
      show_source: false

## qBittorrent

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.QbittorrentDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - category
        - postimport_category
        - recent_priority
        - older_priority
        - initial_state
        - sequential_order
        - first_and_last_first
      show_root_heading: false
      show_source: false

## RTorrent (ruTorrent)

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.RtorrentDownloadClient
    options:
      members:
        - type
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - category
        - postimport_category
        - recent_priority
        - older_priority
        - add_stopped
      show_root_heading: false
      show_source: false

## Torrent Blackhole

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.TorrentBlackholeDownloadClient
    options:
      members:
        - type
        - torrent_folder
        - watch_folder
        - save_magnet_files
        - magnet_file_extension
        - read_only
      show_root_heading: false
      show_source: false

## Transmission/Vuze

Transmission and Vuze use the same configuration parameters.

To use Transmission, set the `type` attribute in the download client to `transmission`.

To use Vuze, set the `type` attribute in the download client to `vuze`.

##### ::: buildarr.plugins.sonarr.config.download_clients.download_clients.TransmissionDownloadClientBase
    options:
      members:
        - host
        - port
        - use_ssl
        - url_base
        - username
        - password
        - category
        - directory
        - recent_priority
        - older_priority
        - add_paused
      show_root_heading: false
      show_source: false

## Configuring remote path mappings

##### ::: buildarr.plugins.sonarr.config.download_clients.remote_path_mappings.SonarrRemotePathMappingsSettingsConfig
    options:
      members:
        - delete_unmanaged
        - definitions
      show_root_heading: false
      show_source: false

### Remote path mapping parameters

##### ::: buildarr.plugins.sonarr.config.download_clients.remote_path_mappings.RemotePathMapping
    options:
      members:
        - host
        - remote_path
        - local_path
        - ensure
      show_root_heading: false
      show_source: false

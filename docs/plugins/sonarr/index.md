# `buildarr-sonarr`

`buildarr-sonarr` is a Buildarr plugin for configuring and managing [Sonarr](http://sonarr.tv) instances.

Sonarr is a PVR application which downloads, renames and manages the lifecycle of TV shows in your media library. It is capable of scanning for higher quality versions of your media and automatically upgrading them when a suitable version is available.

Currently, Sonarr V3 is the only supported version. Sonarr V4 support is planned for the future.

## Installation

As of the current release of Buildarr, `buildarr-sonarr` is distributed with Buildarr itself, to ease the burden of developing the Buildarr plugin API and `buildarr-sonarr` itself.

However, it is the intention that as the Buildarr plugin API stabilises, `buildarr-sonarr` will be eventually be separated from Buildarr itself, and developed independently.

## Quick Start

To use the `buildarr-sonarr` plugin, create a `sonarr` block within `buildarr.yml`, and enter the connection information required for the Buildarr instance to connect to the Sonarr instance you'd like to manage.

Buildarr won't modify anything yet since no configuration has been defined, but you are able to test if Buildarr is able to connect to and authenticate with the Sonarr instance.

```yaml
---

buildarr:
  watch_config: true

sonarr:
  hostname: "localhost" # Defaults to `sonarr`, or the instance name for instance-specific configs.
  port: 8989 # Defaults to 8989.
  protocol: "http" # Defaults to `http`.
  api_key: "..." # Optional. If undefined, auto-fetch (authentication must be disabled).
```

Now try a `buildarr run`. If the output is similar to the below output, Buildarr was able to connect to your Sonarr instance's API.

```bash
$ buildarr run
2023-02-22 20:34:43,271 buildarr:1 buildarr.main [INFO] Buildarr version 0.1.2 (log level: INFO)
2023-02-22 20:34:43,271 buildarr:1 buildarr.main [INFO] Loading configuration file '/config/buildarr.yml'
2023-02-22 20:34:43,308 buildarr:1 buildarr.main [INFO] Finished loading configuration file
2023-02-22 20:34:43,337 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr
2023-02-22 20:34:43,342 buildarr:1 buildarr.main [INFO] Running with plugins: sonarr
2023-02-22 20:34:43,344 buildarr:1 buildarr.main [INFO] Loading secrets file from '/config/secrets.json'
2023-02-22 20:34:43,345 buildarr:1 buildarr.main [INFO] Finished loading secrets file
2023-02-22 20:34:43,345 buildarr:1 buildarr.plugins.sonarr default [INFO] Checking secrets
2023-02-22 20:34:43,355 buildarr:1 buildarr.plugins.sonarr default [INFO] Connection test failed using cached secrets (or not cached), fetching secrets
2023-02-22 20:34:43,379 buildarr:1 buildarr.plugins.sonarr default [INFO] Connection test successful using fetched secrets
2023-02-22 20:34:43,380 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished checking secrets
2023-02-22 20:34:43,380 buildarr:1 buildarr.main [INFO] Saving updated secrets file to 'secrets.json'
2023-02-22 20:34:43,381 buildarr:1 buildarr.main [INFO] Finished saving updated secrets file
2023-02-22 20:34:50,508 buildarr:1 buildarr.plugins.sonarr default [INFO] Getting remote configuration
2023-02-22 20:34:50,774 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished getting remote configuration
2023-02-22 20:34:50,832 buildarr:1 buildarr.plugins.sonarr default [INFO] Updating remote configuration
2023-02-22 20:34:51,177 buildarr:1 buildarr.plugins.sonarr default [INFO] Remote configuration is up to date
2023-02-22 20:34:51,178 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished updating remote configuration
```

## Configuring your Sonarr instance

The following sections cover comprehensive configuration of a Sonarr instance.

Note that these documents do not show how you *should* configure a Sonarr instance. Rather, they show how you *can* configure a Sonarr instance the way you want with Buildarr. For more information on how to optimally configure Sonarr, you can refer to the excellent guides from [WikiArr](https://wiki.servarr.com/sonarr) and [TRaSH-Guides](https://trash-guides.info/Sonarr/).

* [Host Configuration](configuration/host.md)
* [Media Management](configuration/media-management.md)
* Profiles
    * [Quality Profiles](configuration/profiles/quality.md)
    - [Language Profiles](configuration/profiles/language.md)
    - [Delay Profiles](configuration/profiles/delay.md)
    - [Release Profiles](configuration/profiles/release.md)
- [Quality](configuration/quality.md)
- [Indexers](configuration/indexers.md)
- [Download Clients](configuration/download-clients.md)
- [Import Lists](configuration/import-lists.md)
- [Connect](configuration/connect.md)
- [Metadata](configuration/metadata.md)
- [Tags](configuration/tags.md)
- [General](configuration/general.md)
- [UI](configuration/ui.md)

## Dumping an existing Sonarr instance configuration

Buildarr is capable of dumping a running Sonarr instance's configuration.

```bash
$ buildarr sonarr dump-config http://localhost:8989 > sonarr.yml
Sonarr instance API key: <Paste API key here>
```

The dumped YAML object can be placed directly under the `sonarr` configuration block, or used as an [instance-specific configuration](../../configuration.md#multiple-instances-of-the-same-type).

Most values are explicitly defined in this dumped configuration, ensuring that when used with Buildarr, the configuration will always remain static.

```yaml
api_key: 1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d
hostname: localhost
port: 8989
protocol: http
settings:
  connect:
    definitions:
      Trakt:
        access_token: 1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b
        auth_user: example
        expires: '2023-05-10T15:34:08.117451+00:00'
        notification_triggers:
          include_health_warnings: false
          on_application_update: false
          on_episode_file_delete: true
          on_episode_file_delete_for_upgrade: true
          on_grab: false
          on_health_issue: false
          on_import: true
          on_rename: false
          on_series_delete: true
          on_upgrade: true
        refresh_token: 1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b
        tags: []
  download_clients:
    definitions:
      Transmission:
        add_paused: false
        category: sonarr
        directory: null
        enable: true
        host: transmission
        older_priority: last
        password: null
        port: 9091
        priority: 1
        recent_priority: last
        remove_completed_downloads: true
        remove_failed_downloads: true
        tags: []
        url_base: /transmission/
        use_ssl: false
        username: null
    enable_completed_download_handling: true
    redownload_failed: true
    remote_path_mappings:
      definitions: []
  general:
    analytics:
      send_anonymous_usage_data: true
    backup:
      folder: Backups
      interval: 7
      retention: 28
    host:
      bind_address: '*'
      instance_name: Sonarr (Example)
      port: 8989
      ssl_port: 9898
      url_base: null
      use_ssl: false
    logging:
      log_level: INFO
    proxy:
      bypass_proxy_for_local_addresses: true
      enable: false
      hostname: null
      ignored_addresses: []
      password: null
      port: 8080
      proxy_type: http
      username: null
    security:
      authentication: none
      certificate_validation: enabled
      password: null
      username: null
    updates:
      automatic: false
      branch: main
      mechanism: docker
      script_path: null
  import_lists:
    definitions: {}
  indexers:
    definitions: {}
    maximum_size: 0
    minimum_age: 0
    retention: 0
    rss_sync_interval: 15
  media_management:
    analyze_video_files: true
    anime_episode_format: '{Series TitleYear} - S{season:00}E{episode:00} - {absolute:000}
      - {Episode CleanTitle} {[Preferred Words]} {[Quality Full]} {[MediaInfo VideoDynamicRangeType]}
      [{MediaInfo VideoBitDepth}bit] {[MediaInfo VideoCodec]} [{Mediainfo AudioCodec}
      { Mediainfo AudioChannels}]{MediaInfo AudioLanguages} {[Release Group]} - Default'
    change_file_date: none
    chmod_folder: drwxr-xr-x
    chown_group: null
    create_empty_series_folders: false
    daily_episode_format: '{Series TitleYear} - {Air-Date} - {Episode CleanTitle}
      - {[Preferred Words]} {[Quality Full]} {[MediaInfo VideoDynamicRangeType]} [{MediaInfo
      VideoBitDepth}bit] {[MediaInfo VideoCodec]} [{Mediainfo AudioCodec} {Mediainfo
      AudioChannels}] {[MediaInfo AudioLanguages]} {[Release Group]} - Default'
    delete_empty_folders: false
    episode_title_required: always
    import_extra_files: false
    minimum_free_space: 100
    multiepisode_style: range
    propers_and_repacks: do-not-prefer
    recycling_bin: null
    recycling_bin_cleanup: 7
    rename_episodes: true
    replace_illegal_characters: true
    rescan_series_folder_after_refresh: always
    root_folders: []
    season_folder_format: Season {season:00}
    series_folder_format: '{Series TitleYear} [imdbid-{ImdbId}]'
    set_permissions: false
    skip_free_space_check: false
    specials_folder_format: Specials
    standard_episode_format: '{Series TitleYear} - S{season:00}E{episode:00} - {Episode
      CleanTitle} - {[Preferred Words]} {[Quality Full]} {[MediaInfo VideoDynamicRangeType]}
      [{MediaInfo VideoBitDepth}bit] {[MediaInfo VideoCodec]} [{Mediainfo AudioCodec}
      {Mediainfo AudioChannels}] {[MediaInfo AudioLanguages]} {[Release Group]} -
      Default'
    use_hardlinks: true
  metadata:
    kodi_emby:
      enable: false
      episode_images: true
      episode_metadata: true
      season_images: true
      series_images: true
      series_metadata: true
      series_metadata_url: true
    roksbox:
      enable: false
      episode_images: true
      episode_metadata: true
      season_images: true
      series_images: true
    wdtv:
      enable: false
      episode_images: true
      episode_metadata: true
      season_images: true
      series_images: true
  profiles:
    delay_profiles:
      definitions:
      - bypass_if_highest_quality: true
        preferred_protocol: usenet-prefer
        tags: []
        torrent_delay: 0
        usenet_delay: 0
    language_profiles:
      definitions:
        Shows:
          languages:
          - english
          upgrade_until: english
          upgrades_allowed: true
    quality_profiles:
      definitions:
        SD/HD:
          qualities:
          - Bluray-1080p
          - members:
            - WEBDL-1080p
            - WEBRip-1080p
            name: WEB 1080p
          - HDTV-1080p
          - Bluray-720p
          - members:
            - WEBDL-720p
            - WEBRip-720p
            name: WEB 720p
          - HDTV-720p
          - Raw-HD
          - Bluray-480p
          - DVD
          - members:
            - WEBDL-480p
            - WEBRip-480p
            name: WEB 480p
          - SDTV
          upgrade_until: Bluray-1080p
          upgrades_allowed: true
    release_profiles:
      definitions:
        '[Trash] Low Quality Groups':
          enable: true
          include_preferred_when_renaming: false
          indexer: null
          must_contain: []
          must_not_contain: []
          preferred:
          - score: -10000
            term: /(-BRiNK|-CHX|-GHOSTS|-EVO|-FGT|JFF|PSA|MeGusta|-NERO|nhanc3|Pahe\.ph|Pahe\.in|TBS|-VIDEOHOLE|-worldmkv|-XLF)\b/i
          tags: []
        '[Trash] Optionals':
          enable: true
          include_preferred_when_renaming: false
          indexer: null
          must_contain: []
          must_not_contain:
          - /^(?=.*(1080|720))(?=.*((x|h)[ ._-]?265|hevc)).*/i
          - /\b(-alfaHD|-BAT|-BNd|-C\.A\.A|-Cory|-EXTREME|-FF|-FOXX|-G4RiS|-GUEIRA|-N3G4N|-PD|-PTHome|-RiPER|-RK|-SiGLA|-Tars|-WTV|-Yatogam1|-YusukeFLA|-ZigZag)\b/i
          - /\b(-scene)\b/i
          - /^(?!.*(HDR|HULU|REMUX))(?=.*\b(DV|Dovi|Dolby[- .]?Vision)\b).*/i
          - /\bAV1\b/i
          - /^(?!.*(web[ ]dl|-deflate|-inflate))(?=.*([_. ]WEB[_. ]|-CAKES\b|-GGEZ\b|-GGWP\b|-GLHF\b|-GOSSIP\b|-KOGI\b|-PECULATE\b|-SLOT\b)).*/i
          preferred:
          - score: 15
            term: /\bS\d+\b(?!E\d+\b)/i
          - score: -10000
            term: /(-4P|-4Planet|-AsRequested|-BUYMORE|-CAPTCHA|-Chamele0n|-GEROV|-iNC0GNiTO|-NZBGeek|-Obfuscated|-postbot|-Rakuv|-Scrambled|-WhiteRev|-WRTEAM|-xpost)\b/i
          - score: -10000
            term: /(?<!\d\.)(1-.+)$/i
          - score: -10000
            term: /(\[rartv\]|\[rarbg\]|\[eztv\]|\[TGx\])/i
          - score: -10000
            term: /\s?\ben\b$/i
          tags: []
        '[Trash] P2P Groups + Repack/Proper':
          enable: true
          include_preferred_when_renaming: false
          indexer: null
          must_contain: []
          must_not_contain: []
          preferred:
          - score: 1800
            term: /(-deflate|-inflate)\b/i
          - score: 1700
            term: /(-ABBIE|-AJP69|-APEX|-CasStudio|CRFW|-CtrlHD|-FLUX|\bHONE|-KiNGS|-monkee|NOSiViD|-NTb|-NTG|-PAXA|-PEXA|-QOQ|-RTN|-SiC|T6D|-TOMMY|-ViSUM|-XEPA)\b/i
          - score: 1650
            term: /(3CTWeB|BLUTONiUM|-BTW|-Chotab|-Cinefeel|-CiT|Coo7|-dB|-DEEP|-END|-ETHiCS|-FC|-Flights|-GNOME|-iJP|-iKA|-iT00NZ|-JETIX|-KHN|-KiMCHI|-LAZY|-MZABI|-NPMS|-NYH|-orbitron|playWEB|PSiG|-ROCCaT|RTFM|-SA89|-SDCC|-SIGMA|-SMURF|-SPiRiT|-TEPES|-TVSmash|-WELP)\b/i
          - score: 1600
            term: /(-DRACULA|SLiGNOME|T4H|-ViSiON|SwAgLaNdEr)\b/i
          - score: 13
            term: /(repack3)/i
          - score: 12
            term: /(repack2)/i
          - score: 11
            term: /\b(repack|proper)\b/i
          tags: []
        '[Trash] Release Sources (Streaming Service)':
          enable: true
          include_preferred_when_renaming: true
          indexer: null
          must_contain: []
          must_not_contain: []
          preferred:
          - score: 100
            term: /\b(amzn|amazon)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 100
            term: /\b(atvp|aptv|Apple TV\+)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 95
            term: /\b(sho|showtime)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 90
            term: /\b(dsnp|dsny|disney|Disney\+)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 90
            term: /\b(hmax|hbom|hbo[ ._-]max)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 90
            term: /\b(nf|netflix)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 90
            term: /\b(qibi|quibi)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 85
            term: /\b(hulu)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 85
            term: /\b(pcok|Peacock TV)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(dcu)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(hbo)(?![ ._-]max)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(it)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(nlz)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(pmtp)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(red)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(stan)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          - score: 75
            term: /\b(vdl)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i
          tags: []
  quality:
    definitions:
      Bluray-1080p:
        max: 227.0
        min: 50.4
        title: null
      Bluray-1080p Remux:
        max: null
        min: 69.1
        title: null
      Bluray-2160p:
        max: null
        min: 94.6
        title: null
      Bluray-2160p Remux:
        max: null
        min: 204.4
        title: null
      Bluray-480p:
        max: 100.0
        min: 2.0
        title: null
      Bluray-720p:
        max: 137.3
        min: 17.1
        title: null
      DVD:
        max: 100.0
        min: 2.0
        title: null
      HDTV-1080p:
        max: 137.3
        min: 15.0
        title: null
      HDTV-2160p:
        max: 350.0
        min: 50.4
        title: null
      HDTV-720p:
        max: 67.5
        min: 10.0
        title: null
      Raw-HD:
        max: null
        min: 4.0
        title: null
      SDTV:
        max: 100.0
        min: 2.0
        title: null
      Unknown:
        max: 199.9
        min: 1.0
        title: null
      WEBDL-1080p:
        max: 137.3
        min: 15.0
        title: null
      WEBDL-2160p:
        max: 350.0
        min: 50.4
        title: null
      WEBDL-480p:
        max: 100.0
        min: 2.0
        title: null
      WEBDL-720p:
        max: 137.3
        min: 10.0
        title: null
      WEBRip-1080p:
        max: 137.3
        min: 15.0
        title: null
      WEBRip-2160p:
        max: 350.0
        min: 50.4
        title: null
      WEBRip-480p:
        max: 100.0
        min: 2.0
        title: null
      WEBRip-720p:
        max: 137.3
        min: 10.0
        title: null
  tags:
    definitions: []
  ui:
    enable_color_impaired_mode: false
    first_day_of_week: sunday
    long_date_format: day-first
    short_date_format: word-month-second
    show_relative_dates: true
    time_format: twentyfour-hour
    week_column_header: day-first
version: 3.0.9.1549
```

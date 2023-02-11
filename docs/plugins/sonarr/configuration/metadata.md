# Metadata

Sonarr can output metadata alongside media files in a variety of formats to suit the media playing being users.

Multiple of these can be configured at a time.

To enable a metadata format, set `enable` to `true` in the configuration block in Buildarr.

## Kodi (XBMC) / Emby

##### ::: buildarr.plugins.sonarr.config.metadata.KodiEmbyMetadata
    options:
      members:
        - series_metadata
        - series_metadata_url
        - episode_metadata
        - series_images
        - season_images
        - episode_images
      show_root_heading: false
      show_source: false

## Roksbox

##### ::: buildarr.plugins.sonarr.config.metadata.RoksboxMetadata
    options:
      members:
        - episode_metadata
        - series_images
        - season_images
        - episode_images
      show_root_heading: false
      show_source: false

## WDTV

##### ::: buildarr.plugins.sonarr.config.metadata.WdtvMetadata
    options:
      members:
        - episode_metadata
        - series_images
        - season_images
        - episode_images
      show_root_heading: false
      show_source: false

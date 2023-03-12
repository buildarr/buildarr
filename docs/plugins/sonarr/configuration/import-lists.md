# Import Lists

##### ::: buildarr.plugins.sonarr.config.import_lists.SonarrImportListsSettingsConfig
    options:
      members:
        - delete_unmanaged
        - delete_unmanaged_exclusions
        - definitions
        - exclusions
      show_root_heading: false
      show_source: false

## Configuring import lists

The following

##### ::: buildarr.plugins.sonarr.config.import_lists.ImportList
    options:
      members:
        - enable_automatic_add
        - monitor
        - root_folder
        - quality_profile
        - language_profile
        - series_type
        - season_folder
        - tags
      show_root_heading: false
      show_source: false

## Sonarr

##### ::: buildarr.plugins.sonarr.config.import_lists.SonarrImportList
    options:
      members:
        - type
        - instance_name
        - full_url
        - api_key
        - source_quality_profiles
        - source_language_profiles
        - source_tags
      show_root_heading: false
      show_source: false

## Plex

##### ::: buildarr.plugins.sonarr.config.import_lists.PlexWatchlistImportList
    options:
      members:
        - type
        - access_token
      show_root_heading: false
      show_source: false

## Trakt

##### ::: buildarr.plugins.sonarr.config.import_lists.TraktImportList
    options:
      members:
        - access_token
        - refresh_token
        - expires
        - auth_user
        - rating
        - username
        - genres
        - years
        - limit
        - trakt_additional_parameters
      show_root_heading: false
      show_source: false

### List

##### ::: buildarr.plugins.sonarr.config.import_lists.TraktListImportList
    options:
      members:
        - type
        - list_name
      show_root_heading: false
      show_source: false

### Popular List

##### ::: buildarr.plugins.sonarr.config.import_lists.TraktPopularlistImportList
    options:
      members:
        - type
        - list_type
      show_root_heading: false
      show_source: false

### User

##### ::: buildarr.plugins.sonarr.config.import_lists.TraktUserImportList
    options:
      members:
        - type
        - list_type
      show_root_heading: false
      show_source: false

# Quality Profiles

Quality profiles determine the allowed quality levels for media, and the behaviour of how to upgrade media files if higher quality versions become available.

Within a quality profile you set upgrade settings, the maximum quality level to automatically upgrade media to, the allowed quality levels, and the priority given to those quality levels.

```yaml
sonarr:
  settings:
    profiles:
      quality_profiles:
        # Set to `true` or `false` as desired. (Default `false`)
        delete_unmanaged: true
        definitions:
          # Add Quality profiles here.
          # The name of the block becomes the name of the quality profile.
          SDTV:
            upgrades_allowed: true
            upgrade_until: "Bluray-1080p"
            # Highest priority quality first, lowest priority goes last.
            qualities:
              - "Bluray-480p"
              - "DVD"
              - name: "WEB 480p"
                members:
                  - "WEBDL-480p"
                  - "WEBRip-480p"
              - "SDTV"
          # Add additional quality profiles here as needed.
```

In Buildarr, quality profiles are defined using a dictonary structure. The quality levels listed in the `qualities` attribute are the qualities to enable, and are prioritised from first to last (top to bottom). Quality groups, where multiple qualities are given the same priority level, can also be defined.

## General configuration

##### ::: buildarr.plugins.sonarr.config.profiles.quality.SonarrQualityProfilesSettingsConfig
    options:
      members:
        - delete_unmanaged
        - definitions
      show_root_heading: false
      show_source: false

## Creating a quality profile

##### ::: buildarr.plugins.sonarr.config.profiles.quality.QualityProfile
    options:
      members:
        - upgrades_allowed
        - upgrade_until
        - qualities
      show_root_heading: false
      show_source: false

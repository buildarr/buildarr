# Delay Profiles

Delay profiles allow you to reduce the number of releases that will be downloaded for an episode by adding a delay while Sonarr continues to watch for releases that better match your preferences.

```yaml
sonarr:
  settings:
    profiles:
      delay_profiles:
        # Set to `true` or `false` as desired. (Default `false`)
        # Works a bit differently to other profile types, see
        # the `delete_unmanaged` attribute docs.
        delete_unmanaged: true
        definitions:
          # Ordered in priority, highest priority first.
          - preferred_protocol: "usenet-prefer"
            usenet_delay: 0
            torrent_delay: 0
            bypass_if_highest_quality: true
            tags:
              - "tv-shows"
          # Add additional delay profiles here as needed.
          ...
          # Default delay profile goes last, and MUST be defined
          # if you have defined any other delay profiles.
          - preferred_protocol: "torrent-prefer"
            usenet_delay: 1440
            torrent_delay: 1440
            bypass_if_highest_quality: false
            # Tags will be ignored for default delay profile.
```

In Buildarr, due to the unique way how delay profiles work, they are defined using an ordered list structure, prioritised from first to last (top to bottom). The last delay profile in the list is assumed to be the default delay profile. Every non-default delay profile must have tags defined, and the default delay profile must have no tags defined.

For more information, see this guide from [WikiArr](https://wiki.servarr.com/sonarr/settings#language-profiles).

## General configuration

##### ::: buildarr.plugins.sonarr.config.profiles.delay.SonarrDelayProfilesSettingsConfig
    options:
      members:
        - delete_unmanaged
        - definitions
      show_root_heading: false
      show_source: false

## Creating a delay profile

##### ::: buildarr.plugins.sonarr.config.profiles.delay.DelayProfile
    options:
      members:
        - preferred_protocol
        - usenet_delay
        - torrent_delay
        - bypass_if_highest_quality
        - tags
      show_root_heading: false
      show_source: false

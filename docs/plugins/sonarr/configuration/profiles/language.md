# Language Profiles

Language profiles define preferred audio languages for media files, and tell Sonarr how media files should be upgraded if a more preferred language version becomes available.

```yaml
sonarr:
  settings:
    profiles:
      language_profiles:
        definitions:
          # Add language profiles here.
          # The name of the block becomes the name of the quality profile.
          Anime:
            upgrades_allowed: true
            upgrade_until: "Japanese"
            # Highest priority quality first, lowest priority goes last.
            languages:
              - "Japanese"
              - "English"
          # Add additional language profiles here as needed.
```

In Buildarr, language profiles are defined using a dictonary structure. The languages listed in the `languages` attribute are enabled, and prioritised from first to last (top to bottom). Languages not in this list are not selected for download.

For more information, see this guide from [WikiArr](https://wiki.servarr.com/sonarr/settings#language-profiles).

## General configuration

##### ::: buildarr.plugins.sonarr.config.profiles.language.SonarrLanguageProfilesSettingsConfig
    options:
      members:
        - delete_unmanaged
        - definitions
      show_root_heading: false
      show_source: false

## Creating a language profile

##### ::: buildarr.plugins.sonarr.config.profiles.language.LanguageProfile
    options:
      members:
        - upgrades_allowed
        - upgrade_until
        - languages
      show_root_heading: false
      show_source: false

## Available languages

##### ::: buildarr.plugins.sonarr.config.profiles.language.Language
    options:
      show_root_heading: false
      show_source: false

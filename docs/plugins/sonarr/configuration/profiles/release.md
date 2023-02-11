# Release Profiles

Release profiles are used to select releases to download that best fit the criteria for what you want to retrieve for your media library.

Since not all releases are created equal, and each release group has their own way of packaging and encoding their material, being able to dial-in what Sonarr selects is important to getting good results.

```yaml
sonarr:
  settings:
    profiles:
      release_profiles:
        definitions:
          Example:
            must_contain:
              - '\.*\.mkv$/i'
            must_not_contain:
              - '-FAKEGROUP'
            preferred:
              - term: '/\b(amzn|amazon)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i'
                score: 100
              - term: '/(-BRiNK|-CHX|-GHOSTS|-EVO|)\b/i'
                score: -10000
          Release Sources (Streaming Service):
            trash_id: 1B018E0C53EC825085DD911102E2CA36
          P2P Groups + Repack/Proper:
            trash_id: 71899E6C303A07AF0E4746EFF9873532
```

In Buildarr, release profiles are defined using a dictonary structure. Each profile has either a set of
filters determining the kind of releases that should be prioritised (or ignored),
or a reference to an external provider of pre-made release profiles like TRaSH-Guides.

For more information on release profiles, refer to this page on
[WikiArr](https://wiki.servarr.com/sonarr/settings#release-profiles).

## General configuration

##### ::: buildarr.plugins.sonarr.config.profiles.release.SonarrReleaseProfilesSettingsConfig
    options:
      members:
        - delete_unmanaged
        - definitions
      show_root_heading: false
      show_source: false

## Creating a release profile

Release profiles are defined in Sonarr like this.

```yaml
sonarr:
  settings:
    profiles:
      release_profiles:
        definitions:
          Example:
            must_contain:
              - '\.*\.mkv$/i'
            must_not_contain:
              - '-FAKEGROUP'
            preferred:
              - term: '/\b(amzn|amazon)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i'
                score: 100
              - term: '/(-BRiNK|-CHX|-GHOSTS|-EVO|)\b/i'
                score: -10000
```

The below attributes are common to all release profiles.

##### ::: buildarr.plugins.sonarr.config.profiles.release.ReleaseProfile
    options:
      members:
        - enable
        - include_preferred_when_renaming
        - indexer
        - tags
      show_root_heading: false
      show_source: false

## Manually defining filters

When not importing release profiles from external sources like TRaSH-Guides,
settings for how to prefer and ignore releases must be defined within
the release profile using the following parameters.

##### ::: buildarr.plugins.sonarr.config.profiles.release.ReleaseProfile
    options:
      members:
        - must_contain
        - must_not_contain
        - preferred
      show_root_heading: false
      show_source: false

## Importing release profiles from TRaSH-Guides

TRaSH-Guides maintains a list of release profiles for a variety of use cases.

* [Release Profile RegEx (WEB-DL)](https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx/)
* [Release Profile RegEx (Anime)](https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx-Anime/)

Buildarr supports downloading these release profiles from the
[TRaSH-Guides metadata repository](https://github.com/TRaSH-/Guides/tree/master/docs/json/sonarr/rp),
and pushing the latest changes to Sonarr directly, without having to manually input them.

```yaml
sonarr:
  settings:
    profiles:
      release_profiles:
        definitions:
          Release Sources (Streaming Service):
            trash_id: 1B018E0C53EC825085DD911102E2CA36
          P2P Groups + Repack/Proper:
            trash_id: 71899E6C303A07AF0E4746EFF9873532
```

When using imported release profiles, the filters within the release profile itself cannot be modified,
but there are some customisation options that alter how Buildarr interprets them.
These are identical to the customisation options for release profiles
provided by
[Recyclarr](https://recyclarr.dev/wiki/yaml/config-reference#release-profile-settings).

##### ::: buildarr.plugins.sonarr.config.profiles.release.ReleaseProfile
    options:
      members:
        - trash_id
        - filter
        - strict_negative_scores
      show_root_heading: false
      show_source: false

## TRaSH-Guides release profile import examples

Here are some examples of importing well used release profiles from TRaSH-Guides.

##### Release Profile RegEx (WEB-DL)

```yaml
sonarr:
  settings:
    profiles:
      release_profiles:
        definitions:
          Release Sources (Streaming Service):
            trash_id: 1B018E0C53EC825085DD911102E2CA36
          P2P Groups + Repack/Proper:
            trash_id: 71899E6C303A07AF0E4746EFF9873532
          Low Quality Groups:
            trash_id: EBC725268D687D588A20CBC5F97E538B
          Optionals:
            trash_id: 76e060895c5b8a765c310933da0a5357
            filter:
              include:
                - ea83f4740cec4df8112f3d6dd7c82751 # Prefer Season Packs
                - 6f2aefa61342a63387f2a90489e90790 # Dislike renamed/retagged releases
                - 19cd5ecc0a24bf493a75e80a51974cdd # Dislike retagged/obfuscated groups
                - 6a7b462c6caee4a991a9d8aa38ce2405 # Dislike release ending: en
                - 236a3626a07cacf5692c73cc947bc280 # Dislike release containing: 1-
                - cec8880b847dd5d31d29167ee0112b57 # Ignore 720p/1080p HEVC re-encodes (Golden Rule)
                - 436f5a7d08fbf02ba25cb5e5dfe98e55 # Ignore Dolby Vision without HDR10 fallback
                - f3f0f3691c6a1988d4a02963e69d11f2 # Ignore The Group -SCENE
                - 5bc23c3a055a1a5d8bbe4fb49d80e0cb # Ignore so-called scene releases
                - 538bad00ee6f8aced8e0db5218b8484c # Ignore Bad Dual Audio Groups
                - 4861d8238f9234606df6721df6e27deb # Ignore AV1
```

##### Release Profile RegEx (Anime)

```yaml
sonarr:
  settings:
    profiles:
      release_profiles:
        definitions:
          Anime Profile 1:
            #   * Prefer uncensored
            #   * Prefer Multi-Audio or Dual-Audio
            # https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx-Anime/#first-release-profile
            trash_id: d428eda85af1df8904b4bbe4fc2f537c
            strict_negative_scores: true
          Anime Profile 2:
            # Prioritise/ignore releases based on group.
            # You may need to adjust the profile based on actual results.
            # https://trash-guides.info/Sonarr/Sonarr-Release-Profile-RegEx-Anime/#second-release-profile
            trash_id: 6cd9e10bb5bb4c63d2d7cd3279924c7b
            strict_negative_scores: true
```

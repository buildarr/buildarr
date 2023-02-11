# Quality

##### ::: buildarr.plugins.sonarr.config.quality.SonarrQualitySettingsConfig
    options:
      members:
        - trash_id
        - definitions
      show_root_heading: false
      show_source: false

## Setting quality definitions

##### ::: buildarr.plugins.sonarr.config.quality.QualityDefinition
    options:
      members:
        - title
        - min
        - max
      show_root_heading: false
      show_source: false

## TRaSH-Guides quality definition profiles

TRaSH-Guides quality definition profiles for Sonarr are tracked
[here](https://github.com/TRaSH-/Guides/tree/master/docs/json/sonarr/quality-size).

Trash IDs:

* `bef99584217af744e404ed44a33af589` (Series)
* `387e6278d8e06083d813358762e0ac63` (Anime)

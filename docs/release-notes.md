# Release Notes

## [v0.1.2](https://github.com/buildarr/buildarr/releases/tag/v0.1.2) - 2023-02-20

This is a bugfix release that fixes updates of certain types of Sonarr instance configuration, improving usability of the Sonarr plugin.

The following types of Sonarr instance configuration have had bugfixes and improvements made, and are confirmed to work without errors:

* Media Management
    * Ensure that `minimum_free_space` is set to a minimum of 100 MB
    * Fix `unmonitor_deleted_episodes` so that it is now checked and updated by Buildarr
    * Add a `delete_unmanaged_root_folders` option to allow Buildarr to delete undefined root folders (disabled by default)
    * Improve other configuration constraints so that it more closely matches Sonarr
    * Fix a minor logging bug in root folder updates
* Profiles
    * Quality Profiles / Language Profiles
        * Improve attribute constraints e.g. ensure duplicate quality values cannot be defined, enforce `upgrade_until` being required when `allow_upgrades` is `True`
        * Fix conversion between Buildarr and Sonarr configuration state so that no errors occur when upgrades are disabled
        * Internal refactor to make the code easier to understand
    * Delay Profiles - Confirmed to work properly as of `v0.1.1` (and likely `v0.1.0`)
    * Release Profiles
        * Fix bug introduced in `v0.1.1` where internal validation is not done on release profiles downloaded from TRaSH-Guides, resulting in preferred word lists being updated on each run, and potential errors not being caught if there are invalid values in the profile
        * Internal refactor to simplify implementation
* Quality
    * Fix bug introduced in `v0.1.1` where internal validation is not done on quality profiles downloaded from TRaSH-Guides, resulting in potential errors not being caught if there are invalid values in the profile
* Metadata - Confirmed to work properly as of `v0.1.1` (and likely `v0.1.0`)
    * Small logging bug fixed where it was ambiguous which metadata type was being modified on update
* Tags - Confirmed to work properly as of `v0.1.1` (and likely `v0.1.0`)
* General
    * Improve behaviour when setting an authentication username and password so that configuration updates are idempotent when authentication is disabled
    * Fix setting a proxy password
    * Fix setting backup intervals and retentions so that it is no longer possible to set a value not supported by Sonarr

Incorrect syntax in some examples in the documentation were also found and fixed.

### Added

* Added the `sonarr.settings.media_management.delete_unmanaged_root_folders` configuration attribute ([#24](https://github.com/buildarr/buildarr/pull/24))

### Changed

* Improve and fix Sonarr general settings configuration updates ([#19](https://github.com/buildarr/buildarr/pull/19))
* Fix Sonarr UI settings updates ([#20](https://github.com/buildarr/buildarr/pull/20))
* Fix small bug Sonarr metadata definition update logging ([#21](https://github.com/buildarr/buildarr/pull/21))
* Improve Sonarr quality profile definition parsing ([#22](https://github.com/buildarr/buildarr/pull/22))
* Make improvements and bug fixes to quality/language/release profile and quality definition parsing ([#23](https://github.com/buildarr/buildarr/pull/23))
* Fix Sonarr media management settings and improve root folder handling ([#24](https://github.com/buildarr/buildarr/pull/24))


## [v0.1.1](https://github.com/buildarr/buildarr/releases/tag/v0.1.1) - 2023-02-19

This is a support release that fixes quality definition and backup configuration updates
on remote Sonarr instances.

A new Dummy plugin is now included with Buildarr, used for testing Buildarr and its
plugin API, and also serves as a reference implementation for plugin developers.

Other behind-the-scenes improvements include a refactor of the plugin API to allow
for accurate type hints for configuration objects in secrets metadata classes
(and vice versa), and numerous updates to the documentation to correct errors
and add more detail.

### Added

* Add a GitHub Action to push releases to PyPI ([#11](https://github.com/buildarr/buildarr/pull/11))
* Create a `buildarr-dummy` plugin for testing the Buildarr plugin API ([#12](https://github.com/buildarr/buildarr/pull/12))

### Changed

* Fix $PUID and $GUID declarations ([b5110f3](https://github.com/buildarr/buildarr/commit/b5110f3))
* Fix Docker Hub link ([be0ba12](https://github.com/buildarr/buildarr/commit/be0ba12))
* Fix Docker volume mount docs ([fe328aa](https://github.com/buildarr/buildarr/commit/fe328aa))
* Fix troubleshooting Buildarr run docs ([e3b8833](https://github.com/buildarr/buildarr/commit/e3b8833))
* Update dependency versions ([3c19ede](https://github.com/buildarr/buildarr/commit/3c19ede))
* Fix debug Docker command in the GitHub Pages site ([1e17741](https://github.com/buildarr/buildarr/commit/1e17741))
* Disable automatic dependency version updates ([c5c61cd](https://github.com/buildarr/buildarr/commit/c5c61cd))
* Add missing download client documentation ([d07936f](https://github.com/buildarr/buildarr/commit/d07936f))
* Fix incorrect config value definition in docs ([d1807a0](https://github.com/buildarr/buildarr/commit/d1807a0))
* Fix to-do list indenting ([bca56e5](https://github.com/buildarr/buildarr/commit/bca56e5))
* Add a link to the configuration documentation in README.md ([a5c0e6d](https://github.com/buildarr/buildarr/commit/a5c0e6d))
* Clean up and update Sonarr plugin internals ([#14](https://github.com/buildarr/buildarr/pull/14))
* Fix updates to Sonarr quality definitions ([#15](https://github.com/buildarr/buildarr/pull/15))
* Fix updates to Sonarr backup general settings ([#16](https://github.com/buildarr/buildarr/pull/16))

### Removed

* Removed `buildarr.__version__` (please use [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#distribution-versions) instead)


## [v0.1.0](https://github.com/buildarr/buildarr/releases/tag/v0.1.0) - 2023-02-11

Release the initial version of Buildarr (v0.1.0).

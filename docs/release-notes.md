# Release Notes (Buildarr Core)

## [v0.4.2](https://github.com/buildarr/buildarr/releases/tag/v0.4.2) - 2023-04-14

This is a backwards-compatible feature and bugfix release.

This release mainly introduces new behind-the-scenes plugin API functionality to accommodate for new Buildarr plugins currently in development.

* Add a new generic rendering stage to Buildarr runs for populating dynamic configuration attributes (e.g. TRaSH-Guides metadata), that is not specific to TRaSH-Guides metadata.
    * The current TRaSH-Guides metadata rendering function is now deprecated, and scheduled to be removed in Buildarr v0.5.0.
* Add a new stage to Buildarr runs for initialising new instances (e.g. with admin credentials or environment settings), that runs after rendering dynamic configuration attributes, but before secrets or remote configuration fetching takes place.
    * This is intended to be used if an application requires initialising before the main API can be used by Buildarr, even before secrets metadata can be checked/fetched.
* Add a new stage to Buildarr runs for deleting resources from the remote instance if they are not managed by Buildarr or unused, and deletion is allowed in the configuration.
    * This runs after the main configuration update stage, and improves stability of resource deletions by performing them in the reverse instance dependency order, ensuring resources that require resources on another instance are removed first.
    * Any plugins that perform resource deletions are expected to move this functionality to this new Buildarr run stage.

Some bugs that are likely to be encountered when setting up a complex Arr stack with linked instances have also been fixed:

* Partially fix an issue where attributes of the integer enumeration type (`BaseIntEnum`) were not properly handled, resulting in strange logging and potentially validation errors.
    * Since it is not feasible to fully resolve the issue, the `BaseIntEnum` type is now deprecated, and scheduled to be removed in Buildarr v0.5.0.
* Allow the default instance of an application plugin (a configuration specified without using `instances:`) to be referenced in instance links, by specifying the reserved `default` instance name.
    * A validation check has been added to disallow the user from defining an instance-specific configuration named `default`, as that is now (and always has been) a reserved name with respect to instance names in Buildarr.
* Fix an issue where some non-empty data structure types were not evaluated properly when reading the active configuration of a remote instance, resulting in a Buildarr internal error.

### Added

* Add Buildarr run stage for initialising new instances ([#99](https://github.com/buildarr/buildarr/pull/99))
* Add generic configuration rendering stage ([#101](https://github.com/buildarr/buildarr/pull/101))
* Add resource deletion stage after configuration updates ([#102](https://github.com/buildarr/buildarr/pull/102))

### Changed

* Deprecate `BaseIntEnum` ([#95](https://github.com/buildarr/buildarr/pull/95))
* Allow the default instance to be used in instance links ([#98](https://github.com/buildarr/buildarr/pull/98))
* Update development dependencies ([#103](https://github.com/buildarr/buildarr/pull/103))
* Fix default config attribute decoder type discovery ([#105](https://github.com/buildarr/buildarr/pull/105))
* Delete resources using the reverse execution order ([#106](https://github.com/buildarr/buildarr/pull/106))


## [v0.4.1](https://github.com/buildarr/buildarr/releases/tag/v0.4.1) - 2023-04-09

This is a backwards-compatible feature and bugfix release that resolves some issues when running Buildarr in a Docker container, and other small bugs.

* A bug was fixed where Buildarr would not always detect configuration file changes in the Docker environment, particularly if run in Docker Desktop or Docker on WSL2.
* The default settings for the YAML encoder for configurations were adjusted, changing the configuration attribute order to be closer to the intended order, and making automatically generated configuration easier to read.
* The documentation has been updated to note the release of the [Prowlarr plugin for Buildarr](https://buildarr.github.io/plugins/prowlarr), and the installation instructions for the Docker image have been extended to reflect changes in the way the Docker container can be used.
* The plugin API has been extended to add a hook for overriding the function that Buildarr uses to compare local and remote configuration attribute values, for when custom code for that is required.

### Added

* Add overriding the value compare function to remote maps ([#84](https://github.com/buildarr/buildarr/pull/84))

### Changed

* Fix config file monitoring in the Docker container ([#82](https://github.com/buildarr/buildarr/pull/82))
* Fix mistakes in error messages ([#85](https://github.com/buildarr/buildarr/pull/85))
* Update Buildarr docs ([#87](https://github.com/buildarr/buildarr/pull/87))
* Improve built-in YAML encoding ([#88](https://github.com/buildarr/buildarr/pull/88))


## [v0.4.0](https://github.com/buildarr/buildarr/releases/tag/v0.4.0) - 2023-03-31

This is a semi backwards-incompatible feature and bugfix release that undertakes large refactors to move Buildarr closer to the final form it will take for stable release.

As major strides have been taken to stabilise the plugin API, the Sonarr plugin for Buildarr has been forked into a separate package, [`buildarr-sonarr`](https://buildarr.github.io/plugins/sonarr). From this version onwards, Buildarr no longer bundles application plugins.

The [Docker container](plugins/index.md#installing-plugins-into-the-docker-container) still bundles the Sonarr plugin for ease of use, but when upgrading an existing [standalone installation](plugins/index.md#installing-plugins-for-a-standalone-application) of Buildarr, the Sonarr plugin package will need to be installed using `pip`.

```bash
$ pip install buildarr-sonarr
```

This will allow the Sonarr plugin to deliver releases independently of the base Buildarr package, allowing for more rapid releases of both packages, while ensuring compability between Buildarr and its plugins through plugin version pinning of the Buildarr base package.

Buildarr uses [semantic versioning](https://semver.org).

While Buildarr is in beta, point releases (e.g. `0.x.0`) signify there may be a breaking change to the plugin API, which plugins should accommodate with corresponding changes and adjustment of their dependency requirements.

After Buildarr releases its first stable version (`v1.0.0`), major version increases (e.g. `v2.0.0`) will be used for backward-incompatible releases, while point releases (e.g. `v1.x.0`) will be made for backward-compatible feature releases.

A number of other features and bugfixes have been added in this release:

* Add support for dry runs in Buildarr ad-hoc runs, for testing configuration changes against live instances *without* modifying them
* Add [configuration validity testing](usage.md#testing-configuration) using the `buildarr test-config` command
* Add support for [overriding the secrets file](configuration.md#buildarr.config.buildarr.BuildarrConfig.secrets_file_path) path using the `--secrets-file` option
* Add [automatic generation of Docker Compose files](usage.md#generating-a-docker-compose-file) from Buildarr configuration files using the `buildarr compose` command
* Improve configuration parsing so that local relative paths read by Buildarr are resolved relative to the parent directory of the file the attribute was read from, rather than the current directory of the Buildarr process
* Improve validation to output easier-to-read error messages in some cases
* Improve logging so that it is clearer what source file the log message came from, and what plugin and instance name the message relates to
* Relax Buildarr base package dependency version requirements, for improved compatibility with external plugins

### Added

* Add the `--dry-run` option to `buildarr run` ([#56](https://github.com/buildarr/buildarr/pull/56))
* Add instance-specific configs to global state and fix Sonarr dry-run bug ([#59](https://github.com/buildarr/buildarr/pull/59))
* Add the `buildarr test-config` command ([#60](https://github.com/buildarr/buildarr/pull/60))
* Add `--secrets-file` option to daemon and run modes ([#67](https://github.com/buildarr/buildarr/pull/67))
* Add the `buildarr compose` command ([#73](https://github.com/buildarr/buildarr/pull/73))
* Reintroduce `buildarr.__version__` and use it internally ([#75](https://github.com/buildarr/buildarr/pull/75))
* Add `version` attribute to plugin metadata object ([#78](https://github.com/buildarr/buildarr/pull/78))

### Changed

* Convert most root validators to attribute-specific validators ([#54](https://github.com/buildarr/buildarr/pull/54))
* Remove unused code and fix pre-commit job ([#58](https://github.com/buildarr/buildarr/pull/58))
* Enable validating default config/secrets attribute values ([#63](https://github.com/buildarr/buildarr/pull/63))
* Reduce usage of `initialize.js` endpoints ([#66](https://github.com/buildarr/buildarr/pull/66))
* Refactor logging infrastructure ([#68](https://github.com/buildarr/buildarr/pull/68))
* Relax dependency version requirements ([#69](https://github.com/buildarr/buildarr/pull/69))
* Improve and add missing docs for new features ([#70](https://github.com/buildarr/buildarr/pull/70))
* Evaluate local paths relative to the config file ([#71](https://github.com/buildarr/buildarr/pull/71))
* Add temporary ignore for `watchdog.Observer` type hint ([#72](https://github.com/buildarr/buildarr/pull/72))
* Fork the Sonarr plugin into its own package ([#76](https://github.com/buildarr/buildarr/pull/76))


## [v0.3.0](https://github.com/buildarr/buildarr/releases/tag/v0.3.0) - 2023-03-15

This is a feature and bugfix release that extends the groundwork laid in the previous version for making Buildarr more usable, and future-proof for the planned new plugins.

A major bug where running Buildarr when `secrets.json` does not exist would result in an error, even if valid instance credentials were found, has been fixed. This would have prevented many people from trying out Buildarr, and for this I would like to apologise.

In the future automated unit tests are planned, and major refactors of the Buildarr codebase are now less likely to happen as a result of development, so bugs like this should not happen as often in the future.

The major new feature this release introduces is instance linking: the ability to define relationships between two instances.

Most of the work went into the internal implementation to make it possible to use in plugins, but one use case within the Sonarr plugin itself is now supported: [Sonarr instances using another Sonarr instance](https://buildarr.github.io/plugins/sonarr/configuration/import-lists/#sonarr) as an import list, via the new [`instance_name`](https://buildarr.github.io/plugins/sonarr/configuration/import-lists/#buildarr_sonarr.config.import_lists.SonarrImportList.instance_name) attribute.

When using this attribute, Buildarr will automatically fill in the API key attribute so you don't have to, and instead of using IDs to reference quality profiles/language profiles/tags in the source instance, names can now be used:

```yaml
sonarr:
  instances:
    sonarr-hd:
      hostname: "localhost"
      port: 8989
    sonarr-4k:
      hostname: "localhost"
      port: 8990
      settings:
        import_lists:
          definitions:
            Sonarr (HD):
              type: "sonarr"
              # Global import list options.
              root_folder: "/path/to/videos"
              quality_profile: "4K"
              language_profile: "English"
              # Sonarr import list-specific options.
              full_url: "http://sonarr:8989"
              instance_name: "sonarr-hd"
              source_quality_profiles:
                - "HD/SD"
              source_language_profiles:
                - "English"
              source_tags:
                - "shows"
```

When instance links are made, Buildarr automatically adjusts the order of execution such that the target instance is always processed before the instance linking to the target. This ensures the state of the target instance is consistent when they are both updated to establish the link.

A number of other improvements and bugfixes were made, such as:

* Fix configuration validation to allow local and non-qualified domains on all URL-type attributes (fixes `localhost` API URL references)
* Rename the following Sonarr import list attributes (and retain the old names as aliases to ensure backwards compatibility):
    * `source_quality_profile_ids` renamed to [`source_quality_profiles`](https://buildarr.github.io/plugins/sonarr/configuration/import-lists/#buildarr_sonarr.config.import_lists.SonarrImportList.source_quality_profiles)
    * `source_language_profile_ids` renamed to [`source_language_profiles`](https://buildarr.github.io/plugins/sonarr/configuration/import-lists/#buildarr_sonarr.config.import_lists.SonarrImportList.source_language_profiles)
    * `source_tag_ids` renamed to [`source_tags`](https://buildarr.github.io/plugins/sonarr/configuration/import-lists/#buildarr_sonarr.config.import_lists.SonarrImportList.source_tags)
* Fix reading the `$BUILDARR_LOG_LEVEL` environment variable to be case-insensitive
* Clean up runtime state after individual update runs in daemon mode, to ensure no state leakage into subsequent runs
* Add a new [`buildarr.request_timeout`](configuration.md#buildarr.config.buildarr.BuildarrConfig.request_timeout) configuration attribute for adjusting API request timeouts (the default is 30 seconds)
* Improve Sonarr quality definition [`min` and `max`](https://buildarr.github.io/plugins/sonarr/configuration/quality/#buildarr_sonarr.config.quality.QualityDefinition.min) validation so that `400` is also a valid value for `max`, and enforce `min`-`max` value difference constraints
* Major internal code refactor through the introduction of [Ruff](https://beta.ruff.rs/docs) to the development pipeline, fixing a large number of minor code quality issues

### Changed

* Fix fetching new instance secrets ([#44](https://github.com/buildarr/buildarr/pull/44))
* Accept local and non-qualified domain names in URLs ([#46](https://github.com/buildarr/buildarr/pull/46))
* Add instance referencing and dependency resolution ([#47](https://github.com/buildarr/buildarr/pull/47))
* Replace isort and Flake8 with Ruff and reformat source files ([#49](https://github.com/buildarr/buildarr/pull/49))


## [v0.2.0](https://github.com/buildarr/buildarr/releases/tag/v0.2.0) - 2023-02-23

This is a feature release that comprehensively refactors the internal structure of Buildarr and the plugin API, and introduces a new, formally defined global state architecture that Buildarr and plugins can utilise.

These changes improve maintainability of the codebase, allow for more accurate type validation of global state objects, make the plugin API easier to understand for developers, and pave the way for planned new features such as configuring instance-to-instance links within Buildarr.

This release also introduces connection testing of cached and auto-retrieved instance secrets, to ensure Buildarr can communicate and authenticate with instances before it tries to update them.

A handful of bugs were fixed, including but not limited to:

* Work around a parsing bug in Pydantic that causes Buildarr to error out when specifying Sonarr instance API keys in the Buildarr configuration
* More accurate resource type detection eliminating the chance of parsing errors for Sonarr import list, indexer, download client and connection definitions
* Set better constraints on some Sonarr configuration attributes:
    * To handle suboptimal configuration (e.g. ignore duplicate elements)
    * To reject invalid configuration (e.g. require at least one recipient e-mail address on Mailgun and Sendgrid connection types)

### Added

* Implement testing of cached and fetched instance secrets ([#32](https://github.com/buildarr/buildarr/pull/32))
* Refactor the internals of Buildarr to improve maintainability ([#30](https://github.com/buildarr/buildarr/pull/30))

### Changed

* Convert `Password` and `SonarrApiKey` to subclasses of `SecretStr` ([#34](https://github.com/buildarr/buildarr/pull/34))
* Fix CLI exception class inheritance ([#35](https://github.com/buildarr/buildarr/pull/35))
* Use discriminated unions to accurately determine resource type ([#36](https://github.com/buildarr/buildarr/pull/36))
* Change log types of some TRaSH logs to `INFO` ([#37](https://github.com/buildarr/buildarr/pull/37))
* Set better constraints on Sonarr configuration attributes ([#38](https://github.com/buildarr/buildarr/pull/38))


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

# Using Buildarr

Apart from the configuration, most of the interactions with Buildarr are done via the command line.

The following commands are available for Buildarr:

* `buildarr run` - Manually perform an update run on one or more instances and exit
* `buildarr daemon` - Run Buildarr forever: perform an initial update run, and then
  schedule periodic updates
* `buildarr test-config` - Test a configuration file for correctness (*New in version 0.4.0*)
* `buildarr compose` - Generate a Docker Compose file from Buildarr configuration (*New in version 0.4.0*)
* `buildarr <plugin-name> <command...>` - Ad-hoc commands defined by any loaded plugins

The verbosity of Buildarr logging output can be adjusted using the `--log-level` option.
This option can also be set using the `$BUILDARR_LOG_LEVEL` environment variable.

For more interactive documentation, you can pass `--help` to any individual command.

```text
$ buildarr --help
Usage: buildarr [OPTIONS] COMMAND [ARGS]...

  Construct and configure Arr PVR stacks.

  Can be run as a daemon or as an ad-hoc command.

  Supports external plugins to allow for adding support for multiple types of
  instances.

Options:
  -l, --log-level [ERROR|WARNING|INFO|DEBUG]
                                  Buildarr logging system log level. Can also
                                  be set using the `$BUILDARR_LOG_LEVEL'
                                  environment variable.  [default: INFO]
  --help                          Show this message and exit.

Commands:
  daemon       Run as a daemon and periodically update defined instances.
  run          Update configured instances, and exit.
  sonarr       Sonarr instance ad-hoc commands.
  test-config  Test a Buildarr configuration file for correctness.
```

## Manual runs

Buildarr is capable of executing individual update runs, optionally passing
an arbitrary configuration file to parse.
This is useful to test configuration files before formally deploying Buildarr.

```bash
$ buildarr run [/path/to/config.yml]
```

If using Docker, the command would look something like this:

```bash
$ docker run --rm -v /path/to/config:/config -e PUID=<PUID> -e PGID=<PGID> callum027/buildarr:latest run [/config/buildarr.yml]
```

Executing `buildarr run` will result in something resembling the following output.

```text
$ buildarr run
2023-11-12 10:00:29,220 buildarr:1 buildarr.cli.daemon [INFO] Buildarr version 0.7.0 (log level: INFO)
2023-11-12 10:00:29,220 buildarr:1 buildarr.cli.daemon [INFO] Loading configuration file '/config/buildarr.yml'
2023-11-12 10:00:29,775 buildarr:1 buildarr.cli.daemon [INFO] Finished loading configuration file
2023-11-12 10:00:29,932 buildarr:1 buildarr.cli.run [INFO] Loaded plugins: jellyseerr (0.3.0), prowlarr (0.5.0), radarr (0.2.0), sonarr (0.6.0)
2023-11-12 10:00:29,932 buildarr:1 buildarr.cli.run [INFO] Loading instance configurations
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Finished loading instance configurations
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Running with plugins: sonarr
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Resolving instance dependencies
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Finished resolving instance dependencies
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Fetching TRaSH metadata
2023-11-12 10:00:36,723 buildarr:1 buildarr.cli.run [INFO] Finished fetching TRaSH metadata
2023-11-12 10:00:36,723 buildarr:1 buildarr.cli.run [INFO] Rendering instance configuration dynamic attributes
2023-11-12 10:00:36,739 buildarr:1 buildarr.cli.run [INFO] Finished rendering instance configuration dynamic attributes
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Fetching instance secrets
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished fetching instance secrets
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Running connection test
2023-11-12 10:00:37,343 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Connection test successful
2023-11-12 10:00:38,112 buildarr:1 buildarr.cli.run [INFO] Performing post-initialisation configuration render
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] Finished performing post-initialisation configuration render
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] Updating configuration on remote instances
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Fetching remote configuration to check if updates are required
2023-11-12 10:00:39,738 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished fetching remote configuration
2023-11-12 10:00:39,810 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Updating remote configuration
2023-11-12 10:00:39,850 buildarr:1 buildarr.config.base [INFO] <sonarr> (default) sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
2023-11-12 10:00:39,933 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Remote configuration successfully updated
2023-11-12 10:00:40,574 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished updating remote configuration
2023-11-12 10:00:49,722 buildarr:1 buildarr.cli.run [INFO] Finished updating configuration on remote instances
2023-11-12 10:00:49,722 buildarr:1 buildarr.cli.run [INFO] Deleting unmanaged/unused resources on remote instances
2023-11-12 10:00:52,579 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Refetching remote configuration to delete unused resources
2023-11-12 10:00:52,714 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished refetching remote configuration
2023-11-12 10:00:52,771 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Deleting unmanaged/unused resources on the remote instance
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Remote configuration is clean
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished deleting unmanaged/unused resources on the remote instance
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] Finished deleting unmanaged/unused resources on remote instances
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] Deleting downloaded TRaSH metadata
2023-11-12 10:00:52,873 buildarr:1 buildarr.cli.run [INFO] Finished deleting downloaded TRaSH metadata
```

Of note in particular is the following line:

```text
2023-03-29 20:39:51,927 buildarr:1 buildarr.config.base [INFO] <sonarr> (default) sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
```

When Buildarr detects that the remote configuration differs from the locally defined configuration, the remote configuration will be updated. In this case, Buildarr detected that on the `default` instance configured in the Sonarr plugin, the configured GUI instance name is different from the locally defined value, so it updated the Sonarr instance to reflect the change.

If the run fails for one reason or another, an error message will be logged and Buildarr will exit with a non-zero status code.

*Changed in version 0.5.0*: Dry runs have been removed from Buildarr. If [testing your configuration](#testing-configuration) does not cover your needs, consider creating a staging environment for your Arr stack, and test changes there before rolling it out to your production stack.

## As a service (daemon mode)

This is the mode in which that Buildarr is intended to run in most cases.

Buildarr will run as a daemon in the foreground. First, an initial update run is performed, similar to `buildarr run`. If the initial run is successful, Buildarr will then schedule updates to run at specific times according to the configuration,
logging when the next scheduled run will occur.

This is intended to be used to keep a *Arr stack continually up to date, particularly if it has TRaSH-Guides metadata configured. Every scheduled run, the TRaSH-Guides metadata is updated, ensuring that any instances using it will always be using the most up to date profiles.

There are several options for changing how Buildarr daemon runs in the [Buildarr configuration](configuration.md#buildarr-settings).

```text
2023-11-12 10:00:29,220 buildarr:1 buildarr.cli.daemon [INFO] Buildarr version 0.7.0 (log level: INFO)
2023-11-12 10:00:29,220 buildarr:1 buildarr.cli.daemon [INFO] Loading configuration file '/config/buildarr.yml'
2023-11-12 10:00:29,775 buildarr:1 buildarr.cli.daemon [INFO] Finished loading configuration file
2023-11-12 10:00:29,775 buildarr:1 buildarr.cli.daemon [INFO] Daemon configuration:
2023-11-12 10:00:29,776 buildarr:1 buildarr.cli.daemon [INFO]  - Watch configuration files: No
2023-11-12 10:00:29,776 buildarr:1 buildarr.cli.daemon [INFO]  - Update at:
2023-11-12 10:00:29,776 buildarr:1 buildarr.cli.daemon [INFO]    - Monday 03:00
2023-11-12 10:00:29,776 buildarr:1 buildarr.cli.daemon [INFO]    - Tuesday 03:00
2023-11-12 10:00:29,777 buildarr:1 buildarr.cli.daemon [INFO]    - Wednesday 03:00
2023-11-12 10:00:29,777 buildarr:1 buildarr.cli.daemon [INFO]    - Thursday 03:00
2023-11-12 10:00:29,778 buildarr:1 buildarr.cli.daemon [INFO]    - Friday 03:00
2023-11-12 10:00:29,778 buildarr:1 buildarr.cli.daemon [INFO]    - Saturday 03:00
2023-11-12 10:00:29,778 buildarr:1 buildarr.cli.daemon [INFO]    - Sunday 03:00
2023-11-12 10:00:29,778 buildarr:1 buildarr.cli.daemon [INFO] Scheduling update jobs
2023-11-12 10:00:29,779 buildarr:1 buildarr.cli.daemon [INFO] Finished scheduling update jobs
2023-11-12 10:00:29,779 buildarr:1 buildarr.cli.daemon [INFO] Config file monitoring is already disabled
2023-11-12 10:00:29,779 buildarr:1 buildarr.cli.daemon [INFO] Applying initial configuration
2023-11-12 10:00:29,932 buildarr:1 buildarr.cli.run [INFO] Loaded plugins: jellyseerr (0.3.0), prowlarr (0.5.0), radarr (0.2.0), sonarr (0.6.0)
2023-11-12 10:00:29,932 buildarr:1 buildarr.cli.run [INFO] Loading instance configurations
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Finished loading instance configurations
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Running with plugins: sonarr
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Resolving instance dependencies
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Finished resolving instance dependencies
2023-11-12 10:00:29,973 buildarr:1 buildarr.cli.run [INFO] Fetching TRaSH metadata
2023-11-12 10:00:36,723 buildarr:1 buildarr.cli.run [INFO] Finished fetching TRaSH metadata
2023-11-12 10:00:36,723 buildarr:1 buildarr.cli.run [INFO] Rendering instance configuration dynamic attributes
2023-11-12 10:00:36,739 buildarr:1 buildarr.cli.run [INFO] Finished rendering instance configuration dynamic attributes
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Fetching instance secrets
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished fetching instance secrets
2023-11-12 10:00:37,273 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Running connection test
2023-11-12 10:00:37,343 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Connection test successful
2023-11-12 10:00:38,112 buildarr:1 buildarr.cli.run [INFO] Performing post-initialisation configuration render
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] Finished performing post-initialisation configuration render
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] Updating configuration on remote instances
2023-11-12 10:00:39,292 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Fetching remote configuration to check if updates are required
2023-11-12 10:00:39,738 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished fetching remote configuration
2023-11-12 10:00:39,810 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Updating remote configuration
2023-11-12 10:00:39,850 buildarr:1 buildarr.config.base [INFO] <sonarr> (default) sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
2023-11-12 10:00:39,933 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Remote configuration successfully updated
2023-11-12 10:00:40,574 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished updating remote configuration
2023-11-12 10:00:49,722 buildarr:1 buildarr.cli.run [INFO] Finished updating configuration on remote instances
2023-11-12 10:00:49,722 buildarr:1 buildarr.cli.run [INFO] Deleting unmanaged/unused resources on remote instances
2023-11-12 10:00:52,579 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Refetching remote configuration to delete unused resources
2023-11-12 10:00:52,714 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished refetching remote configuration
2023-11-12 10:00:52,771 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Deleting unmanaged/unused resources on the remote instance
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Remote configuration is clean
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] <sonarr> (default) Finished deleting unmanaged/unused resources on the remote instance
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] Finished deleting unmanaged/unused resources on remote instances
2023-11-12 10:00:52,843 buildarr:1 buildarr.cli.run [INFO] Deleting downloaded TRaSH metadata
2023-11-12 10:00:52,873 buildarr:1 buildarr.cli.run [INFO] Finished deleting downloaded TRaSH metadata
2023-11-12 10:00:52,874 buildarr:1 buildarr.cli.daemon [INFO] Finished applying initial configuration
2023-11-12 10:00:52,874 buildarr:1 buildarr.cli.daemon [INFO] Setting up signal handlers
2023-11-12 10:00:52,875 buildarr:1 buildarr.cli.daemon [INFO] Finished setting up signal handlers
2023-11-12 10:00:52,875 buildarr:1 buildarr.cli.daemon [INFO] The next run will be at 2023-11-13 03:00
2023-11-12 10:00:52,875 buildarr:1 buildarr.cli.daemon [INFO] Buildarr ready.
```

Buildarr daemon supports the following signal types:

* `SIGTERM`/`SIGINT` - Gracefully shutdown the Buildarr daemon.
* `SIGHUP` - Reload the Buildarr configuration file and perform an update run
  (the same action taken as when the `watch_config` option is enabled and Buildarr detects configuration changes).
  Not supported on Windows.

## Testing configuration

*New in version 0.4.0.*

This is a mode for testing whether or not a configuration file is syntactically correct, can be loaded, and contains valid instance-to-instance link references and TRaSH-Guides metadata IDs.

This mode is intended for the user to test that a configuration will be loaded properly by Buildarr, before attempting to connect with any remote instances.

```bash
$ buildarr test-config [/path/to/config.yml]
```

If a configuration file is valid, the output from Buildarr will be similar to the following:

```text
$ buildarr test-config /config/buildarr.yml
2023-03-19 10:59:27,819 buildarr:1 buildarr.main [INFO] Buildarr version 0.4.0 (log level: INFO)
2023-03-19 10:59:27,820 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr (0.4.0)
2023-03-19 10:59:27,820 buildarr:1 buildarr.main [INFO] Testing configuration file: /config/buildarr.yml
2023-03-19 10:59:27,947 buildarr:1 buildarr.main [INFO] Loading configuration: PASSED
2023-03-19 10:59:27,947 buildarr:1 buildarr.main [INFO] Loading plugin managers: PASSED
2023-03-19 10:59:27,971 buildarr:1 buildarr.main [INFO] Loading instance configurations: PASSED
2023-03-19 10:59:27,971 buildarr:1 buildarr.main [INFO] Checking configured plugins: PASSED
2023-03-19 10:59:27,971 buildarr:1 buildarr.main [INFO] Resolving instance dependencies: PASSED
2023-03-19 10:59:31,634 buildarr:1 buildarr.main [INFO] Fetching TRaSH-Guides metadata: PASSED
2023-03-19 10:59:31,708 buildarr:1 buildarr.main [INFO] Rendering TRaSH-Guides metadata: PASSED
2023-03-19 10:59:32,053 buildarr:1 buildarr.main [INFO] Configuration test successful.
```

Since Buildarr does not connect to any remote instances in this mode, even if a configuration file passes the tests performed by `buildarr test-config`, it will not necessarily successfully communicate with them.

## Generating a Docker Compose file

*New in version 0.4.0.*

This is an ad-hoc command that can be used to automatically generate a Docker Compose file from a given Buildarr configuration file.

The generated Docker Compose file is guaranteed to have:

* Image tags matching the instance versions defined in the Buildarr configuration file
* Restart policy set on all services
* Any required volumes created
* Service dependencies added based on instance-to-instance links present in the Buildarr configuration
* Buildarr itself added as a service in daemon mode, to deploy instance configurations and keep them up to date

The resulting file will be relatively basic and might require some additional changes to suit your environment, but it should provide a good starting point for setting up automatic deployment and configuration of your *Arr stack.

!!! note

    There are a few additional limitations on the instance configurations, on top of Buildarr's regular constraints:

    * Instance hostnames must not be set to IP addresses.
    * All instances must have unique hostnames, unless the `--ignore-hostnames` option is set.

Given the following example Buildarr configuration file, located at `/opt/buildarr/buildarr.yml`:

```yaml
---
sonarr:
  instances:
    sonarr-hd: {}
    sonarr-4k:
      settings:
        media_management:
          root_folders:
            - /tmp/videos
        profiles:
          language_profiles:
            definitions:
              English:
                languages:
                  - "English"
        import_lists:
          definitions:
            "Sonarr (HD)":
              type: "sonarr"
              root_folder: "/tmp/videos"
              quality_profile: "Any"
              language_profile: "English"
              full_url: "http://sonarr-hd:8989"
              instance_name: "sonarr-hd"
```

We can use the following command to create a corresponding Docker Compose file.

```bash
$ buildarr compose /opt/buildarr/buildarr.yml > /opt/buildarr/docker-compose.yml
```

The resulting file located at `/opt/buildarr/docker-compose.yml` will look like this:

```yaml
---
version: '3.7'
services:
  sonarr_sonarr-hd:
    image: lscr.io/linuxserver/sonarr:latest
    volumes:
      sonarr_sonarr-hd: /config
    hostname: sonarr-hd
    restart: always
  sonarr_sonarr-4k:
    image: lscr.io/linuxserver/sonarr:latest
    volumes:
      sonarr_sonarr-4k: /config
    hostname: sonarr-4k
    restart: always
    depends_on:
    - sonarr_sonarr-hd
  buildarr:
    image: callum027/buildarr:0.4.0
    command:
    - daemon
    - /config/buildarr.yml
    volumes:
    - type: bind
      source: /opt/buildarr
      target: /config
    restart: always
    depends_on:
    - sonarr_sonarr-hd
    - sonarr_sonarr-4k
volumes:
- sonarr_sonarr-4k
- sonarr_sonarr-hd
```

## Plugin-specific commands

Plugins can implement their own ad-hoc commands. These are mainly used for things such as dumping configuration from running instances.

For more information, refer to the user guide for the respective plugin.

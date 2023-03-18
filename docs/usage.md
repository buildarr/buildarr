# Using Buildarr

Apart from the configuration, most of the interactions with Buildarr are done via the command line.

The following commands are available for Buildarr:

* `buildarr run` - Manually perform an update run on one or more instances and exit
* `buildarr daemon` - Run Buildarr forever: perform an initial update run, and then
  schedule periodic updates
* `buildarr test-config` - Test a configuration file for correctness (*Added in version 0.4.0*)
* `buildarr <plugin-name> <command...>` - Ad-hoc commands defined by any loaded plugins

!!! note
    Every time Buildarr performs an update run, a metadata file called `secrets.json` is generated to store secrets information for every configured instance in the current directory. Ensure that you are running Buildarr in a folder that is not world-viewable, to avoid exposing secrets.

    If you are using the Docker image, ensure that the folder mounted as `/config` into the container has appropriately secure permissions.

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
  -l, --log-level [CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET]
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
2023-02-22 21:21:25,047 buildarr:1 buildarr.main [INFO] Buildarr version 0.2.0 (log level: INFO)
2023-02-22 21:21:25,048 buildarr:1 buildarr.main [INFO] Loading configuration file '/config/buildarr.yml'
2023-02-22 21:21:25,080 buildarr:1 buildarr.main [INFO] Finished loading configuration file
2023-02-22 21:21:25,104 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr
2023-02-22 21:21:25,108 buildarr:1 buildarr.main [INFO] Running with plugins: sonarr
2023-02-22 21:21:25,110 buildarr:1 buildarr.main [INFO] Loading secrets file from '/config/secrets.json'
2023-02-22 21:21:25,111 buildarr:1 buildarr.main [INFO] Finished loading secrets file
2023-02-22 21:21:25,112 buildarr:1 buildarr.plugins.sonarr default [INFO] Checking secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.plugins.sonarr default [INFO] Connection test successful using cached secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished checking secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.main [INFO] Saving updated secrets file to 'secrets.json'
2023-02-22 21:21:25,140 buildarr:1 buildarr.main [INFO] Finished saving updated secrets file
2023-02-22 21:21:26,010 buildarr:1 buildarr.plugins.sonarr default [INFO] Getting remote configuration
2023-02-22 21:21:26,334 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished getting remote configuration
2023-02-22 21:21:26,406 buildarr:1 buildarr.plugins.sonarr default [INFO] Updating remote configuration
2023-02-22 21:21:26,783 buildarr:1 buildarr.plugins.sonarr default [INFO] sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
2023-02-22 21:21:26,874 buildarr:1 buildarr.plugins.sonarr default [INFO] Remote configuration successfully updated
2023-02-22 21:21:26,875 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished updating remote configuration
```

Of note in particular is the following line:

```text
2023-02-22 21:21:26,783 buildarr:1 buildarr.plugins.sonarr default [INFO] sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
```

When Buildarr detects that the remote configuration differents from the locally defined configuration, the remote configuration will be updated. In this case, Buildarr detected that on the `default` instance configured in the Sonarr plugin, the configured GUI instance name is different from the locally defined value, so it updated the Sonarr instance to reflect the change.

If the run fails for one reason or another, an error message will be logged and Buildarr with exit with a non-zero status.

### Dry runs

*Added in version 0.4.0.*

Buildarr ad-hoc runs support a dry-run mode, so you can check what *would* change on configured instances, before actually applying them. Under this mode, the output of Buildarr itself is almost exactly the same, but any actions logged in the output are not actually performed.

```bash
$ buildarr run --dry-run
```

This allows you to test changes in the configuration, or check the current state of remote instances against the configuration before actually committing changes.

## As a service (daemon mode)

This is the mode in which that Buildarr is intended to run in most cases.

Buildarr will run as a daemon in the foreground. First, an initial update run is performed, similar to `buildarr run`. If the initial run is successful, Buildarr will then schedule updates to run at specific times according to the configuration,
logging when the next scheduled run will occur.

This is intended to be used to keep a *Arr stack continually up to date, particularly if it has TRaSH-Guides metadata configured. Every scheduled run, the TRaSH-Guides metadata is updated, ensuring that any instances using it will always be using the most up to date profiles.

There are several options for changing how Buildarr daemon runs in the [Buildarr configuration](configuration.md#buildarr-settings).

```text
2023-02-22 21:21:25,047 buildarr:1 buildarr.main [INFO] Buildarr version 0.2.0 (log level: INFO)
2023-02-22 21:21:25,048 buildarr:1 buildarr.main [INFO] Loading configuration file '/config/buildarr.yml'
2023-02-22 21:21:25,080 buildarr:1 buildarr.main [INFO] Finished loading configuration file
2023-02-22 21:21:25,084 buildarr:1 buildarr.main [INFO] Daemon configuration:
2023-02-22 21:21:25,084 buildarr:1 buildarr.main [INFO]  - Watch configuration files: Yes
2023-02-22 21:21:25,084 buildarr:1 buildarr.main [INFO]  - Configuration files to watch:
2023-02-22 21:21:25,085 buildarr:1 buildarr.main [INFO]    - /config/buildarr.yml
2023-02-22 21:21:25,085 buildarr:1 buildarr.main [INFO]  - Update at:
2023-02-22 21:21:25,085 buildarr:1 buildarr.main [INFO]    - Monday 03:00
2023-02-22 21:21:25,085 buildarr:1 buildarr.main [INFO]    - Tuesday 03:00
2023-02-22 21:21:25,085 buildarr:1 buildarr.main [INFO]    - Wednesday 03:00
2023-02-22 21:21:25,086 buildarr:1 buildarr.main [INFO]    - Thursday 03:00
2023-02-22 21:21:25,086 buildarr:1 buildarr.main [INFO]    - Friday 03:00
2023-02-22 21:21:25,086 buildarr:1 buildarr.main [INFO]    - Saturday 03:00
2023-02-22 21:21:25,086 buildarr:1 buildarr.main [INFO]    - Sunday 03:00
2023-02-22 21:21:25,086 buildarr:1 buildarr.main [INFO] Applying initial configuration
2023-02-22 21:21:25,104 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr
2023-02-22 21:21:25,108 buildarr:1 buildarr.main [INFO] Running with plugins: sonarr
2023-02-22 21:21:25,110 buildarr:1 buildarr.main [INFO] Loading secrets file from '/config/secrets.json'
2023-02-22 21:21:25,111 buildarr:1 buildarr.main [INFO] Finished loading secrets file
2023-02-22 21:21:25,112 buildarr:1 buildarr.plugins.sonarr default [INFO] Checking secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.plugins.sonarr default [INFO] Connection test successful using cached secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished checking secrets
2023-02-22 21:21:25,138 buildarr:1 buildarr.main [INFO] Saving updated secrets file to 'secrets.json'
2023-02-22 21:21:25,140 buildarr:1 buildarr.main [INFO] Finished saving updated secrets file
2023-02-22 21:21:26,010 buildarr:1 buildarr.plugins.sonarr default [INFO] Getting remote configuration
2023-02-22 21:21:26,334 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished getting remote configuration
2023-02-22 21:21:26,406 buildarr:1 buildarr.plugins.sonarr default [INFO] Updating remote configuration
2023-02-22 21:21:26,783 buildarr:1 buildarr.plugins.sonarr default [INFO] sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
2023-02-22 21:21:26,874 buildarr:1 buildarr.plugins.sonarr default [INFO] Remote configuration successfully updated
2023-02-22 21:21:26,875 buildarr:1 buildarr.plugins.sonarr default [INFO] Finished updating remote configuration
2023-02-22 21:21:27,220 buildarr:1 buildarr.main [INFO] Finished applying initial configuration
2023-02-22 21:21:27,221 buildarr:1 buildarr.main [INFO] Scheduling update jobs
2023-02-22 21:21:27,221 buildarr:1 buildarr.main [INFO] Finished scheduling update jobs
2023-02-22 21:21:27,222 buildarr:1 buildarr.main [INFO] The next run will be at 2023-02-23 03:00
2023-02-22 21:21:27,222 buildarr:1 buildarr.main [INFO] Setting up config file monitoring
2023-02-22 21:21:27,223 buildarr:1 buildarr.main [INFO] Finished setting up config file monitoring
2023-02-22 21:21:27,223 buildarr:1 buildarr.main [INFO] Setting up signal handlers
2023-02-22 21:21:27,223 buildarr:1 buildarr.main [INFO] Finished setting up signal handlers
2023-02-22 21:21:27,223 buildarr:1 buildarr.main [INFO] Buildarr ready.
```

Buildarr daemon supports the following signal types:

* `SIGTERM`/`SIGINT` - Gracefully shutdown the Buildarr daemon.
* `SIGHUP` - Reload the Buildarr configuration file and perform an update run
  (the same action taken as when the `watch_config` option is enabled and Buildarr detects configuration changes).
  Not supported on Windows.

## Testing configuration

*Added in version 0.4.0.*

This is a mode for testing whether or not a configuration file is syntactically correct, can be loaded, and contains valid instance-to-instance link references and TRaSH-Guides metadata IDs.

This mode is intended for the user to test that a configuration will be loaded properly by Buildarr, before attempting to connect with any remote instances.

```bash
$ buildarr test-config [/path/to/config.yml]
```

If a configuration file is valid, the output from Buildarr will be similar to the following:

```text
$ buildarr test-config /config/buildarr.yml
2023-03-19 10:59:27,819 buildarr:1 buildarr.main [INFO] Buildarr version 0.4.0 (log level: INFO)
2023-03-19 10:59:27,820 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr
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

To test the configuration against live remote instances, without modifying them, you can use `buildarr run --dry-run` as documented in [Dry runs](#dry-runs).

## Plugin-specific commands

Plugins can implement their own ad-hoc commands. These are mainly used for things such as dumping configuration from running instances.

For more information, refer to the user guide for the respective plugin.

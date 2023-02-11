# Welcome to Buildarr!

[![Docker Version](https://img.shields.io/docker/v/callum027/buildarr?sort=semver)](https://hub.docker.com/callum027/buildarr) [![PyPI](https://img.shields.io/pypi/v/buildarr)](https://pypi.org/project/buildarr) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/buildarr)  [![GitHub](https://img.shields.io/github/license/buildarr/buildarr)](https://github.com/buildarr/buildarr/blob/main/LICENSE) ![Pre-commit hooks](https://github.com/buildarr/buildarr/actions/workflows/pre-commit.yml/badge.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is Buildarr, a solution to automating deployment and configuration of your *Arr stack.

Have you spent many hours getting your setup for one or more linked Sonarr/Radarr/Prowlarr instances just right, only to have no way to reproduce this setup apart from UI screenshots and database backups?

Buildarr aims to alleviate those concerns by using a static configuration file to store settings for all your *Arr applications, and automatically configure them as defined. It can just once using an ad-hoc user command, or as a service to keep your application configurations up to date. Buildarr runs idempotently, only making changes to your instance if they are required.

It can also automatically retrieve optimal configuration values from TRaSH-Guides for many things such as quality definitions and release profiles, so not only is there no need to manually input them into your configuration, Buildarr will also continually keep them up to date for you.

The full documentation for Buildarr is available [here](http://buildarr.github.io).

## Similar projects

Buildarr attempts to fulfill some of the needs of users of the following projects.

* [Bobarr](https://github.com/iam4x/bobarr) - An all-in-one package containing Sonarr, Radarr, Jackett etc
    * Still requires manual configuration of many components, and there is no way to store the configuration as code.
* [Flemmarr](https://github.com/Flemmarr/Flemmarr) - Uses API parameters stored in YAML configuration files to push configuration changes to Sonarr, Radarr, Lidarr etc
    * Requires users to comprehensively learn how the APIs of each application work, going through often poor documentation.
    * Since the values are machine-oriented, configuration files are difficult to write and understand.
    * Does not support idempotent updates ([at this time](https://github.com/Flemmarr/Flemmarr/pull/14)).
* [Recyclarr](https://github.com/recyclarr/recyclarr) - Automatically syncs recommended TRaSH-Guides settings to Sonarr/Radarr instances
    * Buildarr has support for this built-in, and in the case of Sonarr release profiles, supports the same filtering syntax.

## Installation

Buildarr is available on Docker Hub as a Docker image.

```bash
$ docker pull callum027/buildarr:latest
```

Buildarr can also be installed using `pip`. Python 3.8 or later is required. Windows is natively supported.

```bash
$ python3 -m venv buildarr-venv
$ . buildarr-venv/bin/activate
$ python3 -m pip install buildarr
```

You can deploy Buildarr as a service within a [Docker Compose](https://docs.docker.com/compose) environment, or use configuration management tools such as [Ansible](https://www.ansible.com) to automatically deploy it.

For more information, check the [installation instructions](http://buildarr.github.io/installation).

## Plugins

Buildarr supports external plugins to allow additional applications to be supported. To allow for rapid development of both the plugin and the API, however, the one currently existing plugin, `buildarr-sonarr`, is vendored in as `buildarr.plugins.sonarr`.

At the time of this release the following plugins are available:

* `buildarr-sonarr` - [Sonarr](https://sonarr.tv) PVR for TV shows (V3 only for now)

For more information on installing plugins and configuring the vendored plugins, check the [plugin documentation](http://buildarr.github.io/plugins).

## Configuration

Buildarr uses YAML as its configuration file format. By default, Buildarr looks for `buildarr.yml` in the current directory.

It contains not only the settings for Buildarr itself, but also the application instances to be managed. Multiple instances of the same application type can be defined (for example, a common use case would be separate Sonarr instances for HD TV shows, 4K TV shows, and anime).

Any configuration on the remote instance not explicitly defined in the Buildarr configuration is not modified.

For more information on how to configure Buildarr, please refer to the documentation.

Here is an example of a simple Buildarr configuration that changes some settings on a Sonarr instance:

```yaml
---
# buildarr.yml
# Buildarr example configuration file.

# Buildarr configuration (all settings have sane default values)
buildarr:
  watch_config: true
  update_days:
    - "monday"
    - "tuesday"
    - "wednesday"
    - "thursday"
    - "friday"
    - "saturday"
    - "sunday"
  update_times:
    - "03:00"

# Sonarr instance configuration
sonarr:
  hostname: "localhost"
  port: 8989
  use_ssl: false
  settings:
    # General settings (all options supported except for changing the API key)
    general:
      host:
        instance_name: "Sonarr (Buildarr Example)"
```

If you have an already configured application instance, its configuration can be dumped. For example, to get the configuration of a Sonarr instance, this can be done using the following command (Buildarr will prompt for your API key):

```bash
$ docker run -it --rm callum027/buildarr:latest sonarr dump-config http://sonarr.example.com:8989
```

Once you have this configuration, you can insert it into `buildarr.yml` and ensure this configuration is maintained.

## Running Buildarr

Once you have a valid configuration file, you can try Buildarr on your local machine using the Docker image.

The following command will mount the current folder into the Docker container so `buildarr.yml` can be read, and start Buildarr in daemon mode.

```bash
$ docker run -d --name buildarr -v ./:/config -e PUID=$UID -e PGID=$GID callum027/buildarr:latest
```

If installed using `pip`, simply run the `buildarr` CLI command.

```bash
$ buildarr daemon
```

On startup, Buildarr daemon will do an initial sync with the defined instances, updating their configuration immediately.
After this initial run, Buildarr will wake up at the scheduled times to periodically run updates as required.

```txt
2023-02-11 13:43:48,890 buildarr:4308 buildarr.main [INFO] Buildarr version 0.1.0 (log level: INFO)
2023-02-11 13:43:48,891 buildarr:4308 buildarr.main [INFO] Loading configuration file '/config/buildarr.yml'
2023-02-11 13:43:48,898 buildarr:4308 buildarr.main [INFO] Finished loading configuration file
2023-02-11 13:43:48,900 buildarr:4308 buildarr.main [INFO] Daemon configuration:
2023-02-11 13:43:48,900 buildarr:4308 buildarr.main [INFO]  - Watch configuration files: Yes
2023-02-11 13:43:48,900 buildarr:4308 buildarr.main [INFO]  - Configuration files to watch:
2023-02-11 13:43:48,900 buildarr:4308 buildarr.main [INFO]    - /config/buildarr.yml
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]  - Update at:
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Monday 03:00
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Tuesday 03:00
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Wednesday 03:00
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Thursday 03:00
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Friday 03:00
2023-02-11 13:43:48,901 buildarr:4308 buildarr.main [INFO]    - Saturday 03:00
2023-02-11 13:43:48,902 buildarr:4308 buildarr.main [INFO]    - Sunday 03:00
2023-02-11 13:43:48,902 buildarr:4308 buildarr.main [INFO] Applying initial configuration
2023-02-11 13:43:48,904 buildarr:4308 buildarr.main [INFO] Plugins loaded: sonarr
2023-02-11 13:43:48,906 buildarr:4308 buildarr.main [INFO] Using plugins: sonarr
2023-02-11 13:43:48,907 buildarr:4308 buildarr.main [INFO] Loading secrets file from 'secrets.json'
2023-02-11 13:43:48,909 buildarr:4308 buildarr.main [INFO] Finished loading secrets file
2023-02-11 13:43:48,910 buildarr:4308 buildarr.plugins.sonarr default [INFO] Checking and fetching secrets
2023-02-11 13:43:48,910 buildarr:4308 buildarr.plugins.sonarr default [INFO] Finished checking and fetching secrets
2023-02-11 13:43:48,910 buildarr:4308 buildarr.main [INFO] Saving updated secrets file to 'secrets.json'
2023-02-11 13:43:48,911 buildarr:4308 buildarr.main [INFO] Finished saving updated secrets file
2023-02-11 13:43:48,914 buildarr:4308 buildarr.plugins.sonarr default [INFO] Getting remote configuration
2023-02-11 13:43:49,870 buildarr:4308 buildarr.plugins.sonarr default [INFO] Finished getting remote configuration
2023-02-11 13:43:49,914 buildarr:4308 buildarr.plugins.sonarr default [INFO] Updating remote configuration
2023-02-11 13:43:49,954 buildarr:4308 buildarr.plugins.sonarr default [INFO] sonarr.settings.general.host.instance_name: 'Sonarr' -> 'Sonarr (Buildarr Example)'
2023-02-11 13:43:50,177 buildarr:4308 buildarr.plugins.sonarr default [INFO] Remote configuration successfully updated
2023-02-11 13:43:50,177 buildarr:4308 buildarr.plugins.sonarr default [INFO] Finished updating remote configuration
2023-02-11 13:43:50,178 buildarr:4308 buildarr.main [INFO] Finished applying initial configuration
2023-02-11 13:43:50,179 buildarr:4308 buildarr.main [INFO] Scheduling update jobs
2023-02-11 13:43:50,180 buildarr:4308 buildarr.main [INFO] Finished scheduling update jobs
2023-02-11 13:43:50,180 buildarr:4308 buildarr.main [INFO] The next run will be at 2023-02-12 03:00
2023-02-11 13:43:50,181 buildarr:4308 buildarr.main [INFO] Setting up config file monitoring
2023-02-11 13:43:50,183 buildarr:4308 buildarr.main [INFO] Finished setting up config file monitoring
2023-02-11 13:43:50,183 buildarr:4308 buildarr.main [INFO] Setting up signal handlers
2023-02-11 13:43:50,183 buildarr:4308 buildarr.main [INFO] Finished setting up signal handlers
2023-02-11 13:43:50,184 buildarr:4308 buildarr.main [INFO] Buildarr ready.
```

For more information on how to interfact with Buildarr, check the [usage documentation](https://buildarr.github.io/usage).

## To-do list

* Add a dry-run mode for testing configurations
* Test updates for all available attributes in the existing Sonarr plugin
* Unit tests and code coverage
* Split Sonarr plugin to its own repository
* Create plugins for the following applications:
  * Sonarr V4
  * Radarr
  * Prowlarr
  * Bazarr
  * FlareSolverr
  * Unmanic
  * Tdarr (maybe)
  * Unpackerr
  * Lidarr
* Instance linking (e.g. Prowlarr-to-Sonarr/Radarr) and dependency resolution
* Stable plugin API between major versions
* Auto-generation of Docker Compose environment files reflecting the Buildarr configuration

## Contributions

Buildarr is still early in development, and even currently implemented features still require testing and fixing. There are so many possible configurations to cover that I simply cannot feasibly test every feature at this time.

If you encounter an issue or error while using Buildarr, please do a Buildarr ad-hoc run with verbose log output by executing `buildarr run --log-level DEBUG` and making an issue on [our GitHub repository](https://github.com/buildarr/buildarr/issues/new) explaining the issue and attaching the output. (Please ensure that any API keys or other sensitive information are obfuscated before submitting.)

```bash
$ docker run -d --name buildarr -v ./:/config -e PUID=$UID -e PGID=$GID callum027/buildarr:latest run --log-level DEBUG
```

For developers looking to make a contribution to this project, thank you! Documentation of the internal APIs is still in the works, so for now, the best way to learn how Buildarr works is to clone the project and have a look at the comments and docstrings.

Pre-commit hooks are configured for this project. In this pre-commit hook, `black`, `flake8`, `isort` and `mypy` are run to automatically format source files, ensure grammatical correctness and variable type consistency.

To enable them, ensure the `pre-commit` Python package is installed in your local environment and run the following command:

```bash
$ pre-commit install
```

Poetry is used to manage the Python package definition and dependencies in this project.

Pull requests for Buildarr itself and the currently vendored plugins are welcome.

If you're looking to develop a new plugin for adding support for a new application, please develop it as a new package and configure entry points in your Python package definitions to allow Buildarr to load your plugin.

Setuptools `setup.py` entry point definition example:
```python
from setuptools import setup

setup(
    # ...,
    entry_points={
        "buildarr.plugins": [
            "example = buildarr_example.plugin:ExamplePlugin",
        ],
    },
)
```

Setuptools `setup.cfg` entry point definition example:
```ini
[options.entry_points]
buildarr.plugins =
    example = buildarr_example.plugin:ExamplePlugin
```

Setuptools `pyproject.toml` entry point definition example:
```toml
[project.entry-points."buildarr.plugins"]
"example" = "buildarr_example.plugin:ExamplePlugin"
```

Poetry plugin definition example:
```toml
[tool.poetry.plugins."buildarr.plugins"]
"example" = "buildarr_example.plugin:ExamplePlugin"
```

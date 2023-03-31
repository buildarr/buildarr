# Plugins

Buildarr supports external plugins to allow support for additional *Arr stack applications to be added.

Successfully installed plugins will be loaded when Buildarr is run, with the plugin's version output. Configured plugins will be listed under `Running with plugins`.

```text
$ buildarr run
2023-03-29 20:39:50,856 buildarr:1 buildarr.cli.run [INFO] Buildarr version 0.4.0 (log level: INFO)
2023-03-29 20:39:50,856 buildarr:1 buildarr.cli.run [INFO] Loading configuration file '/config/buildarr.yml'
2023-03-29 20:39:50,872 buildarr:1 buildarr.cli.run [INFO] Finished loading configuration file
2023-03-29 20:39:50,874 buildarr:1 buildarr.cli.run [INFO] Loaded plugins: sonarr (0.4.0)
2023-03-29 20:39:50,875 buildarr:1 buildarr.cli.run [INFO] Loading instance configurations
2023-03-29 20:39:50,877 buildarr:1 buildarr.cli.run [INFO] Finished loading instance configurations
2023-03-29 20:39:50,877 buildarr:1 buildarr.cli.run [INFO] Running with plugins: sonarr
...
```

Buildarr plugins are installed as Python packages, just like Buildarr itself.

## Supported plugins

At the time of this release the following plugins are available:

* [buildarr-sonarr](https://buildarr.github.io/plugins/sonarr) - [Sonarr](https://sonarr.tv) PVR for TV shows

## Installing plugins for a standalone application

As Buildarr plugins are standard Python packages, they can simply be installed using `pip install` into the environment Buildarr is installed into, and Buildarr will automatically load them.

```bash
$ pip install buildarr-sonarr
```

For more information on installing Buildarr as a standalone application, see the [installation instructions](../installation.md#standalone-application).

## Installing plugins into the Docker container

The official Buildarr container, `callum027/buildarr`, bundles the Sonarr plugin into the image, so there is no need to install the plugin separately if you wish to manage Sonarr instances.

If you would like to install an external plugin that is not bundled, the Buildarr Docker container supports installing plugins at runtime by defining the `$BUILDARR_INSTALL_PACKAGES` environment variable.

`$BUILDARR_INSTALL_PACKAGES` is a space-separated list of packages that gets passed directly to `pip install` on container startup, ensuring that any defined packages are ready before Buildarr starts running.

```bash
$ docker run -d --name buildarr --restart=always -v /path/to/config:/config -e PUID=<PUID> -e PGID=<PGID> -e BUILDARR_INSTALL_PLUGINS="buildarr-sonarr" callum027/buildarr:latest
```

For more information on installing Buildarr as a Docker container, see the [Docker installation instructions](../installation.md#docker).

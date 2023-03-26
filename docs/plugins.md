# Plugins

Buildarr supports external plugins to allow support for additional *Arr stack applications to be added.

Successfully installed plugins will be loaded when Buildarr is run. Configured plugins will be listed under `Using plugins`.

```text
$ buildarr run
2023-02-22 14:50:49,356 buildarr:1 buildarr.main [INFO] Buildarr version 0.2.0 (log level: INFO)
2023-02-22 14:50:49,357 buildarr:1 buildarr.main [INFO] Loading configuration file '/config/buildarr.yml'
2023-02-22 14:50:49,374 buildarr:1 buildarr.main [INFO] Finished loading configuration file
2023-02-22 14:50:49,378 buildarr:1 buildarr.main [INFO] Plugins loaded: sonarr
2023-02-22 14:50:49,380 buildarr:1 buildarr.main [INFO] Running with plugins: sonarr
...
```

## Supported plugins

At the time of this release the following plugins are available:

* [buildarr-sonarr](https://buildarr.github.io/plugins/sonarr) - [Sonarr](https://sonarr.tv) PVR for TV shows

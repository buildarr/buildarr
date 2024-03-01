# Configuring Buildarr

Buildarr uses YAML as its configuration file format. By default, Buildarr looks for `buildarr.yml` in the current directory.

It contains not only the settings for Buildarr itself, but also the application instances to be managed. When an update run of the managed instances is performed, Buildarr will check the remote instances against this configuration, and if there are any differences, Buildarr will update the instance to match the configuration.

Here is an abbreviated example of a `buildarr.yml` where Buildarr is managing a single Sonarr instance.

```yaml
---

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

sonarr:
  hostname: "sonarr.example.com"
  port: 8989
  protocol: "http"
  settings:
    ...
```

## Multiple configuration files

Using the `includes` block, multiple configuration files can be included and read from one `buildarr.yml` file.

This is useful for logical seperation of configuration structures, for example:

* By instance type (Sonarr, Radarr, and so on)
* Defining secrets (API keys and passwords) in separate, encrypted configuration files (e.g. for secrets management in Kubernetes)

Nested inclusion is allowed (included files can include other files). All the loaded configuration files are combined into a single structure using [depth-first search](https://en.wikipedia.org/wiki/Depth-first_search).

Each configuration file will be combined according to the following rules:

* If there are any overlapping configuration attributes defined in multiple files, the value in the last-read file will take precedence.
* Overlapping `list`-type attributes will be overwritten, rather than combined.
* If a local path attribute defined in the configuration file is a relative path, that path will be resolved relative to the parent directory of the configuration file it is defined in. If they are not defined in *any* file, the default value will be resolved relative to the parent directory of the *first* configuration file loaded.

!!! note

    To make troubleshooting easier and to ensure readability, overly complicated include structures in configuration files should be avoided, if possible.


### Separating by instance type

Here is an example where Sonarr and Radarr instances are configured in separate files.

`buildarr.yml`:
```yaml
---

includes:
  - sonarr.yml
  - radarr.yml

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
```

`sonarr.yml`:
```yaml
---

sonarr:
  hostname: "sonarr.example.com"
  port: 8989
  protocol: "http"
  settings:
    ...
```

`radarr.yml`:
```yaml
---

radarr:
  hostname: "radarr.example.com"
  port: 7878
  protocol: "http"
  settings:
    ...
```

### Separating secret and non-secret configuration

Here is an example where Sonarr instance API keys are configured in a separate file from the standard (non-secret) settings.

`buildarr.yml`:
```yaml
---

includes:
  - buildarr-secret.yml

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

sonarr:
  hostname: "sonarr.example.com"
  port: 8989
  protocol: "http"
  settings:
    ...
```

`buildarr-secret.yml`:
```yaml
---

sonarr:
  api_key: 1a2b3c4d5e1a2b3c4d5e1a
```

## Multiple instances of the same type

Using the `instances` attribute, multiple instances of the same type can be administered using a single Buildarr instance. Globally set configuration will apply to all defined instances, and settings defined under a single instance only apply to that instance.

```yaml
sonarr:
  # Configuration common to all Sonarr instances.
  settings:
    ...

  instances:
    # Sonarr instance 1 connection information and configuration.
    sonarr1:
      hostname: "sonarr1.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...

    # Sonarr instance 1 connection information and configuration.
    sonarr2:
      hostname: "sonarr2.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...
```

## How does configuration get pushed to instances?

Buildarr operates on a principle of "don't touch what is not explicitly defined", and idempotent operation.

1. Buildarr downloads the active configuration of a remote instance, and compares it to the configuration file.
2. If a configuration value is not explicitly defined in the Buildarr configuration, it is not updated.
3. If the explicitly set local configuration value matches the remote instance, it is not updated (unless other parameters set using the same API command have been changed).
4. Only if a configuration update is available will it be pushed to the remote instance.

## Buildarr Settings

##### ::: buildarr.config.buildarr.BuildarrConfig
    options:
      members:
        - watch_config
        - update_days
        - update_times
        - request_timeout
        - trash_metadata_download_url
        - trash_metadata_dir_prefix
        - docker_image_uri

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
  host: "sonarr.example.com"
  port: 8989
  protocol: "http"
  settings:
    ...
```

## Multiple configuration files

Using the `includes` block, multiple configuration files can be included and read from one `buildarr.yml` file.

Nested inclusion is allowed (included files can include other files). All the loaded configuration files are merged into a single structure in a [breadth-first](https://en.wikipedia.org/wiki/Breadth-first_search) fashion.

If any configuration attributes in files overlap, the last-read value will take precedence. Note that any overlapping attributes that are lists will be overwritten, rather than combined.

Overly complicated include structures should be avoided, to ensure legibility of the configuration.

`buildarr.yml`:
```yaml
---
includes:
  - sonarr1.yml
  - sonarr2.yml

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
  # Configuration common to all Sonarr instances.
  settings:
    ...
```

`sonarr1.yml`:
```yaml
---

sonarr:
  instances:
    # Sonarr instance 1 connection information and configuration.
    sonarr1:
      host: "sonarr1.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...
```

`sonarr2.yml`:
```yaml
---

sonarr:
  instances:
    # Sonarr instance 2 connection information and configuration.
    sonarr2:
      host: "sonarr2.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...
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
      host: "sonarr1.example.com"
      port: 8989
      protocol: "http"
      settings:
        ...

    # Sonarr instance 1 connection information and configuration.
    sonarr2:
      host: "sonarr2.example.com"
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
        - secrets_file_path
        - trash_metadata_download_url
        - trash_metadata_dir_prefix
      show_root_heading: false
      show_source: false

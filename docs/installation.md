# Installing and running Buildarr

Many users will already have configuraton management automatically deploying their *Arr stacks, and Buildarr is designed to seamlessly integrate into existing setups.

## Standalone application

Buildarr can be installed as a standalone Python application using `pip`. Python 3.8 or later is required.

Buildarr also runs natively on Windows.

As Buildarr can be extended with external plugins, it is recommended to create a dedicated virtual environment to install Buildarr.

```bash
$ python3 -m venv buildarr-venv
$ . buildarr-venv/bin/activate
$ python3 -m pip install buildarr
```

!!! note

    As of Buildarr v0.4.0, plugins are no longer bundled with the Buildarr base package.

    For more information on the available plugins and installing them, see [Plugins](plugins/index.md).

Once installed and a configuration file has been created, you can execute an update of your stack by running the following command.

```bash
 $ buildarr run
```

Buildar can also be run as a daemon to schedule periodic updates of your stack.

```bash
$ buildarr daemon
```

## Docker

Buildarr is available on Docker Hub as a Docker image.

```bash
$ docker pull callum027/buildarr:latest
```

!!! note

    Because the Docker container is a bundle of packages consisting of Buildarr and implementing plugins, it has a separate version number from Buildarr itself.

    For more information, check out the [Docker Hub page](https://hub.docker.com/r/callum027/buildarr) for the Buildarr Docker container.

Once you have a configuration file, create a folder to store the configuration and auto-generated secrets files to mount into the Docker container.

As API keys and login credentials are to be stored here, they should have strict permissions set, with ownership exclusively
set to the `PUID` (process user ID) and `PGID` (process group ID) to be configured on the container.

```bash
$ mkdir --mode=700 /path/to/config
$ sudo chown -R <PUID>:<PGID> /path/to/config
```

You can start a Buildarr container by calling `docker run`, bind mounting the configuration directory as `/config`.

By default, the Buildarr Docker container runs in daemon mode.

```bash
$ docker run -d --name buildarr --restart=always -v /path/to/config:/config -e PUID=<PUID> -e PGID=<PGID> callum027/buildarr:latest
```

For configuration testing purposes, you can call `buildarr run` using the Docker image to run an update of your stack and exit.

```bash
$ docker run --rm -v /path/to/config:/config -e PUID=<PUID> -e PGID=<PGID> callum027/buildarr:latest run
```

The Docker container for Buildarr is bundled with the following plugins (allowing out-of-the-box configuration):

* [`buildarr-sonarr`](https://buildarr.github.io/plugins/sonarr) - [Sonarr](https://sonarr.tv) PVR for TV shows
* [`buildarr-radarr`](https://buildarr.github.io/plugins/radarr) - [Radarr](https://radarr.video) PVR for movies
* [`buildarr-prowlarr`](https://buildarr.github.io/plugins/prowlarr) - [Prowlarr](https://prowlarr.com) indexer manager for Arr applications
* [`buildarr-jellyseerr`](https://buildarr.github.io/plugins/jellyseerr) - [Jellyseerr](https://github.com/Fallenbagel/jellyseerr) media request manager for Jellyfin, Sonarr and Radarr

If you would like to install external plugins into the Docker container, see [Installing plugins into the Docker container](plugins/index.md#installing-plugins-into-the-docker-container).

## Docker Compose

Buildarr can be integrated into a Docker Compose environment containing your *Arr stack instances. `depends_on` should be used to ensure Docker Compose services are started in the correct order.

Here is an example of a `docker-compose.yml` file with Buildarr managing one Sonarr instance.

```yaml
version: "3.7"

services:
  sonarr:
    image: linuxserver/sonarr:3.0.9
    container_name: sonarr
    restart: always
    ports:
      - 127.0.0.1:8989:8989
    volumes:
      - ./sonarr:/config
      - /path/to/downloads:/downloads
      - /path/to/videos:/videos
    environment:
      TZ: Pacific/Auckland
      PUID: "1000"
      PGID: "1000"

  buildarr:
    image: callum027/buildarr:latest
    container_name: buildarr
    restart: always
    volumes:
      - type: bind
        source: ./buildarr
        target: /config
    environment:
      TZ: Pacific/Auckland
      PUID: "1000"
      PGID: "1000"
    depends_on:
      - sonarr
```

The corresponding instance configuration in `buildarr.yml` would look something like this:

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
  # Configuration common to all Sonarr instances can be defined here.
  # settings:
  #   ...
  instances:
    # Name of the instance as referred to by Buildarr.
    # Assign instance-specific configuration to it.
    sonarr:
      host: "sonarr"
      port: 8989
      protocol: "http"
      # Define instance-specific Sonarr settings here.
      settings:
        ...
```

*New in version 0.4.0*: Buildarr now supports [generating a Docker Compose file](usage.md#generating-a-docker-compose-file) from a Buildarr configuration file, using the `buildarr compose` command.

## Automatic deployment using Ansible

Buildarr is designed to be automatically deployed with your *Arr stack using tools such as [Ansible](https://www.ansible.com).

The easiest way to do this is to create a Docker Compose environment, and deploy it using the [community.docker.docker_compose](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_module.html) module.

For applications that expose their API key on an unauthenticated endpoint (such as Sonarr V3), Buildarr will automatically retrieve and use the API keys. For these applications, no manual configuration is required once Buildarr and the managed applications are deployed.

Applications that require an account to be setup (Sonarr V4) are not yet supported.

# -*- coding: utf-8 -*-

# Copyright (C) 2023 Callum Dickinson
#
# Buildarr is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Buildarr is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Buildarr.
# If not, see <https://www.gnu.org/licenses/>.


"""
Sonarr plugin general settings configuration.
"""


from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Union, cast

from pydantic import Field
from typing_extensions import Self

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, Password, Port, RemoteMapEntry
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_get, api_put


class AuthenticationMethod(ConfigEnum):
    """
    Sonarr authentication method.
    """

    none = "none"
    basic = "basic"
    form = "forms"


class CertificateValidation(ConfigEnum):
    """
    External site HTTPS certification validation method.
    """

    enabled = "enabled"
    local_disabled = "disabledForLocalAddresses"
    disabled = "disabled"


class ProxyType(ConfigEnum):
    """
    Proxy server type.
    """

    http = "http"
    socks4 = "socks4"
    socks5 = "socks5"


class SonarrLogLevel(ConfigEnum):
    """
    Log level of the Sonarr application.
    """

    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"


class UpdateMechanism(ConfigEnum):
    """
    Sonarr updating mechanism.
    """

    builtin = "builtIn"
    script = "script"
    external = "external"
    apt = "apt"
    docker = "docker"


class GeneralSettings(ConfigBase):
    """
    Sonarr general settings base class.
    """

    _remote_map: List[RemoteMapEntry]

    @classmethod
    def _from_remote(
        cls,
        sonarr_secrets: SonarrSecrets,
        remote_attrs: Mapping[str, Any],
    ) -> Self:
        return cls(**cls.get_local_attrs(cls._remote_map, remote_attrs))

    def _update_remote_attrs(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> Tuple[bool, Dict[str, Any]]:
        return self.get_update_remote_attrs(
            tree,
            remote,
            self._remote_map,
            check_unmanaged=check_unmanaged,
            set_unchanged=True,
        )


class HostGeneralSettings(GeneralSettings):
    """
    Sonarr instance connection and name configuration.

    Many of these settings configure Sonarr's external connection interface.
    If they are changed, the [settings Buildarr uses to connect](host.md) with this
    Sonarr instance may need to be updated, so take care when modifying them.

    **Changing any of these settings require a restart of Sonarr to take effect.**
    """

    # According to docs, IPv6 not supported at this time.
    bind_address: Union[Literal["*"], IPv4Address] = "*"
    """
    Bind address for Sonarr. Set to an IPv4 address bound to a local interface
    or `*` to bind on all interfaces.

    Unless you run Sonarr directly on a host machine (i.e. not via Docker) and
    want Sonarr to only be available on a specific network or interface,
    this generally should be left untouched.
    """

    port: Port = 8989  # type: ignore[assignment]
    """
    Unencrypted (HTTP) listening port for Sonarr.

    If Sonarr is being run via Docker in the default bridge mode,
    this setting shouldn't be changed.
    Instead, change the external port it is bound to using
    `--publish <port number>:8989`.
    """

    ssl_port: Port = 9898  # type: ignore[assignment]
    """
    Enncrypted (HTTPS) listening port for Sonarr.

    If Sonarr is being run via Docker in the default bridge mode,
    this setting shouldn't be changed.
    Instead, change the external port it is bound to using
    `--publish <port number>:9898`.
    """

    use_ssl: bool = False
    """
    Enable the encrypted (HTTPS) listening port in Sonarr.
    As Sonarr only supports self-signed certificates, it is recommended
    to put Sonarr behind a HTTPS-terminating reverse proxy such as Nginx, Caddy or Traefik.
    """

    url_base: Optional[str] = None
    """
    Add a prefix to all Sonarr URLs,
    e.g. `http://localhost:8989/<url_base>/settings/general`.

    Generally used to accommodate reverse proxies where Sonarr
    is assigned to a subfolder, e.g. `https://example.com/sonarr`.
    """

    instance_name: NonEmptyStr = "Sonarr"  # type: ignore[assignment]
    """
    Instance name in the browser tab and in syslog.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("bind_address", "bindAddress", {}),
        ("port", "port", {}),
        ("ssl_port", "sslPort", {}),
        ("use_ssl", "enableSsl", {}),
        ("url_base", "urlBase", {"decoder": lambda v: v or None, "encoder": lambda v: v or ""}),
        ("instance_name", "instanceName", {}),
    ]


class SecurityGeneralSettings(GeneralSettings):
    """
    Sonarr instance security (authentication) settings.
    """

    authentication: AuthenticationMethod = AuthenticationMethod.none
    """
    Authentication method for logging into Sonarr.
    By default, do not require authentication.

    Values:

    * `none` - No authentication
    * `basic` - Authentication using HTTP basic auth (browser popup)
    * `form` - Authentication using a login page

    Requires a restart of Sonarr to take effect.
    """

    # TODO: constraint - required when authentication is not none
    username: Optional[str] = None
    """
    Username for the administrator user.
    Only used when authentication is enforced.

    Requires a restart of Sonarr to take effect.
    """

    # TODO: constraint - required when authentication is not none
    password: Optional[Password] = None
    """
    Password for the administrator user.
    Only used when authentication is enforced.

    Requires a restart of Sonarr to take effect.
    """

    certificate_validation: CertificateValidation = CertificateValidation.enabled
    """
    Change how strict HTTPS certification validation is.
    Do not change unless you understand the risks.

    Values:

    * `enabled` - Validate HTTPS certificates for all hosts
    * `local-disabled` - Disable HTTPS certificate validation for hosts on the local network
    * `disabled` - Disable HTTPS certificate validation completely
    """

    _remote_map: List[RemoteMapEntry] = [
        ("authentication", "authenticationMethod", {}),
        (
            "username",
            "username",
            {
                "optional": True,  # Set to default value (None) if not found on remote
                "set_if": lambda v: v is not None,  # Do not send to remote if set to None
                "decoder": lambda v: v or None,
                "encoder": lambda v: v or "",
            },
        ),
        (
            "password",
            "password",
            {
                "optional": True,  # Set to default value (None) if not found on remote
                "set_if": lambda v: v is not None,  # Do not send to remote if set to None
            },
        ),
        ("certificate_validation", "certificateValidation", {}),
    ]


class ProxyGeneralSettings(GeneralSettings):
    """
    Proxy configuration for Sonarr.
    """

    enable: bool = False
    """
    Use a proxy server to access the Internet.
    """

    proxy_type: ProxyType = ProxyType.http
    """
    Type of proxy to connect to.

    Values:

    * `http` - HTTP(S) proxy
    * `socks4` - SOCKSv4 proxy
    * `socks5` - SOCKSv5 proxy (Tor is supported)
    """

    # TODO: Enforce constraint
    hostname: Optional[str] = None
    """
    Proxy server hostname.

    Required if using a proxy is enabled.
    """

    port: Port = 8080  # type: ignore[assignment]
    """
    Proxy server access port.
    """

    username: Optional[str] = None
    """
    Username to authenticate with.
    Only enter if authentication is required by the proxy.
    """

    password: Optional[Password] = None
    """
    Password for the proxy user.
    Only enter if authentication is required by the proxy.
    """

    ignored_addresses: List[NonEmptyStr] = []
    """
    List of domains/addresses which bypass the proxy. Wildcards (`*`) are supported.
    """

    bypass_proxy_for_local_addresses: bool = True
    """
    Do not use the proxy to access local network addresses.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("enable", "proxyEnabled", {}),
        ("proxy_type", "proxyType", {}),
        (
            "hostname",
            "proxyHostname",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("port", "proxyPort", {}),
        (
            "username",
            "proxyUsername",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "password",
            "proxyPassword",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "ignored_addresses",
            "proxyBypassFilter",
            {
                "decoder": lambda v: (
                    [addr.strip() for addr in v.split(",")] if v and v.strip() else []
                ),
                "encoder": lambda v: ",".join(v),
            },
        ),
        ("bypass_proxy_for_local_addresses", "proxyBypassLocalAddresses", {}),
    ]


class LoggingGeneralSettings(GeneralSettings):
    """
    Logging configuration for the Sonarr application.
    """

    log_level: SonarrLogLevel = SonarrLogLevel.INFO
    """
    Verbosity of logging output.

    Values:

    * `INFO` - Standard log output
    * `DEBUG` - Debugging log output
    * `TRACE` - Trace diagnostics log output
    """

    _remote_map: List[RemoteMapEntry] = [("log_level", "logLevel", {})]


class AnalyticsGeneralSettings(GeneralSettings):
    """
    Configuration of analytics and telemetry from within Sonarr.
    """

    send_anonymous_usage_data: bool = True
    """
    Send anonymous usage and error information to Sonarr's servers.

    This includes information on your browser, which Sonarr Web UI pages you use,
    error reporting and OS/runtime versions. This information is reportedly used
    to prioritise features and bug fixes.

    Requires a restart of Sonarr to take effect.
    """

    _remote_map: List[RemoteMapEntry] = [("send_anonymous_usage_data", "analyticsEnabled", {})]


class UpdatesGeneralSettings(GeneralSettings):
    """
    Settings for updating Sonarr.
    """

    branch: NonEmptyStr = "main"  # type: ignore[assignment]
    """
    Branch used by the external update mechanism.
    Changing this value has no effect on Docker installations.

    If unsure, leave this undefined in Buildarr and use the value already set in Sonarr.
    """

    automatic: bool = False
    """
    Automatically download and install updates.
    Manual updates can still be performed from System -> Updates.

    This option must be left set to `false` on Docker installations.
    """

    # script_path is required when mechanism is "script"
    # script_path should be absolute only
    mechanism: UpdateMechanism = UpdateMechanism.docker
    """
    Set the mechanism for updating Sonarr.
    Must be set to `docker` on Docker installations.

    Values:

    * `builtin` - Sonarr built-in updater mechanism
    * `script` - Use the configured update script
    * `external` - External update mechanism
    * `apt` - Debian APT package
    * `docker` - Docker image
    """

    # TODO: Constraint - required if update mechanism is "script"
    script_path: Optional[str] = None
    """
    Path to a custom script that takes an extracted update package
    and handles the remainder of the update process.

    Required if `mechanism` is set to `script`.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("branch", "branch", {}),
        ("automatic", "updateAutomatically", {}),
        ("mechanism", "updateMechanism", {}),
        (
            "script_path",
            "updateScriptPath",
            {"decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class BackupGeneralSettings(GeneralSettings):
    """
    Settings for Sonarr automatic backups.
    """

    folder: NonEmptyStr = "Backups"  # type: ignore[assignment]
    """
    Folder to backup Sonarr data to.

    Relative paths will be under Sonarr's AppData directory.
    """

    interval: int = Field(7, ge=0)  # days
    """
    Interval between automatic backups, in days.
    """

    retention: int = Field(28, ge=0)  # days
    """
    Retention period for backups, in days.
    Backups older than the retention period will be cleaned up automatically.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("folder", "backupFolder", {}),
        ("interval", "backupInterval", {}),
        ("retention", "backupRetention", {}),
    ]


class SonarrGeneralSettingsConfig(ConfigBase):
    """
    Sonarr general settings.
    """

    host = HostGeneralSettings()
    security = SecurityGeneralSettings()
    proxy = ProxyGeneralSettings()
    logging = LoggingGeneralSettings()
    analytics = AnalyticsGeneralSettings()
    updates = UpdatesGeneralSettings()
    backup = BackupGeneralSettings()

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrGeneralSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        settings = api_get(sonarr_secrets, "/api/v3/config/host")
        return cls(
            host=HostGeneralSettings._from_remote(sonarr_secrets, settings),
            security=SecurityGeneralSettings._from_remote(sonarr_secrets, settings),
            proxy=ProxyGeneralSettings._from_remote(sonarr_secrets, settings),
            logging=LoggingGeneralSettings._from_remote(sonarr_secrets, settings),
            analytics=AnalyticsGeneralSettings._from_remote(sonarr_secrets, settings),
            updates=UpdatesGeneralSettings._from_remote(sonarr_secrets, settings),
            backup=BackupGeneralSettings._from_remote(sonarr_secrets, settings),
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrGeneralSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        host_updated, host_attrs = self.host._update_remote_attrs(
            f"{tree}.host",
            sonarr_secrets,
            remote.host,
            check_unmanaged=check_unmanaged,
        )
        security_updated, security_attrs = self.security._update_remote_attrs(
            f"{tree}.security",
            sonarr_secrets,
            remote.security,
            check_unmanaged=check_unmanaged,
        )
        proxy_updated, proxy_attrs = self.proxy._update_remote_attrs(
            f"{tree}.proxy",
            sonarr_secrets,
            remote.proxy,
            check_unmanaged=check_unmanaged,
        )
        logging_updated, logging_attrs = self.logging._update_remote_attrs(
            f"{tree}.logging",
            sonarr_secrets,
            remote.logging,
            check_unmanaged=check_unmanaged,
        )
        analytics_updated, analytics_attrs = self.analytics._update_remote_attrs(
            f"{tree}.analytics",
            sonarr_secrets,
            remote.analytics,
            check_unmanaged=check_unmanaged,
        )
        updates_updated, updates_attrs = self.updates._update_remote_attrs(
            f"{tree}.updates",
            sonarr_secrets,
            remote.updates,
            check_unmanaged=check_unmanaged,
        )
        backup_updated, backup_attrs = self.backup._update_remote_attrs(
            f"{tree}.backup",
            sonarr_secrets,
            remote.backup,
            check_unmanaged=check_unmanaged,
        )
        if any(
            [
                host_updated,
                security_updated,
                proxy_updated,
                logging_updated,
                analytics_updated,
                updates_updated,
                backup_updated,
            ],
        ):
            remote_config = api_get(sonarr_secrets, "/api/v3/config/host")
            api_put(
                sonarr_secrets,
                f"/api/v3/config/host/{remote_config['id']}",
                {
                    # There are some undocumented values that are not
                    # set by Buildarr. Pass those through unmodified.
                    **remote_config,
                    **host_attrs,
                    **security_attrs,
                    **proxy_attrs,
                    **logging_attrs,
                    **analytics_attrs,
                    **updates_attrs,
                    **backup_attrs,
                },
            )
            return True
        return False

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
Sonarr plugin connect settings configuration.
"""


from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Type, Union, cast

from pydantic import ConstrainedInt, Field, HttpUrl, NameEmail, SecretStr
from typing_extensions import Annotated, Self

from buildarr.config import ConfigBase, ConfigEnum, NonEmptyStr, Password, Port, RemoteMapEntry
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_delete, api_get, api_post, api_put
from .util import TraktAuthUser, trakt_expires_encoder


class OnGrabField(ConfigEnum):
    """
    Values for `on_grab_fields` for the Discord connection.
    """

    overview = 0
    rating = 1
    genres = 2
    quality = 3
    group = 4
    size = 5
    links = 6
    release = 7
    poster = 8
    fanart = 9


class OnImportField(ConfigEnum):
    """
    Values for `on_import_fields` for the Discord connection.
    """

    overview = 0
    rating = 1
    genres = 2
    quality = 3
    codecs = 4
    group = 5
    size = 6
    languages = 7
    subtitles = 8
    links = 9
    release = 10
    poster = 11
    fanart = 12


class GotifyPriority(ConfigEnum):
    """
    Gotify notification priority.
    """

    min = 0
    low = 2
    normal = 5
    high = 8


class JoinPriority(ConfigEnum):
    """
    Join notification priority.
    """

    silent = -2
    quiet = -1
    normal = 0
    high = 1
    emergency = 2


class ProwlPriority(ConfigEnum):
    """
    Prowl notification priority.
    """

    verylow = -2
    low = -1
    normal = 0
    high = 1
    emergency = 2


class PushoverPriority(ConfigEnum):
    """
    Pushover notification priority.
    """

    silent = -2
    quiet = -1
    normal = 0
    high = 1
    emergency = 2


class PushoverRetry(ConstrainedInt):
    """
    Constrained integer type to enforce Pushover retry field limits.
    """

    ge = 30


class WebhookMethod(ConfigEnum):
    """
    HTTP method to use on a webhook connection.
    """

    POST = 1
    PUT = 2


class NotificationTriggers(ConfigBase):
    """
    Connections are configured using the following syntax.

    ```yaml
    sonarr:
      settings:
        connect:
          delete_unmanaged: false # Optional
          definitions:
            Email: # Name of connection in Sonarr.
              type: "email" # Required
              notification_triggers: # When to send notifications.
                on_grab: true
                on_import: true
                on_upgrade: true
                on_rename: false # Not supported by email notifications.
                on_series_delete: true
                on_episode_file_delete: true
                on_episode_file_delete_for_upgrade: true
                on_health_issue: true
                include_health_warnings: false # Do not send on just warnings.
                on_application_update: true
              tags: # Tags can also be assigned to connections.
                - "example"
              # Connection-specific parameters.
              server: "smtp.example.com"
              port: 465
              use_encryption: true
              username: "sonarr"
              password: "fake-password"
              from_address: "sonarr@example.com"
              recipient_addresses:
                - "admin@example.com"
            # Add additional connections here.
    ```

    A `type` attribute must be defined so Buildarr knows what type of connection to make.
    Each connection has a unique value for `type` documented below.

    The triggers enabled on a connection are defined under `notification_triggers`.
    Tags can be assigned to connections, to only allow notifications relating
    to media under those tags.

    The `delete_unmanaged` flag on the outer `connect` block can be set
    to remove connections not defined in Buildarr.
    Take care when using this option, as it can remove connections
    automatically managed by other applications.

    The following notification triggers can be enabled.
    Some connection types only allow a subset of these to be enabled,
    check the documentation the specific connection type for more information.
    """

    on_grab: bool = False
    """
    Be notified when episodes are available for download and has been sent to a download client.
    """

    on_import: bool = False
    """
    Be notified when episodes are successfully imported. (Formerly known as On Download)
    """

    on_upgrade: bool = False
    """
    Be notified when episodes are upgraded to a better quality.
    """

    on_rename: bool = False
    """
    Be notified when episodes are renamed.
    """

    on_series_delete: bool = False
    """
    Be notified when series are deleted.
    """

    on_episode_file_delete: bool = False
    """
    Be notified when episodes files are deleted.
    """

    on_episode_file_delete_for_upgrade: bool = False
    """
    Be notified when episode files are deleted for upgrades.
    """

    on_health_issue: bool = False
    """
    Be notified on health check failures.
    """

    include_health_warnings: bool = False
    """
    Be notified on health warnings in addition to errors.

    Requires `on_health_issue` to be enabled to have any effect.
    """

    on_application_update: bool = False
    """
    Be notified when Sonarr gets updated to a new version.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("on_grab", "onGrab", {}),
        ("on_import", "onDownload", {}),
        ("on_upgrade", "onUpgrade", {}),
        ("on_rename", "onRename", {}),
        ("on_series_delete", "onSeriesDelete", {}),
        ("on_episode_file_delete", "onEpisodeFileDelete", {}),
        ("on_episode_file_delete_for_upgrade", "onEpisodeFileDeleteForUpgrade", {}),
        ("on_health_issue", "onHealthIssue", {}),
        ("include_health_warnings", "includeHealthWarnings", {}),
        ("on_application_update", "onApplicationUpdate", {}),
    ]


class Connection(ConfigBase):
    """
    Base class for a Sonarr connection.
    """

    notification_triggers: NotificationTriggers = NotificationTriggers()
    """
    Notification triggers to enable on this connection.
    """

    tags: List[NonEmptyStr] = []
    """
    Sonarr tags to associate this connection with.
    """

    _implementation_name: str
    _implementation: str
    _config_contract: str
    _remote_map: List[RemoteMapEntry]

    @classmethod
    def _get_base_remote_map(
        cls,
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return [
            (
                "tags",
                "tags",
                {
                    "decoder": lambda v: set(
                        (tag for tag, tag_id in tag_ids.items() if tag_id in v),
                    ),
                    "encoder": lambda v: sorted(tag_ids[tag] for tag in v),
                },
            ),
        ]

    @classmethod
    def _from_remote(
        cls,
        sonarr_secrets: SonarrSecrets,
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> Connection:
        return cls(
            notification_triggers=NotificationTriggers(
                **NotificationTriggers.get_local_attrs(
                    remote_map=NotificationTriggers._remote_map,
                    remote_attrs=remote_attrs,
                ),
            ),
            **cls.get_local_attrs(
                remote_map=cls._get_base_remote_map(tag_ids) + cls._remote_map,
                remote_attrs=remote_attrs,
            ),
        )

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        tag_ids: Mapping[str, int],
        connection_name: str,
    ) -> None:
        api_post(
            sonarr_secrets=sonarr_secrets,
            api_url="/api/v3/notification",
            req={
                "name": connection_name,
                "implementation": self._implementation,
                "implementationName": self._implementation_name,
                "configContract": self._config_contract,
                **self.notification_triggers.get_create_remote_attrs(
                    tree=f"{tree}.notification_triggers",
                    remote_map=self.notification_triggers._remote_map,
                ),
                **self.get_create_remote_attrs(
                    tree=tree,
                    remote_map=self._get_base_remote_map(tag_ids) + self._remote_map,
                ),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: Self,
        tag_ids: Mapping[str, int],
        connection_id: int,
        connection_name: str,
    ) -> bool:
        (
            triggers_updated,
            triggers_remote_attrs,
        ) = self.notification_triggers.get_update_remote_attrs(
            tree=tree,
            remote=remote.notification_triggers,
            remote_map=self.notification_triggers._remote_map,
            # TODO: check if check_unmanaged and/or set_unchanged are required (probably are)
        )
        base_updated, base_remote_attrs = self.get_update_remote_attrs(
            tree=tree,
            remote=remote,
            remote_map=self._get_base_remote_map(tag_ids) + self._remote_map,
            # TODO: check if check_unmanaged and/or set_unchanged are required (probably are)
        )
        if triggers_updated or base_updated:
            api_put(
                sonarr_secrets=sonarr_secrets,
                api_url=f"/api/v3/notification/{connection_id}",
                req={
                    "id": connection_id,
                    "name": connection_name,
                    "implementation": self._implementation,
                    "implementationName": self._implementation_name,
                    "configContract": self._config_contract,
                    **triggers_remote_attrs,
                    **base_remote_attrs,
                },
            )
            return True
        return False

    def _delete_remote(self, tree: str, sonarr_secrets: SonarrSecrets, connection_id: int) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets=sonarr_secrets, api_url=f"/api/v3/notification/{connection_id}")


class BoxcarConnection(Connection):
    """
    Receive media update and health alert push notifications via Boxcar.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["boxcar"] = "boxcar"
    """
    Type value associated with this kind of connection.
    """

    access_token: Password
    """
    Access token for authenticating with Boxcar.
    """

    _implementation_name: str = "Boxcar"
    _implementation: str = "Boxcar"
    _config_contract: str = "BoxcarSettings"
    _remote_map: List[RemoteMapEntry] = [("access_token", "token", {"is_field": True})]


class CustomscriptConnection(Connection):
    """
    Execute a local script on the Sonarr instance when events occur.

    Supported notification triggers: All
    """

    type: Literal["customscript"] = "customscript"
    """
    Type value associated with this kind of connection.
    """

    path: NonEmptyStr
    """
    Path of the script to execute.
    """

    _implementation_name: str = "Custom Script"
    _implementation: str = "CustomScript"
    _config_contract: str = "CustomScriptSettings"
    _remote_map: List[RemoteMapEntry] = [("path", "path", {"is_field": True})]


class DiscordConnection(Connection):
    """
    Send media update and health alert messages to a Discord server.

    Supported notification triggers: All
    """

    type: Literal["discord"] = "discord"
    """
    Type value associated with this kind of connection.
    """

    webhook_url: HttpUrl
    """
    Discord server webhook URL.
    """

    username: Optional[str] = None
    """
    The username to post as.

    If unset, blank or set to `None`, use the default username set to the webhook URL.
    """

    avatar: Optional[str] = None
    """
    Change the avatar that is used for messages from this connection.

    If unset, blank or set to `None`, use the default avatar for the user.
    """

    # Name override, None -> use machine_name
    host: Optional[str] = None
    """
    Override the host name that shows for this notification.

    If unset, blank or set to `None`, use the machine name.
    """

    on_grab_fields: List[OnGrabField] = [
        OnGrabField.overview,
        OnGrabField.rating,
        OnGrabField.genres,
        OnGrabField.quality,
        OnGrabField.size,
        OnGrabField.links,
        OnGrabField.release,
        OnGrabField.poster,
        OnGrabField.fanart,
    ]
    """
    Set the fields that are passed in for this 'on grab' notification.
    By default, all fields are passed in.

    Values:

    * `overview`
    * `rating`
    * `genres`
    * `quality`
    * `group`
    * `size`
    * `links`
    * `release`
    * `poster`
    * `fanart`

    Example:

    ```yaml
    ...
      connect:
        definitions:
          Discord:
            type: "discord"
            webhook_url: "https://..."
            on_grab_fields:
              - "overview"
              - "quality"
              - "release"
    ```
    """

    on_import_fields: List[OnImportField] = [
        OnImportField.overview,
        OnImportField.rating,
        OnImportField.genres,
        OnImportField.quality,
        OnImportField.codecs,
        OnImportField.group,
        OnImportField.size,
        OnImportField.languages,
        OnImportField.subtitles,
        OnImportField.links,
        OnImportField.release,
        OnImportField.poster,
        OnImportField.fanart,
    ]
    """
    Set the fields that are passed in for this 'on import' notification.
    By default, all fields are passed in.

    Values:

    * `overview`
    * `rating`
    * `genres`
    * `quality`
    * `codecs`
    * `group`
    * `size`
    * `languages`
    * `subtitles`
    * `links`
    * `release`
    * `poster`
    * `fanart`

    Example:

    ```yaml
    ...
      connect:
        definitions:
          Discord:
            type: "discord"
            webhook_url: "https://..."
            on_import_fields:
              - "overview"
              - "quality"
              - "release"
    ```
    """

    _implementation_name: str = "Discord"
    _implementation: str = "Discord"
    _config_contract: str = "DiscordSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("webhook_url", "webHookUrl", {"is_field": True}),
        (
            "username",
            "username",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "avatar",
            "avatar",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "host",
            "host",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        ("on_grab_fields", "grabFields", {"is_field": True}),
        ("on_import_fields", "importFields", {"is_field": True}),
    ]


class EmailConnection(Connection):
    """
    Send media update and health alert messages to an email address.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["email"] = "email"
    """
    Type value associated with this kind of connection.
    """

    server: NonEmptyStr
    """
    Hostname or IP address of the SMTP server to send outbound mail to.
    """

    port: Port = 587  # type: ignore[assignment]
    """
    The port number on the SMTP server to use to submit mail.

    The default is to use STARTTLS on the standard SMTP submission port.
    """

    use_encryption: bool = True
    """
    Whether or not to use encryption when sending mail to the SMTP server.

    If the port number is set to 465, SMTPS (implicit TLS) will be used.
    Any other port number will result in STARTTLS being used.

    The default is to enable encryption.
    """

    username: NonEmptyStr
    """
    SMTP username of the account to send the mail from.
    """

    password: Password
    """
    SMTP password of the account to send the mail from.
    """

    from_address: NameEmail
    """
    Email address to send the mail as.

    RFC-5322 formatted mailbox addresses are also supported,
    e.g. `Sonarr Notifications <sonarr@example.com>`.
    """

    recipient_addresses: Annotated[List[NameEmail], Field(min_items=1, unique_items=True)]
    """
    List of email addresses to directly address the mail to.

    At least one address must be provided.
    """

    cc_addresses: List[NameEmail] = []
    """
    Optional list of email addresses to copy (CC) the mail to.
    """

    bcc_addresses: List[NameEmail] = []
    """
    Optional list of email addresses to blind copy (BCC) the mail to.
    """

    _implementation_name: str = "Email"
    _implementation: str = "Email"
    _config_contract: str = "EmailSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("server", "server", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_encryption", "requireEncryption", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        ("from_address", "from", {"is_field": True}),
        ("recipient_addresses", "to", {"is_field": True}),
        ("cc_addresses", "cc", {"is_field": True}),
        ("bcc_addresses", "bcc", {"is_field": True}),
    ]


class EmbyConnection(Connection):
    """
    Send media update and health alert notifications to an Emby server.

    Supported notification triggers: All
    """

    type: Literal["emby"] = "emby"
    """
    Type value associated with this kind of connection.
    """

    host: NonEmptyStr
    """
    Emby server hostname or IP address.
    """

    port: Port = 8096  # type: ignore[assignment]
    """
    Emby server port.
    """

    use_ssl: bool = False
    """
    Use HTTPS to connect to Emby, instead of HTTP.
    """

    api_key: Password
    """
    API key to authenticate with Emby.
    """

    send_notifications: bool = False
    """
    Have MediaBrowser send notifications to configured providers.
    """

    update_library: bool = False
    """
    Update the Emby library on import, rename, or delete.
    """

    _implementation_name: str = "Emby"
    _implementation: str = "MediaBrowser"
    _config_contract: str = "MediaBrowserSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("api_key", "apiKey", {"is_field": True}),
        ("send_notifications", "notify", {"is_field": True}),
        ("update_library", "updateLibrary", {"is_field": True}),
    ]


class GotifyConnection(Connection):
    """
    Send media update and health alert push notifications via a Gotify server.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["gotify"] = "gotify"
    """
    Type value associated with this kind of connection.
    """

    server: HttpUrl
    """
    Gotify server URL. (e.g. `http://gotify.example.com:1234`)
    """

    app_token: Password
    """
    App token to use to authenticate with Gotify.
    """

    priority: GotifyPriority = GotifyPriority.normal
    """
    Gotify notification priority.

    Values:

    * `min`
    * `low`
    * `normal`
    * `high`
    """

    _implementation: str = "Gotify"
    _implementation_name: str = "Gotify"
    _config_contract: str = "GotifySettings"
    _remote_map: List[RemoteMapEntry] = [
        ("server", "server", {"is_field": True}),
        ("app_token", "appToken", {"is_field": True}),
        ("priority", "priority", {"is_field": True}),
    ]


class JoinConnection(Connection):
    """
    Send media update and health alert push notifications via Join.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["join"] = "join"
    """
    Type value associated with this kind of connection.
    """

    api_key: Password
    """
    API key to use to authenticate with Join.
    """

    # Deprecated, only uncomment if absolutely required by Sonarr
    # device_ids: List[int] = []

    device_names: List[NonEmptyStr] = []
    """
    List of full or partial device names you'd like to send notifications to.

    If unset or empty, all devices will receive notifications.
    """

    priority: JoinPriority = JoinPriority.normal
    """
    Join push notification priority.

    Values:

    * `silent`
    * `quiet`
    * `normal`
    * `high`
    * `emergency`
    """

    _implementation: str = "Join"
    _implementation_name: str = "Join"
    _config_contract: str = "JoinSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("api_key", "apiKey", {"is_field": True}),
        ("device_names", "deviceNames", {"is_field": True}),
        (
            "device_names",
            "deviceNames",
            {
                "is_field": True,
                "decoder": lambda v: v.split(",") if v else [],
                "encoder": lambda v: ",".join(v) if v else "",
            },
        ),
        ("priority", "priority", {"is_field": True}),
    ]


class KodiConnection(Connection):
    """
    Send media update and health alert notifications to a Kodi (XBMC) instance.

    Supported notification triggers: All
    """

    type: Literal["kodi", "xbmc"] = "kodi"
    """
    Type values associated with this kind of connection. (Use either one)
    """

    host: NonEmptyStr
    """
    Kodi hostname or IP address.
    """

    port: Port = 8080  # type: ignore[assignment]
    """
    Kodi API port.
    """

    use_ssl: bool = False
    """
    Connect to Kodi over HTTPS instead of HTTP.
    """

    username: NonEmptyStr
    """
    Username to use to login to Kodi.
    """

    password: Password
    """
    Password to use to login to Kodi.
    """

    gui_notification: bool = False
    """
    Enable showing notifications from Sonarr in the Kodi GUI.
    """

    display_time: int = Field(5, ge=0)  # seconds
    """
    How long the notification will be displayed for (in seconds).
    """

    update_library: bool = False
    """
    Update the Kodi library on import/rename.
    """

    clean_library: bool = False
    """
    Clean the Kodi library after update.
    """

    always_update: bool = False
    """
    Update the Kodi library even when a video is playing.
    """

    _implementation_name: str = "Kodi"
    _implementation: str = "Xbmc"
    _config_contract: str = "XbmcSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        ("gui_notification", "notify", {"is_field": True}),
        ("display_time", "displayTime", {"is_field": True}),
        ("update_library", "updateLibrary", {"is_field": True}),
        ("clean_library", "cleanLibrary", {"is_field": True}),
        ("always_update", "alwaysUpdate", {"is_field": True}),
    ]


class MailgunConnection(Connection):
    """
    Send media update and health alert emails via the Mailgun delivery service.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["mailgun"] = "mailgun"
    """
    Type value associated with this kind of connection.
    """

    api_key: Password
    """
    API key to use to authenticate with Mailgun.
    """

    use_eu_endpoint: bool = False
    """
    Send mail via the EU endpoint instead of the US one.
    """

    from_address: NameEmail
    """
    Email address to send the mail as.

    RFC-5322 formatted mailbox addresses are also supported,
    e.g. `Sonarr Notifications <sonarr@example.com>`.
    """

    sender_domain: NonEmptyStr
    """
    The domain from which the mail will be sent.
    """

    recipient_addresses: List[NameEmail] = []
    """
    The recipient email addresses of the notification mail.
    """

    _implementation: str = "Mailgun"
    _implementation_name: str = "MailGun"
    _config_contract: str = "MailgunSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("api_key", "apiKey", {"is_field": True}),
        ("use_eu_endpoint", "useEuEndpoint", {"is_field": True}),
        ("from_address", "from", {"is_field": True}),
        ("sender_domain", "senderDomain", {"is_field": True}),
        ("recipient_addresses", "recipients", {"is_field": True}),
    ]


class PlexHomeTheaterConnection(Connection):
    """
    Send media update notifications to a Plex Home Theater instance.

    Supported notification triggers: `on_grab`, `on_import`, `on_upgrade` **only**
    """

    type: Literal["plex-home-theater"] = "plex-home-theater"
    """
    Type value associated with this kind of connection.
    """

    host: NonEmptyStr
    """
    Plex Home Theater hostname or IP address.
    """

    port: Port = 3005  # type: ignore[assignment]
    """
    Plex Home Theater API port.
    """

    use_ssl: bool = False
    """
    Connect to Plex Home Theater over HTTPS instead of HTTP.
    """

    username: NonEmptyStr
    """
    Username to use to login to Plex Home Theater.
    """

    password: Password
    """
    Password to use to login to Plex Home Theater.
    """

    gui_notification: bool = False
    """
    Enable showing notifications from Sonarr in the Plex Home Theater GUI.
    """

    display_time: int = Field(5, ge=0)  # seconds
    """
    How long the notification will be displayed for (in seconds).
    """

    update_library: bool = False
    """
    Update the Plex Home Theater library on import/rename.
    """

    clean_library: bool = False
    """
    Clean the Plex Home Theater library after update.
    """

    always_update: bool = False
    """
    Update the Plex Home THeater library even when a video is playing.
    """

    _implementation_name: str = "Plex Home Theater"
    _implementation: str = "PlexHomeTheater"
    _config_contract: str = "PlexHomeTheaterSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
        ("gui_notification", "notify", {"is_field": True}),
        ("display_time", "displayTime", {"is_field": True}),
        ("update_library", "updateLibrary", {"is_field": True}),
        ("clean_library", "cleanLibrary", {"is_field": True}),
        ("always_update", "alwaysUpdate", {"is_field": True}),
    ]


class PlexMediaCenterConnection(Connection):
    """
    Send media update notifications to a Plex Media Center instance.

    Supported notification triggers: `on_grab`, `on_import`, `on_upgrade` **only**
    """

    type: Literal["plex-media-center"] = "plex-media-center"
    """
    Type value associated with this kind of connection.
    """

    host: NonEmptyStr
    """
    Plex Media Center hostname or IP address.
    """

    port: Port = 3000  # type: ignore[assignment]
    """
    Plex Media Center API port.
    """

    username: NonEmptyStr
    """
    Username to use to login to Plex Media Center.
    """

    password: Password
    """
    Password to use to login to Plex Media Center.
    """

    _implementation_name: str = "Plex Media Center"
    _implementation: str = "PlexClient"
    _config_contract: str = "PlexClientSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
    ]


class PlexMediaServerConnection(Connection):
    """
    Send media update notifications to a Plex Media Server instance.

    Supported notification triggers: All except `on_grab`, `on_health_issue`
    and `on_application_update`
    """

    type: Literal["plex-media-server"] = "plex-media-server"
    """
    Type value associated with this kind of connection.
    """

    host: NonEmptyStr
    """
    Plex Media Server hostname or IP address.
    """

    port: Port = 32400  # type: ignore[assignment]
    """
    Plex Media Server API port.
    """

    use_ssl: bool = False
    """
    Connect to Plex Media Server over HTTPS instead of HTTP.
    """

    auth_token: Password
    """
    Plex authentication token.

    If unsure on where to find this token,
    [follow this guide from Plex.tv][PATK].
    [PATK]: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token
    """

    # TODO: Determine how this should be handled.
    # I think as long as auth_token is specified, there should be no problems.
    # sign_in: Literal["startOAuth"] = "startOAuth"

    update_library: bool = True
    """
    Update the Plex Media Server library on import, rename or delete.
    """

    _implementation_name: str = "Plex Media Server"
    _implementation: str = "PlexServer"
    _config_contract: str = "PlexServerSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("host", "host", {"is_field": True}),
        ("port", "port", {"is_field": True}),
        ("use_ssl", "useSsl", {"is_field": True}),
        ("auth_token", "authToken", {"is_field": True}),
        ("update_library", "updateLibrary", {"is_field": True}),
    ]


class ProwlConnection(Connection):
    """
    Send media update and health alert push notifications to a Prowl client.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["prowl"] = "prowl"
    """
    Type value associated with this kind of connection.
    """

    api_key: Password
    """
    API key to use when authenticating with Prowl.
    """

    priority: ProwlPriority = ProwlPriority.normal
    """
    Prowl push notification priority.

    Values:

    * `verylow`
    * `low`
    * `normal`
    * `high`
    * `emergency`
    """

    _implementation: str = "Prowl"
    _implementation_name: str = "Prowl"
    _config_contract: str = "ProwlSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("api_key", "apiKey", {"is_field": True}),
        ("priority", "priority", {"is_field": True}),
    ]


class PushbulletConnection(Connection):
    """
    Send media update and health alert push notifications to 1 or more Pushbullet devices.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["pushbullet"] = "pushbullet"
    """
    Type value associated with this kind of connection.
    """

    api_key: Password
    """
    API key to use when authenticating with Pushbullet.
    """

    device_ids: List[NonEmptyStr] = []
    """
    List of device IDs to send notifications to.

    If unset or empty, send to all devices.
    """

    channel_tags: List[NonEmptyStr] = []
    """
    List of Channel Tags to send notifications to.
    """

    sender_id: Optional[str] = None
    """
    The device ID to send notifications from
    (`device_iden` in the device's URL on [pushbullet.com](https://pushbullet.com)).

    Leave unset, blank or set to `None` to send from yourself.
    """

    _implementation: str = "Pushbullet"
    _implementation_name: str = "PushBullet"
    _config_contract: str = "PushBulletSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("api_key", "apiKey", {"is_field": True}),
        ("device_ids", "deviceIds", {"is_field": True}),
        ("channel_tags", "channelTags", {"is_field": True}),
        (
            "sender_id",
            "senderId",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class PushoverConnection(Connection):
    """
    Send media update and health alert push notifications to 1 or more Pushover devices.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["pushover"] = "pushover"
    """
    Type value associated with this kind of connection.
    """

    user_key: Annotated[SecretStr, Field(min_length=30, max_length=30)]
    """
    User key to use to authenticate with your Pushover account.
    """

    api_key: Annotated[SecretStr, Field(min_length=30, max_length=30)]
    """
    API key assigned to Sonarr in Pushover.
    """

    devices: List[NonEmptyStr] = []
    """
    List of device names to send notifications to.

    If unset or empty, send to all devices.
    """

    priority: PushoverPriority = PushoverPriority.normal
    """
    Pushover push notification priority.

    Values:

    * `silent`
    * `quiet`
    * `normal`
    * `high`
    * `emergency`
    """

    retry: Union[Literal[0], PushoverRetry] = 0
    """
    Interval to retry emergency alerts, in seconds.

    Minimum 30 seconds. Set to 0 to disable retrying emergency alerts.
    """

    # TODO: Enforce "expire > retry if retry > 0" constraint
    expire: int = Field(0, ge=0, le=86400)
    """
    Threshold for retrying emergency alerts, in seconds.
    If `retry` is set, this should be set to a higher value.

    Maximum 86400 seconds (1 day).
    """

    sound: Optional[str] = None
    """
    Notification sound to use on devices.

    Leave unset, blank or set to `None` to use the default.
    """

    _implementation_name: str = "Pushover"
    _implementation: str = "Pushover"
    _config_contract: str = "PushoverSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("user_key", "userKey", {"is_field": True}),
        ("api_key", "apiKey", {"is_field": True}),
        ("devices", "devices", {"is_field": True}),
        ("priority", "priority", {"is_field": True}),
        ("retry", "retry", {"is_field": True}),
        ("expire", "expire", {"is_field": True}),
        (
            "sound",
            "sound",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class SendgridConnection(Connection):
    """
    Send media update and health alert emails via the SendGrid delivery service.

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["sendgrid"] = "sendgrid"
    """
    Type value associated with this kind of connection.
    """

    api_key: Password
    """
    API key to use to authenticate with SendGrid.
    """

    from_address: NameEmail
    """
    Email address to send the mail as.

    RFC-5322 formatted mailbox addresses are also supported,
    e.g. `Sonarr Notifications <sonarr@example.com>`.
    """

    recipient_addresses: List[NameEmail] = []
    """
    The recipient email addresses of the notification mail.
    """

    _implementation: str = "SendGrid"
    _implementation_name: str = "SendGrid"
    _config_contract: str = "SendGridSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("api_key", "apiKey", {"is_field": True}),
        ("from_address", "from", {"is_field": True}),
        ("recipient_addresses", "recipients", {"is_field": True}),
    ]


class SlackConnection(Connection):
    """
    Send media update and health alert messages to a Slack channel.

    Supported notification triggers: All
    """

    type: Literal["slack"] = "slack"
    """
    Type value associated with this kind of connection.
    """

    webhook_url: HttpUrl
    """
    Webhook URL for the Slack channel to send to.
    """

    username: NonEmptyStr
    """
    Username to post as.
    """

    icon: Optional[str] = None
    """
    The icon that is used for messages from this integration (emoji or URL).

    If unset, blank or set to `None`, use the default for the user.
    """

    channel: Optional[str] = None
    """
    If set, overrides the default channel in the webhook.
    """

    _implementation: str = "Slack"
    _implementation_name: str = "Slack"
    _config_contract: str = "SlackSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("webhook_url", "webHookUrl", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        (
            "icon",
            "icon",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
        (
            "channel",
            "channel",
            {"is_field": True, "decoder": lambda v: v or None, "encoder": lambda v: v or ""},
        ),
    ]


class SynologyIndexerConnection(Connection):
    """
    Send media update notifications to the local Synology Indexer.

    Supported notification triggers: All except `on_grab`, `on_health_issue`
    and `on_application_update`
    """

    type: Literal["synology-indexer"] = "synology-indexer"
    """
    Type value associated with this kind of connection.
    """

    update_library: bool = True
    """
    Update the library on media import/rename/delete.
    """

    _implementation_name: str = "Synology Indexer"
    _implementation: str = "SynologyIndexer"
    _config_contract: str = "SynologyIndexerSettings"
    _remote_map: List[RemoteMapEntry] = [("update_library", "updateLibrary", {"is_field": True})]


class TelegramConnection(Connection):
    """
    Send media update and health alert messages to a Telegram chat room.

    Supported notification triggers: All
    """

    type: Literal["telegram"] = "telegram"
    """
    Type value associated with this kind of connection.
    """

    bot_token: Password
    """
    The bot token assigned to the Sonarr instance.
    """

    chat_id: NonEmptyStr
    """
    The ID of the chat room to send messages to.

    You must start a conversation with the bot or add it to your group to receive messages.
    """

    send_silently: bool = False
    """
    Sends the message silently. Users will receive a notification with no sound.
    """

    _implementation: str = "Telegram"
    _implementation_name: str = "Telegram"
    _config_contract: str = "TelegramSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("bot_token", "botToken", {"is_field": True}),
        ("chat_id", "chatId", {"is_field": True}),
        ("send_silently", "sendSilently", {"is_field": True}),
    ]


class TraktConnection(Connection):
    """
    Send media update and health alert messages to the Trakt media tracker.

    !!! note

        Sonarr directly authenticates with Trakt to generate tokens for it to use.
        At the moment, the easiest way to generate the tokens for Buildarr
        is to do it using the GUI within Sonarr, and use the following
        shell command to retrieve the generated configuration.

        ```bash
        $ curl -X "GET" "<sonarr-url>/api/v3/notification" -H "X-Api-Key: <api-key>"
        ```

    Supported notification triggers: All except `on_grab`, `on_rename`,
    `on_health_issue` and `on_application_update`
    """

    # FIXME: Determine easier procedure for getting access tokens and test.

    type: Literal["trakt"] = "trakt"
    """
    Type value associated with this kind of connection.
    """

    access_token: Password
    """
    Access token for Sonarr from Trakt.
    """

    refresh_token: Password
    """
    Refresh token for Sonarr from Trakt.
    """

    expires: datetime
    """
    Expiry date-time of the access token, preferably in ISO-8601 format and in UTC.

    Example: `2023-05-10T15:34:08.117451Z`
    """

    auth_user: TraktAuthUser
    """
    The username being authenticated in Trakt.
    """

    _implementation_name: str = "Trakt"
    _implementation: str = "Trakt"
    _config_contract: str = "TraktSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("access_token", "accessToken", {"is_field": True}),
        ("refresh_token", "refreshToken", {"is_field": True}),
        ("expires", "expires", {"is_field": True, "encoder": trakt_expires_encoder}),
        ("auth_user", "authUser", {"is_field": True}),
    ]


class TwitterConnection(Connection):
    """
    Send media update and health alert messages via Twitter.

    Twitter requires you to create an application for their API
    to generate the necessary keys and secrets.
    If unsure how to proceed, refer to these guides from
    [Twitter](https://developer.twitter.com/en/docs/authentication/oauth-1-0a/api-key-and-secret)
    and [WikiArr](https://wiki.servarr.com/useful-tools#twitter-connect).

    Access tokens can be obtained using the prodecure documented [here](
    https://developer.twitter.com/en/docs/authentication/oauth-1-0a/obtaining-user-access-tokens).

    Supported notification triggers: All except `on_rename`
    """

    type: Literal["twitter"] = "twitter"
    """
    Type value associated with this kind of connection.
    """

    consumer_key: Password
    """
    Consumer key from a Twitter application.
    """

    consumer_secret: Password
    """
    Consumer key from a Twitter application.
    """

    access_token: Password
    """
    Access token for a Twitter user.
    """

    access_token_secret: Password
    """
    Access token secret for a Twitter user.
    """

    mention: NonEmptyStr
    """
    Mention this user in sent tweets.
    """

    direct_message: bool = True
    """
    Send a direct message instead of a public message.
    """

    _implementation_name: str = "Twitter"
    _implementation: str = "Twitter"
    _config_contract: str = "TwitterSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("consumer_key", "consumerKey", {"is_field": True}),
        ("consumer_secret", "consumerSecret", {"is_field": True}),
        ("access_token", "accessToken", {"is_field": True}),
        ("access_token_secret", "accessTokenSecret", {"is_field": True}),
        ("mention", "mention", {"is_field": True}),
        ("direct_message", "direct_message", {"is_field": True}),
    ]


class WebhookConnection(Connection):
    """
    Send media update and health alert notifications to a webhook API.

    Supported notification triggers: All
    """

    type: Literal["webhook"] = "webhook"
    """
    Type value associated with this kind of connection.
    """

    url: HttpUrl
    """
    Webhook URL to send notifications to.
    """

    method: WebhookMethod = WebhookMethod.POST
    """
    HTTP request method type to use.

    Values:

    * `POST`
    * `PUT`
    """

    username: NonEmptyStr
    """
    Webhook API username.
    """

    password: Password
    """
    Webhook API password.
    """

    _implementation_name: str = "Webhook"
    _implementation: str = "Webhook"
    _config_contract: str = "WebhookSettings"
    _remote_map: List[RemoteMapEntry] = [
        ("url", "url", {"is_field": True}),
        ("method", "method", {"is_field": True}),
        ("username", "username", {"is_field": True}),
        ("password", "password", {"is_field": True}),
    ]


CONNECTION_TYPES: Tuple[Type[Connection], ...] = (
    BoxcarConnection,
    CustomscriptConnection,
    DiscordConnection,
    EmailConnection,
    EmbyConnection,
    GotifyConnection,
    JoinConnection,
    KodiConnection,
    MailgunConnection,
    PlexHomeTheaterConnection,
    PlexMediaCenterConnection,
    PlexMediaServerConnection,
    ProwlConnection,
    PushbulletConnection,
    PushoverConnection,
    SendgridConnection,
    SlackConnection,
    SynologyIndexerConnection,
    TelegramConnection,
    TraktConnection,
    TwitterConnection,
    WebhookConnection,
)
CONNECTION_TYPE_MAP: Dict[str, Type[Connection]] = {
    connection_type._implementation: connection_type for connection_type in CONNECTION_TYPES
}


class SonarrConnectSettingsConfig(ConfigBase):
    """
    Manage notification connections in Sonarr.
    """

    delete_unmanaged: bool = False
    """
    Automatically delete connections not configured in Buildarr.

    Take care when enabling this option, as this can remove connections automatically
    managed by other applications.
    """

    # TODO: Set minimum Python version to 3.11 and subscript CONNECTION_TYPES here.
    definitions: Dict[
        str,
        Union[
            BoxcarConnection,
            CustomscriptConnection,
            DiscordConnection,
            EmailConnection,
            EmbyConnection,
            GotifyConnection,
            JoinConnection,
            KodiConnection,
            MailgunConnection,
            PlexHomeTheaterConnection,
            PlexMediaCenterConnection,
            PlexMediaServerConnection,
            ProwlConnection,
            PushbulletConnection,
            PushoverConnection,
            SendgridConnection,
            SlackConnection,
            SynologyIndexerConnection,
            TelegramConnection,
            TraktConnection,
            TwitterConnection,
            WebhookConnection,
        ],
    ] = {}
    """
    Connection definitions to configure in Sonarr.
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrConnectSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        connections = api_get(sonarr_secrets, "/api/v3/notification")
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(connection["tags"] for connection in connections)
            else {}
        )
        return cls(
            definitions={
                connection["name"]: CONNECTION_TYPE_MAP[connection["implementation"]]._from_remote(
                    sonarr_secrets=sonarr_secrets,
                    tag_ids=tag_ids,
                    remote_attrs=connection,
                )
                for connection in connections
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrConnectSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        #
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        #
        connection_ids: Dict[str, int] = {
            connection_json["name"]: connection_json["id"]
            for connection_json in api_get(sonarr_secrets, "/api/v3/notification")
        }
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(connection.tags for connection in self.definitions.values())
            or any(connection.tags for connection in remote.definitions.values())
            else {}
        )
        #
        for connection_name, connection in self.definitions.items():
            connection_tree = f"{tree}.definitions[{repr(connection_name)}]"
            #
            if connection_name not in remote.definitions:
                connection._create_remote(
                    tree=connection_tree,
                    sonarr_secrets=sonarr_secrets,
                    tag_ids=tag_ids,
                    connection_name=connection_name,
                )
                changed = True
            #
            else:
                if connection._update_remote(
                    tree=connection_tree,
                    sonarr_secrets=sonarr_secrets,
                    remote=remote.definitions[connection_name],  # type: ignore[arg-type]
                    tag_ids=tag_ids,
                    connection_id=connection_ids[connection_name],
                    connection_name=connection_name,
                ):
                    changed = True
        #
        for connection_name, connection in remote.definitions.items():
            if connection_name not in self.definitions:
                connection_tree = f"{tree}.definitions[{repr(connection_name)}]"
                if self.delete_unmanaged:
                    connection._delete_remote(
                        tree=connection_tree,
                        sonarr_secrets=sonarr_secrets,
                        connection_id=connection_ids[connection_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", connection_tree)
        #
        return changed

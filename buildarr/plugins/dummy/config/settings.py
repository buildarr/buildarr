# Copyright (C) 2024 Callum Dickinson
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
Dummy plugin settings configuration.
"""

from __future__ import annotations

import json

from typing import Any, ClassVar, List, Mapping, Optional, Union, cast
from uuid import UUID, uuid4

from pydantic import Field
from typing_extensions import Annotated, Self

from buildarr.config import ConfigTrashIDNotFoundError, RemoteMapEntry
from buildarr.state import state
from buildarr.types import InstanceReference, TrashID

from ..api import api_get, api_post
from ..secrets import DummySecrets
from .types import DummyConfigBase


class DummySettingsConfig(DummyConfigBase):
    """
    Dummy settings configuration.

    Specify any of the following attributes to ensure the attribute
    on the remote Dummy instance is set accordingly.

    ```yaml
    dummy:
      settings:
        trash_value: 5
    ```

    Specify `trash_id` to get a value from TRaSH-Guides metadata and set it to `trash_value`.

    ```yaml
    dummy:
      settings:
        trash_id: "387e6278d8e06083d813358762e0ac63" # anime
    ```
    """

    instance_name: Annotated[Optional[str], InstanceReference(plugin_name="dummy")] = None
    """
    The name of the Dummy instance within Buildarr, if linking this Dummy instance
    with another Buildarr-defined Dummy instance.
    """

    trash_id: Optional[TrashID] = None
    """
    TRaSH-Guides Sonarr quality definition profile ID to use when filling out `trash_value`.
    """

    trash_value: Union[float, None] = None
    """
    Value retrieved from the TRaSH-Guides repository.

    If this value is explicitly specified in the configuration, it does not get overwritten.
    """

    trash_value_2: Union[float, None] = None
    """
    Another value retrieved from the TRaSH-Guides repository.

    If this value is explicitly specified in the configuration, it does not get overwritten.
    """

    instance_value: Optional[UUID] = Field(default_factory=uuid4)
    """
    Instance-specific UUID generated by Buildarr, which is unique on each execution
    (unless explicitly defined within the Buildarr configuration).

    If `instance_name` is defined, this value will instead be read from the target instance.
    """

    _remote_map: ClassVar[List[RemoteMapEntry]] = [
        (
            "trash_value",  # Buildarr config attribute name.
            "trashValue",  # Dummy instance API attribute name.
            {},  # Local/remote map conversion function parameters.
        ),
        (
            "trash_value_2",  # Buildarr config attribute name.
            "trashValue2",  # Dummy instance API attribute name.
            {},  # Local/remote map conversion function parameters.
        ),
        (
            "instance_value",  # Buildarr config attribute name.
            "instanceValue",  # Dummy instance API attribute name.
            {"check_unmanaged": True},  # Local/remote map conversion function parameters.
        ),
    ]
    """
    A list of remote map entries containing metadata for how to convert
    between local and remote Dummy instance configuration values.

    For more information on how to create this structure,
    see the documentation for the following methods in `buildarr/config/__init__.py`:

    * `ConfigBase.get_local_attrs`
    * `ConfigBase.get_create_remote_attrs`
    * `ConfigBase.get_update_remote_attrs`
    """

    def uses_trash_metadata(self) -> bool:
        """
        Return whether or not this instance configuration uses TRaSH-Guides metadata.

        Returns:
            `True` if TRaSH-Guides metadata is used, otherwise `False`
        """
        return bool(self.trash_id)

    def _render(self) -> None:
        """
        Render dynamic configuration attributes in place.

        Specifically, this function reads a value from the TRaSH-Guides metadata
        and populates the `trash_value` attribute with it (if not already defined).

        Set `trash_value` to the minimum data rate value for the
        `Bluray-1080p` quality definition in the profile.
        """
        if not self.trash_id:
            return
        if self.trash_value:
            return
        for quality_file in (
            state.trash_metadata_dir / "docs" / "json" / "sonarr" / "quality-size"
        ).iterdir():
            with quality_file.open() as f:
                quality_json: Mapping[str, Any] = json.load(f)
                if cast(str, quality_json["trash_id"]).lower() == self.trash_id:
                    for definition_json in quality_json["qualities"]:
                        if definition_json["quality"] == "Bluray-1080p":
                            self.trash_value = cast(float, definition_json["min"])
                            break
                    else:
                        raise ValueError(
                            "Quality definition 'Bluray-1080p' not found in TRaSH-Guides profile",
                        )
                    break
        else:
            raise ConfigTrashIDNotFoundError(
                f"Unable to find Sonarr quality definition file with trash ID '{self.trash_id}'",
            )

    def _post_init_render(self) -> None:
        """
        Post-init render dynamic configuration attributes in place.

        Specifically, this function reads a value from the TRaSH-Guides metadata
        and populates the `trash_value_2` attribute with it (if not already defined).

        Set `trash_value` to the minimum data rate value for the
        `Bluray-2160p` quality definition in the profile.
        """
        if not self.trash_id:
            return
        if self.trash_value_2:
            return
        for quality_file in (
            state.trash_metadata_dir / "docs" / "json" / "sonarr" / "quality-size"
        ).iterdir():
            with quality_file.open() as f:
                quality_json: Mapping[str, Any] = json.load(f)
                if cast(str, quality_json["trash_id"]).lower() == self.trash_id:
                    for definition_json in quality_json["qualities"]:
                        if definition_json["quality"] == "Bluray-2160p":
                            self.trash_value_2 = cast(float, definition_json["min"])
                            break
                    else:
                        raise ValueError(
                            "Quality definition 'Bluray-1080p' not found in TRaSH-Guides profile",
                        )
                    break
        else:
            raise ConfigTrashIDNotFoundError(
                f"Unable to find Sonarr quality definition file with trash ID '{self.trash_id}'",
            )

    def _resolve(self) -> Self:
        """
        Resolve any instance references in this configuration, and
        return an object with fully qualified attribute values.

        Returns:
            Fully qualified Dummy configuration object
        """
        if not self.instance_name:
            return self
        secrets = cast(DummySecrets, state.instance_secrets["dummy"][self.instance_name])
        return self.model_copy(
            update={
                "instance_name": self.instance_name,
                "instance_value": api_get(secrets, "/api/v1/settings")["instanceValue"],
            },
        )

    @classmethod
    def from_remote(cls, secrets: DummySecrets) -> Self:
        """
        Read configuration from a remote instance and return it as a configuration object.

        Args:
            secrets (DummySecrets): Instance host and secrets information

        Returns:
            Configuration object for remote instance
        """
        return cls(
            trash_id=None,
            **cls.get_local_attrs(
                remote_map=cls._remote_map,
                remote_attrs=api_get(secrets, "/api/v1/settings"),
            ),
        )

    def update_remote(
        self,
        tree: str,
        secrets: DummySecrets,
        remote: Self,
        check_unmanaged: bool = False,
    ) -> bool:
        """
        Compare this configuration to a remote instance's, and update the remote to match.

        Args:
            tree (str): Configuration tree represented as a string. Mainly used in logging.
            secrets (DummySecrets): Remote instance host and secrets information.
            remote (Self): Remote instance configuration for the current section.
            check_unmanaged (bool, optional): Set unmanaged fields to defaults (default `False`).

        Returns:
            `True` if the remote configuration changed, otherwise `False`
        """
        changed, remote_attrs = self._resolve().get_update_remote_attrs(
            tree=tree,
            remote=remote,
            remote_map=self._remote_map,
            check_unmanaged=check_unmanaged,
            set_unchanged=True,
        )
        if changed:
            api_post(secrets, "/api/v1/settings", remote_attrs)
            return True
        return False

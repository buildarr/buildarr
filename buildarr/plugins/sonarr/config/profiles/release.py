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
Sonarr plugin release profile configuration.
"""


from __future__ import annotations

import json
import sys

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, cast

from pydantic import validator
from typing_extensions import Self

from buildarr.config import ConfigBase, NonEmptyStr, RemoteMapEntry, TrashID
from buildarr.config.exceptions import ConfigTrashIDNotFoundError
from buildarr.logging import plugin_logger
from buildarr.secrets import SecretsPlugin

from ...secrets import SonarrSecrets
from ...util import api_delete, api_get, api_post, api_put


class TrashFilter(ConfigBase):
    """
    Defines various ways that release profile terms from the guide are synchronised with Sonarr.
    These terms have individual trash IDs, and using this filter allows you to
    pick and choose which parts of the release profile you want to use.

    ```yaml
    ...
      release_profiles:
        definitions:
          Optionals:
            trash_id: 76e060895c5b8a765c310933da0a5357
            filter:
              include:
                - ea83f4740cec4df8112f3d6dd7c82751 # Prefer Season Packs
                - cec8880b847dd5d31d29167ee0112b57 # Ignore 720p/1080p HEVC (Golden Rule)
                # All the other preferred words in the 'Optionals' profile
                # are ignored.
    ```

    The attributes `include` and `exclude` are mutually exclusive.
    If both are defined, `include` is used.
    """

    # TODO: mutual exclusion

    include: List[TrashID] = []
    """
    A list of `trash_id` values representing terms (`Required`, `Ignored`, or `Preferred`)
    that should be included in the created Release Profile in Sonarr.

    Terms that are *not* specified here are excluded automatically.
    """

    exclude: List[TrashID] = []
    """
    A list of `trash_id` values representing terms (`Required`, `Ignored`, or `Preferred`)
    that should be excluded from the created Release Profile in Sonarr.

    Terms that are *not* specified here are included automatically.
    """


class PreferredWord(ConfigBase):
    """
    Buildarr object representing a Preferred Word in a Release Profile.
    """

    term: NonEmptyStr
    score: int


class ReleaseProfile(ConfigBase):
    # Release profile data structure.
    #
    # There are two types of release profile: the type where filters are manually defined,
    # and the type where the profile is simply a reference to a pre-made
    # TRaSH-Guides profile (with some handling options).

    enable: bool = True
    """
    Enable the release profile in Sonarr.

    If set to `False`, the release profile will be uploaded to Sonarr, but inactive.
    """

    trash_id: Optional[TrashID] = None
    """
    The trash ID of the release profile to import from TRaSH-Guides metadata.

    If not specified, Buildarr assumes the release profile filters are manually defined.
    """

    # Preferred word Trash ID filter for this release profile.
    # See the `TrashFilter` class for more details.
    # If undefined, use the TRaSH-Guides provided release profile defaults.
    filter: TrashFilter = TrashFilter()
    """
    ###### ::: buildarr.plugins.sonarr.config.profiles.release.TrashFilter
        options:
          members:
            - include
            - exclude
          show_root_heading: false
          show_source: false
    """

    strict_negative_scores: bool = False
    """
    Enables preferred term scores less than 0 to be instead treated
    as "Must Not Contain" (ignored) terms.

    For example, if something is "Preferred" with a score of `-10,` it will instead
    be put in the "Must Not Contain" section of the uploaded release profile.
    """

    # TODO: constraint that checks at least one of these filters
    #       are not empty, if trash_id is not defined.

    must_contain: Set[NonEmptyStr] = set()
    """
    A list of terms to mark as "Must Contain" in Sonarr.

    The release will be rejected if it does not contain one or more of terms
    (case insensitive) or regular expressions.
    """

    must_not_contain: Set[NonEmptyStr] = set()
    """
    A list of terms to mark as "Must Not Contain" in Sonarr.

    The release will be rejected if it contains one or more of terms (case insensitive)
    or regular expressions.
    """

    preferred: List[PreferredWord] = []
    """
    Assign a score to terms (or a regular expression patterns) found in the file name
    of a release, and prefer it or not prefer it depending on the result
    of comparing a release file name against all terms.

    ```yaml
    ...
      release_profiles:
        Example:
          preferred:
            - term: "/\b(amzn|amazon)\b(?=[ ._-]web[ ._-]?(dl|rip)\b)/i"
              score: 100
            - term: "/(-BRiNK|-CHX|-GHOSTS|-EVO|)\b/i"
              score: -10000
    ```

    The release will be preferred based on each term's score.
    Positive scores will be more preferred, and negative scores will be less preferred.
    """

    include_preferred_when_renaming: bool = False
    """
    Add preferred words to the file name as `{Preferred Words}`
    when doing automatic renaming in Sonarr.
    """

    # None = (Any)
    indexer: Optional[NonEmptyStr] = None
    """
    When set to `None` or an empty string, use any available indexer.
    """

    #
    tags: Set[NonEmptyStr] = set()
    """
    A list of one or more strings representing tags that will be applied to this release profile.

    All tags on an existing release profile (if present) are removed
    and replaced with only the tags in this list.

    If an empty list is explicitly defined, no tags will be set on the release profile,
    and any existing tags (if present) are removed.
    """

    @validator("preferred")
    def sort_preferred(cls, preferred: Iterable[PreferredWord]) -> List[PreferredWord]:
        return sorted(
            preferred,
            key=lambda q: ((sys.maxsize - q.score), q.term),
        )

    @classmethod
    def _get_remote_map(
        cls,
        indexer_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> List[RemoteMapEntry]:
        return [
            ("enable", "enabled", {}),
            ("must_contain", "required", {"encoder": lambda v: sorted(v)}),
            ("must_not_contain", "ignored", {"encoder": lambda v: sorted(v)}),
            (
                "preferred",
                "preferred",
                {
                    "decoder": lambda v: [
                        PreferredWord(term=p["key"], score=p["value"]) for p in v
                    ],
                    "encoder": lambda v: [{"key": p.term, "value": p.score} for p in v],
                },
            ),
            ("include_preferred_when_renaming", "includePreferredWhenRenaming", {}),
            (
                "indexer",
                "indexerId",
                {
                    "decoder": lambda v: next(
                        (ind for ind, ind_id in indexer_ids.items() if ind_id == v),
                        None,
                    ),
                    "encoder": lambda v: indexer_ids[v] if v else 0,
                },
            ),
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
        indexer_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
        remote_attrs: Mapping[str, Any],
    ) -> Self:
        return cls(**cls.get_local_attrs(cls._get_remote_map(indexer_ids, tag_ids), remote_attrs))

    def render_trash_metadata(self, sonarr_metadata_dir: Path) -> ReleaseProfile:
        if not self.trash_id:
            return self
        for profile_file in (sonarr_metadata_dir / "rp").iterdir():
            with profile_file.open() as f:
                profile: Dict[str, Any] = json.load(f)
                if cast(str, profile["trash_id"]).lower() == self.trash_id:
                    #
                    must_contain: List[str] = []
                    must_not_contain: List[str] = []
                    preferred: List[PreferredWord] = []
                    #
                    for required in profile["required"]:
                        if isinstance(required, dict):
                            term: str = required["term"]
                            if (
                                "trash_id" in required
                                and cast(str, required["trash_id"]).lower() in self.filter.exclude
                            ):
                                must_not_contain.append(term)
                            else:
                                must_contain.append(term)
                        else:
                            must_contain.append(required)
                    #
                    for ignored in profile["ignored"]:
                        if isinstance(ignored, dict):
                            term = ignored["term"]
                            if (
                                "trash_id" in ignored
                                and cast(str, ignored["trash_id"]).lower() in self.filter.include
                            ):
                                must_contain.append(term)
                            else:
                                must_not_contain.append(term)
                        else:
                            must_not_contain.append(ignored)
                    #
                    for pref in profile["preferred"]:
                        score: int = pref["score"]
                        for term_obj in pref["terms"]:
                            term_trash_id: Optional[str] = None
                            if isinstance(term_obj, dict):
                                term = term_obj["term"]
                                if "trash_id" in term_obj:
                                    term_trash_id = cast(str, term_obj["trash_id"]).lower()
                            else:
                                term = term_obj
                            if (self.strict_negative_scores and score < 0) or (
                                term_trash_id and term_trash_id in self.filter.exclude
                            ):
                                must_not_contain.append(term)
                            else:
                                preferred.append(PreferredWord(term=term, score=score))
                    #
                    return ReleaseProfile(
                        must_contain=must_contain,
                        must_not_contain=must_not_contain,
                        preferred=preferred,
                        **{
                            attr_name: getattr(self, attr_name)
                            for attr_name in (
                                "enable",
                                "indexer",
                                "include_preferred_when_renaming",
                                "tags",
                            )
                            if attr_name in self.__fields_set__
                        },
                    )
        raise ConfigTrashIDNotFoundError(
            f"Unable to find Sonarr release profile file with trash ID '{self.trash_id}'",
        )

    def _create_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        profile_name: str,
        indexer_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> None:
        api_post(
            sonarr_secrets,
            "/api/v3/releaseprofile",
            {
                "name": profile_name,
                **self.get_create_remote_attrs(tree, self._get_remote_map(indexer_ids, tag_ids)),
            },
        )

    def _update_remote(
        self,
        tree: str,
        sonarr_secrets: SonarrSecrets,
        remote: ReleaseProfile,
        profile_id: int,
        profile_name: str,
        indexer_ids: Mapping[str, int],
        tag_ids: Mapping[str, int],
    ) -> bool:
        changed, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._get_remote_map(indexer_ids, tag_ids),
            check_unmanaged=True,
            set_unchanged=True,
        )
        if changed:
            api_put(
                sonarr_secrets,
                f"/api/v3/releaseprofile/{profile_id}",
                {"id": profile_id, "name": profile_name, **remote_attrs},
            )
            return True
        return False

    def _delete_remote(self, tree: str, sonarr_secrets: SonarrSecrets, profile_id: int) -> None:
        plugin_logger.info("%s: (...) -> (deleted)", tree)
        api_delete(sonarr_secrets, f"/api/v3/releaseprofile/{profile_id}")


class SonarrReleaseProfilesSettingsConfig(ConfigBase):
    """
    Configuration parameters for controlling how Buildarr handles release profiles.
    """

    delete_unmanaged: bool = False
    """
    Automatically delete release profiles not defined in Buildarr.
    """

    definitions: Dict[str, ReleaseProfile] = {}
    """
    Define release profiles to configure on Sonarr here.

    If there are no release profiles defined and `delete_unmanaged` is `False`,
    Buildarr will not modify existing release profiles, but if `delete_unmanaged` is `True`,
    **Buildarr will delete all existing profiles. Be careful when using `delete_unmanaged`.**
    """

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrReleaseProfilesSettingsConfig:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        profiles: List[Dict[str, Any]] = api_get(sonarr_secrets, "/api/v3/releaseprofile")
        indexer_ids: Dict[str, int] = (
            {tag["name"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/indexer")}
            if any(profile["indexerId"] for profile in profiles)
            else {}
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(profile["tags"] for profile in profiles)
            else {}
        )
        return SonarrReleaseProfilesSettingsConfig(
            definitions={
                profile["name"]: ReleaseProfile._from_remote(indexer_ids, tag_ids, profile)
                for profile in profiles
            },
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrReleaseProfilesSettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        #
        changed = False
        sonarr_secrets = cast(SonarrSecrets, secrets)
        #
        profile_ids: Dict[str, int] = {
            profile_json["name"]: profile_json["id"]
            for profile_json in api_get(sonarr_secrets, "/api/v3/releaseprofile")
        }
        indexer_ids: Dict[str, int] = (
            {tag["name"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/indexer")}
            if any(p.indexer for p in self.definitions.values())
            or any(p.indexer for p in remote.definitions.values())
            else {}
        )
        tag_ids: Dict[str, int] = (
            {tag["label"]: tag["id"] for tag in api_get(sonarr_secrets, "/api/v3/tag")}
            if any(profile.tags for profile in self.definitions.values())
            or any(profile.tags for profile in remote.definitions.values())
            else {}
        )
        #
        for profile_name, profile in self.definitions.items():
            profile_tree = f"{tree}.definitions[{repr(profile_name)}]"
            #
            if profile_name not in remote.definitions:
                profile._create_remote(
                    profile_tree,
                    sonarr_secrets,
                    profile_name,
                    indexer_ids,
                    tag_ids,
                )
                changed = True
            #
            else:
                if profile._update_remote(
                    profile_tree,
                    sonarr_secrets,
                    remote.definitions[profile_name],
                    profile_ids[profile_name],
                    profile_name,
                    indexer_ids,
                    tag_ids,
                ):
                    changed = True
        #
        for profile_name, profile in remote.definitions.items():
            if profile_name not in self.definitions:
                profile_tree = f"{tree}.definitions[{repr(profile_name)}]"
                if self.delete_unmanaged:
                    profile._delete_remote(
                        profile_tree,
                        sonarr_secrets,
                        profile_ids[profile_name],
                    )
                    changed = True
                else:
                    plugin_logger.debug("%s: (...) (unmanaged)", profile_tree)
        #
        return changed

---
name: Release
about: Template for creating a checklist issue for a new release.
title: Tag v<new version>
labels: release
assignees: Callum027

---

Checklist:

1. [ ] Update the `tool.poetry.version` field in `pyproject.toml`
2. [ ] Get the raw changelog using the following command:
   ```bash
   $ git log --oneline --decorate v<previous version>
   ```
3. [ ] Add release notes to `docs/release-notes.md` in the following format:
   ```markdown
   ## [v<new release>](https://github.com/buildarr/buildarr/releases/tag/v<new release>) - <release date e.g. 2023-02-19>

   This is a <feature|bugfix> release that <short description of release>.

   <longer desription of headline features>

   ### Added

   * Add a thing ([#<issue number](https://github.com/buildarr/buildarr/pull/<issue number>))

   ### Changed

   * Change a thing ([#<issue number](https://github.com/buildarr/buildarr/pull/<issue number>))

   ### Removed

   * Remote a thing ([#<issue number](https://github.com/buildarr/buildarr/pull/<issue number>))
   ```
4. [ ] Create pull request: (paste link to pull request here)
5. [ ] Merge pull request
6. [ ] Tag the new release
7. [ ] Check that the release was automatically published to PyPI: (paste link to workflow here)
8. [ ] Push an update to http://github.com/buildarr/buildarr-docker to release to Docker Hub

# Zenodo DOI and citation

PyMOL Figure Agent can be archived on Zenodo through GitHub releases.
Once a GitHub release is created and the Zenodo GitHub integration is enabled,
Zenodo will assign a DOI automatically.

## How it works

- **CITATION.cff** is used by GitHub to show "Cite this repository" on the repo page.
- **.zenodo.json** provides rich metadata that Zenodo reads when archiving a release.
- After the DOI is obtained, update `CITATION.cff`, `README.md` badges, release notes,
  and `.zenodo.json` as needed.

## DOI types

| Type | Description |
|---|---|
| **Version DOI** | DOI specific to a particular release/version. Created per GitHub release. |
| **Concept DOI** | DOI that represents the software across all versions. Zenodo provides this if the repository record is set up as a concept. |

## Checklist before creating a Zenodo DOI

- [ ] `main` is stable.
- [ ] `CHANGELOG.md` is up to date.
- [ ] `CITATION.cff` is up to date.
- [ ] `.zenodo.json` is valid JSON.
- [ ] GitHub release created with a semantic version tag (e.g., `v0.2.0`).
- [ ] Zenodo GitHub integration is enabled for this repository.
- [ ] DOI obtained from Zenodo.
- [ ] DOI added to `CITATION.cff`.
- [ ] DOI added to `README.md` badges.

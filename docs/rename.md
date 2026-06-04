# Project rename

## Summary

- **Previous name:** PyMOL Figure Agent
- **New name:** MolWeaver
- **Effective:** 2026-06-03

## Rationale

PyMOL Figure Agent started as a figure-generation API. The project has since evolved
into a broader local control layer for agent-driven molecular scene construction,
structural analysis, alignment, measurement, editable PyMOL sessions, reproducible
scripts and future docking/MD workflows. The name **MolWeaver** better reflects this
broader scope — molecular tool orchestration rather than just figure generation.

PyMOL remains the primary molecular engine behind MolWeaver. The project is not
affiliated with, endorsed by, or sponsored by Schrödinger or the official PyMOL project.

## GitHub redirect

When the repository is renamed on GitHub (Settings → General → Repository name),
GitHub automatically redirects old URLs to the new one. Users with local clones
should update their remotes:

```bash
git remote set-url origin git@github.com:BrandonGBz/molweaver.git
# or
git remote set-url origin https://github.com/BrandonGBz/molweaver.git
```

## What changed

- Package name: `pymol-figure-agent` → `molweaver` (in `pyproject.toml`)
- Conda environment name: `pymol-figure-agent` → `molweaver` (in `environment.yml`)
- API title, docs, citations, badges, and all text references.
- The `CITATION.cff` title, `.zenodo.json` title, and repository URLs.

## What did NOT change

- Endpoints, API surface, and functional logic remain identical.
- PyMOL remains the molecular engine and is referenced throughout the project.
- The project is still local-first, open-source, and agent-ready.
- No breaking changes for existing users other than the package name.

# Agent Instructions

These rules apply to AI coding agents working on MolWeaver.

## Operating mode

- Do not work directly on `main`.
- Inspect the repository before changing files.
- Use PLAN ONLY mode until a human explicitly authorizes BUILD work.
- In BUILD mode, keep changes scoped and reversible.
- Do not commit, tag, push, or publish releases unless explicitly requested.

## Safety

- Never add secrets, tokens, credentials, real `.env` files, or private file paths.
- Do not add private structures, unpublished research data, `.pse` sessions, or generated heavy outputs.
- Do not include PyMOL, conda environments, micromamba downloads, or other binaries in the repository.
- Do not expose the API outside `127.0.0.1` by default.
- Do not enable arbitrary PyMOL command execution unless the user explicitly accepts the risk.
- Do not add heavy dependencies without explaining why they are needed.
- Agents should use structured operations whenever possible. Do not use trusted-script or raw PyMOL commands unless explicitly authorized by the user.

## Examples

- Use public PDB IDs such as `1GYC`.
- Do not modify examples to use local private paths.
- Keep generated images out of git unless a maintainer explicitly approves a small public asset.
- Agents may work with local user-provided molecular files during runtime. These files must not be committed unless they are intentional public examples.

## Validation

Before final delivery, run:

```powershell
git status --short
git diff --stat
python -m ruff check .
python -m pytest
```

If PyMOL is available locally, also test `/health` and a public `1GYC` render.

## Final response

Report branch, changed files, created files, summary, tests, manual checks, risks, and next steps.

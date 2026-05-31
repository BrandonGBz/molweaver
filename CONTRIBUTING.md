# Contributing

Thank you for helping improve PyMOL Figure Agent. This project is intended for reproducible scientific visualization and AI-agent workflows.

## Branches

- Do not work directly on `main`.
- Use short branches such as `docs/update-agent-guide`, `fix/output-name-validation`, or `feat/new-preset`.

## Commits

Use Conventional Commits:

- `feat: add surface preset`
- `fix: reject unsafe output names`
- `docs: improve Windows installation guide`
- `test: cover render request validation`

## Local checks

```powershell
python -m ruff check .
python -m pytest
```

Real PyMOL rendering tests are currently local/manual because CI does not install PyMOL.

## Presets

New presets should include:

- a clear scientific use case,
- safe PyMOL selections,
- a JSON example using public PDB `1GYC` or another public structure,
- documentation in `docs/presets.md`.

## Bug reports

Please include:

- OS and Python version,
- PyMOL installation method,
- endpoint and request JSON,
- sanitized error output.

Do not include private file paths, unpublished structures, credentials, or generated research images.

## Documentation

Docs contributions are welcome. Keep examples public, reproducible, and free of personal paths.

## What will not be accepted

- Private or unpublished structures without an explicit public license.
- Secrets, credentials, tokens, or real `.env` files.
- Heavy generated outputs, conda environments, micromamba binaries, or rendered image folders.
- Arbitrary PyMOL command execution enabled by default.

# Security Policy

## Reporting vulnerabilities

Do not open public issues for security vulnerabilities. Use GitHub Private Vulnerability Reporting for this repository.

If private reporting is temporarily unavailable, contact the maintainer privately through GitHub before sharing technical details.

## Repository scope

The repository contains the engine, documentation, tests and public examples. User structures, trajectories, generated PyMOL sessions, generated scripts, rendered images and metadata are local runtime artifacts and are intentionally ignored by Git.

## Security model

The project follows a local-first design and binds to `127.0.0.1` by default. It should not be exposed directly to the internet without authentication, sandboxing and input allowlists.

- Local-first API: bind to `127.0.0.1` by default.
- Structured operations: prefer typed JSON operations over raw PyMOL command execution.
- Original input preservation: operations modify temporary scenes or exported sessions, not source molecular files.
- Runtime artifacts: `outputs/`, `sessions/`, `scripts/` and generated files are local execution artifacts.
- Path safety: output names and served artifact names must be basename-only.
- File handling: allowlist supported molecular extensions, enforce size limits, and do not serve arbitrary paths.
- Resource limits: width, height, dpi, timeout and file size limits prevent accidental runaway jobs.
- External fetching: PDB downloads should be restricted to expected public sources such as RCSB; do not accept arbitrary URLs unless a strict allowlist is implemented.
- Trusted script mode: disabled by default; advanced local-only mode.
- MCP future: use strict schemas, least privilege, no broad filesystem access, no raw shell commands, and no silent tool changes.

## Current mitigations

- The default host is `127.0.0.1`.
- `output_name` is validated as a base name, not a path.
- `trusted-script` is disabled unless `PYMOL_ALLOW_UNSAFE_COMMANDS=1`.
- Local structure paths can be restricted with `PYMOL_ALLOWED_INPUT_DIR`.
- Maximum input size can be limited with `PYMOL_MAX_FILE_SIZE_MB`.
- `/sessions/{filename}` and `/scripts/{filename}` only serve files from their dedicated directories.

## Notes

This repository is not a substitute for institutional security review when deployed beyond a single-user local environment.

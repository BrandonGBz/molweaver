# Security Model

This document summarizes OWASP-aligned security considerations for a local PyMOL control layer.

The project is not OWASP certified and does not claim compliance. It is designed with OWASP-aligned security considerations for local-first scientific tooling.

## Relevant threat areas

- OWASP API Security Top 10:
  - resource consumption from large structures, high render sizes or long timeouts,
  - security misconfiguration if the API is exposed beyond `127.0.0.1`,
  - API inventory concerns if extra endpoints are added without documentation,
  - SSRF-style concerns if external fetching is expanded beyond trusted public sources.
- OWASP File Upload Cheat Sheet:
  - extension allowlists,
  - generated filenames,
  - size limits,
  - safe file serving.
- OWASP Input Validation:
  - allowlist validation,
  - typed schemas,
  - bounded ranges,
  - regex validation for names and selectors.
- OWASP AI Agent Security:
  - least privilege,
  - tool scoping,
  - human-in-the-loop for high-impact actions,
  - avoid arbitrary shell or command execution.
- OWASP MCP Security:
  - tool poisoning,
  - tool shadowing,
  - confused deputy risks,
  - strict schemas,
  - sandboxing and no broad filesystem access.

## Practical controls in this repository

- Bind to `127.0.0.1` by default.
- Keep structured JSON operations as the preferred interface.
- Preserve the original molecular input and operate on temporary job copies.
- Keep runtime artifacts local: `outputs/`, `sessions/`, `scripts/`.
- Use basename-only checks for served artifacts.
- Restrict supported molecular file types and file sizes.
- Prefer known public sources for downloads, such as RCSB.
- Disable trusted raw-script execution by default.

### MCP-specific controls

The MCP server (`mcp_server.py`) adds additional safeguards:

- **No raw PyMOL commands.** All MCP tools use structured operations with Pydantic validation. The trusted-script endpoint is not exposed through MCP.
- **Strict tool schemas.** Every tool parameter is validated with type, range, and pattern constraints.
- **stderr-only logging.** No log output is written to stdout, preventing protocol interference in stdio mode.
- **No arbitrary filesystem access.** Local file paths are validated against allowed extensions and optional `PYMOL_ALLOWED_INPUT_DIR` restrictions.
- **No shell execution.** All PyMOL operations run through the existing subprocess pipeline with controlled arguments.
- **No URLs beyond RCSB PDB.** The server does not fetch from arbitrary URLs; only `pdb_id` downloads from the trusted RCSB PDB endpoint are supported.
- **Descriptive analysis only.** Distance measurements and site analyses are geometric descriptions, not biochemical validations.

## Operational guidance

When extending the API, add explicit validation, bounded resource limits and clear documentation for any new tool or endpoint. Do not silently add filesystem or shell access in agent-facing features.

# Changelog

## [0.3.0] - Unreleased

### Changed
- Project renamed from PyMOL Figure Agent to MolWeaver to reflect its broader scope
  beyond figure generation.

### Added
- Optional MCP server exposing MolWeaver capabilities as agent tools.
- MCP tools: `render_molecular_figure`, `inspect_structure`, `measure_distance`,
  `analyze_binding_site`, `align_structures`, `generate_site_report`, `export_pymol_script`.
- MCP prompts: `create_publication_figure`, `inspect_active_site`, `align_and_compare_structures`,
  `prepare_docking_pose_figure`, `render_md_snapshot`.
- MCP resources for capabilities, presets, security model, and examples.
- Full cross-platform support: Windows, Linux, and macOS tested.
- MCP documentation (`docs/mcp.md`) and example client configuration.
- Agent prompt recipes (`docs/agent-prompt-recipes.md`).
- Zenodo DOI preparation (`.zenodo.json`, `docs/zenodo.md`).

## [0.2.0] - 2026-06-01

### Added

- Structured PyMOL scene operations for agent-ready rendering workflows.
- Structural inspection, distance measurement, site analysis, and alignment endpoints.
- Editable `.pse` and reproducible `.pml` artifact exports.
- One-command Windows installer and experimental Linux/macOS installer.
- Expanded visual gallery with publication-style examples.

## [0.1.0-alpha] - 2026-05-31

### Added

- Initial FastAPI bridge for PyMOL rendering.
- Health endpoint.
- Render endpoint.
- Support for PDB ID and local structure paths.
- Basic visualization presets.
- Ray-traced PNG output.
- Initial documentation for AI agents.

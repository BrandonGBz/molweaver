# PyMOL Figure Agent

[![CI](https://github.com/BrandonGBz/pymol-figure-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/BrandonGBz/pymol-figure-agent/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-v0.1.0--alpha-orange.svg)](CHANGELOG.md)

PyMOL Figure Agent is an open-source API bridge that allows AI agents and scientific users to generate reproducible molecular visualizations with PyMOL for structural bioinformatics, theses, presentations, and publication-ready figures.

## What problem does it solve?

PyMOL is powerful, but reproducible figure generation often depends on manual GUI steps or ad hoc scripts. This project exposes a local FastAPI service so humans, notebooks, and AI coding agents can request consistent molecular renders through JSON.

## Intended users

- Structural bioinformaticians
- Wet-lab scientists
- Graduate students
- Educators
- AI coding agents

## Main features

- Render molecular structures through a local API.
- Load structures from a public PDB ID or local `.pdb`/`.cif` files.
- Apply visualization presets such as `publication_cartoon`, `copper_sites`, and `surface`.
- Generate ray-traced PNG images.
- Return `image_path` and `image_url` for downstream workflows.
- Designed for AI-agent workflows and reproducible figure prompts.

## Project status

Experimental `v0.1.0-alpha`. The API is usable locally, but interfaces may change before `v1.0.0`.

## Requirements

- Python 3.10+
- PyMOL Open Source installed through conda-forge
- micromamba or conda recommended
- Windows tested
- Linux support is planned and documented as experimental

PyMOL is intentionally not installed from `pip` in this project. On Windows, `pip install pymol-open-source` may fail because of native DLL dependencies. Use conda-forge instead.

## Quick installation

```powershell
git clone https://github.com/BrandonGBz/pymol-figure-agent.git
cd pymol-figure-agent
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\setup_pymol_env.ps1
.\start_server.ps1
```

Open the API docs:

```text
http://127.0.0.1:8010/docs
```

## Quick use

Health check:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8010/health"
```

Render public PDB `1GYC`:

```powershell
$body = @{
  pdb_id = "1GYC"
  output_name = "1gyc_copper_sites"
  preset = "copper_sites"
  color = "chainbow"
  ray = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8010/render" -Method Post -ContentType "application/json" -Body $body
```

Python example:

```python
import requests

payload = {
    "pdb_id": "1GYC",
    "output_name": "1gyc_copper_sites",
    "preset": "copper_sites",
    "color": "chainbow",
    "ray": True,
}

response = requests.post("http://127.0.0.1:8010/render", json=payload, timeout=240)
response.raise_for_status()
print(response.json()["image_path"])
```

## Example for AI agents

Prompt:

```text
Use the local PyMOL API at http://127.0.0.1:8010.
Load PDB 1GYC, apply the copper_sites preset, render a high-quality PNG, and return image_path.
```

Agent JSON:

```json
{
  "pdb_id": "1GYC",
  "output_name": "1gyc_copper_sites",
  "preset": "copper_sites",
  "color": "chainbow",
  "ray": true
}
```

## Limitations

- This project is local-first and should not be exposed directly to the internet.
- CI does not install PyMOL yet; real rendering tests are local/manual.
- Local file paths are OS-specific.
- Some PyMOL installations differ in command-line behavior.

## Security

Run the API on `127.0.0.1` by default. Do not expose it publicly without authentication, sandboxing, and input allowlists. Do not share private structures, unpublished research data, credentials, or absolute local paths in examples, issues, logs, or pull requests.

## Roadmap

- `v0.1.x`: hardening, more presets, better errors, more tests.
- `v0.2.x`: batch rendering, `.pml` export, metadata JSON, residue highlighting, distance measurements.
- `v0.3.x`: MCP server, CLI, agent tool schemas.
- `v1.0.0`: stable public release.

## Citation

If you use this software in academic work, please cite it. See [CITATION.cff](CITATION.cff).

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Schrodinger or the official PyMOL project. Users must comply with the licenses of PyMOL and all third-party dependencies.

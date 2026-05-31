# API Reference

Base URL:

```text
http://127.0.0.1:8010
```

## GET /health

Returns backend and output directory status.

Example response:

```json
{
  "status": "ok",
  "pymol_available": true,
  "backend": "bundled_conda_pymol2",
  "backend_command": ["tools/pymol_env/python.exe"],
  "message": "PyMOL/pymol2 detected in the local conda environment for this API.",
  "output_dir": "outputs"
}
```

If PyMOL is unavailable, `status` becomes `missing_pymol`.

## GET /capabilities

Returns supported inputs, presets, output format, and whether trusted scripts are enabled.

## POST /render

Render a molecule to PNG.

Request:

```json
{
  "pdb_id": "1GYC",
  "output_name": "1gyc_copper_sites",
  "preset": "copper_sites",
  "color": "chainbow",
  "ray": true,
  "width": 1600,
  "height": 1200
}
```

Response:

```json
{
  "job_id": "abc123",
  "image_url": "/images/1gyc_copper_sites.png",
  "image_path": "outputs/images/1gyc_copper_sites.png",
  "source_path": "outputs/jobs/abc123/1GYC.pdb",
  "metadata": {
    "backend": "bundled_conda_pymol2",
    "width": 1600,
    "height": 1200,
    "dpi": 300,
    "ray": true,
    "preset": "copper_sites",
    "warnings": []
  }
}
```

Use exactly one source:

- `pdb_id`
- `structure_path`
- `inline_pdb`

## GET /images/{filename}

Serves a generated PNG from `outputs/images`.

## Common errors

- `400`: invalid source, missing file, invalid PDB ID, unsupported extension.
- `413`: input file exceeds `PYMOL_MAX_FILE_SIZE_MB`.
- `422`: request schema validation error.
- `502`: PyMOL failed to render.
- `503`: PyMOL backend not available.

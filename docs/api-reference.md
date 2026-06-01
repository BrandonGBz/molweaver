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
  "render_quality": "high",
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

Local `structure_path` inputs support common structure formats including `.pdb`, `.ent`, `.pqr`, `.pdbqt`, `.cif`, `.mmcif`, `.sdf`, `.mol`, and `.mol2`.

## POST /inspect

Return a geometric structure summary using a controlled analysis job.

Request:

```json
{
  "source": {
    "pdb_id": "1GYC"
  },
  "include_solvent": false,
  "export_pml": false
}
```

Response:

```json
{
  "job_id": "abc123",
  "result": {
    "atom_count": 12345,
    "polymer_atom_count": 12000,
    "protein_atom_count": 11800,
    "nucleic_atom_count": 0,
    "solvent_atom_count": 0,
    "organic_ligand_atom_count": 40,
    "metal_atom_count": 6,
    "chains": ["A", "B"],
    "residue_count": 900,
    "organic_ligands": [],
    "metals": []
  },
  "metadata": {
    "backend": "bundled_conda_pymol2",
    "operation": "inspect",
    "analysis_version": "0.1.0-alpha"
  },
  "warnings": [
    "Geometric structural analysis is descriptive only and does not replace experimental validation, docking validation, molecular dynamics, thermodynamic analysis, or biochemical assays."
  ],
  "artifacts": {
    "analysis_spec_path": "outputs/jobs/abc123/analysis_spec.json",
    "result_json_path": "outputs/jobs/abc123/result.json"
  }
}
```

## POST /measure/distance

Measure a deterministic atom-to-atom or centroid-to-centroid distance using structured selectors.

Request:

```json
{
  "source": {
    "pdb_id": "1GYC"
  },
  "selector_a": {
    "element": "Cu"
  },
  "selector_b": {
    "organic": true
  },
  "export_pml": false
}
```

Response fields include `distance_angstrom`, selector atom counts, centroids, atom previews, and selection warnings.

## POST /analyze/site

Inspect the residue neighborhood around a metal, ligand, or other structured selector.

Request:

```json
{
  "source": {
    "pdb_id": "1GYC"
  },
  "center": {
    "element": "Cu"
  },
  "radius_angstrom": 5.5,
  "include_solvent": false,
  "export_pml": false
}
```

Response fields include `nearby_residue_count`, `nearby_residues`, `nearby_metals`, and `nearby_organic_ligands`.

## POST /align

Align two public structures with a controlled method and optional rendering.

Request:

```json
{
  "reference_pdb_id": "1GYC",
  "mobile_pdb_id": "1KYA",
  "method": "align",
  "render": false,
  "export_pml": false
}
```

Response:

```json
{
  "job_id": "abc123",
  "result": {
    "rmsd_angstrom": 1.234,
    "aligned_atoms": 850,
    "method": "align",
    "reference_source": {
      "type": "pdb_id",
      "id": "1GYC"
    },
    "mobile_source": {
      "type": "pdb_id",
      "id": "1KYA"
    }
  },
  "warnings": [
    "Structural alignment is descriptive geometry only and does not imply conserved catalytic activity, binding affinity, stability, thermodynamic behavior, molecular dynamics behavior, or experimental validation."
  ],
  "artifacts": {
    "analysis_spec_path": "outputs/jobs/abc123/analysis_spec.json",
    "result_json_path": "outputs/jobs/abc123/result.json"
  }
}
```

When `render=true`, the response can also include an `image_url` artifact for the aligned figure.

## GET /images/{filename}

Serves a generated PNG from `outputs/images`.

## Common errors

- `400`: invalid source, missing file, invalid PDB ID, unsupported extension.
- `413`: input file exceeds `PYMOL_MAX_FILE_SIZE_MB`.
- `422`: request schema validation error.
- `502`: PyMOL failed to render.
- `503`: PyMOL backend not available.

# Agent Usage

AI coding agents can use this API as a local-first tool for reproducible molecular figures and geometric structural summaries.

## Agent system hint

```text
You have access to a local PyMOL API at http://127.0.0.1:8010.
Use POST /render to generate molecular PNG images.
Use public PDB IDs for examples. Do not include private local paths in public outputs.
Return image_path and image_url after rendering.
```

## Example task

```text
Load PDB 1GYC, apply copper_sites preset, render high-quality PNG and return path.
```

## Beyond rendering

The same API also supports agent-friendly structural analysis:

- `POST /inspect` for atom counts, chain summaries, and ligand or metal inventory.
- `POST /measure/distance` for structured distances between atoms, residues, ligands, or metal centers.
- `POST /analyze/site` for geometric neighborhoods around a site of interest.
- `POST /align` for reproducible structural alignment using public PDB structures such as `1GYC` and `1KYA`.

These endpoints are descriptive and geometric. They should not be presented as biochemical validation or mechanistic proof.

## Example request

```json
{
  "pdb_id": "1GYC",
  "output_name": "1gyc_copper_sites",
  "preset": "copper_sites",
  "color": "chainbow",
  "ray": true
}
```

## Python client

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
print(response.json())
```

## Guidance for agents

- Prefer `pdb_id` for public examples.
- Use `structure_path` only when the user explicitly provides a local file.
- Never echo private paths in public documentation or commits.
- Do not use `/render/trusted-script` unless a human explicitly enables it and accepts the risk.
- Keep selectors structured and avoid free-form PyMOL command strings.
- Treat geometry metrics, distances, and alignments as descriptive outputs.

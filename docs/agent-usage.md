# Agent Usage

AI coding agents can use this API as a local agent-ready PyMOL control layer for molecular visualization, structural inspection, alignment, measurement and reproducible figure generation.

## Agent system hint

```text
You have access to a local PyMOL API at http://127.0.0.1:8010.
Use POST /render to generate molecular PNG images.
Use public PDB IDs for examples. Do not include private local paths in public outputs.
Return image_path and image_url after rendering.
```

## Example task

```text
Load a public structure, build a clean cartoon-and-ligand scene, hide solvent, highlight the key atoms, render a PNG, and export an editable session.
```

## Beyond rendering

The same API also supports agent-friendly structural analysis:

- `POST /inspect` for atom counts, chain summaries, and ligand or metal inventory.
- `POST /measure/distance` for structured distances between atoms, residues, ligands, or metal centers.
- `POST /analyze/site` for geometric neighborhoods around a site of interest.
- `POST /align` for reproducible structural alignment using public PDB structures such as `1GYC` and `1KYA`.
- `export_session=true` and `export_script=true` on `/render` when the user wants local editable artifacts.
- `operations` on `/render` when the user wants structured scene control such as `show`, `hide`, `color`, `remove`, `select`, `label`, `zoom`, `orient`, `center`, `set_background`, or `set_transparency`.

These endpoints are descriptive and geometric. They should not be presented as biochemical validation or mechanistic proof.

## Example request

```json
{
  "pdb_id": "1GYC",
  "output_name": "custom_scene",
  "operations": [
    {
      "action": "remove",
      "selection": "solvent"
    },
    {
      "action": "show",
      "representation": "cartoon",
      "selection": "polymer.protein"
    },
    {
      "action": "color",
      "selection": "polymer.protein",
      "color": "slate"
    },
    {
      "action": "show",
      "representation": "sticks",
      "selection": "organic"
    }
  ],
  "ray": true,
  "export_session": true,
  "export_script": true
}
```

## Python client

```python
import requests

payload = {
    "pdb_id": "1GYC",
    "output_name": "custom_scene",
    "operations": [
        {"action": "remove", "selection": "solvent"},
        {"action": "show", "representation": "cartoon", "selection": "polymer.protein"},
        {"action": "color", "selection": "polymer.protein", "color": "slate"},
    ],
    "ray": True,
    "export_session": True,
    "export_script": True,
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
- Treat `.pse` and `.pml` outputs as local user artifacts, not repository assets.
- Future MD workflows should be documented as planned capabilities until they are implemented and tested.

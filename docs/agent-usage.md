# Agent Usage

AI coding agents can use this API as a local tool for reproducible molecular figures.

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

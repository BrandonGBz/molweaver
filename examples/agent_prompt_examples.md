# Agent Prompt Examples

## Basic render

```text
Use the local PyMOL API at http://127.0.0.1:8010.
Render public PDB 1GYC with preset publication_cartoon and return image_path.
```

## Copper sites

```text
Load PDB 1GYC, apply copper_sites preset, render high-quality PNG and return path.
```

## Local file, private workflow

```text
The user provided a local structure path. Use POST /render with structure_path.
Do not write the private path into public documentation or commits.
```

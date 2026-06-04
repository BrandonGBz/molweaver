# Structured PyMOL Operations

MolWeaver is designed as a local agent-ready control layer for PyMOL. The goal is not just to render presets, but to let an agent translate natural-language instructions into controlled JSON operations that PyMOL can execute locally.

## Purpose

- Build molecular scenes reproducibly.
- Keep PyMOL command execution structured and typed.
- Preserve the original molecular input file.
- Export local runtime artifacts such as PNG, `.pse`, and `.pml`.

## Current operations

Current structured scene operations supported by `/render` include:

- `show`
- `hide`
- `color`
- `remove`
- `select`
- `label`
- `zoom`
- `orient`
- `center`
- `set_representation`
- `set_background`
- `set_transparency`

These operations are executed against the temporary scene for the job or the exported session. They do not modify the user’s original source file.

## Planned operations

Future versions may add more fine-grained selection helpers, frame-based scene building for molecular dynamics workflows, and richer alignment or comparison templates. These additions should remain structured and bounded.

## How agents should translate instructions

An agent should map the user’s request into a small sequence of scene operations. For example:

- "show the protein as cartoon and the ligand as sticks" becomes `show` operations with structured selections.
- "hide solvent" becomes a `hide` or `remove` operation on `solvent`, depending on whether the user wants only the scene changed or the selected atoms removed from the exported session.
- "color chain A slate" becomes a `color` operation with a chain selection and a named or hex color.
- "label the copper atom" becomes a `label` operation with a metal selection and short text.

The agent should prefer structured selectors and avoid raw PyMOL command strings unless the user explicitly authorizes the advanced trusted-script mode.

## show, hide, remove

- `show` changes a representation into view, such as cartoon, sticks, spheres, lines or surface.
- `hide` removes a representation from view but keeps the atoms available.
- `remove` deletes atoms from the temporary job scene or exported session, not from the original file on disk.

That distinction matters because `remove` is an editing action for the scene, not a mutation of the source molecular file.

## Examples

### Protein figure

```json
{
  "pdb_id": "1GYC",
  "output_name": "protein_figure",
  "operations": [
    {"action": "show", "representation": "cartoon", "selection": "polymer.protein"},
    {"action": "color", "selection": "polymer.protein", "color": "slate"},
    {"action": "zoom", "selection": "polymer.protein", "buffer": 4}
  ],
  "export_session": true,
  "export_script": true
}
```

### Ligand pocket

```json
{
  "pdb_id": "1KYA",
  "output_name": "ligand_pocket",
  "operations": [
    {"action": "remove", "selection": "solvent"},
    {"action": "show", "representation": "cartoon", "selection": "polymer.protein"},
    {"action": "show", "representation": "sticks", "selection": "organic"},
    {"action": "zoom", "selection": "organic", "buffer": 6}
  ],
  "export_session": true,
  "export_script": true
}
```

### Chain coloring

```json
{
  "pdb_id": "6VMB",
  "output_name": "chain_coloring",
  "operations": [
    {"action": "show", "representation": "cartoon", "selection": "polymer.protein"},
    {"action": "color", "selection": "chain A", "color": "slate"},
    {"action": "color", "selection": "chain B", "color": "marine"}
  ]
}
```

### Metal highlighting

```json
{
  "pdb_id": "1GYC",
  "output_name": "metal_highlight",
  "operations": [
    {"action": "show", "representation": "spheres", "selection": "elem Cu"},
    {"action": "color", "selection": "elem Cu", "color": "#f28c28"},
    {"action": "label", "selection": "elem Cu", "text": "Cu"},
    {"action": "zoom", "selection": "elem Cu", "buffer": 6}
  ]
}
```

### Distance measurement

```json
{
  "source": {"pdb_id": "1GYC"},
  "selector_a": {"element": "Cu"},
  "selector_b": {"organic": true}
}
```

### Alignment

```json
{
  "reference_pdb_id": "1GYC",
  "mobile_pdb_id": "1KYA",
  "method": "align",
  "render": true
}
```

### Future MD frame comparison

Future versions may accept frame or snapshot inputs and then compare, align, or render selected time points from a trajectory-compatible workflow. That capability is planned for future molecular dynamics support and is not yet part of the current API.


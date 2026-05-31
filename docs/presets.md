# Presets

Current presets:

## publication_cartoon

Default publication-style protein cartoon. Ligands are shown as sticks and metals as spheres when present.

## copper_sites

Designed for laccases and other copper-containing proteins. Copper atoms are shown as orange spheres.

Example:

```json
{
  "pdb_id": "1GYC",
  "output_name": "1gyc_copper_sites",
  "preset": "copper_sites",
  "color": "chainbow",
  "ray": true
}
```

## surface

Shows a molecular surface with configurable transparency.

## active_site

Combines cartoon and surface rendering for active-site views.

## ligand_focus

Highlights organic ligands as sticks with a softer protein context.

## minimal

Clean cartoon representation.

## Naming notes

Older design notes may mention `basic_cartoon`, `chainbow`, or `publication_white`. In v0.1.0-alpha, those are represented by the current `publication_cartoon` preset plus `color="chainbow"` and `background="white"`.

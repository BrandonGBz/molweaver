# AI agent prompt recipes

This document shows how users can ask an AI agent to use the local PyMOL Figure Agent API
to build, modify, analyze, align, render, and export molecular scenes.
Each recipe includes a goal, a natural-language user prompt, expected API behavior,
suggested endpoints, and relevant notes.

## Recipe 1: General protein figure

**Goal:** Render a clean protein figure with ligands and export editable artifacts.

**User prompt:**
> Use the local PyMOL Figure Agent API. Load PDB 6LU7, show the protein as a clean cartoon,
> color chains distinctly, show organic ligands as sticks, remove solvent, render a PNG,
> and export a .pse session and .pml script.

**Endpoint(s):** `POST /render`

**Expected API behavior:**
- Remove solvent.
- Show protein as cartoon, organic ligands as sticks.
- Apply chainbow coloring.
- Render PNG with ray tracing.
- Export `.pse` session and `.pml` script.

**Notes:** Use `preset: "publication_cartoon"` with `color: "chainbow"`.

---

## Recipe 2: Ligand pocket figure

**Goal:** Inspect a ligand-binding pocket and generate a focused figure.

**User prompt:**
> Load PDB 6LU7, focus on the inhibitor pocket, show nearby residues within 5 A as sticks,
> label the ligand, render a close-up image, and export editable artifacts.

**Endpoint(s):** `POST /analyze/site`, `POST /render`

**Expected API behavior:**
- Analyze the site around the organic ligand.
- Use structured scene operations to set up a pocket-focused view.
- Render a publication-style close-up image.
- Export `.pse` and `.pml` artifacts.

**Notes:** Use `operations` to set up the close-up scene after the site analysis.

---

## Recipe 3: Metal-site visualization

**Goal:** Highlight metal centers and analyze their environment.

**User prompt:**
> Load PDB 1GYC, detect metal atoms, show the protein as cartoon, highlight metal atoms as spheres,
> label them, analyze nearby residues within 6 A, and render a publication-style image.

**Endpoint(s):** `POST /inspect`, `POST /analyze/site`, `POST /render`

**Expected API behavior:**
- Inspect the structure to identify metal atoms.
- Analyze the site around each metal center.
- Show protein as cartoon, metals as spheres with labels.
- Render a publication-style image.

**Notes:** `preset: "copper_sites"` is a convenient starting point for copper-containing structures.
Use structured `operations` for other metals.

---

## Recipe 4: Structural alignment

**Goal:** Align two structures and compare them visually.

**User prompt:**
> Align PDB 1GYC against 1KYA, report RMSD and aligned atoms, render the aligned structures
> with different colors, and export a PyMOL session for manual inspection.

**Endpoint(s):** `POST /align`

**Expected API behavior:**
- Download both PDB structures.
- Run the selected alignment method (`align`, `super`, or `cealign`).
- Return RMSD and aligned atom count.
- Optionally render the superposition image.
- Export session file.

**Notes:** Use `method: "super"` for structure-based alignment or `method: "cealign"` for CE-based alignment.

---

## Recipe 5: Distance measurement

**Goal:** Measure geometry between selected atoms or groups.

**User prompt:**
> Load PDB 1GYC, measure the minimum distance between a selected metal atom and nearby
> coordinating residues, return structured JSON, and generate a visual distance callout.

**Endpoint(s):** `POST /measure/distance`, `POST /render`

**Expected API behavior:**
- Measure the distance between two structured selectors.
- Return distance in angstroms with atom-level detail.
- Optionally render a scene showing the measured distance.

**Notes:** Use `StructuredSelector` with `chain`, `resi`, `resn`, and `element` fields.
Avoid free-form PyMOL selection strings.

---

## Recipe 6: Docking pose visualization

**Goal:** Visualize a docking result with receptor pocket and ligand pose.

**User prompt:**
> Load a local receptor structure and a local docking pose file, show the receptor pocket
> as translucent surface, show the ligand as sticks, label key residues, measure selected
> distances, render the figure, and export .pse and .pml artifacts.

**Endpoint(s):** `POST /analyze/site`, `POST /measure/distance`, `POST /render`

**Expected API behavior:**
- Load the receptor and ligand from local files.
- Analyze the pocket around the ligand.
- Measure relevant distances.
- Build a scene with translucent surface and ligand sticks.
- Export all artifacts.

**Notes:** Use local user-provided files at runtime. Do not commit generated outputs.
Use `structure_path` with local file paths.

---

## Recipe 7: Molecular dynamics snapshot rendering

**Goal:** Render a selected frame from an MD trajectory.

**User prompt:**
> Load a selected PDB snapshot exported from a molecular dynamics trajectory, align it to
> a reference structure, highlight conformationally relevant residues, render the snapshot,
> and export the scene for manual inspection.

**Endpoint(s):** `POST /align`, `POST /render`

**Expected API behavior:**
- Load the exported snapshot PDB.
- Align to the reference structure.
- Highlight specified residues.
- Render and export.

**Notes:** Trajectory-native workflows are planned for future versions. Current workflows
operate on exported frames/snapshots saved as PDB files.

---

## Recipe 8: Comparative MD poses across time

**Goal:** Compare multiple MD snapshots from different time points.

**User prompt:**
> Compare three exported MD snapshots from different time points, align all snapshots to
> the same reference, color each time point differently, measure a selected distance in
> each snapshot, and generate a figure panel.

**Endpoint(s):** `POST /align`, `POST /measure/distance`, `POST /render`

**Expected API behavior:**
- Align each snapshot to the reference structure.
- Apply distinct coloring per snapshot.
- Measure distances for each snapshot.
- Combine into a multi-panel figure.

**Notes:** Full batch and trajectory workflows are planned for future versions. The agent
should orchestrate multiple API calls to handle each snapshot individually.

---

## Recipe 9: Virtual screening figure preparation

**Goal:** Generate a figure for a docking hit from a virtual screening campaign.

**User prompt:**
> For a selected docking hit from a virtual screening campaign, load the receptor and ligand
> pose, focus on the binding pocket, identify nearby residues, measure relevant distances,
> render a figure, and export metadata for a report.

**Endpoint(s):** `POST /analyze/site`, `POST /measure/distance`, `POST /render`

**Expected API behavior:**
- Load receptor and docked ligand from local files.
- Analyze the binding site.
- Measure key distances.
- Render a publication-ready figure.
- Export JSON metadata alongside the image.

**Notes:** This workflow is suitable for preparing figures for screening reports, publications,
or presentations. Export metadata JSON for integration with automated reporting pipelines.

---

## Recipe 10: Reproducible figure regeneration

**Goal:** Regenerate a figure from a previous job's artifacts.

**User prompt:**
> Use the saved .pml script and metadata from a previous PyMOL Figure Agent job to regenerate
> the same figure and verify that the exported PNG matches the expected scene settings.

**Endpoint(s):** `POST /render` or local `.pml` execution.

**Expected API behavior:**
- Read the `.pml` script from the previous job's artifacts.
- Execute the same render pipeline.
- Verify the output matches expected parameters.

**Notes:** The `.pml` script is a fully reproducible PyMOL script that can be loaded directly
in PyMOL. The API can also re-execute the same render job if the original spec JSON is preserved.

---

## General guidance for agents

- Always translate user intent into structured API operations whenever possible.
- Prefer `pdb_id` for public examples; use `structure_path` only when the user provides a local file.
- Use the `/inspect` endpoint first when the structure content is unknown.
- Combine `/analyze/site`, `/measure/distance`, and `/render` for multi-step analysis-and-figure workflows.
- Presets are starting points, not limits. Use `operations` for detailed scene control.
- Export `.pse` and `.pml` artifacts when the user wants editable or reproducible outputs.
- Never include private paths or unpublished data in public outputs.
- Treat geometry metrics and alignments as descriptive, not as biochemical validation.

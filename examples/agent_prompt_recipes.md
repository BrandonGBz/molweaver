# Agent prompt recipes

Quick-start prompt recipes for AI agents using the PyMOL Figure Agent API.
For detailed recipes with expected API behavior, endpoint guidance, and notes,
see [docs/agent-prompt-recipes.md](../docs/agent-prompt-recipes.md).

## Quick prompts

1. **General protein figure:** Load PDB 6LU7, cartoon, chain coloring, ligands as sticks, remove solvent, render PNG, export .pse and .pml.
2. **Ligand pocket:** Load PDB 6LU7, focus inhibitor pocket, nearby residues within 5 A as sticks, label ligand, render close-up.
3. **Metal site:** Load PDB 1GYC, detect metals, cartoon + sphere highlights, label, analyze neighborhood, render.
4. **Alignment:** Align 1GYC vs 1KYA, report RMSD and aligned atoms, render colored superposition, export session.
5. **Distance measurement:** Load 1GYC, measure metal-to-residue distances, return JSON, render distance callout.
6. **Docking pose:** Load local receptor + docking pose, translucent pocket surface, ligand sticks, measure distances, export artifacts.
7. **MD snapshot:** Load exported MD snapshot PDB, align to reference, highlight conformational residues, render.
8. **Comparative MD poses:** Compare 3 MD snapshots across time points, align to reference, color each differently, measure distances.
9. **Virtual screening hit:** Load receptor + docking hit, focus binding pocket, identify nearby residues, measure distances, render figure for report.
10. **Reproducible regeneration:** Use saved .pml script and metadata from a previous job to regenerate the same figure.

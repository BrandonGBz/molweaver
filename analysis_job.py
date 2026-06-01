from __future__ import annotations

import json
import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any


METAL_SELECTION = "elem Cu+Zn+Fe+Mg+Mn+Ca+Na+K+Co+Ni"
SCIENTIFIC_WARNING = (
    "Geometric structural analysis is descriptive only and does not replace experimental validation, "
    "docking validation, molecular dynamics, thermodynamic analysis, or biochemical assays."
)


def main() -> None:
    spec_path, result_path = _parse_args()
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))

    try:
        if os.getenv("PYMOL_USE_PYMOL2") == "1":
            import pymol2

            with pymol2.PyMOL() as pymol_instance:
                payload = _run_analysis(pymol_instance.cmd, spec)
        else:
            from pymol import cmd

            payload = _run_analysis(cmd, spec)
            cmd.quit()
        _write_result(result_path, {"ok": True, **payload})
    except Exception as exc:
        _write_result(
            result_path,
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        raise


def _run_analysis(cmd: Any, spec: dict[str, Any]) -> dict[str, Any]:
    cmd.reinitialize()
    obj = spec.get("object_name") or "structure"
    cmd.load(spec["input_path"], obj)
    if not spec.get("include_solvent", False):
        cmd.remove(f"({obj}) and solvent")

    operation = spec["operation"]
    if operation == "inspect":
        result = _inspect(cmd, obj)
    elif operation == "distance":
        result = _distance(cmd, spec)
    elif operation == "site":
        result = _site(cmd, spec)
    else:
        raise ValueError(f"Unsupported analysis operation: {operation}")

    artifacts: dict[str, str] = {}
    pml_path = spec.get("pml_script_path")
    if pml_path:
        _write_pml(Path(pml_path), spec)
        artifacts["pml_script_path"] = str(pml_path)

    return {
        "result": result,
        "metadata": {
            "operation": operation,
            "source": spec.get("source_summary"),
            "object_name": obj,
            "analysis_version": "0.1.0-alpha",
        },
        "warnings": [SCIENTIFIC_WARNING],
        "artifacts": artifacts,
    }


def _inspect(cmd: Any, obj: str) -> dict[str, Any]:
    chains = sorted(chain for chain in cmd.get_chains(obj) if chain)
    polymer_atoms = cmd.count_atoms(f"({obj}) and polymer")
    protein_atoms = cmd.count_atoms(f"({obj}) and polymer.protein")
    nucleic_atoms = cmd.count_atoms(f"({obj}) and polymer.nucleic")
    solvent_atoms = cmd.count_atoms(f"({obj}) and solvent")
    organic_atoms = cmd.count_atoms(f"({obj}) and organic")
    metal_atoms = cmd.count_atoms(f"({obj}) and ({METAL_SELECTION})")

    return {
        "atom_count": cmd.count_atoms(obj),
        "polymer_atom_count": polymer_atoms,
        "protein_atom_count": protein_atoms,
        "nucleic_atom_count": nucleic_atoms,
        "solvent_atom_count": solvent_atoms,
        "organic_ligand_atom_count": organic_atoms,
        "metal_atom_count": metal_atoms,
        "chains": chains,
        "residue_count": len(_unique_residues(cmd, f"({obj}) and polymer")),
        "organic_ligands": _unique_residues(cmd, f"({obj}) and organic"),
        "metals": _atom_descriptors(cmd, f"({obj}) and ({METAL_SELECTION})"),
    }


def _distance(cmd: Any, spec: dict[str, Any]) -> dict[str, Any]:
    selection_a = spec["selector_a"]
    selection_b = spec["selector_b"]
    atoms_a = _atoms(cmd, selection_a)
    atoms_b = _atoms(cmd, selection_b)
    if not atoms_a:
        raise ValueError("selector_a did not match any atoms.")
    if not atoms_b:
        raise ValueError("selector_b did not match any atoms.")

    centroid_a = _centroid(atoms_a)
    centroid_b = _centroid(atoms_b)
    distance = _distance_between(centroid_a, centroid_b)
    warnings: list[str] = []
    if len(atoms_a) > 1:
        warnings.append(f"selector_a matched {len(atoms_a)} atoms; centroid distance was used.")
    if len(atoms_b) > 1:
        warnings.append(f"selector_b matched {len(atoms_b)} atoms; centroid distance was used.")

    return {
        "distance_angstrom": round(distance, 3),
        "selector_a_atom_count": len(atoms_a),
        "selector_b_atom_count": len(atoms_b),
        "selector_a_centroid": _round_coord(centroid_a),
        "selector_b_centroid": _round_coord(centroid_b),
        "selector_a_atoms": [_atom_descriptor(atom) for atom in atoms_a[:20]],
        "selector_b_atoms": [_atom_descriptor(atom) for atom in atoms_b[:20]],
        "selection_warnings": warnings,
    }


def _site(cmd: Any, spec: dict[str, Any]) -> dict[str, Any]:
    center_selection = spec["center_selector"]
    radius = float(spec["radius_angstrom"])
    include_solvent = bool(spec.get("include_solvent", False))
    center_atoms = _atoms(cmd, center_selection)
    if not center_atoms:
        raise ValueError("center selector did not match any atoms.")

    center = _centroid(center_atoms)
    site_selection = f"byres (({spec['object_name']}) within {radius:.3f} of ({center_selection}))"
    if not include_solvent:
        site_selection = f"({site_selection}) and not solvent"

    residues = _nearby_residues(cmd, site_selection, center)
    return {
        "center_atom_count": len(center_atoms),
        "center_centroid": _round_coord(center),
        "radius_angstrom": radius,
        "site_selection": site_selection,
        "nearby_residue_count": len(residues),
        "nearby_residues": residues[:80],
        "nearby_metals": _atom_descriptors(cmd, f"({site_selection}) and ({METAL_SELECTION})"),
        "nearby_organic_ligands": _unique_residues(cmd, f"({site_selection}) and organic"),
    }


def _nearby_residues(cmd: Any, selection: str, center: tuple[float, float, float]) -> list[dict[str, Any]]:
    by_residue: dict[tuple[str, str, str], float] = {}
    for atom in _atoms(cmd, selection):
        key = (str(atom.chain), str(atom.resi), str(atom.resn))
        distance = _distance_between(center, tuple(atom.coord))
        by_residue[key] = min(distance, by_residue.get(key, distance))
    residues = [
        {
            "chain": chain,
            "resi": resi,
            "resn": resn,
            "min_distance_angstrom": round(distance, 3),
        }
        for (chain, resi, resn), distance in by_residue.items()
    ]
    return sorted(residues, key=lambda item: item["min_distance_angstrom"])


def _unique_residues(cmd: Any, selection: str) -> list[dict[str, str]]:
    residues = {
        (str(atom.chain), str(atom.resi), str(atom.resn))
        for atom in _atoms(cmd, selection)
    }
    return [
        {"chain": chain, "resi": resi, "resn": resn}
        for chain, resi, resn in sorted(residues)
    ]


def _atom_descriptors(cmd: Any, selection: str) -> list[dict[str, Any]]:
    return [_atom_descriptor(atom) for atom in _atoms(cmd, selection)]


def _atom_descriptor(atom: Any) -> dict[str, Any]:
    return {
        "chain": str(atom.chain),
        "resi": str(atom.resi),
        "resn": str(atom.resn),
        "atom_name": str(atom.name),
        "element": str(getattr(atom, "symbol", "") or getattr(atom, "elem", "")),
        "coord": _round_coord(tuple(atom.coord)),
    }


def _atoms(cmd: Any, selection: str) -> list[Any]:
    return list(cmd.get_model(selection).atom)


def _centroid(atoms: list[Any]) -> tuple[float, float, float]:
    count = len(atoms)
    return (
        sum(float(atom.coord[0]) for atom in atoms) / count,
        sum(float(atom.coord[1]) for atom in atoms) / count,
        sum(float(atom.coord[2]) for atom in atoms) / count,
    )


def _distance_between(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def _round_coord(coord: tuple[float, float, float]) -> list[float]:
    return [round(float(value), 3) for value in coord]


def _write_pml(path: Path, spec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Reproducible PyMOL analysis script generated by PyMOL Figure Agent.",
        "# Descriptive geometry only; not experimental validation.",
        f"load {Path(spec['input_path']).as_posix()}, {spec.get('object_name', 'structure')}",
    ]
    if spec["operation"] == "distance":
        lines.extend(
            [
                f"select selector_a, {spec['selector_a']}",
                f"select selector_b, {spec['selector_b']}",
                "distance measured_distance, selector_a, selector_b",
            ]
        )
    elif spec["operation"] == "site":
        lines.extend(
            [
                f"select center_selector, {spec['center_selector']}",
                f"select site_shell, {spec.get('site_selector_preview', 'center_selector')}",
                "show sticks, site_shell",
                "show spheres, center_selector",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> tuple[str, str]:
    args = [arg for arg in sys.argv[1:] if arg != "--"]
    if len(args) < 2:
        raise SystemExit("Usage: analysis_job.py SPEC_JSON RESULT_JSON")
    return args[0], args[1]


def _write_result(result_path: str, result: dict[str, Any]) -> None:
    Path(result_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

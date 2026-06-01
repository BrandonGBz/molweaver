from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from scene_operations import apply_scene_operations


METAL_SELECTION = "elem Cu+Zn+Fe+Mg+Mn+Ca+Na+K+Co+Ni"


def main() -> None:
    spec_path, result_path = _parse_args()
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))

    try:
        if os.getenv("PYMOL_USE_PYMOL2") == "1":
            import pymol2

            with pymol2.PyMOL() as pymol_instance:
                warnings = _render_scene(pymol_instance.cmd, spec)
        else:
            from pymol import cmd

            warnings = _render_scene(cmd, spec)
            cmd.quit()
        _write_result(
            result_path,
            {"ok": True, "output_path": spec["output_path"], "warnings": warnings},
        )
    except Exception as exc:  # PyMOL errors should be returned to the API, not swallowed.
        _write_result(
            result_path,
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        raise


def _render_scene(cmd: Any, spec: dict[str, Any]) -> list[str]:
    cmd.reinitialize()
    cmd.load(spec["input_path"], spec["object_name"])
    obj = spec["object_name"]
    quality = str(spec.get("render_quality") or "high").lower()

    if spec.get("trusted_script"):
        for command in spec.get("trusted_commands", []):
            cmd.do(command)
        _export_session(cmd, spec)
        _finalize_image(cmd, spec)
        return []

    cmd.viewport(int(spec["width"]), int(spec["height"]))
    cmd.bg_color(_color(cmd, spec.get("background", "white")))
    cmd.set("ray_opaque_background", 0 if spec.get("transparent") else 1)
    cmd.set("antialias", 2)
    cmd.set("orthoscopic", 1)
    cmd.set("depth_cue", 0)
    cmd.set("cartoon_fancy_helices", 1)
    cmd.set("cartoon_smooth_loops", 1)
    cmd.set("sphere_scale", 0.55)
    cmd.set("stick_radius", 0.18)

    if quality in {"high", "publication", "ultra"}:
        # Publication-style defaults: smoother surface, smoother cartoon and ray-traced outlines.
        cmd.set("surface_quality", 2)
        cmd.set("cartoon_sampling", 14)
        cmd.set("mesh_quality", 2)
        cmd.set("ray_trace_mode", 1)
        cmd.set("ray_trace_color", "black")
        cmd.set("ray_trace_gain", 0.16)
        cmd.set("ray_trace_fog", 0)
        cmd.set("ray_trace_fog_start", 0)
        cmd.set("ray_shadow", 1)
    else:
        cmd.set("surface_quality", 1)
        cmd.set("cartoon_sampling", 10)
        cmd.set("mesh_quality", 2)
        cmd.set("ray_trace_mode", 0)

    if not spec.get("show_solvent", False):
        cmd.remove(f"({obj}) and solvent")

    cmd.hide("everything", obj)
    _apply_preset(cmd, spec, obj)
    _apply_representations(cmd, spec, obj)
    _apply_color(cmd, spec, obj)
    _apply_highlights(cmd, spec, obj)
    _apply_labels(cmd, spec, obj)
    operation_warnings = apply_scene_operations(cmd, spec.get("operations"), object_name=obj)

    orient_selection = spec.get("orient_selection") or "all"
    zoom_selection = spec.get("zoom_selection") or orient_selection
    cmd.orient(orient_selection)
    cmd.zoom(zoom_selection, buffer=4)
    _export_session(cmd, spec)
    _finalize_image(cmd, spec)
    return operation_warnings


def _apply_preset(cmd: Any, spec: dict[str, Any], obj: str) -> None:
    preset = spec.get("preset") or "publication_cartoon"

    if preset == "minimal":
        cmd.show("cartoon", obj)
        return

    if preset in {"publication_cartoon", "ligand_focus", "active_site", "copper_sites"}:
        cmd.show("cartoon", f"({obj}) and polymer.protein")
        cmd.show("cartoon", f"({obj}) and polymer.nucleic")

    if preset in {"surface", "active_site"}:
        cmd.show("surface", obj)
        cmd.set("transparency", float(spec.get("surface_transparency", 0.35)), obj)

    if preset == "ligand_focus":
        spec["show_ligands"] = True
        cmd.set("cartoon_transparency", 0.25, obj)

    if preset == "copper_sites":
        spec["show_metals"] = True
        spec.setdefault("highlights", [])
        spec["highlights"].append(
            {
                "selection": f"({obj}) and elem Cu",
                "color": "#f28c28",
                "representation": "spheres",
                "label": "Cu",
            }
        )

    if spec.get("show_ligands", True):
        cmd.show("sticks", f"({obj}) and organic")
    if spec.get("show_metals", True):
        cmd.show("spheres", f"({obj}) and ({METAL_SELECTION})")


def _apply_representations(cmd: Any, spec: dict[str, Any], obj: str) -> None:
    for representation in spec.get("representations") or []:
        cmd.show(representation, obj)


def _apply_color(cmd: Any, spec: dict[str, Any], obj: str) -> None:
    color = spec.get("color") or "chainbow"
    if color == "chainbow":
        try:
            cmd.util.chainbow(obj)
        except Exception:
            cmd.spectrum("count", "rainbow", obj)
    elif color == "spectrum":
        cmd.spectrum("count", "rainbow", obj)
    elif color == "element":
        cmd.color("gray80", obj)
        try:
            cmd.util.cnc(obj)
        except Exception:
            pass
    else:
        cmd.color(_color(cmd, color), obj)

    cmd.color("orange", f"({obj}) and elem Cu")
    cmd.color("marine", f"({obj}) and ({METAL_SELECTION}) and not elem Cu")
    cmd.color("atomic", f"({obj}) and organic")


def _apply_highlights(cmd: Any, spec: dict[str, Any], obj: str) -> None:
    for index, item in enumerate(spec.get("highlights") or []):
        selection = item.get("selection") or "all"
        color = _color(cmd, item.get("color") or "yellow", suffix=str(index))
        representation = item.get("representation") or "sticks"
        cmd.show(representation, selection)
        cmd.color(color, selection)
        if representation == "spheres":
            cmd.set("sphere_scale", 0.75, selection)
        if item.get("label"):
            cmd.label(selection, repr(str(item["label"])))


def _apply_labels(cmd: Any, spec: dict[str, Any], obj: str) -> None:
    for item in spec.get("labels") or []:
        selection = item.get("selection") or obj
        text = item.get("text") or "resn + resi"
        if not _looks_like_pymol_label_expression(text):
            text = repr(text)
        cmd.label(selection, text)
    cmd.set("label_size", 22)
    cmd.set("label_color", "black")


def _finalize_image(cmd: Any, spec: dict[str, Any]) -> None:
    output_path = Path(spec["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd.png(
        str(output_path),
        width=int(spec["width"]),
        height=int(spec["height"]),
        dpi=int(spec["dpi"]),
        ray=1 if spec.get("ray", True) else 0,
        quiet=1,
    )


def _export_session(cmd: Any, spec: dict[str, Any]) -> None:
    session_path = spec.get("session_path")
    if not session_path:
        return

    path = Path(session_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd.save(str(path))
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"PyMOL did not create a valid session file at {path}.")


def _color(cmd: Any, value: str, *, suffix: str = "") -> str:
    text = str(value).strip()
    if text.startswith("#") and len(text) == 7:
        red = int(text[1:3], 16) / 255
        green = int(text[3:5], 16) / 255
        blue = int(text[5:7], 16) / 255
        name = f"api_color_{text[1:].lower()}{suffix}"
        cmd.set_color(name, [red, green, blue])
        return name
    return text or "white"


def _looks_like_pymol_label_expression(value: str) -> bool:
    allowed = {"name", "resn", "resi", "chain", "segi", "elem", "oneletter"}
    tokens = {
        token.strip()
        for token in value.replace("+", " ").replace("'", " ").replace('"', " ").split()
        if token.strip()
    }
    return bool(tokens) and tokens.issubset(allowed)


def _parse_args() -> tuple[str, str]:
    args = [arg for arg in sys.argv[1:] if arg != "--"]
    if len(args) < 2:
        raise SystemExit("Uso: render_job.py SPEC_JSON RESULT_JSON")
    return args[0], args[1]


def _write_result(result_path: str, result: dict[str, Any]) -> None:
    Path(result_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

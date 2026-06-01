from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from pymol_renderer import BASE_DIR, OUTPUT_DIR, Backend, RenderError, _safe_output_name, discover_backend
from schemas import DistanceRequest, InspectRequest, SiteAnalysisRequest, StructureSource, StructuredSelector
from source_resolver import resolve_source


RUNNER = BASE_DIR / "analysis_job.py"
METAL_SELECTION = "elem Cu+Zn+Fe+Mg+Mn+Ca+Na+K+Co+Ni"
SCIENTIFIC_WARNING = (
    "Geometric structural analysis is descriptive only and does not replace experimental validation, "
    "docking validation, molecular dynamics, thermodynamic analysis, or biochemical assays."
)


def inspect_structure(request: InspectRequest) -> dict[str, object]:
    return _run_analysis(
        operation="inspect",
        source=request.source,
        request_payload=request.model_dump(mode="json"),
        timeout_seconds=request.timeout_seconds,
        output_name=request.output_name,
        export_pml=request.export_pml,
        spec_extra={"include_solvent": request.include_solvent},
    )


def measure_distance(request: DistanceRequest) -> dict[str, object]:
    selector_a = selector_to_pymol(request.selector_a)
    selector_b = selector_to_pymol(request.selector_b)
    return _run_analysis(
        operation="distance",
        source=request.source,
        request_payload=request.model_dump(mode="json"),
        timeout_seconds=request.timeout_seconds,
        output_name=request.output_name,
        export_pml=request.export_pml,
        spec_extra={
            "selector_a": selector_a,
            "selector_b": selector_b,
        },
    )


def analyze_site(request: SiteAnalysisRequest) -> dict[str, object]:
    center_selector = selector_to_pymol(request.center)
    site_preview = (
        f"byres ((structure) within {float(request.radius_angstrom):.3f} of ({center_selector}))"
    )
    if not request.include_solvent:
        site_preview = f"({site_preview}) and not solvent"
    return _run_analysis(
        operation="site",
        source=request.source,
        request_payload=request.model_dump(mode="json"),
        timeout_seconds=request.timeout_seconds,
        output_name=request.output_name,
        export_pml=request.export_pml,
        spec_extra={
            "center_selector": center_selector,
            "site_selector_preview": site_preview,
            "radius_angstrom": request.radius_angstrom,
            "include_solvent": request.include_solvent,
        },
    )


def selector_to_pymol(selector: StructuredSelector, *, object_name: str = "structure") -> str:
    clauses = [f"({object_name})"]
    if selector.chain:
        clauses.append(f"chain {selector.chain}")
    if selector.resi:
        clauses.append(f"resi {selector.resi}")
    if selector.resn:
        clauses.append(f"resn {selector.resn}")
    if selector.atom_name:
        clauses.append(f"name {selector.atom_name}")
    if selector.element:
        clauses.append(f"elem {selector.element}")
    if selector.ligand:
        clauses.append(f"(organic and resn {selector.ligand})")
    if selector.metal:
        clauses.append(f"({METAL_SELECTION})")
    if selector.organic:
        clauses.append("organic")
    return " and ".join(clauses)


def _run_analysis(
    *,
    operation: str,
    source: StructureSource,
    request_payload: dict[str, Any],
    timeout_seconds: int,
    output_name: str | None,
    export_pml: bool,
    spec_extra: dict[str, Any],
) -> dict[str, object]:
    backend = discover_backend()
    if not backend.available:
        raise RenderError(backend.message, status_code=503)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "jobs").mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    job_dir = OUTPUT_DIR / "jobs" / job_id
    input_dir = job_dir / "inputs"
    job_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    try:
        resolved = resolve_source(source, input_dir)
    except ValueError as exc:
        message = str(exc)
        if "exceeds PYMOL_MAX_FILE_SIZE_MB" in message:
            raise RenderError(message, status_code=413) from exc
        if any(
            token in message
            for token in (
                "does not exist",
                "outside PYMOL_ALLOWED_INPUT_DIR",
                "Unsupported extension",
                "Missing structure source.",
            )
        ):
            raise RenderError(message, status_code=400) from exc
        if any(
            token in message
            for token in ("Could not download", "Could not connect", "RCSB returned no data")
        ):
            raise RenderError(message, status_code=502) from exc
        raise RenderError(message, status_code=400) from exc
    source_path = resolved.path
    source_summary = resolved.summary
    source_warnings = resolved.warnings
    safe_name = _safe_output_name(output_name or f"{operation}_{job_id}")
    spec_path = job_dir / "analysis_spec.json"
    result_path = job_dir / "result.json"
    pml_path = job_dir / f"{safe_name}.pml" if export_pml else None

    spec = {
        "operation": operation,
        "input_path": str(source_path),
        "object_name": "structure",
        "source_summary": source_summary,
        "request": request_payload,
        "pml_script_path": str(pml_path) if pml_path else None,
        **spec_extra,
    }
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    command, env = _build_command(backend, spec_path, result_path)
    completed = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    stdout_path = job_dir / "stdout.log"
    stderr_path = job_dir / "stderr.log"
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    (job_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "PyMOL analysis job failed.").strip()
        raise RenderError(f"PyMOL failed with code {completed.returncode}: {message}", status_code=502)
    if not result_path.exists():
        raise RenderError("PyMOL did not create an analysis result file.", status_code=502)

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if not payload.get("ok"):
        raise RenderError(payload.get("error", "PyMOL could not complete the analysis."), status_code=502)

    artifacts = {
        "analysis_spec_path": str(spec_path),
        "result_json_path": str(result_path),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        **payload.get("artifacts", {}),
    }
    warnings = _dedupe_warnings(source_warnings + payload.get("warnings", []) + [SCIENTIFIC_WARNING])
    metadata = {
        **payload.get("metadata", {}),
        "backend": backend.kind,
        "job_dir": str(job_dir),
    }
    return {
        "job_id": job_id,
        "result": payload.get("result", {}),
        "metadata": metadata,
        "warnings": warnings,
        "artifacts": artifacts,
    }
def _build_command(backend: Backend, spec_path: Path, result_path: Path) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    if backend.kind in {"python_pymol2", "bundled_conda_pymol2"}:
        env["PYMOL_USE_PYMOL2"] = "1"
        return [backend.command[0], str(RUNNER), str(spec_path), str(result_path)], env
    return [
        backend.command[0],
        "-cq",
        str(RUNNER),
        "--",
        str(spec_path),
        str(result_path),
    ], env


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for warning in warnings:
        if warning and warning not in seen:
            seen.add(warning)
            result.append(warning)
    return result

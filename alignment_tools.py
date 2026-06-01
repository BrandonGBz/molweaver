from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

from pymol_renderer import BASE_DIR, OUTPUT_DIR, Backend, RenderError, _safe_output_name, discover_backend
from schemas import AlignmentRequest
from source_resolver import resolve_source
from structure_analyzer import SCIENTIFIC_WARNING, _dedupe_warnings


RUNNER = BASE_DIR / "alignment_job.py"


def align_structures(request: AlignmentRequest) -> dict[str, object]:
    backend = discover_backend()
    if not backend.available:
        raise RenderError(backend.message, status_code=503)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "jobs").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex[:12]
    job_dir = OUTPUT_DIR / "jobs" / job_id
    reference_dir = job_dir / "inputs" / "reference"
    mobile_dir = job_dir / "inputs" / "mobile"
    job_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    mobile_dir.mkdir(parents=True, exist_ok=True)

    try:
        reference_resolved = resolve_source(request.reference, reference_dir)
        mobile_resolved = resolve_source(request.mobile, mobile_dir)
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
    reference_path = reference_resolved.path
    mobile_path = mobile_resolved.path
    reference_summary = reference_resolved.summary
    mobile_summary = mobile_resolved.summary
    reference_warnings = reference_resolved.warnings
    mobile_warnings = mobile_resolved.warnings
    safe_name = _safe_output_name(request.output_name or f"alignment_{job_id}")
    spec_path = job_dir / "analysis_spec.json"
    result_path = job_dir / "result.json"
    image_path = OUTPUT_DIR / "images" / f"{safe_name}.png" if request.render else None
    pml_path = job_dir / f"{safe_name}.pml" if request.export_pml else None

    if image_path and image_path.exists():
        image_path = OUTPUT_DIR / "images" / f"{safe_name}_{job_id}.png"

    spec = {
        "method": request.method,
        "reference_path": str(reference_path),
        "mobile_path": str(mobile_path),
        "reference_summary": reference_summary,
        "mobile_summary": mobile_summary,
        "request": request.model_dump(mode="json"),
        "render": request.render,
        "image_path": str(image_path) if image_path else None,
        "pml_script_path": str(pml_path) if pml_path else None,
        "width": request.width,
        "height": request.height,
        "dpi": request.dpi,
        "ray": request.ray,
    }
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    command, env = _build_command(backend, spec_path, result_path)
    completed = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=request.timeout_seconds,
        check=False,
    )

    stdout_path = job_dir / "stdout.log"
    stderr_path = job_dir / "stderr.log"
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    (job_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "PyMOL alignment job failed.").strip()
        raise RenderError(f"PyMOL failed with code {completed.returncode}: {message}", status_code=502)
    if not result_path.exists():
        raise RenderError("PyMOL did not create an alignment result file.", status_code=502)

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if not payload.get("ok"):
        raise RenderError(payload.get("error", "PyMOL could not complete the alignment."), status_code=502)

    artifacts = {
        "analysis_spec_path": str(spec_path),
        "result_json_path": str(result_path),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        **payload.get("artifacts", {}),
    }
    if image_path:
        artifacts["image_url"] = f"/images/{image_path.name}"

    warnings = _dedupe_warnings(
        reference_warnings + mobile_warnings + payload.get("warnings", []) + [SCIENTIFIC_WARNING]
    )
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

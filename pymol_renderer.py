from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_export import build_render_script_text
from source_resolver import resolve_source


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("PYMOL_OUTPUT_DIR") or os.getenv("PYMOL_API_OUTPUT_DIR") or BASE_DIR / "outputs")
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = BASE_DIR / OUTPUT_DIR
OUTPUT_DIR = OUTPUT_DIR.resolve()
RUNNER = BASE_DIR / "render_job.py"
MAX_FILE_SIZE_MB = int(os.getenv("PYMOL_MAX_FILE_SIZE_MB", "100"))


class RenderError(RuntimeError):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class Backend:
    available: bool
    kind: str
    command: list[str]
    message: str
    allow_unsafe_commands: bool = False


def discover_backend() -> Backend:
    allow_unsafe = os.getenv("PYMOL_ALLOW_UNSAFE_COMMANDS") == "1"
    configured = os.getenv("PYMOL_EXECUTABLE")
    if configured:
        executable = Path(configured).expanduser()
        if executable.exists():
            return Backend(
                True,
                "pymol_executable",
                [str(executable)],
                "PyMOL detected through PYMOL_EXECUTABLE.",
                allow_unsafe,
            )
        return Backend(
            False,
            "missing",
            [],
            f"PYMOL_EXECUTABLE points to a missing path: {configured}",
            allow_unsafe,
        )

    bundled_python = BASE_DIR / "tools" / "pymol_env" / "python.exe"
    if bundled_python.exists():
        return Backend(
            True,
            "bundled_conda_pymol2",
            [str(bundled_python)],
            "PyMOL/pymol2 detected in the local conda environment for this API.",
            allow_unsafe,
        )

    executable = shutil.which("pymol")
    if executable:
        return Backend(
            True,
            "pymol_executable",
            [executable],
            "PyMOL detected in PATH.",
            allow_unsafe,
        )

    from importlib.util import find_spec

    if find_spec("pymol2") and _can_import_pymol2():
        return Backend(
            True,
            "python_pymol2",
            [sys.executable],
            "pymol2 module available in the Python runtime that runs this API.",
            allow_unsafe,
        )

    return Backend(
        False,
        "missing",
        [],
        (
            "PyMOL was not found. Install PyMOL with conda-forge or set PYMOL_EXECUTABLE."
        ),
        allow_unsafe,
    )


def _can_import_pymol2() -> bool:
    try:
        import pymol2  # noqa: F401
    except Exception:
        return False
    return True


def render_structure(request: dict[str, Any], *, trusted_script: bool = False) -> dict[str, Any]:
    backend = discover_backend()
    if not backend.available:
        raise RenderError(backend.message, status_code=503)
    if trusted_script and not backend.allow_unsafe_commands:
        raise RenderError(
            "The trusted-script endpoint is disabled. Set PYMOL_ALLOW_UNSAFE_COMMANDS=1 "
            "only if you trust the client that will send PyMOL commands.",
            status_code=403,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "jobs").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "sessions").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "scripts").mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex[:12]
    job_dir = OUTPUT_DIR / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        source_resolution = resolve_source(request, job_dir)
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
    source_path = source_resolution.path
    output_name = _safe_output_name(request.get("output_name") or f"pymol_{job_id}")
    image_path = OUTPUT_DIR / "images" / f"{output_name}.png"
    if image_path.exists():
        image_path = OUTPUT_DIR / "images" / f"{output_name}_{job_id}.png"
    session_path = None
    if bool(request.get("export_session", False)):
        session_path = OUTPUT_DIR / "sessions" / f"{output_name}.pse"
        if session_path.exists():
            session_path = OUTPUT_DIR / "sessions" / f"{output_name}_{job_id}.pse"
    script_path = None
    if request.get("export_script", True):
        script_path = OUTPUT_DIR / "scripts" / f"{output_name}.pml"
        if script_path.exists():
            script_path = OUTPUT_DIR / "scripts" / f"{output_name}_{job_id}.pml"

    if script_path:
        script_path.write_text(
            build_render_script_text(
                request,
                source_type=source_resolution.source_type,
                source_summary=source_resolution.summary,
                source_path=source_path,
                image_path=image_path,
                session_path=session_path,
            ),
            encoding="utf-8",
        )

    spec = _build_job_spec(request, source_path, image_path, trusted_script=trusted_script)
    spec["session_path"] = str(session_path) if session_path else None
    spec["script_path"] = str(script_path) if script_path else None
    spec_path = job_dir / "render_spec.json"
    result_path = job_dir / "render_result.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    command, env = _build_command(backend, spec_path, result_path)
    timeout = int(request.get("timeout_seconds") or 180)
    completed = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    (job_dir / "stdout.log").write_text(completed.stdout or "", encoding="utf-8")
    (job_dir / "stderr.log").write_text(completed.stderr or "", encoding="utf-8")
    (job_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "PyMOL termino con error.").strip()
        raise RenderError(f"PyMOL failed with code {completed.returncode}: {message}", status_code=502)

    if not result_path.exists():
        raise RenderError("PyMOL did not create a result file.", status_code=502)

    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not result.get("ok"):
        raise RenderError(result.get("error", "PyMOL could not render the scene."), status_code=502)
    if not image_path.exists() or image_path.stat().st_size == 0:
        raise RenderError("PyMOL did not create a valid PNG image.", status_code=502)
    if session_path and (not session_path.exists() or session_path.stat().st_size == 0):
        raise RenderError("PyMOL did not create a valid session file.", status_code=502)
    result_warnings = result.get("warnings", [])
    if not isinstance(result_warnings, list):
        result_warnings = []

    artifacts = {
        "image_path": str(image_path),
        "image_url": f"/images/{image_path.name}",
        "session_path": str(session_path) if session_path else None,
        "session_url": f"/sessions/{session_path.name}" if session_path else None,
        "script_path": str(script_path) if script_path else None,
        "script_url": f"/scripts/{script_path.name}" if script_path else None,
    }
    return {
        "job_id": job_id,
        "image_path": str(image_path),
        "image_url": f"/images/{image_path.name}",
        "source_path": str(source_path),
        "session_path": str(session_path) if session_path else None,
        "session_url": f"/sessions/{session_path.name}" if session_path else None,
        "script_path": str(script_path) if script_path else None,
        "script_url": f"/scripts/{script_path.name}" if script_path else None,
        "artifacts": artifacts,
        "metadata": {
            "backend": backend.kind,
            "width": spec["width"],
            "height": spec["height"],
            "dpi": spec["dpi"],
            "ray": spec["ray"],
            "preset": spec.get("preset"),
            "source": source_resolution.summary,
            "source_warnings": source_resolution.warnings,
            "warnings": _dedupe_warnings(source_resolution.warnings + [str(w) for w in result_warnings if w]),
            "job_dir": str(job_dir),
            "stdout_log": str(job_dir / "stdout.log"),
            "stderr_log": str(job_dir / "stderr.log"),
        },
    }


def _prepare_source(request: dict[str, Any], job_dir: Path) -> Path:
    try:
        return resolve_source(request, job_dir).path
    except ValueError as exc:
        message = str(exc)
        if any(
            token in message
            for token in ("does not exist", "outside PYMOL_ALLOWED_INPUT_DIR", "Unsupported extension")
        ):
            raise RenderError(message, status_code=400) from exc
        if "Could not download" in message or "Could not connect" in message or "RCSB returned no data" in message:
            raise RenderError(message, status_code=502) from exc
        if "exceeds PYMOL_MAX_FILE_SIZE_MB" in message:
            raise RenderError(message, status_code=413) from exc
        raise RenderError(message, status_code=400) from exc


def _build_job_spec(
    request: dict[str, Any],
    source_path: Path,
    image_path: Path,
    *,
    trusted_script: bool,
) -> dict[str, Any]:
    return {
        "input_path": str(source_path),
        "output_path": str(image_path),
        "object_name": "structure",
        "width": int(request.get("width") or 1600),
        "height": int(request.get("height") or 1200),
        "dpi": int(request.get("dpi") or 300),
        "ray": bool(request.get("ray", True)),
        "transparent": bool(request.get("transparent", False)),
        "render_quality": request.get("render_quality") or "high",
        "preset": request.get("preset") or "publication_cartoon",
        "representations": request.get("representations") or [],
        "color": request.get("color") or "chainbow",
        "background": request.get("background") or "white",
        "show_ligands": bool(request.get("show_ligands", True)),
        "show_metals": bool(request.get("show_metals", True)),
        "show_solvent": bool(request.get("show_solvent", False)),
        "surface_transparency": float(request.get("surface_transparency") or 0.35),
        "zoom_selection": request.get("zoom_selection") or "all",
        "orient_selection": request.get("orient_selection") or "all",
        "highlights": request.get("highlights") or [],
        "labels": request.get("labels") or [],
        "operations": request.get("operations") or [],
        "trusted_script": trusted_script,
        "trusted_commands": request.get("trusted_commands") or [],
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


def _safe_output_name(value: str) -> str:
    import re

    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned[:80] or "pymol_render"


def _safe_filename(value: str) -> str:
    import re

    cleaned = Path(value).name
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", cleaned)[:120] or "inline_structure.pdb"


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for warning in warnings:
        if warning and warning not in seen:
            seen.add(warning)
            result.append(warning)
    return result

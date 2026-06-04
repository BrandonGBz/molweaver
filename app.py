from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

import alignment_tools
import structure_analyzer
from pymol_renderer import (
    OUTPUT_DIR,
    RenderError,
    discover_backend,
    render_structure,
)
from schemas import (
    AlignmentRequest,
    DistanceRequest,
    InspectRequest,
    RenderRequest,
    SiteAnalysisRequest,
    TrustedScriptRequest,
    validate_output_name,
)

app = FastAPI(
    title="MolWeaver",
    version="0.2.0",
    description=(
        "Local FastAPI bridge for generating reproducible molecular figures "
        "with PyMOL from AI agents or scientific scripts."
    ),
)


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "MolWeaver",
        "version": "0.2.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": [
            "/health",
            "/capabilities",
            "/render",
            "/inspect",
            "/measure/distance",
            "/analyze/site",
            "/align",
            "/images/{filename}",
            "/sessions/{filename}",
            "/scripts/{filename}",
        ],
    }


@app.get("/health")
def health() -> dict[str, object]:
    backend = discover_backend()
    return {
        "status": "ok" if backend.available else "missing_pymol",
        "pymol_available": backend.available,
        "backend": backend.kind,
        "backend_command": backend.command,
        "message": backend.message,
        "output_dir": str(OUTPUT_DIR),
    }


@app.get("/capabilities")
def capabilities() -> dict[str, object]:
    backend = discover_backend()
    return {
        "pymol_available": backend.available,
        "input_sources": ["pdb_id", "structure_path", "inline_pdb"],
        "output_format": "png",
        "presets": [
            "publication_cartoon",
            "ligand_focus",
            "surface",
            "active_site",
            "copper_sites",
            "minimal",
        ],
        "representations": ["cartoon", "surface", "sticks", "spheres", "lines"],
        "colors": ["chainbow", "spectrum", "element", "named PyMOL colors", "#RRGGBB"],
        "scene_operations": [
            "show",
            "hide",
            "color",
            "remove",
            "select",
            "label",
            "zoom",
            "orient",
            "center",
            "set_representation",
            "set_background",
            "set_transparency",
        ],
        "artifact_outputs": ["image_png", "session_pse", "reproducible_pml"],
        "analysis_endpoints": ["/inspect", "/measure/distance", "/analyze/site"],
        "alignment_methods": ["align", "super", "cealign"],
        "analysis_policy": "descriptive_geometric_only",
        "safe_by_default": True,
        "trusted_script_endpoint_enabled": backend.allow_unsafe_commands,
    }


@app.post("/render")
def render(request: RenderRequest) -> dict[str, object]:
    _validate_source_count(request.pdb_id, request.structure_path, request.inline_pdb)
    try:
        result = render_structure(request.model_dump(mode="json"))
    except AttributeError:
        result = render_structure(request.dict())
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return _render_response(result, request)


@app.post("/render/trusted-script")
def render_trusted_script(request: TrustedScriptRequest) -> dict[str, object]:
    _validate_source_count(request.pdb_id, request.structure_path, request.inline_pdb)
    try:
        payload = request.model_dump(mode="json")
    except AttributeError:
        payload = request.dict()
    payload["trusted_commands"] = payload.pop("commands")
    try:
        result = render_structure(payload, trusted_script=True)
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return _render_response(result, request)


@app.post("/inspect")
def inspect_endpoint(request: InspectRequest) -> dict[str, object]:
    try:
        return structure_analyzer.inspect_structure(request)
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.post("/measure/distance")
def measure_distance_endpoint(request: DistanceRequest) -> dict[str, object]:
    try:
        return structure_analyzer.measure_distance(request)
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.post("/analyze/site")
def analyze_site_endpoint(request: SiteAnalysisRequest) -> dict[str, object]:
    try:
        return structure_analyzer.analyze_site(request)
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.post("/align")
def align_endpoint(request: AlignmentRequest) -> dict[str, object]:
    try:
        return alignment_tools.align_structures(request)
    except RenderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.get("/images/{filename}")
def image(filename: str) -> FileResponse:
    return _serve_file(OUTPUT_DIR / "images", filename, ".png", "image/png", "Imagen no encontrada.")


@app.get("/sessions/{filename}")
def session_file(filename: str) -> FileResponse:
    return _serve_file(
        OUTPUT_DIR / "sessions",
        filename,
        ".pse",
        "application/octet-stream",
        "Sesión no encontrada.",
    )


@app.get("/scripts/{filename}")
def script_file(filename: str) -> FileResponse:
    return _serve_file(
        OUTPUT_DIR / "scripts",
        filename,
        ".pml",
        "text/plain; charset=utf-8",
        "Script no encontrado.",
    )


def _validate_source_count(*sources: object) -> None:
    count = sum(1 for value in sources if value)
    if count != 1:
        raise HTTPException(
            status_code=400,
            detail="Indica exactamente una fuente: pdb_id, structure_path o inline_pdb.",
        )


def _validate_output_name(value: str | None) -> str | None:
    return validate_output_name(value)


def _with_request_warnings(
    metadata: dict[str, object], request: RenderRequest | TrustedScriptRequest
) -> dict[str, object]:
    enriched = dict(metadata)
    warnings: list[str] = list(enriched.get("warnings", [])) if isinstance(enriched.get("warnings"), list) else []
    if request.structure_path:
        warnings.append("Local structure_path was used; verify it does not reference private data before sharing logs.")
    enriched["warnings"] = warnings
    return enriched


def _render_response(result: dict[str, object], request: RenderRequest | TrustedScriptRequest) -> dict[str, object]:
    image_path = str(result["image_path"])
    image_url = str(result.get("image_url") or f"/images/{Path(image_path).name}")
    session_path = result.get("session_path")
    session_path_text = str(session_path) if session_path else None
    session_url = None
    if session_path_text:
        session_url = str(result.get("session_url") or f"/sessions/{Path(session_path_text).name}")
    script_path = result.get("script_path")
    script_path_text = str(script_path) if script_path else None
    script_url = None
    if script_path_text:
        script_url = str(result.get("script_url") or f"/scripts/{Path(script_path_text).name}")
    artifacts = dict(result.get("artifacts") or {})
    artifacts.setdefault("image_path", image_path)
    artifacts.setdefault("image_url", image_url)
    artifacts.setdefault("session_path", session_path_text)
    artifacts.setdefault("session_url", session_url)
    artifacts.setdefault("script_path", script_path_text)
    artifacts.setdefault("script_url", script_url)
    return {
        "job_id": result["job_id"],
        "image_url": image_url,
        "image_path": image_path,
        "session_path": session_path_text,
        "session_url": session_url,
        "script_path": script_path_text,
        "script_url": script_url,
        "source_path": result["source_path"],
        "artifacts": artifacts,
        "metadata": _with_request_warnings(result["metadata"], request),
    }


def _serve_file(base_dir: Path, filename: str, suffix: str, media_type: str, detail: str) -> FileResponse:
    safe_name = Path(filename).name
    file_path = base_dir / safe_name
    if not file_path.exists() or file_path.suffix.lower() != suffix:
        raise HTTPException(status_code=404, detail=detail)
    return FileResponse(file_path, media_type=media_type, filename=safe_name)

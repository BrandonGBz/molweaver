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
    title="PyMOL Figure Agent",
    version="0.1.0-alpha",
    description=(
        "Local FastAPI bridge for generating reproducible molecular figures "
        "with PyMOL from AI agents or scientific scripts."
    ),
)


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "PyMOL Figure Agent",
        "version": "0.1.0-alpha",
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

    return {
        "job_id": result["job_id"],
        "image_url": f"/images/{Path(result['image_path']).name}",
        "image_path": result["image_path"],
        "source_path": result["source_path"],
        "metadata": _with_request_warnings(result["metadata"], request),
    }


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

    return {
        "job_id": result["job_id"],
        "image_url": f"/images/{Path(result['image_path']).name}",
        "image_path": result["image_path"],
        "source_path": result["source_path"],
        "metadata": _with_request_warnings(result["metadata"], request),
    }


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
    safe_name = Path(filename).name
    image_path = OUTPUT_DIR / "images" / safe_name
    if not image_path.exists() or image_path.suffix.lower() != ".png":
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    return FileResponse(image_path, media_type="image/png", filename=safe_name)


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

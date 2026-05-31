from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from pymol_renderer import (
    OUTPUT_DIR,
    RenderError,
    discover_backend,
    render_structure,
)


OUTPUT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")

app = FastAPI(
    title="PyMOL Figure Agent",
    version="0.1.0-alpha",
    description=(
        "Local FastAPI bridge for generating reproducible molecular figures "
        "with PyMOL from AI agents or scientific scripts."
    ),
)


class Highlight(BaseModel):
    selection: str = Field(..., description="Seleccion PyMOL, por ejemplo: resn CU or elem Cu")
    color: str = Field("yellow", description="Color PyMOL o hexadecimal, por ejemplo yellow o #ff8800")
    representation: Literal["sticks", "spheres", "surface", "cartoon", "lines"] = "sticks"
    label: str | None = Field(None, description="Texto fijo para etiquetar la seleccion.")


class LabelSpec(BaseModel):
    selection: str
    text: str = Field("resn + resi", description="Expresion PyMOL o texto fijo entre comillas.")


class RenderRequest(BaseModel):
    pdb_id: str | None = Field(None, description="ID PDB de 4 caracteres; se descarga desde RCSB.")
    structure_path: str | None = Field(None, description="Ruta local a .pdb, .cif, .mmcif, .sdf, .mol o .pse.")
    inline_pdb: str | None = Field(None, description="Contenido PDB enviado directamente en JSON.")
    inline_name: str = "inline_structure.pdb"

    output_name: str | None = Field(None, description="Nombre base opcional para el PNG.")
    width: int = Field(1600, ge=300, le=5000)
    height: int = Field(1200, ge=300, le=5000)
    dpi: int = Field(300, ge=72, le=1200)
    ray: bool = True
    transparent: bool = False
    timeout_seconds: int = Field(180, ge=10, le=900)

    preset: Literal[
        "publication_cartoon",
        "ligand_focus",
        "surface",
        "active_site",
        "copper_sites",
        "minimal",
    ] = "publication_cartoon"
    representations: list[Literal["cartoon", "surface", "sticks", "spheres", "lines"]] = Field(
        default_factory=list
    )
    color: str = Field("chainbow", description="chainbow, spectrum, element, o color PyMOL/hex.")
    background: str = "white"
    show_ligands: bool = True
    show_metals: bool = True
    show_solvent: bool = False
    surface_transparency: float = Field(0.35, ge=0.0, le=1.0)
    zoom_selection: str = "all"
    orient_selection: str = "all"
    highlights: list[Highlight] = Field(default_factory=list)
    labels: list[LabelSpec] = Field(default_factory=list)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return _validate_output_name(value)


class TrustedScriptRequest(BaseModel):
    structure_path: str | None = None
    pdb_id: str | None = None
    inline_pdb: str | None = None
    commands: list[str] = Field(
        ...,
        min_length=1,
        description="Comandos PyMOL. Requiere PYMOL_ALLOW_UNSAFE_COMMANDS=1.",
    )
    output_name: str | None = None
    width: int = Field(1600, ge=300, le=5000)
    height: int = Field(1200, ge=300, le=5000)
    dpi: int = Field(300, ge=72, le=1200)
    ray: bool = True
    timeout_seconds: int = Field(180, ge=10, le=900)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return _validate_output_name(value)


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "PyMOL Figure Agent",
        "version": "0.1.0-alpha",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": ["/health", "/capabilities", "/render", "/images/{filename}"],
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
    if value is None:
        return value
    text = value.strip()
    if not text:
        raise ValueError("output_name no puede estar vacio.")
    path = Path(text)
    if path.is_absolute() or path.name != text or ".." in path.parts or any(sep in text for sep in ("/", "\\")):
        raise ValueError("output_name debe ser solo un nombre base, no una ruta.")
    if not OUTPUT_NAME_PATTERN.fullmatch(text):
        raise ValueError("output_name solo puede usar letras, numeros, guion, guion bajo y punto.")
    return text


def _with_request_warnings(
    metadata: dict[str, object], request: RenderRequest | TrustedScriptRequest
) -> dict[str, object]:
    enriched = dict(metadata)
    warnings: list[str] = list(enriched.get("warnings", [])) if isinstance(enriched.get("warnings"), list) else []
    if request.structure_path:
        warnings.append("Local structure_path was used; verify it does not reference private data before sharing logs.")
    enriched["warnings"] = warnings
    return enriched

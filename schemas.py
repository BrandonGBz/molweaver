from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


OUTPUT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
PDB_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{4}$")
SAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
SAFE_CHAIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,8}$")
SAFE_ELEMENT_PATTERN = re.compile(r"^[A-Za-z]{1,2}$")


class StructureSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pdb_id: str | None = Field(None, description="ID PDB publico de 4 caracteres; se descarga desde RCSB.")
    structure_path: str | None = Field(
        None,
        description="Ruta local a .pdb, .ent, .pqr, .pdbqt, .cif, .mmcif, .sdf, .mol o .mol2.",
    )
    inline_pdb: str | None = Field(None, description="Contenido PDB enviado directamente en JSON.")
    inline_name: str = "inline_structure.pdb"

    @field_validator("pdb_id")
    @classmethod
    def validate_pdb_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        text = value.strip().upper()
        if not PDB_ID_PATTERN.fullmatch(text):
            raise ValueError("pdb_id debe contener exactamente 4 caracteres alfanumericos.")
        return text

    @model_validator(mode="after")
    def validate_one_source(self) -> StructureSource:
        count = sum(1 for value in (self.pdb_id, self.structure_path, self.inline_pdb) if value)
        if count != 1:
            raise ValueError("Indica exactamente una fuente: pdb_id, structure_path o inline_pdb.")
        return self


class Highlight(BaseModel):
    selection: str = Field(..., description="Seleccion PyMOL, por ejemplo: resn CU or elem Cu")
    color: str = Field("yellow", description="Color PyMOL o hexadecimal, por ejemplo yellow o #ff8800")
    representation: Literal["sticks", "spheres", "surface", "cartoon", "lines"] = "sticks"
    label: str | None = Field(None, description="Texto fijo para etiquetar la seleccion.")


class LabelSpec(BaseModel):
    selection: str
    text: str = Field("resn + resi", description="Expresion PyMOL o texto fijo entre comillas.")


class RenderRequest(StructureSource):
    output_name: str | None = Field(None, description="Nombre base opcional para el PNG.")
    width: int = Field(1600, ge=300, le=5000)
    height: int = Field(1200, ge=300, le=5000)
    dpi: int = Field(300, ge=72, le=1200)
    ray: bool = True
    transparent: bool = False
    timeout_seconds: int = Field(180, ge=10, le=900)
    render_quality: Literal["balanced", "high", "publication", "ultra"] = "high"

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
        return validate_output_name(value)


class TrustedScriptRequest(StructureSource):
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
    render_quality: Literal["balanced", "high", "publication", "ultra"] = "high"

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return validate_output_name(value)


class StructuredSelector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chain: str | None = None
    resi: str | None = Field(None, description="Numero o codigo de residuo validado, por ejemplo 500.")
    resn: str | None = Field(None, description="Nombre de residuo, por ejemplo HIS o CU.")
    atom_name: str | None = Field(None, description="Nombre de atomo, por ejemplo CA, ND1 u O.")
    element: str | None = Field(None, description="Elemento quimico, por ejemplo Cu, Zn, C u O.")
    ligand: str | None = Field(None, description="Nombre de residuo de ligando organico, por ejemplo XYD.")
    metal: bool = False
    organic: bool = False
    within_angstrom: float | None = Field(None, ge=0.1, le=30.0)

    @field_validator("chain")
    @classmethod
    def validate_chain(cls, value: str | None) -> str | None:
        return _validate_safe_token(value, SAFE_CHAIN_PATTERN, "chain")

    @field_validator("resi", "resn", "atom_name", "ligand")
    @classmethod
    def validate_safe_token(cls, value: str | None) -> str | None:
        return _validate_safe_token(value, SAFE_TOKEN_PATTERN, "selector")

    @field_validator("element")
    @classmethod
    def validate_element(cls, value: str | None) -> str | None:
        text = _validate_safe_token(value, SAFE_ELEMENT_PATTERN, "element")
        if text is None:
            return text
        return text[0].upper() + text[1:].lower()

    @model_validator(mode="after")
    def validate_selector_has_filter(self) -> StructuredSelector:
        values = [self.chain, self.resi, self.resn, self.atom_name, self.element, self.ligand]
        if not any(values) and not self.metal and not self.organic:
            raise ValueError("El selector debe incluir al menos un filtro estructurado.")
        if self.metal and self.organic:
            raise ValueError("metal y organic no pueden usarse juntos en el mismo selector.")
        return self


class InspectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: StructureSource
    output_name: str | None = None
    include_solvent: bool = False
    export_pml: bool = False
    timeout_seconds: int = Field(120, ge=10, le=900)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return validate_output_name(value)


class DistanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: StructureSource
    selector_a: StructuredSelector
    selector_b: StructuredSelector
    output_name: str | None = None
    export_pml: bool = False
    timeout_seconds: int = Field(120, ge=10, le=900)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return validate_output_name(value)


class SiteAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: StructureSource
    center: StructuredSelector
    radius_angstrom: float = Field(4.0, ge=0.5, le=20.0)
    output_name: str | None = None
    include_solvent: bool = False
    export_pml: bool = False
    timeout_seconds: int = Field(120, ge=10, le=900)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return validate_output_name(value)


class AlignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: StructureSource | None = None
    mobile: StructureSource | None = None
    reference_pdb_id: str | None = None
    reference_path: str | None = None
    reference_inline_pdb: str | None = None
    reference_inline_name: str | None = None
    mobile_pdb_id: str | None = None
    mobile_path: str | None = None
    mobile_inline_pdb: str | None = None
    mobile_inline_name: str | None = None
    method: Literal["align", "super", "cealign"] = "align"
    output_name: str | None = None
    render: bool = False
    export_pml: bool = False
    width: int = Field(1600, ge=300, le=5000)
    height: int = Field(1200, ge=300, le=5000)
    dpi: int = Field(300, ge=72, le=1200)
    ray: bool = True
    timeout_seconds: int = Field(240, ge=10, le=900)

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, value: str | None) -> str | None:
        return validate_output_name(value)

    @model_validator(mode="after")
    def normalize_sources(self) -> AlignmentRequest:
        self.reference = self._normalize_source(
            current=self.reference,
            prefix="reference",
        )
        self.mobile = self._normalize_source(
            current=self.mobile,
            prefix="mobile",
        )
        return self

    def _normalize_source(self, *, current: StructureSource | None, prefix: str) -> StructureSource:
        flat_payload = {
            "pdb_id" if key == "pdb_id" else key: getattr(self, f"{prefix}_{key}")
            for key in ("pdb_id", "path", "inline_pdb", "inline_name")
        }
        if current is not None and any(value is not None for value in flat_payload.values()):
            raise ValueError(f"No combines el selector anidado y los campos planos para {prefix}.")
        if current is not None:
            return current

        payload = {
            "pdb_id": flat_payload["pdb_id"],
            "structure_path": flat_payload["path"],
            "inline_pdb": flat_payload["inline_pdb"],
            "inline_name": flat_payload["inline_name"] or "inline_structure.pdb",
        }
        if not any(value for value in payload.values() if value is not None):
            raise ValueError(f"Indica exactamente una fuente para {prefix}: referencia PDB, ruta local o PDB inline.")
        return StructureSource.model_validate(payload)


def validate_output_name(value: str | None) -> str | None:
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


def _validate_safe_token(value: str | None, pattern: re.Pattern[str], label: str) -> str | None:
    if value is None:
        return value
    text = value.strip()
    if not pattern.fullmatch(text):
        raise ValueError(f"{label} contiene caracteres no permitidos.")
    return text

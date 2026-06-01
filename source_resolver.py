from __future__ import annotations

import os
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from schemas import StructureSource


ALLOWED_EXTENSIONS = {
    ".pdb",
    ".ent",
    ".pqr",
    ".pdbqt",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol",
    ".mol2",
}
PDB_LIKE_EXTENSIONS = {".pqr", ".pdbqt"}
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")
MAX_FILE_SIZE_MB = int(os.getenv("PYMOL_MAX_FILE_SIZE_MB", "100"))
RCSB_DOWNLOAD_TIMEOUT_SECONDS = 45


@dataclass(slots=True)
class ResolvedSource:
    path: Path
    summary: dict[str, str]
    warnings: list[str]
    source_type: str


def resolve_source(source: StructureSource | dict[str, Any] | Any, job_dir: Path) -> ResolvedSource:
    payload = _coerce_source_payload(source)
    model = StructureSource.model_validate(payload)

    job_dir.mkdir(parents=True, exist_ok=True)

    if model.pdb_id:
        return _resolve_pdb_id(model.pdb_id, job_dir)

    if model.inline_pdb:
        return _resolve_inline_pdb(model, job_dir)

    if model.structure_path:
        return _resolve_local_path(model, job_dir)

    raise ValueError("Missing structure source.")


def _coerce_source_payload(source: StructureSource | dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(source, "model_dump"):
        raw = source.model_dump(mode="json")  # type: ignore[call-arg]
    elif isinstance(source, dict):
        raw = dict(source)
    else:
        raw = {
            key: getattr(source, key, None)
            for key in ("pdb_id", "structure_path", "inline_pdb", "inline_name")
        }
    return {
        "pdb_id": raw.get("pdb_id"),
        "structure_path": raw.get("structure_path"),
        "inline_pdb": raw.get("inline_pdb"),
        "inline_name": raw.get("inline_name") or "inline_structure.pdb",
    }


def _resolve_pdb_id(pdb_id: str, job_dir: Path) -> ResolvedSource:
    source_path = job_dir / f"{pdb_id}.pdb"
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        with urllib.request.urlopen(url, timeout=RCSB_DOWNLOAD_TIMEOUT_SECONDS) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Could not download {pdb_id} from RCSB: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not connect to RCSB to download {pdb_id}: {exc}") from exc
    if not data:
        raise ValueError(f"RCSB returned no data for {pdb_id}.")
    _validate_bytes_size(len(data), label=f"{pdb_id}.pdb")
    source_path.write_bytes(data)
    return ResolvedSource(
        path=source_path,
        summary={"type": "pdb_id", "id": pdb_id},
        warnings=[],
        source_type="pdb_id",
    )


def _resolve_inline_pdb(model: StructureSource, job_dir: Path) -> ResolvedSource:
    inline_name = _safe_filename(model.inline_name or "inline_structure.pdb")
    if Path(inline_name).suffix.lower() not in {".pdb", ".ent"}:
        inline_name = f"{Path(inline_name).stem}.pdb"
    source_path = job_dir / inline_name
    inline_text = str(model.inline_pdb)
    _validate_bytes_size(len(inline_text.encode("utf-8")), label=inline_name)
    source_path.write_text(inline_text, encoding="utf-8")
    return ResolvedSource(
        path=source_path,
        summary={"type": "inline_pdb", "name": inline_name},
        warnings=[],
        source_type="inline_pdb",
    )


def _resolve_local_path(model: StructureSource, job_dir: Path) -> ResolvedSource:
    source_path = Path(str(model.structure_path)).expanduser().resolve()
    if not source_path.exists():
        raise ValueError(f"structure_path does not exist: {source_path}")
    allowed_root = os.getenv("PYMOL_ALLOWED_INPUT_DIR")
    if allowed_root:
        allowed_path = Path(allowed_root).expanduser().resolve()
        if not source_path.is_relative_to(allowed_path):
            raise ValueError("structure_path is outside PYMOL_ALLOWED_INPUT_DIR.")
    suffix = source_path.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported extension. Use one of: {allowed}")
    _validate_bytes_size(source_path.stat().st_size, label=source_path.name)

    normalized_name = _normalized_filename(source_path.name)
    destination = job_dir / normalized_name
    if suffix in PDB_LIKE_EXTENSIONS and destination.suffix.lower() != ".pdb":
        destination = destination.with_suffix(".pdb")
    shutil.copy2(source_path, destination)
    warnings = [
        (
            "Local structure_path was copied into the job directory; the original filesystem path is not "
            "required for reproducibility."
        )
    ]
    return ResolvedSource(
        path=destination,
        summary={"type": "structure_path", "name": source_path.name},
        warnings=warnings,
        source_type="structure_path",
    )


def _validate_bytes_size(size_bytes: int, *, label: str) -> None:
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"{label} exceeds PYMOL_MAX_FILE_SIZE_MB={MAX_FILE_SIZE_MB}.")


def _safe_filename(value: str) -> str:
    cleaned = Path(value).name
    cleaned = SAFE_FILENAME_PATTERN.sub("_", cleaned)
    return cleaned[:120] or "inline_structure.pdb"


def _normalized_filename(value: str) -> str:
    cleaned = _safe_filename(value)
    suffix = Path(cleaned).suffix.lower()
    if suffix in PDB_LIKE_EXTENSIONS:
        return f"{Path(cleaned).stem}.pdb"
    return cleaned

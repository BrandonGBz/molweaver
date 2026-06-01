from pathlib import Path

import pytest
from pydantic import ValidationError

from pymol_renderer import RenderError, _prepare_source
from schemas import (
    AlignmentRequest,
    DistanceRequest,
    SiteAnalysisRequest,
    StructureSource,
    StructuredSelector,
)
from source_resolver import resolve_source


def test_structure_source_requires_exactly_one_source() -> None:
    with pytest.raises(ValidationError):
        StructureSource()

    with pytest.raises(ValidationError):
        StructureSource(pdb_id="1GYC", inline_pdb="ATOM")


def test_analysis_requests_accept_public_pdb_ids() -> None:
    DistanceRequest(
        source={"pdb_id": "1GYC"},
        selector_a={"chain": "A", "resi": "500", "resn": "CU", "element": "Cu"},
        selector_b={"chain": "A", "resi": "501", "resn": "CU", "element": "Cu"},
    )
    SiteAnalysisRequest(
        source={"pdb_id": "6LU7"},
        center={"chain": "C", "organic": True},
        radius_angstrom=4.0,
    )
    AlignmentRequest(
        reference={"pdb_id": "1GYC"},
        mobile={"pdb_id": "1KYA"},
        method="super",
    )
    AlignmentRequest(
        reference_pdb_id="1GYC",
        mobile_pdb_id="1KYA",
        method="align",
    )


def test_structured_selector_rejects_free_form_or_empty_selection() -> None:
    with pytest.raises(ValidationError):
        StructuredSelector()

    with pytest.raises(ValidationError):
        StructuredSelector(resi="500 or all")

    with pytest.raises(ValidationError):
        StructuredSelector(chain="A", selection="all")  # type: ignore[call-arg]


def test_alignment_request_rejects_unknown_method() -> None:
    with pytest.raises(ValidationError):
        AlignmentRequest(
            reference={"pdb_id": "1GYC"},
            mobile={"pdb_id": "1KYA"},
            method="magic",
        )


def test_prepare_source_rejects_path_outside_allowed_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.pdb"
    outside.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000\nEND\n", encoding="utf-8")
    monkeypatch.setenv("PYMOL_ALLOWED_INPUT_DIR", str(allowed))

    with pytest.raises(RenderError):
        _prepare_source({"structure_path": str(outside)}, tmp_path / "job")


def test_resolve_source_copies_local_structure_into_job_dir(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdb"
    source.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000\nEND\n", encoding="utf-8")
    job_dir = tmp_path / "job"

    resolved = resolve_source({"structure_path": str(source)}, job_dir)

    assert resolved.path.parent == job_dir
    assert resolved.path.exists()
    assert resolved.summary["type"] == "structure_path"
    assert resolved.warnings

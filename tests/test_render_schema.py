from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import RenderRequest, _validate_source_count
from pymol_renderer import RenderError, _prepare_source


def test_render_request_accepts_public_pdb_id() -> None:
    request = RenderRequest(pdb_id="1GYC", output_name="1gyc_copper_sites")

    assert request.pdb_id == "1GYC"
    assert request.output_name == "1gyc_copper_sites"


@pytest.mark.parametrize("output_name", ["../bad", "nested/name", r"nested\name", "C:/temp/out", "C:temp"])
def test_render_request_rejects_path_like_output_name(output_name: str) -> None:
    with pytest.raises(ValidationError):
        RenderRequest(pdb_id="1GYC", output_name=output_name)


def test_source_count_rejects_multiple_sources_before_pymol() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _validate_source_count("1GYC", None, "ATOM      1  N   ALA A   1       0.0   0.0   0.0")

    assert exc_info.value.status_code == 400


def test_prepare_source_rejects_bad_pdb_id(tmp_path: Path) -> None:
    with pytest.raises(RenderError):
        _prepare_source({"pdb_id": "BAD!"}, tmp_path)


def test_prepare_source_rejects_missing_local_file(tmp_path: Path) -> None:
    with pytest.raises(RenderError):
        _prepare_source({"structure_path": str(tmp_path / "missing.pdb")}, tmp_path)


def test_prepare_source_accepts_pdbqt_and_normalizes_to_pdb(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdbqt"
    source.write_text(
        "\n".join(
            [
                "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N",
                "HETATM    2 CU    CU E   1       1.000   2.000   3.000  1.00  0.00          Cu",
                "END",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    normalized = _prepare_source({"structure_path": str(source)}, tmp_path)

    assert normalized.suffix == ".pdb"
    assert normalized.exists()
    assert normalized.read_text(encoding="utf-8").startswith("ATOM      1  N   ALA A   1")

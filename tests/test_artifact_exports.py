from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module
from artifact_export import build_render_script_text
from schemas import RenderRequest


client = TestClient(app_module.app)


def test_render_request_defaults_to_script_export_and_no_session() -> None:
    request = RenderRequest(pdb_id="1GYC")

    assert request.export_script is True
    assert request.export_session is False


def test_build_render_script_text_includes_public_fetch_and_session_save(tmp_path: Path) -> None:
    script = build_render_script_text(
        {
            "width": 1200,
            "height": 900,
            "dpi": 300,
            "ray": True,
            "background": "white",
            "preset": "publication_cartoon",
            "render_quality": "high",
            "representations": ["cartoon"],
            "color": "chainbow",
            "show_ligands": True,
            "show_metals": True,
            "show_solvent": False,
            "surface_transparency": 0.35,
            "zoom_selection": "all",
            "orient_selection": "all",
            "highlights": [],
            "labels": [],
            "operations": [
                {"action": "hide", "target": "everything", "selection": "all"},
                {"action": "show", "representation": "cartoon", "selection": "polymer.protein"},
                {"action": "color", "color": "slate", "selection": "polymer.protein"},
            ],
        },
        source_type="pdb_id",
        source_summary={"type": "pdb_id", "id": "1GYC"},
        source_path=tmp_path / "1GYC.pdb",
        image_path=tmp_path / "figure.png",
        session_path=tmp_path / "figure.pse",
    )

    assert "fetch 1GYC, structure, async=0" in script
    assert "hide everything, all" in script
    assert "show cartoon, polymer.protein" in script
    assert "color slate, polymer.protein" in script
    assert "save \"" in script
    assert "png \"" in script


def test_runtime_session_and_script_endpoints_serve_only_runtime_files(tmp_path: Path, monkeypatch) -> None:
    outputs = tmp_path
    (outputs / "sessions").mkdir(parents=True, exist_ok=True)
    (outputs / "scripts").mkdir(parents=True, exist_ok=True)
    (outputs / "sessions" / "demo.pse").write_bytes(b"PSE")
    (outputs / "scripts" / "demo.pml").write_text("load demo.pdb, structure\n", encoding="utf-8")
    monkeypatch.setattr(app_module, "OUTPUT_DIR", outputs)

    session_response = client.get("/sessions/demo.pse")
    script_response = client.get("/scripts/demo.pml")

    assert session_response.status_code == 200
    assert session_response.content == b"PSE"
    assert script_response.status_code == 200
    assert "load demo.pdb" in script_response.text
    assert client.get("/sessions/../../demo.pse").status_code == 404
    assert client.get("/scripts/../../demo.pml").status_code == 404

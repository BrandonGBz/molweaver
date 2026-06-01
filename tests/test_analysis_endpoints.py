from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module


client = TestClient(app_module.app)


def test_render_endpoint_can_be_mocked(monkeypatch) -> None:
    monkeypatch.setattr(
        app_module,
        "render_structure",
        lambda request, trusted_script=False: {
            "job_id": "job123",
            "image_path": "K:/tmp/figure.png",
            "source_path": "K:/tmp/source.pdb",
            "metadata": {"backend": "mock", "warnings": []},
        },
    )

    response = client.post("/render", json={"pdb_id": "1GYC"})

    assert response.status_code == 200
    assert response.json()["image_path"].endswith("figure.png")


def test_inspect_endpoint_can_be_mocked(monkeypatch) -> None:
    def _mock_inspect(request):
        return {
            "job_id": "job123",
            "result": {"atom_count": 10},
            "metadata": {},
            "warnings": [],
            "artifacts": {},
        }

    monkeypatch.setattr(
        app_module.structure_analyzer,
        "inspect_structure",
        _mock_inspect,
    )

    response = client.post("/inspect", json={"source": {"pdb_id": "1GYC"}})

    assert response.status_code == 200
    assert response.json()["result"]["atom_count"] == 10


def test_distance_endpoint_can_be_mocked(monkeypatch) -> None:
    def _mock_distance(request):
        return {
            "job_id": "job123",
            "result": {"distance_angstrom": 3.2},
            "metadata": {},
            "warnings": [],
            "artifacts": {},
        }

    monkeypatch.setattr(
        app_module.structure_analyzer,
        "measure_distance",
        _mock_distance,
    )

    response = client.post(
        "/measure/distance",
        json={
            "source": {"pdb_id": "1GYC"},
            "selector_a": {"chain": "A", "resi": "500", "resn": "CU", "element": "Cu"},
            "selector_b": {"chain": "A", "resi": "501", "resn": "CU", "element": "Cu"},
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["distance_angstrom"] == 3.2


def test_site_endpoint_can_be_mocked(monkeypatch) -> None:
    def _mock_site(request):
        return {
            "job_id": "job123",
            "result": {"nearby_residue_count": 3},
            "metadata": {},
            "warnings": [],
            "artifacts": {},
        }

    monkeypatch.setattr(
        app_module.structure_analyzer,
        "analyze_site",
        _mock_site,
    )

    response = client.post(
        "/analyze/site",
        json={
            "source": {"pdb_id": "6LU7"},
            "center": {"chain": "A", "resi": "145", "resn": "HIS"},
            "radius_angstrom": 4.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["nearby_residue_count"] == 3


def test_alignment_endpoint_can_be_mocked(monkeypatch) -> None:
    def _mock_align(request):
        return {
            "job_id": "job123",
            "result": {"rmsd_angstrom": 1.1, "aligned_atoms": 100, "method": "align"},
            "metadata": {},
            "warnings": [],
            "artifacts": {},
        }

    monkeypatch.setattr(
        app_module.alignment_tools,
        "align_structures",
        _mock_align,
    )

    response = client.post(
        "/align",
        json={
            "reference": {"pdb_id": "1GYC"},
            "mobile": {"pdb_id": "1KYA"},
            "method": "align",
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["method"] == "align"

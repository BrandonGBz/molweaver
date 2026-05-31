from app import capabilities, health


def test_health_schema() -> None:
    data = health()

    assert data["status"] in {"ok", "missing_pymol"}
    assert isinstance(data["pymol_available"], bool)
    assert "backend" in data
    assert "message" in data
    assert "output_dir" in data


def test_capabilities_schema() -> None:
    data = capabilities()

    assert "pdb_id" in data["input_sources"]
    assert data["output_format"] == "png"
    assert "copper_sites" in data["presets"]

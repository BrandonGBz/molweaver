"""Tests for mcp_server.py.

These tests do NOT require PyMOL. They validate:
- Import behaviour when MCP is installed.
- That tools, prompts, and resources are registered.
- That tool input schemas are valid.
- That stdout is not written to during import.
- Mocked tool execution paths.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import logging  # noqa: E402

logging.disable(logging.CRITICAL)


def _patch_pymol_discovery(monkeypatch, available: bool = True) -> None:
    """Patch discover_backend so the MCP server does not need real PyMOL."""
    from backend_discovery import Backend

    if available:
        backend = Backend(
            available=True,
            kind="test_mock",
            command=[sys.executable],
            message="Mock PyMOL for testing.",
            allow_unsafe_commands=False,
        )
    else:
        backend = Backend(
            available=False,
            kind="missing",
            command=[],
            message="PyMOL not available.",
            allow_unsafe_commands=False,
        )
    monkeypatch.setattr("backend_discovery.discover_backend", lambda base_dir=None: backend)


def _reset_import_cache() -> None:
    """Clear the lazy-import cache so mocks take effect."""
    import mcp_server

    mcp_server._figure_imports.clear()


# ── import tests ─────────────────────────────────────────────────────────────


def test_mcp_server_imports_without_pymol() -> None:
    import mcp_server  # noqa: F401


def test_mcp_server_name() -> None:
    from mcp_server import mcp as mcp_instance

    assert mcp_instance.name == "molweaver"


def test_no_stdout_on_import(capsys) -> None:
    import importlib

    import mcp_server  # noqa: F401

    importlib.reload(mcp_server)
    captured = capsys.readouterr()
    assert captured.out == "", f"stdout should be empty, got: {captured.out!r}"


# ── tool registration tests ──────────────────────────────────────────────────


def test_seven_tools_registered() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    tool_names = {t.name for t in tools}
    expected = {
        "render_molecular_figure",
        "inspect_structure",
        "measure_distance",
        "analyze_binding_site",
        "align_structures",
        "generate_site_report",
        "export_pymol_script",
    }
    assert tool_names == expected


def test_tool_render_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    render = next(t for t in tools if t.name == "render_molecular_figure")
    assert "properties" in render.parameters
    assert "output_name" in render.parameters["properties"]


def test_tool_inspect_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    inspect = next(t for t in tools if t.name == "inspect_structure")
    assert "properties" in inspect.parameters
    assert "pdb_id" in inspect.parameters["properties"]


def test_tool_measure_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    measure = next(t for t in tools if t.name == "measure_distance")
    assert "properties" in measure.parameters
    assert "pdb_id" in measure.parameters["properties"]


def test_tool_align_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    align = next(t for t in tools if t.name == "align_structures")
    assert "properties" in align.parameters
    assert "reference_pdb_id" in align.parameters["properties"]


def test_tool_site_report_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    site = next(t for t in tools if t.name == "generate_site_report")
    assert "properties" in site.parameters
    assert "output_name" in site.parameters["properties"]


def test_tool_export_script_has_input_schema() -> None:
    from mcp_server import mcp as mcp_instance

    tools = mcp_instance._tool_manager.list_tools()
    export = next(t for t in tools if t.name == "export_pymol_script")
    assert "properties" in export.parameters
    assert "output_name" in export.parameters["properties"]


# ── prompt registration tests ────────────────────────────────────────────────


def test_five_prompts_registered() -> None:
    from mcp_server import mcp as mcp_instance

    prompts = mcp_instance._prompt_manager.list_prompts()
    prompt_names = {p.name for p in prompts}
    expected = {
        "create_publication_figure",
        "inspect_active_site",
        "align_and_compare_structures",
        "prepare_docking_pose_figure",
        "render_md_snapshot",
    }
    assert prompt_names == expected


# ── resource registration tests ──────────────────────────────────────────────


def test_four_resources_registered() -> None:
    from mcp_server import mcp as mcp_instance

    resources = mcp_instance._resource_manager.list_resources()
    uris = {str(r.uri) for r in resources}
    expected = {
        "molweaver://capabilities",
        "molweaver://presets",
        "molweaver://security-model",
        "molweaver://examples",
    }
    assert uris == expected


def test_capabilities_resource_returns_json() -> None:
    from mcp_server import mcp as mcp_instance

    resources = mcp_instance._resource_manager.list_resources()
    caps = next(r for r in resources if str(r.uri) == "molweaver://capabilities")
    result = caps.fn()
    data = json.loads(result)
    assert "presets" in data
    assert "alignment_methods" in data
    assert "scene_operations" in data


def test_presets_resource_returns_json() -> None:
    from mcp_server import mcp as mcp_instance

    resources = mcp_instance._resource_manager.list_resources()
    presets = next(r for r in resources if str(r.uri) == "molweaver://presets")
    result = presets.fn()
    data = json.loads(result)
    assert "publication_cartoon" in data
    assert "copper_sites" in data


# ── mock tool tests ──────────────────────────────────────────────────────────


def test_inspect_structure_mocked(monkeypatch) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=True)

    mock_result = {
        "result": {
            "chains": [{"id": "A", "residues": 100}],
            "residue_count": 100,
            "ligands": ["XYD"],
            "metals": ["Cu"],
            "solvent_present": True,
        },
        "warnings": [],
    }
    monkeypatch.setattr("structure_analyzer.inspect_structure", lambda request: mock_result)

    from mcp_server import _ensure_imports, inspect_structure_tool

    _ensure_imports()
    result = inspect_structure_tool(pdb_id="1GYC")
    assert result.chains == [{"id": "A", "residues": 100}]
    assert result.ligands == ["XYD"]
    assert result.metals == ["Cu"]
    assert result.solvent_present is True


def test_measure_distance_mocked(monkeypatch) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=True)

    mock_result = {
        "result": {
            "distance_angstrom": 2.5,
            "selection_a": {"atoms": 1},
            "selection_b": {"atoms": 1},
            "atoms": [{"name": "CA", "resn": "HIS", "resi": "100"}],
        },
        "warnings": [],
    }
    monkeypatch.setattr("structure_analyzer.measure_distance", lambda request: mock_result)

    from mcp_server import _ensure_imports, measure_distance_tool

    _ensure_imports()
    result = measure_distance_tool(
        pdb_id="1GYC", chain_a="A", resi_a="100", resn_a="HIS",
        chain_b="A", resi_b="200", resn_b="CYS",
    )
    assert result.distance_angstrom == 2.5


def test_align_structures_mocked(monkeypatch) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=True)

    mock_result = {
        "result": {"rmsd_angstrom": 1.2, "aligned_atoms": 450, "method": "super"},
        "warnings": [],
        "artifacts": {},
    }
    monkeypatch.setattr("alignment_tools.align_structures", lambda request: mock_result)

    from mcp_server import _ensure_imports, align_structures_tool

    _ensure_imports()
    result = align_structures_tool(reference_pdb_id="1GYC", mobile_pdb_id="1KYA", method="super")
    assert result.rmsd_angstrom == 1.2
    assert result.aligned_atoms == 450


def test_pymol_unavailable_raises_clear_error(monkeypatch) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=False)

    from mcp_server import _ensure_imports, inspect_structure_tool

    _ensure_imports()
    with pytest.raises(RuntimeError, match="PyMOL is not available"):
        inspect_structure_tool(pdb_id="1GYC")


def test_export_pymol_script_mocked(monkeypatch, tmp_path) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=True)

    monkeypatch.setattr("pymol_renderer.OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        "source_resolver.resolve_source",
        lambda source, job_dir: mock.Mock(
            path=tmp_path / "1GYC.pdb",
            summary={"type": "pdb_id", "id": "1GYC"},
            warnings=[],
            source_type="pdb_id",
        ),
    )

    from mcp_server import _ensure_imports, export_pymol_script_tool

    _ensure_imports()
    result = export_pymol_script_tool(output_name="test_export", pdb_id="1GYC")
    assert "test_export" in result.script_path
    assert result.script_url.startswith("/scripts/")
    assert Path(result.script_path).exists()
    content = Path(result.script_path).read_text()
    assert "fetch 1GYC" in content


def test_site_report_mocked(monkeypatch) -> None:
    _reset_import_cache()
    _patch_pymol_discovery(monkeypatch, available=True)

    mock_inspect = {
        "result": {
            "chains": [{"id": "A"}],
            "ligands": ["XYD"],
            "metals": [],
            "solvent_present": False,
            "residue_count": 300,
        },
        "warnings": [],
    }
    mock_site = {
        "result": {
            "nearby_residues": [{"resn": "HIS"}],
            "residue_count": 5,
            "center_selection": {"organic": True},
            "radius_angstrom": 4.0,
        },
        "warnings": [],
    }
    mock_render = {
        "image_path": "/tmp/out.png",
        "image_url": "/images/out.png",
        "session_path": None,
        "script_path": "/tmp/out.pml",
        "metadata": {"warnings": []},
    }

    monkeypatch.setattr("structure_analyzer.inspect_structure", lambda req: mock_inspect)
    monkeypatch.setattr("structure_analyzer.analyze_site", lambda req: mock_site)
    monkeypatch.setattr("pymol_renderer.render_structure", lambda req: mock_render)

    from mcp_server import _ensure_imports, generate_site_report_tool

    _ensure_imports()
    result = generate_site_report_tool(output_name="test_site_report", pdb_id="6LU7", center_organic=True)
    assert result.inspection is not None
    assert result.site_analysis is not None
    assert len(result.structured_notes) >= 2
    assert result.artifacts.get("image_path") == "/tmp/out.png"

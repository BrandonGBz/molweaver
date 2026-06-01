from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

import backend_discovery


@pytest.mark.parametrize(
    ("platform_name", "expected_parts"),
    [
        ("Windows", ("tools", "pymol_env", "python.exe")),
        ("Linux", ("tools", "pymol_env", "bin", "python")),
        ("Darwin", ("tools", "pymol_env", "bin", "python")),
    ],
)
def test_local_pymol_python_path_by_platform(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    platform_name: str,
    expected_parts: tuple[str, ...],
) -> None:
    monkeypatch.setattr(backend_discovery.platform, "system", lambda: platform_name)

    path = backend_discovery.local_pymol_python_path(tmp_path)

    assert path == tmp_path.joinpath(*expected_parts)


def test_discover_backend_prefers_configured_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = tmp_path / "pymol"
    configured.write_text("", encoding="utf-8")
    local_python = tmp_path / "tools" / "pymol_env" / "bin" / "python"
    local_python.parent.mkdir(parents=True, exist_ok=True)
    local_python.write_text("", encoding="utf-8")

    monkeypatch.setenv("PYMOL_EXECUTABLE", str(configured))
    monkeypatch.delenv("PYMOL_ALLOW_UNSAFE_COMMANDS", raising=False)
    monkeypatch.setattr(backend_discovery, "local_pymol_python_path", lambda base_dir=None: local_python)
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/pymol")
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(backend_discovery, "_can_import_pymol2", lambda: False)

    backend = backend_discovery.discover_backend(tmp_path)

    assert backend.kind == "pymol_executable"
    assert backend.command == [str(configured)]


def test_discover_backend_prefers_local_env_over_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_python = tmp_path / "tools" / "pymol_env" / "bin" / "python"
    local_python.parent.mkdir(parents=True, exist_ok=True)
    local_python.write_text("", encoding="utf-8")

    monkeypatch.delenv("PYMOL_EXECUTABLE", raising=False)
    monkeypatch.setattr(backend_discovery, "local_pymol_python_path", lambda base_dir=None: local_python)
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/pymol")
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(backend_discovery, "_can_import_pymol2", lambda: False)

    backend = backend_discovery.discover_backend(tmp_path)

    assert backend.kind == "bundled_conda_pymol2"
    assert backend.command == [str(local_python)]


def test_discover_backend_missing_when_no_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PYMOL_EXECUTABLE", raising=False)
    monkeypatch.setattr(
        backend_discovery,
        "local_pymol_python_path",
        lambda base_dir=None: tmp_path / "tools" / "pymol_env" / "bin" / "python",
    )
    monkeypatch.setattr(shutil, "which", lambda _: None)
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(backend_discovery, "_can_import_pymol2", lambda: False)

    backend = backend_discovery.discover_backend(tmp_path)

    assert backend.kind == "missing"
    assert backend.available is False


def test_portable_scripts_exist() -> None:
    assert Path("install.sh").exists()
    assert Path("start_server.sh").exists()

from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Backend:
    available: bool
    kind: str
    command: list[str]
    message: str
    allow_unsafe_commands: bool = False


def local_pymol_python_path(base_dir: Path | None = None) -> Path:
    root = base_dir or BASE_DIR
    system_name = platform.system().lower()
    if system_name == "windows":
        return root / "tools" / "pymol_env" / "python.exe"
    return root / "tools" / "pymol_env" / "bin" / "python"


def discover_backend(base_dir: Path | None = None) -> Backend:
    root = base_dir or BASE_DIR
    allow_unsafe = os.getenv("PYMOL_ALLOW_UNSAFE_COMMANDS") == "1"
    configured = os.getenv("PYMOL_EXECUTABLE")
    if configured:
        executable = Path(configured).expanduser()
        if executable.exists():
            return Backend(
                True,
                "pymol_executable",
                [str(executable)],
                "PyMOL detected through PYMOL_EXECUTABLE.",
                allow_unsafe,
            )
        return Backend(
            False,
            "missing",
            [],
            f"PYMOL_EXECUTABLE points to a missing path: {configured}",
            allow_unsafe,
        )

    bundled_python = local_pymol_python_path(root)
    if bundled_python.exists():
        return Backend(
            True,
            "bundled_conda_pymol2",
            [str(bundled_python)],
            "PyMOL/pymol2 detected in the local conda environment for this API.",
            allow_unsafe,
        )

    executable = shutil.which("pymol")
    if executable:
        return Backend(
            True,
            "pymol_executable",
            [executable],
            "PyMOL detected in PATH.",
            allow_unsafe,
        )

    from importlib.util import find_spec

    if find_spec("pymol2") and _can_import_pymol2():
        return Backend(
            True,
            "python_pymol2",
            [sys.executable],
            "pymol2 module available in the Python runtime that runs this API.",
            allow_unsafe,
        )

    return Backend(
        False,
        "missing",
        [],
        "PyMOL was not found. Install PyMOL with conda-forge or set PYMOL_EXECUTABLE.",
        allow_unsafe,
    )


def _can_import_pymol2() -> bool:
    try:
        import pymol2  # noqa: F401
    except Exception:
        return False
    return True

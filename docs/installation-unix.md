# Linux and macOS Installation

Linux x86_64, macOS Intel, and macOS Apple Silicon are supported experimentally through conda-forge or micromamba.

## Quick install

```bash
git clone https://github.com/BrandonGBz/molweaver.git
cd molweaver
chmod +x install.sh start_server.sh
./install.sh
./start_server.sh
```

One-command install:

```bash
./install.sh --start
```

## What the installer does

- Creates or reuses `.venv`
- Installs `requirements.txt`
- Creates or reuses `tools/pymol_env`
- Creates `.env` from `.env.example` when needed
- Prefers system `micromamba`, `mamba`, or `conda` when available
- Falls back to a local `micromamba` download when no package manager is installed
- Verifies `pymol2` inside the local PyMOL environment

## Notes

- Headless Linux systems may need Xvfb or OpenGL support for full rendering.
- macOS requires a conda-forge build of `pymol-open-source`.
- The API still runs locally on `127.0.0.1` by default.

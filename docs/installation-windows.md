# Windows Installation

Windows 10/11 is the recommended development path and has been tested locally.

## Quick install

```powershell
git clone https://github.com/BrandonGBz/molweaver.git
cd molweaver
.\install.ps1
.\start_server.ps1
```

One-command install:

```powershell
.\install.ps1 -Start
```

## What the installer does

- Creates or reuses `.venv`
- Installs `requirements.txt`
- Creates or reuses `tools/pymol_env`
- Creates `.env` from `.env.example` when needed
- Verifies `pymol2` inside the local conda-forge environment

## Notes

PyMOL should be installed through conda-forge or micromamba. On Windows, `pip install pymol-open-source` may install but fail at runtime because native DLLs such as OpenGL, GLEW, FreeType, libpng, libxml2, or NetCDF are missing.

On Windows, `pip install pymol-open-source` may install but fail at runtime because native DLLs such as OpenGL, GLEW, FreeType, libpng, libxml2, or NetCDF are missing. Conda-forge packages these dependencies more reliably.

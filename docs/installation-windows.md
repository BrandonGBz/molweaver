# Windows Installation

Windows support has been tested locally.

## Python API dependencies

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## PyMOL through micromamba

The recommended route is conda-forge:

```powershell
.\setup_pymol_env.ps1
```

This creates a local ignored environment under `tools/pymol_env`.

## Start the server

```powershell
.\start_server.ps1
```

The default server is:

```text
http://127.0.0.1:8010
```

## Why not pip PyMOL?

On Windows, `pip install pymol-open-source` may install but fail at runtime because native DLLs such as OpenGL, GLEW, FreeType, libpng, libxml2, or NetCDF are missing. Conda-forge packages these dependencies more reliably.

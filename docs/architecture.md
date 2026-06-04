# Architecture

MolWeaver is a local FastAPI bridge around PyMOL.

## Components

- `app.py`: HTTP API, request schemas, endpoint validation, response shape.
- `backend_discovery.py`: platform-aware PyMOL backend detection and local environment path selection.
- `pymol_renderer.py`: backend discovery, source preparation, job folders, PyMOL subprocess execution.
- `render_job.py`: isolated PyMOL scene construction and PNG export.

## Flow

```text
Client or AI agent
  -> POST /render
  -> validate request
  -> download PDB or validate local file
  -> create render job spec
  -> run PyMOL/pymol2
  -> save PNG under outputs/images
  -> return image_path and image_url
```

## Backends

The renderer checks, in order:

1. `PYMOL_EXECUTABLE`
2. local conda-forge environment at `tools/pymol_env` using the platform-specific Python path
3. `pymol` on `PATH`
4. importable `pymol2`

The local conda backend is recommended on all platforms because it keeps PyMOL isolated from the system Python and matches the repository's local-first design.

# Architecture

PyMOL Figure Agent is a local FastAPI bridge around PyMOL.

## Components

- `app.py`: HTTP API, request schemas, endpoint validation, response shape.
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
2. local conda environment at `tools/pymol_env`
3. `pymol` on `PATH`
4. importable `pymol2`

The local conda backend is recommended for Windows.

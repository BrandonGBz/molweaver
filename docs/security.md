# Security Notes

## Threats

- Arbitrary local paths could reveal private data.
- Publicly exposing the API could allow unwanted render jobs.
- Arbitrary PyMOL commands could perform unsafe actions.
- Logs and examples can leak private structures, unpublished data, or personal paths.
- Structural analysis endpoints can still leak geometry or labels if private paths or unpublished coordinates are used.

## Current mitigations

- Default host is `127.0.0.1`.
- `output_name` cannot be a path.
- `PYMOL_ALLOWED_INPUT_DIR` can restrict local file inputs.
- `PYMOL_MAX_FILE_SIZE_MB` limits input size.
- `/render/trusted-script` is disabled unless `PYMOL_ALLOW_UNSAFE_COMMANDS=1`.
- `source_resolver.py` copies local inputs into per-job folders so analysis jobs do not mutate original files.
- `/inspect`, `/measure/distance`, `/analyze/site`, and `/align` use controlled job specs instead of arbitrary PyMOL commands from the client.
- Analysis outputs are described as geometric and descriptive only.
- `.gitignore` excludes outputs, environments, logs, and PyMOL session files.

## Pending mitigations

- Optional authentication.
- Stronger sandboxing for local file access.
- Command allowlists for advanced PyMOL operations.
- Safer deployment profile for shared machines.

## Public contribution rule

Do not submit private structures, unpublished data, credentials, local research paths, rendered private images, or generated heavy outputs.

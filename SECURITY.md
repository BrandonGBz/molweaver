# Security Policy

## Reporting vulnerabilities

Do not open public issues for security vulnerabilities. Use GitHub Private Vulnerability Reporting for this repository.

If private reporting is temporarily unavailable, contact the maintainer privately through GitHub before sharing technical details.

## Sensitive data

Do not share:

- private file paths,
- unpublished structures,
- credentials,
- API keys,
- tokens,
- private `.pse` sessions,
- generated images that reveal unpublished research.

## Local-first design

This API is designed to run locally on `127.0.0.1`. It should not be exposed directly to the internet.

Running it on a public interface without authentication and sandboxing may expose local files or allow unsafe workloads.

## Current mitigations

- The default host is `127.0.0.1`.
- `output_name` is validated as a base name, not a path.
- `trusted-script` is disabled unless `PYMOL_ALLOW_UNSAFE_COMMANDS=1`.
- Local structure paths can be restricted with `PYMOL_ALLOWED_INPUT_DIR`.
- Maximum input size can be limited with `PYMOL_MAX_FILE_SIZE_MB`.

## Planned hardening

Future versions should add optional authentication, stricter sandboxing, command allowlists, request logging controls, and safer deployment profiles.

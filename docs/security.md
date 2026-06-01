# Security Notes

For the current security model, see [security-model.md](security-model.md) and the repository-level [SECURITY.md](../SECURITY.md).

Key reminders:

- The API is local-first and should bind to `127.0.0.1` by default.
- Structured operations are preferred over raw PyMOL commands.
- User files, rendered outputs, sessions and scripts are runtime artifacts and should remain local unless they are intentional public examples.
- Basename-only checks are used for served artifact filenames.
- Trusted-script mode stays disabled by default.


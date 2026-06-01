#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo ".venv no existe o no contiene bin/python. Ejecuta ./install.sh primero." >&2
  exit 1
fi

HOST="${PYMOL_API_HOST:-127.0.0.1}"
PORT="${PYMOL_API_PORT:-8010}"

cd "$ROOT_DIR"
exec "$PYTHON" -m uvicorn app:app --host "$HOST" --port "$PORT"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
PYMOL_PYTHON="$ROOT_DIR/tools/pymol_env/bin/python"

if [ -x "$PYTHON" ] && "$PYTHON" -c "import fastapi" 2>/dev/null; then
  :
elif [ -x "$PYMOL_PYTHON" ]; then
  log() { printf '\n%s\n' "$1"; }
  log ".venv no disponible o incompleto. Usando el Python del entorno PyMOL."
  "$PYMOL_PYTHON" -m pip install -r "$ROOT_DIR/requirements.txt" 2>/dev/null || true
  PYTHON="$PYMOL_PYTHON"
else
  echo "No se encontro un entorno Python valido. Ejecuta ./install.sh primero." >&2
  exit 1
fi

HOST="${PYMOL_API_HOST:-127.0.0.1}"
PORT="${PYMOL_API_PORT:-8010}"

cd "$ROOT_DIR"
exec "$PYTHON" -m uvicorn app:app --host "$HOST" --port "$PORT"

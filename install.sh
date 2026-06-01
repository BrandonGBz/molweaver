#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log() {
  printf '\n%s\n' "$1"
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 no está instalado o no está en PATH." >&2
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Se requiere Python 3.10 o superior.")
PY

if [ ! -d ".venv" ]; then
  log "Creando entorno virtual .venv..."
  python3 -m venv .venv
fi

log "Actualizando pip e instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  log "Creando .env desde .env.example..."
  cp .env.example .env
fi

TOOLS_DIR="$ROOT_DIR/tools"
PYMOL_PYTHON="$TOOLS_DIR/pymol_env/bin/python"

if [ -x "$PYMOL_PYTHON" ]; then
  log "Verificando PyMOL existente..."
  "$PYMOL_PYTHON" -c "import pymol2; print('PyMOL/pymol2 ready')"
else
  if command -v micromamba >/dev/null 2>&1; then
    log "Creando entorno PyMOL con micromamba..."
    micromamba create -y -p "$TOOLS_DIR/pymol_env" -c conda-forge python=3.10 pymol-open-source
    "$PYMOL_PYTHON" -c "import pymol2; print('PyMOL/pymol2 ready')"
  elif command -v conda >/dev/null 2>&1; then
    log "Creando entorno PyMOL con conda..."
    conda create -y -p "$TOOLS_DIR/pymol_env" -c conda-forge python=3.10 pymol-open-source
    "$PYMOL_PYTHON" -c "import pymol2; print('PyMOL/pymol2 ready')"
  else
    cat <<'EOF'

No se encontró conda ni micromamba, así que no se pudo crear el entorno de PyMOL.
Instala conda o micromamba y vuelve a ejecutar este script.
EOF
    exit 1
  fi
fi

log "Instalación completada."
echo "  API: http://127.0.0.1:8010"
echo "  Docs: http://127.0.0.1:8010/docs"
echo "  Para iniciar el servidor: ./start_server.ps1 o PYMOL_API_PORT=8010 ./.venv/bin/python -m uvicorn app:app"

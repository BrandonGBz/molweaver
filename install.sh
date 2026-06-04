#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$ROOT_DIR/tools"
VENV_DIR="$ROOT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
PYMOL_PREFIX="$TOOLS_DIR/pymol_env"
PYMOL_PYTHON="$PYMOL_PREFIX/bin/python"
MAMBA_ROOT="$TOOLS_DIR/mamba_root"
MICROMAMBA_DIR="$TOOLS_DIR/micromamba"
MICROMAMBA_BIN="$MICROMAMBA_DIR/bin/micromamba"
START=false
PORT="8010"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START=true
      shift
      ;;
    --port)
      PORT="${2:-}"
      if [[ -z "$PORT" ]]; then
        echo "--port requiere un valor." >&2
        exit 1
      fi
      shift 2
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./install.sh [--start] [--port N]
EOF
      exit 0
      ;;
    *)
      echo "Argumento no reconocido: $1" >&2
      exit 1
      ;;
  esac
done

log() {
  printf '\n%s\n' "$1"
}

python3_version_ok() {
  if ! command -v python3 >/dev/null 2>&1; then
    return 1
  fi
  python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null
}

download_local_micromamba() {
  local system_name arch url archive
  system_name="$(uname -s)"
  arch="$(uname -m)"

  case "$system_name:$arch" in
    Linux:x86_64)
      url="https://micro.mamba.pm/api/micromamba/linux-64/latest"
      ;;
    Linux:aarch64|Linux:arm64)
      url="https://micro.mamba.pm/api/micromamba/linux-aarch64/latest"
      ;;
    Darwin:x86_64)
      url="https://micro.mamba.pm/api/micromamba/osx-64/latest"
      ;;
    Darwin:arm64)
      url="https://micro.mamba.pm/api/micromamba/osx-arm64/latest"
      ;;
    *)
      echo "Plataforma no soportada para descarga automatica de micromamba: $system_name $arch" >&2
      exit 1
      ;;
  esac

  mkdir -p "$MICROMAMBA_DIR"
  archive="$MICROMAMBA_DIR/micromamba.tar.bz2"

  if [ ! -x "$MICROMAMBA_BIN" ]; then
    log "Descargando micromamba local..."
    curl -fsSL "$url" -o "$archive"
    tar -xjf "$archive" -C "$MICROMAMBA_DIR"
    chmod +x "$MICROMAMBA_BIN"
  fi
}

detect_package_manager() {
  if command -v micromamba >/dev/null 2>&1; then
    echo "micromamba"
    return
  fi
  if command -v mamba >/dev/null 2>&1; then
    echo "mamba"
    return
  fi
  if command -v conda >/dev/null 2>&1; then
    echo "conda"
    return
  fi
  echo "local-micromamba"
}

ensure_pymol_env() {
  if [ -x "$PYMOL_PYTHON" ] && "$PYMOL_PYTHON" -c "import pymol2; print('PyMOL/pymol2 ready')" >/dev/null 2>&1; then
    log "Entorno PyMOL existente verificado."
    return
  fi

  local manager
  manager="$(detect_package_manager)"

  case "$manager" in
    micromamba)
      log "Creando entorno PyMOL con micromamba..."
      micromamba create -y -r "$MAMBA_ROOT" -p "$PYMOL_PREFIX" -c conda-forge python=3.10 pymol-open-source
      ;;
    mamba)
      log "Creando entorno PyMOL con mamba..."
      mamba create -y -p "$PYMOL_PREFIX" -c conda-forge python=3.10 pymol-open-source
      ;;
    conda)
      log "Creando entorno PyMOL con conda..."
      conda create -y -p "$PYMOL_PREFIX" -c conda-forge python=3.10 pymol-open-source
      ;;
    local-micromamba)
      download_local_micromamba
      log "Creando entorno PyMOL con micromamba local..."
      "$MICROMAMBA_BIN" create -y -r "$MAMBA_ROOT" -p "$PYMOL_PREFIX" -c conda-forge python=3.10 pymol-open-source
      ;;
  esac

  if [ ! -x "$PYMOL_PYTHON" ]; then
    echo "No se pudo encontrar $PYMOL_PYTHON despues de crear el entorno de PyMOL." >&2
    exit 1
  fi

  "$PYMOL_PYTHON" -c "import pymol2; print('PyMOL/pymol2 ready')"
}

ensure_venv() {
  local python_bin="python3"

  if ! python3_version_ok; then
    log "Python 3.10+ no encontrado en el sistema. Usando el Python del entorno PyMOL."
    ensure_pymol_env
    python_bin="$PYMOL_PYTHON"
  fi

  if [ ! -x "$VENV_PYTHON" ]; then
    log "Creando entorno virtual .venv..."
    "$python_bin" -m venv "$VENV_DIR"
  fi

  log "Actualizando pip e instalando dependencias..."
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r "$ROOT_DIR/requirements.txt"
}

ensure_env_file() {
  if [ ! -f "$ROOT_DIR/.env" ] && [ -f "$ROOT_DIR/.env.example" ]; then
    log "Creando .env desde .env.example..."
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  fi
}

ensure_venv
ensure_env_file
ensure_pymol_env

log "Instalacion completada."
echo "  API: http://127.0.0.1:${PORT}"
echo "  Docs: http://127.0.0.1:${PORT}/docs"
echo "  Para iniciar el servidor manualmente: ./start_server.sh"

if [ "$START" = true ]; then
  log "Iniciando servidor..."
  PYMOL_API_PORT="$PORT" exec "$ROOT_DIR/start_server.sh"
fi

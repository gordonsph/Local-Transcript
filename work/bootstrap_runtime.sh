#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
WHISPER_REPO="${WHISPER_REPO:-https://github.com/ggml-org/whisper.cpp.git}"
WHISPER_COMMIT="${WHISPER_COMMIT:-0d14756929dc9f21ddccf6102bb783397b7a8f1b}"
WHISPER_DIR="$ROOT/work/whisper.cpp"
VENV_DIR="$ROOT/work/transcribe-venv"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

cpu_count() {
  if command -v sysctl >/dev/null 2>&1; then
    sysctl -n hw.ncpu
  else
    echo 4
  fi
}

require_command git
require_command cmake
require_command curl
require_command "$PYTHON_BIN"

mkdir -p "$ROOT/work"

if [ ! -d "$WHISPER_DIR/.git" ]; then
  git clone "$WHISPER_REPO" "$WHISPER_DIR"
fi

git -C "$WHISPER_DIR" fetch --tags origin
git -C "$WHISPER_DIR" checkout "$WHISPER_COMMIT"

cmake -S "$WHISPER_DIR" -B "$WHISPER_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_METAL=ON
cmake --build "$WHISPER_DIR/build" --config Release -j "$(cpu_count)"

"$WHISPER_DIR/models/download-ggml-model.sh" large-v3 "$WHISPER_DIR/models"
"$WHISPER_DIR/models/download-vad-model.sh" silero-v6.2.0 "$WHISPER_DIR/models"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$ROOT/work/transcribe_app/requirements.txt"

echo "Runtime ready."
echo "Start with:"
echo "  $VENV_DIR/bin/python $ROOT/work/transcribe_app/app.py"
echo "Then open:"
echo "  http://127.0.0.1:5057/"

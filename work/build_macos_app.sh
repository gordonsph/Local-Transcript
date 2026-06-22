#!/usr/bin/env bash
# Build the Local Transcript .app bundle with py2app.
#
# Produces work/transcribe_app/dist/Local Transcript.app. The bundle contains the
# Python runtime, Flask backend, dependencies, AND the relocated whisper-cli
# engine (Contents/Resources/whisper-runtime/). Only the large-v3 model is NOT
# bundled — it is downloaded on first run into Application Support (see app.py).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/transcribe_app"
PYTHON="$SCRIPT_DIR/transcribe-venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Python venv not found at $PYTHON. Run work/bootstrap_runtime.sh first." >&2
  exit 1
fi

# Ensure the build tool is present (py2app is a build-only dep, kept out of the
# runtime requirements). Idempotent; makes a clean checkout build without relying
# on setup_requires' deprecated network fetch.
"$PYTHON" -m pip install -r "$APP_DIR/requirements-build.txt"

# Stage the relocated, self-contained whisper-cli runtime so py2app bundles it.
"$SCRIPT_DIR/relocate_whisper.sh"

cd "$APP_DIR"
rm -rf build dist
"$PYTHON" setup.py py2app

# Insurance: py2app copies whisper-runtime via data_files. Make sure the engine
# kept its executable bit and a valid ad-hoc signature; re-sign inside-out if not.
RT="$APP_DIR/dist/Local Transcript.app/Contents/Resources/whisper-runtime"
if [ -d "$RT" ]; then
  chmod +x "$RT/whisper-cli"
  if ! codesign --verify "$RT/whisper-cli" >/dev/null 2>&1; then
    for dylib in "$RT"/*.dylib; do codesign --force --sign - "$dylib"; done
    codesign --force --sign - "$RT/whisper-cli"
  fi
fi

echo
echo "Built: $APP_DIR/dist/Local Transcript.app"
echo "Run it with: open \"$APP_DIR/dist/Local Transcript.app\""

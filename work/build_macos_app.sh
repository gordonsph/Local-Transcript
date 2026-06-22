#!/usr/bin/env bash
# Build the Local Transcript .app bundle with py2app.
#
# Produces work/transcribe_app/dist/Local Transcript.app. The bundle contains
# the Python runtime, Flask backend, and dependencies, but NOT the large-v3
# model or whisper-cli — those are resolved at runtime from
# ~/Library/Application Support/LocalTranscript (see app.py).
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

cd "$APP_DIR"
rm -rf build dist
"$PYTHON" setup.py py2app

echo
echo "Built: $APP_DIR/dist/Local Transcript.app"
echo "Run it with: open \"$APP_DIR/dist/Local Transcript.app\""

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${LOCAL_TRANSCRIPT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

cd "$ROOT"
exec "$ROOT/work/transcribe-venv/bin/python" "$ROOT/work/transcribe_app/app.py"

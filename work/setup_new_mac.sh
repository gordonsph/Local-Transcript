#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
URL="http://127.0.0.1:5057/"

ensure_optional_dependency() {
  local command_name="$1"
  local brew_package="$2"

  if command -v "$command_name" >/dev/null 2>&1; then
    return 0
  fi

  if command -v brew >/dev/null 2>&1; then
    echo "Installing $brew_package with Homebrew..."
    brew install "$brew_package"
    return 0
  fi

  echo "Missing required command: $command_name" >&2
  echo "Install Homebrew or install $brew_package manually, then rerun this script." >&2
  exit 1
}

ensure_optional_dependency git git
ensure_optional_dependency cmake cmake
ensure_optional_dependency curl curl

if ! command -v python3 >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing Python with Homebrew..."
    brew install python
  else
    echo "Missing required command: python3" >&2
    echo "Install Python 3, then rerun this script." >&2
    exit 1
  fi
fi

"$ROOT/work/bootstrap_runtime.sh"
"$ROOT/work/install_persistent_local_transcript.sh"

echo "Waiting for Local Transcript to respond..."
for _ in $(seq 1 30); do
  if curl --max-time 2 -fsS "$URL/api/health" >/dev/null 2>&1; then
    echo "Local Transcript is ready."
    echo "Open $URL"
    exit 0
  fi
  sleep 1
done

echo "The service was installed, but did not respond within 30 seconds." >&2
echo "Check logs under:" >&2
echo "  $HOME/Library/Application Support/LocalTranscript/work/transcribe_app/logs/" >&2
exit 1

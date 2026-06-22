#!/usr/bin/env bash
set -euo pipefail

# Provision the runtime that the native Local Transcript.app needs, WITHOUT
# installing the always-on LaunchAgent service. The .app bundles its own Python
# and app code, so it only needs the whisper.cpp binary, the models, and a
# writable outputs tree under Application Support (the data ROOT the frozen app
# defaults to). Run this once per Mac after building the .app:
#
#   work/provision_app_runtime.sh
#
# Use install_persistent_local_transcript.sh instead if you want the legacy
# always-on background service rather than the native app.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="${SOURCE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
INSTALL_ROOT="$HOME/Library/Application Support/LocalTranscript"

WHISPER_CLI="work/whisper.cpp/build/bin/whisper-cli"
MODEL="work/whisper.cpp/models/ggml-large-v3.bin"
VAD_MODEL="work/whisper.cpp/models/ggml-silero-v6.2.0.bin"

# Build the source runtime first if the binary or models are missing.
if [ ! -x "$SOURCE_ROOT/$WHISPER_CLI" ] ||
   [ ! -f "$SOURCE_ROOT/$MODEL" ] ||
   [ ! -f "$SOURCE_ROOT/$VAD_MODEL" ]; then
  echo "Source runtime is incomplete. Bootstrapping it first..."
  "$SOURCE_ROOT/work/bootstrap_runtime.sh"
fi

mkdir -p "$INSTALL_ROOT/work/whisper.cpp/build"
mkdir -p "$INSTALL_ROOT/work/whisper.cpp/models"
mkdir -p "$INSTALL_ROOT/outputs/transcribe_app/results"
mkdir -p "$INSTALL_ROOT/outputs/transcribe_app/jobs"

# Copy only what the app reads at runtime: the compiled binary (with its Metal
# shaders) and the model files. Not the venv (the .app has its own) and not the
# app code (it is inside the bundle).
rsync -a --delete "$SOURCE_ROOT/work/whisper.cpp/build/" "$INSTALL_ROOT/work/whisper.cpp/build/"
rsync -a --delete "$SOURCE_ROOT/work/whisper.cpp/models/" "$INSTALL_ROOT/work/whisper.cpp/models/"

echo "Provisioned native-app runtime at:"
echo "  $INSTALL_ROOT"
echo "Local Transcript.app is now ready to launch by double-click."

#!/usr/bin/env bash
# One-command release: build the .app, ad-hoc sign it, and package the DMG.
#
#   work/release.sh
#
# Produces work/transcribe_app/dist/Local Transcript.dmg, ready to share.
# (The 2.9 GB model is not bundled — recipients download it on first launch.)
# Runs the three steps in order and stops on the first failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 1/3  Building Local Transcript.app …"
"$SCRIPT_DIR/build_macos_app.sh"

echo "==> 2/3  Ad-hoc signing the bundle …"
"$SCRIPT_DIR/sign_macos_app.sh"

echo "==> 3/3  Packaging the DMG …"
"$SCRIPT_DIR/build_dmg.sh"

echo
echo "Release complete:"
echo "  $SCRIPT_DIR/transcribe_app/dist/Local Transcript.dmg"

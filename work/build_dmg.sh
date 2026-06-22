#!/usr/bin/env bash
# Package the signed Local Transcript.app into a distributable DMG.
#
# The DMG contains the app, an /Applications shortcut (so users drag it there —
# required: running from the image/Downloads triggers App Translocation, which
# blocks the engine), a "Read Me First" with the Gatekeeper approval steps, and
# the third-party license notices.
#
# Run after build_macos_app.sh + sign_macos_app.sh:
#   work/build_dmg.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP="$SCRIPT_DIR/transcribe_app/dist/Local Transcript.app"
OUT="$SCRIPT_DIR/transcribe_app/dist/Local Transcript.dmg"
VOLNAME="Local Transcript"

if [ ! -d "$APP" ]; then
  echo "Bundle not found at $APP. Run work/build_macos_app.sh (and sign_macos_app.sh) first." >&2
  exit 1
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Layout the DMG contents.
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cp "$ROOT/NOTICES.md" "$STAGE/Licenses.txt"

# Plain-text "Read Me First" derived from the install guide (DMGs don't render md).
{
  echo "Local Transcript — read me first"
  echo "================================="
  echo
  echo "1. Drag Local Transcript onto the Applications shortcut in this window."
  echo "   (Launch it from Applications, NOT from this disk image or Downloads.)"
  echo
  echo "2. First launch: macOS will say it cannot verify the app. Click Done, then"
  echo "   open  System Settings > Privacy & Security,  scroll down, and click"
  echo "   'Open Anyway' next to Local Transcript. Confirm with Open. (One time.)"
  echo
  echo "3. On first open, click 'Download model' to fetch the one-time 2.9 GB"
  echo "   Whisper large-v3 model. After that, everything runs offline on your Mac."
  echo
  echo "Requires an Apple Silicon Mac (M1 or later), macOS 11+. Audio never leaves"
  echo "your device. Full instructions: docs/INSTALL.md. Licenses: Licenses.txt."
} > "$STAGE/Read Me First.txt"

rm -f "$OUT"
echo "Building DMG…"
hdiutil create \
  -volname "$VOLNAME" \
  -srcfolder "$STAGE" \
  -fs HFS+ \
  -format UDZO \
  -ov \
  "$OUT" >/dev/null

echo "Built: $OUT"
echo "Size:  $(du -h "$OUT" | cut -f1)"

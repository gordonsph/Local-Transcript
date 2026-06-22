#!/usr/bin/env bash
# Ad-hoc sign the whole Local Transcript.app, inside-out, and verify.
#
# We distribute FREE / non-notarized (no Apple Developer account), so this is
# an ad-hoc signature (codesign -s -). On Apple Silicon every Mach-O must carry
# at least an ad-hoc signature to run; py2app signs the bundle but we re-sign
# every nested binary inside-out so a consistent, valid signature is guaranteed,
# then gate on codesign --verify --deep --strict.
#
# Recipients still see Gatekeeper's "unidentified developer" prompt on first
# launch and approve via System Settings → Privacy & Security (see the DMG docs).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/transcribe_app/dist/Local Transcript.app"

if [ ! -d "$APP" ]; then
  echo "Bundle not found at $APP. Run work/build_macos_app.sh first." >&2
  exit 1
fi

echo "Signing nested Mach-O (inside-out)…"
# Sign every Mach-O file deepest-first: dylibs/.so, then frameworks, then the app.
# Identify Mach-O by magic via `file`, sort by path depth descending.
find "$APP" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -u+x \) -print0 \
  | while IFS= read -r -d '' f; do
      if file -b "$f" | grep -q "Mach-O"; then printf '%s\t%s\n' "$(echo "$f" | tr -cd '/' | wc -c)" "$f"; fi
    done \
  | sort -rn -k1 \
  | cut -f2- \
  | while IFS= read -r f; do
      codesign --force --sign - --timestamp=none "$f" 2>/dev/null || codesign --force --sign - "$f"
    done

# Sign nested bundles (frameworks/.app) then the top bundle last.
find "$APP" -type d \( -name "*.framework" -o -name "*.app" \) ! -path "$APP" -print0 \
  | while IFS= read -r -d '' b; do codesign --force --deep --sign - "$b"; done
codesign --force --deep --sign - "$APP"

echo
echo "Verifying…"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "Signature: $(codesign -dvv "$APP" 2>&1 | grep -E 'Signature|Identifier' | tr '\n' ' ')"
echo
echo "Signed (ad-hoc) + verified: $APP"

#!/usr/bin/env bash
# Produce a portable, self-contained whisper-cli runtime for bundling inside the
# .app. The CMake build links whisper-cli to its dylibs via @rpath but bakes in
# absolute dev-machine LC_RPATH entries, so the binary is not relocatable as-is.
#
# This collects whisper-cli + its 6 dylibs into ONE directory, strips the
# absolute rpaths, points the binary at @executable_path and each dylib at
# @loader_path (every install-name and inter-dependency is already @rpath/libX,
# so co-location + those rpaths resolves the whole graph), then re-signs ad-hoc
# inside-out (install_name_tool invalidates signatures).
#
# Note: this script only manages LC_RPATH. During bundling, py2app rewrites each
# dylib's LC_ID_DYLIB to an @executable_path-relative path and re-signs — that is
# expected and harmless, because the binary loads its siblings via @rpath/libX
# (resolved by @executable_path), so the install IDs are not load-critical.
#
# Output: work/transcribe_app/whisper-runtime/{whisper-cli, lib*.dylib}
# Idempotent. Run before building the .app (build_macos_app.sh calls it).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD="$ROOT/work/whisper.cpp/build"
DEST="$ROOT/work/transcribe_app/whisper-runtime"

# The exact files whisper-cli loads (by their @rpath soname), and where the
# CMake build places each (symlinks resolve to the real versioned dylib).
BIN_SRC="$BUILD/bin/whisper-cli"
declare -a DYLIBS=(
  "libwhisper.1.dylib:$BUILD/src/libwhisper.1.dylib"
  "libggml.0.dylib:$BUILD/ggml/src/libggml.0.dylib"
  "libggml-base.0.dylib:$BUILD/ggml/src/libggml-base.0.dylib"
  "libggml-cpu.0.dylib:$BUILD/ggml/src/libggml-cpu.0.dylib"
  "libggml-blas.0.dylib:$BUILD/ggml/src/ggml-blas/libggml-blas.0.dylib"
  "libggml-metal.0.dylib:$BUILD/ggml/src/ggml-metal/libggml-metal.0.dylib"
)

if [ ! -x "$BIN_SRC" ]; then
  echo "whisper-cli not found at $BIN_SRC. Run work/bootstrap_runtime.sh first." >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"

# Copy real file content under the soname filename (cp follows the symlinks).
cp "$BIN_SRC" "$DEST/whisper-cli"
for entry in "${DYLIBS[@]}"; do
  name="${entry%%:*}"; src="${entry#*:}"
  if [ ! -f "$src" ]; then echo "missing dylib: $src" >&2; exit 1; fi
  cp "$src" "$DEST/$name"
done
chmod u+w "$DEST"/*

# Strip every absolute LC_RPATH from a Mach-O, then add the given portable one.
strip_and_add_rpath() {
  local file="$1" portable="$2"
  # Delete any existing absolute (/...) rpath; ignore failures for ones already gone.
  while IFS= read -r rp; do
    case "$rp" in
      /*) install_name_tool -delete_rpath "$rp" "$file" 2>/dev/null || true ;;
    esac
  done < <(otool -l "$file" | awk '/LC_RPATH/{f=1} f&&/path /{print $2; f=0}')
  # Add the portable rpath if not already present.
  if ! otool -l "$file" | awk '/LC_RPATH/{f=1} f&&/path /{print $2; f=0}' | grep -qx "$portable"; then
    install_name_tool -add_rpath "$portable" "$file"
  fi
}

strip_and_add_rpath "$DEST/whisper-cli" "@executable_path"
for entry in "${DYLIBS[@]}"; do
  name="${entry%%:*}"
  strip_and_add_rpath "$DEST/$name" "@loader_path"
done

# Re-sign ad-hoc, inside-out: dylibs first, then the executable.
for entry in "${DYLIBS[@]}"; do
  name="${entry%%:*}"
  codesign --force --sign - "$DEST/$name"
done
codesign --force --sign - "$DEST/whisper-cli"

echo "Relocated whisper runtime -> $DEST"
ls -1 "$DEST"

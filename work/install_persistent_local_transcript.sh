#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="${SOURCE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
INSTALL_ROOT="$HOME/Library/Application Support/LocalTranscript"
LABEL="com.siuph.local-transcript"
PLIST_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(id -u)"

if [ ! -x "$SOURCE_ROOT/work/transcribe-venv/bin/python" ] ||
   [ ! -x "$SOURCE_ROOT/work/whisper.cpp/build/bin/whisper-cli" ] ||
   [ ! -f "$SOURCE_ROOT/work/whisper.cpp/models/ggml-large-v3.bin" ] ||
   [ ! -f "$SOURCE_ROOT/work/whisper.cpp/models/ggml-silero-v6.2.0.bin" ]; then
  echo "Runtime is incomplete. Bootstrapping local runtime first..."
  "$SOURCE_ROOT/work/bootstrap_runtime.sh"
fi

mkdir -p "$INSTALL_ROOT/work"
mkdir -p "$INSTALL_ROOT/outputs/transcribe_app/results"
mkdir -p "$INSTALL_ROOT/outputs/transcribe_app/jobs"
mkdir -p "$INSTALL_ROOT/work/transcribe_app/logs"
mkdir -p "$HOME/Library/LaunchAgents"

launchctl bootout "gui/$UID_VALUE" "$PLIST_TARGET" 2>/dev/null || true
pkill -f "$INSTALL_ROOT/work/transcribe_app/app.py" 2>/dev/null || true
pkill -f "$SOURCE_ROOT/work/transcribe_app/app.py" 2>/dev/null || true

rsync -a --delete "$SOURCE_ROOT/work/transcribe_app/" "$INSTALL_ROOT/work/transcribe_app/"
rsync -a --delete "$SOURCE_ROOT/work/transcribe-venv/" "$INSTALL_ROOT/work/transcribe-venv/"
rsync -a --delete "$SOURCE_ROOT/work/whisper.cpp/build/" "$INSTALL_ROOT/work/whisper.cpp/build/"
rsync -a --delete "$SOURCE_ROOT/work/whisper.cpp/models/" "$INSTALL_ROOT/work/whisper.cpp/models/"
rsync -a "$SOURCE_ROOT/work/start_transcribe_app.sh" "$INSTALL_ROOT/work/start_transcribe_app.sh"
chmod +x "$INSTALL_ROOT/work/start_transcribe_app.sh"

cat > "$PLIST_TARGET" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$INSTALL_ROOT/work/start_transcribe_app.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$INSTALL_ROOT</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>LOCAL_TRANSCRIPT_ROOT</key>
    <string>$INSTALL_ROOT</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>$INSTALL_ROOT/work/transcribe_app/logs/launchd.out.log</string>

  <key>StandardErrorPath</key>
  <string>$INSTALL_ROOT/work/transcribe_app/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

chmod 644 "$PLIST_TARGET"

launchctl bootstrap "gui/$UID_VALUE" "$PLIST_TARGET"
launchctl enable "gui/$UID_VALUE/$LABEL"
launchctl kickstart -k "gui/$UID_VALUE/$LABEL"

echo "Installed $LABEL at $INSTALL_ROOT"
echo "Open http://127.0.0.1:5057/"

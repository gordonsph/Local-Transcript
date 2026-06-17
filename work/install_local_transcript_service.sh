#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${LOCAL_TRANSCRIPT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LABEL="com.siuph.local-transcript"
PLIST_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_VALUE="$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT/work/transcribe_app/logs"

launchctl bootout "gui/$UID_VALUE" "$PLIST_TARGET" 2>/dev/null || true
pkill -f "$ROOT/work/transcribe_app/app.py" 2>/dev/null || true

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
    <string>$ROOT/work/start_transcribe_app.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$ROOT</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>LOCAL_TRANSCRIPT_ROOT</key>
    <string>$ROOT</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>$ROOT/work/transcribe_app/logs/launchd.out.log</string>

  <key>StandardErrorPath</key>
  <string>$ROOT/work/transcribe_app/logs/launchd.err.log</string>
</dict>
</plist>
PLIST
chmod 644 "$PLIST_TARGET"

launchctl bootstrap "gui/$UID_VALUE" "$PLIST_TARGET"
launchctl enable "gui/$UID_VALUE/$LABEL"
launchctl kickstart -k "gui/$UID_VALUE/$LABEL"

echo "Installed $LABEL"
echo "Open http://127.0.0.1:5057/"

# Persistent Local Hosting

Use this skill when making the local web app available from a stable bookmark URL.

## User Goal

The user wants to bookmark:

```text
http://127.0.0.1:5057/
```

and open it later without manually restarting Codex.

## Important Constraint

This cannot be purely static hosting because transcription requires a backend process.

The right local shape is:

- Flask backend as a user LaunchAgent.
- Stable localhost port.
- Local files only.

## Failed Attempt

Files added:

```text
work/com.siuph.local-transcript.plist
work/install_local_transcript_service.sh
```

Problem observed:

```text
Operation not permitted
```

when launchd tried to execute the app from the Documents/Codex workspace.

Likely cause:

- macOS privacy restrictions around Documents folder access for background LaunchAgents.

## Recommended Fix

Install the runtime into:

```text
~/Library/Application Support/LocalTranscript
```

Then point LaunchAgent `ProgramArguments` and `WorkingDirectory` there.

Keep user-facing transcript outputs configurable and separate from the installed app runtime.

## Current Installed Shape

Use:

```sh
work/install_persistent_local_transcript.sh
```

This copies the runtime into:

```text
~/Library/Application Support/LocalTranscript
```

and writes:

```text
~/Library/LaunchAgents/com.siuph.local-transcript.plist
```

The LaunchAgent sets:

```text
LOCAL_TRANSCRIPT_ROOT=/Users/siuph/Library/Application Support/LocalTranscript
```

The app should report installed paths from `/api/health`, not paths under the Codex workspace.

## Verification

After installing LaunchAgent:

```sh
launchctl print gui/$(id -u)/com.siuph.local-transcript
curl http://127.0.0.1:5057/api/health
lsof -nP -iTCP:5057 -sTCP:LISTEN
```

The service should survive closing Codex and should start at user login.

Expected health shape:

```json
{
  "ready": true,
  "model": "/Users/siuph/Library/Application Support/LocalTranscript/work/whisper.cpp/models/ggml-large-v3.bin",
  "vad": true
}
```

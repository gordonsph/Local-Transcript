# Audio Ingest And Output Formats

Use this skill when changing upload handling, audio conversion, or transcript output formats.

## Upload Handling

The frontend accepts common audio and video containers. The backend should not assume `whisper.cpp` can read every uploaded container directly.

Current behavior:

1. Save original upload inside the job folder.
2. Decode with PyAV.
3. Convert to 16 kHz mono WAV.
4. Pass the prepared WAV to `whisper.cpp`.

Reason:

- `whisper.cpp` supports common audio formats such as WAV, MP3, FLAC, and OGG.
- The user's original file was an M4A/MP4-style container with an unusual `.m4a.mpeg` name.
- PyAV handled that file reliably.

## Output Generation

The app asks `whisper.cpp` for full JSON output, then generates the user-facing files itself.

Reason:

- It gives consistent Hong Kong Traditional normalization.
- It keeps formatting predictable across Markdown, SRT, VTT, CSV, JSON, and TXT.
- It avoids relying on several native output formats that may differ subtly.

## Keep Outputs Lean

When output format is `All formats`, the zip should contain transcript files only.

Do not include:

- Original upload.
- Prepared WAV.
- Raw `whisper.cpp` JSON unless intentionally exposed.
- Temporary logs.

## Format Notes

Markdown:

- Timestamped readable transcript.

SRT and VTT:

- Subtitle-compatible formats.

CSV:

- Columns: `start`, `end`, `text`.

JSON:

- Structured segment list with numeric and label timestamps.

TXT:

- Plain text only, one segment per line.


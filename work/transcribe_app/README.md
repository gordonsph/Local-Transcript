# Local Transcript App

Lightweight local frontend for `whisper.cpp` with the full `large-v3` model.

## Stack

- Backend: Flask
- Frontend: vanilla HTML, CSS, JavaScript
- Speech model: `whisper.cpp` `large-v3`
- Audio preparation: PyAV, 16 kHz mono WAV
- Storage: local filesystem only
- Design checks: UI/UX Pro Max and Impeccable skills installed at the project root

## Day-1 Settings

User-facing:

- Source mode: file upload, direct media URL, or live browser recording
- Language
- Output format
- Result folder
- Terminology hints
- Pause, continue, terminate while transcribing
- Progress, ETA, elapsed time, and system usage while running

Fixed:

- Full `large-v3` model
- Highest accuracy decoding: beam size 5, best-of 5
- Transcribe task, not translate
- Segment timestamps
- Conservative VAD when the VAD model is installed
- Hong Kong Traditional normalization for Cantonese/Chinese output

## Start

```sh
cd /path/to/local-transcript
work/transcribe-venv/bin/python work/transcribe_app/app.py
```

Open:

```text
http://127.0.0.1:5057
```

## Install As Mac Web App

Open `http://127.0.0.1:5057/`, then use the app's **Install app** button for current macOS browser steps.

Safari:

```text
File or Share > Add to Dock > Add
```

Chrome:

```text
More > Cast, save, and share > Install page as app
```

Persistent hosting uses a macOS LaunchAgent. See:

```text
skills/persistent-local-hosting/SKILL.md
```

For frontend design and audit workflow, see:

```text
skills/frontend-lightweight-design/SKILL.md
skills/ui-design-audit-workflow/SKILL.md
```

Root design context:

```text
PRODUCT.md
DESIGN.md
.impeccable/design.json
```

Generated transcripts are saved under:

```text
outputs/transcribe_app/results/<job-id>/
```

Temporary job files are saved under:

```text
outputs/transcribe_app/jobs/<job-id>/
```

Original source files, URL downloads, and live recording audio are saved under:

```text
outputs/transcribe_app/jobs/<job-id>/source/
```

## Persistent Install

Refresh the always-on local service after app changes:

```sh
work/install_persistent_local_transcript.sh
```

Verify:

```sh
curl --max-time 5 -s http://127.0.0.1:5057/api/health
```

The response should point to `/Users/siuph/Library/Application Support/LocalTranscript/`.

## Frontend Checks

Run after UI changes:

```sh
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
npx --yes impeccable@2.3.2 detect --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

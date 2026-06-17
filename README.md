# Local Transcript

Lightweight local web app for high-accuracy audio transcription on macOS using `whisper.cpp`, Metal, and the full `large-v3` model.

The app is intentionally small:

- Flask backend
- Vanilla HTML, CSS, and JavaScript frontend
- Local filesystem storage only
- Fixed high-accuracy transcription settings
- Runtime controls for pause, continue, terminate, progress, ETA, and system pressure

## What Is Tracked

This repository tracks the app source, install scripts, design context, and future-agent runbooks.

Large/generated/private artifacts are intentionally excluded:

- `work/whisper.cpp/`
- `work/transcribe-venv/`
- `outputs/`
- downloaded model binaries
- generated transcripts
- uploaded or sample audio
- local logs and Python cache files

See `CONTEXT.md` for the full development history and decision log.

## App Source

Main app files:

```text
work/transcribe_app/app.py
work/transcribe_app/templates/index.html
work/transcribe_app/static/styles.css
work/transcribe_app/static/app.js
work/transcribe_app/requirements.txt
```

Local workflow skills:

```text
work/transcribe_app/skills/*/SKILL.md
```

Design context:

```text
PRODUCT.md
DESIGN.md
.impeccable/design.json
.impeccable/critique/
```

## Runtime Dependency Layout

The app expects this local runtime layout:

```text
work/transcribe-venv/
work/whisper.cpp/build/bin/whisper-cli
work/whisper.cpp/models/ggml-large-v3.bin
work/whisper.cpp/models/ggml-silero-v6.2.0.bin
```

The current Mac already has those local assets installed. A fresh clone needs to recreate them before running the app.

On a fresh Mac, run the full setup script:

```sh
work/setup_new_mac.sh
```

That recreates the runtime, installs the persistent LaunchAgent, and verifies:

```text
http://127.0.0.1:5057/
```

If you only want to recreate runtime dependencies without installing the always-on service, run:

```sh
work/bootstrap_runtime.sh
```

The script creates `work/transcribe-venv/`, clones the pinned `whisper.cpp` revision, builds with Metal enabled, and downloads the full `large-v3` model plus Silero VAD model.

## Local Start

```sh
python3 -m venv work/transcribe-venv
work/transcribe-venv/bin/python -m pip install -r work/transcribe_app/requirements.txt
work/transcribe-venv/bin/python work/transcribe_app/app.py
```

Open:

```text
http://127.0.0.1:5057/
```

## Persistent macOS Service

After the runtime dependencies exist, install or refresh the always-on local service:

```sh
work/install_persistent_local_transcript.sh
```

Verify:

```sh
curl --max-time 5 -s http://127.0.0.1:5057/api/health
```

## Documentation

Start here for future maintenance:

```text
AGENTS.md
CONTEXT.md
work/transcribe_app/README.md
work/transcribe_app/skills/transcribe-app-maintenance/SKILL.md
work/transcribe_app/skills/transcription-model-upgrade/SKILL.md
work/transcribe_app/skills/mac-whisper-cpp-metal/SKILL.md
work/transcribe_app/skills/ui-design-audit-workflow/SKILL.md
```

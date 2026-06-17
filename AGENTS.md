# Agent Runbook

This repository is a local macOS transcription app. Future agents should preserve the lightweight stack and make the project portable across Macs.

## Brand-New Mac Setup

After cloning this repository on a new Mac, run:

```sh
work/setup_new_mac.sh
```

That single script should:

1. Check for `git`, `cmake`, `curl`, and `python3`.
2. Install missing dependencies with Homebrew when Homebrew is available.
3. Run `work/bootstrap_runtime.sh`.
4. Clone the pinned `whisper.cpp` revision.
5. Build `whisper-cli` with Metal enabled.
6. Download `ggml-large-v3.bin`.
7. Download `ggml-silero-v6.2.0.bin`.
8. Create `work/transcribe-venv/`.
9. Install Python requirements.
10. Install the persistent macOS LaunchAgent.
11. Verify the app responds at `http://127.0.0.1:5057/`.

Expected stable app URL:

```text
http://127.0.0.1:5057/
```

Health endpoint:

```text
http://127.0.0.1:5057/api/health
```

The health endpoint is JSON, not the UI.

## Important Files

App:

```text
work/transcribe_app/app.py
work/transcribe_app/templates/index.html
work/transcribe_app/static/styles.css
work/transcribe_app/static/app.js
work/transcribe_app/requirements.txt
```

Setup:

```text
work/setup_new_mac.sh
work/bootstrap_runtime.sh
work/install_persistent_local_transcript.sh
work/runtime-manifest.md
```

Documentation:

```text
CONTEXT.md
README.md
PRODUCT.md
DESIGN.md
work/transcribe_app/README.md
work/transcribe_app/skills/*/SKILL.md
```

Design tooling:

```text
.agents/skills/impeccable/
.codex/skills/ui-ux-pro-max/
.impeccable/
```

## Do Not Commit

Do not commit generated, private, or heavyweight runtime artifacts:

```text
outputs/
work/transcribe-venv/
work/whisper.cpp/
work/transcribe_app/logs/
work/transcribe_app/sample_*.wav
work/transcribe_app/test_outputs/
```

Reason: GitHub rejects normal Git files over 100 MB. The full `large-v3` model is about 2.9 GB, so the portable approach is to recreate it with `work/bootstrap_runtime.sh`.

## Current Runtime Pin

See `work/runtime-manifest.md`.

Current pin:

```text
whisper.cpp: https://github.com/ggml-org/whisper.cpp.git
commit: 0d14756929dc9f21ddccf6102bb783397b7a8f1b
model: ggml-large-v3.bin
vad: ggml-silero-v6.2.0.bin
```

## Maintenance Rules

- Keep the stack bloatless: Flask plus vanilla HTML/CSS/JS.
- Keep quality fixed to the highest-accuracy day-1 config unless the user explicitly asks for speed tradeoffs.
- Keep the local service URL stable at `http://127.0.0.1:5057/`.
- Update `CONTEXT.md` after meaningful architecture, model, setup, or UX decisions.
- Update or add a focused `SKILL.md` when adding a repeatable workflow future agents need.
- After frontend changes, run the Impeccable detector documented in `work/transcribe_app/skills/ui-design-audit-workflow/SKILL.md`.

## Verification Commands

After code changes:

```sh
work/transcribe-venv/bin/python -m py_compile work/transcribe_app/app.py
```

After persistent install:

```sh
curl --max-time 5 -s http://127.0.0.1:5057/api/health
```

Expected health response should include:

```json
{"ready": true, "vad": true}
```

# Source Workspace And Live Recording

Use this skill when changing source selection, URL import, browser live recording, saved source audio, or the Voice Memos-inspired source UI.

## Product Shape

The app supports three source modes in one segmented workspace:

- `file`: save an uploaded audio/video file under the job's local `source/` folder.
- `url`: download a direct `http` or `https` media URL under the job's local `source/` folder.
- `live`: record microphone audio in the browser with `MediaRecorder`, upload the captured audio after Stop, save it under the job's local `source/` folder, then transcribe it.

Keep transcription after source persistence. Do not stream live transcription unless a future task explicitly designs it.

## UI Reference

Use the user's Voice Memos recording as the interaction reference:

- Compact source/library rail.
- Detail pane for the selected source.
- Live recording title, timer, waveform-like strip, and Record/Stop controls.
- Compact toolbar/action vocabulary.
- Transcript visibility as a toggle-like detail, not a separate route.

Preserve the existing Local Transcript visual system:

- Cool neutral workspace.
- White surfaces with 1px borders.
- One teal accent for current source, progress, and primary action.
- System font.
- No gradients, glass, decorative illustrations, nested cards, or oversized hero sections.

## Backend Rules

Every source must resolve to a local file before transcription starts:

```text
outputs/transcribe_app/jobs/<job-id>/source/<source-file>
```

Job JSON should include:

```text
source_type
source_name
source_path
source_url
saved_source_filename
```

The download route should be able to serve the saved source file separately from transcript outputs. Do not include source media in the all-formats transcript ZIP unless the user explicitly requests that behavior.

## Verification

After source-mode changes, run:

```sh
work/transcribe-venv/bin/python -m unittest tests.test_app_sources -v
work/transcribe-venv/bin/python -m py_compile work/transcribe_app/app.py
node --check work/transcribe_app/static/app.js
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

For manual QA, test:

- Switching File, URL, and Live source tabs.
- File source starts only after a file is chosen.
- URL source starts only after a URL is entered.
- Live source records, stops, enables Save & transcribe, and shows the saved source path after job creation.

# Local Transcribe App Maintenance

Use this skill when maintaining the lightweight local upload app for audio transcription.

## App Shape

The app lives here:

```text
work/transcribe_app/
```

Files:

```text
app.py                 Flask backend, job runner, output generation
templates/index.html   Single-page upload UI
static/styles.css      Plain CSS
static/app.js          Plain JavaScript polling and upload behavior
README.md              Local app runbook
```

Launcher:

```text
work/start_transcribe_app.sh
```

Outputs:

```text
outputs/transcribe_app/results/<job-id>/
```

Temporary job files:

```text
outputs/transcribe_app/jobs/<job-id>/
```

## Maintenance Rules

- Keep the stack small: Flask, vanilla HTML/CSS/JS, local files.
- Do not add a database unless there is a concrete need.
- Do not add a frontend framework for ordinary UI changes.
- Keep transcription jobs as folder-based artifacts with `status.json`.
- Keep generated downloads separate from temporary audio.
- Avoid bundling the original upload in the download zip.

## Day-1 UI Controls

Expose only:

- Language.
- Output format.
- Result folder.
- Terminology hints.

Do not expose:

- Model picker.
- Beam size.
- VAD threshold.
- Thread count.
- Word timestamps.
- Speaker labels.

Those settings are fixed so future use remains simple.

## Verification

After app changes:

1. Run Python syntax check:

```sh
work/transcribe-venv/bin/python -m py_compile work/transcribe_app/app.py
```

2. Start the app:

```sh
work/start_transcribe_app.sh
```

3. Open `http://127.0.0.1:5057`.
4. Upload a short audio sample.
5. Confirm the job reaches `Complete`.
6. Confirm the requested output files download.

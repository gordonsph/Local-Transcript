# Source Workspace And Live Recording Design

## Goal

Add the Buzz-inspired workflows to Local Transcript without changing the lightweight stack: File upload, URL import, Live Recording, and Advanced Settings all live in one segmented workspace.

## Approved Direction

Use Option A from the visual companion: one source selector at the top of the job form with three modes.

- **File:** existing upload/dropzone flow.
- **URL:** accepts a direct media URL, downloads it locally, then transcribes it through the existing pipeline.
- **Live:** records microphone audio in the browser, uploads the captured audio as a job source, stores that audio in the local job folder, then transcribes it.
- **Advanced Settings:** inline expandable area showing engine, model, task, language behavior, VAD, decoding quality, and optional AI translation/export placeholders. Keep transcription quality fixed to `whisper.cpp large-v3`.

## UI Design

The first screen remains the actual workflow, not a landing page. The form keeps the existing neutral product style from `DESIGN.md`: flat bordered panels, system font, one teal accent for active state and primary action, no gradients, no nested cards.

The selected source panel changes in place:

- File shows the dropzone.
- URL shows one `type="url"` field with validation.
- Live shows microphone permission state, record/stop controls, a recording timer, and a saved-audio note.

Shared controls stay below source selection: language, output format, result folder, terminology hints, and primary action. The primary action label changes by source mode: `Start transcript`, `Import URL`, or `Start recording`.

## Backend Design

Reuse the existing `run_transcription` pipeline by making every source resolve to a local source file first.

- File source saves the uploaded file in `outputs/transcribe_app/jobs/<job-id>/source/<filename>`.
- URL source downloads the remote media into the same source folder before starting transcription.
- Live source receives browser-recorded audio as a multipart upload, saves it into the same source folder, and transcribes it after recording stops.

Job status JSON gains source metadata:

- `source_type`
- `source_name`
- `source_path`
- `source_url`
- `saved_source_filename`

Download links keep focusing on transcript outputs, but the saved source path is visible in the job panel so the original live recording can be found locally.

## Constraints

- Keep Flask plus vanilla HTML/CSS/JS.
- Do not add a database or frontend build step.
- Do not expose low-level quality knobs that would reduce day-1 accuracy.
- Do not claim browser live transcription while recording; transcription starts after the saved recording is uploaded.
- Keep live source audio local and durable inside the job folder.

## Verification

- Unit tests for URL validation, safe URL filename derivation, and job/source serialization.
- Unit tests for live audio upload persistence using Flask's test client while stubbing the background transcription thread.
- `py_compile` for `app.py`.
- Impeccable detector on the changed frontend files.
- Manual browser verification at `http://127.0.0.1:5057/` if the local server is available.

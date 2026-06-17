# Transcription Workflow Context

## Goal

Build a lightweight local web workflow for future audio transcription:

- Upload audio through a simple frontend.
- Pick language and output format.
- Use `whisper.cpp` with the full `large-v3` model.
- Keep quality settings fixed to highest accuracy on day 1.
- Keep the stack small and local.

## Workspace

Root:

```text
/Users/siuph/Documents/Codex/2026-06-17/can-you-transcribe-a-cantonese-audio
```

Important paths:

```text
work/transcribe-venv/                         Local Python environment
work/whisper.cpp/                             Cloned whisper.cpp source and build
work/whisper.cpp/build/bin/whisper-cli        Built CLI
work/whisper.cpp/models/ggml-large-v3.bin     Full large-v3 model
work/whisper.cpp/models/ggml-silero-v6.2.0.bin VAD model
work/transcribe_app/                          Local upload web app
work/start_transcribe_app.sh                  App launcher
outputs/transcribe_app/jobs/                  Future app job outputs
outputs/cantonese_transcript_full.md          Earlier faster-whisper transcript
```

## What Happened

1. The original audio was `/Users/siuph/Downloads/16 Jun at 5-28 pm.m4a.mpeg`.
2. The first completed transcript used `faster-whisper` with `large-v3-turbo`, CPU int8, language `yue`, VAD, and Hong Kong Traditional normalization.
3. We then decided `large-v3-turbo` was not the absolute highest-accuracy path because it is a faster pruned variant of `large-v3`.
4. The new workflow was set up with `whisper.cpp` plus full `large-v3`.
5. `whisper.cpp` was cloned into `work/whisper.cpp`.
6. CMake was missing, so it was installed only into `work/transcribe-venv`, not globally.
7. `whisper.cpp` was built with Metal enabled:

```sh
work/transcribe-venv/bin/cmake -S work/whisper.cpp -B work/whisper.cpp/build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
work/transcribe-venv/bin/cmake --build work/whisper.cpp/build --config Release -j 8
```

8. Models were downloaded with the upstream scripts:

```sh
work/whisper.cpp/models/download-ggml-model.sh large-v3
work/whisper.cpp/models/download-vad-model.sh silero-v6.2.0
```

9. A Flask app was created at `work/transcribe_app/app.py` with vanilla HTML, CSS, and JS.
10. The app prepares uploads to 16 kHz mono WAV using PyAV, runs `whisper-cli`, parses JSON output, normalizes Chinese text to Hong Kong Traditional, and writes requested transcript formats.

## Day-1 Product Decisions

Expose in the interface:

- Language.
- Output format.
- Result folder.
- Optional terminology hints.

Keep fixed:

- Model: `large-v3`.
- Engine: `whisper.cpp`.
- Decoding: beam size `5`, best-of `5`.
- Task: transcribe, not translate.
- Timestamps: segment-level.
- VAD: enabled when the Silero VAD model is installed.
- Chinese normalization: `s2hk` for Cantonese/Chinese.
- Speaker labels: excluded because `whisper.cpp` does not provide reliable general diarization.

Operational UI:

- Show real percent complete from `whisper.cpp` when available.
- Show estimated percent while the model is loading or between progress callbacks.
- Show remaining time and elapsed time.
- Show pause, continue, and terminate controls.
- Show live process CPU/RAM, system load, and Metal/GPU status.

## Learning Over Time

Do not try to make the lightweight app fine-tune Whisper weights day to day.

Practical lightweight improvement path:

- Keep a domain glossary.
- Save user corrections.
- Feed short terminology hints into future jobs.
- Apply narrow post-processing replacements for proven recurring errors.
- Use regression samples to verify any correction layer.

This is not true model training, but it is the right lightweight path for improving accuracy on repeated domain vocabulary.

## Persistent Local Hosting

The browser URL can stay stable:

```text
http://127.0.0.1:5057/
```

A LaunchAgent attempt was added:

```text
work/com.siuph.local-transcript.plist
work/install_local_transcript_service.sh
```

Important issue:

- macOS LaunchAgent was blocked from executing this app directly from the Documents/Codex workspace with `Operation not permitted`.
- The robust fix is to install/copy the app runtime into a LaunchAgent-friendly location such as `~/Library/Application Support/LocalTranscript` and run from there.
- Do not rely on the Codex session process for persistence.

## App Stack

- Backend: Flask.
- Frontend: plain HTML/CSS/JS.
- Audio decode: PyAV.
- Chinese conversion: `opencc-python-reimplemented`.
- No database.
- No frontend framework.
- The transcription runtime avoids global package installs. Exception: `uipro-cli` was installed globally at the user's request for UI/UX Pro Max.

## Known Caveats

- `large-v3` is much slower than `large-v3-turbo`, especially on a Mac with 8 GB RAM.
- `whisper.cpp` and full `large-v3` use Metal successfully on this Apple M1, but runtime should be tested on representative audio before rerunning a full two-hour job.
- A direct 90-second `large-v3` sample test completed successfully with Metal and VAD. Total time was about 169 seconds for 90 seconds of source audio.
- VAD reduces silence hallucinations but can miss very quiet speech. Keep it fixed for day 1 unless a real file shows dropped speech.
- Terminology hints can help domain vocabulary, but overly strong prompts can bias or hallucinate text. Keep the field optional and short.

## Local Skills

Future agents should read the focused local skills under:

```text
work/transcribe_app/skills/
```

Current skills:

```text
audio-ingest-output-formats/SKILL.md
cantonese-transcript-quality/SKILL.md
correction-memory-lightweight-learning/SKILL.md
frontend-lightweight-design/SKILL.md
job-control-pause-resume-terminate/SKILL.md
live-system-metrics/SKILL.md
long-audio-job-operations/SKILL.md
mac-whisper-cpp-metal/SKILL.md
persistent-local-hosting/SKILL.md
progress-eta-estimation/SKILL.md
quality-regression-testing/SKILL.md
transcribe-app-maintenance/SKILL.md
transcription-model-upgrade/SKILL.md
ui-design-audit-workflow/SKILL.md
```

## Start App

```sh
cd /Users/siuph/Documents/Codex/2026-06-17/can-you-transcribe-a-cantonese-audio
work/start_transcribe_app.sh
```

Open:

```text
http://127.0.0.1:5057
```

## Full Development Record, 2026-06-17

This section is intentionally detailed. The user explicitly asked future AI agents to have enough context to continue the work accurately.

### User Requirements Captured

The user wanted:

- Full word-by-word Cantonese transcription for a near two-hour audio file.
- Timestamps and speaker labels if practical.
- Highest local accuracy, preferring full `large-v3` over faster variants.
- A reusable local workflow based on `whisper.cpp` and `large-v3`.
- A simple frontend for future uploads.
- User-selectable language and output format.
- Fixed highest-quality transcription settings so future use does not require tuning.
- A result output location field in the UI.
- Real progress, percent done, elapsed time, and estimated remaining time.
- Pause, continue, and terminate controls.
- Live CPU/GPU/RAM/system pressure display.
- A stable bookmarkable local URL that survives Codex inactivity.
- Lightweight, bloatless repo/stack.
- Documentation in `CONTEXT.md` and multiple focused `SKILL.md` files.
- UI/UX Pro Max installed via `uipro init --ai codex`.

### Model And Engine Decisions

Final day-1 choice:

```text
whisper.cpp + ggml-large-v3.bin + Metal + Silero VAD
```

Why:

- Full `large-v3` is the highest-accuracy Whisper-family model available locally in this setup.
- `large-v3-turbo` is faster but is a distilled/pruned speed-focused variant and is not the maximum-accuracy choice.
- `whisper.cpp` gives a practical local Apple Silicon path with Metal acceleration.
- The app can remain lightweight by calling the `whisper-cli` binary instead of embedding a larger Python inference stack.

Alternatives considered:

- `faster-whisper large-v3-turbo`: used for the original completed transcript because it was available quickly and practical on CPU int8. Rejected for the reusable highest-accuracy workflow because turbo trades some accuracy for speed.
- OpenAI Whisper Python package: possible, but heavier for local Mac use and not the chosen Metal path.
- True model fine-tuning: rejected for day 1 because it is not lightweight, requires curated audio/transcript pairs, is hardware-intensive, and can overfit.
- Correction memory/glossary layer: accepted as the lightweight future improvement path.
- General speaker diarization: deferred because `whisper.cpp` does not provide reliable general meeting diarization. Do not promise speaker labels until a separate diarization tool is deliberately added.

### Exact Local Build

Workspace source root:

```text
/Users/siuph/Documents/Codex/2026-06-17/can-you-transcribe-a-cantonese-audio
```

Persistent installed runtime root:

```text
/Users/siuph/Library/Application Support/LocalTranscript
```

Important installed/source paths:

```text
work/transcribe_app/app.py
work/transcribe_app/templates/index.html
work/transcribe_app/static/styles.css
work/transcribe_app/static/app.js
work/start_transcribe_app.sh
work/install_persistent_local_transcript.sh
work/transcribe-venv/
work/whisper.cpp/
work/whisper.cpp/build/bin/whisper-cli
work/whisper.cpp/models/ggml-large-v3.bin
work/whisper.cpp/models/ggml-silero-v6.2.0.bin
```

Observed sizes:

```text
ggml-large-v3.bin: 2.9G
ggml-silero-v6.2.0.bin: 868K
work/transcribe-venv: 365M
work/transcribe_app: 3.7M
```

`whisper.cpp` source revision observed:

```text
0d14756929dc9f21ddccf6102bb783397b7a8f1b
```

Build commands used:

```sh
work/transcribe-venv/bin/python -m pip install cmake
work/transcribe-venv/bin/cmake -S work/whisper.cpp -B work/whisper.cpp/build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
work/transcribe-venv/bin/cmake --build work/whisper.cpp/build --config Release -j 8
work/whisper.cpp/models/download-ggml-model.sh large-v3
work/whisper.cpp/models/download-vad-model.sh silero-v6.2.0
```

### App Implementation Decisions

Backend:

- Flask single process.
- No database.
- Job state stored in memory while active and serialized to `status.json`.
- Uploads and temporary audio stay under `outputs/transcribe_app/jobs/<job-id>/`.
- Final user-facing transcripts are written to the chosen result folder under `<result-folder>/<job-id>/`.
- The app root is portable via `LOCAL_TRANSCRIPT_ROOT`, so the same source can run from the workspace or the installed Application Support copy.

Frontend:

- Vanilla HTML/CSS/JS.
- No React/Vue/Svelte, no build step, no CSS framework.
- First screen is the working tool, not a landing page.
- User-facing controls are limited to language, output format, result folder, terminology hints, start, pause, continue, and terminate.
- Low-level quality controls such as beam size, VAD threshold, thread count, model picker, word timestamps, and diarization are intentionally hidden on day 1.

Output formats:

- Markdown, TXT, SRT, VTT, CSV, JSON, ZIP bundle.
- ZIP includes transcript outputs only, not the original upload, prepared WAV, or raw model JSON.

Audio handling:

- Save original upload.
- Convert through PyAV to 16 kHz mono WAV before calling `whisper.cpp`.
- This was chosen because the original file had an unusual `.m4a.mpeg` name and PyAV handled the container reliably.

Text normalization:

- Cantonese/Chinese outputs are converted through OpenCC `s2hk` for Hong Kong Traditional text.
- Only narrow recurring technical-term replacements are allowed; do not paraphrase because the user requested word-by-word behavior.

### Current whisper.cpp Command Shape

The app builds this command pattern:

```sh
work/whisper.cpp/build/bin/whisper-cli \
  -m work/whisper.cpp/models/ggml-large-v3.bin \
  -f prepared.wav \
  -l yue \
  -t 8 \
  -bs 5 \
  -bo 5 \
  -oj \
  -ojf \
  -of raw_whisper \
  --print-progress \
  --suppress-nst \
  --vad \
  -vm work/whisper.cpp/models/ggml-silero-v6.2.0.bin \
  -vsd 700 \
  --prompt "Preserve these terms exactly when spoken: <terms>"
```

### Progress And ETA Implementation

The UI reads job JSON fields directly:

```text
progress
progress_source
audio_duration_seconds
elapsed_seconds
elapsed_label
eta_seconds
eta_label
system
process_pid
```

Sources:

- Actual progress is parsed from `whisper.cpp --print-progress` lines when available.
- Estimated progress is calculated from audio duration, `MODEL_STARTUP_SECONDS`, `LOCAL_LARGE_V3_REALTIME_FACTOR`, and actual elapsed runtime while the process is alive.
- Browser polling triggers backend refreshes, so elapsed time and estimates keep moving even if `whisper.cpp` is quiet.
- Pause time is excluded from processing elapsed time using `paused_at` and `total_paused_seconds`.

Important observed caveat:

- A 25-second sample job with full `large-v3` reached estimated `95%` but entered a long final inference phase under very high system load. It did not produce outputs before it was manually terminated.
- The ETA logic was patched afterward so running jobs do not show `0s` remaining just because the conservative estimate was exceeded.
- Future agents should consider chunked long-audio processing if this repeats on representative files. Chunking was deferred to keep day 1 lightweight.

### Pause, Continue, Terminate

Implemented endpoints:

```text
POST /api/jobs/<job_id>/pause
POST /api/jobs/<job_id>/resume
POST /api/jobs/<job_id>/terminate
```

Implementation:

- Pause sends `SIGSTOP` to the `whisper.cpp` child process.
- Continue sends `SIGCONT`.
- Terminate sets `cancel_requested` and sends `SIGTERM`.
- If a paused job is terminated, the backend sends `SIGCONT` after `SIGTERM` so the process can receive the termination.

Limitations:

- Controls work for currently attached in-memory jobs.
- If Flask exits, old `status.json` files remain but there is no live process handle to control.
- This is acceptable for day 1 and avoids adding a heavier job manager.

### Live System Metrics

Implemented lightweight sources:

```text
ps -p <pid> -o %cpu=,%mem=,rss=,etime=
os.getloadavg()
vm_stat
whisper.cpp logs for Metal backend evidence
```

UI shows:

- Process CPU.
- Process memory footprint.
- System load.
- Memory free/used estimate.
- GPU state as `Metal active`.

Important limitation:

- macOS per-process GPU percentage is not exposed here without heavier tooling or private APIs. Do not show a fake numeric GPU percentage.

### Persistent Hosting Decision

Stable URL:

```text
http://127.0.0.1:5057/
```

Initial approach:

- A LaunchAgent was pointed directly at the Documents/Codex workspace.
- It failed with `Operation not permitted`, likely due macOS privacy restrictions for background LaunchAgents accessing Documents.

Final approach:

- Copy the runtime into:

```text
~/Library/Application Support/LocalTranscript
```

- Install a LaunchAgent at:

```text
~/Library/LaunchAgents/com.siuph.local-transcript.plist
```

- Set:

```text
LOCAL_TRANSCRIPT_ROOT=/Users/siuph/Library/Application Support/LocalTranscript
```

- Run:

```sh
work/install_persistent_local_transcript.sh
```

Verification command:

```sh
curl -s http://127.0.0.1:5057/api/health
```

Verified response after install:

```json
{
  "model": "/Users/siuph/Library/Application Support/LocalTranscript/work/whisper.cpp/models/ggml-large-v3.bin",
  "ready": true,
  "vad": true,
  "whisper_cli": "/Users/siuph/Library/Application Support/LocalTranscript/work/whisper.cpp/build/bin/whisper-cli"
}
```

This confirms the bookmark is served from the installed persistent runtime, not the temporary workspace server.

Do not use the older `work/install_local_transcript_service.sh` approach unless intentionally debugging the original failure; it points launchd at the Documents workspace and is not the robust path.

### UI/UX Pro Max Setup

User requested:

```sh
npm install -g uipro-cli
uipro init --ai codex
```

What happened:

- `npm install -g uipro-cli` installed `uipro-cli@2.2.3`.
- npm's global prefix was `/Users/siuph/.hermes/node`.
- The direct `uipro` command was initially unavailable on PATH.
- The binary existed at `/Users/siuph/.hermes/node/bin/uipro`.
- A symlink was added so `uipro` resolves normally:

```text
/Users/siuph/.local/bin/uipro -> /Users/siuph/.hermes/node/bin/uipro
```

Verified:

```sh
uipro --version
# 2.2.3
```

Initializer run:

```sh
uipro init --ai codex
```

Generated:

```text
.codex/skills/ui-ux-pro-max/
.codex/skills/ui-ux-pro-max/SKILL.md
.codex/skills/ui-ux-pro-max/data/*.csv
.codex/skills/ui-ux-pro-max/scripts/*.py
```

Decision:

- Keep this generated `.codex` skill as a design-reference tool.
- Do not move the transcription app to a large frontend stack.
- Use it for future UI review/search when helpful, while preserving the bloatless Flask plus vanilla frontend.

### Impeccable Setup

User requested:

```sh
npx impeccable install
```

Observed:

- `npx` installed/ran `impeccable@2.3.2`.
- That exact command is not the skill installer in this package; it was interpreted as a detector target and printed:

```text
Warning: cannot access install
```

Correct installer used:

```sh
npx --yes impeccable@2.3.2 skills install -y --providers=.agents
```

Reason:

- Impeccable `2.3.2` maps Codex to `.agents/skills`.
- Its provider allowlist accepts `.agents` but not `.codex`.

Installed:

```text
.agents/skills/impeccable/
```

Impeccable context files created:

```text
PRODUCT.md
DESIGN.md
.impeccable/design.json
.impeccable/live/config.json
```

The live config targets the Flask/Jinja template:

```json
{
  "files": ["work/transcribe_app/templates/index.html"],
  "insertBefore": "</body>",
  "commentSyntax": "html",
  "cspChecked": true
}
```

Later `impeccable init` was invoked again. Because `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, and `.impeccable/live/config.json` already existed, no files were overwritten. The init check validated the existing files instead.

Validation run:

```sh
python3 -m json.tool .impeccable/live/config.json
python3 -m json.tool .impeccable/design.json
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
node .agents/skills/impeccable/scripts/context-signals.mjs
```

Results:

- JSON files parsed successfully.
- Detector returned `[]`.
- `context-signals.mjs` reported `hasProduct: true`, `hasDesign: true`, register `product`.
- `context-signals.mjs` reported `hasCode: false` because this is a lightweight Flask/Jinja app, not a standard detected frontend framework. Future agents should still use the explicit detector targets above.

### UI Refinement With UI/UX Pro Max And Impeccable

The user asked that both design skills be used together and that any Impeccable questions be answered from context unless truly unclear.

What was inferred:

- Register: product UI.
- Users: Mac owner running private long-form transcription jobs; future agents maintaining the app.
- Purpose: local high-accuracy transcription with visible job control and system status.
- Brand personality: quiet, precise, trustworthy.
- Anti-references: landing-page hero, purple AI gradients, glassmorphism, nested cards, decorative SaaS dashboard patterns, hidden job state.

UI/UX Pro Max command used:

```sh
python3 .codex/skills/ui-ux-pro-max/scripts/search.py "local transcription productivity tool audio upload system monitoring" --design-system -p "Local Transcript" --format markdown
```

Useful guidance retained:

- Productivity-tool teal accent.
- Micro-interactions.
- High contrast and focus states.

Guidance intentionally adapted or rejected:

- Its landing-page pattern was not applied because this is a product tool, not a marketing surface.
- Extra CTA color was not introduced because Impeccable product-register guidance and the local UI both favor one restrained accent.

Frontend refinements made:

- Changed palette from warm beige-leaning neutrals to cool utility neutrals.
- Kept one teal accent: `#0b7f68`.
- Kept flat bordered panels and avoided decorative shadows.
- Changed progress bar animation from `width` to `transform: scaleX(...)`.
- Added `prefers-reduced-motion` handling.
- Disabled pause/continue/terminate controls in initial hidden markup.
- Kept stack lightweight: Flask plus vanilla HTML/CSS/JS.

Design checks run:

```sh
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
npx --yes impeccable@2.3.2 detect --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

Both returned:

```json
[]
```

### Verification So Far

Completed:

- Python syntax check:

```sh
work/transcribe-venv/bin/python -m py_compile work/transcribe_app/app.py
```

- Persistent LaunchAgent running from Application Support.
- `curl /api/health` confirms installed `large-v3` model and VAD.
- Browser UI check confirmed visible controls:
  - Result folder.
  - Terminology hints.
  - Pause.
  - Continue.
  - Terminate.
  - Progress/ETA/elapsed panel.
  - CPU/RAM/load/GPU panel.
- Prior end-to-end source-workspace API test completed:

```text
outputs/transcribe_app/jobs/3282a54ec512/
```

It generated:

```text
transcript.md
transcript.txt
transcript.srt
transcript.vtt
transcript.csv
transcript.json
transcript.zip
```

- A later persistent-runtime job verified live progress, ETA, elapsed time, output-location serialization, Metal logs, VAD logs, and system metrics, but was manually terminated after a long final phase and did not produce final transcript files.
- Browser check after final persistent reinstall verified title `Local Transcript`, status `Ready`, default result folder under `/Users/siuph/Library/Application Support/LocalTranscript/outputs/transcribe_app/results`, background `rgb(246, 247, 248)`, accent `#0b7f68`, initial job panel hidden, and pause/continue/terminate initially disabled.

### Known Risks And Future Improvements

Known risks:

- Full `large-v3` can be very slow on this Apple M1 with 8 GB RAM.
- Under heavy load, process status may look alive while useful output is delayed.
- ETA is an estimate, not a guarantee; it should remain conservative and never claim a running job has exactly `0s` remaining.
- Pause/resume/terminate use POSIX signals and are best-effort around native compute kernels.
- No true diarization yet.
- No true continual model learning yet.

Good next improvements, in priority order:

1. Add optional chunked processing for long audio if `large-v3` finalization stalls again.
2. Save partial transcript output per chunk.
3. Add a small local correction/glossary memory UI.
4. Add a regression sample folder and comparison script before any model/prompt/VAD changes.
5. Consider diarization only as a separate deliberate feature.
6. Consider a lighter model mode only if the user explicitly prioritizes speed over highest accuracy.

### 2026-06-17 Impeccable Critique Run

User requested:

```text
[impeccable] critique http://127.0.0.1:5057/
```

Critique workflow used:

- Loaded `.agents/skills/impeccable/SKILL.md`.
- Loaded `.agents/skills/impeccable/reference/critique.md`.
- Loaded product register guidance from `.agents/skills/impeccable/reference/product.md`.
- Read `PRODUCT.md`, `DESIGN.md`, the Flask template, CSS, and frontend JS.
- Verified the app was live with `curl --max-time 5 -s http://127.0.0.1:5057/api/health`.
- Ran detector:

```sh
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

Detector result:

```json
[]
```

Browser inspection:

- Opened fresh in-app browser tabs at `http://127.0.0.1:5057/`.
- Checked narrow rendering around `599 x 934`.
- Temporarily checked desktop rendering at `1280 x 900`, then reset viewport.
- Observed the UI remained visually stable with no text overlap.
- Observed the default result folder path is visibly clipped in the desktop three-column layout.
- Attempted Impeccable overlay injection on a fresh tab. It failed because Codex Browser Playwright evaluation is read-only for mutation:

```text
TypeError: Cannot set property title of [object Object] which has only a getter
```

Decision:

- No user-visible Impeccable overlay was claimed.
- Fallback evidence used DOM snapshots, screenshots, computed layout reads, and the clean detector output.

Critique result:

- Score: `31/40`.
- P0 findings: `0`.
- P1 findings: `1`.
- Main P1 issue: result folder is too fragile as a raw, clipped filesystem path.

Snapshot written:

```text
.impeccable/critique/2026-06-17T10-06-38Z__127-0-0-1.md
```

Trend:

```text
31
```

### Documentation Map

Future agents should use:

```text
CONTEXT.md
work/transcribe_app/README.md
work/transcribe_app/skills/*/SKILL.md
.codex/skills/ui-ux-pro-max/SKILL.md
.agents/skills/impeccable/SKILL.md
PRODUCT.md
DESIGN.md
.impeccable/design.json
```

The focused local skills are the operational runbooks. `CONTEXT.md` is the historical record and decision log.

### GitHub Portability Decision

User wants the codebase on GitHub so the project can be used from another laptop.

Decision:

- Track app code, docs, design context, install scripts, local `SKILL.md` runbooks, and Impeccable critique snapshots.
- Do not track generated transcripts, uploaded audio, sample audio, logs, `__pycache__`, Python virtualenv, `whisper.cpp` checkout, build outputs, or model binaries.
- Add `work/bootstrap_runtime.sh` so another Mac can recreate the ignored runtime assets.
- Add `work/setup_new_mac.sh` as the preferred one-command fresh-device installer.
- Add `AGENTS.md` and `AGENT.md` so future agents know how to install the app on a brand-new Mac.
- Add `work/runtime-manifest.md` documenting the pinned runtime:
  - `whisper.cpp` repo: `https://github.com/ggml-org/whisper.cpp.git`
  - commit: `0d14756929dc9f21ddccf6102bb783397b7a8f1b`
  - model: `ggml-large-v3.bin`
  - VAD: `ggml-silero-v6.2.0.bin`

Why:

- GitHub normal Git files are enforced at 100 MB per object.
- The full `large-v3` model is about 2.9 GB.
- Git LFS is not the day-1 choice because Free/Pro LFS per-file limits and bandwidth/storage quotas make it less portable than rebuilding/downloading with a script.

Current GitHub blocker:

- `gh` is not installed.
- Homebrew was not found in PATH.
- GitHub connector tools are available for existing repositories, but no create-new-repository tool was exposed in this session.
- If no remote repo already exists, the user needs to either create an empty GitHub repo and provide its URL, or install/authenticate `gh` so Codex can create and push the repository.

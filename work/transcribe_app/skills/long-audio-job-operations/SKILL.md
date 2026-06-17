# Long Audio Job Operations

Use this skill when running or improving two-hour transcription jobs.

## Runtime Expectations

`large-v3` is slower than `large-v3-turbo`.

Observed local sample:

```text
90 seconds of source audio took about 169 seconds with whisper.cpp large-v3 on Apple M1.
```

Do not promise a fast full run with full `large-v3` on this hardware.

## Job Folder Structure

Each app job should stay self-contained:

```text
outputs/transcribe_app/jobs/<job-id>/
```

Expected files:

```text
status.json
<original upload>
prepared.wav
raw_whisper.json
```

Final transcript files are written to the selected result folder:

```text
outputs/transcribe_app/results/<job-id>/transcript.md / .srt / .vtt / .csv / .json / .txt / .zip
```

## Recovery

Current app jobs are process-local. If the Flask process exits, active jobs stop.

Future improvement, if needed:

- Add a simple resumable job runner.
- Split long audio into chunks.
- Write partial outputs after each chunk.
- Merge segment timestamps at the end.

Do not add this until a real need appears. It adds complexity.

## Progress

The app reads `whisper.cpp --print-progress` output and stores recent logs in `status.json`.

Keep logs bounded so `status.json` does not grow without limit.

## Temporary Files

The prepared WAV can be large. Keep it in the job folder so cleanup is obvious.

Do not put temporary audio in the home directory.

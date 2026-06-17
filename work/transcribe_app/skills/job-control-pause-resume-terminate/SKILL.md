# Job Control: Pause, Continue, Terminate

Use this skill when changing runtime controls for active transcription jobs.

## Current Design

The app stores the `whisper.cpp` child process PID in job state:

```text
process_pid
```

Actions:

- Pause: send `SIGSTOP`.
- Continue: send `SIGCONT`.
- Terminate: set `cancel_requested` and send `SIGTERM`.

Endpoints:

```text
POST /api/jobs/<job_id>/pause
POST /api/jobs/<job_id>/resume
POST /api/jobs/<job_id>/terminate
```

## UI Behavior

- Pause button enabled only when job is running.
- Continue button enabled only when job is paused.
- Terminate button enabled while a process exists.
- Cancelled jobs should not show downloads unless outputs already exist.

## Caveats

Pause and continue only work for currently attached in-memory jobs. If Flask exits, existing status files remain, but there is no live process handle.

This is acceptable for the lightweight day-1 design. A more robust job manager would require more persistent process supervision and is intentionally not added yet.


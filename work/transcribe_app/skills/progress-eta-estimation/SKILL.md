# Progress And ETA Estimation

Use this skill when changing progress bars, remaining-time estimates, or long-job status reporting.

## Requirements

The UI must show:

- Percent complete.
- Estimated remaining time.
- Elapsed time.
- Current task message.

## Sources

Use actual `whisper.cpp` progress when available:

```text
whisper_print_progress_callback: progress = 42%
```

Before the first actual progress event, or between sparse updates, estimate from:

- Audio duration.
- Local benchmark factor.
- Model startup overhead.
- Elapsed runtime.

Current constants in `app.py`:

```text
LOCAL_LARGE_V3_REALTIME_FACTOR = 2.4
MODEL_STARTUP_SECONDS = 60
```

Observed benchmark:

```text
90 seconds of audio took about 169 seconds with large-v3 on Apple M1.
```

## ETA Behavior

- Use conservative estimates.
- Apply slowdown margin early in the run.
- Once actual progress appears, prefer actual progress.
- Smooth ETA using recent progress samples.
- Never show negative remaining time.
- Never show `0s` remaining while a job is still running just because the estimate has been exceeded.
- At completion, set progress to `100%` and ETA to `0s`.

## Implementation Notes

Important functions:

```text
format_duration
wav_duration
initial_runtime_estimate
eta_from_progress
update_progress
refresh_runtime_status
processing_elapsed
```

Progress data is serialized in `status.json`:

```text
progress
progress_source
audio_duration_seconds
elapsed_seconds
elapsed_label
eta_seconds
eta_label
```

The frontend should read these fields directly rather than parsing logs.

## Observed Edge Case

A 25-second `large-v3` persistent-runtime test reached estimated `95%` and then stayed in a long final native inference phase under high system load. It was manually terminated before output was produced.

If this repeats on representative audio, the next engineering step is chunked processing with partial output writes. Do not simply lower the quality defaults to make the ETA look better.

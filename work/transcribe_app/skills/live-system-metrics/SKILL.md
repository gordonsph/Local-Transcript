# Live System Metrics

Use this skill when changing CPU/RAM/GPU status display.

## Goal

While a transcription is running, the UI should tell the user what the machine is doing:

- Transcription process CPU percent.
- Transcription process memory footprint.
- System load.
- Memory free/used estimate.
- Whether Metal/GPU backend is active.

## Current Lightweight Implementation

No extra system-monitoring dependency is used.

Data sources:

- `ps -p <pid> -o %cpu=,%mem=,rss=,etime=`
- `os.getloadavg()`
- `vm_stat`
- `whisper.cpp` logs for Metal/GPU backend evidence

Serialized under:

```text
system
```

In job status.

## GPU Caveat

macOS per-process GPU percent is not available here without heavier tooling or private APIs.

Show:

```text
Metal active
```

when the workflow is using the Metal-enabled `whisper.cpp` build. Do not claim a numeric GPU percent unless a real measured source is added.

## Keep It Lightweight

Avoid:

- Adding a database.
- Adding a full metrics daemon.
- Adding heavyweight monitoring libraries.

Use bounded, best-effort snapshots.


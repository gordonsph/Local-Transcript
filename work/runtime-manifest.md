# Runtime Manifest

This repository intentionally does not track heavyweight runtime artifacts. A fresh Mac should recreate them with:

```sh
work/setup_new_mac.sh
```

Use `work/bootstrap_runtime.sh` only when recreating runtime dependencies without installing the persistent LaunchAgent.

## Pinned Runtime

`whisper.cpp`:

```text
repository: https://github.com/ggml-org/whisper.cpp.git
commit: 0d14756929dc9f21ddccf6102bb783397b7a8f1b
```

Models:

```text
work/whisper.cpp/models/ggml-large-v3.bin
work/whisper.cpp/models/ggml-silero-v6.2.0.bin
```

Python environment:

```text
work/transcribe-venv/
work/transcribe_app/requirements.txt
```

## Why These Files Are Not In Git

GitHub rejects normal Git objects over 100 MB. The full `large-v3` model is about 2.9 GB, so it cannot be pushed as a regular Git file.

Git LFS is not the default here because the full model is also larger than the GitHub Free/Pro LFS per-file limit, and LFS storage/bandwidth quotas would make clones less predictable.

The portable path is:

1. Clone this repository.
2. Run `work/bootstrap_runtime.sh`.
3. Run `work/install_persistent_local_transcript.sh` if the always-on local service is desired.

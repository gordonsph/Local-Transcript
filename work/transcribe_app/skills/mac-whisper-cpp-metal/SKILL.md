# Mac whisper.cpp Metal Setup

Use this skill when building or repairing `whisper.cpp` on Apple Silicon.

## Environment Observed

Machine:

```text
Apple M1
8 GB RAM
macOS 26.5.1
Command Line Tools installed
```

Tools found:

```text
/usr/bin/git
/usr/bin/make
/usr/bin/clang
```

CMake was not installed globally, so it was installed inside the local venv:

```sh
work/transcribe-venv/bin/python -m pip install cmake
```

## Build

Clone:

```sh
git clone https://github.com/ggml-org/whisper.cpp.git work/whisper.cpp
```

Configure and build:

```sh
work/transcribe-venv/bin/cmake -S work/whisper.cpp -B work/whisper.cpp/build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
work/transcribe-venv/bin/cmake --build work/whisper.cpp/build --config Release -j 8
```

Expected binary:

```text
work/whisper.cpp/build/bin/whisper-cli
```

## Models

Download full large-v3:

```sh
work/whisper.cpp/models/download-ggml-model.sh large-v3
```

Download VAD:

```sh
work/whisper.cpp/models/download-vad-model.sh silero-v6.2.0
```

Expected files:

```text
work/whisper.cpp/models/ggml-large-v3.bin
work/whisper.cpp/models/ggml-silero-v6.2.0.bin
```

## Metal Verification

Run a short sample and check logs for:

```text
use gpu = 1
Metal framework found
Including METAL backend
GPU name: Apple M1
model size = 3094.36 MB
using MTL0 backend
```

If logs show `--no-gpu` or no Metal backend, rebuild with `-DGGML_METAL=ON`.

## Core ML

Core ML was not used in the day-1 setup.

Use Core ML only if:

- Metal alone is too slow.
- You can afford additional setup complexity.
- You verify output quality and timestamps after enabling it.

Do not add Core ML preemptively. It increases setup complexity and is not required for the current app to work.


# Third-Party Notices — Local Transcript

Local Transcript bundles and uses the following open-source components. All are
permissively licensed and free to redistribute.

## whisper.cpp (MIT)
High-performance C/C++ inference engine for OpenAI's Whisper, by the ggml authors.
- Source: https://github.com/ggml-org/whisper.cpp
- License: MIT — Copyright (c) 2023–2026 The ggml authors

## Whisper large-v3 model (MIT)
The `ggml-large-v3.bin` weights are a GGML conversion of OpenAI's Whisper large-v3
model, downloaded on first run (not bundled).
- Model: https://github.com/openai/whisper — License: MIT — Copyright (c) 2022 OpenAI
- GGML conversion hosted at https://huggingface.co/ggerganov/whisper.cpp

## Silero VAD model (MIT)
Optional voice-activity-detection model (`ggml-silero-v6.2.0.bin`), downloaded on
first run.
- Source: https://github.com/snakers4/silero-vad — License: MIT
- GGML conversion hosted at https://huggingface.co/ggml-org/whisper-vad

## Python runtime & libraries
Bundled via py2app: CPython (PSF License), Flask / Werkzeug / Jinja2 (BSD-3-Clause),
PyAV + FFmpeg libraries (PyAV BSD-3-Clause; FFmpeg LGPL-2.1+), NumPy (BSD-3-Clause),
OpenCC (Apache-2.0), pywebview (BSD-3-Clause), pyobjc (MIT).

Full license texts for each component are available at their respective project
repositories linked above.

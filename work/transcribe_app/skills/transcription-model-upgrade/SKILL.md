# Transcription Model Upgrade

Use this skill when changing or evaluating transcription models for this app.

## Core Distinction

Separate these decisions:

- Model weights: `large-v3`, `large-v3-turbo`, `medium`, etc.
- Inference engine: `whisper.cpp`, `faster-whisper`, OpenAI Whisper Python.
- Quantization: full precision, int8, q5, q8, etc.
- Runtime backend: CPU, Metal, Core ML, CUDA.

Changing the engine does not automatically improve accuracy. Accuracy mostly follows the model weights, decoding settings, language selection, audio quality, and prompts.

## Current Day-1 Choice

Use:

```text
whisper.cpp + ggml-large-v3.bin
```

Reason:

- Full `large-v3` is the highest-accuracy Whisper family choice available locally.
- `large-v3-turbo` is faster but is a pruned/optimized version and can lose some accuracy.
- `whisper.cpp` gives a practical Apple Silicon path with Metal.

## When To Use faster-whisper

Use `faster-whisper` when:

- You need a quick local transcript.
- `large-v3-turbo` speed is more important than maximum accuracy.
- You want a Python-native pipeline.
- You need easier integration with Python post-processing.

Known previous setup:

```text
faster-whisper large-v3-turbo
device=cpu
compute_type=int8
language=yue
vad_filter=True
```

It completed the first two-hour transcript but showed technical-term errors and occasional translation-like behavior depending on prompts.

## When To Use whisper.cpp

Use `whisper.cpp` when:

- You want full `large-v3` locally.
- You want Apple Metal acceleration on Mac.
- You want a standalone CLI backend.
- You want direct SRT/VTT/CSV/JSON outputs.

Current command pattern:

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
  --vad \
  -vm work/whisper.cpp/models/ggml-silero-v6.2.0.bin \
  -vsd 700 \
  --suppress-nst \
  --print-progress
```

## Upgrade Workflow

1. Pick the model target.
2. Download or convert the model into `work/whisper.cpp/models/`.
3. Update `MODEL_PATH` in `work/transcribe_app/app.py`.
4. Run a 60-90 second sample through the exact app backend.
5. Compare against the previous model on:
   - Cantonese recognition.
   - Mixed English technical terms.
   - Silence hallucinations.
   - Timestamp quality.
   - Runtime and memory use.
6. Only run a full two-hour transcription after the sample improves or clearly matches quality.

## Comparison Rule

Do not judge models by one short easy clip. Include:

- Silence at the beginning.
- Mixed Cantonese and English terms.
- Overlapping or fast speech.
- A section with important domain vocabulary.


# Quality Regression Testing

Use this skill before changing models, prompts, VAD settings, language defaults, or output post-processing.

## Test Set

Do not test only one easy clip. Build a small set with:

- Opening silence.
- Fast Cantonese.
- Mixed English technical terms.
- Product/security vocabulary.
- A quiet section.
- A long segment with multiple speakers or interruptions if available.

## Current Known Sample

Source:

```text
/Users/siuph/Downloads/16 Jun at 5-28 pm.m4a.mpeg
```

A 90-second sample from the beginning was used to verify `whisper.cpp + large-v3`.

Observed:

- Metal loaded successfully.
- VAD found speech segments.
- Cantonese language code `yue` worked.
- Runtime was about 169 seconds for a 90-second sample on Apple M1.

## Compare On These Axes

- Cantonese fidelity.
- Mixed English term fidelity.
- Hallucinations during silence.
- Missing quiet speech.
- Timestamp boundaries.
- Runtime.
- Memory pressure.

## Do Not Overfit

If a prompt improves one phrase but causes translation-like output or repeated terms elsewhere, reject it.

Prefer:

- Short terminology hints.
- Cantonese language code.
- Minimal post-processing.

Avoid:

- Long behavioral prompts.
- Aggressive automatic replacements.
- Broad paraphrasing.

## Full Run Gate

Before a full two-hour transcription:

1. Run a 60-90 second representative sample.
2. Inspect output manually.
3. Compare with the previous known-good run.
4. Only run the full file after the sample passes.


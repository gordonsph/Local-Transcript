# Cantonese Transcript Quality

Use this skill when tuning Cantonese or mixed Cantonese-English transcription quality.

## Defaults

Use Cantonese language code:

```text
yue
```

Normalize Chinese output to Hong Kong Traditional:

```text
OpenCC s2hk
```

Keep task as transcription, not translation.

## Prompt And Terminology

Terminology hints are useful for product or security terms such as:

```text
trust device, 3DS, saved card, safe address, checkout, OTP
```

Keep hints short. Overly strong prompts can cause hallucinations or translation-like output.

Recommended prompt shape:

```text
Preserve these terms exactly when spoken: <terms>
```

Do not write long instructions telling the model how to behave unless a sample proves it helps.

## VAD

Use VAD for long recordings with silence. It reduces silence hallucinations.

Risk:

- Very quiet speech can be dropped.

If a user reports missing quiet speech:

1. Test the same clip with VAD off.
2. Test a lower VAD threshold.
3. Compare before changing the default.

## Speaker Labels

Do not promise speaker labels from this setup.

`whisper.cpp` supports limited stereo diarization and tinydiarize paths, but this is not reliable general speaker diarization for meeting audio. Keep speaker labels out of day-1 output unless a separate diarization tool is intentionally added.

## Post-Processing

Allowed default cleanup:

- Convert Simplified to Hong Kong Traditional for Cantonese/Chinese.
- Fix narrow repeated model artifacts only when they are clearly technical-term recognition errors.

Avoid broad rewriting. The user asked for word-by-word transcript behavior, so post-processing should not paraphrase.


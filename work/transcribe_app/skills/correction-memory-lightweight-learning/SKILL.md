# Correction Memory And Lightweight Learning

Use this skill when the user asks whether the transcription system can improve from day-to-day use.

## Answer

Do not fine-tune Whisper weights inside this lightweight app.

Reasons:

- Fine-tuning is not lightweight.
- It requires curated audio/transcript pairs.
- It is slow and hardware-intensive.
- It can overfit or make general transcription worse.
- It complicates the local app significantly.

## Lightweight Alternative

Build a correction memory layer around the model:

- Domain glossary.
- User correction table.
- Narrow recurring replacement rules.
- Short terminology prompt generated from the glossary.
- Regression samples to verify changes.

This improves practical accuracy over time without changing model weights.

## Safe Design

Store corrections as plain local files, for example:

```text
work/transcribe_app/memory/glossary.csv
work/transcribe_app/memory/replacements.csv
```

Suggested columns:

```text
heard_as,correct,context,language,enabled
```

Apply corrections only when:

- The error is repeated.
- The replacement is narrow.
- The context makes the replacement safe.

Do not add broad replacements that can rewrite valid speech.

## Future UI

If this feature is added later, keep it small:

- A review screen for uncertain terms.
- A button to save a correction.
- A glossary list.

Do not add automatic training language. Call it `Glossary` or `Corrections`, not model learning.


# Lightweight Frontend Design

Use this skill when changing the local upload UI.

## Product Shape

This is a tool, not a landing page.

The first screen should be the actual workflow:

- Audio upload.
- Language.
- Output format.
- Result folder.
- Terminology hints.
- Start button.
- Progress.
- Downloads.

## Stack

Use:

- Plain HTML template.
- Plain CSS.
- Plain JavaScript.

Avoid:

- React/Vue/Svelte.
- CSS frameworks.
- Icon packages.
- Build tools.
- Client-side routing.

## Visual Direction

Keep it quiet and work-focused:

- Cool neutral background.
- High contrast text.
- Stable control dimensions.
- Clear focus states.
- No decorative blobs or gradients.
- No card nesting.

Current documented palette:

```text
background #f6f7f8
surface    #ffffff
ink        #111827
muted      #667085
line       #d7dde5
accent     #0b7f68
danger     #b42318
focus      #8eb8ff
```

Use the teal accent only for primary action, progress, focus-related emphasis, or current state. Do not introduce purple/blue gradients, beige paper backgrounds, or extra accent colors without updating `DESIGN.md`.

## Controls

Use ordinary, predictable controls:

- File input/dropzone for upload.
- Select for language.
- Select for output format.
- Text input for result folder.
- Small textarea for terminology hints.
- Single primary action button.

Do not expose low-level quality settings unless the user asks for them.

## Motion

Motion should be small and state-driven:

- Progress fill uses `transform: scaleX(...)`, not width animation.
- Normal UI transitions should be 150-250ms.
- Always keep a `prefers-reduced-motion` fallback.

## Mobile

Controls should stack cleanly on narrow screens. Text must wrap within containers.

## Design Documentation

When refining the UI, keep these root files aligned:

```text
PRODUCT.md
DESIGN.md
.impeccable/design.json
```

After CSS/HTML/JS changes, run:

```sh
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
npx --yes impeccable@2.3.2 detect --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

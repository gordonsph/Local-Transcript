# UI Design Audit Workflow

Use this skill when refining the Local Transcript frontend with UI/UX Pro Max and Impeccable.

## Installed Design Tools

UI/UX Pro Max:

```text
.codex/skills/ui-ux-pro-max/
```

Installed with:

```sh
npm install -g uipro-cli
uipro init --ai codex
```

`npm` installed the binary under:

```text
/Users/siuph/.hermes/node/bin/uipro
```

A symlink was added so `uipro` works from PATH:

```text
/Users/siuph/.local/bin/uipro -> /Users/siuph/.hermes/node/bin/uipro
```

Impeccable:

```text
.agents/skills/impeccable/
```

The user requested `npx impeccable install`, but this package treats that as a detect target and prints:

```text
Warning: cannot access install
```

The correct install command for this version is:

```sh
npx --yes impeccable@2.3.2 skills install -y --providers=.agents
```

Reason:

- Impeccable `2.3.2` maps Codex to `.agents/skills`.
- Its provider allowlist does not accept `.codex` directly.

## Required Context Files

Keep these files in sync with frontend decisions:

```text
PRODUCT.md
DESIGN.md
.impeccable/design.json
.impeccable/live/config.json
CONTEXT.md
```

`PRODUCT.md` is strategic: users, purpose, register, anti-references, design principles.

`DESIGN.md` is visual: palette, type, elevation, components, do/don't rules.

`.impeccable/design.json` carries sidecar detail for motion, breakpoints, and component-specific rules.

## Current Product Register

Treat this as product UI, not brand/marketing UI.

Design should serve a task:

- Upload audio.
- Pick language and format.
- Choose result folder.
- Start transcription.
- Monitor progress and system pressure.
- Pause, continue, or terminate.
- Download outputs.

## Design Direction

Current direction:

```text
Quiet, precise, trustworthy local utility.
```

Use:

- Cool neutral background.
- White surfaces.
- Strong ink text.
- One restrained teal accent.
- Flat panels with borders, not shadows.
- System font stack.
- Stable control dimensions.

Avoid:

- Landing-page hero design.
- Purple gradients.
- Glassmorphism.
- Nested cards.
- Decorative illustrations.
- Fake GPU percentages.
- Exposing quality knobs by default.

## UI/UX Pro Max Workflow

Use UI/UX Pro Max for broad design-system suggestions:

```sh
python3 .codex/skills/ui-ux-pro-max/scripts/search.py "local transcription productivity tool audio upload system monitoring" --design-system -p "Local Transcript" --format markdown
```

Interpret recommendations through the product register. UI/UX Pro Max suggested a productivity-tool teal palette and micro-interactions; keep those, but do not adopt landing-page structure or extra CTA colors if they reduce utility.

## Impeccable Workflow

Run context first:

```sh
node .agents/skills/impeccable/scripts/context.mjs
```

Run detector after UI changes:

```sh
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
npx --yes impeccable@2.3.2 detect --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

Use the bundled detector as design-system-aware after `DESIGN.md` exists. Use the npm detector as a package-level independent scan.

For critique runs, also follow:

```sh
node .agents/skills/impeccable/scripts/critique-storage.mjs slug "http://127.0.0.1:5057/"
node .agents/skills/impeccable/scripts/critique-storage.mjs trend 127-0-0-1 5
```

Persist the final critique body with:

```sh
IMPECCABLE_CRITIQUE_META='{"target":"http://127.0.0.1:5057/","total_score":31,"p0_count":0,"p1_count":1}' \
  node .agents/skills/impeccable/scripts/critique-storage.mjs write 127-0-0-1 <body-file>
```

The current URL slug is:

```text
127-0-0-1
```

Codex Browser limitation observed on 2026-06-17:

- Browser Playwright `evaluate` is read-only for mutation.
- Impeccable overlay preflight failed when trying to set `document.title`.
- Do not claim a user-visible overlay exists unless a future browser surface supports script injection.
- Use DOM snapshots, screenshots, computed layout reads, and detector output as fallback evidence.

## Current Refinement Decisions

Changes made during the combined UI/UX Pro Max + Impeccable pass:

- Moved away from beige-leaning UI into a cool neutral palette.
- Documented product strategy in `PRODUCT.md`.
- Documented visual system in `DESIGN.md`.
- Added `.impeccable/design.json`.
- Added `.impeccable/live/config.json` targeting the Flask template.
- Replaced progress width animation with `transform: scaleX(...)`.
- Added reduced-motion fallback.
- Disabled pause/continue/terminate buttons in initial hidden markup.
- Kept stack bloatless: no frontend framework, no icon library, no CSS framework.

## Verification

Current expected clean checks:

```text
node .agents/skills/impeccable/scripts/detect.mjs ... => []
npx --yes impeccable@2.3.2 detect --json ... => []
```

After UI changes, reinstall persistent runtime:

```sh
work/install_persistent_local_transcript.sh
```

Then verify:

```sh
curl --max-time 5 -s http://127.0.0.1:5057/api/health
```

The response should point to:

```text
/Users/siuph/Library/Application Support/LocalTranscript/
```

---
name: Local Transcript
description: A native macOS Liquid Glass utility for high-accuracy, on-device transcription.
register: product
colors:
  accent: "#0b7f68"
  accent-deep: "#096153"
  on-accent: "#ffffff"
  label: "rgba(0,0,0,0.88)"
  label-2: "rgba(0,0,0,0.56)"
  label-3: "rgba(0,0,0,0.40)"
  sidebar: "rgba(246,247,249,0.55)"
  content: "rgba(255,255,255,0.78)"
  card: "#ffffff"
  inset: "rgba(120,120,128,0.08)"
  sep: "rgba(0,0,0,0.10)"
  focus: "#2f6bff"
  danger: "#c0362c"
typography:
  family: "-apple-system, BlinkMacSystemFont, SF Pro Text, SF Pro Display, system-ui, sans-serif"
  mono: "ui-monospace, SF Mono, Menlo, monospace"
  title: { fontSize: "14px", fontWeight: 600 }
  toolbar-title: { fontSize: "15px", fontWeight: 600 }
  body: { fontSize: "14px", fontWeight: 400 }
  group-label: { fontSize: "12px", fontWeight: 600 }
  readout-value: { fontSize: "17px", fontWeight: 600, tabularNums: true }
rounded: { window: "13px", card: "11px", row: "8px", pill: "980px" }
---

# Design System: Local Transcript

## 1. Overview

**Creative North Star: a first-party macOS "Liquid Glass" app (macOS Tahoe 26).**

Local Transcript should be indistinguishable from something Apple shipped: real
system materials (vibrancy), a translucent sidebar over a legible content pane,
grouped inset rows, SF Pro, hairline separators, tabular numerals, and the system
control vocabulary. It is a **repeat-use pro tool** for supervising long on-device
transcriptions — calm, legible, and fast on the 20th use, not just the 1st.

> This direction (finalized via a 6-variation, 5-judge design tournament) **supersedes
> the earlier flat "control-room" look.** Glass is now the language — done the Apple
> way (restraint, correct material hierarchy), never as cheap glassmorphism.

**Key characteristics**
- Two-tier material: translucent **chrome** (sidebar/toolbar/action bar) over a
  near-opaque **content** pane where all body text lives.
- Real vibrancy from the OS, not a CSS gradient (see §4).
- One accent — the brand **teal** — applied HIG-disciplined.
- Progressive disclosure + clear IA: one obvious primary action per state.

## 2. The two named rules

**The Material Hierarchy Rule.** Translucency is for chrome, opacity is for content.
The sidebar (`--sidebar`, ~0.55 alpha) and bars are vibrant glass; the content pane
(`--content`, ~0.78) and every card/field is near-opaque. **Body text only ever sits
on the near-opaque content tier or on solid cards/fields — never directly on the
translucent chrome or the desktop behind it.**

**The Legibility-First Rule (the #1 Liquid Glass risk).** All body text, labels, and
readouts must meet **WCAG AA (≥4.5:1)**. Because content sits on the opaque tier this
is structural, not luck. The `--label` ramp (0.88 / 0.56 / 0.40) is tuned for the
content pane. The teal selected-row fill carries white text and must stay dark enough
to clear 4.5:1 (`#0b7f68` ≈ 4.95:1 — do not lighten it for selection). Focus is a
distinct **blue** ring (`--focus`), never the teal accent (the One-Accent rule).

## 3. Colors

Restrained: neutral glass tiers + a single deep-teal accent for action, selection,
and progress. Teal — not system blue — because it is the brand identity (and matches
the app icon); native feel comes from materials and layout, not the hue.

- **Operational Teal** `#0b7f68` / **Deep** `#096153`: primary action, active nav row,
  progress fill, focus tint, brand mark. Reserved — never decoration.
- **Label ramp** `rgba(0,0,0, .88 / .56 / .40)` (and the inverse in dark): primary,
  secondary, tertiary/icon text on the content tier.
- **Glass tiers**: `--sidebar` (translucent chrome), `--content` (near-opaque),
  `--card` (solid rows), `--inset` (quiet fills), `--toolbar` (translucent bars).
- **Focus Blue** `#2f6bff` (light) / `#7aa7ff` (dark): keyboard focus ring + halo.
- **Danger** `#c0362c`: Terminate, failures, and the move-to-Applications banner only.
- A full dark theme mirrors every token under `prefers-color-scheme: dark`.

## 4. Material & elevation (real vibrancy)

The pywebview shell creates the window with `vibrancy=True` + `transparent=True`, so
macOS puts an **NSVisualEffectView** behind a transparent webview. On load the shell
adds `body.vibrancy`, which drops the CSS faux-desktop gradient and lets the real
system material (the user's desktop/windows, blurred) show through the chrome. The
faux-desktop gradient remains as the browser-preview / non-vibrancy fallback.

Depth is conveyed by the material tiers, hairline `--sep` borders, and `backdrop-filter`
blur — **not** by heavy drop shadows. Only true overlays (the install dialog) carry a
shadow.

## 5. Components

- **Sidebar nav** (`.source-tab`): icon + title + sublabel rows; the active row is a
  filled teal pill with white text. Footer: install button, a status pill with a live
  dot, and a persistent "Runs entirely on this Mac" privacy chip.
- **Grouped inset card** (`.card` + `.row`): System-Settings-style rounded group with
  hairline-separated rows (icon · label · value/control). Used for Output settings and
  Advanced. **No nested cards.**
- **Controls**: native `select.macsel` with a custom chevron, `.rowinput` text/textarea,
  segmented/disclosure patterns. Every interactive control has hover/focus/active/disabled.
- **Readout clusters** (`.readout-grid`): de-carded instrument tiles (one bordered
  container, 1px hairline gaps) with uppercase micro-labels over tabular values — used
  for the monitor's metrics and the download stats.
- **Job monitor**: a large tabular `%` headline, teal progress bar, Remaining/Elapsed,
  a CPU/RAM/Load/GPU(Metal) cluster, pause/continue/terminate, a dark mono live log,
  and result download links.
- **First-run download**: a designed moment — icon, reassurance copy ("runs entirely on
  your Mac… one-time 2.9 GB… offline forever"), checksum/on-device metatags, progress +
  speed/ETA, and a single teal CTA. Gated by `model_ready`; only shown until the model
  is installed.
- **Motion**: 120–250 ms, ease-out. Conveys state, not spectacle. `prefers-reduced-motion`
  collapses all of it.

## 6. Information architecture & disclosure

- **Sidebar = navigation** (Source: File / URL / Live), **content = the task**. Only the
  selected source's controls render.
- **Reveal as needed**: Advanced settings collapsed by default; the job monitor appears
  only while a job runs; the model-download panel only on first run; the
  move-to-Applications banner only when translocated.
- **One primary action per state** in the action bar (Start transcript / Download model).
- The `hidden` attribute is the gate for every conditional surface and must always win
  (`[hidden] { display: none !important }`) over `display: grid/flex`.

## 7. Do's and Don'ts

**Do**
- Keep body text on the opaque content tier or solid cards; verify ≥4.5:1.
- Reserve teal for action/selection/progress; use the blue ring for focus.
- Prefer native control vocabulary and grouped inset rows.
- Preserve the JS hook contract (ids + `.source-tab`/`.source-panel`/`.dropzone`/
  `.waveform`/`.bar`/`.readout`/`.spinner`) when restyling.

**Don't**
- Put text on the translucent chrome or directly over the desktop.
- Use cheap glassmorphism tropes: chromatic aberration, iridescent gradients,
  decorative blur, or low-contrast "frosted" text.
- Add nested cards, or surface every control at once.
- Switch the accent to system blue, or use teal for focus.
- Claim a measured GPU percent without a real source; keep the on-device promise honest.

## 8. Fixed product contract

The engine is **whisper.cpp + large-v3**, fully on-device. The model is **not bundled**;
the app downloads it on first run into Application Support (resumable, checksum-verified).
Any redesign must preserve this flow and the install → download → transcribe journey.

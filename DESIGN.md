---
name: Local Transcript
description: A quiet local utility for long-running high-accuracy transcription jobs.
colors:
  canvas: "#e7eaee"
  surface: "#ffffff"
  surface-2: "#f4f6f8"
  inset: "#f7f9fb"
  ink: "#0e1726"
  muted: "#5b6677"
  line: "#dde2ea"
  accent: "#0b7f68"
  accent-deep: "#075f4e"
  accent-soft: "#e4f3ee"
  danger: "#b42318"
  focus: "#2563eb"
typography:
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, sans-serif"
    fontSize: "22px"
    fontWeight: 680
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  section-title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 660
    lineHeight: 1.25
    letterSpacing: "-0.006em"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, sans-serif"
    fontSize: "11.5px"
    fontWeight: 640
    lineHeight: 1.35
    letterSpacing: "0.04em"
    textTransform: "uppercase"
  mono:
    fontFamily: "ui-monospace, SF Mono, SFMono-Regular, Menlo, Consolas, monospace"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "48px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "44px"
---

# Design System: Local Transcript

## 1. Overview

**Creative North Star: "The Local Control Room"**

Local Transcript is a focused product interface for supervising long-running transcription work. It should feel calm, readable, and operational rather than promotional. The visual language uses a light neutral work surface, one restrained teal accent, strong text contrast, and compact information panels.

The interface rejects decorative AI-product tropes: no purple gradients, no glass cards, no hero storytelling, no nested-card composition, and no oversized marketing metrics. The job is to help the user start, monitor, pause, resume, stop, and collect transcription work.

**Key Characteristics:**
- Product UI, not a landing page.
- Light, quiet, high-contrast surface (with a matching dark theme that follows `prefers-color-scheme`).
- System font stack for fast loading and native feel (SF Pro on macOS via `system-ui`).
- One accent color reserved for primary action, current state, and progress — never for focus (focus is blue, see the One Accent Rule).
- Stable dimensions for controls, metrics, and log output; numeric readouts use tabular numerals.

## 2. Colors

The palette is restrained: cool neutral surfaces with a single deep teal accent for action and progress.

### Primary
- **Operational Teal** (`#0b7f68`): Primary action, progress fill, active dropzone state, and selected operational emphasis.
- **Deep Operational Teal** (`#075f4e`): Primary hover state and stronger active affordance.

### Neutral — Layered

Depth comes from three tonal layers (the implementation of the Flat-By-Default Rule), not shadows:

- **Canvas** (`#e7eaee`): Page background; cool and non-tinted, sits a step below the surface so panels read as lifted without a shadow.
- **Surface White** (`#ffffff`): Forms, progress panels, controls, download links.
- **Second Neutral** (`#f4f6f8`): Toolbars/rails and quiet button fills.
- **Inset** (`#f7f9fb`): Recessed instrument surfaces — dropzone, waveform, readout cells, the progress track. This is the "gauge" layer.
- **Ink** (`#0e1726`): Primary text. **Label Ink** (`#4a5667`): instrument/field captions.
- **Muted Slate** (`#5b6677`): Secondary metadata.
- **Divider Slate** (`#dde2ea`, strong `#c6cedb`): Borders, separators, and the hairlines between readout cells.

(The dark theme mirrors these as canvas `#0b0e0d` → surface `#141a18` → inset `#101714`, with a brighter teal `#2fd1aa`.)

### Tertiary
- **Danger Red** (`#b42318`): Terminate action and failed status only.
- **Focus Blue** (`#2563eb` light / `#7aa7ff` dark): Keyboard focus outline. Deliberately a different hue from teal so a focus ring is never mistaken for the active/selected accent state. Replaces the earlier `#8eb8ff`, which was too low-contrast to serve as a visible indicator.

### Named Rules

**The One Accent Rule.** Teal is used for the one current action or current job state. It should not become decoration, and it is **not** used for focus — focus is blue.

**The No Black Box Rule.** If the model is running, the UI must show visible state: progress, elapsed time, remaining estimate, save path, and system pressure.

## 3. Typography

**Display Font:** System sans-serif stack.
**Body Font:** System sans-serif stack.
**Label/Mono Font:** System sans-serif stack for UI, system monospace for logs.

**Character:** Native, direct, and functional. Typography should support scanning and repeated use rather than brand expression.

### Hierarchy
- **Title** (680, 22px, 1.2, -0.012em): App title only.
- **Section Title** (660, 16px, 1.25): Job status and compact panel headings.
- **Body** (400, 15px, 1.5): Form text, metadata, status text, and readable UI copy.
- **Field Label** (640, 11.5px, uppercase, +0.04em): Form field labels (Language, Output, …).
- **Instrument Label** (640, 10.5px, uppercase, +0.07em): Captions inside readout cells (DONE, CPU, …).

### Named Rules

**The Product Scale Rule.** Do not use hero-scale typography in this tool. The app should feel ready for repeated operational use; the operational scale above is intentionally tighter than display type.

**The Instrument Numerals Rule.** Every numeric readout — the recording timer, percent done, remaining/elapsed, and the CPU/RAM/Load cells — uses `font-variant-numeric: tabular-nums` so digits don't jitter as values update. Logs and paths use the monospace family.

## 4. Elevation

The system is flat by default. Depth is conveyed through tonal layering, borders, and spacing rather than shadows. This keeps the utility precise and avoids the ghost-card pattern.

### Shadow Vocabulary

One shadow token exists: `--shadow-pop`, used **only** on the install dialog (a true overlay). Panels, controls, inputs, buttons, and the status pill carry no shadow — they separate via the canvas→surface→inset tonal layering and 1px borders. Small concentric glows on the status/record LED dots and the keyboard focus ring are indicators, not elevation, and are allowed.

### Named Rules

**The Flat-By-Default Rule.** Panels and controls use borders and surface contrast. Shadows are reserved for true overlays (currently just the install dialog).

## 5. Components

### Buttons
- **Shape:** 8px radius.
- **Primary:** **Solid** Operational Teal (no gradient), white text, 50px height, full-width in the upload form.
- **Hover / Active:** Teal deepens on hover; 1px downward translate on `:active`. No shadow.
- **Secondary:** Surface white, slate border, ink text, 42px height (44px on mobile touch).
- **Danger:** Pale red background, red border, red text. Use only for termination or destructive actions.
- **Focus:** blue ring (2px outline + offset + soft halo), never teal.

### Cards / Containers
- **Corner Style:** 16px panels, 12px inner clusters, 8px controls.
- **Background:** Surface White on Canvas.
- **Shadow Strategy:** No shadows (overlay dialog excepted).
- **Border:** Divider Slate 1px.
- **Internal Padding:** ~22px for main panels, 12-14px for readout cells.
- **No nested cards:** see the readout-cluster pattern below — grouped data is one bordered container divided by hairlines, never a grid of individually-bordered boxes.

### Readout Clusters (de-carded instrument groups)

Grouped operational data — advanced settings, progress metrics, system metrics — renders as a **single** bordered, rounded container whose cells are separated by 1px hairlines (cells sit on the divider color with a 1px gap; each cell fills with the inset tone). This reads as one instrument cluster and satisfies the no-nested-cards rule. Each cell is an uppercase Instrument Label over a tabular value.

### Icons

Inline stroke SVG (Lucide-style, 1.75 stroke, `currentColor`) for source selectors and affordances. **No emoji as icons.** Icons inherit muted ink at rest and the accent when their control is active.

### Inputs / Fields
- **Style:** Surface white, slate border, 8px radius, 44px height for text/select controls; selects use a custom chevron.
- **Focus:** 2px blue outline + 2px offset + soft halo.
- **Text Handling:** Long filenames and paths must wrap with `overflow-wrap: anywhere`.

### Progress And Metrics
- **Progress Bar:** Teal fill on an inset track with a 1px border. Animate with transform, not width.
- **Metrics:** Done, remaining, elapsed, CPU, RAM, load, and GPU use a fixed readout cluster (above) to avoid layout shifts; values are tabular.
- **Logs:** Dark monospace area with bounded height and scroll.
- **The monitor panel is gated by the `hidden` attribute** until a job starts; any `display` set on it must be paired with a `[hidden]` guard.

### Source Workspace

Use a compact source rail inspired by macOS Voice Memos: File, URL, and Live act as source selectors, while the active detail pane shows the current source controls. Live recording should use a timer and waveform-like strip to make recording state legible without decorative motion. Keep the app single-screen unless a future workflow genuinely needs another route.

## 6. Do's and Don'ts

### Do:
- **Do** keep source selection, file/URL/live recording inputs, settings, progress, controls, metrics, paths, logs, and downloads on one task-focused screen.
- **Do** use the teal accent for primary action, progress, and focus-related emphasis only.
- **Do** preserve native form controls unless a custom control solves a real workflow problem.
- **Do** keep text wrapping safe for long filenames, folders, and transcript terms.
- **Do** document any new control, output format, model choice, or quality setting in `CONTEXT.md` and the relevant local `SKILL.md`.

### Don't:
- **Don't** use purple gradients, gradient text, glassmorphism, decorative blur, decorative illustration, or hero-metric layouts.
- **Don't** put cards inside cards.
- **Don't** add a marketing landing page before the actual upload workflow.
- **Don't** expose model quality knobs unless the user asks; day-1 quality settings are fixed.
- **Don't** claim numeric GPU percent unless a real measured source is added.

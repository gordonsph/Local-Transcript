---
name: Local Transcript
description: A quiet local utility for long-running high-accuracy transcription jobs.
colors:
  background: "#f6f7f8"
  surface: "#ffffff"
  ink: "#111827"
  muted: "#667085"
  line: "#d7dde5"
  accent: "#0b7f68"
  accent-deep: "#075f4e"
  danger: "#b42318"
  focus: "#8eb8ff"
typography:
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "28px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "0"
  section-title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "18px"
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: "0"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 560
    lineHeight: 1.35
    letterSpacing: "0"
rounded:
  md: "8px"
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
- Light, quiet, high-contrast surface.
- System font stack for fast loading and native feel.
- One accent color reserved for primary action, focus, and progress.
- Stable dimensions for controls, metrics, and log output.

## 2. Colors

The palette is restrained: cool neutral surfaces with a single deep teal accent for action and progress.

### Primary
- **Operational Teal** (`#0b7f68`): Primary action, progress fill, active dropzone state, and selected operational emphasis.
- **Deep Operational Teal** (`#075f4e`): Primary hover state and stronger active affordance.

### Neutral
- **Workspace Background** (`#f6f7f8`): Page background; neutral and non-tinted enough to avoid the beige/paper default.
- **Surface White** (`#ffffff`): Forms, progress panels, metric cells, controls, and transcript download links.
- **Ink** (`#111827`): Primary text.
- **Muted Slate** (`#667085`): Secondary metadata and non-critical labels.
- **Divider Slate** (`#d7dde5`): Borders and separators.

### Tertiary
- **Danger Red** (`#b42318`): Terminate action and failed status only.
- **Focus Blue** (`#8eb8ff`): Keyboard focus outline.

### Named Rules

**The One Accent Rule.** Teal is used for the one current action or current job state. It should not become decoration.

**The No Black Box Rule.** If the model is running, the UI must show visible state: progress, elapsed time, remaining estimate, save path, and system pressure.

## 3. Typography

**Display Font:** System sans-serif stack.
**Body Font:** System sans-serif stack.
**Label/Mono Font:** System sans-serif stack for UI, system monospace for logs.

**Character:** Native, direct, and functional. Typography should support scanning and repeated use rather than brand expression.

### Hierarchy
- **Title** (650, 28px, 1.2): App title only.
- **Section Title** (650, 18px, 1.25): Job status and compact panel headings.
- **Body** (400, 16px, 1.45): Form text, metadata, status text, and readable UI copy.
- **Label** (560, 14px, 1.35): Field labels and compact controls.
- **Metric Label** (400, 12px): Metric captions inside fixed status cells.

### Named Rules

**The Product Scale Rule.** Do not use hero-scale typography in this tool. The app should feel ready for repeated operational use.

## 4. Elevation

The system is flat by default. Depth is conveyed through tonal layering, borders, and spacing rather than shadows. This keeps the utility precise and avoids the ghost-card pattern.

### Shadow Vocabulary

No default box-shadow token is used. If a future modal is added, use a small structural shadow only for the modal surface and document it here.

### Named Rules

**The Flat-By-Default Rule.** Panels and controls use borders and surface contrast. Shadows are reserved for true overlays.

## 5. Components

### Buttons
- **Shape:** 8px radius.
- **Primary:** Operational Teal background, white text, 48px minimum height, full-width in the upload form.
- **Hover / Focus:** Teal deepens on hover. Focus uses the shared blue outline.
- **Secondary:** White background, slate border, ink text, 40px minimum height.
- **Danger:** Pale red background, red border, red text. Use only for termination or destructive actions.

### Cards / Containers
- **Corner Style:** 8px radius.
- **Background:** Surface White on Workspace Background.
- **Shadow Strategy:** No default shadows.
- **Border:** Divider Slate 1px.
- **Internal Padding:** 18-20px for main panels, 10-12px for metric cells.

### Inputs / Fields
- **Style:** White background, slate border, 8px radius, 44px height for text/select controls.
- **Focus:** 3px blue focus outline with 2px offset.
- **Text Handling:** Long filenames and paths must wrap with `overflow-wrap: anywhere`.

### Progress And Metrics
- **Progress Bar:** Teal fill on slate track. Animate with transform, not width.
- **Metrics:** Done, remaining, elapsed, CPU, RAM, load, and GPU use fixed cells to avoid layout shifts.
- **Logs:** Dark monospace area with bounded height and scroll.

### Navigation

There is no navigation yet. Keep the app single-screen until there is a real second workflow.

## 6. Do's and Don'ts

### Do:
- **Do** keep the upload, settings, progress, controls, metrics, path, logs, and downloads on one task-focused screen.
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

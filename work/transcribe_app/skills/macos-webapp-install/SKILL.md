# macOS Web App Install

Use this skill when changing the Local Transcript install-as-web-app option, manifest metadata, app icon, or user-facing Dock installation guidance.

## Product Goal

Local Transcript runs at a stable local URL, but the user should be able to launch it like a Mac app from the Dock or Spotlight.

Stable URL:

```text
http://127.0.0.1:5057/
```

## Implementation Shape

Keep this lightweight:

- `static/manifest.webmanifest` for install metadata.
- `static/app-icon.svg` for a local app icon.
- HTML `<link rel="manifest">`, `<link rel="icon">`, and `theme-color`.
- A native `<dialog>` opened from the `Install app` button with browser-specific macOS steps.

Do not add Electron, Tauri, a native wrapper, or a build step unless the user explicitly asks.

## Browser Reality

A local website cannot silently add itself to the macOS Dock. The app can expose metadata and instructions; the final install/add-to-Dock step must be completed by the user in the browser.

Current macOS flows:

- Safari: open the site, then use File or Share > Add to Dock > Add.
- Chrome: open the site, then use More > Cast, save, and share > Install page as app.

Chrome may expose a `beforeinstallprompt` event when the browser considers the page installable. Treat that prompt as optional enhancement; always keep manual steps visible.

## Verification

After changes, run:

```sh
node --check work/transcribe_app/static/app.js
node .agents/skills/impeccable/scripts/detect.mjs --json work/transcribe_app/templates/index.html work/transcribe_app/static/styles.css work/transcribe_app/static/app.js
```

Manual QA:

- Open the app at `http://127.0.0.1:5057/`.
- Click `Install app`.
- Confirm the dialog opens, closes, and wraps on mobile widths.
- Confirm `manifest.webmanifest` is served at `/static/manifest.webmanifest`.

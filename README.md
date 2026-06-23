<p align="center">
  <img src="work/transcribe_app/static/app-icon.svg" alt="Local Transcript app icon" width="88">
</p>

<h1 align="center">Local Transcript</h1>

<p align="center"><strong>Free, on-device transcription for Mac.</strong><br>
Turn audio, video, URLs, or live recordings into accurate text — fully offline. Your audio never leaves your Mac.</p>

<p align="center">
  <a href="https://github.com/gordonsph/Local-Transcript/releases/latest"><img src="https://img.shields.io/github/v/release/gordonsph/Local-Transcript?label=Download&color=0b7f68" alt="Download latest release"></a>
  <img src="https://img.shields.io/badge/macOS-Apple%20Silicon-black?logo=apple&logoColor=white" alt="macOS Apple Silicon">
  <a href="https://github.com/gordonsph/Local-Transcript/releases"><img src="https://img.shields.io/github/downloads/gordonsph/Local-Transcript/total?label=downloads&color=0b7f68" alt="Total downloads"></a>
  <img src="https://img.shields.io/badge/100%25-on--device-2faf6a" alt="100% on-device">
</p>

<p align="center">
  <img src="docs/local-transcript-ui.jpg" alt="Local Transcript — native macOS app transcribing audio on-device" width="820">
</p>

<p align="center">
  <a href="https://github.com/gordonsph/Local-Transcript/releases/latest"><b>⬇&nbsp; Download for macOS (Apple Silicon)</b></a>
  &nbsp;·&nbsp; Free &nbsp;·&nbsp; No account &nbsp;·&nbsp; <a href="docs/INSTALL.md">Install guide</a>
</p>

---

## What is Local Transcript?

**Local Transcript is a free, open-source macOS app that transcribes audio and video entirely on your Mac.** It runs OpenAI's Whisper `large-v3` model on-device through `whisper.cpp` with Apple Metal GPU acceleration — so your recordings are never uploaded to a server. It transcribes Cantonese, Mandarin/Chinese, English, Japanese, Korean, French, and Spanish (or auto-detects), with especially strong Cantonese and Chinese results.

## Why Local Transcript

- **🔒 Private by design.** Transcription runs locally. The only time it touches the network is a one-time model download.
- **💸 Free, no subscription.** No account, no per-minute fees, no telemetry.
- **🎯 Cloud-grade accuracy.** The full Whisper `large-v3` model — not a cut-down version — accelerated by Apple Metal.
- **🗣️ Strong Cantonese & Chinese** — where many tools fall short — plus English, Mandarin, Japanese, Korean, French, and Spanish.
- **📄 Six export formats.** Markdown, SRT, VTT, CSV, JSON, and plain text — subtitles included.
- **🎙️ Three sources.** A file, a media URL, or a live microphone recording.

## Local Transcript vs. the alternatives

| | **Local Transcript** | Cloud tools (Otter, Rev…) | Raw `whisper.cpp` CLI |
|---|:---:|:---:|:---:|
| Audio stays on your Mac | ✅ Always | ❌ Uploaded | ✅ |
| Price | ✅ Free | 💸 Subscription | ✅ Free |
| Works fully offline | ✅ | ❌ | ✅ |
| Whisper large-v3 accuracy | ✅ | ⚠️ Varies | ✅ |
| Cantonese / Chinese focus | ✅ | ⚠️ Weak | ✅ |
| Native Mac app, no terminal | ✅ | ✅ | ❌ |
| Subtitles (SRT/VTT) & 6 formats | ✅ | ⚠️ Some | ⚠️ Manual |

## Download & install

1. **[Download the latest `.dmg`](https://github.com/gordonsph/Local-Transcript/releases/latest)**, open it, and drag the app onto your **Applications** folder. Launch it from Applications (not from the disk image).
2. **First launch:** because the app is free and not notarized by Apple, macOS asks you to confirm you trust it. Open **System Settings → Privacy & Security**, then click **Open Anyway**. *(One time only. Older macOS: right-click the app → Open → Open.)*
3. **Download the model:** on first open, click **Download** to fetch the Whisper `large-v3` model — a one-time **2.9 GB** download, checksum-verified and stored on your Mac. After that, everything runs offline.

Full walkthrough: **[docs/INSTALL.md](docs/INSTALL.md)**.

## How it works

1. Pick a **File**, paste a **URL**, or record **Live** from your microphone.
2. Choose the **language** and **output format**.
3. Click **Start transcript**. Results are saved to your chosen folder and listed for download when the job finishes.

Live recordings are saved alongside their transcript, so you keep both.

## Features

- **Sources:** audio/video file · media URL · live microphone recording
- **Languages:** Cantonese, Mandarin/Chinese, English, Japanese, Korean, French, Spanish, and auto-detect
- **Formats:** Markdown · SRT · VTT · CSV · JSON · plain text
- **Engine:** `whisper.cpp` + Whisper `large-v3`, Apple Metal GPU acceleration
- **Terminology hints:** bias decoding toward names, jargon, and acronyms
- **On-device:** no account, no cloud, no telemetry

## FAQ

**Is my audio really private?**
Yes. Transcription runs locally on your Mac via `whisper.cpp` and Metal. The only network request the app makes is the one-time model download from Hugging Face. Your recordings are never uploaded.

**Is it free?**
Yes — free and open-source. No account, no subscription, no usage limits.

**Does it transcribe Cantonese and Chinese?**
Yes. Cantonese and Chinese were the original focus. It also handles English, Mandarin, Japanese, Korean, French, Spanish, and auto-detect.

**Which Macs are supported?**
Apple Silicon Macs (M1 or later) on macOS 11 or newer. Intel Macs are not supported.

**Why does macOS say the app can't be opened?**
Because it's free and not signed with a paid Apple Developer certificate. Approve it once via System Settings → Privacy & Security → **Open Anyway**. See the [install guide](docs/INSTALL.md).

**How much disk space do I need?**
About 4 GB free for the one-time 2.9 GB Whisper `large-v3` model.

**Does it work offline?**
Yes — after the one-time model download, transcription runs entirely offline.

**What can I export?**
Markdown, SRT, VTT, CSV, JSON, and plain text — so you can use it for notes, subtitles, or data.

## Privacy

All transcription runs locally via `whisper.cpp` + Apple Metal. Audio never leaves your Mac. The only network request is the one-time model download from Hugging Face.

## Build from source

Developers can build the app bundle and DMG from this repo:

```sh
work/release.sh   # builds Local Transcript.app, ad-hoc signs it, and packages the DMG
```

The build relocates a portable `whisper.cpp` runtime into the bundle and packages it with py2app. The 2.9 GB model is **not** bundled — the app downloads it on first launch.

## Requirements

- Apple Silicon Mac (M1 or later), macOS 11+
- ~4 GB free disk space for the model
- Internet for the one-time model download
- Microphone permission (only for live recording)

---

<p align="center"><sub>Runs on <a href="https://github.com/ggml-org/whisper.cpp">whisper.cpp</a> with OpenAI's Whisper <code>large-v3</code> model · 100% on-device · made for Mac</sub></p>

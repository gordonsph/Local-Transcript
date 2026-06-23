# Product Marketing Context

*Last updated: 2026-06-24*

## Product Overview
**One-liner:** Free, on-device transcription app for Mac — turn audio, video, or live recordings into text without uploading anything.
**What it does:** Local Transcript runs OpenAI's Whisper large-v3 model entirely on your Apple Silicon Mac (GPU-accelerated via Metal). You give it a file, a media URL, or a live mic recording; it produces an accurate transcript in your chosen format. Audio never leaves the device.
**Product category:** on-device / offline / private transcription app for macOS. People search for "offline transcription Mac," "private transcription app," "free Mac transcription," "Cantonese transcription," "Whisper app for Mac."
**Product type:** Free, open-source native macOS app (.dmg download). Not SaaS, no account, no subscription.
**Business model:** Free. No paid tiers, no telemetry, no upsell.

## Target Audience
**Target users:** Privacy-conscious Mac users on Apple Silicon who need accurate transcripts and won't (or can't) upload audio to the cloud.
**Primary use case:** Transcribe interviews, meetings, lectures, voice notes, or videos locally — especially Cantonese/Chinese content that cloud tools handle poorly.
**Jobs to be done:**
- "Transcribe this sensitive recording without sending it to a third party."
- "Get an accurate Cantonese / Chinese transcript I can actually trust."
- "Subtitle a video (SRT/VTT) without a subscription."
- "Turn my voice memos into searchable text, offline."
**Use cases:** journalists/researchers (source protection), lawyers & clinicians (confidential audio), students (lectures), content creators (subtitles), bilingual HK/Cantonese users, anyone on slow/no internet.

## Problems & Pain Points
**Core problem:** Good transcription means uploading private audio to a cloud service, paying a subscription, and still getting weak results for Cantonese/Chinese.
**Why alternatives fall short:**
- Cloud tools (Otter, Rev, cloud Whisper APIs): upload your audio, charge monthly, require internet, raise privacy/compliance concerns.
- Raw `whisper.cpp` / CLI: powerful but command-line only — no model management, no formats UI, no live recording.
**What it costs them:** privacy/compliance risk, subscription fees, upload time, and re-typing bad Cantonese output.
**Emotional tension:** unease about where sensitive recordings end up; frustration that the best models are locked behind clouds or terminals.

## Competitive Landscape
**Direct (other local Mac apps):** MacWhisper — polished but paid; this is free and open.
**Secondary (cloud transcription):** Otter.ai, Rev, Descript, cloud Whisper APIs — they upload audio, cost money, need internet.
**Indirect:** raw `whisper.cpp` CLI / Python scripts — capable but not user-friendly; manual model + format handling.

## Differentiation
**Key differentiators:**
- 100% on-device — audio never leaves the Mac; the only network call is the one-time model download.
- Free and open-source — no account, no subscription, no telemetry.
- Full Whisper **large-v3** (not a distilled/small model), GPU-accelerated via Apple Metal.
- Strong Cantonese / Chinese support (the product's origin focus), plus English, Mandarin, Japanese, Korean, French, Spanish, and auto-detect.
- File, URL, and live-mic sources; six output formats (Markdown, SRT, VTT, CSV, JSON, plain text).
**Why customers choose us:** they want cloud-grade accuracy with zero cloud — private, free, and good at Cantonese.

## Objections
| Objection | Response |
|-----------|----------|
| "Is it really private?" | Yes — transcription runs locally via whisper.cpp + Metal. The only network request is the one-time 2.9 GB model download from Hugging Face. |
| "Why does macOS warn it's unverified?" | It's free and not notarized by Apple. One-time "Open Anyway" in System Settings → Privacy & Security; documented in the install guide. |
| "Is it accurate enough?" | It runs the full Whisper large-v3 model — the same large model behind many cloud services — locally. |
| "Will it run on my Mac?" | Apple Silicon (M1 or later), macOS 11+. Intel Macs are not supported. |

**Anti-persona:** Intel-Mac or Windows users; teams needing real-time live captioning or multi-user cloud collaboration.

## Customer Language
**How they describe the problem:** "I don't want to upload my interviews," "Otter is expensive," "nothing transcribes Cantonese well," "I just want it on my Mac."
**Words to use:** on-device, private, offline, free, Whisper large-v3, Cantonese, Apple Silicon, no subscription, audio never leaves your Mac.
**Words to avoid:** cloud, upload, account, subscription, "AI-powered" fluff, "revolutionary," "forever."

## Brand Voice
**Tone:** plain, confident, calm — like Apple's own system copy.
**Style:** direct, specific, terse. No marketing fluff or hype.
**Personality:** trustworthy, private, technical-but-approachable, no-nonsense.

## Proof Points
**Factual specifics (no fabricated metrics/testimonials):** runs Whisper large-v3 on-device; Apple Metal GPU acceleration; one-time 2.9 GB model; six output formats; eight language options + auto-detect; open source.

## Goals
**Business goal:** adoption by privacy-conscious and Cantonese/Chinese Mac users; GitHub stars + release downloads.
**Conversion action:** download the latest `.dmg` from GitHub Releases and run a first transcript.

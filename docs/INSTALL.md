# Installing Local Transcript

Local Transcript is a free, on-device transcription app for **Apple Silicon Macs**
(M1 or later), running whisper.cpp with the Whisper large-v3 model. Everything stays
on your Mac — nothing is uploaded.

It is distributed **without an Apple Developer signature** (it's free), so macOS will
ask you to confirm you trust it the first time. This is a one-time, three-step
approval.

## 1. Move it to Applications
Open `Local Transcript.dmg` and **drag the app onto the Applications shortcut.**

> Important: launch it from **Applications**, not from the disk image or Downloads.
> macOS runs apps from temporary locations in a locked-down mode that prevents this
> app from starting its engine.

## 2. First launch — approve it
1. Open **Local Transcript** from Applications. macOS will say it "cannot be opened
   because Apple cannot check it for malicious software." Click **Done**.
2. Open **System Settings → Privacy & Security**, scroll down, and next to
   "Local Transcript was blocked" click **Open Anyway**.
3. Confirm with **Open**. (You only do this once.)

*On older macOS you can instead right-click the app → **Open** → **Open**.*

## 3. Download the model (one time)
The first time it opens, Local Transcript will offer to download the Whisper large-v3
model — a **one-time 2.9 GB download** stored on your Mac. Click **Download model**
and wait for it to finish (it resumes if interrupted and is checksum-verified). After
that, transcription works fully offline, forever.

## Using it
Choose a **File**, paste a **URL**, or record **Live** from the microphone; pick a
language and output format; click **Start transcript**. Results are saved to your
chosen folder and listed for download when the job finishes.

## Requirements
- Apple Silicon Mac (M1 or later), macOS 11+
- ~4 GB free disk space for the model
- Internet access for the one-time model download
- Microphone permission (only for Live recording)

## Privacy
All transcription runs locally via whisper.cpp + Metal. Audio never leaves your Mac.
The only network request is the one-time model download from Hugging Face.

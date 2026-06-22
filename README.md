# Local Transcript

<p align="center">
  <img src="work/transcribe_app/static/app-icon.svg" alt="Local Transcript logo" width="96">
</p>

<p align="center">
  <img src="docs/local-transcript-ui.jpg" alt="Local Transcript app UI">
</p>

Local Transcript is a private macOS app for turning audio, video, URLs, or live
microphone recordings into transcripts. It runs locally with `whisper.cpp` and
the full `large-v3` model.

Stable app URL:

```text
http://127.0.0.1:5057/
```

## Requirements

- macOS
- Internet access for the first setup
- Enough disk space for the runtime and model files
- Microphone permission in the browser for Live recording

## First-Time Setup

Open Terminal in the project folder, then run:

```sh
work/setup_new_mac.sh
```

The first setup can take a while. It installs the local runtime, builds
`whisper.cpp`, downloads the `large-v3` model, installs the macOS background
service, and checks that the app is ready.

When setup finishes, open:

```text
http://127.0.0.1:5057/
```

## Add To Dock

Open `http://127.0.0.1:5057/`, then click `Install app` in the app header.

Safari:

```text
File > Add to Dock > Add
```

Chrome:

```text
... > Cast, save, and share > Install page as app
```

After this, launch Local Transcript from the Dock like a normal Mac app.

## First Transcript

1. Open Local Transcript from the Dock or go to `http://127.0.0.1:5057/`.
2. Choose `File`, `URL`, or `Live`.
3. Pick the language and output format.
4. Click the main action button to start.
5. Download the transcript when the job finishes.

Live recordings are saved locally before transcription, so both the recording and
the transcript are kept.

## Saved Files

Installed app data is stored here:

```text
~/Library/Application Support/LocalTranscript/
```

Transcripts:

```text
~/Library/Application Support/LocalTranscript/outputs/transcribe_app/results/
```

Uploaded files, URL downloads, and Live recordings:

```text
~/Library/Application Support/LocalTranscript/outputs/transcribe_app/jobs/<job-id>/source/
```

## Check Status

Open:

```text
http://127.0.0.1:5057/api/health
```

Or run:

```sh
curl --max-time 5 -s http://127.0.0.1:5057/api/health
```

A ready app shows:

```json
{"ready": true, "vad": true}
```

## If It Does Not Open

Run:

```sh
work/install_persistent_local_transcript.sh
```

Then open:

```text
http://127.0.0.1:5057/
```

Logs are stored here:

```text
~/Library/Application Support/LocalTranscript/work/transcribe_app/logs/
```

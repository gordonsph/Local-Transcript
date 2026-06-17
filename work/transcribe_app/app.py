from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import signal
import threading
import time
import uuid
import wave
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import av
import numpy as np
from flask import Flask, jsonify, render_template, request, send_file
from opencc import OpenCC
from werkzeug.utils import secure_filename


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("LOCAL_TRANSCRIPT_ROOT", DEFAULT_ROOT)).expanduser().resolve()
APP_ROOT = ROOT / "work" / "transcribe_app"
OUTPUT_ROOT = ROOT / "outputs" / "transcribe_app"
DEFAULT_RESULT_ROOT = OUTPUT_ROOT / "results"
WHISPER_ROOT = ROOT / "work" / "whisper.cpp"
WHISPER_CLI = WHISPER_ROOT / "build" / "bin" / "whisper-cli"
MODEL_PATH = WHISPER_ROOT / "models" / "ggml-large-v3.bin"
VAD_MODEL_PATH = WHISPER_ROOT / "models" / "ggml-silero-v6.2.0.bin"
LOCAL_LARGE_V3_REALTIME_FACTOR = 2.4
MODEL_STARTUP_SECONDS = 60

LANGUAGES = {
    "auto": "Auto detect",
    "yue": "Cantonese",
    "zh": "Mandarin / Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "es": "Spanish",
}

FORMATS = {
    "all": "All formats",
    "md": "Markdown",
    "srt": "SRT",
    "vtt": "VTT",
    "csv": "CSV",
    "json": "JSON",
    "txt": "Text",
}

app = Flask(
    __name__,
    template_folder=str(APP_ROOT / "templates"),
    static_folder=str(APP_ROOT / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024 * 1024


@dataclass
class Job:
    id: str
    status: str = "queued"
    message: str = "Queued"
    language: str = "yue"
    output_format: str = "all"
    output_location: str = ""
    terminology: str = ""
    progress: float = 0.0
    progress_source: str = "pending"
    audio_duration_seconds: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float | None = None
    transcribe_started_at: float = 0.0
    estimated_total_seconds: float = 0.0
    paused_at: float = 0.0
    total_paused_seconds: float = 0.0
    process_pid: int | None = None
    cancel_requested: bool = False
    system: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    log: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    last_status_save: float = 0.0


jobs: dict[str, Job] = {}
jobs_lock = threading.Lock()
cc = OpenCC("s2hk")


def job_dir(job_id: str) -> Path:
    return OUTPUT_ROOT / "jobs" / job_id


def resolve_output_location(raw: str = "") -> Path:
    value = (raw or "").strip()
    if not value:
        return DEFAULT_RESULT_ROOT
    expanded = Path(value).expanduser()
    if not expanded.is_absolute():
        expanded = ROOT / expanded
    return expanded.resolve()


def result_dir(job_id: str, output_location: str = "") -> Path:
    return resolve_output_location(output_location) / job_id


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / float(audio.getframerate())


def initial_runtime_estimate(audio_duration: float) -> float:
    return MODEL_STARTUP_SECONDS + audio_duration * LOCAL_LARGE_V3_REALTIME_FACTOR


def system_snapshot(pid: int | None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    try:
        load1, load5, load15 = os.getloadavg()
        snapshot["load"] = {"1m": round(load1, 2), "5m": round(load5, 2), "15m": round(load15, 2)}
        snapshot["cpu_count"] = os.cpu_count() or 0
    except Exception:
        pass

    if pid:
        try:
            output = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "%cpu=,%mem=,rss=,etime="],
                text=True,
                timeout=2,
            ).strip()
            if output:
                parts = output.split(None, 3)
                if len(parts) >= 4:
                    snapshot["process"] = {
                        "cpu_percent": float(parts[0]),
                        "mem_percent": float(parts[1]),
                        "rss_mb": round(float(parts[2]) / 1024, 1),
                        "elapsed": parts[3],
                    }
        except Exception:
            pass

    try:
        vm = subprocess.check_output(["vm_stat"], text=True, timeout=2)
        page_size_match = re.search(r"page size of (\d+) bytes", vm)
        page_size = int(page_size_match.group(1)) if page_size_match else 4096
        values: dict[str, int] = {}
        for line in vm.splitlines():
            if ":" not in line:
                continue
            key, raw = line.split(":", 1)
            number = re.sub(r"[^0-9]", "", raw)
            if number:
                values[key.strip()] = int(number)
        free_pages = values.get("Pages free", 0) + values.get("Pages speculative", 0)
        active_pages = values.get("Pages active", 0)
        wired_pages = values.get("Pages wired down", 0)
        compressed_pages = values.get("Pages occupied by compressor", 0)
        used_mb = round((active_pages + wired_pages + compressed_pages) * page_size / 1024 / 1024, 1)
        free_mb = round(free_pages * page_size / 1024 / 1024, 1)
        snapshot["memory"] = {"used_mb": used_mb, "free_mb": free_mb}
    except Exception:
        pass

    return snapshot


def processing_elapsed(job: Job, now: float | None = None) -> float:
    if not job.transcribe_started_at:
        return job.elapsed_seconds
    now = now or time.time()
    paused_seconds = job.total_paused_seconds
    if job.status == "paused" and job.paused_at:
        paused_seconds += max(0.0, now - job.paused_at)
    return max(0.0, now - job.transcribe_started_at - paused_seconds)


def eta_from_progress(progress: float, elapsed: float, samples: list[tuple[float, float]], fallback_total: float) -> float:
    now = time.time()
    if progress <= 0:
        return max(0.0, fallback_total - elapsed)

    global_eta = elapsed * max(0.0, 100.0 - progress) / max(progress, 0.1)
    recent_eta = global_eta
    recent = [sample for sample in samples if now - sample[0] <= 300]
    if len(recent) >= 2:
        first_time, first_progress = recent[0]
        last_time, last_progress = recent[-1]
        rate = (last_progress - first_progress) / max(1.0, last_time - first_time)
        if rate > 0:
            recent_eta = max(0.0, (100.0 - progress) / rate)

    slowdown_margin = 1.25 if progress < 30 else 1.15 if progress < 70 else 1.08
    return max(global_eta, recent_eta) * slowdown_margin


def refresh_runtime_status(job: Job) -> None:
    now = time.time()
    if job.process_pid:
        job.system = system_snapshot(job.process_pid)

    if job.status not in {"running", "paused", "cancelling"} or not job.transcribe_started_at:
        job.updated_at = now
        return

    elapsed = processing_elapsed(job, now)
    job.elapsed_seconds = elapsed
    fallback_total = max(job.estimated_total_seconds or initial_runtime_estimate(job.audio_duration_seconds), 1.0)

    if job.status == "running":
        if job.progress_source == "actual" and job.progress > 0:
            job.eta_seconds = eta_from_progress(job.progress, elapsed, [], fallback_total)
        else:
            estimated_progress = min(95.0, max(job.progress, elapsed / fallback_total * 100.0))
            job.progress = estimated_progress
            job.progress_source = "estimate"
            if elapsed <= fallback_total:
                job.eta_seconds = max(1.0, fallback_total - elapsed)
            else:
                job.eta_seconds = max(30.0, eta_from_progress(job.progress, elapsed, [], fallback_total))
        job.message = f"Transcribing {job.progress:.0f}%"
    elif job.status == "paused":
        job.message = "Paused"
    elif job.status == "cancelling":
        job.message = "Cancelling"

    job.updated_at = now


def serialize_job(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "message": job.message,
        "language": job.language,
        "language_label": LANGUAGES.get(job.language, job.language),
        "output_format": job.output_format,
        "output_format_label": FORMATS.get(job.output_format, job.output_format),
        "output_location": job.output_location,
        "terminology": job.terminology,
        "progress": round(job.progress, 1),
        "progress_source": job.progress_source,
        "audio_duration_seconds": job.audio_duration_seconds,
        "elapsed_seconds": job.elapsed_seconds,
        "elapsed_label": format_duration(job.elapsed_seconds),
        "eta_seconds": job.eta_seconds,
        "eta_label": format_duration(job.eta_seconds),
        "transcribe_started_at": job.transcribe_started_at,
        "estimated_total_seconds": job.estimated_total_seconds,
        "paused_at": job.paused_at,
        "total_paused_seconds": job.total_paused_seconds,
        "process_pid": job.process_pid,
        "cancel_requested": job.cancel_requested,
        "system": job.system,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "log": job.log[-80:],
        "files": job.files,
        "error": job.error,
    }


def save_status(job: Job) -> None:
    path = job_dir(job.id) / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize_job(job), ensure_ascii=False, indent=2), encoding="utf-8")


def update_job(job_id: str, **changes: Any) -> None:
    with jobs_lock:
        job = jobs[job_id]
        for key, value in changes.items():
            setattr(job, key, value)
        job.updated_at = time.time()
        save_status(job)


def update_progress(job_id: str, progress: float, source: str, started_at: float, progress_samples: list[tuple[float, float]], fallback_total: float) -> None:
    progress = max(0.0, min(100.0, progress))
    now = time.time()
    with jobs_lock:
        job = jobs[job_id]
        pid = job.process_pid
        elapsed = processing_elapsed(job, now)
    eta = 0.0 if progress >= 100 else eta_from_progress(progress, elapsed, progress_samples, fallback_total)
    update_job(
        job_id,
        progress=progress,
        progress_source=source,
        elapsed_seconds=elapsed,
        eta_seconds=eta,
        transcribe_started_at=started_at,
        estimated_total_seconds=fallback_total,
        message=f"Transcribing {progress:.0f}%",
        system=system_snapshot(pid),
    )


def append_log(job_id: str, line: str) -> None:
    line = line.strip()
    if not line:
        return
    with jobs_lock:
        job = jobs[job_id]
        job.log.append(line)
        job.log = job.log[-200:]
        job.updated_at = time.time()
        should_save = job.updated_at - job.last_status_save > 1.0 or "progress =" in line
        if should_save:
            job.last_status_save = job.updated_at
            save_status(job)


def ensure_ready() -> None:
    missing = []
    for label, path in {
        "whisper.cpp binary": WHISPER_CLI,
        "large-v3 model": MODEL_PATH,
    }.items():
        if not path.exists():
            missing.append(f"{label}: {path}")
    if missing:
        raise RuntimeError("Missing required local files:\n" + "\n".join(missing))


def convert_audio_to_wav(src: Path, dst: Path) -> None:
    container = av.open(str(src))
    stream = next((s for s in container.streams if s.type == "audio"), None)
    if stream is None:
        raise RuntimeError("No audio stream found in uploaded file.")

    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(dst), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)

        for frame in container.decode(stream):
            converted = resampler.resample(frame)
            if converted is None:
                continue
            frames = converted if isinstance(converted, list) else [converted]
            for audio_frame in frames:
                data = audio_frame.to_ndarray()
                data = np.asarray(data, dtype=np.int16).reshape(-1)
                out.writeframes(data.tobytes())


def ts_srt(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    h, rem = divmod(millis, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ts_label(seconds: float) -> str:
    return ts_srt(seconds).replace(",", ".")


def normalize_text(text: str, language: str) -> str:
    text = text.strip()
    if language in {"yue", "zh", "auto"}:
        text = cc.convert(text)
    replacements = {
        "trusteevice": "trust device",
        "Trusteevice": "Trust device",
        "untrustified": "untrusted device",
        "trustified": "trusted device",
        "LOCKING": "login",
        "Lockin": "login",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return text


def load_segments(json_path: Path, language: str) -> list[dict[str, Any]]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    raw_segments = data.get("transcription") or data.get("segments") or []
    segments = []
    for idx, item in enumerate(raw_segments, start=1):
        offsets = item.get("offsets") or {}
        start = item.get("start")
        end = item.get("end")
        if start is None:
            start = offsets.get("from")
        if end is None:
            end = offsets.get("to")
        if start is None or end is None:
            continue
        if start > 10_000 or end > 10_000:
            start = start / 1000
            end = end / 1000
        text = normalize_text(str(item.get("text", "")), language)
        if not text:
            continue
        segments.append({"index": idx, "start": float(start), "end": float(end), "text": text})
    return segments


def write_outputs(source_name: str, segments: list[dict[str, Any]], base: Path, requested: str) -> dict[str, str]:
    files: dict[str, str] = {}

    def wants(fmt: str) -> bool:
        return requested == "all" or requested == fmt

    if wants("md"):
        path = base.with_suffix(".md")
        with path.open("w", encoding="utf-8") as f:
            f.write("# Transcript\n\n")
            f.write(f"Audio: {source_name}\n\n")
            f.write("Model: whisper.cpp large-v3\n\n")
            for seg in segments:
                f.write(f"[{ts_label(seg['start'])} - {ts_label(seg['end'])}] {seg['text']}\n\n")
        files["Markdown"] = path.name

    if wants("txt"):
        path = base.with_suffix(".txt")
        with path.open("w", encoding="utf-8") as f:
            for seg in segments:
                f.write(seg["text"] + "\n")
        files["Text"] = path.name

    if wants("srt"):
        path = base.with_suffix(".srt")
        with path.open("w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, start=1):
                f.write(f"{idx}\n{ts_srt(seg['start'])} --> {ts_srt(seg['end'])}\n{seg['text']}\n\n")
        files["SRT"] = path.name

    if wants("vtt"):
        path = base.with_suffix(".vtt")
        with path.open("w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start = ts_label(seg["start"])
                end = ts_label(seg["end"])
                f.write(f"{start} --> {end}\n{seg['text']}\n\n")
        files["VTT"] = path.name

    if wants("csv"):
        path = base.with_suffix(".csv")
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start", "end", "text"])
            for seg in segments:
                writer.writerow([ts_label(seg["start"]), ts_label(seg["end"]), seg["text"]])
        files["CSV"] = path.name

    if wants("json"):
        path = base.with_suffix(".json")
        payload = {
            "source": source_name,
            "model": "whisper.cpp large-v3",
            "segments": [
                {
                    "index": idx,
                    "start": seg["start"],
                    "end": seg["end"],
                    "start_label": ts_label(seg["start"]),
                    "end_label": ts_label(seg["end"]),
                    "text": seg["text"],
                }
                for idx, seg in enumerate(segments, start=1)
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        files["JSON"] = path.name

    if requested == "all":
        bundle = base.with_suffix(".zip")
        if bundle.exists():
            bundle.unlink()
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for filename in files.values():
                item = base.parent / filename
                zf.write(item, arcname=item.name)
        files["ZIP"] = bundle.name

    return files


def run_transcription(job_id: str, upload_path: Path, language: str, output_format: str, output_location: str, terminology: str) -> None:
    try:
        ensure_ready()
        out_dir = job_dir(job_id)
        wav_path = out_dir / "prepared.wav"
        raw_base = out_dir / "raw_whisper"
        final_dir = result_dir(job_id, output_location)
        final_dir.mkdir(parents=True, exist_ok=True)
        final_base = final_dir / "transcript"

        update_job(job_id, status="preparing", message="Preparing audio", progress=1.0, progress_source="preparing")
        convert_audio_to_wav(upload_path, wav_path)
        audio_duration = wav_duration(wav_path)
        fallback_total = initial_runtime_estimate(audio_duration)
        append_log(job_id, "Audio prepared at 16 kHz mono.")
        append_log(job_id, f"Audio duration: {format_duration(audio_duration)}.")

        started_at = time.time()
        progress_samples: list[tuple[float, float]] = []
        update_job(
            job_id,
            status="running",
            message="Loading large-v3",
            progress=2.0,
            progress_source="estimate",
            audio_duration_seconds=audio_duration,
            elapsed_seconds=0.0,
            eta_seconds=fallback_total,
            transcribe_started_at=started_at,
            estimated_total_seconds=fallback_total,
            paused_at=0.0,
            total_paused_seconds=0.0,
        )
        cmd = [
            str(WHISPER_CLI),
            "-m",
            str(MODEL_PATH),
            "-f",
            str(wav_path),
            "-l",
            language,
            "-t",
            "8",
            "-bs",
            "5",
            "-bo",
            "5",
            "-oj",
            "-ojf",
            "-of",
            str(raw_base),
            "--print-progress",
            "--suppress-nst",
        ]
        if VAD_MODEL_PATH.exists():
            cmd.extend(["--vad", "-vm", str(VAD_MODEL_PATH), "-vsd", "700"])
        if terminology.strip():
            cmd.extend(["--prompt", f"Preserve these terms exactly when spoken: {terminology.strip()}"])

        process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        update_job(job_id, process_pid=process.pid)
        assert process.stdout is not None
        progress_pattern = re.compile(r"progress\s*=\s*(\d+)%")
        for line in process.stdout:
            with jobs_lock:
                if jobs[job_id].cancel_requested:
                    process.terminate()
                    break
            append_log(job_id, line)
            match = progress_pattern.search(line)
            if match:
                progress = float(match.group(1))
                progress_samples.append((time.time(), progress))
                progress_samples = progress_samples[-30:]
                update_progress(job_id, progress, "actual", started_at, progress_samples, fallback_total)
            else:
                elapsed = time.time() - started_at
                estimated_progress = min(95.0, max(2.0, elapsed / max(fallback_total, 1.0) * 100.0))
                with jobs_lock:
                    current = jobs[job_id]
                    should_update = current.progress_source != "actual" and estimated_progress - current.progress >= 1.0
                if should_update:
                    update_progress(job_id, estimated_progress, "estimate", started_at, progress_samples, fallback_total)

        code = process.wait()
        update_job(job_id, process_pid=None)
        with jobs_lock:
            was_cancelled = jobs[job_id].cancel_requested
        if was_cancelled:
            update_job(job_id, status="cancelled", message="Cancelled", eta_seconds=0.0, process_pid=None)
            return
        if code != 0:
            raise RuntimeError(f"whisper.cpp exited with status {code}")

        raw_json = raw_base.with_suffix(".json")
        if not raw_json.exists():
            raise RuntimeError("whisper.cpp did not produce JSON output.")

        update_job(job_id, status="finalizing", message="Creating downloads", progress=98.0, progress_source="actual", eta_seconds=10)
        segments = load_segments(raw_json, language)
        files = write_outputs(upload_path.name, segments, final_base, output_format)
        append_log(job_id, f"Saved final transcripts to {final_dir}")
        with jobs_lock:
            final_elapsed = processing_elapsed(jobs[job_id]) if job_id in jobs else time.time() - started_at
        update_job(
            job_id,
            status="done",
            message="Complete",
            files=files,
            output_location=str(final_dir),
            progress=100.0,
            progress_source="actual",
            elapsed_seconds=final_elapsed,
            eta_seconds=0.0,
        )
    except Exception as exc:
        update_job(job_id, status="failed", message="Failed", error=str(exc))


@app.get("/")
def index():
    return render_template(
        "index.html",
        languages=LANGUAGES,
        formats=FORMATS,
        model_ready=MODEL_PATH.exists(),
        default_result_location=str(DEFAULT_RESULT_ROOT),
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ready": MODEL_PATH.exists() and WHISPER_CLI.exists(),
            "whisper_cli": str(WHISPER_CLI),
            "model": str(MODEL_PATH),
            "vad": VAD_MODEL_PATH.exists(),
        }
    )


@app.post("/api/jobs")
def create_job():
    file = request.files.get("audio")
    if file is None or not file.filename:
        return jsonify({"error": "Choose an audio file."}), 400

    language = request.form.get("language", "yue")
    output_format = request.form.get("format", "all")
    output_location = request.form.get("output_location", "").strip()
    terminology = request.form.get("terminology", "").strip()[:2000]
    if language not in LANGUAGES:
        return jsonify({"error": "Unsupported language."}), 400
    if output_format not in FORMATS:
        return jsonify({"error": "Unsupported output format."}), 400
    try:
        chosen_output_base = resolve_output_location(output_location)
        chosen_output_base.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return jsonify({"error": f"Cannot use result folder: {exc}"}), 400

    job_id = uuid.uuid4().hex[:12]
    out_dir = job_dir(job_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file.filename) or "audio"
    upload_path = out_dir / filename
    file.save(upload_path)

    job = Job(
        id=job_id,
        language=language,
        output_format=output_format,
        output_location=str(chosen_output_base / job_id),
        terminology=terminology,
    )
    with jobs_lock:
        jobs[job_id] = job
        save_status(job)

    thread = threading.Thread(
        target=run_transcription,
        args=(job_id, upload_path, language, output_format, str(chosen_output_base), terminology),
        daemon=True,
    )
    thread.start()
    return jsonify(serialize_job(job)), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job:
            if job.process_pid:
                refresh_runtime_status(job)
                save_status(job)
            return jsonify(serialize_job(job))

    status_path = job_dir(job_id) / "status.json"
    if status_path.exists():
        return jsonify(json.loads(status_path.read_text(encoding="utf-8")))
    return jsonify({"error": "Job not found."}), 404


@app.post("/api/jobs/<job_id>/<action>")
def control_job(job_id: str, action: str):
    if action not in {"pause", "resume", "terminate"}:
        return jsonify({"error": "Unsupported action."}), 400

    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            status_path = job_dir(job_id) / "status.json"
            if status_path.exists():
                return jsonify({"error": "This job is no longer attached to a running process."}), 409
            return jsonify({"error": "Job not found."}), 404
        pid = job.process_pid

    if not pid:
        return jsonify({"error": "No active transcription process for this job."}), 409

    try:
        if action == "pause":
            os.kill(pid, signal.SIGSTOP)
            update_job(job_id, status="paused", message="Paused", paused_at=time.time())
            append_log(job_id, "Paused transcription.")
        elif action == "resume":
            os.kill(pid, signal.SIGCONT)
            with jobs_lock:
                job = jobs[job_id]
                if job.paused_at:
                    job.total_paused_seconds += max(0.0, time.time() - job.paused_at)
                job.paused_at = 0.0
                job.status = "running"
                job.message = "Resumed"
                job.updated_at = time.time()
                save_status(job)
            append_log(job_id, "Resumed transcription.")
        else:
            with jobs_lock:
                was_paused = jobs[job_id].status == "paused"
                jobs[job_id].cancel_requested = True
            os.kill(pid, signal.SIGTERM)
            if was_paused:
                os.kill(pid, signal.SIGCONT)
            update_job(job_id, status="cancelling", message="Cancelling", cancel_requested=True)
            append_log(job_id, "Cancellation requested.")
    except ProcessLookupError:
        update_job(job_id, process_pid=None)
        return jsonify({"error": "The transcription process already exited."}), 409
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    with jobs_lock:
        return jsonify(serialize_job(jobs[job_id]))


@app.get("/download/<job_id>/<path:filename>")
def download(job_id: str, filename: str):
    safe_name = Path(filename).name
    status_path = job_dir(job_id) / "status.json"
    output_location = ""
    with jobs_lock:
        job = jobs.get(job_id)
        if job:
            output_location = job.output_location
    if not output_location and status_path.exists():
        output_location = json.loads(status_path.read_text(encoding="utf-8")).get("output_location", "")

    search_dirs = []
    if output_location:
        search_dirs.append(Path(output_location))
    search_dirs.append(job_dir(job_id))
    path = next((folder / safe_name for folder in search_dirs if (folder / safe_name).is_file()), job_dir(job_id) / safe_name)
    if not path.exists() or not path.is_file():
        return jsonify({"error": "File not found."}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5057"))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)

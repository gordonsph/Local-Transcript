from __future__ import annotations

import csv
import ipaddress
import json
import os
import socket
import re
import shutil
import subprocess
import signal
import sys
import threading
import time
import uuid
import wave
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import HTTPRedirectHandler, build_opener

import av
import numpy as np
from flask import Flask, jsonify, render_template, request, send_file
from opencc import OpenCC

import model_downloader


# Templates/static resolve next to this module in a source checkout. In a frozen
# .app bundle the module lives inside lib/python3.13, while py2app copies those
# folders to Contents/Resources (exposed as $RESOURCEPATH), so resolve there
# instead. The data ROOT (models, whisper-cli, outputs) is resolved separately
# below and may live elsewhere on disk.
FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN and os.environ.get("RESOURCEPATH"):
    APP_ROOT = Path(os.environ["RESOURCEPATH"])
else:
    # Source checkout, or a frozen build without RESOURCEPATH set (defensive).
    APP_ROOT = Path(__file__).resolve().parent

# When frozen into a .app bundle there is no source tree to fall back on, so the
# writable runtime defaults to Application Support; from a source checkout it
# defaults to the repository root. Either can be overridden with the env var.
if FROZEN:
    DEFAULT_ROOT = Path.home() / "Library" / "Application Support" / "LocalTranscript"
else:
    DEFAULT_ROOT = APP_ROOT.parents[1]
ROOT = Path(os.environ.get("LOCAL_TRANSCRIPT_ROOT", DEFAULT_ROOT)).expanduser().resolve()
OUTPUT_ROOT = ROOT / "outputs" / "transcribe_app"
DEFAULT_RESULT_ROOT = OUTPUT_ROOT / "results"
WHISPER_ROOT = ROOT / "work" / "whisper.cpp"

# Code vs data split: the whisper-cli binary + its dylibs ship INSIDE the .app
# (relocated and signed, riding the app's Gatekeeper approval), so when frozen it
# resolves from the bundle. Only the model files are downloaded into the writable
# ROOT (Application Support) on first run. A source checkout uses the build tree.
if FROZEN:
    WHISPER_CLI = APP_ROOT / "whisper-runtime" / "whisper-cli"
else:
    WHISPER_CLI = WHISPER_ROOT / "build" / "bin" / "whisper-cli"
MODEL_PATH = WHISPER_ROOT / "models" / "ggml-large-v3.bin"  # default download target
VAD_MODEL_PATH = WHISPER_ROOT / "models" / "ggml-silero-v6.2.0.bin"
model_downloader.configure(MODEL_PATH, VAD_MODEL_PATH)

# User settings (default language + optional model-path override) persist here.
SETTINGS_PATH = ROOT / "settings.json"
DEFAULT_LANGUAGE = "yue"


def load_settings() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_name(SETTINGS_PATH.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_PATH)  # atomic write so a crash never leaves half a file


def active_model_path() -> Path:
    """The model to use: a validated user override, else the bundled default.

    The override lets people point at an existing large-v3 model they already
    have (e.g. shared with Buzz) instead of downloading a duplicate 2.9 GB copy.
    Only a present, correctly-sized file is honored — otherwise we fall back to
    the default so a stale/bad override can't wedge the app."""
    override = load_settings().get("model_path")
    if override:
        candidate = Path(override).expanduser()
        try:
            if candidate.is_file() and candidate.stat().st_size == model_downloader.LARGE_V3_SIZE:
                return candidate
        except OSError:
            pass
    return MODEL_PATH


def default_language() -> str:
    lang = load_settings().get("default_language")
    return lang if lang in LANGUAGES else DEFAULT_LANGUAGE

# App Translocation: when a downloaded app is launched from Downloads (not moved
# to /Applications), macOS runs it from a read-only randomized mount. The bundle
# can't be declassified there, so the bundled whisper-cli would hang — surface it
# to the UI so the user is told to move the app instead of hitting a silent dead end.
TRANSLOCATED = FROZEN and "/AppTranslocation/" in str(APP_ROOT)
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

SOURCE_TYPES = {"file", "url", "live"}
# A job is "active" (occupies the single transcription slot) in any of these.
ACTIVE_STATUSES = {"queued", "preparing", "running", "paused", "cancelling", "finalizing"}
TERMINAL_STATUSES = {"done", "failed", "cancelled"}
MAX_RETAINED_JOBS = 50  # cap the in-memory registry; status.json keeps older history

app = Flask(
    __name__,
    template_folder=str(APP_ROOT / "templates"),
    static_folder=str(APP_ROOT / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024 * 1024


@app.errorhandler(413)
def _too_large(_error):
    # Always JSON so the frontend shows a clear message instead of misreading
    # an HTML 413 body as a lost connection.
    return jsonify({"error": "That file is too large (5 GB limit)."}), 413


@app.errorhandler(500)
def _server_error(_error):
    return jsonify({"error": "Something went wrong on the local server."}), 500


@dataclass
class Job:
    id: str
    status: str = "queued"
    message: str = "Queued"
    language: str = "yue"
    output_format: str = "all"
    output_location: str = ""
    terminology: str = ""
    source_type: str = "file"
    source_name: str = ""
    source_path: str = ""
    source_url: str = ""
    saved_source_filename: str = ""
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


def source_dir(job_id: str) -> Path:
    return job_dir(job_id) / "source"


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


def safe_local_name(name: str, fallback: str) -> str:
    """Sanitize a filename for safe local storage while PRESERVING Unicode.

    werkzeug's secure_filename strips every non-ASCII character, which destroys
    Cantonese/Chinese filenames (the primary use case) — '會議錄音.mp3' becomes
    'mp3'. We only need path-safety here (each job has its own isolated dir), so
    keep the Unicode and just remove path separators, control chars, and leading
    dots. Cap length to stay filesystem-safe.
    """
    name = Path(str(name or "")).name  # strips any directory / traversal components
    name = re.sub(r"[/\\\x00-\x1f]", "", name).strip().lstrip(".")
    if len(name) > 180:
        stem, dot, ext = name.rpartition(".")
        name = ((stem[:160] + dot + ext[:16]) if dot else name[:180])
    return name or fallback


def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid http or https media URL.")
    name = unquote(Path(parsed.path).name or "")
    return safe_local_name(name, "media")


def assert_public_url(url: str) -> None:
    """Reject URLs that resolve to loopback/private/link-local/reserved addresses.

    The transcription server has no auth and binds loopback, so an attacker-supplied
    URL could otherwise be used to make it fetch 127.0.0.1 or LAN hosts (SSRF). We
    resolve the host and refuse any non-public address. (DNS rebinding between this
    check and the fetch is still theoretically possible but out of scope for a local
    single-user tool.)
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("Enter a valid http or https media URL.")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("Enter a valid http or https media URL.") from exc
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve host: {host}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        # Positive allowlist: only globally-routable addresses are permitted.
        # is_global is False for private, loopback, link-local, reserved,
        # multicast, unspecified AND CGNAT/shared space (100.64.0.0/10), so this
        # is stricter and simpler than enumerating each special range.
        if not ip.is_global:
            raise ValueError("Refusing to fetch a non-public (private, loopback, or reserved) address.")


class _PublicOnlyRedirect(HTTPRedirectHandler):
    """Re-validate every redirect target so a public URL can't 30x to localhost/LAN."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        assert_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_safe_url_opener = build_opener(_PublicOnlyRedirect)


MAX_URL_DOWNLOAD_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB ceiling for remote media


def download_url_to_source(url: str, destination_dir: Path) -> Path:
    filename = safe_filename_from_url(url)
    assert_public_url(url)
    destination_dir.mkdir(parents=True, exist_ok=True)
    path = destination_dir / filename
    with _safe_url_opener.open(url, timeout=30) as response:
        ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype.startswith("text/") or ctype in {"application/json", "application/xml", "text/html"}:
            raise ValueError("That URL returned a web page, not a media file.")
        total = 0
        with path.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_URL_DOWNLOAD_BYTES:
                    out.close()
                    path.unlink(missing_ok=True)
                    raise ValueError("Remote file exceeds the 5 GB limit.")
                out.write(chunk)
    return path


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
                ["/bin/ps", "-p", str(pid), "-o", "%cpu=,%mem=,rss=,etime="],
                text=True,
                encoding="utf-8",
                errors="replace",
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
        vm = subprocess.check_output(["/usr/bin/vm_stat"], text=True, encoding="utf-8", errors="replace", timeout=2)
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


def refresh_runtime_status(job: Job, snapshot: dict[str, Any] | None = None) -> None:
    now = time.time()
    if job.process_pid:
        # Accept a precomputed snapshot so callers can run the ps/vm_stat
        # subprocesses OUTSIDE jobs_lock (holding it stalls the worker thread).
        job.system = snapshot if snapshot is not None else system_snapshot(job.process_pid)

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
        "source_type": job.source_type,
        "source_name": job.source_name,
        "source_path": job.source_path,
        "source_url": job.source_url,
        "saved_source_filename": job.saved_source_filename,
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


def read_status_json(job_id: str) -> dict[str, Any] | None:
    """Read a job's persisted status.json, tolerating truncated/corrupt content
    (e.g. the app was killed mid-write). Returns None if absent/unreadable."""
    path = job_dir(job_id) / "status.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _prune_finished_jobs() -> None:
    """Cap the in-memory jobs dict so a long-running session doesn't grow forever.
    Only terminal jobs are evicted; status.json still serves their history."""
    with jobs_lock:
        if len(jobs) <= MAX_RETAINED_JOBS:
            return
        terminal = [(j.updated_at, jid) for jid, j in jobs.items() if j.status in TERMINAL_STATUSES]
        terminal.sort()
        for _, jid in terminal[: len(jobs) - MAX_RETAINED_JOBS]:
            jobs.pop(jid, None)


def _fail_job(job_id: str, message: str) -> None:
    """Mark a job failed without ever raising — the worker's last act, so a
    secondary error (e.g. disk full during save) can't kill the thread and hang
    the UI in a permanent 'running' spinner."""
    try:
        with jobs_lock:
            job = jobs.get(job_id)
            if job:
                job.status = "failed"
                job.message = "Failed"
                job.error = message
                job.process_pid = None
                job.updated_at = time.time()
                try:
                    save_status(job)
                except Exception:
                    pass
    except Exception:
        pass


def _stop_process(process: "subprocess.Popen", grace: float = 3.0) -> None:
    """Terminate a child, escalating to SIGKILL if it ignores SIGTERM, so a
    cancel can never hang the worker on a stuck whisper-cli."""
    try:
        process.terminate()
    except OSError:
        pass
    try:
        process.wait(timeout=grace)
        return
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        return
    try:
        process.kill()
        process.wait(timeout=2)
    except Exception:
        pass


def update_job(job_id: str, **changes: Any) -> None:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return
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


def model_complete() -> bool:
    """The model is usable only if present AND the full expected size — a partial
    rsync/copy of ggml-large-v3.bin would otherwise be loaded as a corrupt model.
    Honors a user-set model-path override via active_model_path()."""
    path = active_model_path()
    try:
        return path.exists() and path.stat().st_size == model_downloader.LARGE_V3_SIZE
    except OSError:
        return False


def app_ready() -> bool:
    return model_complete() and WHISPER_CLI.exists()


def ensure_ready() -> None:
    missing = []
    for label, path in {
        "whisper.cpp binary": WHISPER_CLI,
        "large-v3 model": active_model_path(),
    }.items():
        if not path.exists():
            missing.append(f"{label}: {path}")
    if missing:
        raise RuntimeError("Missing required local files:\n" + "\n".join(missing))


def convert_audio_to_wav(src: Path, dst: Path) -> None:
    try:
        container = av.open(str(src))
    except Exception as exc:  # av.error.* / OSError — unreadable or non-media file
        raise RuntimeError("Could not read this file as audio or video.") from exc

    frames_written = 0
    try:
        stream = next((s for s in container.streams if s.type == "audio"), None)
        if stream is None:
            raise RuntimeError("This file has no audio track.")

        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        dst.parent.mkdir(parents=True, exist_ok=True)

        def emit(out, converted) -> int:
            if converted is None:
                return 0
            n = 0
            for audio_frame in (converted if isinstance(converted, list) else [converted]):
                data = np.asarray(audio_frame.to_ndarray(), dtype=np.int16).reshape(-1)
                out.writeframes(data.tobytes())
                n += data.shape[0]
            return n

        with wave.open(str(dst), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(16000)
            try:
                for frame in container.decode(stream):
                    frames_written += emit(out, resampler.resample(frame))
            except Exception as exc:
                raise RuntimeError("Could not decode the audio in this file.") from exc
            # Flush the resampler's internally buffered tail (otherwise the last
            # fraction of a second of every transcript is silently dropped).
            frames_written += emit(out, resampler.resample(None))
    finally:
        container.close()

    if frames_written == 0:
        raise RuntimeError("No decodable audio found in this file.")


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
        start = item.get("start")
        end = item.get("end")
        # whisper.cpp's -ojf JSON has no start/end; it emits offsets.from/to as
        # integer MILLISECONDS. Convert those unconditionally (the old >10000ms
        # heuristic silently 1000x-inflated every sub-10s timestamp). Only the
        # rare second-based float variants populate start/end directly.
        if start is None and end is None:
            offsets = item.get("offsets") or {}
            if offsets.get("from") is not None:
                start = offsets["from"] / 1000.0
            if offsets.get("to") is not None:
                end = offsets["to"] / 1000.0
        if start is None or end is None:
            continue
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

        def csv_safe(text: str) -> str:
            # Neutralize spreadsheet formula injection: a cell starting with
            # = + - @ (or tab/CR) is treated as a formula by Excel/Sheets.
            return ("'" + text) if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start", "end", "text"])
            for seg in segments:
                writer.writerow([ts_label(seg["start"]), ts_label(seg["end"]), csv_safe(seg["text"])])
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
            str(active_model_path()),
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
            # whisper-cli streams the transcript (e.g. Cantonese) to stdout. Decode
            # as UTF-8 explicitly: a Finder-launched .app has no locale, so text=True
            # would otherwise default to ASCII and crash on the first CJK byte.
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        update_job(job_id, process_pid=process.pid)
        assert process.stdout is not None
        progress_pattern = re.compile(r"progress\s*=\s*(\d+)%")
        for line in process.stdout:
            with jobs_lock:
                current = jobs.get(job_id)
                if current and current.cancel_requested:
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
                    current = jobs.get(job_id)
                    should_update = bool(current) and current.progress_source != "actual" and estimated_progress - current.progress >= 1.0
                if should_update:
                    update_progress(job_id, estimated_progress, "estimate", started_at, progress_samples, fallback_total)

        with jobs_lock:
            current = jobs.get(job_id)
            was_cancelled = bool(current and current.cancel_requested)
        if was_cancelled:
            _stop_process(process)  # terminate -> grace -> SIGKILL; never hang here
        code = process.wait()
        update_job(job_id, process_pid=None)
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
        if not segments:
            raise RuntimeError("No speech was detected in the audio.")
        files = write_outputs(upload_path.name, segments, final_base, output_format)
        append_log(job_id, f"Saved final transcripts to {final_dir}")
        # The process already exited, so a terminate during finalizing takes the
        # no-pid branch and only flips status to 'cancelling'. Honor that intent
        # instead of clobbering it with 'done': commit the result atomically only
        # if the user did not ask to cancel while we were writing files.
        with jobs_lock:
            current = jobs.get(job_id)
            cancelled = bool(current and current.cancel_requested)
            if cancelled:
                current.status = "cancelled"
                current.message = "Cancelled"
                current.eta_seconds = 0.0
                current.process_pid = None
                current.updated_at = time.time()
                save_status(current)  # safe under the lock; does not re-acquire it
            else:
                final_elapsed = processing_elapsed(current) if current else time.time() - started_at
        if cancelled:
            # append_log re-acquires jobs_lock, so it MUST run after release.
            append_log(job_id, "Cancelled after processing finished.")
            return
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
        _fail_job(job_id, str(exc))


@app.get("/")
def index():
    settings = load_settings()
    return render_template(
        "index.html",
        languages=LANGUAGES,
        formats=FORMATS,
        model_ready=app_ready(),
        vad_ready=VAD_MODEL_PATH.exists(),
        default_result_location=str(DEFAULT_RESULT_ROOT),
        default_language=default_language(),
        model_path=settings.get("model_path", ""),
        default_model_path=str(MODEL_PATH),
    )


@app.get("/api/health")
def health():
    model_ok = model_complete()
    binary_ok = WHISPER_CLI.exists()
    return jsonify(
        {
            "ready": model_ok and binary_ok,
            "whisper_cli": str(WHISPER_CLI),
            "model": str(active_model_path()),
            "vad": VAD_MODEL_PATH.exists(),
            "binary_ok": binary_ok,
            "model_ok": model_ok,
            # The engine is bundled; only the model is missing -> offer the in-app download.
            "downloadable": binary_ok and not model_ok,
            "setup_status": model_downloader.get_state()["status"],
            "translocated": TRANSLOCATED,
        }
    )


@app.post("/api/setup/start")
def setup_start():
    if not WHISPER_CLI.exists():
        return jsonify({"error": "The transcription engine is missing from the app bundle."}), 409
    started = model_downloader.start_download()
    return jsonify(model_downloader.get_state()), (202 if started else 200)


@app.get("/api/setup/status")
def setup_status():
    return jsonify(model_downloader.get_state())


@app.post("/api/setup/cancel")
def setup_cancel():
    model_downloader.cancel_download()
    return jsonify(model_downloader.get_state())


@app.get("/api/settings")
def get_settings():
    settings = load_settings()
    return jsonify(
        {
            "default_language": default_language(),
            "model_path": settings.get("model_path", ""),
            "default_model_path": str(MODEL_PATH),
            "active_model_path": str(active_model_path()),
            "model_ready": app_ready(),
        }
    )


@app.post("/api/settings")
def update_settings():
    """Persist user settings. The model-path override is validated HERE (on apply)
    so a bad path surfaces an error immediately instead of failing mid-transcription."""
    data = request.get_json(silent=True) or request.form.to_dict()
    settings = load_settings()

    if "default_language" in data:
        lang = (data.get("default_language") or "").strip()
        if lang not in LANGUAGES:
            return jsonify({"error": "Unknown language."}), 400
        settings["default_language"] = lang

    if "model_path" in data:
        raw = (data.get("model_path") or "").strip()
        if not raw:
            settings.pop("model_path", None)  # cleared -> fall back to the default
        else:
            candidate = Path(raw).expanduser()
            if not candidate.is_file():
                return jsonify({"error": f"No file found at that path: {candidate}"}), 400
            try:
                size = candidate.stat().st_size
            except OSError as exc:
                return jsonify({"error": f"Can't read that file: {exc}"}), 400
            if size != model_downloader.LARGE_V3_SIZE:
                got = size / 1_000_000_000
                return jsonify({
                    "error": (
                        "That file isn't the Whisper large-v3 model. Expected about "
                        f"2.9 GB (ggml-large-v3.bin); this is {got:.1f} GB."
                    )
                }), 400
            settings["model_path"] = str(candidate)

    save_settings(settings)
    return jsonify(
        {
            "ok": True,
            "default_language": default_language(),
            "model_path": settings.get("model_path", ""),
            "active_model_path": str(active_model_path()),
            "model_ready": app_ready(),
        }
    )


@app.post("/api/jobs")
def create_job():
    source_type = request.form.get("source_type", "file")
    language = request.form.get("language", "yue")
    output_format = request.form.get("format", "all")
    output_location = request.form.get("output_location", "").strip()
    terminology = request.form.get("terminology", "").strip()[:2000]
    if source_type not in SOURCE_TYPES:
        return jsonify({"error": "Unsupported source type."}), 400
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
    # Single-flight: reject a new job while one is active AND reserve the slot in
    # the SAME locked section (a placeholder 'queued' job), so two near-simultaneous
    # POSTs can't both pass the gate during the slow source-prep that follows.
    with jobs_lock:
        if any(j.status in ACTIVE_STATUSES for j in jobs.values()):
            return jsonify({"error": "A transcription is already running. Wait for it to finish."}), 409
        jobs[job_id] = Job(
            id=job_id, language=language, output_format=output_format,
            terminology=terminology, source_type=source_type,
            status="preparing", message="Preparing source",
            output_location=str(chosen_output_base / job_id),
        )

    out_dir = job_dir(job_id)
    src_dir = source_dir(job_id)
    src_dir.mkdir(parents=True, exist_ok=True)
    source_url = ""
    try:
        if source_type in {"file", "live"}:
            file = request.files.get("audio")
            if file is None or not file.filename:
                message = "Stop recording before starting transcription." if source_type == "live" else "Choose an audio file."
                raise ValueError(message)
            fallback = "live-recording.webm" if source_type == "live" else "audio"
            filename = safe_local_name(file.filename, fallback)
            source_path = src_dir / filename
            file.save(source_path)
            if source_path.stat().st_size == 0:
                raise ValueError("The audio file is empty.")
        else:
            source_url = request.form.get("source_url", "").strip()
            if not source_url:
                raise ValueError("Enter a media URL.")
            source_path = download_url_to_source(source_url, src_dir)
    except Exception as exc:
        with jobs_lock:
            jobs.pop(job_id, None)  # release the reserved slot
        shutil.rmtree(out_dir, ignore_errors=True)  # don't leave orphaned dirs
        return jsonify({"error": str(exc)}), 400

    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:  # terminated during preparation
            shutil.rmtree(out_dir, ignore_errors=True)
            return jsonify({"error": "Job was cancelled."}), 409
        job.source_name = source_path.name
        job.source_path = str(source_path)
        job.source_url = source_url
        job.saved_source_filename = source_path.name
        save_status(job)
        payload = serialize_job(job)  # snapshot before the worker thread mutates it
    _prune_finished_jobs()

    thread = threading.Thread(
        target=run_transcription,
        args=(job_id, source_path, language, output_format, str(chosen_output_base), terminology),
        daemon=True,
    )
    thread.start()
    return jsonify(payload), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        pid = job.process_pid if job else None
        present = job is not None
    if present:
        snap = system_snapshot(pid) if pid else None  # subprocess OUTSIDE the lock
        with jobs_lock:
            job = jobs.get(job_id)
            if job:
                if pid:
                    refresh_runtime_status(job, snapshot=snap)
                    save_status(job)
                return jsonify(serialize_job(job))

    data = read_status_json(job_id)
    if data is not None:
        return jsonify(data)
    return jsonify({"error": "Job not found."}), 404


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def terminate_active_jobs(grace: float = 3.0) -> None:
    """Stop any in-flight whisper-cli children.

    Called on app shutdown (window close / interpreter exit) so quitting never
    leaves an orphaned — or SIGSTOP-suspended — transcription pinning CPU/GPU/RAM.
    SIGCONT first so a paused child can actually receive the SIGTERM, then escalate
    to SIGKILL for anything that ignores the grace period. Safe to call repeatedly
    and when no jobs are running.
    """
    with jobs_lock:
        pids = [job.process_pid for job in jobs.values() if job.process_pid]
        for job in jobs.values():
            if job.process_pid:
                job.cancel_requested = True
    if not pids:
        return
    for pid in pids:
        try:
            os.kill(pid, signal.SIGCONT)
            os.kill(pid, signal.SIGTERM)
        except OSError:
            continue
    # Deliberately do NOT os.waitpid() here: the worker thread's process.wait()
    # owns reaping each child, and a second reaper would race it. The cost is
    # that a SIGTERM'd-but-unreaped child reads as alive (zombie), so in the rare
    # case where the worker isn't reaping (interpreter teardown) this loop may run
    # the full grace before the SIGKILL no-ops. The child is dead either way.
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not any(_pid_alive(pid) for pid in pids):
            return
        time.sleep(0.1)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


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

    # Terminate must work even before whisper-cli has a PID (during 'preparing'):
    # set the cancel flag so the worker bails out as soon as it reaches a check.
    if action == "terminate" and not pid:
        with jobs_lock:
            job = jobs.get(job_id)
            if not job or job.status in TERMINAL_STATUSES:
                return jsonify({"error": "Job is no longer running."}), 409
            job.cancel_requested = True
            job.status = "cancelling"
            job.message = "Cancelling"
            job.updated_at = time.time()
            save_status(job)
            payload = serialize_job(job)
        return jsonify(payload), 202

    if not pid:
        return jsonify({"error": "No active transcription process for this job."}), 409

    # The guard, the signal, and the status write are ONE critical section per
    # action. os.kill is a non-blocking syscall, so holding jobs_lock across it
    # is cheap and prevents a concurrent pause/resume/terminate from interleaving
    # and clobbering each other's status (e.g. a late 'paused' overwriting the
    # worker's 'cancelled', which would wedge the single transcription slot).
    try:
        if action == "pause":
            with jobs_lock:
                job = jobs.get(job_id)
                if not job or job.status != "running" or job.cancel_requested:
                    return jsonify({"error": "Job is not running."}), 409
                os.kill(pid, signal.SIGSTOP)
                job.status = "paused"
                job.message = "Paused"
                job.paused_at = time.time()
                job.updated_at = time.time()
                save_status(job)
                payload = serialize_job(job)
            append_log(job_id, "Paused transcription.")
        elif action == "resume":
            with jobs_lock:
                job = jobs.get(job_id)
                if not job or job.status != "paused" or job.cancel_requested:
                    return jsonify({"error": "Job is not paused."}), 409
                os.kill(pid, signal.SIGCONT)
                if job.paused_at:
                    job.total_paused_seconds += max(0.0, time.time() - job.paused_at)
                job.paused_at = 0.0
                job.status = "running"
                job.message = "Resumed"
                job.updated_at = time.time()
                save_status(job)
                payload = serialize_job(job)
            append_log(job_id, "Resumed transcription.")
        else:  # terminate with a live pid
            with jobs_lock:
                job = jobs.get(job_id)
                if not job or job.status in TERMINAL_STATUSES:
                    return jsonify({"error": "Job is no longer running."}), 409
                was_paused = bool(job.status == "paused")
                job.cancel_requested = True
                os.kill(pid, signal.SIGTERM)
                if was_paused:  # a stopped child can't act on SIGTERM until resumed
                    os.kill(pid, signal.SIGCONT)
                job.status = "cancelling"
                job.message = "Cancelling"
                job.updated_at = time.time()
                save_status(job)
                payload = serialize_job(job)
            append_log(job_id, "Cancellation requested.")
    except ProcessLookupError:
        # os.kill raised inside the `with` block; the lock is already released by
        # the time this handler runs, so update_job can re-acquire it safely.
        update_job(job_id, process_pid=None)
        return jsonify({"error": "The transcription process already exited."}), 409
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(payload), 202


@app.get("/download/<job_id>/<path:filename>")
def download(job_id: str, filename: str):
    safe_name = Path(filename).name  # strip any directory components
    output_location = ""
    with jobs_lock:
        job = jobs.get(job_id)
        if job:
            output_location = job.output_location
    if not output_location:
        data = read_status_json(job_id)
        if data:
            output_location = data.get("output_location", "")

    search_dirs = []
    if output_location:
        search_dirs.append(Path(output_location))
    search_dirs.append(source_dir(job_id))
    search_dirs.append(job_dir(job_id))

    for folder in search_dirs:
        candidate = (folder / safe_name)
        try:
            resolved = candidate.resolve()
            # Confine to the folder we intended — output_location comes from
            # persisted JSON, so never serve a file resolved outside it.
            if resolved.is_file() and resolved.is_relative_to(folder.resolve()):
                return send_file(resolved, as_attachment=True)
        except (OSError, ValueError):
            continue
    return jsonify({"error": "File not found."}), 404


def sweep_stale_jobs() -> None:
    """On startup, mark any persisted job left in a non-terminal state (running/
    paused/etc.) whose process is no longer alive as 'failed'. Otherwise a job
    interrupted by a crash/quit shows forever as 'running' after relaunch."""
    jobs_root = OUTPUT_ROOT / "jobs"
    if not jobs_root.is_dir():
        return
    for status_path in jobs_root.glob("*/status.json"):
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("status") not in ACTIVE_STATUSES:
            continue
        pid = data.get("process_pid")
        if pid and _pid_alive(int(pid)):
            continue  # genuinely still running in another process — leave it
        data["status"] = "failed"
        data["message"] = "Interrupted"
        data["error"] = "This transcription was interrupted (the app was closed)."
        data["process_pid"] = None
        try:
            status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


if __name__ == "__main__":
    sweep_stale_jobs()
    port = int(os.environ.get("PORT", "5057"))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)

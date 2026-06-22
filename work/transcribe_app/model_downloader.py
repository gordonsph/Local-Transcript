"""First-run model downloader for the bundled native app.

The .app ships the whisper-cli engine but NOT the 2.9 GB model (too large to
bundle/notarize). On first run the app downloads the model + the optional Silero
VAD model into the writable runtime dir. Stdlib only, so it works inside the
ad-hoc-signed bundle with no extra dependencies.

Design: a single background daemon thread owns the transfer; Flask handlers only
read/write in-memory state under a lock and never block on I/O. Downloads are
resumable (HTTP Range -> .part file), atomic (os.replace after SHA-256 verify so
the final filename only ever exists fully-verified), and integrity-pinned (the
expected hashes are baked in, never fetched alongside the data).

URLs + hashes + sizes are the canonical Hugging Face files whisper.cpp's own
download scripts use; the SHA-256 values match the local known-good models.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CHUNK = 1024 * 1024
TIMEOUT = 30
MAX_ATTEMPTS = 4
FREE_SPACE_HEADROOM = 64 * 1024 * 1024
USER_AGENT = "LocalTranscript/1.0 (+https://github.com/ggerganov/whisper.cpp)"

LARGE_V3_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin"
LARGE_V3_SHA = "64d182b440b98d5203c4f9bd541544d84c605196c4f7b845dfa11fb23594d1e2"
LARGE_V3_SIZE = 3095033483
SILERO_URL = "https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v6.2.0.bin"
SILERO_SHA = "2aa269b785eeb53a82983a20501ddf7c1d9c48e33ab63a41391ac6c9f7fb6987"
SILERO_SIZE = 885098


@dataclass(frozen=True)
class ModelSpec:
    key: str
    url: str
    sha256: str
    size: int
    dest: Path
    optional: bool


class Status(str, Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class FileProgress:
    key: str
    total: int
    downloaded: int = 0
    status: str = "pending"  # pending | downloading | verifying | done | error
    error: str | None = None


@dataclass
class _State:
    status: Status = Status.IDLE
    files: dict[str, FileProgress] = field(default_factory=dict)
    error: str | None = None
    error_kind: str | None = None
    speed_bps: float = 0.0
    eta_seconds: float | None = None


class _Cancelled(Exception):
    pass


class _DownloadError(Exception):
    def __init__(self, message: str, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


_SPECS: list[ModelSpec] = []
_state = _State()
_lock = threading.Lock()
_worker: threading.Thread | None = None
_cancel = threading.Event()


def configure(model_path: Path, vad_path: Path) -> None:
    """Register the download targets (the paths app.py resolves for the models)."""
    global _SPECS
    _SPECS = [
        ModelSpec("model", LARGE_V3_URL, LARGE_V3_SHA, LARGE_V3_SIZE, Path(model_path), optional=False),
        ModelSpec("vad", SILERO_URL, SILERO_SHA, SILERO_SIZE, Path(vad_path), optional=True),
    ]


def is_ready() -> bool:
    """All REQUIRED model files present. The atomic rename-after-verify guarantees
    a final-named file is fully downloaded and hash-verified, so existence == ready."""
    return bool(_SPECS) and all(s.dest.exists() for s in _SPECS if not s.optional)


def get_state() -> dict:
    with _lock:
        files = {
            k: {"key": p.key, "downloaded": p.downloaded, "total": p.total,
                "status": p.status, "error": p.error}
            for k, p in _state.files.items()
        }
        downloaded = sum(p.downloaded for p in _state.files.values())
        total = sum(p.total for p in _state.files.values())
        return {
            "status": _state.status.value,
            "error": _state.error,
            "error_kind": _state.error_kind,
            "files": files,
            "downloaded": downloaded,
            "total": total,
            "percent": round(downloaded / total * 100, 1) if total else 0.0,
            "speed_bps": round(_state.speed_bps),
            "eta_seconds": round(_state.eta_seconds) if _state.eta_seconds is not None else None,
            "ready": is_ready(),
        }


def start_download() -> bool:
    """Begin (or resume) the download on a background thread. Single-flight: a
    second call while a worker is alive is a no-op and returns False."""
    global _worker
    with _lock:
        if _worker is not None and _worker.is_alive():
            return False
        _cancel.clear()
        _state.status = Status.DOWNLOADING
        _state.error = None
        _state.error_kind = None
        _state.speed_bps = 0.0
        _state.eta_seconds = None
        _state.files = {
            s.key: FileProgress(key=s.key, total=s.size,
                                downloaded=(s.dest.stat().st_size if s.dest.exists() else 0),
                                status=("done" if s.dest.exists() else "pending"))
            for s in _SPECS
        }
        _worker = threading.Thread(target=_run, name="model-downloader", daemon=True)
        _worker.start()
        return True


def cancel_download() -> None:
    _cancel.set()


def _set_file(key: str, **changes: object) -> None:
    with _lock:
        fp = _state.files.get(key)
        if fp:
            for name, value in changes.items():
                setattr(fp, name, value)


def _set_status(status: Status) -> None:
    with _lock:
        _state.status = status


def _run() -> None:
    try:
        for spec in _SPECS:
            if _cancel.is_set():
                raise _Cancelled()
            if spec.dest.exists():
                _set_file(spec.key, downloaded=spec.size, status="done")
                continue
            try:
                _download_one(spec)
            except _DownloadError as exc:
                if spec.optional:
                    # VAD is a nice-to-have; a failure must not block the app.
                    _set_file(spec.key, status="error", error=str(exc))
                    continue
                raise
        with _lock:
            if is_ready():
                _state.status = Status.DONE
            else:
                _state.status = Status.ERROR
                _state.error = "Required model is missing after download."
                _state.error_kind = "incomplete"
    except _Cancelled:
        _set_status(Status.CANCELLED)
    except _DownloadError as exc:
        with _lock:
            _state.status = Status.ERROR
            _state.error = str(exc)
            _state.error_kind = exc.kind
    except Exception as exc:  # noqa: BLE001 — surface any unexpected failure to the UI
        with _lock:
            _state.status = Status.ERROR
            _state.error = str(exc)
            _state.error_kind = "unknown"


def _download_one(spec: ModelSpec) -> None:
    dest = spec.dest
    part = dest.parent / (dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)

    if part.exists() and part.stat().st_size > spec.size:
        part.unlink()  # corrupt/oversized leftover — restart cleanly

    existing = part.stat().st_size if part.exists() else 0
    free = shutil.disk_usage(dest.parent).free
    if free < (spec.size - existing) + FREE_SPACE_HEADROOM:
        raise _DownloadError("Not enough free disk space for the model.", "disk_full")

    # A .part that is already the full size means a previous run finished the
    # transfer but crashed before verify/rename. Skip streaming (a Range request
    # at offset==size would get a 416) and go straight to verify + finalize.
    if existing < spec.size:
        _set_file(spec.key, status="downloading", downloaded=existing)
        attempt = 0
        while True:
            attempt += 1
            try:
                _stream(spec, part)
                break
            except _Cancelled:
                raise
            except (URLError, TimeoutError, ConnectionError, OSError) as exc:
                if not isinstance(exc, URLError) and getattr(exc, "errno", None) == 28:
                    raise _DownloadError("Ran out of disk space.", "disk_full")
                # 4xx (404/410/…) are permanent; 5xx + 429/408 are transient -> retry.
                if isinstance(exc, HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                    raise _DownloadError(f"Server error {exc.code} fetching the model.", "http")
                if attempt >= MAX_ATTEMPTS:
                    if isinstance(exc, HTTPError):
                        raise _DownloadError(f"Server error {exc.code} fetching the model.", "http")
                    raise _DownloadError("Network error — check your connection and retry.", "offline")
                time.sleep(2 * attempt)  # backoff, then resume from the current .part size

    _set_file(spec.key, status="verifying")
    _set_status(Status.VERIFYING)
    actual = _sha256(part)
    _set_status(Status.DOWNLOADING)
    if actual != spec.sha256:
        part.unlink(missing_ok=True)
        raise _DownloadError("Downloaded file failed its integrity check.", "checksum")

    os.replace(part, dest)  # atomic within the same directory
    _set_file(spec.key, status="done", downloaded=spec.size)


def _stream(spec: ModelSpec, part: Path) -> None:
    existing = part.stat().st_size if part.exists() else 0
    request = Request(spec.url, headers={"User-Agent": USER_AGENT})
    if existing:
        request.add_header("Range", f"bytes={existing}-")

    with urlopen(request, timeout=TIMEOUT) as response:
        # If we asked for a range but the server ignored it (200, not 206), the
        # body is the whole file again — restart from zero to avoid corruption.
        if existing and response.getcode() != 206:
            existing = 0
            mode = "wb"
        else:
            mode = "ab" if existing else "wb"

        _set_file(spec.key, downloaded=existing)
        window_start = time.monotonic()
        window_bytes = existing
        with open(part, mode) as out:
            while True:
                if _cancel.is_set():
                    raise _Cancelled()
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                existing += len(chunk)
                now = time.monotonic()
                if now - window_start >= 0.5:
                    speed = (existing - window_bytes) / (now - window_start)
                    remaining = max(0, spec.size - existing)
                    with _lock:
                        _state.speed_bps = speed
                        _state.eta_seconds = (remaining / speed) if speed > 0 else None
                    window_start = now
                    window_bytes = existing
                _set_file(spec.key, downloaded=existing)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            if _cancel.is_set():
                raise _Cancelled()
            block = handle.read(CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()

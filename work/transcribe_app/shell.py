"""Native macOS WebView shell for Local Transcript.

Boots the existing Flask app on an ephemeral localhost port inside this
process, then displays it in a native WKWebView window via pywebview. The
server's lifecycle is owned by the window: closing the window shuts the
server down and exits.

Run directly during development:

    work/transcribe-venv/bin/python work/transcribe_app/shell.py
"""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import webview
from werkzeug.serving import make_server

from app import app, terminate_active_jobs


# WKWebView denies getUserMedia (Live recording) unless the app's UI delegate
# implements requestMediaCapturePermissionForOrigin. pywebview's Cocoa backend
# doesn't, so we inject the selector into its delegate class. WKPermissionDecision
# values: 0 = prompt, 1 = grant, 2 = deny. We grant; the OS still gates real
# microphone access behind its own TCC prompt (driven by NSMicrophoneUsageDescription).
def _enable_media_capture() -> None:
    try:
        import objc
        import WebKit  # noqa: F401 — ensures WebKit block signatures are loaded
        from webview.platforms import cocoa
    except Exception:
        return  # Non-macOS or backend unavailable; nothing to patch.

    delegate_cls = cocoa.BrowserView.BrowserDelegate
    selector_name = (
        b"webView:requestMediaCapturePermissionForOrigin:"
        b"initiatedByFrame:type:decisionHandler:"
    )

    if delegate_cls.instancesRespondToSelector_(selector_name):
        return  # Future pywebview versions may add this themselves.

    def grant_media_capture(self, web_view, origin, frame, capture_type, handler):
        handler(1)  # WKPermissionDecisionGrant

    method = objc.selector(
        grant_media_capture,
        selector=selector_name,
        signature=b"v@:@@@q@?",
    )
    objc.classAddMethods(delegate_cls, [method])


WINDOW_TITLE = "Local Transcript"
HEALTH_PATH = "/api/health"
STARTUP_TIMEOUT_SECONDS = 15


def _declassify_bundle() -> None:
    """Strip the Gatekeeper quarantine flag from our own .app on launch.

    When a user downloads the app, macOS quarantines every nested file. Approving
    the app ("Open Anyway") only clears the MAIN executable LaunchServices starts;
    the whisper-cli we later spawn via subprocess would otherwise hang on an
    unresolved Gatekeeper assessment. An app may declassify its own bundle, so we
    remove the flag recursively (covers whisper-cli + its dylibs). No-op in source
    mode and when running translocated (a read-only randomized mount — the user
    must move the app to /Applications first).
    """
    if not getattr(sys, "frozen", False):
        return
    resource = os.environ.get("RESOURCEPATH")
    if not resource:
        return
    bundle = Path(resource).resolve().parent.parent  # Contents/Resources -> .app
    if "/AppTranslocation/" in str(bundle):
        return
    try:
        subprocess.run(
            ["xattr", "-dr", "com.apple.quarantine", str(bundle)],
            check=False,
            timeout=30,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # best-effort; never block launch on this


def _free_port() -> int:
    """Ask the OS for an unused TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class FlaskServer:
    """Runs the Flask app in a background thread with a clean shutdown."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._server = make_server(host, port, app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self._thread.start()

    def wait_until_ready(self, timeout: float = STARTUP_TIMEOUT_SECONDS) -> bool:
        deadline = time.monotonic() + timeout
        health_url = f"{self.base_url}{HEALTH_PATH}"
        while time.monotonic() < deadline:
            try:
                with urlopen(health_url, timeout=1):
                    return True
            except (URLError, ConnectionError, OSError):
                time.sleep(0.1)
        return False

    def shutdown(self) -> None:
        self._server.shutdown()


def main() -> None:
    _declassify_bundle()

    server = FlaskServer("127.0.0.1", _free_port())
    server.start()

    if not server.wait_until_ready():
        raise SystemExit("Local Transcript server did not start in time.")

    _enable_media_capture()

    # Closing the window must also stop any in-flight transcription, not just the
    # HTTP listener. atexit is the belt-and-suspenders path: it runs on the main
    # thread during interpreter shutdown, so the kill lands even if the closed
    # handler races teardown. Both are idempotent.
    def on_close() -> None:
        terminate_active_jobs()
        server.shutdown()

    atexit.register(terminate_active_jobs)

    # Real macOS "Liquid Glass": vibrancy puts an NSVisualEffectView behind the
    # webview, and transparent lets it show through. On load we add body.vibrancy
    # so the CSS drops its faux-desktop fallback and reveals the system material.
    window = webview.create_window(
        WINDOW_TITLE,
        url=server.base_url,
        width=1180,
        height=860,
        min_size=(820, 640),
        vibrancy=True,
        transparent=True,
        background_color="#1A1E20",
    )
    window.events.closed += on_close

    def on_loaded() -> None:
        try:
            window.evaluate_js("document.body.classList.add('vibrancy')")
        except Exception:
            pass  # vibrancy is a visual nicety; never block on it

    window.events.loaded += on_loaded

    webview.start()


if __name__ == "__main__":
    main()

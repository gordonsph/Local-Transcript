"""Tests for the Step-1 hardening: URL SSRF guard and shutdown process cleanup.

These are deterministic and offline: getaddrinfo on numeric IP literals does not
perform DNS, and the process-kill test uses a local `sleep` child.
"""

import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work" / "transcribe_app"))

import app  # noqa: E402


class UrlSafetyTests(unittest.TestCase):
    def test_rejects_loopback_private_linklocal_reserved_unspecified(self):
        for bad in (
            "http://127.0.0.1/a.mp3",
            "http://[::1]/a.mp3",
            "http://10.0.0.5/a.mp3",
            "http://192.168.1.10/a.mp3",
            "http://169.254.1.1/a.mp3",
            "http://0.0.0.0/a.mp3",
            "http://100.64.0.1/a.mp3",  # CGNAT / RFC 6598 shared space
        ):
            with self.assertRaises(ValueError, msg=bad):
                app.assert_public_url(bad)

    def test_rejects_non_http_scheme_and_malformed(self):
        for bad in ("ftp://example.com/a", "file:///etc/passwd", "data:text/plain,hi",
                    "not-a-url", "http://8.8.8.8:notaport/a"):
            with self.assertRaises(ValueError, msg=bad):
                app.assert_public_url(bad)

    def test_allows_public_ip_literal(self):
        # 8.8.8.8 is a public address; numeric host needs no DNS, so this is offline-safe.
        app.assert_public_url("http://8.8.8.8/a.mp3")


class TerminateActiveJobsTests(unittest.TestCase):
    def test_no_jobs_is_a_noop(self):
        with app.jobs_lock:
            app.jobs.clear()
        app.terminate_active_jobs(grace=0.5)  # must not raise

    def test_kills_a_live_child(self):
        child = subprocess.Popen(["sleep", "30"])
        try:
            with app.jobs_lock:
                app.jobs.clear()
                app.jobs["t"] = app.Job(id="t", process_pid=child.pid)
            app.terminate_active_jobs(grace=1.0)
            # Reap the (now-dead) child and confirm it was ended by a signal
            # (-SIGTERM or -SIGKILL), not still running. We must reap here because
            # this process is the child's parent; in the real app the worker
            # thread's process.wait() does the reaping.
            child.wait(timeout=5)
            self.assertIsNotNone(child.returncode)
            self.assertLess(child.returncode, 0, "child should be killed by a signal")
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            with app.jobs_lock:
                app.jobs.clear()


if __name__ == "__main__":
    unittest.main()

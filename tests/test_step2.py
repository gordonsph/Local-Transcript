"""Step-2 tests: quarantine bundle-path resolution + optional-VAD download policy."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work" / "transcribe_app"))

import model_downloader as md  # noqa: E402
import shell  # noqa: E402


class DeclassifyBundleTests(unittest.TestCase):
    def test_noop_when_not_frozen(self):
        with mock.patch.object(sys, "frozen", False, create=True), \
             mock.patch.object(shell.subprocess, "run") as run:
            shell._declassify_bundle()
        run.assert_not_called()

    def test_strips_quarantine_on_app_root_when_frozen(self):
        resource = "/Applications/Local Transcript.app/Contents/Resources"
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.dict(os.environ, {"RESOURCEPATH": resource}), \
             mock.patch.object(shell.subprocess, "run") as run:
            shell._declassify_bundle()
        run.assert_called_once()
        argv = run.call_args[0][0]
        self.assertEqual(argv[:3], ["xattr", "-dr", "com.apple.quarantine"])
        self.assertTrue(argv[3].endswith("Local Transcript.app"), argv[3])

    def test_skips_when_translocated(self):
        resource = "/private/var/folders/x/AppTranslocation/AB/d/Local Transcript.app/Contents/Resources"
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.dict(os.environ, {"RESOURCEPATH": resource}), \
             mock.patch.object(shell.subprocess, "run") as run:
            shell._declassify_bundle()
        run.assert_not_called()


class OptionalVadPolicyTests(unittest.TestCase):
    def test_optional_vad_failure_does_not_block_ready(self):
        d = Path(tempfile.mkdtemp())
        model, vad = d / "ggml-large-v3.bin", d / "ggml-silero-v6.2.0.bin"
        md.configure(model, vad)
        with md._lock:
            md._state.files = {s.key: md.FileProgress(key=s.key, total=s.size) for s in md._SPECS}
            md._state.status = md.Status.DOWNLOADING

        def fake_one(spec):
            if spec.key == "model":
                spec.dest.write_bytes(b"x")  # required succeeds
            else:
                raise md._DownloadError("vad host down", "http")  # optional fails

        with mock.patch.object(md, "_download_one", side_effect=fake_one):
            md._run()

        self.assertEqual(md.get_state()["status"], "done")
        self.assertTrue(md.is_ready(), "ready despite optional VAD failure")

    def test_required_model_failure_blocks(self):
        d = Path(tempfile.mkdtemp())
        md.configure(d / "ggml-large-v3.bin", d / "ggml-silero-v6.2.0.bin")
        with md._lock:
            md._state.files = {s.key: md.FileProgress(key=s.key, total=s.size) for s in md._SPECS}
            md._state.status = md.Status.DOWNLOADING

        with mock.patch.object(md, "_download_one", side_effect=md._DownloadError("offline", "offline")):
            md._run()

        self.assertEqual(md.get_state()["status"], "error")
        self.assertFalse(md.is_ready())


if __name__ == "__main__":
    unittest.main()

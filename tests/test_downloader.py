"""Offline tests for the model downloader's state logic (no network).

The real network download path (HF redirect, resume, SHA-256) is exercised
separately; these cover the readiness/state/integrity-pinning logic that must
hold deterministically.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work" / "transcribe_app"))

import model_downloader as md  # noqa: E402


class DownloaderStateTests(unittest.TestCase):
    def test_is_ready_tracks_required_model_only(self):
        d = Path(tempfile.mkdtemp())
        model, vad = d / "ggml-large-v3.bin", d / "ggml-silero-v6.2.0.bin"
        md.configure(model, vad)
        self.assertFalse(md.is_ready(), "not ready while required model missing")
        model.write_bytes(b"x")
        self.assertTrue(md.is_ready(), "ready once required model present (VAD optional)")

    def test_get_state_shape(self):
        d = Path(tempfile.mkdtemp())
        md.configure(d / "m.bin", d / "v.bin")
        state = md.get_state()
        for key in ("status", "files", "downloaded", "total", "percent",
                    "ready", "speed_bps", "eta_seconds", "error"):
            self.assertIn(key, state)
        self.assertEqual(state["status"], "idle")

    def test_specs_pin_integrity(self):
        md.configure(Path("/nope/m.bin"), Path("/nope/v.bin"))
        specs = {s.key: s for s in md._SPECS}
        self.assertEqual(len(specs["model"].sha256), 64)
        self.assertFalse(specs["model"].optional)
        self.assertTrue(specs["vad"].optional)
        self.assertTrue(specs["model"].url.startswith("https://huggingface.co/"))


if __name__ == "__main__":
    unittest.main()

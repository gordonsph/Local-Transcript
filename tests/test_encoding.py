"""Regression test for the frozen-app ASCII decode crash.

A Finder-launched .app inherits no locale, so Python's text mode defaults to
ASCII and crashes decoding non-ASCII (e.g. Cantonese) whisper-cli output. The fix
is explicit encoding="utf-8" on the subprocess (plus PYTHONUTF8 in the bundle).
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "work" / "transcribe_app" / "app.py"


class EncodingTests(unittest.TestCase):
    def test_ascii_decode_of_cjk_raises(self):
        # The bug class: decoding UTF-8 CJK as ASCII fails exactly like the report
        # ("'ascii' codec can't decode byte 0xe6 …").
        with self.assertRaises(UnicodeDecodeError):
            "你好".encode("utf-8").decode("ascii")

    def test_subprocess_utf8_decode_survives_cjk(self):
        # The fix: reading a child's CJK output with encoding="utf-8" must not crash.
        child = [sys.executable, "-c", "import sys; sys.stdout.buffer.write('你好世界'.encode('utf-8'))"]
        out = subprocess.check_output(child, encoding="utf-8", errors="replace")
        self.assertIn("你好世界", out)

    def test_whisper_subprocess_declares_utf8(self):
        # Guard: the whisper-cli Popen must pin encoding so it never inherits ASCII.
        src = APP.read_text(encoding="utf-8")
        idx = src.find("subprocess.Popen(")
        self.assertNotEqual(idx, -1, "whisper-cli Popen not found")
        chunk = src[idx:idx + 600]
        self.assertIn('encoding="utf-8"', chunk)
        self.assertIn('errors="replace"', chunk)


if __name__ == "__main__":
    unittest.main()

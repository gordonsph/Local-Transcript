from __future__ import annotations

import io
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "work" / "transcribe_app" / "app.py"


def load_app_module():
    spec = importlib.util.spec_from_file_location("local_transcript_app", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeThread:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return None


class SourceJobTests(unittest.TestCase):
    def setUp(self):
        self.module = load_app_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module.OUTPUT_ROOT = self.root / "outputs"
        self.module.DEFAULT_RESULT_ROOT = self.module.OUTPUT_ROOT / "results"
        self.module.jobs.clear()
        self.client = self.module.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_safe_filename_from_url_preserves_media_extension(self):
        filename = self.module.safe_filename_from_url(
            "https://example.com/archive/Quarterly%20Review.m4a?token=private"
        )
        # The sanitizer preserves the real name (incl. spaces and Unicode); it
        # only strips path separators / control chars.
        self.assertEqual(filename, "Quarterly Review.m4a")

    def test_safe_filename_from_url_preserves_cjk(self):
        filename = self.module.safe_filename_from_url("https://example.com/%E7%B2%B5%E8%AA%9E.mp3")
        self.assertEqual(filename, "粵語.mp3")

    def test_url_source_downloads_to_local_source_folder_and_records_metadata(self):
        def fake_download(url, destination_dir):
            destination_dir.mkdir(parents=True, exist_ok=True)
            path = destination_dir / "meeting.mp3"
            path.write_bytes(b"audio")
            return path

        with (
            mock.patch.object(self.module, "download_url_to_source", side_effect=fake_download, create=True),
            mock.patch.object(self.module.threading, "Thread", FakeThread),
        ):
            response = self.client.post(
                "/api/jobs",
                data={
                    "source_type": "url",
                    "source_url": "https://example.com/media/meeting.mp3",
                    "language": "en",
                    "format": "txt",
                    "output_location": str(self.root / "results"),
                },
            )

        self.assertEqual(response.status_code, 202)
        payload = response.get_json()
        self.assertEqual(payload["source_type"], "url")
        self.assertEqual(payload["source_name"], "meeting.mp3")
        self.assertEqual(payload["source_url"], "https://example.com/media/meeting.mp3")
        self.assertEqual(payload["saved_source_filename"], "meeting.mp3")
        self.assertTrue(Path(payload["source_path"]).is_file())
        self.assertIn("/source/", payload["source_path"])

    def test_live_source_persists_uploaded_recording_and_records_metadata(self):
        with mock.patch.object(self.module.threading, "Thread", FakeThread):
            response = self.client.post(
                "/api/jobs",
                data={
                    "source_type": "live",
                    "audio": (io.BytesIO(b"recorded audio bytes"), "live-recording.webm"),
                    "language": "yue",
                    "format": "all",
                    "output_location": str(self.root / "results"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 202)
        payload = response.get_json()
        self.assertEqual(payload["source_type"], "live")
        self.assertEqual(payload["source_name"], "live-recording.webm")
        self.assertEqual(payload["saved_source_filename"], "live-recording.webm")
        source_path = Path(payload["source_path"])
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_bytes(), b"recorded audio bytes")
        self.assertIn("/source/", str(source_path))


if __name__ == "__main__":
    unittest.main()

"""Settings: default language + custom model-path override (v1.1.0, issues #1/#3)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work" / "transcribe_app"))
import app  # noqa: E402


class SettingsTests(unittest.TestCase):
    def setUp(self):
        # Redirect settings to a throwaway file so we never touch real config.
        self._tmp = tempfile.mkdtemp()
        self._orig = app.SETTINGS_PATH
        app.SETTINGS_PATH = Path(self._tmp) / "settings.json"
        self.client = app.app.test_client()

    def tearDown(self):
        app.SETTINGS_PATH = self._orig

    def test_default_language_falls_back_to_yue(self):
        self.assertEqual(app.default_language(), "yue")
        app.save_settings({"default_language": "klingon"})  # invalid -> fallback
        self.assertEqual(app.default_language(), "yue")
        app.save_settings({"default_language": "en"})
        self.assertEqual(app.default_language(), "en")

    def test_active_model_path_falls_back_when_override_invalid(self):
        app.save_settings({"model_path": "/no/such/model.bin"})
        self.assertEqual(app.active_model_path(), app.MODEL_PATH)

    def test_post_settings_validates_language(self):
        ok = self.client.post("/api/settings", json={"default_language": "ja"})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.get_json()["default_language"], "ja")
        bad = self.client.post("/api/settings", json={"default_language": "zz"})
        self.assertEqual(bad.status_code, 400)

    def test_post_settings_rejects_wrong_size_model(self):
        # /etc/hosts exists but is nowhere near the large-v3 size -> rejected on apply.
        res = self.client.post("/api/settings", json={"model_path": "/etc/hosts"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("large-v3", res.get_json()["error"])

    def test_post_settings_clears_override_with_empty_path(self):
        app.save_settings({"model_path": "/whatever.bin"})
        res = self.client.post("/api/settings", json={"model_path": ""})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["model_path"], "")

    def test_get_settings_shape(self):
        keys = set(self.client.get("/api/settings").get_json())
        self.assertTrue({"default_language", "model_path", "active_model_path", "model_ready"} <= keys)


if __name__ == "__main__":
    unittest.main()

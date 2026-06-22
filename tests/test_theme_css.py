from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "work" / "transcribe_app" / "static" / "styles.css"
TEMPLATE = ROOT / "work" / "transcribe_app" / "templates" / "index.html"


class ThemeCssTests(unittest.TestCase):
    def test_stylesheet_declares_system_dark_theme_tokens(self):
        css = CSS.read_text(encoding="utf-8")

        self.assertIn("color-scheme: light dark;", css)
        self.assertNotIn("color-scheme: light;", css)

        dark_match = re.search(
            r"@media\s*\(prefers-color-scheme:\s*dark\)\s*{\s*:root\s*{(?P<body>.*?)\n\s*}\s*\n}",
            css,
            re.S,
        )
        self.assertIsNotNone(dark_match)

        dark_body = dark_match.group("body")
        for token in (
            "--canvas",
            "--surface",
            "--surface-2",
            "--inset",
            "--ink",
            "--muted",
            "--line",
            "--disabled-bg",
            "--disabled-ink",
        ):
            self.assertRegex(dark_body, rf"{re.escape(token)}\s*:")

    def test_primary_disabled_state_uses_dedicated_theme_tokens(self):
        css = CSS.read_text(encoding="utf-8")

        primary_disabled = re.search(r"\.primary:disabled\s*{(?P<body>.*?)\n}", css, re.S)
        self.assertIsNotNone(primary_disabled)
        self.assertIn("background: var(--disabled-bg);", primary_disabled.group("body"))
        self.assertIn("color: var(--disabled-ink);", primary_disabled.group("body"))

        record_disabled = re.search(r"\.record-button:disabled\s*{(?P<body>.*?)\n}", css, re.S)
        self.assertIsNotNone(record_disabled)
        self.assertIn("background: var(--disabled-bg);", record_disabled.group("body"))
        self.assertIn("color: var(--disabled-ink);", record_disabled.group("body"))

    def test_template_declares_light_and_dark_theme_colors(self):
        html = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            '<meta name="theme-color" media="(prefers-color-scheme: light)" content="#0b7f68">',
            html,
        )
        self.assertIn(
            '<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0b0e0d">',
            html,
        )
        self.assertNotIn('<meta name="theme-color" content="#0b7f68">', html)


if __name__ == "__main__":
    unittest.main()

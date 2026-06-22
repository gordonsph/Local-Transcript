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
        self.assertIsNotNone(dark_match, "dark theme :root block must exist")

        # Core Liquid Glass tokens that must be redefined for the dark theme.
        dark_body = dark_match.group("body")
        for token in ("--accent", "--label", "--sidebar", "--content", "--inset", "--sep"):
            self.assertRegex(dark_body, rf"{re.escape(token)}\s*:", f"{token} missing from dark theme")

    def test_hidden_attribute_is_globally_enforced(self):
        # display: grid/flex on .move-banner/.readout-grid/etc. must not defeat
        # the hidden attribute that gates the banner, setup stats, and monitor.
        css = CSS.read_text(encoding="utf-8")
        self.assertRegex(css, r"\[hidden\]\s*{\s*display:\s*none\s*!important;\s*}")

    def test_primary_disabled_state_is_styled(self):
        css = CSS.read_text(encoding="utf-8")
        primary_disabled = re.search(r"\.primary:disabled\s*{(?P<body>.*?)}", css, re.S)
        self.assertIsNotNone(primary_disabled, ".primary:disabled must be styled")
        self.assertIn("cursor: not-allowed", primary_disabled.group("body"))

    def test_readable_section_header_uses_label_2_not_label_3(self):
        # --label-3 is icon/chevron/disabled-only; it fails WCAG AA as body text
        # on the translucent sidebar glass. The "SOURCE" group header is readable
        # text, so it must use --label-2.
        css = CSS.read_text(encoding="utf-8")
        rule = re.search(r"\.side-section\s*{(?P<body>.*?)}", css, re.S)
        self.assertIsNotNone(rule, ".side-section must be styled")
        body = rule.group("body")
        self.assertIn("var(--label-2)", body, ".side-section header must use --label-2")
        self.assertNotIn("var(--label-3)", body, ".side-section must not use icon-only --label-3")

    def test_toolbar_status_badge_is_wired_for_live_updates(self):
        # The toolbar badge must have an id + data-state (so app.js keeps it in
        # sync with the sidebar pill) and the dot must react to data-state.
        html = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('id="tbStatus"', html)
        self.assertIn('id="tbStatusText"', html)
        css = CSS.read_text(encoding="utf-8")
        self.assertIn('.tb-status[data-state="busy"] .status-dot', css)
        self.assertIn('.tb-status[data-state="error"] .status-dot', css)

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

"""The palette must stay small, deliberate and impossible to drift.

Colours used to change between revisions without anyone asking: a border here, a
hover shade there, each written as a fresh hex value. By 0.4.12 the stylesheet held
113 colour literals and 91 distinct values, of which only 10 had ever been chosen.
Nothing was watching, so nothing stopped it.

These tests watch. They are deliberately about the SHAPE of the stylesheet rather
than its appearance, because appearance is a taste question and shape is not.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
UI = ROOT / "ui.html"

# The blocks that are ALLOWED to name a colour. Everything else must use a token.
TOKEN_BLOCKS = (
    ':root, [data-theme="light"]',
    '[data-theme="dark"]',
    "body.live-mode",
    '[data-theme="dark"] body.live-mode',
)

# A colour literal, but not an id selector like "#fee-selected": a real value is
# never followed by another identifier character.
COLOUR = re.compile(r"#(?:[0-9a-fA-F]{3,8})(?![0-9a-zA-Z_-])"
                    r"|\b(?:rgba?|hsla?)\s*\(")


def stylesheet() -> str:
    text = UI.read_text(encoding="utf-8")
    return text[text.index("<style>") + len("<style>"):text.index("</style>")]


def strip_comments(css: str) -> str:
    """Comments explain the rule; they are not the rule."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def token_block(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
    return match.group(1) if match else ""


def token_names(block: str) -> set:
    return set(re.findall(r"(--[a-z0-9-]+)\s*:", block))


class PaletteShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = strip_comments(stylesheet())

    def test_no_colour_is_named_outside_the_palette_blocks(self):
        """The whole point. A new hardcoded shade fails here, not in a revision.

        This is what 89 accidental colours looked like: every one of them was
        reasonable on the day it was added, and nothing objected.
        """
        outside = self.css
        for selector in TOKEN_BLOCKS:
            block = re.search(re.escape(selector) + r"\s*\{.*?\}", self.css, re.S)
            if block:
                outside = outside.replace(block.group(0), "")
        found = COLOUR.findall(outside)
        self.assertEqual(
            found, [],
            "These colours are named outside the palette blocks. Give each one a role "
            f"in the palette instead: {sorted(set(found))}")

    def test_light_and_dark_define_exactly_the_same_roles(self):
        """A role missing from dark silently inherits the light value.

        That is the classic dark-theme defect: one white border, one unreadable
        label, on the one screen nobody opened in the dark.
        """
        light = token_names(token_block(self.css, ':root, [data-theme="light"]'))
        dark = token_names(token_block(self.css, '[data-theme="dark"]'))
        self.assertTrue(light, "the light palette defines no tokens at all")
        self.assertEqual(sorted(light - dark), [], "dark is missing these roles")
        self.assertEqual(sorted(dark - light), [], "dark invents roles light does not have")

    def test_mainnet_only_overrides_roles_it_already_has(self):
        """Mainnet is a louder reading of the palette, not a second palette."""
        light = token_names(token_block(self.css, ':root, [data-theme="light"]'))
        for selector in ("body.live-mode", '[data-theme="dark"] body.live-mode'):
            with self.subTest(selector=selector):
                overrides = token_names(token_block(self.css, selector))
                self.assertTrue(overrides, f"{selector} overrides nothing")
                self.assertEqual(sorted(overrides - light), [],
                                 f"{selector} declares roles the palette does not have")

    def test_mainnet_is_alarming_in_both_themes(self):
        """The safety signal has to survive the theme change.

        On real Bitcoin the operator must notice. A mainnet header that renders
        calm in dark mode is a safety regression, not a style choice.
        """
        light = token_block(self.css, "body.live-mode")
        dark = token_block(self.css, '[data-theme="dark"] body.live-mode')
        for name, block in (("light", light), ("dark", dark)):
            with self.subTest(theme=name):
                self.assertTrue(block, f"mainnet has no {name} treatment")
                self.assertIn("--header", block)
                self.assertIn("--canvas", block)
                self.assertIn("--accent", block)

    def test_the_palette_stays_small_enough_to_hold_in_your_head(self):
        """Five hues, assigned to roles. The ceiling is deliberate.

        If this fails, the question is not how to raise the limit: it is which of
        the new roles is really an existing one under a different name.
        """
        roles = token_names(token_block(self.css, ':root, [data-theme="light"]'))
        self.assertLessEqual(
            len(roles), 30,
            f"the palette has grown to {len(roles)} roles; it was designed as a "
            "handful of hues filling fixed roles")


class ThemeToggleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = UI.read_text(encoding="utf-8")

    def test_the_page_offers_a_toggle(self):
        self.assertIn('id="theme-toggle"', self.html)

    def test_the_toggle_is_wired_and_can_never_break_the_app(self):
        """A decoration must not be able to take down a signing screen.

        This code runs in front of every other line of the app, so an exception in
        it would cost the signing screen, not the theme.
        """
        self.assertIn("globals.__applyTheme = apply", self.html)
        # The browser global is looked up rather than assumed, every API it touches
        # is probed first, and the whole block is wrapped.
        self.assertIn('typeof window === "undefined" ? {} : window', self.html)
        self.assertIn('typeof matchMedia === "function"', self.html)
        self.assertIn("document.documentElement || document.body", self.html)
        self.assertIn("} catch { /* decoration only: never take the signing screen down */ }",
                      self.html)

    def test_no_stale_palette_name_survives_anywhere(self):
        """The old role names are gone, so nothing can quietly depend on one.

        --green, --mint, --warn, --red and --navy were the 0.4.12 palette. A rule
        still referencing one would resolve to nothing and render as an unset
        colour, which looks like a rendering bug rather than a stale name.
        """
        for stale in ("var(--green)", "var(--mint)", "var(--warn)", "var(--red)",
                      "var(--navy)"):
            with self.subTest(token=stale):
                self.assertNotIn(stale, self.html,
                                 f"{stale} is from the old palette and no longer exists")

    def test_ink_and_accent_stay_distinguishable_in_both_themes(self):
        """Contrast on the two colours an operator must actually read.

        Addresses and amounts are read character by character. If a theme makes
        that harder, the theme is wrong, whatever it looks like.
        """
        def luminance(value: str) -> float:
            digits = value.lstrip("#")
            if len(digits) == 3:
                digits = "".join(c * 2 for c in digits)
            channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                      for c in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def contrast(a: str, b: str) -> float:
            high, low = sorted((luminance(a), luminance(b)), reverse=True)
            return (high + 0.05) / (low + 0.05)

        css = strip_comments(stylesheet())
        for selector in (':root, [data-theme="light"]', '[data-theme="dark"]'):
            with self.subTest(theme=selector):
                block = token_block(css, selector)
                values = dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", block))
                for surface in ("--canvas", "--paper"):
                    with self.subTest(surface=surface):
                        ratio = contrast(values["--ink"], values[surface])
                        self.assertGreaterEqual(
                            ratio, 7.0,
                            f"{selector}: --ink on {surface} is {ratio:.1f}:1, below the "
                            "7:1 this app holds itself to for reading an address")


if __name__ == "__main__":
    unittest.main()

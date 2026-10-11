"""Every page-script suite runs, and losing one is a failure, not silence.

`tests/ui_*.cjs` are the only tests that execute the real page script: they read
`ui.html`, take the `<script>` block and run it in a Node `vm` with a hand-built
DOM. Three v0.6.8 findings live in that layer -- CT-05's address-bar rewrite,
CT-52's busy ownership and CT-53's developer-mode dialog -- and the workflow runs
them with a glob (`for test in tests/ui_*.cjs`). A glob cannot notice a suite that
was deleted, renamed out of the pattern, or broken on the day it was written:
nothing runs, and nothing says so.

This module gives every present suite a loadable Python test. That makes the page
scripts part of `python -m unittest discover -s tests` on every platform, and it
lets a ledger row cite a `.cjs` suite through a name
`tests/test_ledger_completeness.py` can resolve -- it reads `tests/*.py` citations
only, so without this a JS pin is unquotable evidence.

`EXPECTED` is deliberately a list and not the glob itself: a suite that quietly
disappears has to fail this file, and adding one has to be a deliberate edit.
"""

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
NODE = shutil.which("node")

EXPECTED = (
    "ui_amount_entry",
    "ui_broadcast_outcome",
    "ui_busy_feedback",
    "ui_busy_ownership",
    "ui_developer_mode",
    "ui_large_amount",
    "ui_send_mode",
    "ui_signer_slots",
    "ui_state_reuse",
    "ui_theme",
    # CT-05: the token leaves the fragment and the address bar behind it.
    "ui_token_history",
)


class UiScriptTests(unittest.TestCase):
    """One case per page-script suite, plus the roster itself."""

    def test_every_expected_page_script_suite_is_present(self):
        present = sorted(path.stem for path in TESTS.glob("ui_*.cjs"))
        self.assertEqual(
            present,
            sorted(EXPECTED),
            "the page-script roster changed: a suite was deleted or renamed out of "
            "the `tests/ui_*.cjs` glob, or a new one was added without being listed "
            "here. Either way the workflow's glob and this list disagree, and the "
            "unlisted suite would be evidence nobody runs.",
        )


def _case(name):
    def test(self):
        script = TESTS / ("%s.cjs" % name)
        self.assertIsNotNone(
            NODE,
            "node is not on PATH, so %s cannot run; every platform in the release "
            "matrix ships it" % script.name,
        )
        completed = subprocess.run(
            [NODE, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "%s failed under node:\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (script.name, completed.stdout.strip(), completed.stderr.strip()),
        )
        self.assertTrue(
            completed.stdout.strip(),
            "%s printed nothing: a suite that asserts nothing passes silently"
            % script.name,
        )

    test.__name__ = "test_%s" % name
    test.__doc__ = "%s must pass under node." % ("%s.cjs" % name)
    return test


for _name in EXPECTED:
    setattr(UiScriptTests, "test_%s" % _name, _case(_name))


if __name__ == "__main__":
    unittest.main()

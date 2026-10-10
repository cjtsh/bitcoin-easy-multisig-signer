"""The source archive is scanned for secrets before it is uploaded.

GitHub secret scanning and push protection are enabled at the platform level --
scripts/check-platform-state.sh records that in releases/platform-state.json --
but until 0.6.8 nothing in the repository asserted it, and nothing read the bytes
a tag actually publishes. A credential that reaches a tag is public for as long
as the tag exists; deleting the file afterwards does not unpublish the commit.

This is CT-86. The scanner is detect-secrets, pinned by version and hash in
requirements-ci.lock -- the same ``--require-hashes`` set the source job already
installs, and deliberately not a floating action, which would be a new
unverified input on the release path. scripts/scan-secrets.py is the wrapper that
decides the exit code, and the source job runs it over the extracted tarball
before the upload-artifact step.

Red case: this module plants a canary in a temporary tree and requires the scan
to refuse it. The canary is assembled at run time and never written down: the
archive ships both tests/ and ci/, so a literal token in this module or in the
workflow would be a finding of the very scan it tests.

Break-and-watch: remove the scan step (ArchiveScanStepTests catches it), or make
the wrapper's finding path return 0 (CanaryTests catches it).
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

try:
    import yaml
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The checkout keeps the canonical workflow under .github; the source archive
# keeps the generated copy at ci/. Pick whichever exists so these checks also
# run against the archived source, which is where a missing file shows up.
ACTIVE = ROOT / ".github/workflows/build-candidate.yml"
if not ACTIVE.is_file():
    ACTIVE = ROOT / "ci/build-candidate.yml"

SCANNER = ROOT / "scripts/scan-secrets.py"

# A secret a scanner must catch, in pieces. `github_token` and the value are two
# separate literals on two separate lines: a line that spells a keyword next to a
# token is itself the kind of finding this scan exists to report.
CANARY_KEY = "github_token"
CANARY_TOKEN = "gh" + "p_" + "012345678901234567890123456789012345"


def canary_text() -> str:
    """The planted secret, as it would look in a file someone committed."""
    return f'{CANARY_KEY} = "{CANARY_TOKEN}"\n'


def scanner_module():
    """Import scripts/scan-secrets.py by path (its name is not an identifier)."""
    if not SCANNER.is_file():
        raise AssertionError(f"{SCANNER} does not exist")
    spec = importlib.util.spec_from_file_location("scan_secrets", SCANNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_scan(*paths: pathlib.Path) -> subprocess.CompletedProcess:
    """Run the wrapper the way the workflow does, as a program."""
    return subprocess.run(
        [sys.executable, str(SCANNER), *[str(path) for path in paths]],
        capture_output=True,
        text=True,
        check=False,
    )


def write_lf(path: pathlib.Path, body: str) -> None:
    path.write_text(body, encoding="utf-8", newline="\n")


class CanaryTests(unittest.TestCase):
    """The red case: a planted canary must be caught, or the control is theatre."""

    def test_a_planted_canary_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_lf(pathlib.Path(tmp) / "planted.env", canary_text())
            result = run_scan(tmp)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("planted.env", result.stdout)
        self.assertIn("GitHub Token", result.stdout)

    def test_a_tree_without_secrets_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_lf(pathlib.Path(tmp) / "module.py", 'VERSION = "0.6.8"\n')
            result = run_scan(tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok:", result.stdout)

    def test_the_recorded_status_lines_do_not_hide_a_planted_secret(self):
        """The status exclusion is line-shaped, not file-shaped.

        releases/platform-state.json records the platform's scanning posture, so
        it holds `"secret_scanning": "enabled"` -- which the keyword detector
        reports. The wrapper excludes exactly that line; a credential on any
        other line of the same file must still be caught.
        """
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            write_lf(
                folder / "platform-state.json",
                '{\n  "secret_scanning_push_protection": "enabled",\n'
                '  "generated_by": "scripts/check-platform-state.sh"\n}\n'
                + canary_text(),
            )
            result = run_scan(folder)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("platform-state.json", result.stdout)
        self.assertIn("GitHub Token", result.stdout)

    def test_an_allowlisted_line_is_not_a_finding(self):
        """A documented exception has to work, or nobody will use one."""
        with tempfile.TemporaryDirectory() as tmp:
            write_lf(pathlib.Path(tmp) / "fixture.env",
                     canary_text().rstrip("\n") + "  # pragma: allowlist secret\n")
            result = run_scan(tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_missing_tree_is_refused_not_called_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_scan(pathlib.Path(tmp) / "not-there")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("not-there", result.stderr)

    def test_an_empty_tree_is_refused_not_called_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_scan(tmp)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("empty", result.stderr)

    def test_the_wrapper_refuses_a_scanner_it_was_not_pinned_to(self):
        module = scanner_module()
        self.assertEqual(module.require_pinned_scanner(module.SCANNER_VERSION),
                         module.SCANNER_VERSION)
        with self.assertRaises(module.Refusal):
            module.require_pinned_scanner("1.4.0")


class ScannerPinTests(unittest.TestCase):
    """The scanner is an input to the release, so it is pinned like one."""

    def test_the_lock_pins_the_scanner_by_version_and_hash(self):
        module = scanner_module()
        declared = (ROOT / "requirements-ci.txt").read_text(encoding="utf-8")
        self.assertIn(f"{module.SCANNER_DISTRIBUTION}=={module.SCANNER_VERSION}",
                      declared,
                      "requirements-ci.txt does not pin the scanner the wrapper runs")
        locked = (ROOT / "requirements-ci.lock").read_text(encoding="utf-8")
        entry = re.search(
            rf"^{re.escape(module.SCANNER_DISTRIBUTION)}==(\S+)[^\n]*\n((?:[ \t]+[^\n]*\n)+)",
            locked,
            re.MULTILINE,
        )
        self.assertIsNotNone(entry,
                             f"requirements-ci.lock does not pin {module.SCANNER_DISTRIBUTION}")
        self.assertEqual(entry.group(1), module.SCANNER_VERSION)
        self.assertIn("--hash=sha256:", entry.group(2),
                      "the scanner's lock entry carries no artifact hash, so a "
                      "substituted wheel would install happily")

    def test_the_application_locks_do_not_carry_the_scanner(self):
        """It is a test input; a scanner must never reach a shipped bundle."""
        for name in ("requirements-desktop.lock", "requirements-desktop-windows.lock"):
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(lock=name):
                self.assertNotIn("detect-secrets", text)


@unittest.skipIf(yaml is None, "PyYAML is not installed; the workflow checks are skipped")
class ArchiveScanStepTests(unittest.TestCase):
    """The scan reads the archive, not the worktree, and runs before the upload."""

    def setUp(self):
        recipe = yaml.safe_load(ACTIVE.read_text(encoding="utf-8"))
        self.steps = recipe["jobs"]["source"]["steps"]

    def step_named(self, name: str):
        for index, step in enumerate(self.steps):
            if step.get("name") == name:
                return index, step
        self.fail(f"the source job has no step named {name!r}")

    def test_the_scan_reads_the_archive_before_it_is_uploaded(self):
        scan_index, scan = self.step_named("Scan the source archive for secrets")
        run = scan.get("run", "")
        self.assertIn("scripts/scan-secrets.py", run)
        self.assertIn("tar xzf", run,
                      "the scan must read the tarball's own bytes, not the worktree "
                      "it was built from")
        ordering = {}
        for index, step in enumerate(self.steps):
            if "build-source.sh" in step.get("run", ""):
                ordering["build"] = index
            if str(step.get("uses", "")).startswith("actions/upload-artifact@"):
                ordering["upload"] = index
        self.assertIn("build", ordering, "no step builds the source archive")
        self.assertIn("upload", ordering, "no step uploads the source archive")
        self.assertLess(ordering["build"], scan_index,
                        "the scan must run after the archive exists to be scanned")
        self.assertLess(scan_index, ordering["upload"],
                        "the scan must run before the archive leaves the runner")

    def test_the_scan_carries_a_positive_control(self):
        _, scan = self.step_named("Scan the source archive for secrets")
        run = scan.get("run", "")
        self.assertIn("canary", run.lower(),
                      "the step never proves the scanner can fail on this runner")
        self.assertIn("exit 1", run,
                      "a control that cannot fail the build proves nothing")

    def test_the_workflow_that_carries_the_control_is_not_itself_a_finding(self):
        """This file is inside the archive, so the control must not be a token."""
        text = ACTIVE.read_text(encoding="utf-8")
        self.assertNotIn("ghp_", text,
                         "the workflow spells a token, and the archive ships the workflow")
        result = run_scan(ACTIVE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TheScanReadsItselfTests(unittest.TestCase):
    def test_this_module_is_not_itself_a_finding(self):
        """tests/ ships in the archive, so this module must survive its own scan."""
        result = run_scan(pathlib.Path(__file__))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_platform_record_is_not_a_finding(self):
        """releases/ ships too, and its scanning statuses look like assignments.

        This is the test that catches a dropped status exclusion: without it the
        shipped record reports two findings and the candidate build refuses.
        """
        result = run_scan(ROOT / "releases" / "platform-state.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

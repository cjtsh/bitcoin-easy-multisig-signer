"""Pin the Windows portability helpers every future build depends on.

The first unified 0.6.5 candidate failed the Windows job with 22 false test
failures before any binary was built (run 37407453856): bash -c from Windows
Python, CRLF scripts, POSIX 0600 asserts, and CWD-vs-tempdir cleanup. The
helpers in ``tests/support.py`` are the fix, and ``WINDOWS-PORT.md`` is the
written record. These tests fail if either is weakened, so 0.6.6, 0.7.x and
1.x do not spend hours rediscovering the same Windows quirks.

The 0.6.8 candidate (run 38082865187) added two more of the same shape: a fake
``gh`` that was only a shebang, which the differ's Python side could not exec,
and the release guards' ``shasum`` calls, which Git Bash does not provide.

No test here may skip: the Windows job refuses a suite that reports any skip.
"""

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import gui
import support
import workflow_harness

ROOT = Path(__file__).resolve().parent.parent


class BashHelperTests(unittest.TestCase):
    def test_bash_executable_is_usable(self):
        exe = support.bash_executable()
        self.assertTrue(exe, "bash_executable must return something")
        if sys.platform == "win32":
            self.assertTrue(
                exe == "bash" or Path(exe).is_file(),
                f"Windows bash must be a real file, got {exe!r}")

    def test_scripts_are_written_with_unix_newlines(self):
        path = support.write_lf_script("echo one\necho two")
        try:
            raw = path.read_bytes()
        finally:
            path.unlink(missing_ok=True)
        self.assertNotIn(b"\r\n", raw, "CRLF is a bash syntax error")
        self.assertIn(b"echo one\n", raw)

    def test_a_script_body_actually_runs(self):
        result = support.run_bash_script("echo marker-$((1+1))")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("marker-2", result.stdout)

    def test_syntax_check_accepts_valid_shell_and_rejects_broken_shell(self):
        self.assertEqual(support.bash_syntax_check("echo ok").returncode, 0)
        self.assertNotEqual(support.bash_syntax_check("if then fi").returncode, 0)

    def test_the_workflow_suite_uses_the_helper_not_bash_c(self):
        """Regression canary for the exact pattern that broke Windows CI."""
        text = (ROOT / "tests" / "test_workflow_config.py").read_text(encoding="utf-8")
        self.assertNotIn('["bash", "-c"', text,
                         "multiline bash -c from Python is unreliable on Windows")
        self.assertIn("run_bash_script", text)
        self.assertIn("bash_syntax_check", text)
        notary = (ROOT / "tests" / "test_notary_args.py").read_text(encoding="utf-8")
        self.assertNotIn('["bash"', notary,
                         "test_notary_args must go through support.run_bash_file")


class PrivateFileHelperTests(unittest.TestCase):
    def test_one_definition_of_privacy_lives_in_gui(self):
        """POSIX 0600 vs Windows profile-ACL is assert_private_file's job."""
        source = Path(gui.__file__).read_text(encoding="utf-8")
        self.assertIn("def assert_private_file", source)
        self.assertIn("os.name == \"nt\"", source)
        self.assertIn("0o600", source)

    def test_a_private_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            if sys.platform != "win32":
                os.chmod(target, 0o600)
            support.assert_private_file(self, target)

    def test_a_non_private_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            if sys.platform == "win32":
                # Windows privacy = inside the user's profile. A path outside
                # it must be refused; tempfile is inside, so plant one outside.
                outside = Path(os.environ.get("USERPROFILE") or Path.home()).parent / "dsh-outside-profile.json"
                outside.write_text("{}", encoding="utf-8")
                try:
                    support.assert_private_file(self, outside)
                except AssertionError:
                    pass  # refused, as required
                else:
                    self.fail("a file outside the user's profile must be refused")
                finally:
                    outside.unlink(missing_ok=True)
            else:
                os.chmod(target, 0o644)
                with self.assertRaises(AssertionError):
                    support.assert_private_file(self, target)


class HardeningPinPortabilityTests(unittest.TestCase):
    """The tripwire tests themselves must be Windows-portable.

    Candidate run 37464977050 failed the Windows job because HwiIdentityPins
    wrote a #!/bin/sh helper (CreateProcess: WinError 193) and the source
    archive job because PipToolsPinTests only looked under .github/workflows/
    while the archive ships recipes under ci/. Candidate run 38082865187 failed
    the Windows job because the platform-state differ's fake `gh` was written
    the same shebang-only way, and the archive job because the control
    inventory reopened the inline recipe lookup.
    """

    def test_hwi_identity_helpers_never_rely_on_a_shebang_alone(self):
        text = (ROOT / "tests" / "test_hardening_pins.py").read_text(encoding="utf-8")
        self.assertIn('if sys.platform == "win32"', text)
        self.assertIn("hwi.cmd", text)
        self.assertIn("@echo off", text)

    def test_the_platform_state_fake_gh_never_relies_on_a_shebang_alone(self):
        """Run 38082865187: WinError 193 from the differ's fake `gh`.

        Git Bash runs a `#!` script; the Python side of
        `scripts/check-platform-state.sh` execs it and Windows refuses.
        """
        text = (ROOT / "tests" / "test_platform_state.py").read_text(encoding="utf-8")
        self.assertIn('if sys.platform == "win32"', text)
        self.assertIn("gh.cmd", text)
        self.assertIn("@echo off", text)

    def test_recipe_lookups_go_through_the_shared_helper(self):
        """One resolver, so the ci/ fallback cannot be dropped a third time.

        0.6.6 caught PipToolsPinTests opening only .github/workflows/; 0.6.7
        caught ToolchainPinTests doing the same; 0.6.8 caught
        ControlInventoryTests doing it a third time. All now call
        support.find_build_recipe, and this holds that nothing reopens the
        inline two-path lookup to drift away from it again.
        """
        support_text = (ROOT / "tests" / "support.py").read_text(encoding="utf-8")
        self.assertIn('root / "ci" / name', support_text)
        self.assertIn('root / ".github" / "workflows" / name', support_text)
        for name in ("test_hardening_pins.py", "test_workflow_config.py",
                     "test_libusb_vendor.py", "test_controls_inventory.py"):
            text = (ROOT / "tests" / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                self.assertIn("find_build_recipe", text,
                              f"{name} must resolve build recipes through "
                              f"support.find_build_recipe")
                self.assertNotIn('root / "ci" / name', text,
                                 f"{name} must not reopen the inline lookup")

    def test_the_shared_resolver_finds_the_archived_copy(self):
        """The behaviour behind the list, provable without an archive."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ci").mkdir()
            archived = root / "ci" / "build-candidate.yml"
            archived.write_text("on: push\n", encoding="utf-8")
            self.assertEqual(
                support.find_build_recipe(root, "build-candidate.yml"), archived,
                "an archive ships the recipe as ci/build-candidate.yml")
            checkout = root / ".github" / "workflows" / "build-candidate.yml"
            checkout.parent.mkdir(parents=True)
            checkout.write_text("on: push\n", encoding="utf-8")
            self.assertEqual(
                support.find_build_recipe(root, "build-candidate.yml"), checkout,
                "the checkout copy is canonical when both exist")
            self.assertIsNone(
                support.find_build_recipe(root, "no-such-recipe.yml"),
                "a recipe that is in neither place must be reported missing")


class ReleaseChecksumPortabilityTests(unittest.TestCase):
    """The release guards' checksum steps must run on every runner.

    Candidate run 38082865187 failed three tests in test_publish_guards.py on
    Windows with `shasum: command not found`: Git Bash ships `sha256sum` and no
    `shasum`, macOS ships the opposite. The step harness defines a real shasum,
    so a body that checks real bytes still checks real bytes.
    """

    def test_the_step_harness_defines_a_real_shasum(self):
        shim = workflow_harness.SHASUM_SHIM
        self.assertIn("shasum() {", shim)
        self.assertIn("command -v sha256sum", shim)
        self.assertIn("command shasum", shim)
        preamble = workflow_harness.stub_preamble({}, Path("unused.tsv"))
        self.assertIn("shasum() {", preamble,
                      "every rendered step body must see the shasum")

    def test_the_shasum_shim_verifies_real_bytes_and_refuses_a_changed_one(self):
        body = workflow_harness.SHASUM_SHIM + textwrap.dedent(
            """
            set -euo pipefail
            printf 'payload\\n' > asset.bin
            digest="$(shasum -a 256 asset.bin | awk '{print $1}')"
            printf '%s  asset.bin\\n' "$digest" > SHA256SUMS
            shasum -a 256 -c SHA256SUMS
            printf 'changed\\n' > asset.bin
            if shasum -a 256 -c SHA256SUMS; then
              echo "a changed asset passed the checksum check" >&2
              exit 1
            fi
            echo "refused-the-change"
            """
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = support.run_bash_script(body, cwd=tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("asset.bin: OK", result.stdout)
        self.assertIn("refused-the-change", result.stdout)


if __name__ == "__main__":
    unittest.main()

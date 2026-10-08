"""Pin the Windows portability helpers every future build depends on.

The first unified 0.6.5 candidate failed the Windows job with 22 false test
failures before any binary was built (run 37407453856): bash -c from Windows
Python, CRLF scripts, POSIX 0600 asserts, and CWD-vs-tempdir cleanup. The
helpers in ``tests/support.py`` are the fix, and ``WINDOWS-PORT.md`` is the
written record. These tests fail if either is weakened, so 0.6.6, 0.7.x and
1.x do not spend hours rediscovering the same Windows quirks.

No test here may skip: the Windows job refuses a suite that reports any skip.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import gui
import support

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
        credentials = (ROOT / "tests" / "test_release_credentials.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            '["bash"', credentials,
            "test_release_credentials must go through support.bash_executable: a bare "
            "bash is the WSL launcher on Windows and exits 1 with no output",
        )
        self.assertIn("bash_executable", credentials)


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
    """The 0.6.6 tripwire tests themselves must be Windows-portable.

    Candidate run 37464977050 failed the Windows job because HwiIdentityPins
    wrote a #!/bin/sh helper (CreateProcess: WinError 193) and the source
    archive job because PipToolsPinTests only looked under .github/workflows/
    while the archive ships recipes under ci/.
    """

    def test_hwi_identity_helpers_never_rely_on_a_shebang_alone(self):
        text = (ROOT / "tests" / "test_hardening_pins.py").read_text(encoding="utf-8")
        self.assertIn('if sys.platform == "win32"', text)
        self.assertIn("hwi.cmd", text)
        self.assertIn("@echo off", text)

    def test_recipe_lookups_go_through_the_shared_helper(self):
        """One resolver, so the ci/ fallback cannot be dropped a third time.

        0.6.6 caught PipToolsPinTests opening only .github/workflows/; 0.6.7
        caught ToolchainPinTests doing the same; 0.6.8 caught CT-102's comment
        check doing it a third time, which the old pin missed because it only
        asked whether the module mentioned the helper somewhere. All of them
        now call support.find_build_recipe, and this also refuses the inline
        ROOT-anchored expression itself so a fourth repeat breaks a test.
        """
        support_text = (ROOT / "tests" / "support.py").read_text(encoding="utf-8")
        self.assertIn('root / "ci" / name', support_text)
        self.assertIn('root / ".github" / "workflows" / name', support_text)
        inline = ('ROOT / ".github" / "workflows" / name',
                  'self.root / ".github" / "workflows" / name',
                  'root / ".github" / "workflows" / name')
        for name in ("test_hardening_pins.py", "test_workflow_config.py",
                     "test_libusb_vendor.py"):
            text = (ROOT / "tests" / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                self.assertIn("find_build_recipe", text,
                              f"{name} must resolve build recipes through "
                              f"support.find_build_recipe")
                self.assertNotIn('root / "ci" / name', text,
                                 f"{name} must not reopen the inline lookup")
                for expression in inline:
                    self.assertNotIn(
                        expression, text,
                        f"{name} must not open a recipe under .github/workflows/ "
                        f"directly ({expression}); the source archive ships the "
                        f"recipes under ci/ and has no .github at all, which is "
                        f"how the 0.6.8 archive job failed on CT-102")


if __name__ == "__main__":
    unittest.main()

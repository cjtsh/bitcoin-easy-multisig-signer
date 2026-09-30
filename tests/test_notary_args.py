"""The notarisation credential choice, pinned.

The notarisation round trip cannot run without Apple credentials, so what can be
checked here is the decision of WHICH credentials to present. That is the part
most likely to be silently wrong, and getting it wrong means signing with
something the operator did not intend.

`scripts/notary-args.sh` is deliberately a separate script from build-macos.sh so
this logic has one home and can be exercised without a Mac, a certificate or an
Apple account.
"""

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTARY_ARGS = ROOT / "scripts/notary-args.sh"
BUILD_MACOS = ROOT / "scripts/build-macos.sh"

# Every variable that decides the credential route. Cleared from the inherited
# environment so a developer's own shell cannot change what these tests observe.
CREDENTIAL_VARS = ("MAC_NOTARY_PROFILE", "MAC_NOTARY_KEY_PATH", "MAC_NOTARY_KEY_ID",
                   "MAC_NOTARY_ISSUER_ID", "MAC_SIGN_IDENTITY", "RELEASE")
APP_VERSION = re.search(r'APP_VERSION = "([^"]+)"',
                        (ROOT / "version.py").read_text(encoding="utf-8")).group(1)


def clean_env(**overrides):
    env = {key: value for key, value in os.environ.items() if key not in CREDENTIAL_VARS}
    env.update(overrides)
    return env


class NotaryArgsTests(unittest.TestCase):
    def run_notary_args(self, **env):
        return subprocess.run(["bash", str(NOTARY_ARGS)], capture_output=True,
                              text=True, env=clean_env(**env), timeout=60)

    def test_no_route_configured_prints_nothing_and_is_not_an_error(self):
        """The caller decides whether missing credentials are fatal."""
        result = self.run_notary_args()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_a_keychain_profile_is_passed_through(self):
        result = self.run_notary_args(MAC_NOTARY_PROFILE="eas-notary")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["--keychain-profile", "eas-notary"])

    def test_a_complete_api_key_triple_is_passed_through(self):
        result = self.run_notary_args(MAC_NOTARY_KEY_PATH="/k.p8", MAC_NOTARY_KEY_ID="ABC",
                                      MAC_NOTARY_ISSUER_ID="ISSUER")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(),
                         ["--key", "/k.p8", "--key-id", "ABC", "--issuer", "ISSUER"])

    def test_a_partial_api_key_is_refused_rather_than_guessed(self):
        """Half a credential is a mistake, not an instruction to try anyway."""
        for provided in ({"MAC_NOTARY_KEY_PATH": "/k.p8"},
                         {"MAC_NOTARY_KEY_ID": "ABC"},
                         {"MAC_NOTARY_KEY_PATH": "/k.p8", "MAC_NOTARY_KEY_ID": "ABC"},
                         {"MAC_NOTARY_KEY_ID": "ABC", "MAC_NOTARY_ISSUER_ID": "ISSUER"}):
            with self.subTest(provided=sorted(provided)):
                result = self.run_notary_args(**provided)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(result.stdout, "")
                self.assertIn("all three", result.stderr)

    def test_both_routes_at_once_is_refused_as_ambiguous(self):
        result = self.run_notary_args(MAC_NOTARY_PROFILE="p", MAC_NOTARY_KEY_PATH="/k.p8",
                                      MAC_NOTARY_KEY_ID="A", MAC_NOTARY_ISSUER_ID="B")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("not both", result.stderr)


# The credential logic is pure shell and runs anywhere. Tests that EXECUTE
# build-macos.sh cannot: the script's first act is to refuse anything but macOS
# ("DMGs must be built and tested on macOS.").
#
# They are DELIBERATELY NOT SKIPPED elsewhere, they are not collected. The workflow
# refuses any skip outright - `grep -qE "skipped=[1-9]"` - because a silently skipped
# test can hide a missing dependency, and that guard is worth keeping intact. A
# platform that cannot run these is not a missing dependency, so the honest thing is
# for them not to exist there. They still run in the same workflow's macOS job, which
# is where the fail-closed behaviour actually matters.
def macos_only(target):
    """Mark a test class or method as macOS-only. Applied at import."""
    target._macos_only = True
    return target


def load_tests(loader, tests, pattern):
    if sys.platform == "darwin":
        return tests
    keep = unittest.TestSuite()
    for group in tests:
        for case in (group if isinstance(group, unittest.TestSuite) else [group]):
            method = getattr(case, getattr(case, "_testMethodName", ""), None)
            if not (getattr(method, "_macos_only", False)
                    or getattr(type(case), "_macos_only", False)):
                keep.addTest(case)
    return keep


@macos_only
class BuildFailsClosedTests(unittest.TestCase):
    """RELEASE=1 must never quietly produce an ad-hoc-signed artifact.

    The guard runs before the build, so these complete in well under a second and
    need no Mac toolchain, certificate or Apple account.
    """

    def run_build(self, **env):
        return subprocess.run(["bash", str(BUILD_MACOS), APP_VERSION], cwd=ROOT,
                              capture_output=True, text=True,
                              env=clean_env(**env), timeout=120)

    def test_the_unsigned_path_is_not_gated(self):
        """No RELEASE means an intentional test build, which needs no credentials.

        It gets past the credential guard; whatever fails afterwards is the point
        of this assertion, so only the guard's message is checked for absence.
        """
        result = self.run_build()
        self.assertNotIn("requires MAC_SIGN_IDENTITY and a notarisation credential",
                         result.stderr)

    def test_release_without_any_credential_is_refused(self):
        result = self.run_build(RELEASE="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("requires MAC_SIGN_IDENTITY and a notarisation credential",
                      result.stderr)

    def test_release_with_a_signing_identity_but_no_notary_route_is_refused(self):
        result = self.run_build(RELEASE="1", MAC_SIGN_IDENTITY="Developer ID Application: X")
        self.assertEqual(result.returncode, 1)
        self.assertIn("notarisation credential", result.stderr)

    def test_release_with_a_partial_key_is_refused_before_anything_is_built(self):
        result = self.run_build(RELEASE="1", MAC_SIGN_IDENTITY="Developer ID Application: X",
                                MAC_NOTARY_KEY_PATH="/k.p8")
        self.assertEqual(result.returncode, 1)
        self.assertIn("incompletely", result.stderr)

    def test_release_with_both_routes_is_refused(self):
        result = self.run_build(RELEASE="1", MAC_SIGN_IDENTITY="Developer ID Application: X",
                                MAC_NOTARY_PROFILE="p", MAC_NOTARY_KEY_PATH="/k.p8")
        self.assertEqual(result.returncode, 1)
        self.assertIn("incompletely", result.stderr)


class ReleaseGateTests(unittest.TestCase):
    """The notarized path's finish line, pinned.

    Both of these were wrong the first time and only a real notarized artifact
    revealed it, because the release path cannot be exercised without an Apple
    account. Since the whole point is that a later edit cannot quietly undo them,
    they are asserted here rather than trusted.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = BUILD_MACOS.read_text(encoding="utf-8")

    def test_the_dmg_and_the_app_are_both_stapled(self):
        """Both artifacts are stapled - but this does NOT fix offline for a downloader.

        The image is built from a copy of the app taken before either staple runs, so
        the app a downloader receives stays unstapled and Gatekeeper verifies it with
        an online lookup. Measured on the published v0.4.12 DMG: the image validates,
        the app inside reports "does not have a ticket stapled to it".

        Stapling `$app` is still worth pinning: it makes the copy in dist/
        self-contained for offline testing here, and an accidental removal would
        otherwise go unnoticed. Closing the downloader's offline gap needs the app
        notarized and stapled BEFORE the image is built, at the cost of a second Apple
        round trip; see PHASE-HANDOFF.md.
        """
        self.assertIn('xcrun stapler staple "$dmg"', self.text)
        self.assertIn('xcrun stapler staple "$app"', self.text)

    def test_the_dmg_and_the_app_are_both_validated(self):
        self.assertIn('xcrun stapler validate "$dmg"', self.text)
        self.assertIn('xcrun stapler validate "$app"', self.text)

    def test_gatekeeper_assesses_the_app_not_the_dmg(self):
        """A DMG is not code-signed, so spctl reports it as unsigned.

        Measured against a genuinely notarized and stapled image:
            spctl -a -t open  <dmg>  -> rejected, source=no usable signature
            spctl -a -t exec  <app>  -> accepted, Notarized Developer ID
        Assessing the DMG aborted a build that had notarized correctly.
        """
        gates = [line.strip() for line in self.text.splitlines()
                 if line.strip().startswith("spctl ")]
        self.assertEqual(len(gates), 1, f"expected exactly one Gatekeeper gate, found {gates}")
        self.assertIn('"$app"', gates[0], "the Gatekeeper gate must assess the app")
        self.assertNotIn('"$dmg"', gates[0],
                         "a DMG reports 'no usable signature' even when correctly notarized")


class BuildPythonSelectionTests(unittest.TestCase):
    """The build must be told which Python to use.

    Homebrew's python@3.12 keg ships python3.12 and deliberately NO python3, so the
    script's old advice ("put it first on PATH") could not be followed. Both the
    owner and a coding session had to invent a throwaway symlink directory to build
    at all, which is the tell that the advice was impossible.
    """

    def run_build(self, **env):
        return subprocess.run(["bash", str(BUILD_MACOS), APP_VERSION], cwd=ROOT,
                              capture_output=True, text=True,
                              env=clean_env(**env), timeout=120)

    def test_the_interpreter_is_selectable_and_defaults_to_python3(self):
        text = BUILD_MACOS.read_text(encoding="utf-8")
        self.assertIn('python_bin="${PYTHON:-python3}"', text,
                      "PYTHON must name the interpreter, defaulting to python3")

    def test_the_chosen_interpreter_builds_the_venv(self):
        """A hardcoded python3 there would silently ignore the override."""
        text = BUILD_MACOS.read_text(encoding="utf-8")
        self.assertIn('"$python_bin" -m venv .build-venv', text)
        self.assertNotIn("\npython3 -m venv .build-venv", text)

    @macos_only
    def test_a_missing_interpreter_is_refused_with_a_usable_command(self):
        result = self.run_build(PYTHON="python3.99-definitely-not-here")
        self.assertEqual(result.returncode, 1)
        self.assertIn("was not found on PATH", result.stderr)
        self.assertIn("PYTHON=python3.12 bash scripts/build-macos.sh", result.stderr)

    @macos_only
    def test_an_unsupported_interpreter_names_the_override(self):
        """Host-independent, using a stand-in interpreter that reports 3.14.

        The real python3 is 3.14 on the owner's Mac and 3.12 on a CI runner, so the
        guard cannot be exercised by relying on whichever one happens to be present.
        """
        with tempfile.TemporaryDirectory() as temporary:
            fake = pathlib.Path(temporary) / "python3"
            fake.write_text('#!/bin/sh\n'
                            'if [ "$1" = "-c" ]; then echo "3.14"; exit 0; fi\n'
                            'exit 1\n', encoding="utf-8")
            fake.chmod(0o755)
            result = self.run_build(PYTHON=str(fake))
        self.assertEqual(result.returncode, 1)
        self.assertIn("is Python 3.14", result.stderr)
        self.assertIn("PYTHON=python3.12 bash scripts/build-macos.sh", result.stderr)
        self.assertNotIn("put it first on PATH", result.stderr,
                         "the old PATH advice could not be followed on macOS")


if __name__ == "__main__":
    unittest.main()

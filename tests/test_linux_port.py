"""Checks that the Linux build cannot quietly do the wrong thing.

The macOS tests lint the audited pipeline; this module lints the Linux port's
own promises: the launcher is the reviewed one, the dependency lock was resolved
on Linux, every self-check has to say something, and the only release a
promotion may join is the version's own page.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import linux_entry  # noqa: E402  (the entry point under test, not a package)

WORKFLOW = ROOT / ".github" / "workflows" / "build-candidate.yml"
if not WORKFLOW.is_file():
    WORKFLOW = ROOT / "ci" / "build-candidate.yml"
BUILD_SCRIPT = ROOT / "scripts" / "build-linux.sh"
LOCK = ROOT / "requirements-desktop-linux.lock"
RUNTIME = ROOT / "vendor" / "appimage-runtime-x86_64"

# AppImage/type2-runtime, release 20251108, asset runtime-x86_64. Provenance is
# in vendor/README.md; the same digest is required by scripts/build-linux.sh.
REVIEWED_RUNTIME_SHA256 = "2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d"
# upstream libusb 1.0.30, the source the bundled Linux library is built from.
REVIEWED_LIBUSB_SOURCE_SHA256 = "fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class VendoredRuntimeTests(unittest.TestCase):
    """The launcher that decides whether the AppImage starts at all."""

    def test_the_vendored_runtime_is_the_reviewed_bytes(self):
        self.assertTrue(RUNTIME.is_file(), f"{RUNTIME} is missing from the source tree")
        self.assertEqual(sha256(RUNTIME), REVIEWED_RUNTIME_SHA256)

    def test_the_pinned_libusb_source_is_the_reviewed_one(self):
        source = ROOT / "vendor" / "libusb-1.0.30.tar.bz2"
        self.assertTrue(source.is_file())
        self.assertEqual(sha256(source), REVIEWED_LIBUSB_SOURCE_SHA256)


class LinuxLockTests(unittest.TestCase):
    """A lock that was resolved on another platform cannot be installed here."""

    @classmethod
    def setUpClass(cls):
        cls.text = LOCK.read_text(encoding="utf-8")
        cls.pins = {
            line.split("==", 1)[0]
            for line in cls.text.splitlines()
            if "==" in line and not line.startswith(" ") and not line.startswith("#")
        }

    def test_it_pins_the_linux_wheels(self):
        for package in ("hidapi", "libusb1", "hwi", "certifi", "requests", "pyinstaller"):
            self.assertIn(package, self.pins)

    def test_it_carries_no_other_platform_or_window_toolkit(self):
        for package in ("pywebview", "pyobjc", "macholib", "pythonnet"):
            self.assertNotIn(package, self.pins)

    def test_it_is_hash_pinned(self):
        self.assertIn("--generate-hashes", self.text)
        self.assertIn("--hash=sha256:", self.text)


class LinuxEntryPointTests(unittest.TestCase):
    """The artifact has to be able to prove itself, from a file, not a console."""

    def test_every_check_flag_is_dispatched(self):
        self.assertEqual(
            sorted(linux_entry.CHECKS),
            [
                "--dsh-check-bundle",
                "--dsh-check-devices",
                "--dsh-check-network",
                "--dsh-check-save",
                "--dsh-check-udev",
            ],
        )

    def test_report_writes_what_it_verified_to_the_named_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "check.log"
            with mock.patch.dict(os.environ, {"DSH_LINUX_CHECK_LOG": str(target)}):
                with contextlib.redirect_stdout(io.StringIO()):
                    linux_entry.report("checked")
            self.assertEqual(target.read_text(encoding="utf-8"), "checked\n")

    def test_report_writes_no_file_when_none_was_asked_for(self):
        # Windows cannot rmtree a directory that is still the process working
        # directory (WinError 32), so restore cwd before the TemporaryDirectory
        # context exits — addCleanup runs too late for that.
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                # A relative report path must be the only way a file could appear
                # here, so the working directory is the temporary one.
                with mock.patch.dict(os.environ, {}, clear=True):
                    os.chdir(tmp)
                    with contextlib.redirect_stdout(io.StringIO()):
                        linux_entry.report("checked")
                    self.assertEqual(list(Path(tmp).iterdir()), [])
            finally:
                os.chdir(original_cwd)

    def test_the_udev_installer_only_touches_system_rules_directly(self):
        self.assertEqual(linux_entry.SYSTEM_UDEV_RULES, Path("/usr/lib/udev/rules.d"))


class LinuxBuildScriptTests(unittest.TestCase):
    """What the script must refuse, and what it must prove."""

    @classmethod
    def setUpClass(cls):
        cls.script = BUILD_SCRIPT.read_text(encoding="utf-8")

    def test_it_pins_the_launcher_it_concatenates(self):
        self.assertIn(REVIEWED_RUNTIME_SHA256, self.script)
        self.assertIn('[[ "$runtime_sha" == "$REVIEWED_APPIMAGE_RUNTIME_SHA256" ]]', self.script)

    def test_it_pins_the_source_the_usb_library_is_built_from(self):
        self.assertIn(REVIEWED_LIBUSB_SOURCE_SHA256, self.script)
        self.assertIn("libusb-1.0.30.tar.bz2", self.script)

    def test_it_builds_only_on_linux_x86_64(self):
        self.assertIn('[[ "$(uname -s)" == "Linux" ]]', self.script)
        self.assertIn('[[ "$(uname -m)" == "x86_64" ]]', self.script)

    def test_it_refuses_a_version_version_py_does_not_declare(self):
        self.assertIn("version.py declares", self.script)

    def test_it_refuses_an_unhashed_environment(self):
        self.assertIn("--require-hashes", self.script)
        self.assertIn("changed since the environment was prepared", self.script)

    def test_a_silent_check_is_not_a_pass(self):
        self.assertIn("a silent pass is not a pass", self.script)
        for flag in linux_entry.CHECKS:
            self.assertIn(flag, self.script)

    def test_it_proves_the_packed_appimage_not_only_the_tree(self):
        self.assertIn("--appimage-offset", self.script)
        self.assertIn("--appimage-extract", self.script)
        self.assertIn("squashfs-root/AppRun", self.script)

    def test_it_ships_a_tarball_that_needs_no_fuse(self):
        self.assertIn("run-me.sh", self.script)
        self.assertIn("linux-x86_64.tar.gz", self.script)

    def test_the_artifact_name_has_no_spaces_in_it(self):
        # A file name with a space reaches the user as %20 in the download URL
        # and has to be quoted in every command that touches it.
        self.assertIn('ARTIFACT_NAME="Bitcoin-Easy-Signer"', self.script)
        self.assertNotIn('"$DISPLAY_NAME-v$version', self.script)
        self.assertIn('dist/$ARTIFACT_NAME-v$version-linux-x86_64.AppImage', self.script)

    def test_the_image_is_a_concatenation_not_a_second_tool(self):
        self.assertIn("mksquashfs", self.script)
        self.assertIn('cat "$runtime" build/appdir.squashfs > "$appimage"', self.script)


    def test_the_shipped_readme_points_at_the_release_checksum_list(self):
        # The unified pipeline ships one SHA256SUMS covering every platform
        # (and BUILD-SBOM.json). Naming a per-platform file that is never
        # attached sends the operator at a file that does not exist.
        start = self.script.index('cat > "$tarball_root/README-LINUX.txt"')
        readme = self.script[start:self.script.index("\nEOF", start)]
        self.assertIn("sha256sum -c SHA256SUMS", readme)
        self.assertIn("BUILD-SBOM.json", readme)
        self.assertNotIn("SHA256SUMS-linux-x86_64.txt", readme)
        self.assertNotIn("BUILD-SBOM-linux-x86_64.json", readme)
        self.assertNotIn("SHA256SUMS --ignore-missing", readme)


class LinuxWorkflowTests(unittest.TestCase):
    """The Linux guarantees inside the one pipeline every platform joins.

    The standalone build-linux.yml is retired: .github/workflows/build-candidate.yml
    builds macOS, Windows and Linux from the same commit in the same gated run and
    is the only publish path. These checks keep the Linux half of that promise.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.document = yaml.safe_load(cls.text)
        cls.jobs = cls.document["jobs"]

    def test_the_linux_job_builds_the_appimage_and_the_tarball(self):
        linux = self.jobs["linux"]
        self.assertEqual(linux["runs-on"], "ubuntu-24.04")
        build = next(step for step in linux["steps"]
                     if step.get("name") == "Build the AppImage and the tarball")
        self.assertIn("build-linux.sh", build["run"])

    def test_the_promise_of_no_libfuse_so_2_is_proven_where_the_library_is_absent(self):
        # A machine that has the library cannot show that it is not needed, so
        # the step refuses to run there, shows the launcher's runtime asks no
        # dynamic loader for anything, and then starts the AppImage twice --
        # once on the runner and once in a container that carries no libfuse2.
        step = self.text[self.text.index("Prove the AppImage starts where libfuse.so.2 is absent"):]
        self.assertIn("ldconfig -p", step)
        self.assertIn("libfuse\\.so\\.2", step)
        self.assertIn("the proof is void", step)
        self.assertIn("static-pie", step)
        self.assertIn("p_type == 2", step)
        self.assertIn("p_type == 3", step)
        self.assertIn("--device /dev/fuse", step)
        self.assertIn("ubuntu:24.04", step)
        # CT-99: a tag is a moving name, so the proof image is pinned to the
        # digest it resolved to. Without the digest the same workflow can prove
        # a different Ubuntu than the one this promise was verified against.
        self.assertIn(
            "ubuntu:24.04@sha256:"
            "534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55",
            step,
        )
        self.assertIn("--dsh-check-bundle", step)

    def test_the_files_say_which_platform_they_are(self):
        for name in ("linux-x86_64.AppImage", "linux-x86_64.tar.gz",
                     "BUILD-SBOM-linux-x86_64.json"):
            self.assertIn(name, self.text)

    def test_the_candidate_artifact_is_uploaded(self):
        upload = self.jobs["linux"]["steps"][-1]
        self.assertEqual(upload["with"]["name"], "linux-desktop")
        self.assertEqual(upload["with"]["if-no-files-found"], "error")

    def test_the_suite_refuses_a_silent_skip(self):
        self.assertIn('grep -qE "skipped=[1-9]"', self.text)

    def test_no_per_platform_publish_machinery_survives(self):
        """One release page is created once, by the unified release job only."""
        self.assertNotIn("gh release upload", self.text)
        self.assertNotIn("release_tag", self.text)
        self.assertEqual(self.text.count("gh release create"), 1)
        for verb in ("--clobber", "--draft", "--prerelease", "gh release delete",
                     "gh release edit", "--latest"):
            self.assertNotIn(verb, self.text)


if __name__ == "__main__":
    unittest.main()

"""Every ported platform branch must run on the machine that edits it.

A branch keyed on ``sys.platform == "win32"`` only executes on Windows, so
without these tests the port would be reviewed on macOS and first executed by the
person who downloaded the installer. Each test below drives one conditional line
directly by patching the platform it reads, so a change that breaks the Windows
path fails here too.

``scripts/build-windows.ps1`` cannot be executed on this host at all, so its
gates are pinned by their text instead. Every one of them is a refusal, and a
refusal that disappears quietly is exactly the failure this file exists to catch.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import desktop
import probe
from gui import assert_private_file
from network_settings import settings_path

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def windows_filesystem(profile: str | None = None):
    """Pretend this host is Windows for the code under test.

    ``pathlib`` selects ``WindowsPath`` purely from ``os.name``, and
    ``WindowsPath`` refuses to be instantiated off Windows, so the flavour is
    pointed at ``PosixPath`` for the duration -- but only off Windows. On Windows
    the real ``WindowsPath`` is already the flavour ``os.name == "nt"`` selects,
    and patching it the other way makes ``Path(...)`` raise
    ``NotImplementedError: cannot instantiate 'PosixPath' on your system``, which
    is how these tests failed the first time they ran on the Windows runner.
    """
    environment = {"USERPROFILE": profile} if profile else {}
    real_name = os.name
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(os, "name", "nt"))
        if real_name != "nt":
            stack.enter_context(patch.object(pathlib, "WindowsPath", pathlib.PosixPath))
        stack.enter_context(patch.dict(os.environ, environment))
        yield


class PrivateFileTests(unittest.TestCase):
    """gui.assert_private_file() asks a different question on each platform."""

    def test_windows_accepts_a_file_inside_the_operator_own_profile(self):
        with tempfile.TemporaryDirectory() as profile:
            saved = Path(profile) / "unsigned.psbt"
            saved.write_bytes(b"psbt")
            with windows_filesystem(profile):
                assert_private_file(saved)

    def test_windows_refuses_a_file_in_a_shared_location(self):
        with tempfile.TemporaryDirectory() as profile, \
                tempfile.TemporaryDirectory() as shared:
            saved = Path(shared) / "unsigned.psbt"
            saved.write_bytes(b"psbt")
            with windows_filesystem(profile):
                with self.assertRaisesRegex(
                    RuntimeError, "outside this user's own profile"
                ):
                    assert_private_file(saved)

    def test_the_mode_check_becomes_a_profile_check_on_windows(self):
        """Windows has no readable 0600, so the gate there is the profile instead.

        ``os.chmod`` on Windows only toggles the read-only attribute and
        ``st_mode`` always reports 0666, so a mode assertion cannot hold. What must
        hold is the substitute: a file that is not inside the operator's own
        profile is refused even when it was chmod'ed 0600, because that mode is not
        what protects it.
        """
        with tempfile.TemporaryDirectory() as folder:
            saved = Path(folder) / "unsigned.psbt"
            saved.write_bytes(b"psbt")
            os.chmod(saved, 0o600)
            if os.name == "nt":
                with tempfile.TemporaryDirectory() as profile:
                    with windows_filesystem(profile):
                        with self.assertRaisesRegex(
                            RuntimeError, "outside this user's own profile"
                        ):
                            assert_private_file(saved)
                return
            assert_private_file(saved)
            os.chmod(saved, 0o644)
            with self.assertRaisesRegex(RuntimeError, "not 0600"):
                assert_private_file(saved)


class WebviewRendererTests(unittest.TestCase):
    def test_windows_pins_edgechromium(self):
        with patch.object(sys, "platform", "win32"):
            self.assertEqual(desktop.webview_renderer(), "edgechromium")

    def test_macos_uses_cocoa(self):
        with patch.object(sys, "platform", "darwin"):
            self.assertEqual(desktop.webview_renderer(), "cocoa")

    def test_the_window_opens_on_both_shipping_platforms(self):
        webview = types.ModuleType("webview")
        for platform in ("darwin", "win32"):
            with self.subTest(platform=platform), patch.object(
                sys, "platform", platform
            ), patch.object(sys, "argv", ["desktop.py"]), patch.object(
                desktop, "configure_packaged_tls"
            ), patch.dict(sys.modules, {"webview": webview}), patch.object(
                desktop, "run_desktop"
            ) as run:
                desktop.main()
            run.assert_called_once_with(webview)

    def test_the_window_refuses_every_other_system(self):
        with patch.object(sys, "platform", "linux"), patch.object(
            sys, "argv", ["desktop.py"]
        ), patch.object(desktop, "configure_packaged_tls"):
            with self.assertRaisesRegex(SystemExit, "built for macOS and Windows"):
                desktop.main()


class ProbeHelperPathTests(unittest.TestCase):
    """The packaged helper is named for the platform that runs it."""

    def test_a_frozen_windows_build_looks_for_hwi_exe(self):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "Bitcoin Easy Signer.exe"
            executable.write_bytes(b"")
            helper = Path(folder) / "hwi.exe"
            helper.write_bytes(b"")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "platform", "win32"
            ), patch.object(sys, "executable", str(executable)):
                self.assertEqual(probe._hwi_path("hwi"), str(helper))

    def test_a_frozen_macos_build_looks_for_hwi(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "hwi"
            helper.write_bytes(b"")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "platform", "darwin"
            ), patch.object(sys, "executable", str(Path(folder) / "BESA")):
                self.assertEqual(probe._hwi_path("hwi"), str(helper))

    def test_a_frozen_build_never_falls_through_to_path(self):
        # A PATH search from a packaged build could run a substituted binary.
        with tempfile.TemporaryDirectory() as folder, patch.object(
            sys, "frozen", True, create=True
        ), patch.object(sys, "platform", "win32"), patch.object(
            sys, "executable", str(Path(folder) / "Bitcoin Easy Signer.exe")
        ), patch.object(probe.shutil, "which") as which:
            with self.assertRaisesRegex(probe.ProbeError, "missing from this installation"):
                probe._hwi_path("hwi")
        which.assert_not_called()

    def test_a_source_checkout_resolves_through_path(self):
        with patch.object(probe.shutil, "which", return_value="/usr/local/bin/hwi"):
            self.assertEqual(probe._hwi_path("hwi"), "/usr/local/bin/hwi")
        with patch.object(probe.shutil, "which", return_value=None):
            with self.assertRaisesRegex(probe.ProbeError, "HWI not found"):
                probe._hwi_path("hwi")


class SettingsLocationTests(unittest.TestCase):
    def test_windows_uses_appdata(self):
        with tempfile.TemporaryDirectory() as appdata, patch.object(
            sys, "platform", "win32"
        ), patch.dict(os.environ, {"APPDATA": appdata}):
            self.assertEqual(
                settings_path(),
                Path(appdata) / "Easy Bitcoin Multisig" / "settings.json",
            )

    def test_windows_without_appdata_stays_inside_the_profile(self):
        """The fallback is reached with no APPDATA, not with no home directory.

        ``Path.home()`` reads USERPROFILE on Windows and HOME elsewhere, so
        clearing the whole environment leaves this test with no home to assert
        against -- on the Windows runner that is a RuntimeError, not a fallback.
        """
        with tempfile.TemporaryDirectory() as profile, patch.object(
            sys, "platform", "win32"
        ), patch.dict(
            os.environ, {"USERPROFILE": profile, "HOME": profile}, clear=True
        ):
            self.assertEqual(
                settings_path(),
                Path.home() / "AppData" / "Roaming" / "Easy Bitcoin Multisig"
                / "settings.json",
            )

    def test_macos_uses_application_support(self):
        with patch.object(sys, "platform", "darwin"):
            self.assertEqual(
                settings_path(),
                Path.home() / "Library/Application Support/Easy Bitcoin Multisig"
                / "settings.json",
            )

    def test_other_systems_use_a_dotted_config_directory(self):
        with patch.object(sys, "platform", "linux"):
            self.assertEqual(
                settings_path(),
                Path.home() / ".config/easy-bitcoin-multisig" / "settings.json",
            )


class BuildScriptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (ROOT / "scripts" / "build-windows.ps1").read_text(encoding="utf-8")

    def test_a_non_windows_or_32_bit_host_is_refused(self):
        self.assertIn("if ($env:OS -ne 'Windows_NT')", self.script)
        self.assertIn("$architecture -ne 'AMD64'", self.script)

    def test_the_build_is_gated_on_a_reviewed_libusb_digest(self):
        self.assertIn("$reviewedLibusbSha256 = '", self.script)
        self.assertIn("LIBUSB_SHA256 is required; refusing an unverified native library.",
                      self.script)
        self.assertIn("does not match the reviewed libusb input", self.script)
        self.assertIn("Refusing to bundle a native library that does not match "
                      "LIBUSB_SHA256.", self.script)
        self.assertIn("Get-FileHash", self.script)

    def test_dependencies_are_hash_locked_before_a_signing_secret_could_exist(self):
        self.assertIn("--require-hashes -r $lockFile", self.script)
        self.assertIn("requirements-desktop-windows.lock", self.script)
        self.assertGreater(self.script.index("$env:BUILD_DEPS_PREPARED -eq '1'"),
                           -1)
        self.assertLess(self.script.index("$env:BUILD_DEPS_PREPARED -eq '1'"),
                        self.script.index("$env:PREPARE_ONLY -eq '1'"))
        self.assertLess(self.script.index("$env:PREPARE_ONLY -eq '1'"),
                        self.script.index("-m PyInstaller"))

    def test_the_helper_gets_two_copies_of_the_reviewed_library(self):
        # usb1 searches its own package directory at import time, before
        # hwi_entry.py can choose a library, so one copy must sit in the package
        # while the archive root holds the one hwi_entry.py loads and verifies.
        self.assertIn("'build\\libusb-alias\\libusb-1.0.dll;usb1'", self.script)
        self.assertIn('"$libusbDll;."', self.script)
        self.assertIn("build\\libusb-alias", self.script)
        self.assertIn("--dsh-check-libusb", self.script)

    def test_there_is_no_signing_step_to_go_wrong(self):
        for absent in ("codesign", "hdiutil", ".dmg", "signtool",
                       "Set-AuthenticodeSignature"):
            with self.subTest(absent=absent):
                self.assertNotIn(absent, self.script)

    def test_the_artifact_is_the_zip_the_workflow_publishes(self):
        self.assertIn("Bitcoin-Easy-Signer-v$Version-windows-x64.zip", self.script)
        self.assertIn("Compress-Archive", self.script)
        self.assertIn("'--icon', 'assets\\AppIcon.ico'", self.script)


if __name__ == "__main__":
    unittest.main()

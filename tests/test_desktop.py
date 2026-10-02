"""Desktop wrapper tests run without a window toolkit, a real signer or real wallet files."""

import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen
from unittest.mock import patch

import desktop
import safe_http
from support import real_ca_bundle
from desktop import (DesktopBridge, bundled_capabilities, check_bundle_resources,
                     check_device_bridge, check_psbt_save, configure_packaged_tls,
                     main, report, report_startup_failure, run_desktop, webview_renderer)
from probe import ProbeError
from gui import LocalApp, PreparedPayment, assert_private_file, ui_path
from dataclasses import replace


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path_patch = patch("network_settings.settings_path",
                           return_value=Path(self.temp.name) / "settings.json")
        path_patch.start()
        self.addCleanup(path_patch.stop)
        self.state = LocalApp(desktop=True)
        self.state.chain = "testnet4"
        # check_bundle_resources() requires the licence and the third-party
        # notices to ship beside the app, because the bundle redistributes libusb
        # under LGPL-2.1-or-later. Provide them for every frozen-bundle test.
        for notice in ("LICENSE", "THIRD-PARTY-NOTICES.md", "DISCLAIMER.md", "PRIVACY.md", "libusb-COPYING"):
            (Path(self.temp.name) / notice).write_text(f"synthetic {notice}\n")
        self.raw = b"psbt\xff" + b"synthetic test data"
        self.encoded = base64.b64encode(self.raw).decode()
        self.state.prepared = PreparedPayment(
            None, "testnet4", 0, "test", self.encoded, "", (), ())
        self.url = "http://127.0.0.1:54321/"

    def _bridge(self, current_url=None):
        module = type("Webview", (), {"SAVE_DIALOG": "save"})
        bridge = DesktopBridge(self.state, module, self.url)
        bridge.window = type("Window", (), {
            "get_current_url": lambda _self: current_url or self.url,
        })()
        return bridge

    def test_save_writes_the_prepared_psbt_to_downloads_without_overwriting(self):
        home = Path(self.temp.name) / "home"
        (home / "Downloads").mkdir(parents=True)
        with patch("desktop.Path.home", return_value=home):
            bridge = self._bridge()
            first = bridge.save_psbt(self.encoded, "testnet4")
            self.assertTrue(first["saved"])
            saved = Path(first["path"])
            self.assertEqual(saved.parent, home / "Downloads")
            self.assertEqual(saved.name, "testnet4-unsigned.psbt")
            self.assertEqual(saved.read_bytes(), self.raw)
            # Windows protects the file with a per-user access list rather than
            # POSIX mode bits, so the assertion is the platform-aware one.
            assert_private_file(saved)
            # A second save must never replace the earlier transaction.
            second = bridge.save_psbt(self.encoded, "testnet4")
            self.assertEqual(Path(second["path"]).name, "testnet4-unsigned-2.psbt")
            self.assertEqual(Path(second["path"]).read_bytes(), self.raw)

    def test_save_falls_back_to_the_home_directory_without_downloads(self):
        home = Path(self.temp.name) / "home2"
        home.mkdir()
        with patch("desktop.Path.home", return_value=home):
            result = self._bridge().save_psbt(self.encoded, "testnet4")
        self.assertEqual(Path(result["path"]).parent, home)

    def test_save_refuses_stale_content_or_a_foreign_window(self):
        home = Path(self.temp.name) / "home3"
        home.mkdir()
        with patch("desktop.Path.home", return_value=home):
            bridge = self._bridge()
            with self.assertRaisesRegex(ValueError, "changed"):
                bridge.save_psbt(base64.b64encode(b"psbt\xffother").decode(), "testnet4")
            with self.assertRaisesRegex(ValueError, "changed"):
                bridge.save_psbt(self.encoded, "main")
            original = self.state.prepared
            self.state.prepared = None
            with self.assertRaisesRegex(ValueError, "changed"):
                bridge.save_psbt(self.encoded, "testnet4")
            self.state.prepared = original
            with self.assertRaisesRegex(ValueError, "local app URL"):
                self._bridge(current_url="https://example.org/").save_psbt(
                    self.encoded, "testnet4")
            # A payload that matches the prepared one but is not a PSBT.
            not_psbt = base64.b64encode(b"not a psbt at all").decode()
            self.state.prepared = replace(original, psbt_base64=not_psbt)
            with self.assertRaisesRegex(ValueError, "not valid"):
                bridge.save_psbt(not_psbt, "testnet4")

    def test_save_removes_a_partial_file_when_the_write_fails(self):
        home = Path(self.temp.name) / "home4"
        (home / "Downloads").mkdir(parents=True)
        with patch("desktop.Path.home", return_value=home), \
                patch("desktop.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(ValueError, "Could not save"):
                self._bridge().save_psbt(self.encoded, "testnet4")
        self.assertEqual(list((home / "Downloads").iterdir()), [])

    def test_headless_save_check_actually_writes_a_psbt(self):
        """The packaged app's own save path, using a temp folder."""
        check_psbt_save()  # raises RuntimeError on any failure

    def test_window_starts_one_local_server_and_stops_on_close(self):
        class FakeWebview:
            def create_window(self, _title, url, **kwargs):
                self.url = url
                self.bridge = kwargs["js_api"]
                self.window = type("Window", (), {
                    "get_current_url": lambda _self: url,
                    "create_file_dialog": lambda *_args, **_kwargs: None,
                })()
                return self.window
            def start(self, *, gui):
                self.asserted_gui = gui
                with urlopen(self.url, timeout=3) as response:
                    page = response.read().decode()
                self.page = page
        fake = FakeWebview()
        run_desktop(fake)
        self.assertEqual(fake.asserted_gui, webview_renderer())
        self.assertTrue(fake.url.startswith("http://127.0.0.1:"))
        self.assertIs(fake.bridge.window, fake.window)
        self.assertIn('id="quit" class="secondary" hidden', fake.page)
        self.assertIn('id="wallet-file" type="file"', fake.page)
        self.assertNotIn('id="wallet-file" type="file" accept=', fake.page)
        self.assertIn('/\\.(bsms|txt)$/i.test(file.name)', fake.page)
        self.assertIn('const file = $("wallet-file").files[0];', fake.page)
        self.assertIn('text: await file.text()', fake.page)
        self.assertNotIn("The Mac file picker is not ready", fake.page)
        self.assertNotIn("__DESKTOP_HIDE_QUIT__", fake.page)
        self.assertIn("const desktopMode = true", fake.page)
        self.assertNotIn("__DESKTOP_MODE__", fake.page)

    def test_the_bundle_ships_a_real_icon(self):
        """PyInstaller's stock icon shipped for weeks; it must not come back.

        The build passes flags straight to PyInstaller and keeps no spec in the
        repository (*.spec is ignored), so the icon has to be asserted here, in the
        build script, or it silently reverts to the default.
        """
        root = Path(__file__).resolve().parents[1]
        build = (root / "scripts" / "build-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("'--icon', 'assets\\AppIcon.ico'", build)
        ico = root / "assets" / "AppIcon.ico"
        self.assertTrue(ico.is_file(), "the icon the build references is missing")
        data = ico.read_bytes()
        self.assertEqual(data[:4], b"\x00\x00\x01\x00", "not a valid .ico container")
        self.assertGreater(len(data), 20_000, "the icon looks suspiciously empty")
        # The master artwork travels with the compiled icon so it can be rebuilt,
        # and the derivation script is checked in beside it.
        self.assertTrue((root / "assets" / "icon.svg").is_file())
        self.assertTrue((root / "assets" / "AppIcon.icns").is_file())
        self.assertTrue((root / "scripts" / "make-windows-icon.py").is_file())
        # And the source archive must carry the icon and its master, or a rebuild
        # from the archive loses them.
        source = (root / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.assertIn("assets/AppIcon.ico", source)
        self.assertIn("assets/icon.svg", source)

    def test_bundled_ui_is_resolved_inside_app(self):
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__APP_VERSION__ location.hash __DESKTOP_MODE__</html>")
        # check_bundle_resources() now also insists that the CA store the app
        # will use is the one it ships, so the frozen-app setup must configure it
        # the way main() does. certifi points at a real bundle so the CA-count
        # assertion is meaningful. patch.dict(os.environ, {}) restores the
        # SSL_CERT_FILE that configure_packaged_tls() sets, so it cannot leak
        # into other tests.
        found = real_ca_bundle()
        if found is None:
            self.skipTest("no system CA bundle available to stand in for certifi")
        bundle = Path(found)
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/reset.pem")
        with patch("gui.sys.frozen", True, create=True), patch(
            "gui.sys._MEIPASS", self.temp.name, create=True
        ), patch.dict(os.environ, {}), patch.dict(
            "sys.modules", {"certifi": SimpleNamespace(where=lambda: str(bundle))}
        ):
            self.assertEqual(ui_path().read_text(),
                             "<html>__APP_VERSION__ location.hash __DESKTOP_MODE__</html>")
            configure_packaged_tls()
            check_bundle_resources()

    def test_device_bridge_check_exercises_the_bundled_tool(self):
        """It must prove the tool ran, and fail loudly with HWI's reason when it
        could not -- this is the check that catches a broken bundled libusb."""
        capable = {"jade_http_relay": True, "jade_present": True}
        with patch("desktop.bundled_capabilities", return_value=capable), \
             patch("desktop.invoke_hwi", return_value=[]) as call:
            check_device_bridge()
        self.assertEqual(call.call_args[0][1], "test")
        with patch("desktop.bundled_capabilities", return_value=capable), \
             patch("desktop.invoke_hwi", return_value=[{"model": "Trezor"}]):
            check_device_bridge()
        # A Jade could not be unlocked at all without the relay, and that failure
        # looks like a device fault rather than a packaging omission.
        with patch("desktop.bundled_capabilities",
                   return_value={"jade_http_relay": False}):
            with self.assertRaises(RuntimeError) as err:
                check_device_bridge()
            self.assertIn("Blockstream Jade", str(err.exception))
        with patch("desktop.bundled_capabilities", return_value=capable), \
             patch("desktop.invoke_hwi", side_effect=ProbeError("Device not found")):
            with self.assertRaises(RuntimeError) as err:
                check_device_bridge()
            self.assertIn("Device not found", str(err.exception))
        with patch("desktop.bundled_capabilities", return_value=capable), \
             patch("desktop.invoke_hwi", return_value={"not": "a list"}):
            with self.assertRaises(RuntimeError):
                check_device_bridge()

    def test_the_jade_relay_dependency_is_installed_and_bundled(self):
        """A Jade cannot be unlocked without it, and the failure looks like a
        device fault rather than a missing dependency."""
        root = Path(__file__).resolve().parents[1]
        self.assertIn("requests", (root / "requirements-desktop.txt").read_text(encoding="utf-8"))
        build = (root / "scripts" / "build-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("--collect-all requests", build)

    def test_the_build_proves_the_bundled_usb_library_loads(self):
        """The check that catches a broken bundled libusb must survive the port.

        On macOS the USB library needed a scoped codesign exception, so the build
        finished by running HWI's own library check. Windows has no such exception,
        but it has its own trap: usb1 loads a library at import time, so the DLL has
        to be present inside the usb1 package as well as beside the helper.
        """
        root = Path(__file__).resolve().parents[1]
        build = (root / "scripts" / "build-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("--dsh-check-libusb", build)
        self.assertIn("vendor\\libusb-1.0.dll", build)
        self.assertIn("build\\libusb-alias\\libusb-1.0.dll", build)
        # The alias copy is what usb1's import-time search finds, so it must land
        # inside the package rather than only in the archive root.
        self.assertIn("build\\libusb-alias\\libusb-1.0.dll;usb1", build)
        source = (root / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/*.ps1", source)

    def test_bundle_check_requires_the_licence_and_notices(self):
        """The bundle redistributes libusb under LGPL-2.1-or-later.

        Shipping the licence and the third-party notices is a redistribution
        obligation, so a build that dropped either must fail its own self-check
        rather than ship silently.
        """
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__APP_VERSION__ location.hash __DESKTOP_MODE__</html>")
        for notice in ("LICENSE", "THIRD-PARTY-NOTICES.md", "libusb-COPYING"):
            with self.subTest(notice=notice):
                target = Path(self.temp.name) / notice
                original = target.read_text(encoding="utf-8")
                target.unlink()
                try:
                    with patch("gui.sys.frozen", True, create=True), patch(
                        "gui.sys._MEIPASS", self.temp.name, create=True
                    ):
                        with self.assertRaisesRegex(RuntimeError, notice):
                            check_bundle_resources()
                finally:
                    target.write_text(original, encoding="utf-8")

    def test_bundle_check_rejects_an_unconfigured_trust_store(self):
        """The check must fail when the app would fall back to ambient trust."""
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__APP_VERSION__ location.hash __DESKTOP_MODE__</html>")
        # A real file stands in for the bundled store, so the check that fires is
        # the identity check rather than "trust store is missing".
        bundled_ca = Path(self.temp.name) / "cacert.pem"
        bundled_ca.write_text("stand-in bundle\n")
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/reset.pem")
        safe_http.set_trust_bundle("/nonexistent/reset.pem")
        with patch("gui.sys.frozen", True, create=True), patch(
            "gui.sys._MEIPASS", self.temp.name, create=True
        ), patch.dict(os.environ, {"SSL_CERT_FILE": "/nonexistent/env-ca.pem"}), patch.dict(
            "sys.modules",
            {"certifi": SimpleNamespace(where=lambda: str(bundled_ca))},
        ):
            with self.assertRaisesRegex(RuntimeError, "not the one configured"):
                check_bundle_resources()

    def test_frozen_app_uses_bundled_ca_file_and_checks_testnet_network(self):
        ca = Path(self.temp.name) / "ca.pem"
        ca.write_text("test placeholder")
        # configure_packaged_tls() now also points the HTTP client at the bundle,
        # which is process-global state; reset it so this test cannot leak into
        # unrelated tests that make HTTPS requests.
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/reset.pem")
        with patch("desktop.sys.frozen", True, create=True), patch.dict(
            "sys.modules", {"certifi": SimpleNamespace(where=lambda: str(ca))}
        ), patch.dict(os.environ, {"SSL_CERT_FILE": "old-path"}):
            configure_packaged_tls()
            self.assertEqual(os.environ["SSL_CERT_FILE"], str(ca))
            self.assertEqual(safe_http.trust_bundle(), str(ca))
        with patch("desktop.sys.argv", ["desktop.py", "--check-network"]), patch(
            "desktop.configure_packaged_tls"
        ), patch("desktop.check_testnet4_network") as check:
            main()
        check.assert_called_once_with()


class SelfCheckReportTests(unittest.TestCase):
    """A frozen --windowed build has no stdout, so the checks must report to a file."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log = Path(self.temp.name) / "check.log"

    def test_every_check_result_reaches_the_report_file(self):
        with patch.dict(os.environ, {"DSH_DESKTOP_CHECK_LOG": str(self.log)}):
            report("first line")
            report("second line")
        self.assertEqual(self.log.read_text(encoding="utf-8").splitlines(),
                         ["first line", "second line"])

    def test_a_check_without_the_variable_still_prints_and_writes_nothing(self):
        with patch.dict(os.environ, {}, clear=True):
            report("no file asked for")
        self.assertFalse(self.log.exists())

    def test_the_bundle_check_reports_what_it_verified(self):
        """--check-bundle must leave evidence; it is the CA-store assertion."""
        page = Path(self.temp.name) / "ui.html"
        page.write_text("<html>__APP_VERSION__ location.hash __DESKTOP_MODE__</html>")
        for notice in ("LICENSE", "DISCLAIMER.md", "PRIVACY.md",
                       "THIRD-PARTY-NOTICES.md", "libusb-COPYING"):
            (Path(self.temp.name) / notice).write_text(f"synthetic {notice}\n")
        with patch.dict(os.environ, {"DSH_DESKTOP_CHECK_LOG": str(self.log)}), patch(
            "desktop.ui_path", return_value=page
        ):
            check_bundle_resources()
        self.assertIn("check out", self.log.read_text(encoding="utf-8"))


class StartupFailureTests(unittest.TestCase):
    """A window that will not open must say why; a --windowed build has no console."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Path(self.temp.name) / "settings.json"
        path_patch = patch("desktop.settings_path", return_value=self.settings)
        path_patch.start()
        self.addCleanup(path_patch.stop)
        self.log = Path(self.temp.name) / "desktop-startup-error.log"

    def test_a_failed_start_writes_the_traceback_beside_the_settings(self):
        report_startup_failure(ValueError("the WebView2 runtime is missing"))
        text = self.log.read_text(encoding="utf-8")
        self.assertIn("ValueError", text)
        self.assertIn("the WebView2 runtime is missing", text)

    def test_windows_also_shows_a_dialog_naming_the_report(self):
        with patch.object(desktop, "windows_error_dialog") as dialog, patch.object(
            desktop.sys, "platform", "win32"
        ):
            report_startup_failure(ValueError("no edge"))
        dialog.assert_called_once()
        title, text = dialog.call_args.args[:2]
        self.assertEqual(title, "Bitcoin Easy Signer")
        self.assertIn("could not open its window", text)
        self.assertIn("no edge", text)
        self.assertIn(str(self.log), text)

    def test_main_reports_a_window_that_fails_instead_of_dying_silently(self):
        with patch.dict(sys.modules, {"webview": SimpleNamespace()}), patch.object(
            desktop.sys, "platform", "win32"
        ), patch.object(
            desktop, "run_desktop", side_effect=RuntimeError("no window toolkit")
        ), patch.object(desktop, "report_startup_failure") as reported:
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 1)
        reported.assert_called_once()
        self.assertIsInstance(reported.call_args.args[0], RuntimeError)


if __name__ == "__main__":
    unittest.main()

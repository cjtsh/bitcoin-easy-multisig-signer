"""Desktop wrapper tests run without macOS, WebKit or real wallet files."""

import base64
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen
from unittest.mock import patch

import safe_http
from desktop import DesktopBridge, check_bundle_resources, configure_packaged_tls, main, run_desktop
from gui import LocalApp, ui_path


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
        self.raw = b"psbt\xff" + b"synthetic test data"
        self.encoded = base64.b64encode(self.raw).decode()
        self.state.prepared_psbt = self.encoded
        self.url = "http://127.0.0.1:54321/"

    def test_native_save_is_only_for_current_local_prepared_psbt(self):
        target = Path(self.temp.name) / "unsigned.psbt"

        class Window:
            def get_current_url(self):
                return self.url
            def create_file_dialog(self, *_args, **_kwargs):
                return (str(target),)

        window = Window()
        window.url = self.url
        module = type("Webview", (), {"SAVE_DIALOG": "save"})
        bridge = DesktopBridge(self.state, module, self.url)
        bridge.window = window
        self.assertTrue(bridge.save_psbt(self.encoded, "testnet4")["saved"])
        self.assertEqual(target.read_bytes(), self.raw)
        with self.assertRaisesRegex(ValueError, "already exists"):
            bridge.save_psbt(self.encoded, "testnet4")
        with self.assertRaisesRegex(ValueError, "Wallet or unsigned transaction changed"):
            bridge.save_psbt(base64.b64encode(b"psbt\xffother").decode(), "testnet4")
        with self.assertRaisesRegex(ValueError, "Wallet or unsigned transaction changed"):
            bridge.save_psbt(self.encoded, "main")
        window.url = "https://example.org/"
        with self.assertRaisesRegex(ValueError, "local app URL"):
            bridge.save_psbt(self.encoded, "testnet4")

    def test_native_save_cancel_and_old_psbt_refused(self):
        module = type("Webview", (), {"SAVE_DIALOG": "save"})
        bridge = DesktopBridge(self.state, module, self.url)
        bridge.window = type("Window", (), {
            "get_current_url": lambda _self: self.url,
            "create_file_dialog": lambda *_args, **_kwargs: None,
        })()
        self.assertFalse(bridge.save_psbt(self.encoded, "testnet4")["saved"])
        self.state.prepared_psbt = None
        with self.assertRaisesRegex(ValueError, "changed"):
            bridge.save_psbt(self.encoded, "testnet4")

    def test_native_save_does_not_leave_partial_file_on_write_failure(self):
        target = Path(self.temp.name) / "disk-full.psbt"
        module = type("Webview", (), {"SAVE_DIALOG": "save"})
        bridge = DesktopBridge(self.state, module, self.url)
        bridge.window = type("Window", (), {
            "get_current_url": lambda _self: self.url,
            "create_file_dialog": lambda *_args, **_kwargs: (str(target),),
        })()
        with patch("desktop.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(ValueError, "Could not save"):
                bridge.save_psbt(self.encoded, "testnet4")
        self.assertFalse(target.exists())

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
        self.assertEqual(fake.asserted_gui, "cocoa")
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

    def test_bundled_ui_is_resolved_inside_app(self):
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__APP_VERSION__ location.hash</html>")
        # check_bundle_resources() now also insists that the CA store the app
        # will use is the one it ships, so the frozen-app setup must configure it
        # the way main() does. certifi points at a real bundle so the CA-count
        # assertion is meaningful. patch.dict(os.environ, {}) restores the
        # SSL_CERT_FILE that configure_packaged_tls() sets, so it cannot leak
        # into other tests.
        bundle = Path("/etc/ssl/cert.pem")
        if not bundle.is_file():
            self.skipTest("no system CA bundle available to stand in for certifi")
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/reset.pem")
        with patch("gui.sys.frozen", True, create=True), patch(
            "gui.sys._MEIPASS", self.temp.name, create=True
        ), patch.dict(os.environ, {}), patch.dict(
            "sys.modules", {"certifi": SimpleNamespace(where=lambda: str(bundle))}
        ):
            self.assertEqual(ui_path().read_text(),
                             "<html>__APP_VERSION__ location.hash</html>")
            configure_packaged_tls()
            check_bundle_resources()

    def test_bundle_check_rejects_an_unconfigured_trust_store(self):
        """The check must fail when the app would fall back to ambient trust."""
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__APP_VERSION__ location.hash</html>")
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/reset.pem")
        safe_http.set_trust_bundle("/nonexistent/reset.pem")
        with patch("gui.sys.frozen", True, create=True), patch(
            "gui.sys._MEIPASS", self.temp.name, create=True
        ), patch.dict(os.environ, {"SSL_CERT_FILE": "/nonexistent/env-ca.pem"}), patch.dict(
            "sys.modules",
            {"certifi": SimpleNamespace(where=lambda: "/etc/ssl/cert.pem")},
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


if __name__ == "__main__":
    unittest.main()
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
from support import real_ca_bundle
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
            self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
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
            original = self.state.prepared_psbt
            self.state.prepared_psbt = None
            with self.assertRaisesRegex(ValueError, "changed"):
                bridge.save_psbt(self.encoded, "testnet4")
            self.state.prepared_psbt = original
            with self.assertRaisesRegex(ValueError, "local app URL"):
                self._bridge(current_url="https://example.org/").save_psbt(
                    self.encoded, "testnet4")
            # A payload that matches the prepared one but is not a PSBT.
            not_psbt = base64.b64encode(b"not a psbt at all").decode()
            self.state.prepared_psbt = not_psbt
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
        self.assertIn("const desktopMode = true", fake.page)
        self.assertNotIn("__DESKTOP_MODE__", fake.page)

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


if __name__ == "__main__":
    unittest.main()
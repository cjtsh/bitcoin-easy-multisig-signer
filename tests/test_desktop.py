"""Desktop wrapper tests run without macOS, WebKit or real wallet files."""

import base64
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch

from desktop import DesktopBridge, check_bundle_resources, run_desktop
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

    def test_native_picker_prefers_bsms_and_reads_only_selected_text(self):
        path = Path(self.temp.name) / "sample.bsms"
        path.write_text("BSMS 1.0\nsynthetic data", encoding="utf-8")

        class Window:
            def get_current_url(self):
                return self.url
            def create_file_dialog(self, dialog, **kwargs):
                self.dialog = dialog
                self.file_types = kwargs["file_types"]
                return (str(self.file_path),)

        window = Window()
        window.url = self.url
        window.file_path = path
        module = type("Webview", (), {"OPEN_DIALOG": "open"})
        bridge = DesktopBridge(self.state, module, self.url)
        bridge.window = window
        self.assertEqual(bridge.choose_bsms(), {
            "selected": True, "name": "sample.bsms", "text": "BSMS 1.0\nsynthetic data",
        })
        self.assertEqual(window.dialog, "open")
        self.assertEqual(window.file_types, (
            "BSMS wallet (*.bsms)", "Plain-text BSMS (*.txt)",
        ))

        window.file_path = path.rename(path.with_suffix(".md"))
        with self.assertRaisesRegex(ValueError, "Choose a .bsms"):
            bridge.choose_bsms()
        window.url = "https://example.org/"
        with self.assertRaisesRegex(ValueError, "local app URL"):
            bridge.choose_bsms()

    def test_native_picker_cancel_and_oversized_file(self):
        path = Path(self.temp.name) / "oversized.bsms"
        path.write_bytes(b"x" * 65537)
        module = type("Webview", (), {"OPEN_DIALOG": "open"})
        bridge = DesktopBridge(self.state, module, self.url)
        window = type("Window", (), {
            "get_current_url": lambda _self: self.url,
            "create_file_dialog": lambda *_args, **_kwargs: None,
        })()
        bridge.window = window
        self.assertEqual(bridge.choose_bsms(), {"selected": False})
        window.create_file_dialog = lambda *_args, **_kwargs: (str(path),)
        with self.assertRaisesRegex(ValueError, "unexpectedly large"):
            bridge.choose_bsms()

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
        with self.assertRaisesRegex(ValueError, "Wallet or PSBT changed"):
            bridge.save_psbt(base64.b64encode(b"psbt\xffother").decode(), "testnet4")
        with self.assertRaisesRegex(ValueError, "Wallet or PSBT changed"):
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
        self.assertIn('id="browser-wallet-input" hidden', fake.page)
        self.assertIn('id="native-wallet-input" >', fake.page)
        self.assertIn("const desktopMode = true;", fake.page)
        self.assertNotIn("__DESKTOP_HIDE_QUIT__", fake.page)

    def test_bundled_ui_is_resolved_inside_app(self):
        ui = Path(self.temp.name) / "ui.html"
        ui.write_text("<html>__LOCAL_TOKEN__ __APP_VERSION__</html>")
        with patch("gui.sys.frozen", True, create=True), patch(
            "gui.sys._MEIPASS", self.temp.name, create=True
        ):
            self.assertEqual(ui_path().read_text(), "<html>__LOCAL_TOKEN__ __APP_VERSION__</html>")
            check_bundle_resources()


if __name__ == "__main__":
    unittest.main()
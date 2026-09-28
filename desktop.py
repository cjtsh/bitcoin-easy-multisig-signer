"""Thin macOS window around the existing localhost GUI; no wallet engine fork."""

from __future__ import annotations

import base64
import binascii
import os
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from gui import LocalApp, launch_url, ui_path


class DesktopBridge:
    """Native PSBT save dialog; keep selected paths out of the page."""

    def __init__(self, state: LocalApp, webview_module, url: str):
        """``url`` is the bare local app URL, without the token fragment."""
        self.state = state
        self.webview = webview_module
        self.url = url
        self.window = None

    def _at_app_url(self) -> bool:
        if self.window is None:
            return False
        current = (self.window.get_current_url() or "").split("#", 1)[0]
        return current == self.url

    def save_psbt(self, encoded: str, chain: str) -> dict:
        def ensure_current() -> None:
            if not self._at_app_url():
                raise ValueError("The wallet window is no longer at its local app URL.")
            if not isinstance(encoded, str) or len(encoded) > 2_800_000:
                raise ValueError("Unsigned transaction file is missing or too large.")
            with self.state.lock:
                if chain != self.state.chain or encoded != self.state.prepared_psbt:
                    raise ValueError("Wallet or unsigned transaction changed; prepare and review it again.")

        ensure_current()
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Unsigned transaction file is invalid.") from exc
        if not raw.startswith(b"psbt\xff") or len(raw) > 2_000_000:
            raise ValueError("Unsigned transaction file is invalid or too large.")
        chosen = self.window.create_file_dialog(
            self.webview.SAVE_DIALOG,
            save_filename=f"{chain}-unsigned.psbt",
        )
        if not chosen:
            return {"saved": False}
        ensure_current()
        filename = chosen[0] if isinstance(chosen, (tuple, list)) else chosen
        # Refuse to overwrite an existing file; the selected path comes from
        # the native save dialog, not from arbitrary web-page JavaScript.
        created = False
        try:
            fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            created = True
            with os.fdopen(fd, "wb") as output:
                if output.write(raw) != len(raw):
                    raise OSError("Incomplete PSBT write.")
                output.flush()
                os.fsync(output.fileno())
        except FileExistsError as exc:
            raise ValueError("That file already exists. Choose a new filename.") from exc
        except OSError as exc:
            if created:
                try:
                    os.unlink(filename)
                except OSError:
                    pass
            raise ValueError("Could not save the unsigned transaction file to that location.") from exc
        return {"saved": True}


def check_bundle_resources() -> None:
    """Headless smoke check against the *actual* frozen executable's data path."""
    page = ui_path().read_text(encoding="utf-8")
    if "__APP_VERSION__" not in page:
        raise RuntimeError("Bundled ui.html is missing or does not match this app.")
    if "location.hash" not in page:
        raise RuntimeError("Bundled ui.html does not read its local access token.")
    if getattr(sys, "frozen", False):
        import certifi
        if not Path(certifi.where()).is_file():
            raise RuntimeError("Bundled HTTPS trust store is missing.")


def configure_packaged_tls() -> None:
    """Give the frozen Python runtime a bundled public CA store for HTTPS."""
    if getattr(sys, "frozen", False):
        import certifi
        bundle = Path(certifi.where())
        if not bundle.is_file():
            raise RuntimeError("Bundled HTTPS trust store is missing.")
        os.environ["SSL_CERT_FILE"] = str(bundle)


def check_testnet4_network() -> None:
    """Headless probe of the same HTTPS client used by wallet balance scans."""
    from network_config import NETWORKS
    from wallet_service import explorer_get

    genesis = explorer_get("/block-height/0", text=True, chain="testnet4").strip().lower()
    if genesis != NETWORKS["testnet4"].genesis_hash:
        raise RuntimeError("Testnet4 explorer returned the wrong network's genesis block.")
    print("Bundled Testnet4 explorer HTTPS check passed.")


def run_desktop(webview_module) -> None:
    """Only the window is new; LocalApp owns the same API and state as browser mode."""
    state = LocalApp(desktop=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), state.handler())
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    try:
        thread.start()
        bridge = DesktopBridge(state, webview_module, url)
        bridge.window = webview_module.create_window(
            "Bitcoin Easy Signer", launch_url(port, state.token), js_api=bridge,
            width=1100, height=820, min_size=(780, 600),
        )
        webview_module.start(gui="cocoa")
    finally:
        server.shutdown()
        server.server_close()
        if thread.is_alive():
            thread.join(timeout=5)


def main() -> None:
    configure_packaged_tls()
    if "--check-bundle" in sys.argv[1:]:
        check_bundle_resources()
        return
    if "--check-network" in sys.argv[1:]:
        check_testnet4_network()
        return
    if sys.platform != "darwin":
        raise SystemExit("The desktop window bundle is for macOS; Linux can use gui.py.")
    import webview
    run_desktop(webview)


if __name__ == "__main__":
    main()
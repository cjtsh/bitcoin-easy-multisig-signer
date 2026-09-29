"""Thin macOS window around the existing localhost GUI; no wallet engine fork."""

from __future__ import annotations

import base64
import binascii
import json
import os
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import safe_http
from gui import LocalApp, launch_url, save_prepared_psbt, ui_path
from probe import ProbeError, _hwi_path, invoke_hwi
from wallet_service import WalletError


class DesktopBridge:
    """Saves the prepared PSBT to the user's Downloads folder.

    Deliberately not a native save dialog. In the shipped build the dialog could
    return nothing while reporting no error, so the button appeared to do nothing
    at all — the worst possible failure for the person this app is for. Saving to
    a known folder and naming the full path in the interface is clearer for a
    non-technical user, and it also removes any file path arriving from the web
    page. Overwriting is still refused, the file is created 0600, and the payload
    must still be byte-identical to the PSBT the app prepared.
    """

    def __init__(self, state: LocalApp, webview_module, url: str):
        """``url`` is the bare local app URL, without the token fragment."""
        self.state = state
        self.webview = webview_module
        self.url = url
        self.window = None

    def _window_at_app_url(self) -> bool:
        """Best-effort pin to our own page.

        If the current URL cannot be read, do NOT block the save: the payload
        equality check below is the real protection, and refusing to save because
        of an unreadable URL is exactly the kind of silent failure this replaced.
        """
        if self.window is None:
            return False
        try:
            current = (self.window.get_current_url() or "").split("#", 1)[0].rstrip("/")
        except Exception:  # noqa: BLE001 - treat an unreadable URL as unknown
            return True
        return not current or current == self.url.rstrip("/")

    def save_psbt(self, encoded: str, chain: str) -> dict:
        """pywebview-bridge entry point; the page normally uses POST /api/save.

        Kept so the native bridge still works if it is available, but the shared
        implementation lives in gui.py so the two paths cannot drift.
        """
        if not self._window_at_app_url():
            raise ValueError("The wallet window is no longer at its local app URL.")
        if not isinstance(encoded, str) or len(encoded) > 2_800_000:
            raise ValueError("Unsigned transaction file is missing or too large.")
        with self.state.lock:
            if chain != self.state.chain or encoded != self.state.prepared_psbt:
                raise ValueError("Wallet or unsigned transaction changed; prepare and review it again.")
        try:
            return save_prepared_psbt(self.state, chain)
        except WalletError as exc:
            # pywebview surfaces the message; keep this bridge's documented
            # ValueError contract rather than leaking the API error type.
            raise ValueError(str(exc)) from exc


def check_bundle_resources() -> None:
    """Headless smoke check against the *actual* frozen executable's data path."""
    page = ui_path().read_text(encoding="utf-8")
    if "__APP_VERSION__" not in page:
        raise RuntimeError("Bundled ui.html is missing or does not match this app.")
    if "location.hash" not in page:
        raise RuntimeError("Bundled ui.html does not read its local access token.")
    if "__DESKTOP_MODE__" not in page:
        raise RuntimeError("Bundled ui.html cannot tell that it is the desktop app.")
    if getattr(sys, "frozen", False):
        import certifi
        bundle = Path(certifi.where())
        if not bundle.is_file():
            raise RuntimeError("Bundled HTTPS trust store is missing.")
        # Prove the BUNDLED store is the one configured for use. Checking only
        # that "some CA is loaded" is not enough: on a build machine with ambient
        # OpenSSL CA files that passes even when the bundle is ignored, which is
        # precisely how an earlier build shipped while being unable to verify any
        # certificate on the user's Mac.
        if Path(safe_http.trust_bundle() or "\0") != bundle:
            raise RuntimeError(
                "The bundled HTTPS trust store is not the one configured for use; "
                "HTTPS would depend on the host machine's CA configuration."
            )
        if safe_http.loaded_ca_count() == 0:
            raise RuntimeError(
                "No trusted CA certificates are loaded, so every HTTPS request "
                "would fail. The bundled trust store is not in effect."
            )


def configure_packaged_tls() -> None:
    """Give the frozen Python runtime a bundled public CA store for HTTPS."""
    if getattr(sys, "frozen", False):
        import certifi
        bundle = Path(certifi.where())
        if not bundle.is_file():
            raise RuntimeError("Bundled HTTPS trust store is missing.")
        os.environ["SSL_CERT_FILE"] = str(bundle)
        # The environment variable alone is not enough: the HTTPS handler may
        # already have built its context, so trust the bundle explicitly too.
        safe_http.set_trust_bundle(bundle)


def check_testnet4_network() -> None:
    """Headless probe of the same HTTPS client used by wallet balance scans."""
    from network_config import NETWORKS
    from wallet_service import explorer_get

    genesis = explorer_get("/block-height/0", text=True, chain="testnet4").strip().lower()
    if genesis != NETWORKS["testnet4"].genesis_hash:
        raise RuntimeError("Testnet4 explorer returned the wrong network's genesis block.")
    print("Bundled Testnet4 explorer HTTPS check passed.")


def check_psbt_save() -> None:
    """Headless proof that the packaged app can write an unsigned PSBT to disk.

    The save button once produced no file and no error on a real Mac, and no test
    covered the write from the frozen binary. This does, using a synthetic
    transaction and a temporary folder, so it never touches the user's files.
    """
    import tempfile

    from embit import psbt, script, transaction

    from gui import LocalApp, save_prepared_psbt

    tx = transaction.Transaction(
        vin=[transaction.TransactionInput(bytes(32), 0)],
        vout=[transaction.TransactionOutput(1000, script.Script(b"\x00\x14" + bytes(20)))],
    )
    state = LocalApp(desktop=True)
    state.chain = "testnet4"
    state.prepared_psbt = psbt.PSBT(tx).to_base64()
    with tempfile.TemporaryDirectory() as folder:
        first = save_prepared_psbt(state, "testnet4", Path(folder))
        # A second save must produce a new file, never replace the first.
        second = save_prepared_psbt(state, "testnet4", Path(folder))
        saved = Path(first["path"])
        if not saved.is_file() or saved.parent != Path(folder):
            raise RuntimeError("The prepared transaction was not written to disk.")
        if saved.read_bytes() != Path(second["path"]).read_bytes():
            raise RuntimeError("Two saves produced different files.")
        if not saved.read_bytes().startswith(b"psbt\xff"):
            raise RuntimeError("The saved file is not a PSBT.")
        if saved.stat().st_mode & 0o777 != 0o600:
            raise RuntimeError("The saved file permissions are not 0600.")
    print("Bundled unsigned-PSBT save check passed.")


def bundled_capabilities() -> dict:
    """Ask the bundled hardware-wallet tool what it can do.

    Separated from the check itself so tests can exercise the rest without a
    subprocess. A Jade cannot be unlocked unless the bundled library carries its
    HTTP relay for Blockstream's pin server, so a packaging omission here silently
    disables one whole device family.
    """
    try:
        probe = subprocess.run(
            [_hwi_path("hwi"), "--dsh-capabilities"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except Exception as exc:
        raise RuntimeError("The bundled hardware-wallet tool could not be run.") from exc
    try:
        capabilities = json.loads(probe.stdout)
    except Exception as exc:
        raise RuntimeError(
            "The bundled hardware-wallet tool did not report its capabilities."
        ) from exc
    if not isinstance(capabilities, dict):
        raise RuntimeError("The bundled hardware-wallet tool reported nonsense.")
    return capabilities


def check_device_bridge() -> None:
    """Prove the bundled hardware-wallet tool runs, with no device attached.

    This exercises the layer that cannot be tested any other way: finding the HWI
    executable inside the .app, loading the bundled libusb, running it as a
    subprocess and parsing its JSON. Every one of those can break in a frozen
    build while working perfectly from source, and the first person to find out
    would be someone holding a hardware wallet and wondering why nothing happens.
    No device is required or implied.
    """
    capabilities = bundled_capabilities()
    if not capabilities.get("jade_http_relay"):
        raise RuntimeError(
            "This build cannot unlock a Blockstream Jade: the bundled library has no "
            "HTTP relay for its PIN server. Install `requests` before building."
        )
    try:
        devices = invoke_hwi("hwi", "testnet4", "enumerate")
    except ProbeError as exc:
        raise RuntimeError(f"The bundled hardware-wallet tool could not run: {exc}") from exc
    if not isinstance(devices, list):
        raise RuntimeError("The bundled hardware-wallet tool returned an unexpected response.")
    for device in devices:
        if not isinstance(device, dict):
            raise RuntimeError("The bundled hardware-wallet tool returned a malformed device.")
    print(f"Bundled HWI responded: {len(devices)} device(s) attached right now.")
    print("The device bridge works; plugging in a signer is what remains untested.")


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
    if "--check-save" in sys.argv[1:]:
        check_psbt_save()
        return
    if "--check-devices" in sys.argv[1:]:
        check_device_bridge()
        return
    if sys.platform != "darwin":
        raise SystemExit("The desktop window bundle is for macOS; Linux can use gui.py.")
    import webview
    run_desktop(webview)


if __name__ == "__main__":
    main()
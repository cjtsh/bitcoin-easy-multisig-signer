"""Thin native window around the existing localhost GUI; no wallet engine fork.

The window is the only platform-specific part. It is WebKit on macOS and
WebView2 on Windows; the wallet engine, the interface and the HTTP API are the
same files on both.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import subprocess
import sys
import threading
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path

import safe_http
from gui import LocalApp, assert_private_file, launch_url, save_prepared_psbt, ui_path
from network_settings import settings_path
from probe import ProbeError, _hwi_path, invoke_hwi
from wallet_service import WalletError


def report(message: str) -> None:
    """Record what a headless self-check verified.

    A --windowed build has no console on Windows: ``sys.stdout`` is None, so
    ``print`` writes nothing and the build log cannot tell a check that passed
    from one that never ran. ``DSH_DESKTOP_CHECK_LOG`` names a file the build
    workflow reads for that evidence; where a console exists the same line still
    reaches the terminal.
    """
    print(message)
    destination = os.environ.get("DSH_DESKTOP_CHECK_LOG")
    if destination:
        with open(destination, "a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")


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
            if (chain != self.state.chain or self.state.prepared is None
                    or encoded != self.state.prepared.psbt_base64):
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
    # The licence and third-party notices are a redistribution obligation, not
    # decoration: the bundle ships libusb under LGPL-2.1-or-later.
    for notice in ("LICENSE", "DISCLAIMER.md", "PRIVACY.md", "THIRD-PARTY-NOTICES.md", "libusb-COPYING"):
        if not (ui_path().parent / notice).is_file():
            raise RuntimeError(f"Bundled {notice} is missing from the app bundle.")
    if getattr(sys, "frozen", False):
        import certifi
        bundle = Path(certifi.where())
        if not bundle.is_file():
            raise RuntimeError("Bundled HTTPS trust store is missing.")
        # Prove the BUNDLED store is the one configured for use. Checking only
        # that "some CA is loaded" is not enough: on a build machine with ambient
        # OpenSSL CA files that passes even when the bundle is ignored, which is
        # precisely how an earlier build shipped while being unable to verify any
        # certificate on the user's computer.
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
        report("Bundled ui.html, the licence notices and the packaged HTTPS trust store all check out.")
    else:
        report("Bundled ui.html and the licence notices check out; the trust store is checked in the frozen app.")


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
    """Headless HTTPS probe of both practice-network backends."""
    from network_config import NETWORKS
    from network_settings import verify_esplora
    from wallet_service import explorer_get

    genesis = explorer_get("/block-height/0", text=True, chain="testnet4").strip().lower()
    if genesis != NETWORKS["testnet4"].genesis_hash:
        raise RuntimeError("Testnet4 explorer returned the wrong network's genesis block.")
    report("Bundled Testnet4 explorer HTTPS check passed.")
    verify_esplora("mutinynet", NETWORKS["mutinynet"].explorer_url)
    report("Bundled Mutinynet genesis and fork-checkpoint HTTPS checks passed.")


def check_psbt_save() -> None:
    """Headless proof that the packaged app can write an unsigned PSBT to disk.

    The save button once produced no file and no error on a real Mac, and no test
    covered the write from the frozen binary. This does, using a synthetic
    transaction and a temporary folder, so it never touches the user's files.
    """
    import tempfile

    from embit import psbt, script, transaction

    from gui import LocalApp, PreparedPayment, save_prepared_psbt

    tx = transaction.Transaction(
        vin=[transaction.TransactionInput(bytes(32), 0)],
        vout=[transaction.TransactionOutput(1000, script.Script(b"\x00\x14" + bytes(20)))],
    )
    state = LocalApp(desktop=True)
    state.chain = "testnet4"
    state.prepared = PreparedPayment(None, "testnet4", 0, "self-check",
                                     psbt.PSBT(tx).to_base64(), "", (), ())
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
        assert_private_file(saved)
    report("Bundled unsigned-PSBT save check passed.")


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
        # "test", not "testnet4": see the note in gui.py. A Jade cannot be
        # enumerated under a chain its backend does not know.
        devices = invoke_hwi("hwi", "test", "enumerate")
    except ProbeError as exc:
        raise RuntimeError(f"The bundled hardware-wallet tool could not run: {exc}") from exc
    if not isinstance(devices, list):
        raise RuntimeError("The bundled hardware-wallet tool returned an unexpected response.")
    for device in devices:
        if not isinstance(device, dict):
            raise RuntimeError("The bundled hardware-wallet tool returned a malformed device.")
    report(f"Bundled HWI responded: {len(devices)} device(s) attached right now.")
    report("The device bridge works; plugging in a signer is what remains untested.")


def webview_renderer() -> str:
    """The renderer to ask pywebview for, named rather than left to chance.

    macOS has one option. On Windows the name states the intent, but asking is not
    the same as being obeyed: pywebview picks EdgeChromium when the WebView2
    runtime is present and imports the legacy MSHTML engine when it is not, with no
    error either way. ``require_edge_chromium`` checks which engine it actually
    chose, because this interface uses modern CSS that MSHTML cannot lay out.
    """
    return "edgechromium" if sys.platform == "win32" else "cocoa"


def windows_renderer() -> str:
    """Which engine pywebview will really use on this Windows machine.

    pywebview decides once, when its Windows platform module is imported, and never
    revisits it, so asking that module is the only truthful answer. Kept separate
    from the check so the check can be tested without a Windows toolkit.
    """
    from webview.platforms import winforms

    return winforms.renderer


def require_edge_chromium() -> None:
    """Refuse to open a window that would render in the legacy IE engine.

    A window that opens and renders wrong is the one failure a user cannot
    describe, and the shipped bundle has no other way to notice it: pywebview
    reports no error when the WebView2 runtime is missing, so nothing would reach
    the startup reporter. Failing here turns that silence into a message naming
    the fix.
    """
    if sys.platform != "win32":
        return
    renderer = windows_renderer()
    if renderer != "edgechromium":
        raise RuntimeError(
            "The Microsoft Edge WebView2 runtime is not installed, so the window "
            f"would fall back to the legacy {renderer} engine that cannot display "
            "this interface. Install the WebView2 runtime (free, from Microsoft) "
            "and start the app again."
        )


def run_desktop(webview_module) -> None:
    """Only the window is new; LocalApp owns the same API and state as browser mode."""
    require_edge_chromium()
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
        webview_module.start(gui=webview_renderer())
    finally:
        server.shutdown()
        server.server_close()
        if thread.is_alive():
            thread.join(timeout=5)


def startup_error_log() -> Path:
    """Where a window that failed to start leaves its traceback.

    A ``--windowed`` build has no console on any platform, so the app cannot be
    run "in a terminal" to see why it stopped: a failure to open the window looks
    like nothing happening at all. The report goes beside the settings file the
    app already owns, inside the user's own profile.
    """
    return settings_path().parent / "desktop-startup-error.log"


def windows_error_dialog(title: str, text: str) -> None:
    """A modal error box, the only way a console-less Windows app can speak."""
    import ctypes

    ctypes.windll.user32.MessageBoxW(None, text, title, 0x00000010)


def report_startup_failure(error: BaseException) -> None:
    """Say why the window did not open, where the operator can find it.

    Windows has no crash reporter and a windowed build has no console, so a
    failed start is invisible. The traceback is written next to the app's
    settings and, on Windows, shown in a message box naming that file.
    """
    details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    destination: Path | None = None
    try:
        destination = startup_error_log()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(details, encoding="utf-8")
    except OSError:
        destination = None
    if sys.platform == "win32":
        where = (
            f"The full report is in:\n{destination}"
            if destination is not None
            else "The report could not be written to disk."
        )
        windows_error_dialog(
            "Bitcoin Easy Signer",
            f"Bitcoin Easy Signer could not open its window.\n\n{error}\n\n{where}",
        )
    else:
        print(details)


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
    if sys.platform not in ("darwin", "win32"):
        raise SystemExit(
            "The desktop window bundle is built for macOS and Windows; "
            "other systems can use gui.py in a browser."
        )
    try:
        import webview
        run_desktop(webview)
    except Exception as error:
        # Nothing is watching stderr in a windowed build, so an unreported failure
        # here is indistinguishable from the app doing nothing at all.
        report_startup_failure(error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

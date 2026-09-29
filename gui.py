"""Local-only mainnet/Testnet4 wallet viewer and unsigned PSBT prototype.

Run on the user's own computer. BSMS data and unsigned PSBTs stay in memory;
only derived addresses and requested previous transactions contact the selected
public explorer after the user clicks the balance button.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import json
import math
import os
import secrets
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

from safe_http import open_url as urlopen  # TLS-verified, never follows a redirect

from network_config import NETWORKS as CHAIN_CONFIGS
from network_settings import (
    SettingsError, default_servers, load_servers, save_servers,
    validate_esplora_url, verify_esplora,
)
from version import APP_VERSION
from probe import (MAX_BSMS_BYTES, ProbeError, devices_need_attention, parse_bsms,
                   probe_devices)
from wallet_service import (WalletError, build_unsigned_psbt, estimate_fee_preview,
                            scan_wallet, wallet_summary)

MAX_REQUEST_BYTES = MAX_BSMS_BYTES + 2048
PRICE_URL = "https://mempool.space/api/v1/prices"
PRICE_CACHE_SECONDS = 300
FEES_URL = "https://mempool.space/api/v1/fees/recommended"
FEES_CACHE_SECONDS = 120
# Mainnet payments at or above this size always need the high-value confirmation,
# independent of any remote BTC/USD quote. 0.1 BTC is 10,000,000 satoshis.
LARGE_AMOUNT_SATS_FLOOR = 10_000_000


def launch_url(port: int, token: str) -> str:
    """Local app URL carrying the access token in the fragment.

    The fragment is not sent to the server and is not part of the referrer, so
    the token is never disclosed in an unauthenticated HTTP response, browser
    history, or an upstream log.
    """
    return f"http://127.0.0.1:{port}/#token={token}"


def ui_path() -> Path:
    """PyInstaller puts bundled data under _MEIPASS; source runs beside ui.html."""
    return (Path(sys._MEIPASS) / "ui.html" if getattr(sys, "frozen", False)
            else Path(__file__).with_name("ui.html"))


def fetch_btc_usd() -> dict:
    """Public mainnet BTC/USD spot reference, never a value for test coins."""
    request = Request(PRICE_URL, headers={
        "User-Agent": f"EasyMultisig/{APP_VERSION}",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=7) as response:
            body = response.read(4097)
        if len(body) > 4096:
            raise ValueError("oversized price response")
        data = json.loads(body)
        rate, timestamp = data["USD"], data["time"]
        now = datetime.now(timezone.utc).timestamp()
        if (type(rate) not in (int, float) or not math.isfinite(rate)
            or rate <= 0 or rate > 100_000_000
            or type(timestamp) is not int or not now - 1800 <= timestamp <= now + 300):
            raise ValueError("invalid or stale price")
        return {
            "usd_per_btc": rate,
            "as_of": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            "source": "mempool.space BTC/USD spot",
        }
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise WalletError("BTC/USD rate unavailable; satoshi balances are unaffected.") from exc


def fetch_fee_rates() -> dict:
    """Live mainnet guidance; no wallet data is included in the request."""
    request = Request(FEES_URL, headers={
        "User-Agent": f"EasyMultisig/{APP_VERSION}", "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=7) as response:
            body = response.read(4097)
        if len(body) > 4096:
            raise ValueError("oversized fee response")
        data = json.loads(body)
        fields = ("fastestFee", "halfHourFee", "hourFee", "economyFee", "minimumFee")
        if any(type(data[k]) is not int or not 1 <= data[k] <= 1000 for k in fields):
            raise ValueError("invalid fee quote")
        if not (data["minimumFee"] <= data["economyFee"] <= data["hourFee"]
                <= data["halfHourFee"] <= data["fastestFee"]):
            raise ValueError("inconsistent fee quote")
        return {
            "fastest": data["fastestFee"], "standard": data["halfHourFee"],
            "hour": data["hourFee"], "economy": data["economyFee"],
            "minimum": data["minimumFee"],
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "network": "main",
            "source": "mempool.space mainnet",
        }
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise WalletError("Fee estimates unavailable; the 1–25 sat/vB safety limit remains.") from exc


def public_scan(result: dict) -> dict:
    """Only summary fields cross the local API; UTXO internals stay in process."""
    return {
        "network": result["network"],
        "confirmed_sats": result["confirmed_sats"],
        "pending_delta_sats": result["pending_delta_sats"],
        "observed_sats": result["observed_sats"],
        "addresses": result["addresses"],
        "utxo_count": len(result["utxos"]),
        "scanned": result["scanned"],
        "coverage_limited": result["coverage_limited"],
        "utxo_consistent": result["utxo_consistent"],
        "path_warning": result["path_warning"],
        "scanned_at": result["scanned_at"],
        "source": result["source"],
    }


def save_prepared_psbt(state: "LocalApp", chain, folder: Path | None = None) -> dict:
    """Write the app's currently prepared PSBT into the user's Downloads folder.

    The bytes come from server-side state and never from the page, so nothing a
    web page sends can influence what is written or where. An existing file is
    never replaced: each save gets a new name.
    """
    with state.lock:
        prepared = state.prepared_psbt
        active = state.chain
    if not prepared or chain != active:
        raise WalletError("Prepare and review a transaction before saving it.")
    try:
        raw = base64.b64decode(prepared, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise WalletError("The prepared transaction is not valid.") from exc
    if not raw.startswith(b"psbt\xff") or len(raw) > 2_000_000:
        raise WalletError("The prepared transaction is not valid or is too large.")
    if folder is None:
        folder = Path.home() / "Downloads"
        if not folder.is_dir():
            folder = Path.home()
    for suffix in ("",) + tuple(f"-{n}" for n in range(2, 100)):
        target = folder / f"{chain}-unsigned{suffix}.psbt"
        try:
            handle = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        except OSError as exc:
            raise WalletError(f"Could not save the transaction file to {folder}.") from exc
        try:
            with os.fdopen(handle, "wb") as output:
                if output.write(raw) != len(raw):
                    raise OSError("Incomplete write.")
                output.flush()
                os.fsync(output.fileno())
        except OSError as exc:
            try:
                os.unlink(target)
            except OSError:
                pass
            raise WalletError(f"Could not save the transaction file to {folder}.") from exc
        return {"saved": True, "path": str(target)}
    raise WalletError(
        f"Too many files named {chain}-unsigned*.psbt already exist in {folder}. "
        "Move or rename some and try again."
    )


class LocalApp:
    def __init__(self, *, desktop: bool = False):
        self.token = secrets.token_urlsafe(32)
        self.desktop = desktop
        self.lock = threading.RLock()
        self.record = None
        self.chain = None
        self.explorer_consent = False
        self.scan = None
        self.prepared_psbt = None
        self.prepared_id = None
        self.revision = 0
        self.scan_generation = 0
        self.price = None
        self.price_checked = 0.0
        self.fees = None
        self.fees_checked = 0.0
        try:
            self.servers = load_servers()
            self.settings_error = ""
        except SettingsError as exc:
            self.servers = default_servers()
            self.settings_error = str(exc)

    def handler(self):
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                # Do not log wallet identifiers, browser requests or PSBTs.
                pass

            def _headers(self, status, content_type, size):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'none'; script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
                )
                self.end_headers()

            def _send(self, status, data):
                body = json.dumps(data).encode("utf-8")
                self._headers(status, "application/json; charset=utf-8", len(body))
                self.wfile.write(body)

            def _trusted_host(self):
                return self.headers.get("Host") == (
                    f"127.0.0.1:{self.server.server_address[1]}"
                )

            def do_GET(self):
                if not self._trusted_host():
                    self._send(403, {"error": "Local access only."})
                    return
                if self.path == "/":
                    page = ui_path().read_text(encoding="utf-8")
                    # The access token is deliberately NOT placed in this
                    # unauthenticated response. It travels in the URL fragment of
                    # the launch URL, which a browser never sends to the server.
                    body = (page.replace("__LOCAL_TOKEN__", "")
                            .replace("__APP_VERSION__", APP_VERSION)
                            .replace("__DESKTOP_MODE__", "true" if state.desktop else "false")
                            .replace("__DESKTOP_HIDE_QUIT__", "hidden" if state.desktop else "")
                            .encode("utf-8"))
                    self._headers(200, "text/html; charset=utf-8", len(body))
                    self.wfile.write(body)
                elif self.path == "/api/price":
                    with state.lock:
                        cached = (state.price if state.price is not None
                                  and time.monotonic() - state.price_checked < PRICE_CACHE_SECONDS
                                  else None)
                    if cached is None:
                        try:
                            cached = fetch_btc_usd()
                        except WalletError as exc:
                            self._send(503, {"error": str(exc)})
                            return
                        with state.lock:
                            state.price = cached
                            state.price_checked = time.monotonic()
                    self._send(200, cached)
                elif self.path == "/api/fees":
                    with state.lock:
                        cached = (state.fees if state.fees is not None
                                  and time.monotonic() - state.fees_checked < FEES_CACHE_SECONDS
                                  else None)
                    if cached is None:
                        try:
                            cached = fetch_fee_rates()
                        except WalletError as exc:
                            self._send(503, {"error": str(exc)})
                            return
                        with state.lock:
                            state.fees = cached
                            state.fees_checked = time.monotonic()
                    self._send(200, cached)
                else:
                    self._send(404, {"error": "Not found."})

            def do_POST(self):
                origin = self.headers.get("Origin")
                expected = f"http://127.0.0.1:{self.server.server_address[1]}"
                if (not self._trusted_host()
                    or (origin is not None and origin != expected)
                    or not hmac.compare_digest(
                        self.headers.get("X-Local-Token") or "", state.token
                    )):
                    self._send(403, {"error": "Local access only."})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if (self.headers.get("Content-Type", "").split(";")[0]
                        != "application/json"
                        or length < 2 or length > MAX_REQUEST_BYTES):
                        raise WalletError("Wallet request is too large or malformed.")
                    request = json.loads(self.rfile.read(length))
                    if not isinstance(request, dict):
                        raise WalletError("Wallet request is malformed.")
                    if self.path == "/api/import":
                        self._import(request)
                    elif self.path == "/api/scan":
                        self._scan(request)
                    elif self.path == "/api/prepare":
                        self._prepare(request)
                    elif self.path == "/api/save":
                        self._save(request)
                    elif self.path == "/api/devices":
                        self._devices(request)
                    elif self.path == "/api/estimate":
                        self._estimate(request)
                    elif self.path == "/api/status":
                        self._status()
                    elif self.path == "/api/settings":
                        self._settings(request)
                    elif self.path == "/api/quit":
                        self._send(200, {"stopped": True})
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                    else:
                        self._send(404, {"error": "Not found."})
                except (ProbeError, WalletError, SettingsError) as exc:
                    self._send(400, {"error": str(exc)})
                except (ValueError, TypeError, UnicodeError):
                    self._send(400, {"error": "Wallet request is malformed."})
                except Exception:
                    self._send(500, {"error": "Operation failed safely. No transaction was sent."})

            def _import(self, data):
                chain = data.get("chain")
                if chain not in CHAIN_CONFIGS or not isinstance(data.get("text"), str):
                    raise WalletError("Select mainnet or Testnet4 and choose a BSMS file.")
                if data.get("consent_explorer") is not True:
                    raise WalletError("Confirm public-explorer address disclosure before opening a wallet.")
                with state.lock:
                    state.record = None
                    state.chain = None
                    state.explorer_consent = False
                    state.scan = None
                    state.prepared_psbt = None
                    state.prepared_id = None
                    state.revision += 1
                    state.scan_generation += 1
                    revision = state.revision
                record = parse_bsms(data["text"])
                if record.network != CHAIN_CONFIGS[chain].record_network:
                    raise WalletError("BSMS wallet address does not match the selected network.")
                summary = wallet_summary(record)
                with state.lock:
                    if revision != state.revision:
                        raise WalletError("Wallet changed; import it again.")
                    state.record = record
                    state.chain = chain
                    state.explorer_consent = True
                self._send(200, summary)

            def _scan(self, data):
                with state.lock:
                    record, revision, chain = state.record, state.revision, state.chain
                    if data.get("chain") != chain or chain not in CHAIN_CONFIGS:
                        raise WalletError("Selected network does not match the open wallet.")
                    if not state.explorer_consent:
                        raise WalletError("Public-explorer address disclosure has not been confirmed.")
                    if state.settings_error:
                        raise WalletError(state.settings_error)
                    explorer = state.servers[chain]["explorer"]
                    state.scan = None
                    state.prepared_psbt = None
                    state.prepared_id = None
                    state.scan_generation += 1
                    generation = state.scan_generation
                if record is None:
                    raise WalletError("Import a BSMS wallet first.")
                if explorer != CHAIN_CONFIGS[chain].explorer_url:
                    verify_esplora(chain, explorer)
                result = scan_wallet(record, base_url=explorer)
                with state.lock:
                    if revision != state.revision or generation != state.scan_generation:
                        raise WalletError("Wallet or balance changed during scan; refresh again.")
                    state.scan = result
                self._send(200, public_scan(result))

            def _status(self):
                with state.lock:
                    wallet = wallet_summary(state.record) if state.record else None
                    balance = public_scan(state.scan) if state.scan else None
                    chain = state.chain
                    consent = state.explorer_consent
                self._send(200, {"wallet": wallet, "balance": balance,
                                 "chain": chain, "explorer_consent": consent})

            def _devices(self, data):
                with state.lock:
                    record, chain, preparation_id = state.record, state.chain, state.prepared_id
                if record is None or chain is None:
                    raise WalletError("Open a wallet before checking for signers.")
                # Two legitimate uses. A pre-flight check needs only an open wallet
                # and no transaction: nothing can be mistaken for approval, and the
                # response says so. The check inside a send must belong to the review
                # on screen, so a supplied preparation id must still match. Any
                # future signing endpoint must require the review, not merely allow it.
                supplied = data.get("preparation_id")
                if supplied and supplied != preparation_id:
                    raise WalletError("Review a transaction before continuing to signer recognition.")
                hwi_chain = "main" if chain == "main" else "testnet4"
                statuses = probe_devices(record, "hwi", hwi_chain)
                self._send(200, {
                    "devices": statuses,
                    "attention": devices_need_attention(statuses),
                    "message": ("No compatible hardware signer detected." if not statuses
                                else ("Device check complete. This check does not sign or send."
                                      if supplied else
                                      "Device check complete. This reads public identities only; "
                                      "no transaction was involved.")),
                })

            def _save(self, data):
                self._send(200, save_prepared_psbt(state, data.get("chain")))

            def _estimate(self, data):
                with state.lock:
                    record, scan, chain = state.record, state.scan, state.chain
                if record is None or scan is None or data.get("chain") != chain:
                    raise WalletError("Refresh the open wallet before estimating a transaction.")
                send_all = data.get("send_all", False)
                if type(send_all) is not bool:
                    raise WalletError("Choose either a partial amount or Send all.")
                recipient = data.get("recipient")
                self._send(200, estimate_fee_preview(
                    record, scan, send_all,
                    amount=data.get("amount_sats"),
                    fee_rate=data.get("fee_rate", 2),
                    recipient=recipient if isinstance(recipient, str) else None,
                ))

            def _settings(self, data):
                chain = data.get("chain")
                if chain not in CHAIN_CONFIGS:
                    raise WalletError("Select mainnet or Testnet4 for server settings.")
                action = data.get("action")
                if action not in ("read", "save", "reset"):
                    raise WalletError("Server settings action is invalid.")
                if action != "read":
                    defaults = default_servers()[chain]
                    chosen = (defaults if action == "reset" else {
                        "explorer": validate_esplora_url(data.get("explorer_url")),
                        "broadcaster": validate_esplora_url(data.get("broadcaster_url")),
                    })
                    # Both endpoints use Esplora HTTP; Electrum TLS is a different protocol.
                    for url in set(chosen.values()) - set(defaults.values()):
                        verify_esplora(chain, url)
                    with state.lock:
                        updated = {key: dict(value) for key, value in state.servers.items()}
                        updated[chain] = chosen
                        save_servers(updated)  # Never persist BSMS, addresses or keys.
                        state.servers = updated
                        state.settings_error = ""
                        if chain == state.chain:
                            state.scan = None
                            state.prepared_psbt = None
                            state.prepared_id = None
                            state.scan_generation += 1
                with state.lock:
                    active = dict(state.servers[chain])
                    error = state.settings_error
                self._send(200, {
                    "chain": chain, "explorer_url": active["explorer"],
                    "broadcaster_url": active["broadcaster"],
                    "default_url": CHAIN_CONFIGS[chain].explorer_url,
                    "broadcasting_available": False,
                    "settings_error": error,
                })

            def _prepare(self, data):
                with state.lock:
                    state.prepared_psbt = None
                    state.prepared_id = None
                    record, scan, revision, chain = (
                        state.record, state.scan, state.revision, state.chain
                    )
                    if state.settings_error:
                        raise WalletError(state.settings_error)
                    explorer = state.servers[chain]["explorer"] if chain else None
                if record is None or scan is None:
                    raise WalletError("Open a wallet and refresh its balance before preparing an unsigned transaction.")
                if data.get("chain") != chain:
                    raise WalletError("Selected network does not match the open wallet.")
                if scan.get("source") != explorer:
                    raise WalletError("Explorer changed since the balance scan; refresh before preparing.")
                if explorer != CHAIN_CONFIGS[chain].explorer_url:
                    verify_esplora(chain, explorer)
                with state.lock:
                    fee_quote = (state.fees if state.fees is not None
                                 and time.monotonic() - state.fees_checked < FEES_CACHE_SECONDS
                                 else None)
                if fee_quote is None:
                    try:
                        fee_quote = fetch_fee_rates()
                    except WalletError as exc:
                        raise WalletError(
                            "Live mainnet fee reference is unavailable; "
                            "no unsigned transaction file will be prepared."
                        ) from exc
                    with state.lock:
                        state.fees = fee_quote
                        state.fees_checked = time.monotonic()
                if fee_quote["standard"] > 25:
                    raise WalletError(
                        "Current mainnet standard fee exceeds this app's 25 sat/vB "
                        "safety cap. Wait or use an established wallet."
                    )
                if chain == "main":
                    with state.lock:
                        price = (state.price if state.price is not None
                                 and time.monotonic() - state.price_checked < PRICE_CACHE_SECONDS
                                 else None)
                    if price is None:
                        price = fetch_btc_usd()
                        with state.lock:
                            state.price = price
                            state.price_checked = time.monotonic()
                    requested_amount = (scan["confirmed_sats"] if data.get("send_all")
                                        else data.get("amount_sats"))
                    # Two independent triggers: an absolute satoshi floor that no
                    # remote feed can influence, and the USD reference when the
                    # price quote is available.
                    if (type(requested_amount) is int
                        and (requested_amount >= LARGE_AMOUNT_SATS_FLOOR
                             or requested_amount * price["usd_per_btc"] / 100_000_000 >= 10_000)
                        and data.get("large_amount_confirmed") is not True):
                        raise WalletError(
                            "This is a large mainnet payment: at least 0.1 BTC, or worth "
                            "$10,000 or more at the current BTC/USD reference. Confirm the "
                            "BTC amount and dollar equivalent before preparing it."
                        )
                requested_rate = data.get("fee_rate", 2)
                if type(requested_rate) is not int or not 1 <= requested_rate <= 25:
                    raise WalletError("Fee rate must be a whole number from 1 to 25 sat/vB.")
                if requested_rate < fee_quote["economy"]:
                    raise WalletError(
                        f"{requested_rate} sat/vB is below the live mainnet economy "
                        f"reference of {fee_quote['economy']} sat/vB. Choose a current "
                        "suggestion or wait."
                    )
                result = build_unsigned_psbt(
                    record, scan, data.get("recipient"), data.get("amount_sats"),
                    requested_rate, base_url=explorer, send_all=data.get("send_all", False),
                )
                if requested_rate < fee_quote["standard"]:
                    low_warning = (
                        f"{requested_rate} sat/vB is below the current mainnet "
                        f"standard reference of {fee_quote['standard']} sat/vB. "
                        "Confirmation may take longer; check the rate again."
                    )
                    result["fee_warning"] = " ".join(
                        part for part in (result["fee_warning"], low_warning) if part
                    )
                result["explorer_web"] = CHAIN_CONFIGS[chain].web_url
                result["fee_reference"] = {
                    "standard": fee_quote["standard"],
                    "economy": fee_quote["economy"],
                    "checked_at": fee_quote["checked_at"],
                    "network": fee_quote["network"],
                }
                with state.lock:
                    if revision != state.revision or scan is not state.scan:
                        raise WalletError("Wallet or balance changed; review and prepare again.")
                    state.prepared_psbt = result["psbt_base64"]
                    state.prepared_id = secrets.token_urlsafe(18)
                    result["preparation_id"] = state.prepared_id
                self._send(200, result)

        return Handler


def main():
    state = LocalApp()
    server = ThreadingHTTPServer(("127.0.0.1", 0), state.handler())
    port = server.server_address[1]
    # Printed without the token so it stays out of terminal scrollback and logs.
    display_url = f"http://127.0.0.1:{port}/"
    print("Bitcoin Easy Signer — local mainnet/Testnet4 GUI")
    print("No wallet file is uploaded to a hosted server.")
    print(f"Opening {display_url} in your browser. Close this window to stop the app.")
    threading.Timer(0.5, lambda: webbrowser.open(launch_url(port, state.token))).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

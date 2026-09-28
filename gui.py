"""Local-only, point-and-click Testnet4 wallet prototype.

Run on the user's own computer. BSMS data and unsigned PSBTs stay in memory;
only derived addresses and requested previous transactions contact the public
Testnet4 explorer after the user clicks the balance button.
"""

from __future__ import annotations

import json
import math
import secrets
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from probe import MAX_BSMS_BYTES, ProbeError, parse_bsms
from wallet_service import WalletError, build_unsigned_psbt, scan_wallet, wallet_summary

MAX_REQUEST_BYTES = MAX_BSMS_BYTES + 2048
PRICE_URL = "https://mempool.space/api/v1/prices"
PRICE_CACHE_SECONDS = 300


def fetch_btc_usd() -> dict:
    """Public mainnet BTC/USD spot reference, never a value for test coins."""
    request = Request(PRICE_URL, headers={
        "User-Agent": "EasyMultisigTestnet4/0.0.5",
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


class LocalApp:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.record = None
        self.scan = None
        self.revision = 0
        self.price = None
        self.price_checked = 0.0

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
                    page = Path(__file__).with_name("ui.html").read_text(encoding="utf-8")
                    body = page.replace("__LOCAL_TOKEN__", state.token).encode("utf-8")
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
                else:
                    self._send(404, {"error": "Not found."})

            def do_POST(self):
                origin = self.headers.get("Origin")
                expected = f"http://127.0.0.1:{self.server.server_address[1]}"
                if (not self._trusted_host()
                    or (origin is not None and origin != expected)
                    or self.headers.get("X-Local-Token") != state.token):
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
                    elif self.path == "/api/quit":
                        self._send(200, {"stopped": True})
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                    else:
                        self._send(404, {"error": "Not found."})
                except (ProbeError, WalletError) as exc:
                    self._send(400, {"error": str(exc)})
                except (ValueError, TypeError, UnicodeError):
                    self._send(400, {"error": "Wallet request is malformed."})
                except Exception:
                    self._send(500, {"error": "Operation failed safely. No transaction was sent."})

            def _import(self, data):
                if data.get("chain") != "testnet4" or not isinstance(data.get("text"), str):
                    raise WalletError("Select Testnet4 and choose a BSMS file.")
                with state.lock:
                    state.record = None
                    state.scan = None
                    state.revision += 1
                    revision = state.revision
                record = parse_bsms(data["text"])
                summary = wallet_summary(record)
                with state.lock:
                    if revision != state.revision:
                        raise WalletError("Wallet changed; import it again.")
                    state.record = record
                self._send(200, summary)

            def _scan(self, data):
                if data.get("chain") != "testnet4":
                    raise WalletError("Testnet4 must be selected.")
                with state.lock:
                    record, revision = state.record, state.revision
                    state.scan = None
                if record is None:
                    raise WalletError("Import a BSMS wallet first.")
                result = scan_wallet(record)
                with state.lock:
                    if revision != state.revision:
                        raise WalletError("Wallet changed during scan; refresh again.")
                    state.scan = result
                self._send(200, {
                    "confirmed_sats": result["confirmed_sats"],
                    "pending_delta_sats": result["pending_delta_sats"],
                    "observed_sats": result["observed_sats"],
                    "addresses": result["addresses"],
                    "utxo_count": len(result["utxos"]),
                    "scanned": result["scanned"],
                    "coverage_limited": result["coverage_limited"],
                    "path_warning": result["path_warning"],
                    "scanned_at": result["scanned_at"],
                    "source": result["source"],
                })

            def _prepare(self, data):
                with state.lock:
                    record, scan, revision = state.record, state.scan, state.revision
                if record is None or scan is None:
                    raise WalletError("Import and refresh the balance before preparing a PSBT.")
                if data.get("chain") != "testnet4":
                    raise WalletError("Testnet4 must be selected.")
                result = build_unsigned_psbt(
                    record, scan, data.get("recipient"), data.get("amount_sats"),
                    data.get("fee_rate", 2),
                )
                with state.lock:
                    if revision != state.revision or scan is not state.scan:
                        raise WalletError("Wallet or balance changed; review and prepare again.")
                self._send(200, result)

        return Handler


def main():
    state = LocalApp()
    server = ThreadingHTTPServer(("127.0.0.1", 0), state.handler())
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print("Easy Bitcoin Multisig Signer — Testnet4 local GUI")
    print("No wallet file is uploaded to a hosted server.")
    print(f"Opening {url} in your browser. Close this window to stop the app.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
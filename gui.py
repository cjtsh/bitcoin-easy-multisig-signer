"""Local-only mainnet/Testnet4 wallet viewer and unsigned PSBT prototype.

Run on the user's own computer. BSMS data and unsigned PSBTs stay in memory;
only derived addresses and requested previous transactions contact the selected
public explorer after the user clicks the balance button.
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
FEES_URL = "https://mempool.space/api/v1/fees/recommended"
FEES_CACHE_SECONDS = 120


def fetch_btc_usd() -> dict:
    """Public mainnet BTC/USD spot reference, never a value for test coins."""
    request = Request(PRICE_URL, headers={
        "User-Agent": "EasyMultisig/0.0.6",
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
        "User-Agent": "EasyMultisig/0.0.6", "Accept": "application/json",
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
        "network": result.get("network", "testnet4"),
        "confirmed_sats": result["confirmed_sats"],
        "pending_delta_sats": result["pending_delta_sats"],
        "observed_sats": result["observed_sats"],
        "addresses": result["addresses"],
        "utxo_count": len(result["utxos"]),
        "scanned": result["scanned"],
        "coverage_limited": result["coverage_limited"],
        "utxo_consistent": result.get("utxo_consistent", True),
        "path_warning": result["path_warning"],
        "scanned_at": result["scanned_at"],
        "source": result["source"],
    }


class LocalApp:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.record = None
        self.chain = None
        self.mainnet_consent = False
        self.scan = None
        self.revision = 0
        self.scan_generation = 0
        self.price = None
        self.price_checked = 0.0
        self.fees = None
        self.fees_checked = 0.0

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
                    elif self.path == "/api/status":
                        self._status()
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
                chain = data.get("chain")
                if chain not in ("main", "testnet4") or not isinstance(data.get("text"), str):
                    raise WalletError("Select mainnet or Testnet4 and choose a BSMS file.")
                if chain == "main" and data.get("consent_explorer") is not True:
                    raise WalletError("Confirm public-explorer address disclosure before opening mainnet.")
                with state.lock:
                    state.record = None
                    state.chain = None
                    state.mainnet_consent = False
                    state.scan = None
                    state.revision += 1
                    state.scan_generation += 1
                    revision = state.revision
                record = parse_bsms(data["text"])
                if record.network != ("main" if chain == "main" else "test"):
                    raise WalletError("BSMS wallet address does not match the selected network.")
                summary = wallet_summary(record)
                with state.lock:
                    if revision != state.revision:
                        raise WalletError("Wallet changed; import it again.")
                    state.record = record
                    state.chain = chain
                    state.mainnet_consent = chain == "main"
                self._send(200, summary)

            def _scan(self, data):
                with state.lock:
                    record, revision, chain = state.record, state.revision, state.chain
                    if data.get("chain") != chain or chain not in ("main", "testnet4"):
                        raise WalletError("Selected network does not match the open wallet.")
                    if chain == "main" and not state.mainnet_consent:
                        raise WalletError("Mainnet address disclosure has not been confirmed.")
                    state.scan = None
                    state.scan_generation += 1
                    generation = state.scan_generation
                if record is None:
                    raise WalletError("Import a BSMS wallet first.")
                result = scan_wallet(record)
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
                    consent = state.mainnet_consent
                self._send(200, {"wallet": wallet, "balance": balance,
                                 "chain": chain, "mainnet_consent": consent})

            def _prepare(self, data):
                with state.lock:
                    record, scan, revision, chain = (
                        state.record, state.scan, state.revision, state.chain
                    )
                if record is None or scan is None:
                    raise WalletError("Import and refresh the balance before preparing a PSBT.")
                if data.get("chain") != chain:
                    raise WalletError("Selected network does not match the open wallet.")
                if chain == "main":
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
                                "no mainnet PSBT will be prepared."
                            ) from exc
                        with state.lock:
                            state.fees = fee_quote
                            state.fees_checked = time.monotonic()
                    if fee_quote["standard"] > 25:
                        raise WalletError(
                            "Current mainnet standard fee exceeds this app's 25 sat/vB "
                            "safety cap. Wait or use an established wallet."
                        )
                    requested_rate = data.get("fee_rate", 2)
                    if type(requested_rate) is not int or not 1 <= requested_rate <= 25:
                        raise WalletError("Fee rate must be a whole number from 1 to 25 sat/vB.")
                    if requested_rate < fee_quote["economy"]:
                        raise WalletError(
                            f"{requested_rate} sat/vB is below the live mainnet economy "
                            f"estimate of {fee_quote['economy']} sat/vB. Choose a current "
                            "suggestion or wait."
                        )
                result = build_unsigned_psbt(
                    record, scan, data.get("recipient"), data.get("amount_sats"),
                    data.get("fee_rate", 2),
                )
                if chain == "main":
                    if requested_rate < fee_quote["standard"]:
                        low_warning = (
                            f"{requested_rate} sat/vB is below the current mainnet "
                            f"standard estimate of {fee_quote['standard']} sat/vB. "
                            "Confirmation may take longer; check the rate again."
                        )
                        result["fee_warning"] = " ".join(
                            part for part in (result["fee_warning"], low_warning) if part
                        )
                    result["fee_reference"] = {
                        "standard": fee_quote["standard"],
                        "economy": fee_quote["economy"],
                        "checked_at": fee_quote["checked_at"],
                    }
                with state.lock:
                    if revision != state.revision or scan is not state.scan:
                        raise WalletError("Wallet or balance changed; review and prepare again.")
                self._send(200, result)

        return Handler


def main():
    state = LocalApp()
    server = ThreadingHTTPServer(("127.0.0.1", 0), state.handler())
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print("Easy Bitcoin Multisig Signer — local mainnet/Testnet4 GUI")
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
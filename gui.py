"""Local-only Bitcoin wallet, PSBT signing and practice-network broadcast.

Run on the user's own computer. BSMS data and unsigned PSBTs stay in memory;
only derived addresses and requested previous transactions contact the selected
public explorer after the user clicks the balance button.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import hashlib
import json
import math
import os
import re
import secrets
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

from embit.networks import NETWORKS
from embit.psbt import PSBT

from safe_http import open_url as urlopen  # TLS-verified, never follows a redirect

from network_config import NETWORKS as CHAIN_CONFIGS, SECONDARY_EXPLORERS
from network_settings import (
    SettingsError, default_servers, load_servers, save_servers,
    validate_esplora_url, verify_esplora,
)
from version import APP_VERSION
from probe import (MAX_BSMS_BYTES, ProbeError, device_advice, devices_need_attention, parse_bsms,
                   probe_devices_detailed, sign_psbt_with_device, verify_signer_device)
from signing import (SigningError, accept_signature_update, finalize_multisig,
                     is_complete, signatures_collected, signed_by_signers)
from wallet_service import (BroadcastOutcomeUnknown, WalletError, broadcast_transaction,
                            build_unsigned_psbt, check_selected_outpoints,
                            estimate_fee_preview, explorer_get, scan_wallet, wallet_summary)

MAX_REQUEST_BYTES = MAX_BSMS_BYTES + 2048
PRICE_URL = "https://mempool.space/api/v1/prices"
PRICE_CACHE_SECONDS = 300
FEES_URL = "https://mempool.space/api/v1/fees/recommended"
FEES_CACHE_SECONDS = 120
# Mainnet payments at or above this size always need the high-value confirmation,
# independent of any remote BTC/USD quote. 0.1 BTC is 10,000,000 satoshis.
LARGE_AMOUNT_SATS_FLOOR = 10_000_000
DIAGNOSTIC_STAGES = frozenset({
    "wallet_import", "change_path", "wallet_scan", "transaction_prepare",
    "signer_check", "signer_response", "final_transaction", "broadcast",
})
# Which stage a rejected request belongs to. The route name and the stage name
# never matched ("prepare" vs "transaction_prepare"), so every rejection used to
# be recorded as an unattributable "request": a refused signature was
# indistinguishable from a refused fee estimate.
#
# Routes absent from this map are convenience calls - fee estimates, price,
# settings, status. Their rejections are ordinary interface feedback, so they are
# deliberately not recorded: the buffer holds 80 events, and that chatter used to
# push out the events that matter.
DIAGNOSTIC_ROUTE_STAGES = {
    "import": "wallet_import",
    "scan": "wallet_scan",
    "prepare": "transaction_prepare",
    "devices": "signer_check",
    "sign": "signer_response",
    "finalize": "final_transaction",
    "broadcast": "broadcast",
}
DIAGNOSTIC_OUTCOMES = frozenset({
    "passed", "declared", "standard", "missing", "complete", "incomplete",
    "consistent", "inconsistent", "verified", "rejected", "accepted", "unknown",
})


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


def fetch_mutinynet_fee_rates() -> dict:
    """Mutinynet Esplora rates, queried without wallet identifiers."""
    request = Request(CHAIN_CONFIGS["mutinynet"].explorer_url + "/fee-estimates",
                      headers={"User-Agent": f"EasyMultisig/{APP_VERSION}",
                               "Accept": "application/json"})
    try:
        with urlopen(request, timeout=7) as response:
            body = response.read(4097)
        if len(body) > 4096:
            raise ValueError("oversized fee response")
        data = json.loads(body)
        keys = ("1", "3", "6", "144", "1008")
        if not isinstance(data, dict) or not all(
            type(data.get(key)) in (int, float) and math.isfinite(data[key])
            and 0 < data[key] <= 1000 for key in keys
        ):
            raise ValueError("invalid fee quote")
        rates = [math.ceil(data[key]) for key in keys]
        if not rates[4] <= rates[3] <= rates[2] <= rates[1] <= rates[0]:
            raise ValueError("invalid fee quote")
        return {"fastest": rates[0], "standard": rates[1], "hour": rates[2],
                "economy": rates[3], "minimum": rates[4],
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "network": "mutinynet", "source": "mutinynet.com Esplora"}
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError,
            KeyError, TypeError) as exc:
        raise WalletError("Mutinynet fee estimates unavailable; preparation is paused.") from exc


def public_scan(result: dict) -> dict:
    """Only summary fields cross the local API; UTXO internals stay in process."""
    return {
        "network": result["network"],
        "confirmed_sats": result["confirmed_sats"],
        "pending_delta_sats": result["pending_delta_sats"],
        "pending_outgoing": result.get("pending_outgoing", False),
        "broadcast_outcome_unknown": result.get("broadcast_outcome_unknown", False),
        "observed_sats": result["observed_sats"],
        "addresses": result["addresses"],
        "utxo_count": len(result["utxos"]),
        "scanned": result["scanned"],
        "coverage_limited": result["coverage_limited"],
        "range_limited": result.get("range_limited", result["coverage_limited"]),
        "missing_change": result.get("missing_change", False),
        "utxo_consistent": result["utxo_consistent"],
        "path_warning": result["path_warning"],
        "scanned_at": result["scanned_at"],
        "source": result["source"],
    }


def wallet_identity(record, chain: str) -> bytes:
    """Session-only key for a pending broadcast, including the chosen chain.

    A reimport of the same BSMS file must not erase an uncertain broadcast and
    allow a duplicate payment before the explorer has caught up.
    """
    material = json.dumps([chain, record.descriptor_text,
                           record.reference_address], separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).digest()


def independent_explorer(chain: str, primary: str) -> str | None:
    """Choose a distinct public backend for mainnet outpoint cross-checks."""
    secondary = SECONDARY_EXPLORERS.get(chain)
    if secondary == primary:
        secondary = CHAIN_CONFIGS[chain].explorer_url
    return secondary


def verify_selected_outpoints(packet: PSBT | str, chain: str, primary: str) -> None:
    """One fail-closed gate used at preparation and immediately before submit."""
    secondary = independent_explorer(chain, primary)
    if secondary:
        verify_esplora(chain, secondary)
        heights = []
        for base in (primary, secondary):
            raw = explorer_get("/blocks/tip/height", text=True, chain=chain,
                               base_url=base)
            if (not isinstance(raw, str) or not raw.strip().isdecimal()
                    or len(raw.strip()) > 10):
                raise WalletError("An explorer gave an unclear blockchain height; no payment was prepared or sent.")
            heights.append(int(raw.strip()))
        if abs(heights[0] - heights[1]) > 2:
            raise WalletError(
                "The two blockchain sources disagree or one is behind. "
                "Wait and refresh before preparing or sending."
            )
    try:
        parsed = PSBT.from_base64(packet) if isinstance(packet, str) else packet
    except Exception as exc:
        raise WalletError("The prepared transaction cannot be checked.") from exc
    check_selected_outpoints(parsed, chain, primary, secondary)


@dataclass(frozen=True)
class PreparedPayment:
    """One reviewed payment; signing replaces this whole value atomically.

    The record identity and scan generation prevent a signature returned after
    import or refresh from being attached to a different wallet or balance.
    Review values and selected outpoints are immutable snapshots. The PSBT may
    gain signatures, but device metadata is discarded; only signatures verified
    against this reviewed PSBT are retained.
    """
    wallet: object
    chain: str
    scan_generation: int
    review_id: str
    psbt_base64: str
    txid: str
    review_items: tuple[tuple[str, object], ...]
    outpoints: tuple[tuple[str, int], ...]

    @classmethod
    def create(cls, wallet, chain, generation, review_id, encoded, review):
        packet = PSBT.from_base64(encoded)
        txid = packet.tx.txid().hex()
        if txid != review.get("txid"):
            raise WalletError("The reviewed transaction ID is inconsistent.")
        return cls(wallet, chain, generation, review_id, encoded, txid,
                   tuple(review.items()),
                   tuple((vin.txid.hex(), vin.vout) for vin in packet.tx.vin))

    def checked_psbt(self) -> PSBT:
        packet = PSBT.from_base64(self.psbt_base64)
        if (packet.tx.txid().hex() != self.txid or
            tuple((vin.txid.hex(), vin.vout) for vin in packet.tx.vin) != self.outpoints):
            raise WalletError("The prepared transaction changed. Review it again.")
        return packet

    def review(self) -> dict:
        return dict(self.review_items)


def save_prepared_psbt(state: "LocalApp", chain, folder: Path | None = None) -> dict:
    """Write the app's currently prepared PSBT into the user's Downloads folder.

    The bytes come from server-side state and never from the page, so nothing a
    web page sends can influence what is written or where. An existing file is
    never replaced: each save gets a new name.
    """
    with state.lock:
        prepared = state.prepared.psbt_base64 if state.prepared else None
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


def _clean_token(value) -> str:
    """Reduce a value to a short lowercase identifier, or drop it.

    Diagnostic events must never carry free text, so anything that is not a plain
    token is discarded rather than escaped or truncated into something that looks
    meaningful.
    """
    text = str(value or "").strip().lower()
    return text if re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,19}", text) else ""


# A diagnostic report may name a device *class* and nothing else. The vocabulary
# is fixed at the HWI device families this app supports: a well-formed token that
# is not a known class is dropped too, because a pattern check alone would still
# pass a 20-character address fragment or device serial that happened to fit.
DEVICE_CLASSES = frozenset({
    "bitbox02", "coldcard", "jade", "keepkey", "ledger", "trezor",
})


def _device_class(value) -> str:
    """Reduce a value to a known device class, or drop it."""
    token = _clean_token(value)
    return token if token in DEVICE_CLASSES else ""


def save_diagnostic_report(state: "LocalApp", folder: Path | None = None) -> dict:
    """Export fixed-code events only; never wallet identifiers or raw errors.

    Each event carries the selected network and, when a device was involved, its
    class. No path, serial, fingerprint, xpub, address or error text is written.
    """
    with state.lock:
        report = {"app_version": APP_VERSION, "format": 1,
                  "events": list(state.diagnostic_events)}
    destination = folder or Path.home() / "Downloads"
    if not destination.is_dir():
        raise WalletError("Downloads is unavailable; diagnostic report was not saved.")
    payload = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    for suffix in ("",) + tuple(f"-{n}" for n in range(2, 100)):
        target = destination / f"bitcoin-easy-signer-diagnostics-{APP_VERSION}{suffix}.json"
        try:
            fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        except OSError as exc:
            raise WalletError("Could not save the diagnostic report to Downloads.") from exc
        try:
            with os.fdopen(fd, "wb") as output:
                if output.write(payload) != len(payload):
                    raise OSError("Incomplete write.")
                output.flush()
                os.fsync(output.fileno())
        except OSError as exc:
            try:
                os.unlink(target)
            except OSError:
                pass
            raise WalletError("Could not save the diagnostic report to Downloads.") from exc
        return {"saved": True, "path": str(target)}
    raise WalletError("Too many diagnostic reports in Downloads; move an older report and retry.")


class LocalApp:
    def __init__(self, *, desktop: bool = False):
        self.token = secrets.token_urlsafe(32)
        self.desktop = desktop
        self.lock = threading.RLock()
        self.record = None
        self.chain = None
        self.explorer_consent = False
        self.scan = None
        # Session-only bridge between broadcast and explorer mempool propagation.
        # Never infer confirmation merely because an address scan misses the tx.
        self.pending_broadcast_txid = None
        self.pending_broadcast_unknown = False
        self.pending_by_wallet: dict[bytes, tuple[str, bool]] = {}
        self.prepared: PreparedPayment | None = None
        # Session-only binding from a successful device probe to one review.
        self.verified_signers = None
        self.diagnostic_events = []
        self.revision = 0
        self.scan_generation = 0
        self.price = None
        self.price_checked = 0.0
        self.fees = None
        self.fees_checked = 0.0
        self.mutinynet_fees = None
        self.mutinynet_fees_checked = 0.0
        try:
            self.servers = load_servers()
            self.settings_error = ""
        except SettingsError as exc:
            self.servers = default_servers()
            self.settings_error = str(exc)

    def note(self, stage: str, outcome: str, device: str = "", found=None) -> None:
        """Fixed vocabulary, bounded memory; no wallet data and no exception text.

        The selected network and, where a device was involved, its *class* are
        recorded because both change what a failure means: "broadcast accepted"
        differs between a practice network and mainnet, and the devices behave
        differently enough that "which one, when" is the first troubleshooting
        question. A device model is not an identity - no path, serial,
        fingerprint, xpub, address or error text can be written here.

        A caller that passes `found` always gets the key, even when it is empty.
        An absent key meant "nothing usable was visible", which a reader could not
        tell apart from a field that simply is not written; a real report showed
        two of four signer checks in that ambiguous state.
        """
        if stage not in DIAGNOSTIC_STAGES or outcome not in DIAGNOSTIC_OUTCOMES:
            return
        cleaned = _device_class(device)
        with self.lock:
            event = {
                "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "chain": self.chain, "stage": stage, "outcome": outcome,
            }
            if cleaned:
                event["device"] = cleaned
            if found is not None:
                event["found"] = sorted({c for c in (_device_class(x) for x in found) if c})
            self.diagnostic_events.append(event)
            del self.diagnostic_events[:-80]

    def handler(self):
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                # Do not log wallet identifiers, browser requests or PSBTs.
                pass

            def _headers(self, status, content_type, size, script_nonce=None):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                # A per-response nonce replaces 'unsafe-inline' for scripts. This
                # server has exactly one document and rebuilds it for every
                # request, so a fresh nonce costs nothing, and any script reaching
                # the page without it has no allowance to hide behind.
                script_src = (f"'nonce-{script_nonce}'" if script_nonce
                              else "'self'")
                self.send_header(
                    "Content-Security-Policy",
                    f"default-src 'none'; script-src {script_src}; "
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
                    script_nonce = secrets.token_urlsafe(18)
                    body = (page.replace("__LOCAL_TOKEN__", "")
                            .replace("__APP_VERSION__", APP_VERSION)
                            .replace("__DESKTOP_MODE__", "true" if state.desktop else "false")
                            .replace("__DESKTOP_HIDE_QUIT__", "hidden" if state.desktop else "")
                            .replace("<script>", f'<script nonce="{script_nonce}">', 1)
                            .encode("utf-8"))
                    self._headers(200, "text/html; charset=utf-8", len(body),
                                  script_nonce=script_nonce)
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
                elif self.path in ("/api/fees", "/api/fees?chain=mutinynet"):
                    mutinynet = self.path.endswith("chain=mutinynet")
                    with state.lock:
                        value = state.mutinynet_fees if mutinynet else state.fees
                        checked = (state.mutinynet_fees_checked if mutinynet
                                   else state.fees_checked)
                        cached = value if (value is not None and
                                           time.monotonic() - checked < FEES_CACHE_SECONDS) else None
                    if cached is None:
                        try:
                            cached = (fetch_mutinynet_fee_rates() if mutinynet
                                      else fetch_fee_rates())
                        except WalletError as exc:
                            self._send(503, {"error": str(exc)})
                            return
                        with state.lock:
                            if mutinynet:
                                state.mutinynet_fees = cached
                                state.mutinynet_fees_checked = time.monotonic()
                            else:
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
                    elif self.path == "/api/clear":
                        self._clear(request)
                    elif self.path == "/api/sign":
                        self._sign(request)
                    elif self.path == "/api/finalize":
                        self._finalize(request)
                    elif self.path == "/api/broadcast":
                        self._broadcast(request)
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
                    elif self.path == "/api/diagnostics":
                        self._send(200, save_diagnostic_report(state))
                    else:
                        self._send(404, {"error": "Not found."})
                except BroadcastOutcomeUnknown as exc:
                    state.note("broadcast", "unknown")
                    with state.lock:
                        txid = state.pending_broadcast_txid
                        chain = state.chain
                    self._send(409, {
                        "error": str(exc), "outcome_unknown": True,
                        "explorer": (CHAIN_CONFIGS[chain].web_url + "/tx/" + txid
                                     if txid and chain in CHAIN_CONFIGS else None),
                    })
                except (ProbeError, WalletError, SettingsError) as exc:
                    rejected = DIAGNOSTIC_ROUTE_STAGES.get(self.path.removeprefix("/api/"))
                    if rejected:
                        state.note(rejected, "rejected")
                    self._send(400, {"error": str(exc)})
                except (ValueError, TypeError, UnicodeError):
                    self._send(400, {"error": "Wallet request is malformed."})
                except Exception:
                    self._send(500, {"error": "Operation failed safely. No transaction was sent."})

            def _import(self, data):
                chain = data.get("chain")
                if chain not in CHAIN_CONFIGS or not isinstance(data.get("text"), str):
                    raise WalletError("Select a supported network and choose a BSMS file.")
                if data.get("consent_explorer") is not True:
                    raise WalletError("Confirm public-explorer address disclosure before opening a wallet.")
                with state.lock:
                    state.record = None
                    state.chain = None
                    state.explorer_consent = False
                    state.scan = None
                    state.pending_broadcast_txid = None
                    state.pending_broadcast_unknown = False
                    state.prepared = None
                    state.revision += 1
                    state.scan_generation += 1
                    revision = state.revision
                record = parse_bsms(data["text"])
                if record.network != CHAIN_CONFIGS[chain].record_network:
                    raise WalletError("BSMS wallet address does not match the selected network.")
                summary = wallet_summary(record, chain)
                with state.lock:
                    if revision != state.revision:
                        raise WalletError("Wallet changed; import it again.")
                    state.record = record
                    state.chain = chain
                    pending = state.pending_by_wallet.get(wallet_identity(record, chain))
                    if pending:
                        state.pending_broadcast_txid, state.pending_broadcast_unknown = pending
                    state.explorer_consent = True
                    state.note("wallet_import", "passed")
                    state.note("change_path", "standard" if summary["change_assumed"]
                               else "declared" if summary["can_prepare"] else "missing")
                self._send(200, summary)

            def _scan(self, data):
                with state.lock:
                    record, revision, chain = state.record, state.revision, state.chain
                    pending_txid = state.pending_broadcast_txid
                    pending_unknown = state.pending_broadcast_unknown
                    if data.get("chain") != chain or chain not in CHAIN_CONFIGS:
                        raise WalletError("Selected network does not match the open wallet.")
                    if not state.explorer_consent:
                        raise WalletError("Public-explorer address disclosure has not been confirmed.")
                    if state.settings_error:
                        raise WalletError(state.settings_error)
                    explorer = state.servers[chain]["explorer"]
                    state.scan = None
                    state.prepared = None
                    state.scan_generation += 1
                    generation = state.scan_generation
                if record is None:
                    raise WalletError("Import a BSMS wallet first.")
                if (explorer != CHAIN_CONFIGS[chain].explorer_url or
                    CHAIN_CONFIGS[chain].checkpoint_height is not None):
                    # Custom Signet shares the standard Signet genesis block.
                    # Verify its fork checkpoint even for the built-in URL.
                    verify_esplora(chain, explorer)
                result = scan_wallet(record, base_url=explorer, chain=chain)
                if pending_txid:
                    # A newly broadcast tx may not yet appear in address statistics.
                    # Fail closed on a missing/invalid status until a block confirms it.
                    try:
                        status = explorer_get(f"/tx/{pending_txid}/status", chain=chain,
                                              base_url=explorer)
                        confirmed = (isinstance(status, dict)
                                     and status.get("confirmed") is True)
                    except WalletError:
                        confirmed = False
                    result["pending_outgoing"] = result.get("pending_outgoing", False) or not confirmed
                    result["broadcast_outcome_unknown"] = (
                        pending_unknown and not confirmed)
                with state.lock:
                    if revision != state.revision or generation != state.scan_generation:
                        raise WalletError("Wallet or balance changed during scan; refresh again.")
                    state.scan = result
                    if pending_txid and pending_txid == state.pending_broadcast_txid and confirmed:
                        state.pending_by_wallet.pop(wallet_identity(record, chain), None)
                        state.pending_broadcast_txid = None
                        state.pending_broadcast_unknown = False
                    state.note("wallet_scan", "consistent" if result["utxo_consistent"] else "inconsistent")
                    state.note("wallet_scan", "incomplete" if result["coverage_limited"] else "complete")
                self._send(200, public_scan(result))

            def _status(self):
                with state.lock:
                    wallet = wallet_summary(state.record, state.chain) if state.record else None
                    balance = public_scan(state.scan) if state.scan else None
                    pending_txid = state.pending_broadcast_txid
                    pending_unknown = state.pending_broadcast_unknown
                    chain = state.chain
                    consent = state.explorer_consent
                self._send(200, {"wallet": wallet, "balance": balance,
                                 "chain": chain, "explorer_consent": consent,
                                 "pending_broadcast_explorer": (
                                     CHAIN_CONFIGS[chain].web_url + "/tx/" + pending_txid
                                     if pending_txid and chain in CHAIN_CONFIGS else None),
                                 "broadcast_outcome_unknown": pending_unknown})

            def _devices(self, data):
                with state.lock:
                    record, chain = state.record, state.chain
                    preparation_id = state.prepared.review_id if state.prepared else None
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
                # Ask HWI for "test", never "testnet4". hwilib's Jade backend keeps
                # a strict network map that predates testnet4 and raises "Unhandled
                # network: testnet4"; its neighbouring entries already map signet to
                # testnet "as far as Jade is concerned". The Trezor treats every
                # non-mainnet chain as Testnet and the Ledger derives the same coin
                # type, and testnet and testnet4 share the tpub version bytes and the
                # tb1 address prefix, so the xpub comparison is byte-exact either way.
                hwi_chain = "main" if chain == "main" else "test"
                detailed = probe_devices_detailed(record, "hwi", hwi_chain)
                if supplied:
                    with state.lock:
                        current = state.prepared
                        if (current is None or current.review_id != supplied
                                or current.wallet is not record or state.chain != chain):
                            raise WalletError("The payment changed during the device check. Review it again.")
                        state.verified_signers = (
                            supplied, record, chain,
                            tuple((d["type"], d["path"], d["signer"])
                                  for d in detailed["signable"]),
                        )
                state.note("signer_check", "passed",
                           found=[d.get("type") for d in detailed.get("signable") or []])
                statuses = detailed["statuses"]
                # Which of the wallet's cosigners have already signed, read from the
                # prepared PSBT itself rather than tracked in the page. The signing
                # screen shows one box per cosigner; deriving that from the signed
                # transaction means the boxes cannot drift from what is really there.
                with state.lock:
                    prepared = state.prepared
                signed = []
                if prepared is not None and prepared.wallet is record:
                    try:
                        signed = signed_by_signers(
                            PSBT.from_base64(prepared.psbt_base64), record)
                    except Exception:  # noqa: BLE001 - a status read, never fatal
                        signed = []
                self._send(200, {
                    "devices": statuses,
                    "signable": detailed["signable"],
                    "threshold": record.threshold,
                    "keys": len(record.keys),
                    "signed": signed,
                    "attention": devices_need_attention(statuses),
                    "message": ("No compatible hardware signer detected." if not statuses
                                else ("Device check complete. This check does not sign or send."
                                      if supplied else
                                      "Device check complete. This reads public identities only; "
                                      "no transaction was involved.")),
                })

            def _current_prepared(self, data, action: str):
                """The prepared transaction, but only the one the owner reviewed."""
                with state.lock:
                    record, chain = state.record, state.chain
                    payment = state.prepared
                    generation = state.scan_generation
                if record is None or chain is None or payment is None:
                    raise WalletError(f"Prepare and review a transaction before {action}.")
                if (payment.wallet is not record or payment.chain != chain
                    or payment.scan_generation != generation):
                    raise WalletError("The wallet or balance changed. Review the payment again.")
                if data.get("preparation_id") != payment.review_id:
                    raise WalletError(f"Review the current transaction before {action}.")
                payment.checked_psbt()
                return record, chain, payment

            def _sign(self, data):
                record, chain, payment = self._current_prepared(
                    data, "signing it")
                device_type = str(data.get("device_type") or "")
                device_path = str(data.get("device_path") or "")
                if not device_type or not device_path:
                    raise WalletError("Choose a connected device to sign with.")
                with state.lock:
                    binding = state.verified_signers
                if (binding is None or binding[0] != payment.review_id
                        or binding[1] is not record or binding[2] != chain):
                    raise WalletError("Check signing devices for this payment before signing.")
                matched = [signer for known_type, known_path, signer in binding[3]
                           if known_type == device_type and known_path == device_path]
                if len(matched) != 1:
                    raise WalletError("This device was not verified for this payment. Check devices again.")
                hwi_chain = "main" if chain == "main" else "test"
                before = payment.checked_psbt()
                try:
                    verify_signer_device(record, "hwi", hwi_chain,
                                         device_type, device_path, matched[0])
                    with state.lock:
                        if (state.prepared is not payment
                                or state.verified_signers is not binding):
                            raise WalletError("The payment changed during the device check. Review it again.")
                    updated = sign_psbt_with_device(
                        "hwi", hwi_chain, device_type, device_path, payment.psbt_base64)
                except WalletError:
                    raise
                except ProbeError as exc:
                    advice = device_advice(device_type, str(exc))
                    raise WalletError(str(exc) + (" " + advice if advice else "")) from exc
                try:
                    after = PSBT.from_base64(updated)
                except Exception as exc:
                    raise WalletError("The device returned a file this app cannot read.") from exc
                if after.tx.txid().hex() != before.tx.txid().hex():
                    raise WalletError(
                        "The device returned a different transaction, so it was refused. "
                        "Nothing was signed into the reviewed transaction."
                    )
                try:
                    accepted = accept_signature_update(before, after)
                except SigningError as exc:
                    state.note("signer_response", "rejected", device=device_type)
                    raise WalletError(str(exc)) from exc
                with state.lock:
                    if state.prepared is not payment or state.scan_generation != payment.scan_generation:
                        raise WalletError("The transaction changed while signing. Start again.")
                    state.prepared = replace(payment, psbt_base64=accepted.to_base64())
                    state.note("signer_response", "verified", device=device_type)
                present, threshold = signatures_collected(accepted)
                self._send(200, {
                    "signatures": present,
                    "threshold": threshold,
                    "signers": signed_by_signers(accepted, record),
                    "complete": is_complete(accepted),
                    "key_count": len(record.keys),
                })

            def _finalize(self, data):
                record, _chain, payment = self._current_prepared(
                    data, "finishing it")
                packet = payment.checked_psbt()
                # Read the signers first: finalising clears the partial signatures.
                signers = signed_by_signers(packet, record)
                try:
                    final = finalize_multisig(packet, payment.txid)
                except SigningError as exc:
                    raise WalletError(str(exc)) from exc
                self._check_final_review(record, packet, final, payment.review())
                state.note("final_transaction", "verified")
                self._send(200, {
                    "txid": final["txid"],
                    "vsize": final["vsize"],
                    "fee_sats": final["fee_sats"],
                    "signers": signers,
                    "destination": packet.tx.vout[0].script_pubkey.address(
                        NETWORKS[record.network]),
                    "amount_sats": packet.tx.vout[0].value,
                    "change_sats": (packet.tx.vout[1].value
                                    if len(packet.tx.vout) > 1 else 0),
                    "change_address": (packet.tx.vout[1].script_pubkey.address(
                        NETWORKS[record.network]) if len(packet.tx.vout) > 1 else None),
                    "network": _chain,
                    "effective_fee_rate": round(final["fee_sats"] / final["vsize"], 2),
                })

            def _check_final_review(self, record, packet, final, review):
                """Compare every final output and fee with the accepted review."""
                outputs = packet.tx.vout
                network = NETWORKS[record.network]
                if (not review or len(outputs) != (1 if review["send_all"] else 2)
                    or final["txid"] != review["txid"]
                    or final["fee_sats"] != review["fee_sats"]
                    or outputs[0].value != review["amount_sats"]
                    or outputs[0].script_pubkey.address(network) != review["recipient"]
                    or (not review["send_all"] and
                        (outputs[1].value != review["change_sats"]
                         or outputs[1].script_pubkey.address(network)
                            != review["change_address"]))):
                    raise WalletError("The final transaction differs from the reviewed payment.")

            def _broadcast(self, data):
                _record, chain, payment = self._current_prepared(
                    data, "broadcasting it")
                txid = payment.txid
                if data.get("confirm") is not True:
                    raise WalletError("Confirm the final transaction before broadcasting it.")
                if chain == "main" and data.get("mainnet_opt_in") is not True:
                    raise WalletError(
                        "Confirm the separate mainnet warning before broadcasting real Bitcoin."
                    )
                if str(data.get("confirmed_txid") or "") != (txid or ""):
                    raise WalletError(
                        "The confirmed transaction is not the one prepared. Nothing was sent."
                    )
                # Keep payment state locked until the network request finishes.
                # A concurrent refresh/import/settings edit must not invalidate
                # the reviewed payment during the irreversible submit call.
                with state.lock:
                    if state.prepared is not payment or state.scan_generation != payment.scan_generation:
                        raise WalletError("The payment changed before broadcast.")
                    broadcaster = state.servers[chain]["broadcaster"]
                    packet = payment.checked_psbt()
                    try:
                        final = finalize_multisig(packet, txid)
                    except SigningError as exc:
                        raise WalletError(str(exc)) from exc
                    self._check_final_review(state.record, packet, final, payment.review())
                    # A scan can become stale while the owner reviews devices.
                    # Recheck the exact chosen coins before submitting anything.
                    primary = state.servers[chain]["explorer"]
                    verify_selected_outpoints(packet, chain, primary)
                    if CHAIN_CONFIGS[chain].checkpoint_height is not None:
                        verify_esplora(chain, broadcaster)
                    try:
                        sent = broadcast_transaction(
                            final["raw_transaction_hex"], chain, broadcaster,
                            mainnet_opt_in=(chain == "main"
                                            and data.get("mainnet_opt_in") is True),
                        )
                        if sent != txid:
                            raise BroadcastOutcomeUnknown(
                                "The server reported a different transaction ID. The result "
                                "is unknown. Do not send again; check an explorer first."
                            )
                    except BroadcastOutcomeUnknown:
                        # The network request may have succeeded before its response
                        # was lost. Retrying the reviewed payment is unsafe until a
                        # person independently checks the expected txid.
                        state.prepared = None
                        state.scan = None
                        state.pending_broadcast_txid = txid
                        state.pending_broadcast_unknown = True
                        state.pending_by_wallet[wallet_identity(state.record, chain)] = (txid, True)
                        raise
                    # The funds are spent now, so anything cached is stale.
                    state.prepared = None
                    state.scan = None
                    state.pending_broadcast_txid = sent
                    state.pending_broadcast_unknown = False
                    state.pending_by_wallet[wallet_identity(state.record, chain)] = (sent, False)
                    state.note("broadcast", "accepted")
                self._send(200, {
                    "txid": sent,
                    "explorer": CHAIN_CONFIGS[chain].web_url + "/tx/" + sent,
                })

            def _save(self, data):
                self._send(200, save_prepared_psbt(state, data.get("chain")))

            def _clear(self, data):
                """Discard the prepared, possibly signed, payment from this session.

                A signed-but-unbroadcast transaction is spend authority in its own
                right: anyone holding its bytes can submit them. Its lifetime in
                app state should therefore be something the operator ends
                deliberately rather than something they have to remember.
                """
                with state.lock:
                    if state.prepared is None:
                        raise WalletError("There is no prepared transaction to clear.")
                    if data.get("preparation_id") != state.prepared.review_id:
                        raise WalletError("Review the current transaction before clearing it.")
                    state.prepared = None
                    state.scan_generation += 1
                    state.note("final_transaction", "rejected")
                self._send(200, {"cleared": True})

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
                    raise WalletError("Select a supported network for server settings.")
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
                            state.prepared = None
                            state.scan_generation += 1
                with state.lock:
                    active = dict(state.servers[chain])
                    error = state.settings_error
                self._send(200, {
                    "chain": chain, "explorer_url": active["explorer"],
                    "broadcaster_url": active["broadcaster"],
                    "default_url": CHAIN_CONFIGS[chain].explorer_url,
                    "settings_error": error,
                })

            def _prepare(self, data):
                with state.lock:
                    state.prepared = None
                    record, scan, revision, chain = (
                        state.record, state.scan, state.revision, state.chain
                    )
                    if state.settings_error:
                        raise WalletError(state.settings_error)
                    explorer = state.servers[chain]["explorer"] if chain else None
                if record is None or scan is None:
                    raise WalletError("Open a wallet and refresh its balance before preparing an unsigned transaction.")
                if scan.get("pending_outgoing"):
                    raise WalletError("A payment from this wallet is waiting for one confirmation. Check again later before preparing another payment.")
                if data.get("chain") != chain:
                    raise WalletError("Selected network does not match the open wallet.")
                if scan.get("source") != explorer:
                    raise WalletError("Explorer changed since the balance scan; refresh before preparing.")
                if (explorer != CHAIN_CONFIGS[chain].explorer_url or
                    CHAIN_CONFIGS[chain].checkpoint_height is not None):
                    verify_esplora(chain, explorer)
                with state.lock:
                    mutinynet = chain == "mutinynet"
                    fee_value = state.mutinynet_fees if mutinynet else state.fees
                    fee_checked = (state.mutinynet_fees_checked if mutinynet
                                   else state.fees_checked)
                    fee_quote = (fee_value if fee_value is not None
                                 and time.monotonic() - fee_checked < FEES_CACHE_SECONDS else None)
                if fee_quote is None:
                    try:
                        fee_quote = (fetch_mutinynet_fee_rates() if mutinynet
                                     else fetch_fee_rates())
                    except WalletError as exc:
                        raise WalletError(
                            "Live network fee reference is unavailable; "
                            "no unsigned transaction file will be prepared."
                        ) from exc
                    with state.lock:
                        if mutinynet:
                            state.mutinynet_fees = fee_quote
                            state.mutinynet_fees_checked = time.monotonic()
                        else:
                            state.fees = fee_quote
                            state.fees_checked = time.monotonic()
                fee_source_name = "Mutinynet" if mutinynet else "mainnet"
                if fee_quote["standard"] > 25:
                    raise WalletError(
                        f"Current {fee_source_name} standard fee exceeds this app's 25 sat/vB "
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
                        f"{requested_rate} sat/vB is below the live {fee_source_name} economy "
                        f"reference of {fee_quote['economy']} sat/vB. Choose a current "
                        "suggestion or wait."
                    )
                result = build_unsigned_psbt(
                    record, scan, data.get("recipient"), data.get("amount_sats"),
                    requested_rate, base_url=explorer, send_all=data.get("send_all", False),
                )
                # Verify the selected historical outputs remain unspent. Only
                # their public transaction IDs go to a second mainnet provider.
                verify_selected_outpoints(result["psbt_base64"], chain, explorer)
                if requested_rate < fee_quote["standard"]:
                    low_warning = (
                        f"{requested_rate} sat/vB is below the current {fee_source_name} "
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
                    review = {
                        key: result[key] for key in (
                            "txid", "recipient", "amount_sats", "fee_sats",
                            "change_sats", "change_address", "send_all")
                    }
                    state.prepared = PreparedPayment.create(
                        record, chain, state.scan_generation, secrets.token_urlsafe(18),
                        result["psbt_base64"], review)
                    result["preparation_id"] = state.prepared.review_id
                    state.note("transaction_prepare", "passed")
                self._send(200, result)

        return Handler


def main():
    state = LocalApp()
    server = ThreadingHTTPServer(("127.0.0.1", 0), state.handler())
    port = server.server_address[1]
    # Printed without the token so it stays out of terminal scrollback and logs.
    display_url = f"http://127.0.0.1:{port}/"
    print("Bitcoin Easy Signer — local network-selected GUI")
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

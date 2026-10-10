"""End-to-end test of the real local HTTP API.

Drives the actual ThreadingHTTPServer and request handler over loopback — the
same code path the browser page uses — with a deterministic explorer and fee
feed substituted. No network access is required or performed.

This covers the journey the roadmap requires: import -> scan -> fee estimate ->
prepare -> reviewable unsigned PSBT, plus the access-control behaviour of the
local server itself.
"""

import base64
import contextlib
import io
import json
import re
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from embit import psbt
from embit.networks import NETWORKS

import gui
from fake_explorer import FakeExplorer, three_output_wallet
from probe import parse_bsms
from test_probe import test_record
from test_wallet_service import mainnet_record
from wallet_service import (
    build_unsigned_psbt as real_build,
    estimate_fee_preview as real_estimate,
    scan_wallet as real_scan,
    wallet_layout,
)

FEE_QUOTE = {
    "fastest": 8, "standard": 5, "hour": 2, "economy": 1, "minimum": 1,
    "checked_at": "2026-09-28T00:00:00+00:00", "network": "main",
    "source": "test fixture",
}
PRICE = {
    "usd_per_btc": 100_000.0, "as_of": "2026-09-28T00:00:00+00:00",
    "source": "test fixture",
}


class ApiTestCase(unittest.TestCase):
    """Shared harness: real server, deterministic data, no outbound traffic."""

    bsms_kwargs: dict = {"bsms_template": True}

    def bsms(self):
        """Overridable: returns (bsms_text, synthetic_signing_roots)."""
        return test_record(**self.bsms_kwargs)

    def setUp(self):
        self.text, self.roots = self.bsms()
        self.record = parse_bsms(self.text)
        self.layout = wallet_layout(self.record)
        self.explorer = three_output_wallet(self.layout, NETWORKS[self.record.network])
        self._patch()
        self.state = gui.LocalApp()
        self.token = self.state.token
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.state.handler())
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self._stop)

    def _stop(self):
        self.server.shutdown()
        self.server.server_close()

    def _patch(self):
        # Keep the settings file inside a temp directory. Without this, the
        # /api/settings write in test_stale_explorer_settings_invalidate_a_review
        # lands in the real ~/Library/Application Support/Easy Bitcoin Multisig/
        # settings.json: it silently resets a developer's own saved explorer
        # settings, and it makes the suite report a failure in any environment
        # where $HOME is not writable, which is not a code defect.
        settings_dir = tempfile.TemporaryDirectory()
        self.addCleanup(settings_dir.cleanup)
        settings_patch = patch(
            "network_settings.settings_path",
            return_value=Path(settings_dir.name) / "settings.json")
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        for target, value in (
            ("load_servers", gui.default_servers),
            ("scan_wallet", lambda record, base_url=None, chain=None:
             real_scan(record, self.explorer, chain=chain)),
            ("build_unsigned_psbt",
             lambda record, scan, recipient, amount, fee_rate=2, **kw:
                 real_build(record, scan, recipient, amount, fee_rate,
                            self.explorer, send_all=kw.get("send_all", False))),
            ("estimate_fee_preview",
             lambda record, scan, send_all, **kw:
                 real_estimate(record, scan, send_all, **kw)),
            ("fetch_fee_rates", lambda: FEE_QUOTE),
            ("fetch_btc_usd", lambda: PRICE),
            ("verify_selected_outpoints", lambda *_args: None),
            ("verify_esplora", lambda *_args: None),
        ):
            patcher = patch.object(gui, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    # ---------------------------------------------------------------- HTTP helpers
    def post(self, path, payload, token="__default__", origin=None):
        headers = {"Content-Type": "application/json"}
        if token == "__default__":
            token = self.token
        if token is not None:
            headers["X-Local-Token"] = token
        if origin is not None:
            headers["Origin"] = origin
        request = urllib.request.Request(
            self.base + path, data=json.dumps(payload).encode(), method="POST",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def get_page(self):
        with urllib.request.urlopen(self.base + "/", timeout=15) as response:
            return response.status, response.read().decode()

    def import_wallet(self, chain="testnet4"):
        return self.post("/api/import", {
            "chain": chain, "consent_explorer": True, "text": self.text,
        })


class LocalServerAccessTests(ApiTestCase):
    def test_page_never_contains_the_access_token(self):
        status, page = self.get_page()
        self.assertEqual(status, 200)
        self.assertNotIn(self.token, page)
        self.assertNotIn("__LOCAL_TOKEN__", page)
        # The token is delivered out-of-band in the fragment instead.
        self.assertIn("location.hash", page)
        self.assertTrue(gui.launch_url(self.port, self.token).endswith(f"#token={self.token}"))

    def test_api_requires_the_token(self):
        self.assertEqual(self.post("/api/status", {}, token=None)[0], 403)
        self.assertEqual(self.post("/api/status", {}, token="wrong")[0], 403)
        self.assertEqual(self.post("/api/status", {})[0], 200)

    def test_foreign_origin_is_rejected(self):
        status, body = self.post("/api/status", {}, origin="http://evil.example")
        self.assertEqual(status, 403)
        self.assertIn("Local access only", body["error"])

    def _raw_token_request(self, token_bytes):
        """One hand-built POST, so the header can carry bytes urllib cannot.

        `urllib` encodes a `str` header as latin-1, so a hostile header has to
        be written to the socket by hand to reach the handler as raw bytes.
        """
        request = (
            b"POST /api/status HTTP/1.1\r\n"
            b"Host: 127.0.0.1:" + str(self.port).encode() + b"\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 2\r\n"
            b"Connection: close\r\n"
            b"X-Local-Token: " + token_bytes + b"\r\n"
            b"\r\n{}"
        )
        with socket.create_connection(("127.0.0.1", self.port), timeout=15) as sock:
            sock.sendall(request)
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        return b"".join(chunks)

    def test_a_non_ascii_token_header_is_refused_without_a_traceback(self):
        """CT-81: a hostile header is a wrong token, not a dying connection.

        `hmac.compare_digest` raises TypeError when either `str` argument holds
        a non-ASCII character, and the header arrives decoded as latin-1, so the
        connection used to die with a traceback on stderr instead of returning
        the ordinary 403.
        """
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            response = self._raw_token_request(b"\xff\xfe\x80")
        self.assertTrue(response.startswith(b"HTTP/1.0 403"), response)
        self.assertIn(b"Local access only", response)
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(self.post("/api/status", {})[0], 200)

    def test_wrong_host_header_is_rejected(self):
        request = urllib.request.Request(
            self.base + "/api/status", data=b"{}", method="POST",
            headers={"Content-Type": "application/json", "X-Local-Token": self.token,
                     "Host": "localhost:%d" % self.port},
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=15)
        self.assertEqual(caught.exception.code, 403)


class StalledConnectionTests(ApiTestCase):
    """CT-85: a request that stalls mid-body must not keep its thread.

    `ThreadingHTTPServer` gives every accepted connection a thread and nothing
    armed the socket with a timeout, so a client that announced a body and never
    sent it held a thread -- and its file descriptor -- until the process
    exited. The handler now arms the connection with `CONNECTION_TIMEOUT_SECONDS`;
    a stalled read ends the connection with no response at all (writing one would
    wait on the same client) and the server keeps serving.
    """

    def setUp(self):
        # The shipping budget is 15 s; these tests build the same server from a
        # fraction of it, so the constant -> handler class -> socket wiring is
        # exercised. Setting the handler's `timeout` attribute directly after the
        # fact would keep these tests green even if the constant stopped
        # reaching the handler at all.
        budget = patch.object(gui, "CONNECTION_TIMEOUT_SECONDS", 0.5)
        budget.start()
        self.addCleanup(budget.stop)
        super().setUp()

    def _stall(self, count, token, length=4096):
        """Open `count` connections that promise a body and never finish it."""
        stalled = []
        for _ in range(count):
            sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
            sock.sendall(
                b"POST /api/status HTTP/1.1\r\n"
                + b"Host: 127.0.0.1:%d\r\n" % self.port
                + b"Content-Type: application/json\r\n"
                + b"X-Local-Token: " + token + b"\r\n"
                + b"Content-Length: %d\r\n\r\n" % length
                + b'{"stalled":')  # promised, never finished
            stalled.append(sock)
        return stalled

    def _assert_cut_off(self, stalled):
        try:
            for index, sock in enumerate(stalled):
                sock.settimeout(5)
                # An empty read is the server closing the connection. A 500, a
                # 403 or any other reply would arrive here as bytes instead.
                self.assertEqual(sock.recv(64), b"",
                                 f"stalled connection {index} was not cut off")
        finally:
            for sock in stalled:
                sock.close()

    def test_stalled_bodies_are_cut_off_and_the_server_keeps_serving(self):
        stalled = self._stall(8, self.token.encode())
        self._assert_cut_off(stalled)
        status, body = self.post("/api/status", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["chain"], self.state.chain)

    def test_a_refused_request_with_a_stalled_body_is_cut_off_too(self):
        # A declaration one byte past the cap is refused, and the body is
        # drained first so the refusal is not lost to a reset. That drain runs
        # inside do_POST's own exception guard, so a timeout that escaped it
        # would be answered with a 500; the connection must simply close.
        stalled = self._stall(4, self.token.encode(),
                              length=gui.MAX_REQUEST_BYTES + 1)
        self._assert_cut_off(stalled)


class LocalTokenComparisonTests(ApiTestCase):
    """CT-82: the token is compared whole, in constant time, and never by prefix.

    `tests/test_gui_integration.py` pinned only that a wrong token is refused.
    A comparison that accepted any prefix -- `state.token.startswith(header)` or
    a last-six-characters test -- stayed green under that pin, so the matrix
    below walks every near miss and the shape pin holds the primitive.
    """

    def test_every_near_miss_of_the_token_is_refused(self):
        token = self.token
        substitution = ("0" if token[0] != "0" else "1") + token[1:]
        cases = {
            "no header at all": None,
            "empty value": "",
            "one character short": token[:-1],
            "one character long": token + "x",
            "first six characters": token[:6],
            "last six characters": token[-6:],
            "third through last": token[2:],
            "everything but the first": token[1:],
            "everything but the last": token[:-1],
            "one character substituted": substitution,
            "doubled": token * 2,
        }
        # A surrounding space is not a near miss worth asserting: `http.client`
        # refuses a value containing a newline outright, and both client and
        # parser strip surrounding whitespace, so " token" reaches the handler
        # as the token itself. That is HTTP, not a weakened comparison.
        for name, value in cases.items():
            with self.subTest(name):
                self.assertEqual(self.post("/api/status", {}, token=value)[0], 403, name)
        self.assertEqual(self.post("/api/status", {}, token=token)[0], 200)

    def test_the_comparison_is_whole_value_and_constant_time(self):
        """Pin the primitive: a weakened comparison is what the matrix exposes."""
        source = Path(gui.__file__).read_text(encoding="utf-8")
        self.assertIn(
            'candidate = (self.headers.get("X-Local-Token") or "").encode("utf-8")',
            source,
        )
        self.assertIn('expected = state.token.encode("utf-8")', source)
        self.assertIn("return hmac.compare_digest(candidate, expected)", source)
        for weakened in ("state.token.startswith", "state.token.endswith",
                         "in state.token", "state.token in "):
            self.assertNotIn(weakened, source,
                             f"the token comparison was weakened to {weakened!r}")


class TransactionJourneyTests(ApiTestCase):
    def test_mutinynet_uses_same_builder_with_distinct_network_selection(self):
        self.state.mutinynet_fees = {**FEE_QUOTE, "network": "mutinynet"}
        self.state.mutinynet_fees_checked = time.monotonic()
        with patch.object(gui, "verify_esplora") as verify:
            status, wallet = self.import_wallet("mutinynet")
            self.assertEqual(status, 200)
            self.assertEqual(wallet["network"], "mutinynet")
            status, scan = self.post("/api/scan", {"chain": "mutinynet"})
            self.assertEqual(status, 200)
            self.assertEqual(scan["network"], "mutinynet")
            recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
            status, prepared = self.post("/api/prepare", {
                "chain": "mutinynet", "recipient": recipient,
                "amount_sats": 100_000, "send_all": False, "fee_rate": 5,
            })
            self.assertEqual(status, 200, prepared)
            self.assertEqual(prepared["network"], "mutinynet")
            self.assertEqual(psbt.PSBT.from_base64(prepared["psbt_base64"]).tx.txid().hex(),
                             prepared["txid"])
            verify.assert_any_call("mutinynet", "https://mutinynet.com/api")

    def test_scan_of_the_built_in_explorer_still_checks_its_genesis(self):
        """CT-20: the default URL is not exempt from seeing its own genesis.

        Before the fix, a scan against the built-in testnet4/main URL skipped
        verify_esplora entirely. Remove the unconditional call and this test
        goes red.
        """
        self.import_wallet()
        with patch.object(gui, "verify_esplora") as verify:
            status, scan = self.post("/api/scan", {"chain": "testnet4"})
        self.assertEqual(status, 200)
        verify.assert_called_once_with(
            "testnet4", gui.CHAIN_CONFIGS["testnet4"].explorer_url)

    def test_outpoint_check_can_stop_preparation_after_scan(self):
        self.import_wallet()
        self.post("/api/scan", {"chain": "testnet4"})
        recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
        with patch.object(gui, "verify_selected_outpoints",
                          side_effect=gui.WalletError("A selected output was spent.")):
            status, body = self.post("/api/prepare", {
                "chain": "testnet4", "recipient": recipient,
                "amount_sats": 100_000, "send_all": False, "fee_rate": 5,
            })
        self.assertEqual(status, 400)
        self.assertIn("spent", body["error"])
        self.assertIsNone(self.state.prepared)

    def test_receive_only_wallet_reaches_the_send_form_with_a_plain_note(self):
        """The ordinary Nunchuk BSMS opens the standard custom-amount flow."""
        text, _ = test_record(short_path=True)
        status, summary = self.post("/api/import", {
            "chain": "testnet4", "text": text, "consent_explorer": True})
        self.assertEqual(status, 200)
        self.assertTrue(summary["can_prepare"])
        self.assertTrue(summary["can_send_all"])
        self.assertTrue(summary["change_assumed"])
        self.assertIn("standard change path", summary["change_note"])
        self.assertIn("file does not state that path", summary["change_note"])

    def test_nunchuk_shape_prepares_custom_amount_with_one_file(self):
        text, _ = test_record(short_path=True)
        status, summary = self.post("/api/import", {
            "chain": "mutinynet", "text": text, "consent_explorer": True})
        self.assertEqual(status, 200)
        self.assertTrue(summary["can_prepare"])
        self.assertIn({"stage": "change_path", "outcome": "standard"},
                      [{"stage": item["stage"], "outcome": item["outcome"]}
                       for item in self.state.diagnostic_events])
        status, balance = self.post("/api/scan", {"chain": "mutinynet"})
        self.assertEqual(status, 200)
        self.assertFalse(balance["coverage_limited"])
        recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
        status, preview = self.post("/api/estimate", {
            "chain": "mutinynet", "send_all": False, "amount_sats": 10_000,
            "fee_rate": 2, "recipient": recipient,
        })
        self.assertEqual(status, 200)
        status, prepared = self.post("/api/prepare", {
            "chain": "mutinynet", "recipient": recipient,
            "amount_sats": 10_000, "send_all": False, "fee_rate": 2,
        })
        self.assertEqual(status, 200)
        self.assertGreater(prepared["change_sats"], 0)

    def test_wallet_reaches_a_reviewable_psbt(self):
        status, summary = self.import_wallet()
        self.assertEqual(status, 200)
        self.assertTrue(summary["can_prepare"])
        self.assertFalse(summary["change_assumed"])

        status, scan = self.post("/api/scan", {"chain": "testnet4"})
        self.assertEqual(status, 200)
        self.assertEqual(scan["confirmed_sats"], 175_000)
        self.assertTrue(scan["utxo_consistent"])
        self.assertFalse(scan["coverage_limited"])

        recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
        amount = 100_000
        status, preview = self.post("/api/estimate", {
            "chain": "testnet4", "send_all": False, "amount_sats": amount,
            "fee_rate": 5, "recipient": recipient,
        })
        self.assertEqual(status, 200)

        status, prepared = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": recipient, "amount_sats": amount,
            "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 200)
        # The previewed size must equal what was actually built.
        self.assertEqual(preview["estimated_vbytes"], prepared["estimated_signed_vbytes"])
        self.assertEqual(preview["input_count"], prepared["inputs"])
        self.assertEqual(prepared["fee_sats"], prepared["estimated_signed_vbytes"] * 5)
        self.assertEqual(prepared["amount_sats"], amount)
        self.assertFalse(prepared["change_assumed"])
        self.assertIn("Unsigned only", prepared["change_warning"])
        self.assertTrue(prepared["preparation_id"])

        packet = psbt.PSBT.from_base64(prepared["psbt_base64"])
        self.assertEqual(packet.tx.vout[0].value, amount)
        self.assertEqual(packet.tx.vout[1].value, prepared["change_sats"])
        self.assertEqual(packet.fee(), prepared["fee_sats"])
        self.assertEqual(packet.inputs[0].partial_sigs, {})
        # Change must land on the confirmed change branch, never the recipient.
        self.assertEqual(
            packet.tx.vout[1].script_pubkey.address(NETWORKS["test"]),
            self.layout.change.derive(0).address(NETWORKS["test"]),
        )

    def test_send_all_deducts_the_fee_through_the_api(self):
        self.import_wallet()
        self.post("/api/scan", {"chain": "testnet4"})
        recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
        status, sweep = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": recipient, "amount_sats": None,
            "send_all": True, "fee_rate": 5,
        })
        self.assertEqual(status, 200)
        packet = psbt.PSBT.from_base64(sweep["psbt_base64"])
        self.assertEqual(len(packet.tx.vout), 1)
        self.assertEqual(sweep["amount_sats"], 175_000 - sweep["fee_sats"])
        self.assertEqual(sweep["total_spend_sats"], 175_000)
        self.assertEqual(sweep["remaining_confirmed_sats"], 0)
        self.assertEqual(sweep["change_sats"], 0)
        self.assertEqual(packet.fee(), sweep["fee_sats"])

    def test_saving_writes_the_prepared_psbt_where_the_user_can_find_it(self):
        """The save the user clicks must produce a real file, over the same API
        every other action uses (the pywebview bridge is not always available)."""
        self.import_wallet()
        self.post("/api/scan", {"chain": "testnet4"})
        recipient = self.layout.receive.derive(5).address(NETWORKS["test"])
        status, prepared = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": recipient, "amount_sats": 1_000,
            "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 200)

        home = Path(tempfile.mkdtemp())
        (home / "Downloads").mkdir()
        with patch("gui.Path.home", return_value=home):
            status, body = self.post("/api/save", {"chain": "testnet4"})
        self.assertEqual(status, 200)
        self.assertTrue(body["saved"])
        saved = Path(body["path"])
        self.assertEqual(saved.parent, home / "Downloads")
        self.assertEqual(saved.name, "testnet4-unsigned.psbt")
        self.assertEqual(saved.read_bytes(), base64.b64decode(prepared["psbt_base64"]))
        # The file must be a real, parseable PSBT.
        self.assertEqual(psbt.PSBT.parse(saved.read_bytes()).tx.vout[0].value, 1_000)

        # A second save must not overwrite the first transaction.
        with patch("gui.Path.home", return_value=home):
            _, second = self.post("/api/save", {"chain": "testnet4"})
        self.assertEqual(Path(second["path"]).name, "testnet4-unsigned-2.psbt")

        # Refuse a mismatched network, and refuse when nothing is prepared.
        self.assertEqual(self.post("/api/save", {"chain": "main"})[0], 400)
        self.state.prepared = None
        status, body = self.post("/api/save", {"chain": "testnet4"})
        self.assertEqual(status, 400)
        self.assertIn("Prepare and review", body["error"])

    def test_prepare_is_refused_before_a_scan(self):
        self.import_wallet()
        status, body = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": self.layout.receive.derive(5).address(NETWORKS["test"]),
            "amount_sats": 1_000, "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 400)
        self.assertIn("refresh", body["error"].lower())

    def test_stale_explorer_settings_invalidate_a_review(self):
        self.import_wallet()
        self.post("/api/scan", {"chain": "testnet4"})
        status, _ = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": self.layout.receive.derive(5).address(NETWORKS["test"]),
            "amount_sats": 1_000, "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 200)
        self.assertIsNotNone(self.state.prepared)
        # Changing the explorer for this chain must drop the prepared PSBT.
        self.post("/api/settings", {"chain": "testnet4", "action": "reset"})
        self.assertIsNone(self.state.prepared)

    def test_security_headers_accompany_the_page(self):
        """The loopback API's hardening headers are part of the trust boundary.

        These are defence in depth rather than an injection fix, but a money
        application should not lose them silently to a refactor of the handler.
        """
        with urllib.request.urlopen(self.base + "/", timeout=15) as response:
            headers = response.headers
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["Cache-Control"], "no-store")
        policy = headers["Content-Security-Policy"]
        self.assertIn("default-src 'none'", policy)
        self.assertIn("connect-src 'self'", policy)
        self.assertIn("base-uri 'none'", policy)
        self.assertIn("form-action 'none'", policy)
        self.assertIn("frame-ancestors 'none'", policy)

    def test_the_page_never_echoes_the_access_token(self):
        """The token travels in the URL fragment, so it must not be in the body."""
        _status, page = self.get_page()
        self.assertNotIn(self.token, page)
        self.assertNotIn("__LOCAL_TOKEN__", page)

    def test_the_inline_script_needs_a_nonce_not_unsafe_inline(self):
        """script-src must not permit arbitrary inline script.

        The page is the only document this server has and it is rebuilt for every
        request, so a fresh nonce costs nothing. Without it an injected, or
        future, inline script would inherit the allowance.
        """
        with urllib.request.urlopen(self.base + "/", timeout=15) as response:
            policy = response.headers["Content-Security-Policy"]
            page = response.read().decode("utf-8")
        script_src = policy.split("script-src", 1)[1].split(";", 1)[0]
        self.assertNotIn("unsafe-inline", script_src)
        match = re.search(r"'nonce-([A-Za-z0-9_-]+)'", script_src)
        self.assertIsNotNone(match, f"no nonce in {script_src!r}")
        self.assertIn(f'<script nonce="{match.group(1)}">', page)

    def test_every_page_load_uses_a_fresh_nonce(self):
        nonces = set()
        for _ in range(3):
            with urllib.request.urlopen(self.base + "/", timeout=15) as response:
                policy = response.headers["Content-Security-Policy"]
            nonces.add(re.search(r"'nonce-([A-Za-z0-9_-]+)'", policy).group(1))
        self.assertEqual(len(nonces), 3, "the nonce must not be reused")

    def test_the_page_requires_its_own_sweep_acknowledgement_and_names_the_gap(self):
        """Send All moves everything the scan found, and the scan stops at a gap.

        The generic review checkbox does not mention either, so a sweep needs a
        control that does, and the operator needs the number.
        """
        _status, page = self.get_page()
        # Assert each mention of the gap distinctly: both the sweep row and the
        # coverage line say "20 consecutive unused addresses", so a single loose
        # assertion would pass with either one deleted.
        self.assertIn('id="confirm-sweep"', page)
        self.assertIn("This sweep sends", page)
        self.assertIn("Balance from a standard gap scan: it stops after 20 "
                      "consecutive unused addresses", page)

    def test_clearing_a_prepared_payment_discards_it(self):
        """A signed-but-unbroadcast transaction is spend authority.

        Ending its life in app state should be a deliberate action, so the
        endpoint must clear the payment and refuse to be replayed.
        """
        self.import_wallet()
        self.post("/api/scan", {"chain": "testnet4"})
        _status, prepared = self.post("/api/prepare", {
            "chain": "testnet4",
            "recipient": self.layout.receive.derive(5).address(NETWORKS["test"]),
            "amount_sats": 1_000, "send_all": False, "fee_rate": 5,
        })
        self.assertIsNotNone(self.state.prepared)

        # A stale or guessed id must not clear somebody else's review.
        status, body = self.post("/api/clear", {"preparation_id": "not-the-review"})
        self.assertEqual(status, 400)
        self.assertIn("Review the current transaction", body["error"])
        self.assertIsNotNone(self.state.prepared)

        status, body = self.post("/api/clear",
                                 {"preparation_id": prepared["preparation_id"]})
        self.assertEqual(status, 200)
        self.assertTrue(body["cleared"])
        self.assertIsNone(self.state.prepared)
        # Clearing twice is a refusal, not a silent success.
        self.assertEqual(self.post("/api/clear",
                                   {"preparation_id": prepared["preparation_id"]})[0], 400)

    def test_every_element_the_page_script_reaches_for_actually_exists(self):
        """A $("id") with no matching element throws at the worst moment.

        That is the dangerous shape of this bug: a handler does something
        irreversible, then touches a node that is not there, and the operator is
        left with a half-updated screen or none at all. Static, cheap, and it
        covers every handler rather than the ones with tests.
        """
        _status, page = self.get_page()
        # Match the tag generically: the served page carries a per-response nonce,
        # so it is "<script nonce=...>" rather than a bare "<script>".
        found = re.search(r"<script\b[^>]*>(.*?)</script>", page, re.S)
        self.assertIsNotNone(found, "the served page must carry its script")
        script = found.group(1)
        markup = page[:found.start()] + page[found.end():]
        referenced = set(re.findall(r'\$\("([^"]+)"\)', script))
        declared = set(re.findall(r'id="([^"]+)"', markup))
        self.assertGreater(len(referenced), 20, "expected the script to look up elements")
        self.assertEqual(
            sorted(referenced - declared), [],
            "the page script looks up elements the markup never declares")

    def test_a_rejected_money_action_is_attributed_and_chatter_is_not_recorded(self):
        """A refused signature must not look like a refused fee estimate.

        Until 0.4.8 every rejection was recorded as an unattributable "request",
        because the route name and the stage name never matched: a refused
        signature was indistinguishable from a refused fee estimate.
        """
        # No wallet is open, so a fee estimate is refused. That is ordinary
        # interface feedback, produced by typing an amount, and it must not
        # occupy the 80-event buffer at all.
        status, _body = self.post("/api/estimate", {"chain": "mutinynet",
                                                    "send_all": False,
                                                    "amount_sats": 1000})
        self.assertEqual(status, 400)
        self.assertEqual(self.state.diagnostic_events, [],
                         "convenience-call rejections must not be recorded")

        # A refused signing request is a money stage and must name itself.
        status, _body = self.post("/api/sign", {"preparation_id": "not-a-review",
                                                "device_type": "jade",
                                                "device_path": "/dev/x"})
        self.assertEqual(status, 400)
        self.assertEqual(
            [(event["stage"], event["outcome"]) for event in self.state.diagnostic_events],
            [("signer_response", "rejected")],
            "a refused signature must be attributed to the signing stage")


class LargeAmountGateTests(ApiTestCase):
    """The high-value confirmation must not depend on a remote price feed."""

    def bsms(self):
        return mainnet_record(), []

    def setUp(self):
        super().setUp()
        self.explorer = FakeExplorer(self.layout, NETWORKS["main"], [
            (self.layout.receive.derive(0).address(NETWORKS["main"]), 50_000_000,
             "receive", 0),
        ])

    def test_low_price_feed_cannot_suppress_the_high_value_confirmation(self):
        # A lying or broken price feed reports a tiny BTC price.
        patcher = patch.object(gui, "fetch_btc_usd", lambda: {**PRICE, "usd_per_btc": 1.0})
        patcher.start()
        self.addCleanup(patcher.stop)

        status, summary = self.import_wallet(chain="main")
        self.assertEqual(status, 200)
        self.assertTrue(summary["can_prepare"])
        status, scan = self.post("/api/scan", {"chain": "main"})
        self.assertEqual(status, 200)
        self.assertEqual(scan["confirmed_sats"], 50_000_000)

        recipient = self.layout.receive.derive(1).address(NETWORKS["main"])
        payload = {"chain": "main", "recipient": recipient, "amount_sats": 20_000_000,
                   "send_all": False, "fee_rate": 2}
        status, body = self.post("/api/prepare", payload)
        self.assertEqual(status, 400)
        self.assertIn("large mainnet payment", body["error"])

        # With the explicit acknowledgement it proceeds.
        status, prepared = self.post("/api/prepare", {**payload, "large_amount_confirmed": True})
        self.assertEqual(status, 200)
        self.assertEqual(prepared["amount_sats"], 20_000_000)

    def test_a_lying_low_price_cannot_hide_a_large_payment_under_one_bitcoin(self):
        """CT-30: 0.05 BTC is large whenever BTC is near $200k; $1 must not hide it."""
        patcher = patch.object(gui, "fetch_btc_usd", lambda: {**PRICE, "usd_per_btc": 1.0})
        patcher.start()
        self.addCleanup(patcher.stop)

        status, summary = self.import_wallet(chain="main")
        self.assertEqual(status, 200)
        status, scan = self.post("/api/scan", {"chain": "main"})
        self.assertEqual(status, 200)

        recipient = self.layout.receive.derive(1).address(NETWORKS["main"])
        payload = {"chain": "main", "recipient": recipient, "amount_sats": 5_000_000,
                   "send_all": False, "fee_rate": 2}
        status, body = self.post("/api/prepare", payload)
        self.assertEqual(status, 400)
        self.assertIn("large mainnet payment", body["error"])

        status, prepared = self.post("/api/prepare", {**payload, "large_amount_confirmed": True})
        self.assertEqual(status, 200)
        self.assertEqual(prepared["amount_sats"], 5_000_000)

    def test_below_the_floor_does_not_require_the_extra_confirmation(self):
        self.import_wallet(chain="main")
        self.post("/api/scan", {"chain": "main"})
        status, body = self.post("/api/prepare", {
            "chain": "main", "recipient": self.layout.receive.derive(1).address(NETWORKS["main"]),
            "amount_sats": 1_000_000, "send_all": False, "fee_rate": 2,
        })
        self.assertEqual(status, 200, body)


if __name__ == "__main__":
    unittest.main()

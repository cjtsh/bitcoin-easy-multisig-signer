"""End-to-end test of the real local HTTP API.

Drives the actual ThreadingHTTPServer and request handler over loopback — the
same code path the browser page uses — with a deterministic explorer and fee
feed substituted. No network access is required or performed.

This covers the journey the roadmap requires: import -> scan -> fee estimate ->
prepare -> reviewable unsigned PSBT, plus the access-control behaviour of the
local server itself.
"""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
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

    bsms_kwargs: dict = {"short_path": True}

    def bsms(self):
        """Overridable: returns (bsms_text, synthetic_signing_roots)."""
        return test_record(**self.bsms_kwargs)

    def setUp(self):
        self.text, self.roots = self.bsms()
        self.state = gui.LocalApp()
        self.token = self.state.token
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.state.handler())
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self._stop)
        self.record = parse_bsms(self.text, declared_change=True)
        self.layout = wallet_layout(self.record)
        self.explorer = three_output_wallet(self.layout, NETWORKS[self.record.network])
        self._patch()

    def _stop(self):
        self.server.shutdown()
        self.server.server_close()

    def _patch(self):
        for target, value in (
            ("load_servers", gui.default_servers),
            ("scan_wallet", lambda record, base_url=None: real_scan(record, self.explorer)),
            ("build_unsigned_psbt",
             lambda record, scan, recipient, amount, fee_rate=2, **kw:
                 real_build(record, scan, recipient, amount, fee_rate,
                            self.explorer, send_all=kw.get("send_all", False))),
            ("estimate_fee_preview",
             lambda record, scan, send_all, **kw:
                 real_estimate(record, scan, send_all, **kw)),
            ("fetch_fee_rates", lambda: FEE_QUOTE),
            ("fetch_btc_usd", lambda: PRICE),
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

    def import_wallet(self, declared_change=False, chain="testnet4"):
        return self.post("/api/import", {
            "chain": chain, "consent_explorer": True, "text": self.text,
            "declared_change": declared_change,
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

    def test_wrong_host_header_is_rejected(self):
        request = urllib.request.Request(
            self.base + "/api/status", data=b"{}", method="POST",
            headers={"Content-Type": "application/json", "X-Local-Token": self.token,
                     "Host": "localhost:%d" % self.port},
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=15)
        self.assertEqual(caught.exception.code, 403)


class TransactionJourneyTests(ApiTestCase):
    def test_undeclared_change_wallet_explains_and_is_declarable(self):
        status, summary = self.import_wallet(declared_change=False)
        self.assertEqual(status, 200)
        self.assertFalse(summary["can_prepare"])
        self.assertTrue(summary["can_declare_change"])
        self.assertFalse(summary["change_declared"])
        # The reason is shown to the user and points at the available action.
        self.assertIn("change", summary["prepare_reason"].lower())
        self.assertIn("change branch below", summary["prepare_reason"])

    def test_declared_change_wallet_reaches_a_reviewable_psbt(self):
        status, summary = self.import_wallet(declared_change=True)
        self.assertEqual(status, 200)
        self.assertTrue(summary["can_prepare"])
        self.assertTrue(summary["change_declared"])
        self.assertFalse(summary["can_declare_change"])

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
        self.assertTrue(prepared["change_declared"])
        self.assertIn("enabled by your own confirmation", prepared["change_warning"])
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
        self.import_wallet(declared_change=True)
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

    def test_prepare_is_refused_before_a_scan(self):
        self.import_wallet(declared_change=True)
        status, body = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": self.layout.receive.derive(5).address(NETWORKS["test"]),
            "amount_sats": 1_000, "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 400)
        self.assertIn("refresh", body["error"].lower())

    def test_stale_explorer_settings_invalidate_a_review(self):
        self.import_wallet(declared_change=True)
        self.post("/api/scan", {"chain": "testnet4"})
        status, _ = self.post("/api/prepare", {
            "chain": "testnet4", "recipient": self.layout.receive.derive(5).address(NETWORKS["test"]),
            "amount_sats": 1_000, "send_all": False, "fee_rate": 5,
        })
        self.assertEqual(status, 200)
        self.assertIsNotNone(self.state.prepared_psbt)
        # Changing the explorer for this chain must drop the prepared PSBT.
        self.post("/api/settings", {"chain": "testnet4", "action": "reset"})
        self.assertIsNone(self.state.prepared_psbt)
        self.assertIsNone(self.state.prepared_id)


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

        status, summary = self.import_wallet(declared_change=True, chain="main")
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

    def test_below_the_floor_does_not_require_the_extra_confirmation(self):
        self.import_wallet(declared_change=True, chain="main")
        self.post("/api/scan", {"chain": "main"})
        status, body = self.post("/api/prepare", {
            "chain": "main", "recipient": self.layout.receive.derive(1).address(NETWORKS["main"]),
            "amount_sats": 1_000_000, "send_all": False, "fee_rate": 2,
        })
        self.assertEqual(status, 200, body)


if __name__ == "__main__":
    unittest.main()

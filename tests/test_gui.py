"""Exercise the local browser API without a network or real wallet file."""

import json
import io
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from gui import LocalApp, fetch_btc_usd, fetch_fee_rates
from version import APP_VERSION
from wallet_service import WalletError
from test_probe import test_record
from test_wallet_service import mainnet_record


class LocalGuiTests(unittest.TestCase):
    def setUp(self):
        self.settings_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.settings_dir.cleanup)
        self.settings_patch = patch("network_settings.settings_path",
                                    return_value=Path(self.settings_dir.name) / "settings.json")
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.app = LocalApp()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.app.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def post(self, route, data, token=None, origin=None):
        headers = {"Content-Type": "application/json",
                   "X-Local-Token": self.app.token if token is None else token}
        if origin is not None:
            headers["Origin"] = origin
        request = Request(self.base + route, data=json.dumps(data).encode(),
                          headers=headers, method="POST")
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_file_picker_page_imports_synthetic_public_wallet(self):
        with urlopen(self.base, timeout=3) as response:
            page = response.read().decode()
        self.assertIn('type="file"', page)
        self.assertIn("Testnet4", page)
        self.assertIn('id="balance-usd"', page)
        self.assertIn('id="observed-btc"', page)
        self.assertLess(page.index('id="observed-btc"'), page.index('id="observed"'))
        self.assertIn('setText("observed-btc", btc(data.observed_sats))', page)
        self.assertIn('id="send-equivalent"', page)
        self.assertIn('class="context-help"', page)
        self.assertGreaterEqual(page.count('class="help-popout"'), 6)
        self.assertIn('aria-label="What am I saving as a PSBT file?"', page)
        self.assertIn("PSBT means Partially Signed Bitcoin Transaction.", page)
        self.assertIn("Preparing it does not move Bitcoin.", page)
        self.assertIn("Download unsigned transaction file (.psbt)", page)
        self.assertIn("Apple Silicon (M-series) only. Intel-based Macs are not supported.", page)
        self.assertIn('id="send-all" type="checkbox" checked', page)
        self.assertIn('id="copy-balance"', page)
        self.assertIn('id="confirmed-btc" type="text" readonly', page)
        self.assertIn('id="amount" type="text" inputmode="decimal"', page)
        self.assertIn('send_all:sendAll', page)
        self.assertIn('id="review-amount-sats"', page)
        self.assertIn('id="review-remaining"', page)
        self.assertIn("Other wallet addresses beyond the scan gap may still hold funds.", page)
        self.assertIn("sats at this address", page)
        self.assertIn('value="testnet4"', page)
        self.assertIn('value="main"', page)
        self.assertIn('id="refresh-top"', page)
        self.assertIn("LIVE BITCOIN NETWORK · REAL FUNDS", page)
        self.assertIn("body.live-mode", page)
        self.assertNotIn("__LOCAL_TOKEN__", page)
        self.assertIn("v" + APP_VERSION, page)
        self.assertNotIn("__APP_VERSION__", page)
        text, _ = test_record(short_path=True)
        result = self.post("/api/import", {"chain": "testnet4", "text": text,
                                           "consent_explorer": True})
        self.assertEqual(len(result["keys"]), 3)
        self.assertTrue(result["receive_address"].startswith("tb1"))
        self.assertIsNotNone(self.app.record)
        self.assertIsNone(self.app.scan)

    def test_import_rejects_bad_chain_and_cross_origin_post(self):
        text, _ = test_record()
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "testnet4", "text": text})
        self.assertEqual(err.exception.code, 400)
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "test", "text": text})
        self.assertEqual(err.exception.code, 400)
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "testnet4", "text": text},
                      origin="https://not-local.example")
        self.assertEqual(err.exception.code, 403)
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "testnet4", "text": text},
                      token="wrong-token")
        self.assertEqual(err.exception.code, 403)

    def test_gui_scan_returns_balance_and_does_not_store_file_on_disk(self):
        text, _ = test_record()
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        fake = {
            "network": "testnet4", "utxo_consistent": True,
            "confirmed_sats": 6000, "pending_delta_sats": 0, "observed_sats": 6000,
            "addresses": [], "utxos": [], "scanned": 40, "coverage_limited": False,
            "path_warning": "", "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": "https://mempool.space/testnet4/api",
        }
        with patch("gui.scan_wallet", return_value=fake):
            result = self.post("/api/scan", {"chain": "testnet4"})
        self.assertEqual(result["confirmed_sats"], 6000)
        self.assertEqual(result["utxo_count"], 0)
        self.assertEqual(self.app.scan, fake)

    def test_refresh_twice_uses_same_in_memory_wallet_definition(self):
        text, _ = test_record()
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        record = self.app.record
        base = {
            "network": "testnet4", "utxo_consistent": True,
            "confirmed_sats": 0, "pending_delta_sats": 6000,
            "observed_sats": 6000, "addresses": [], "utxos": [],
            "scanned": 50, "coverage_limited": False,
            "path_warning": "", "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": "https://mempool.space/testnet4/api",
        }
        with patch("gui.scan_wallet", side_effect=[
            base, {**base, "pending_delta_sats": 11_000, "observed_sats": 11_000}
        ]) as scan:
            first = self.post("/api/scan", {"chain": "testnet4"})
            second = self.post("/api/scan", {"chain": "testnet4"})
        self.assertEqual((first["observed_sats"], second["observed_sats"]), (6000, 11_000))
        self.assertIs(self.app.record, record)
        self.assertEqual(scan.call_count, 2)

    def test_mainnet_consent_network_binding_and_restore_after_page_reload(self):
        text = mainnet_record()
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "main", "text": text})
        self.assertEqual(err.exception.code, 400)
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "testnet4", "text": text})
        self.assertEqual(err.exception.code, 400)
        result = self.post("/api/import", {"chain": "main", "text": text,
                                           "consent_explorer": True})
        self.assertTrue(result["can_prepare"])
        self.assertEqual(result["network"], "main")
        fake = {
            "network": "main", "utxo_consistent": True,
            "confirmed_sats": 100_000, "pending_delta_sats": 0, "observed_sats": 100_000,
            "addresses": [], "utxos": [], "scanned": 40, "coverage_limited": False,
            "path_warning": "", "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": "https://mempool.space/api",
        }
        with self.assertRaises(HTTPError) as err:
            self.post("/api/scan", {"chain": "testnet4"})
        self.assertEqual(err.exception.code, 400)
        with patch("gui.scan_wallet", return_value=fake):
            balance = self.post("/api/scan", {"chain": "main"})
        self.assertEqual(balance["source"], "https://mempool.space/api")
        self.assertTrue(balance["utxo_consistent"])
        restored = self.post("/api/status", {})
        self.assertEqual(restored["chain"], "main")
        self.assertTrue(restored["explorer_consent"])
        self.assertEqual(restored["wallet"]["reference_address"], result["reference_address"])
        self.assertEqual(restored["balance"]["observed_sats"], 100_000)
        self.assertNotIn("utxos", restored["balance"])
        with self.assertRaises(HTTPError) as err:
            self.post("/api/prepare", {"chain": "testnet4", "recipient": "tb1wrong",
                                        "amount_sats": 1000})
        self.assertEqual(err.exception.code, 400)

    def test_custom_esplora_server_is_saved_per_network_and_scan_uses_it(self):
        main_url = "https://explorer.btc21.cc/api"
        broadcast_url = "https://relay.example.org/api"
        with patch("gui.verify_esplora") as verify:
            settings = self.post("/api/settings", {
                "chain": "main", "action": "save",
                "explorer_url": main_url, "broadcaster_url": broadcast_url,
            })
        self.assertEqual(settings["explorer_url"], main_url)
        self.assertFalse(settings["broadcasting_available"])
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(self.post("/api/settings", {
            "chain": "testnet4", "action": "read",
        })["explorer_url"], "https://mempool.space/testnet4/api")
        self.assertEqual(LocalApp().servers["main"]["explorer"], main_url)
        self.assertNotIn("bsms", (Path(self.settings_dir.name) / "settings.json").read_text())

        text = mainnet_record()
        self.post("/api/import", {
            "chain": "main", "text": text, "consent_explorer": True,
        })
        fake = {
            "network": "main", "utxo_consistent": True,
            "confirmed_sats": 0, "pending_delta_sats": 0, "observed_sats": 0,
            "addresses": [], "utxos": [], "scanned": 40, "coverage_limited": False,
            "path_warning": "", "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": main_url,
        }
        with patch("gui.verify_esplora"), patch("gui.scan_wallet", return_value=fake) as scan:
            self.post("/api/scan", {"chain": "main"})
        self.assertEqual(scan.call_args.kwargs["base_url"], main_url)
        self.post("/api/settings", {"chain": "main", "action": "reset"})
        self.assertIsNone(self.app.scan)
        self.assertEqual(self.post("/api/settings", {
            "chain": "main", "action": "read",
        })["explorer_url"], "https://mempool.space/api")

    def test_mainnet_fee_reference_is_public_and_cached(self):
        quote = {"network": "main", "fastest": 4, "standard": 3, "hour": 2,
                 "economy": 1, "minimum": 1, "checked_at": "2026-09-28T00:00:00+00:00",
                 "source": "mempool.space mainnet"}
        with patch("gui.fetch_fee_rates", return_value=quote) as fetch:
            for _ in range(2):
                with urlopen(self.base + "/api/fees", timeout=3) as response:
                    self.assertEqual(json.load(response), quote)
        fetch.assert_called_once_with()
        with patch("gui.urlopen", return_value=io.BytesIO(json.dumps({
            "fastestFee": 4, "halfHourFee": 3, "hourFee": 2,
            "economyFee": 1, "minimumFee": 1
        }).encode())) as upstream:
            self.assertEqual(fetch_fee_rates()["fastest"], 4)
        self.assertEqual(upstream.call_args.args[0].full_url,
                         "https://mempool.space/api/v1/fees/recommended")
        with patch("gui.urlopen", return_value=io.BytesIO(json.dumps({
            "fastestFee": True, "halfHourFee": 3, "hourFee": 2,
            "economyFee": 1, "minimumFee": 1
        }).encode())):
            with self.assertRaisesRegex(WalletError, "Fee estimates unavailable"):
                fetch_fee_rates()
        with patch("gui.urlopen", return_value=io.BytesIO(json.dumps({
            "fastestFee": 1, "halfHourFee": 12, "hourFee": 2,
            "economyFee": 1, "minimumFee": 1
        }).encode())):
            with self.assertRaisesRegex(WalletError, "Fee estimates unavailable"):
                fetch_fee_rates()

    def test_mainnet_prepare_refuses_missing_or_excessive_live_fee_reference(self):
        text = mainnet_record()
        self.post("/api/import", {"chain": "main", "text": text,
                                  "consent_explorer": True})
        fake = {
            "network": "main", "utxo_consistent": True,
            "confirmed_sats": 100_000, "pending_delta_sats": 0,
            "observed_sats": 100_000, "addresses": [], "utxos": [],
            "scanned": 40, "coverage_limited": False, "path_warning": "",
            "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": "https://mempool.space/api",
        }
        with patch("gui.scan_wallet", return_value=fake):
            self.post("/api/scan", {"chain": "main"})
        request = {"chain": "main", "recipient": self.app.record.reference_address,
                   "amount_sats": 1000, "fee_rate": 2}
        with patch("gui.fetch_fee_rates", side_effect=WalletError("offline")):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        with patch("gui.fetch_fee_rates", return_value={"standard": 26}):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        self.app.fees = None
        with patch("gui.fetch_fee_rates", return_value={
            "standard": 12, "economy": 3, "checked_at": "2026-09-28T00:00:00Z"
        }), patch("gui.build_unsigned_psbt") as builder:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        builder.assert_not_called()
        self.app.fees = None
        with patch("gui.fetch_fee_rates", return_value={
            "standard": 12, "economy": 1, "network": "main",
            "checked_at": "2026-09-28T00:00:00Z"
        }), patch("gui.build_unsigned_psbt", return_value={
            "fee_warning": "", "fee_rate_estimate": 2, "fee_sats": 540,
            "psbt_base64": "cHNidP8=",
        }):
            result = self.post("/api/prepare", request)
        self.assertIn("below the current mainnet standard", result["fee_warning"])
        self.assertEqual(result["fee_reference"]["standard"], 12)

    def test_testnet4_prepare_uses_identical_fee_guards_and_mainnet_reference(self):
        text, _ = test_record(dual_branch=True)
        wallet = self.post("/api/import", {
            "chain": "testnet4", "text": text, "consent_explorer": True,
        })
        self.assertTrue(wallet["can_prepare"])
        fake = {
            "network": "testnet4", "utxo_consistent": True,
            "confirmed_sats": 6000, "pending_delta_sats": 0,
            "observed_sats": 6000, "addresses": [], "utxos": [],
            "scanned": 50, "coverage_limited": False, "path_warning": "",
            "scanned_at": "2026-09-27T00:00:00+00:00",
            "source": "https://mempool.space/testnet4/api",
        }
        with patch("gui.scan_wallet", return_value=fake):
            self.post("/api/scan", {"chain": "testnet4"})
        request = {"chain": "testnet4", "recipient": wallet["receive_address"],
                   "amount_sats": 1000, "fee_rate": 2}
        with patch("gui.fetch_fee_rates", side_effect=WalletError("offline")):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        with patch("gui.fetch_fee_rates", return_value={
            "standard": 12, "economy": 3, "network": "main",
            "checked_at": "2026-09-28T00:00:00Z"
        }), patch("gui.build_unsigned_psbt") as builder:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        builder.assert_not_called()
        self.app.fees = None
        with patch("gui.fetch_fee_rates", return_value={
            "standard": 12, "economy": 1, "network": "main",
            "checked_at": "2026-09-28T00:00:00Z"
        }), patch("gui.build_unsigned_psbt", return_value={
            "fee_warning": "", "fee_rate_estimate": 2, "fee_sats": 540,
            "psbt_base64": "cHNidP8=",
        }):
            result = self.post("/api/prepare", request)
        self.assertIn("below the current mainnet standard", result["fee_warning"])
        self.assertEqual(result["fee_reference"]["network"], "main")
        with patch("gui.build_unsigned_psbt", return_value={
            "fee_warning": "", "fee_rate_estimate": 12, "fee_sats": 2640,
            "psbt_base64": "cHNidP8=", "send_all": True,
        }) as builder:
            swept = self.post("/api/prepare", {
                "chain": "testnet4", "recipient": wallet["receive_address"],
                "amount_sats": None, "send_all": True, "fee_rate": 12,
            })
        self.assertTrue(swept["send_all"])
        self.assertIsNone(builder.call_args.args[3])
        self.assertTrue(builder.call_args.kwargs["send_all"])

    def test_public_price_endpoint_is_cached_and_independent_of_wallet(self):
        quote = {"usd_per_btc": 84362, "as_of": "2026-09-28T00:00:00+00:00",
                 "source": "mempool.space BTC/USD spot"}
        with patch("gui.fetch_btc_usd", return_value=quote) as fetch:
            with urlopen(self.base + "/api/price", timeout=3) as response:
                self.assertEqual(json.load(response), quote)
            with urlopen(self.base + "/api/price", timeout=3) as response:
                self.assertEqual(json.load(response), quote)
        fetch.assert_called_once_with()
        self.assertIsNone(self.app.record)
        request = Request(self.base + "/api/price", headers={"Host": "not-local.example"})
        with self.assertRaises(HTTPError) as err:
            urlopen(request, timeout=3)
        self.assertEqual(err.exception.code, 403)

    def test_bad_price_does_not_claim_a_zero_wallet_balance(self):
        with patch("gui.fetch_btc_usd", side_effect=WalletError("Rate unavailable")):
            with self.assertRaises(HTTPError) as err:
                urlopen(self.base + "/api/price", timeout=3)
        self.assertEqual(err.exception.code, 503)
        self.assertIsNone(self.app.scan)

    def test_price_feed_rejects_stale_and_malformed_quotes(self):
        now = int(datetime.now(timezone.utc).timestamp())
        for payload in ({"USD": True, "time": now},
                        {"USD": 84362, "time": now - 3600},
                        {"USD": 0, "time": now}):
            with self.subTest(payload=payload):
                with patch("gui.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
                    with self.assertRaisesRegex(WalletError, "rate unavailable"):
                        fetch_btc_usd()
        with patch("gui.urlopen", return_value=io.BytesIO(
            json.dumps({"USD": 84362, "time": now}).encode()
        )) as fetch:
            quote = fetch_btc_usd()
        self.assertEqual(quote["usd_per_btc"], 84362)
        self.assertEqual(fetch.call_args.args[0].full_url,
                         "https://mempool.space/api/v1/prices")


if __name__ == "__main__":
    unittest.main()
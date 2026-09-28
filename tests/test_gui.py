"""Exercise the local browser API without a network or real wallet file."""

import json
import io
import threading
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from gui import LocalApp, fetch_btc_usd
from wallet_service import WalletError
from test_probe import test_record


class LocalGuiTests(unittest.TestCase):
    def setUp(self):
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
        self.assertIn('id="send-equivalent"', page)
        self.assertIn("sats at this address", page)
        self.assertNotIn("__LOCAL_TOKEN__", page)
        text, _ = test_record(short_path=True)
        result = self.post("/api/import", {"chain": "testnet4", "text": text})
        self.assertEqual(len(result["keys"]), 3)
        self.assertTrue(result["receive_address"].startswith("tb1"))
        self.assertIsNotNone(self.app.record)
        self.assertIsNone(self.app.scan)

    def test_import_rejects_bad_chain_and_cross_origin_post(self):
        text, _ = test_record()
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
        self.post("/api/import", {"chain": "testnet4", "text": text})
        fake = {
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
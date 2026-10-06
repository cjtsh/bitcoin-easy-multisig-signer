"""Exercise the local browser API without a network or real wallet file."""

import json
import io
import re
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
from embit import psbt, transaction
from embit.script import Script

from gui import (LocalApp, PreparedPayment, fetch_btc_usd, fetch_fee_rates,
                 fetch_mutinynet_fee_rates)
from version import APP_VERSION
from wallet_service import WalletError
from test_probe import test_record
from test_wallet_service import mainnet_record

SYNTHETIC_TX = transaction.Transaction(
    vin=[transaction.TransactionInput(bytes(32), 0)],
    vout=[transaction.TransactionOutput(1000, Script(b"\x6a"))],
)
SYNTHETIC_PSBT = psbt.PSBT(SYNTHETIC_TX).to_base64()
SYNTHETIC_TXID = SYNTHETIC_TX.txid().hex()


class LocalGuiTests(unittest.TestCase):
    def setUp(self):
        self.settings_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.settings_dir.cleanup)
        self.settings_patch = patch("network_settings.settings_path",
                                    return_value=Path(self.settings_dir.name) / "settings.json")
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.app = LocalApp()
        self.outpoint_patch = patch("gui.verify_selected_outpoints")
        self.outpoint_patch.start()
        self.addCleanup(self.outpoint_patch.stop)
        # CT-20 always genesis-checks the explorer, including the built-in URL.
        # The harness never touches the network, so stub the probe here; the
        # dedicated pin asserts it is actually consulted.
        self.genesis_patch = patch("gui.verify_esplora")
        self.genesis_patch.start()
        self.addCleanup(self.genesis_patch.stop)
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

    def get_page(self):
        with urlopen(self.base, timeout=3) as response:
            return response.read().decode()

    def test_file_picker_page_imports_synthetic_public_wallet(self):
        page = self.get_page()
        self.assertIn('type="file"', page)
        self.assertIn("Testnet4", page)
        self.assertIn('id="balance-usd"', page)
        self.assertIn('id="observed-btc"', page)
        balance_row = page.split('<div class="balance-primary">', 1)[1].split('</section>', 1)[0]
        self.assertLess(balance_row.index('id="observed-btc"'), balance_row.index('id="observed"'))
        self.assertLess(balance_row.index('id="balance-usd"'), balance_row.index('id="observed"'))
        self.assertIn('setText("observed-btc", btc(data.observed_sats))', page)
        self.assertIn('id="send-equivalent"', page)
        self.assertIn('class="context-help"', page)
        # Help is opt-in and was deliberately reduced; keep a floor so it does
        # not disappear entirely.
        self.assertGreaterEqual(page.count('class="help-popout"'), 4)
        self.assertIn('aria-label="What am I saving as a PSBT file?"', page)
        self.assertIn("PSBT means Partially Signed Bitcoin Transaction.", page)
        self.assertIn("Preparing it does not move Bitcoin.", page)
        self.assertIn("Save unsigned transaction file (.psbt) to Downloads", page)
        self.assertIn("Apple Silicon (M-series) only", page)
        self.assertIn('id="send-all" type="checkbox"', page)
        self.assertNotIn('id="send-all" type="checkbox" checked', page)
        self.assertIn('id="send-choice"', page)
        self.assertIn("Would you like to prepare a Bitcoin transaction?", page)
        self.assertIn('id="begin-send"', page)
        self.assertIn('id="decline-send"', page)
        self.assertIn('id="send-flow" hidden', page)
        self.assertNotIn('id="copy-balance"', page)
        self.assertNotIn('id="confirmed-btc"', page)
        self.assertIn('id="amount" type="text" inputmode="decimal"', page)
        self.assertIn('send_all:sendAll', page)
        self.assertIn('id="review-amount-sats"', page)
        self.assertIn('id="review-remaining"', page)
        self.assertIn('id="balance-send-status"', page)
        self.assertIn("No confirmed Bitcoin was found", page)
        self.assertIn("Explorer UTXOs and confirmed balance disagree", page)
        self.assertIn("The scan reached the 100-address limit", page)
        self.assertIn("Other wallet addresses beyond the scan gap may still hold funds.", page)
        self.assertIn("sats at this address", page)
        self.assertIn('value="testnet4"', page)
        self.assertIn('value="mutinynet"', page)
        # Live Bitcoin is not one of the radio cards: the gate returns to it, and
        # a scripted or stale attempt to select mainnet inside developer mode is
        # refused, because that is the one state where the orange frame and the
        # network badge would disagree with the mode.
        self.assertNotIn('value="main"', page)
        self.assertIn('if (developerMode && value === "main") return;', page)
        self.assertIn('id="refresh-top"', page)
        self.assertIn('id="pending-payment"', page)
        self.assertIn('id="pending-check"', page)
        self.assertIn("waiting for one confirmation", page)
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

    def test_technical_detail_is_behind_a_details_panel(self):
        """The screen a lawyer or a spouse sees must not be a wall of keys."""
        page = self.get_page()
        start = page.index('id="wallet-details"')
        panel = page[start:]
        # Everything technical lives in the panel...
        for element in ("id=\"reference\"", "id=\"receive\"", "id=\"change\"",
                        "id=\"keys\"", "id=\"confirmed\"", "id=\"pending\"",
                        "id=\"utxo-count\"", "id=\"addresses\"", "id=\"price-note\"",
                        "id=\"scan-source\""):
            self.assertIn(element, panel, f"{element} should live in the details panel")
        # ...and nothing technical is left on the main screen above it.
        before = page[:start]
        for element in ("id=\"keys\"", "id=\"addresses\"", "id=\"confirmed\"",
                        "id=\"utxo-count\"", "id=\"reference\""):
            self.assertNotIn(element, before,
                             f"{element} should not be on the main screen any more")
        # Two ways in, one dialog.
        self.assertEqual(page.count('class="details-button"'), 2)
        self.assertIn('id="close-details"', panel)

    def test_the_send_flow_offers_signing_and_broadcast(self):
        """The owner has to be able to sign and send from this screen, and the
        transaction id they confirm must be the one that is broadcast."""
        page = self.get_page()
        self.assertIn("Supports hardware multisig wallets with up to three physical keys.", page)
        for element in ('id="sign-step"', 'id="sign-buttons"', 'id="sign-progress"',
                        'id="finalize-step"', 'id="final-amount"', 'id="final-fee"',
                        'id="final-vsize"', 'id="final-signers"', 'id="final-txid"',
                        'id="confirm-broadcast"', 'id="broadcast"',
                        'id="broadcast-message"'):
            self.assertIn(element, page, f"missing {element}")
        # Broadcasting requires the tick, and the confirmed id is what is sent.
        self.assertIn('$("confirm-broadcast").addEventListener("change"', page)
        self.assertIn("confirmed_txid: finalTxid", page)
        self.assertIn("mainnet_opt_in: finalChain === \"main\"", page)
        self.assertIn("Mainnet sends real Bitcoin", page)
        # The broadcast button is disabled until the tick is set.
        self.assertIn('$("broadcast").disabled = true', page)
        self.assertIn('$("broadcast").disabled = !$("confirm-broadcast").checked', page)
        # The old promise that nothing is ever signed is no longer true.
        self.assertNotIn("No transaction is signed or broadcast.", page)

    def test_the_fee_speed_buttons_show_which_one_is_selected(self):
        """Reported bug: pressing Slow/Medium/Fast gave no confirmation at all."""
        page = self.get_page()
        self.assertEqual(page.count('class="secondary rate-button"'), 3)
        # A real visual state, not just an aria attribute nobody styles.
        self.assertIn("button.rate-button.selected", page)
        self.assertIn('id="fee-selected"', page)
        self.assertIn('setText("fee-selected"', page)
        # Selection is tracked by tier, not by rate value: slow, medium and fast are
        # frequently the same whole sat/vB, so comparing rates cannot distinguish them.
        self.assertIn("let selectedTier", page)
        self.assertIn("selectedTier = tier", page)
        self.assertIn('selectedTier = "custom"', page)
        self.assertIn('selectedTier = "medium"', page)

    def test_signer_preflight_is_step_three_of_the_flow(self):
        """A non-technical owner must meet device checking before the payment,
        and understand why, without it being a second competing flow."""
        page = self.get_page()
        self.assertIn('id="signers-card"', page)
        self.assertIn("3. Check your hardware wallets", page)
        self.assertIn("4. Prepare a send", page)
        self.assertIn('id="check-signers-now"', page)
        self.assertIn('id="preflight-message"', page)
        self.assertIn('id="preflight-results"', page)
        # The reason it is here, in plain words.
        self.assertIn("before you build a payment", page)
        # And what it does not do, so nobody fears it.
        self.assertIn("any PIN is entered on the device itself", page)
        self.assertIn("none of your keys are in this app", page)
        # One shared routine serves both places, so they cannot drift apart.
        self.assertIn("async function runSignerCheck", page)
        self.assertEqual(page.count("runSignerCheck("), 3)  # definition + two callers

    def test_step_three_helps_when_no_device_appears(self):
        """The most likely first outcome is nothing being detected; the app must
        give the owner something to try rather than an empty list."""
        page = self.get_page()
        self.assertIn('id="preflight-help"', page)
        for hint in ("Unlock the device with its PIN",
                     "A Ledger needs it open",
                     "Some cables only carry power",
                     "Close any other wallet software"):
            self.assertIn(hint, page, f"missing troubleshooting hint: {hint}")
        # It shows whenever a device still needs the owner to do something:
        # nothing found, one that could not be read, or one that did not match.
        self.assertIn('$(helpId).hidden = !result.attention', page)
        self.assertIn('helpId', page)

    def test_slow_work_shows_a_spinner(self):
        """Reported bug: a slow scan looked like the app had done nothing."""
        page = self.get_page()
        self.assertIn('id="busy"', page)
        self.assertIn('class="spinner"', page)
        self.assertIn('id="busy-text"', page)
        self.assertIn("@keyframes spin", page)
        self.assertIn("function setBusy", page)
        # Each wait the owner can hit, including both they reported.
        for message in ("Reading your wallet file",
                        "Checking the blockchain for your balance",
                        "Looking for your signing device",
                        "Check each screen carefully"):
            self.assertIn(message, page, f"missing progress message: {message}")
        # The bar must take its colours from the palette so it themes with the rest
        # of the app. This assertion used to pin a literal "#ffd447", which is
        # precisely how colours drifted: a test holding a raw value in place while
        # nobody had chosen it. It now pins the role instead.
        self.assertIn("background:var(--pending-bg)", page)
        self.assertNotIn("#ffd447", page)
        # The wait must be visible, but its length must not be. The internal
        # timeouts exist so a slow human is never cut off mid-review; advertising
        # one reads as permission to walk away while a signing ceremony is open.
        for duration in ("10 minutes", "several minutes", "minutes"):
            self.assertNotIn(duration, page, f"the page must not advertise a wait: {duration}")
        # Elapsed seconds prove the app is still working, which is what actually
        # stops people clicking a second time.
        self.assertIn('id="busy-elapsed"', page)
        self.assertIn("setInterval", page)

    def test_the_page_says_up_front_that_steps_take_time(self):
        """The operator should not have to guess that the app is still working.

        The DOM tests cannot see this: they build elements on demand and never
        parse the markup, so a `hidden` attribute is invisible to them. What the
        served page actually renders has to be asserted here.
        """
        page = self.get_page()
        self.assertIn("please wait rather than clicking again", page)
        note = re.search(r'<section id="patience-note"[^>]*>', page)
        self.assertIsNotNone(note, "the note must be in the served page")
        self.assertNotIn("hidden", note.group(0),
                         "the note must be visible at the start, not hidden")
        dismiss = re.search(r'<button id="patience-dismiss"[^>]*>', page)
        self.assertIsNotNone(dismiss, "the note must be dismissible")
        self.assertIn('$("patience-dismiss").addEventListener("click"', page)

    def test_the_main_screen_asks_nothing_technical_of_the_user(self):
        """A lawyer or a spouse must not be asked to assert wallet internals.

        The app resolves the change branch itself and tells the user what it did.
        It must never ask them to confirm a derivation detail they cannot check,
        and the main screen must not expose descriptor jargon.
        """
        page = self.get_page()
        # No confirmation checkbox or button about change paths.
        for removed in ('id="declare-change"', 'id="confirm-change-branch"',
                        'id="declare-change-button"', 'id="declared-change-ack-row"',
                        'id="path-warning"'):
            self.assertNotIn(removed, page)
        # Instead: one plain note, filled from the server's own wording.
        self.assertIn('id="change-note"', page)
        self.assertIn("setText(\"change-note\"", page)
        self.assertIn('id="change-detail"', page)
        # The wallet card itself carries no descriptor jargon.
        card = page.split('id="wallet-card"', 1)[1].split("</section>", 1)[0]
        for jargon in ("descriptor", "/0/*", "/1/*", "xpub", "derivation",
                       "Reference address", "BIP48", "native-SegWit",
                       "tb1 alone cannot identify"):
            self.assertNotIn(jargon, card, f"{jargon} should not be on the main screen")

    def test_send_flow_recommends_a_test_and_links_to_the_explorer(self):
        page = self.get_page()
        self.assertIn("Recommended: send a small test amount first.", page)
        self.assertIn('id="review-txid"', page)
        self.assertIn('id="review-explorer"', page)
        self.assertIn("A payment is not finished until it is confirmed.", page)
        self.assertIn("Continue below to approve signing on the required hardware devices.", page)
        self.assertIn("explorer_web", page)

    def test_prepare_reports_a_final_transaction_id(self):
        """Segwit txids do not cover the witness, so the id is fixed at prepare."""
        from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout
        from fake_explorer import three_output_wallet
        from probe import parse_bsms
        from embit.networks import NETWORKS
        text, _ = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        recipient = layout.receive.derive(5).address(NETWORKS["test"])
        result = build_unsigned_psbt(record, scan, recipient, 1_000, 5, explorer)
        import base64
        packet = __import__("embit").psbt.PSBT.parse(
            base64.b64decode(result["psbt_base64"]))
        self.assertEqual(result["txid"], packet.tx.txid().hex())
        self.assertEqual(len(result["txid"]), 64)

    def test_the_api_accepts_a_sparrow_style_wallet_file(self):
        """The owner's first Sparrow export failed at import with "A descriptor with
        one checksum is required". It must work end to end, not just in the parser."""
        from test_probe import sparrow_record
        text, _ = sparrow_record()
        wallet = self.post("/api/import", {"chain": "testnet4", "text": text,
                                           "consent_explorer": True})
        self.assertEqual(wallet["reference_status"], "verified")
        self.assertEqual(wallet["policy_short"], "2-of-3 multisig wallet")
        # The file omits the checksum, so the app computes it for the owner to
        # compare against the wallet software's own backup document.
        self.assertFalse(wallet["checksum_supplied"])
        self.assertEqual(len(wallet["descriptor_checksum"]), 8)

    def test_read_only_signer_check_requires_current_transaction_review(self):
        text, _ = test_record(short_path=True)
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        self.app.prepared = PreparedPayment(
            self.app.record, "testnet4", self.app.scan_generation,
            "prepared-test", "cHNidP8=", "", (), ())
        with self.assertRaises(HTTPError) as err:
            self.post("/api/devices", {"preparation_id": "stale"})
        self.assertEqual(err.exception.code, 400)
        with patch("gui.probe_devices_detailed", return_value={
                "statuses": ["Trezor: signer 1 of 3 public xpub matched (not a signing test)."],
                "signable": [{"type": "trezor", "path": "p", "model": "Trezor",
                              "signer": 1, "keys": 3, "fingerprint": "aa"}]}):
            result = self.post("/api/devices", {"preparation_id": "prepared-test"})
        self.assertIn("does not sign or send", result["message"])
        self.assertIn("not a signing test", result["devices"][0])
        # A pre-flight check is legitimate with no transaction at all: the open
        # wallet is enough, and the reply must say that no transaction was involved
        # so a device check can never be read as approval of a payment.
        with patch("gui.probe_devices_detailed", return_value={
                "statuses": ["Coldcard: not a signer in this BSMS file."],
                "signable": []}):
            preflight = self.post("/api/devices", {})
        self.assertIn("no transaction was involved", preflight["message"])
        self.assertEqual(preflight["devices"], ["Coldcard: not a signer in this BSMS file."])
        # A device that did not match still needs the owner's attention, so the
        # interface must offer the troubleshooting list.
        self.assertTrue(preflight["attention"])
        with patch("gui.probe_devices_detailed", return_value={
                "statuses": ["Jade: signer 1 of 3 public xpub matched (not a signing test)."],
                "signable": []}):
            matched = self.post("/api/devices", {})
        self.assertFalse(matched["attention"])

    def test_the_device_check_asks_hwi_for_a_chain_it_understands(self):
        """hwilib's Jade backend has no testnet4 in its network map and raises
        "Unhandled network: testnet4", which broke the owner's Jade. Trezor and
        Ledger treat any non-mainnet chain as testnet, and testnet and testnet4 share
        the tpub version bytes and the tb1 prefix, so the check asks for "test"."""
        text, _ = test_record(short_path=True)
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        with patch("gui.probe_devices_detailed",
                   return_value={"statuses": [], "signable": []}) as call:
            self.post("/api/devices", {})
        self.assertEqual(call.call_args[0][2], "test")

    def test_a_mainnet_wallet_still_asks_for_mainnet(self):
        self.post("/api/import", {"chain": "main", "text": mainnet_record(),
                                  "consent_explorer": True})
        with patch("gui.probe_devices_detailed",
                   return_value={"statuses": [], "signable": []}) as call:
            self.post("/api/devices", {})
        self.assertEqual(call.call_args[0][2], "main")

    def test_signer_check_without_an_open_wallet_is_refused(self):
        with self.assertRaises(HTTPError) as err:
            self.post("/api/devices", {})
        self.assertEqual(err.exception.code, 400)

    def test_mainnet_high_value_transaction_needs_explicit_confirmation(self):
        self.app.price = {"usd_per_btc": 50_000}
        self.app.price_checked = time.monotonic()
        self.app.fees = {"standard": 2, "economy": 1, "network": "main",
                         "checked_at": "2026-09-28T00:00:00Z"}
        self.app.fees_checked = time.monotonic()
        self.post("/api/import", {"chain": "main", "text": mainnet_record(),
                                  "consent_explorer": True})
        fake = {
            "network": "main", "utxo_consistent": True, "confirmed_sats": 50_000_000,
            "pending_delta_sats": 0, "observed_sats": 50_000_000, "addresses": [],
            "utxos": [], "scanned": 40, "coverage_limited": False, "path_warning": "",
            "scanned_at": "2026-09-28T00:00:00+00:00", "source": "https://mempool.space/api",
        }
        with patch("gui.scan_wallet", return_value=fake):
            self.post("/api/scan", {"chain": "main"})
        request = {"chain": "main", "recipient": self.app.record.reference_address,
                   "amount_sats": 20_000_000, "fee_rate": 2}
        with patch("gui.build_unsigned_psbt") as builder:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", request)
        self.assertEqual(err.exception.code, 400)
        builder.assert_not_called()
        request["large_amount_confirmed"] = True
        with patch("gui.build_unsigned_psbt", return_value={
            "psbt_base64": SYNTHETIC_PSBT, "fee_warning": "", "txid": SYNTHETIC_TXID,
            "fee_sats": 540, "fee_rate_estimate": 2,
            "recipient": request["recipient"], "amount_sats": request["amount_sats"],
            "change_sats": 1000, "change_address": request["recipient"],
            "send_all": False,
        }):
            result = self.post("/api/prepare", request)
        self.assertTrue(result["preparation_id"])

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

    def test_oversized_requests_are_refused_before_parsing(self):
        """The request-size bound holds at the HTTP boundary (CT-08)."""
        from gui import MAX_REQUEST_BYTES
        with self.assertRaises(HTTPError) as err:
            self.post("/api/import", {"chain": "testnet4",
                                      "text": "x" * MAX_REQUEST_BYTES})
        self.assertEqual(err.exception.code, 400)
        self.assertIn("too large or malformed",
                      json.load(err.exception)["error"])

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

    def test_recent_broadcast_stays_paused_until_explorer_confirms_it(self):
        text, _ = test_record()
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        txid = "ab" * 32
        self.app.pending_broadcast_txid = txid
        fake = {
            "network": "testnet4", "utxo_consistent": True,
            "confirmed_sats": 6000, "pending_delta_sats": 0,
            "observed_sats": 6000, "pending_outgoing": False,
            "addresses": [], "utxos": [], "scanned": 40,
            "coverage_limited": False, "path_warning": "",
            "scanned_at": "2026-09-29T00:00:00+00:00",
            "source": "https://mempool.space/testnet4/api",
        }
        with patch("gui.scan_wallet", side_effect=lambda *_args, **_kwargs: dict(fake)), \
             patch("gui.explorer_get", side_effect=[{"confirmed": False},
                                                    WalletError("Explorer unavailable"),
                                                    {"confirmed": True}]) as status:
            waiting = self.post("/api/scan", {"chain": "testnet4"})
            self.assertTrue(waiting["pending_outgoing"])
            with self.assertRaises(HTTPError) as err:
                self.post("/api/prepare", {"chain": "testnet4"})
            self.assertEqual(err.exception.code, 400)
            still_waiting = self.post("/api/scan", {"chain": "testnet4"})
            self.assertTrue(still_waiting["pending_outgoing"])
            ready = self.post("/api/scan", {"chain": "testnet4"})
        self.assertFalse(ready["pending_outgoing"])
        self.assertIsNone(self.app.pending_broadcast_txid)
        self.assertEqual(status.call_count, 3)

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
        self.app.prepared = PreparedPayment.create(
            self.app.record, "main", self.app.scan_generation, "mainnet-review",
            SYNTHETIC_PSBT, {"txid": SYNTHETIC_TXID},
        )
        with self.assertRaises(HTTPError) as err:
            self.post("/api/broadcast", {
                "preparation_id": "mainnet-review", "confirm": True,
                "confirmed_txid": SYNTHETIC_TXID,
            })
        self.assertEqual(err.exception.code, 400)
        self.assertIn("separate mainnet warning", err.exception.read().decode())
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

    def test_mutinynet_fee_quote_is_network_specific_and_validated(self):
        values = {"1": 3.2, "3": 2.2, "6": 2.1, "144": 1.1, "1008": 1.0}
        with patch("gui.urlopen", return_value=io.BytesIO(json.dumps(values).encode())) as upstream:
            quote = fetch_mutinynet_fee_rates()
        self.assertEqual((quote["network"], quote["standard"]), ("mutinynet", 3))
        self.assertEqual(upstream.call_args.args[0].full_url,
                         "https://mutinynet.com/api/fee-estimates")
        with patch("gui.urlopen", return_value=io.BytesIO(json.dumps(
                {**values, "1": True}).encode())):
            with self.assertRaisesRegex(WalletError, "Mutinynet fee estimates unavailable"):
                fetch_mutinynet_fee_rates()

    def test_mainnet_prepare_refuses_missing_or_excessive_live_fee_reference(self):
        text = mainnet_record()
        self.post("/api/import", {"chain": "main", "text": text,
                                  "consent_explorer": True})
        self.app.price = {"usd_per_btc": 50_000}
        self.app.price_checked = time.monotonic()
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
            "psbt_base64": SYNTHETIC_PSBT,
            "txid": SYNTHETIC_TXID, "recipient": request["recipient"],
            "amount_sats": request["amount_sats"], "change_sats": 1000,
            "change_address": request["recipient"], "send_all": False,
        }):
            result = self.post("/api/prepare", request)
        self.assertIn("below the current mainnet standard", result["fee_warning"])
        self.assertEqual(result["fee_reference"]["standard"], 12)

    def test_testnet4_prepare_uses_identical_fee_guards_and_mainnet_reference(self):
        text, _ = test_record(bsms_template=True)
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
            "psbt_base64": SYNTHETIC_PSBT,
            "txid": SYNTHETIC_TXID, "recipient": request["recipient"],
            "amount_sats": request["amount_sats"], "change_sats": 1000,
            "change_address": request["recipient"], "send_all": False,
        }):
            result = self.post("/api/prepare", request)
        self.assertIn("below the current mainnet standard", result["fee_warning"])
        self.assertEqual(result["fee_reference"]["network"], "main")
        with patch("gui.build_unsigned_psbt", return_value={
            "fee_warning": "", "fee_rate_estimate": 12, "fee_sats": 2640,
            "psbt_base64": SYNTHETIC_PSBT, "send_all": True,
            "txid": SYNTHETIC_TXID, "recipient": wallet["receive_address"],
            "amount_sats": 1000, "change_sats": 0, "change_address": None,
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

"""The signing, finalisation and broadcast endpoints.

These are the guards around the only code in this app that can move money, so they
are tested through the real local API rather than by calling functions directly: the
preparation binding, the refusal of a device that returns a different transaction, the
refusal to broadcast an unconfirmed or un-finalisable transaction, and the mainnet
lock all have to hold at the HTTP boundary, because that is where the page talks to
them.
"""

import base64
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from http.server import ThreadingHTTPServer  # noqa: E402

from embit import psbt as E  # noqa: E402
from embit.networks import NETWORKS  # noqa: E402
from urllib.request import Request  # noqa: E402

from fake_explorer import three_output_wallet  # noqa: E402
from gui import LocalApp  # noqa: E402
from probe import parse_bsms  # noqa: E402
from test_probe import test_record  # noqa: E402
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout  # noqa: E402
from wallet_service import BroadcastOutcomeUnknown, WalletError  # noqa: E402


class SendFlowTests(unittest.TestCase):
    def setUp(self):
        self.settings_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.settings_dir.cleanup)
        self.settings_patch = patch(
            "network_settings.settings_path",
            return_value=Path(self.settings_dir.name) / "settings.json")
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.app = LocalApp()
        self.outpoint_patch = patch("gui.verify_selected_outpoints")
        self.outpoint_check = self.outpoint_patch.start()
        self.addCleanup(self.outpoint_patch.stop)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.app.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.addCleanup(self._stop_server)

    def _stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def post(self, route, data, token=None):
        headers = {"Content-Type": "application/json",
                   "X-Local-Token": self.app.token if token is None else token}
        request = Request(self.base + route, data=json.dumps(data).encode(),
                          headers=headers, method="POST")
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def prepare_a_reviewed_transaction(self, chain="testnet4"):
        """Put the app in the state it is in after a reviewed, saved transaction."""
        text, roots = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        recipient = layout.receive.derive(5).address(NETWORKS["test"])
        result = build_unsigned_psbt(record, scan, recipient, 100_000, 5, explorer)
        self.post("/api/import", {"chain": chain, "text": text,
                                  "consent_explorer": True})
        self.app.record = record
        self.app.chain = chain
        self.app.prepared_psbt = result["psbt_base64"]
        self.app.prepared_id = "reviewed-1"
        self.app.prepared_txid = result["txid"]
        self.app.prepared_review = {key: result[key] for key in (
            "txid", "recipient", "amount_sats", "fee_sats", "change_sats",
            "change_address", "send_all")}
        keys = [root.derive("m/48h/1h/0h/2h/0/0") for root in roots]
        return result, keys

    def signing_device(self, key):
        """A stand-in for one hardware device holding one key.

        A real device signs every input it can in one go, which is what embit's
        sign_with does, so two devices complete a 2-of-3 transaction whatever the
        number of inputs.
        """
        def fake_sign(_executable, _chain, _type, _path, psbt_base64):
            packet = E.PSBT.from_base64(psbt_base64)
            packet.sign_with(key)
            return packet.to_base64()
        return fake_sign

    def test_a_signed_transaction_finalises_and_broadcasts(self):
        result, keys = self.prepare_a_reviewed_transaction()
        txid = result["txid"]

        # One signature is not enough.
        with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(keys[0])):
            first = self.post("/api/sign", {"preparation_id": "reviewed-1",
                                            "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual((first["signatures"], first["threshold"]), (1, 2))
        self.assertFalse(first["complete"])
        self.assertEqual(first["signers"], [1])
        with self.assertRaises(HTTPError) as err:
            self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        self.assertEqual(err.exception.code, 400)

        # A second signature completes it.
        with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(keys[1])):
            second = self.post("/api/sign", {"preparation_id": "reviewed-1",
                                             "device_type": "trezor", "device_path": "webusb:1"})
        self.assertTrue(second["complete"])
        self.assertEqual(second["signers"], [1, 2])

        final = self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        self.assertEqual(final["txid"], txid)
        self.assertGreater(final["vsize"], 0)
        self.assertEqual(final["amount_sats"], 100_000)
        self.assertEqual(final["signers"], [1, 2])

        with patch("gui.broadcast_transaction", return_value=txid) as send:
            sent = self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                                "confirm": True, "confirmed_txid": txid})
        self.assertEqual(sent["txid"], txid)
        self.assertIn(txid, sent["explorer"])
        self.assertIn("mempool.space", sent["explorer"])
        # What was broadcast is the finalised transaction, not the unsigned one.
        self.assertGreater(len(send.call_args[0][0]), 200)

    def test_signing_requires_the_reviewed_transaction(self):
        self.prepare_a_reviewed_transaction()
        for bad in ("", "stale-id", None):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/sign", {"preparation_id": bad,
                                        "device_type": "jade", "device_path": "/dev/x"})
            self.assertEqual(err.exception.code, 400)

    def test_a_device_returning_a_different_transaction_is_refused(self):
        """A device that hands back some other transaction must never be accepted."""
        self.prepare_a_reviewed_transaction()
        other, _keys, _ = None, None, None
        text, roots = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        other = build_unsigned_psbt(record, scan,
                                    layout.receive.derive(7).address(NETWORKS["test"]),
                                    50_000, 5, explorer)
        with patch("gui.sign_psbt_with_device", return_value=other["psbt_base64"]):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(err.exception.code, 400)

    def test_broadcast_needs_an_explicit_confirmation_of_that_exact_transaction(self):
        result, keys = self.prepare_a_reviewed_transaction()
        txid = result["txid"]
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"), ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        with patch("gui.broadcast_transaction", return_value=txid) as send:
            for payload in ({"preparation_id": "reviewed-1"},
                            {"preparation_id": "reviewed-1", "confirm": False,
                             "confirmed_txid": txid},
                            {"preparation_id": "reviewed-1", "confirm": True},
                            {"preparation_id": "reviewed-1", "confirm": True,
                             "confirmed_txid": "00" * 32}):
                with self.assertRaises(HTTPError) as err:
                    self.post("/api/broadcast", payload)
                self.assertEqual(err.exception.code, 400)
            send.assert_not_called()

    def test_unknown_broadcast_result_locks_the_payment_from_retry(self):
        result, keys = self.prepare_a_reviewed_transaction()
        txid = result["txid"]
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                           ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        payload = {"preparation_id": "reviewed-1", "confirm": True,
                   "confirmed_txid": txid}
        with patch("gui.broadcast_transaction", side_effect=BroadcastOutcomeUnknown(
                "The broadcast result is unknown.")) as send:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/broadcast", payload)
            self.assertEqual(err.exception.code, 409)
            body = json.load(err.exception)
            self.assertTrue(body["outcome_unknown"])
            self.assertIn(txid, body["explorer"])
            with self.assertRaises(HTTPError) as repeat:
                self.post("/api/broadcast", payload)
            self.assertEqual(repeat.exception.code, 400)
            send.assert_called_once()
        self.assertIsNone(self.app.prepared_psbt)
        self.assertEqual(self.app.pending_broadcast_txid, txid)
        self.assertTrue(self.app.pending_broadcast_unknown)

    def test_spent_output_is_refused_before_broadcast_request(self):
        result, keys = self.prepare_a_reviewed_transaction()
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                           ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        self.outpoint_check.side_effect = WalletError("A selected output was spent.")
        with patch("gui.broadcast_transaction") as send:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                             "confirm": True,
                                             "confirmed_txid": result["txid"]})
            self.assertEqual(err.exception.code, 400)
            send.assert_not_called()

    def test_broadcasting_real_bitcoin_is_not_enabled(self):
        """The mainnet lock is the most important refusal in this file.

        It is checked against the open wallet's network before anything else, so a
        fully signed, perfectly valid mainnet transaction is still refused.
        """
        self.prepare_a_reviewed_transaction()
        self.app.chain = "main"
        with patch("gui.broadcast_transaction", return_value=self.app.prepared_txid) as send:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                             "confirm": True,
                                             "confirmed_txid": self.app.prepared_txid})
            self.assertEqual(err.exception.code, 400)
            self.assertIn("not enabled", err.exception.read().decode())
        send.assert_not_called()

    def test_wallet_import_waits_until_broadcast_submission_finishes(self):
        """A concurrent import cannot replace the reviewed payment mid-submit."""
        result, keys = self.prepare_a_reviewed_transaction()
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"), ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        entered = threading.Event()
        release = threading.Event()
        import_done = threading.Event()
        outcomes = {}

        def delayed_broadcast(*_args):
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Timed out waiting for race test")
            return result["txid"]

        def send():
            try:
                outcomes["send"] = self.post("/api/broadcast", {
                    "preparation_id": "reviewed-1", "confirm": True,
                    "confirmed_txid": result["txid"]})
            except Exception as exc:
                outcomes["send_error"] = exc

        def replace_wallet():
            try:
                outcomes["import"] = self.post("/api/import", {
                    "chain": "testnet4", "text": test_record(bsms_template=True)[0],
                    "consent_explorer": True})
            finally:
                import_done.set()

        with patch("gui.broadcast_transaction", side_effect=delayed_broadcast):
            sender = threading.Thread(target=send)
            sender.start()
            self.assertTrue(entered.wait(2), "broadcast did not enter the submission step")
            importer = threading.Thread(target=replace_wallet)
            importer.start()
            try:
                self.assertFalse(import_done.wait(0.2),
                                 "wallet import passed while broadcast was in flight")
            finally:
                release.set()
                sender.join(3)
                importer.join(3)
        self.assertNotIn("send_error", outcomes)
        self.assertEqual(outcomes["send"]["txid"], result["txid"])
        self.assertTrue(import_done.is_set())

    def test_the_device_check_reports_what_can_sign(self):
        text, _ = test_record()
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        matched = [{"type": "jade", "path": "/dev/cu.usbserial-1", "model": "Jade",
                    "signer": 1, "keys": 3, "fingerprint": "a54cf273"}]
        with patch("gui.probe_devices_detailed",
                   return_value={"statuses": ["Jade: signer 1 of 3 public xpub matched "
                                              "(not a signing test)."],
                                 "signable": matched}):
            result = self.post("/api/devices", {})
        self.assertEqual(result["signable"], matched)
        self.assertFalse(result["attention"])


if __name__ == "__main__":
    unittest.main()

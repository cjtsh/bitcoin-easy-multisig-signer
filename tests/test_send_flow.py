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
from dataclasses import replace
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
from gui import LocalApp, PreparedPayment  # noqa: E402
from probe import ProbeError, parse_bsms  # noqa: E402
from test_probe import test_record  # noqa: E402
from test_wallet_service import mainnet_record, mainnet_roots  # noqa: E402
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
        self.identity_patch = patch("gui.verify_signer_device")
        self.identity_check = self.identity_patch.start()
        self.addCleanup(self.identity_patch.stop)
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

    def prepare_a_reviewed_transaction(self, chain="testnet4", mainnet=False):
        """Put the app in the state it is in after a reviewed, saved transaction."""
        if mainnet:
            text, roots = mainnet_record(), mainnet_roots()
            network, signing_path = NETWORKS["main"], "m/48h/0h/0h/2h/0/0"
        else:
            text, roots = test_record(bsms_template=True)
            network, signing_path = NETWORKS["test"], "m/48h/1h/0h/2h/0/0"
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, network)
        scan = scan_wallet(record, explorer)
        recipient = layout.receive.derive(5).address(network)
        result = build_unsigned_psbt(record, scan, recipient, 100_000, 5, explorer)
        self.post("/api/import", {"chain": chain, "text": text,
                                  "consent_explorer": True})
        self.app.record = record
        self.app.chain = chain
        review = {key: result[key] for key in (
            "txid", "recipient", "amount_sats", "fee_sats", "change_sats",
            "change_address", "send_all")}
        self.app.prepared = PreparedPayment.create(
            record, chain, self.app.scan_generation, "reviewed-1",
            result["psbt_base64"], review)
        # A real signing screen discovers and binds devices to this review first.
        # The separate probe tests exercise the xpub check itself.
        signable = [
            {"type": "jade", "path": "/dev/x", "signer": 1},
            {"type": "trezor", "path": "webusb:1", "signer": 2},
            {"type": "trezor", "path": "usb:1", "signer": 2},
            {"type": "ledger", "path": "hid:1", "signer": 1},
        ]
        with patch("gui.probe_devices_detailed", return_value={
                "statuses": [], "signable": signable}):
            self.post("/api/devices", {"preparation_id": "reviewed-1"})
        keys = [root.derive(signing_path) for root in roots]
        return result, keys

    def test_unmatched_device_path_cannot_receive_the_reviewed_psbt(self):
        self.prepare_a_reviewed_transaction()
        with patch("gui.sign_psbt_with_device") as signer:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/other"})
        self.assertEqual(error.exception.code, 400)
        signer.assert_not_called()
        self.identity_check.assert_not_called()

    def test_matched_device_is_reverified_before_signing(self):
        _result, keys = self.prepare_a_reviewed_transaction()
        with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(keys[0])):
            self.post("/api/sign", {"preparation_id": "reviewed-1",
                                    "device_type": "jade", "device_path": "/dev/x"})
        self.identity_check.assert_called_once_with(
            self.app.record, "hwi", "test", "jade", "/dev/x", 1)

    def test_signing_refuses_when_no_device_binding_was_recorded(self):
        self.prepare_a_reviewed_transaction()
        self.app.verified_signers = None
        reviewed = self.app.prepared
        with patch("gui.sign_psbt_with_device") as signer, \
                patch("gui.broadcast_transaction") as broadcaster:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(error.exception.code, 400)
        self.assertIn("Check signing devices", json.load(error.exception)["error"])
        signer.assert_not_called()
        broadcaster.assert_not_called()
        self.assertIs(self.app.prepared, reviewed)
        self.assertEqual(reviewed.checked_psbt().inputs[0].partial_sigs, {})
        self.assertIsNone(self.app.pending_broadcast_txid)

    def test_signing_refuses_a_binding_from_a_different_review(self):
        self.prepare_a_reviewed_transaction()
        binding = self.app.verified_signers
        self.app.verified_signers = ("stale-review", *binding[1:])
        reviewed = self.app.prepared
        with patch("gui.sign_psbt_with_device") as signer, \
                patch("gui.broadcast_transaction") as broadcaster:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(error.exception.code, 400)
        self.assertIn("Check signing devices", json.load(error.exception)["error"])
        signer.assert_not_called()
        broadcaster.assert_not_called()
        self.assertIs(self.app.prepared, reviewed)
        self.assertEqual(reviewed.checked_psbt().inputs[0].partial_sigs, {})
        self.assertIsNone(self.app.pending_broadcast_txid)

    def test_signing_refuses_when_device_reverification_fails(self):
        self.prepare_a_reviewed_transaction()
        reviewed = self.app.prepared
        with patch("gui.verify_signer_device", side_effect=ProbeError("device changed")) as verify, \
                patch("gui.sign_psbt_with_device") as signer, \
                patch("gui.broadcast_transaction") as broadcaster:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(error.exception.code, 400)
        verify.assert_called_once()
        signer.assert_not_called()
        broadcaster.assert_not_called()
        self.assertIs(self.app.prepared, reviewed)
        self.assertEqual(reviewed.checked_psbt().inputs[0].partial_sigs, {})
        self.assertIsNone(self.app.pending_broadcast_txid)

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

    def test_mutinynet_broadcast_uses_selected_chain_and_checks_checkpoint(self):
        result, keys = self.prepare_a_reviewed_transaction(chain="mutinynet")
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                           ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        final = self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        self.assertEqual(final["network"], "mutinynet")
        with patch("gui.verify_esplora") as verify, patch(
            "gui.broadcast_transaction", return_value=result["txid"]
        ) as send:
            sent = self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                                "confirm": True,
                                                "confirmed_txid": result["txid"]})
        verify.assert_called_once_with("mutinynet", "https://mutinynet.com/api")
        self.assertEqual(send.call_args.args[1], "mutinynet")
        self.assertIn("mutinynet.com", sent["explorer"])

    def test_jade_style_metadata_rewrite_keeps_only_verified_signatures(self):
        result, keys = self.prepare_a_reviewed_transaction(chain="mutinynet")
        original = E.PSBT.from_base64(self.app.prepared.psbt_base64)

        def rewrite_metadata(_executable, _chain, _type, _path, psbt_base64):
            packet = E.PSBT.from_base64(psbt_base64)
            packet.sign_with(keys[0])
            packet.inputs[0].witness_utxo.value += 1
            packet.outputs[0].unknown[b"\xfcdevice"] = b"untrusted"
            return packet.to_base64()

        with patch("gui.sign_psbt_with_device", side_effect=rewrite_metadata):
            first = self.post("/api/sign", {"preparation_id": "reviewed-1",
                                             "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(first["signers"], [1])
        retained = E.PSBT.from_base64(self.app.prepared.psbt_base64)
        self.assertEqual(retained.inputs[0].witness_utxo.value,
                         original.inputs[0].witness_utxo.value)
        self.assertEqual(retained.outputs[0].unknown, original.outputs[0].unknown)
        with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(keys[1])):
            second = self.post("/api/sign", {"preparation_id": "reviewed-1",
                                              "device_type": "trezor", "device_path": "usb:1"})
        self.assertTrue(second["complete"])
        self.assertEqual(self.post("/api/finalize", {"preparation_id": "reviewed-1"})["txid"],
                         result["txid"])

    def test_signing_requires_the_reviewed_transaction(self):
        self.prepare_a_reviewed_transaction()
        for bad in ("", "stale-id", None):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/sign", {"preparation_id": bad,
                                        "device_type": "jade", "device_path": "/dev/x"})
            self.assertEqual(err.exception.code, 400)

    def test_finalise_refuses_a_final_transaction_that_differs_from_the_review(self):
        """The final-vs-review backstop must hold at finalisation (CT-03).

        The review amounts are tampered server-side after signing; if the
        _check_final_review comparison were deleted, this finalise call would
        succeed instead of refusing.
        """
        _result, keys = self.prepare_a_reviewed_transaction()
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                            ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        reviewed = self.app.prepared
        tampered = dict(reviewed.review())
        tampered["amount_sats"] += 1
        self.app.prepared = replace(reviewed, review_items=tuple(tampered.items()))
        with self.assertRaises(HTTPError) as err:
            self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        self.assertEqual(err.exception.code, 400)
        self.assertIn("differs from the reviewed payment",
                      json.load(err.exception)["error"])

    def test_broadcast_refuses_a_final_transaction_that_differs_from_the_review(self):
        """The same backstop runs again inside the broadcast lock (CT-03)."""
        result, keys = self.prepare_a_reviewed_transaction()
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                            ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        reviewed = self.app.prepared
        tampered = dict(reviewed.review())
        tampered["fee_sats"] += 1
        self.app.prepared = replace(reviewed, review_items=tuple(tampered.items()))
        with patch("gui.broadcast_transaction") as send:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                             "confirm": True,
                                             "confirmed_txid": result["txid"]})
            send.assert_not_called()
        self.assertEqual(err.exception.code, 400)
        self.assertIn("differs from the reviewed payment",
                      json.load(err.exception)["error"])

    def test_money_endpoints_refuse_a_stale_review_id_by_name(self):
        """The review-id binding refuses by its own rule, not by accident (CT-05)."""
        self.prepare_a_reviewed_transaction()
        for route, payload in (
            ("/api/finalize", {"preparation_id": "stale-id"}),
            ("/api/broadcast", {"preparation_id": "stale-id", "confirm": True,
                                "confirmed_txid": self.app.prepared.txid}),
        ):
            with self.assertRaises(HTTPError) as err:
                self.post(route, payload)
            self.assertEqual(err.exception.code, 400)
            self.assertIn("Review the current transaction",
                          json.load(err.exception)["error"])

    def test_money_endpoints_refuse_after_the_balance_changes(self):
        """A newer scan generation invalidates the prepared payment (CT-05)."""
        self.prepare_a_reviewed_transaction()
        self.app.scan_generation += 1
        for route, payload in (
            ("/api/finalize", {"preparation_id": "reviewed-1"}),
            ("/api/broadcast", {"preparation_id": "reviewed-1", "confirm": True,
                                "confirmed_txid": self.app.prepared.txid}),
        ):
            with self.assertRaises(HTTPError) as err:
                self.post(route, payload)
            self.assertEqual(err.exception.code, 400)
            self.assertIn("wallet or balance changed",
                          json.load(err.exception)["error"])

    def test_a_stored_psbt_whose_contents_changed_is_refused(self):
        """checked_psbt re-validates the stored bytes on every read (CT-10)."""
        self.prepare_a_reviewed_transaction()
        text, _roots = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        other = build_unsigned_psbt(record, scan,
                                    layout.receive.derive(7).address(NETWORKS["test"]),
                                    50_000, 5, explorer)
        tampered = replace(self.app.prepared, psbt_base64=other["psbt_base64"])
        with self.assertRaisesRegex(WalletError, "prepared transaction changed"):
            tampered.checked_psbt()

    def test_a_signing_timeout_is_not_retried(self):
        """No automatic retry after a signing timeout (CT-11).

        The device-open half is pinned by the Ledger test above; this pins the
        timeout half of the same rule.
        """
        self.prepare_a_reviewed_transaction()
        with patch("gui.sign_psbt_with_device", side_effect=ProbeError(
                "HWI could not complete the request: timed out")) as signer:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
            self.assertEqual(err.exception.code, 400)
            signer.assert_called_once()

    def test_device_check_reports_slot_state_read_from_the_signed_psbt(self):
        """The signing screen draws one box per cosigner.

        The boxes must come from the server's reading of the signed PSBT rather
        than from anything the page remembers, so they cannot drift from what has
        actually been signed.
        """
        _result, keys = self.prepare_a_reviewed_transaction()
        detailed = {
            "statuses": ["Jade: signer 1 of 3 public xpub matched (not a signing test)."],
            "signable": [{"type": "jade", "path": "/dev/x", "model": "Jade",
                          "signer": 1, "keys": 3, "fingerprint": "aaaaaaaa"}],
        }
        with patch("gui.probe_devices_detailed", return_value=detailed):
            body = self.post("/api/devices", {"preparation_id": "reviewed-1"})
        self.assertEqual(body["threshold"], 2)
        self.assertEqual(body["keys"], 3)
        self.assertEqual(body["signed"], [], "nothing has signed yet")
        self.assertEqual([d["signer"] for d in body["signable"]], [1])

        with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(keys[0])):
            self.post("/api/sign", {"preparation_id": "reviewed-1",
                                    "device_type": "jade", "device_path": "/dev/x"})
        with patch("gui.probe_devices_detailed", return_value=detailed):
            body = self.post("/api/devices", {"preparation_id": "reviewed-1"})
        self.assertEqual(body["signed"], [1],
                         "the server must report the signer that actually signed")

    def test_ledger_open_failure_explains_recovery_without_retrying_signing(self):
        self.prepare_a_reviewed_transaction(chain="mutinynet")
        with patch("gui.sign_psbt_with_device", side_effect=ProbeError(
                "HWI reported a device error: open failed")) as signer:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "ledger", "device_path": "hid:1"})
        self.assertEqual(error.exception.code, 400)
        self.assertIn("Look for more devices", json.load(error.exception)["error"])
        signer.assert_called_once()

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
        self.assertIsNone(self.app.prepared)
        self.assertEqual(self.app.pending_broadcast_txid, txid)
        self.assertTrue(self.app.pending_broadcast_unknown)

        # Reopening the same file in this session cannot erase the uncertainty.
        text, _ = test_record(bsms_template=True)
        self.post("/api/import", {"chain": "testnet4", "text": text,
                                  "consent_explorer": True})
        self.assertEqual(self.app.pending_broadcast_txid, txid)
        self.assertTrue(self.app.pending_broadcast_unknown)

    def test_mismatched_broadcast_txid_is_unknown_and_blocks_retry(self):
        result, keys = self.prepare_a_reviewed_transaction()
        expected_txid = result["txid"]
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                            ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device", side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind, "device_path": path})
        payload = {"preparation_id": "reviewed-1", "confirm": True,
                   "confirmed_txid": expected_txid}
        with patch("gui.broadcast_transaction", return_value="11" * 32) as send:
            with self.assertRaises(HTTPError) as error:
                self.post("/api/broadcast", payload)
            self.assertEqual(error.exception.code, 409)
            body = json.load(error.exception)
            self.assertTrue(body["outcome_unknown"])
            self.assertIn(expected_txid, body["explorer"])
            with self.assertRaises(HTTPError) as retry:
                self.post("/api/broadcast", payload)
            self.assertEqual(retry.exception.code, 400)
            send.assert_called_once()
        self.assertIsNone(self.app.prepared)
        self.assertEqual(self.app.pending_broadcast_txid, expected_txid)
        self.assertTrue(self.app.pending_broadcast_unknown)

    def test_device_response_after_balance_refresh_cannot_attach_signature(self):
        _result, keys = self.prepare_a_reviewed_transaction()

        def refresh_while_device_signs(*args):
            self.app.scan_generation += 1
            return self.signing_device(keys[0])(*args)

        with patch("gui.sign_psbt_with_device", side_effect=refresh_while_device_signs):
            with self.assertRaises(HTTPError) as err:
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": "jade", "device_path": "/dev/x"})
        self.assertEqual(err.exception.code, 400)
        self.assertEqual(self.app.prepared.checked_psbt().inputs[0].partial_sigs, {})

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

    def test_mainnet_broadcast_requires_separate_per_transaction_opt_in(self):
        """The explicit mainnet gate is exercised after signing and finalization.

        This drives a real mainnet wallet through the whole flow, so the refusal
        is reached with the payment reviewed, signed by two devices and
        finalised - not short-circuited by an earlier guard. The earlier version
        of this test set app.chain to "main" while the prepared payment's chain
        was still testnet4, so _current_prepared raised "wallet or balance
        changed" first and the assertion passed without ever reaching the lock.
        """
        result, keys = self.prepare_a_reviewed_transaction(chain="main",
                                                           mainnet=True)
        for key, (kind, path) in zip(keys, (("jade", "/dev/x"),
                                            ("trezor", "webusb:1"))):
            with patch("gui.sign_psbt_with_device",
                       side_effect=self.signing_device(key)):
                self.post("/api/sign", {"preparation_id": "reviewed-1",
                                        "device_type": kind,
                                        "device_path": path})
        final = self.post("/api/finalize", {"preparation_id": "reviewed-1"})
        self.assertEqual(final["txid"], result["txid"])
        self.assertEqual(final["network"], "main")

        with patch("gui.broadcast_transaction",
                   return_value=result["txid"]) as send:
            with self.assertRaises(HTTPError) as err:
                self.post("/api/broadcast", {"preparation_id": "reviewed-1",
                                             "confirm": True,
                                             "confirmed_txid": result["txid"]})
            self.assertEqual(err.exception.code, 400)
            self.assertIn("separate mainnet warning",
                          json.load(err.exception)["error"])
            send.assert_not_called()
            sent = self.post("/api/broadcast", {
                "preparation_id": "reviewed-1", "confirm": True,
                "mainnet_opt_in": True, "confirmed_txid": result["txid"],
            })
        self.assertEqual(sent["txid"], result["txid"])
        self.assertTrue(send.call_args.kwargs["mainnet_opt_in"])

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

        def delayed_broadcast(*_args, **_kwargs):
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

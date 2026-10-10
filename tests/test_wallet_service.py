"""Only synthetic public test-wallet data; no real BSMS export is checked in."""

import http.server
import io
import ssl
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from embit import bip32, psbt, transaction
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from probe import ProbeError, load_bsms, parse_bsms
from network_config import NETWORKS as CHAIN_CONFIGS
from test_probe import sparrow_record, test_record
from wallet_service import (
    BroadcastOutcomeUnknown, WalletError, broadcast_transaction, build_unsigned_psbt,
    check_fee_safety, estimate_fee_preview,
    explorer_get, scan_wallet, wallet_layout,
    wallet_summary,
)


class BroadcastOutcomeTests(unittest.TestCase):
    def test_transport_failure_is_unknown_not_definite_rejection(self):
        with patch("wallet_service.urlopen", side_effect=URLError("timeout")):
            with self.assertRaisesRegex(BroadcastOutcomeUnknown, "Do not send"):
                broadcast_transaction("00" * 50)

    def test_a_server_error_is_unknown_not_a_definite_rejection(self):
        """A 5xx can arrive after the node already accepted the transaction.

        Reporting a refusal would state something the app cannot know, and would
        leave the payment retryable without the pending-payment pause in gui.py
        being armed.
        """
        error = HTTPError("https://example.invalid/api/tx", 502, "Bad Gateway",
                          None, None)
        with patch("wallet_service.urlopen", side_effect=error):
            with self.assertRaisesRegex(BroadcastOutcomeUnknown, "result is unknown"):
                broadcast_transaction("00" * 50)

    def test_a_client_rejection_remains_a_definite_refusal(self):
        """A 4xx carrying a node rejection keeps its precise refusal message."""
        error = HTTPError("https://example.invalid/api/tx", 400, "Bad Request",
                          None, None)
        with patch("wallet_service.urlopen", side_effect=error):
            with self.assertRaises(WalletError) as caught:
                broadcast_transaction("00" * 50)
        self.assertNotIsInstance(caught.exception, BroadcastOutcomeUnknown)
        self.assertIn("refused", str(caught.exception))

    def test_mainnet_broadcast_requires_explicit_opt_in_at_engine_boundary(self):
        with patch("wallet_service.urlopen") as send:
            with self.assertRaisesRegex(WalletError, "Explicit mainnet"):
                broadcast_transaction("00" * 50, chain="main")
        send.assert_not_called()

    def test_mainnet_broadcast_uses_selected_esplora_after_opt_in(self):
        response = io.BytesIO(b"a" * 64)
        with patch("wallet_service.urlopen", return_value=response) as send:
            result = broadcast_transaction(
                "00" * 50, chain="main", base_url="https://explorer.example/api",
                mainnet_opt_in=True,
            )
        self.assertEqual(result, "a" * 64)
        self.assertEqual(send.call_args.args[0].full_url,
                         "https://explorer.example/api/tx")


def mainnet_roots():
    """The synthetic signing roots behind mainnet_record(). Test keys only."""
    return [bip32.HDKey.from_seed(bytes([i]) * 32) for i in (1, 2, 3)]


def mainnet_record(suffix="/<0;1>/*"):
    """Synthetic keys only. No real or uploaded wallet data enters tests."""
    roots = mainnet_roots()
    keys = [
        f"[{root.my_fingerprint.hex()}/48h/0h/0h/2h]"
        f"{root.derive('m/48h/0h/0h/2h').to_public().to_base58()}{suffix}"
        for root in roots
    ]
    descriptor = f"wsh(sortedmulti(2,{','.join(keys)}))"
    receive = Descriptor.from_string(
        descriptor.replace("/*", "/0/*") if suffix == "/*" else descriptor
    ).branch(0).derive(0).address(NETWORKS["main"])
    return f"BSMS 1.0\n{descriptor}#{checksum(descriptor)}\nNo path restrictions\n{receive}\n"


class PendingSpendTests(unittest.TestCase):
    """Mempool spends explain UTXO totals but pause the next payment."""

    def setUp(self):
        self.text, _ = test_record(bsms_template=True)
        self.wallet = parse_bsms(self.text)
        self.layout = wallet_layout(self.wallet)
        self.receive = self.layout.receive.derive(0).address(NETWORKS["test"])

    def stub(self, *, mempool_spent, utxos):
        def get(path, *, text=False):
            if path == f"/address/{self.receive}/utxo":
                return utxos
            if path.endswith("/utxo"):
                return []
            if path.startswith("/address/"):
                used = path == f"/address/{self.receive}"
                return {
                    "chain_stats": {"funded_txo_sum": 6000 if used else 0,
                                    "spent_txo_sum": 0, "tx_count": 1 if used else 0},
                    "mempool_stats": {"funded_txo_sum": 0,
                                      "spent_txo_sum": mempool_spent if used else 0,
                                      "tx_count": 1 if (used and mempool_spent) else 0},
                }
            raise AssertionError(path)
        return get

    def test_a_confirmed_output_spent_in_the_mempool_is_not_corruption(self):
        result = scan_wallet(self.wallet, self.stub(mempool_spent=6000, utxos=[]))
        self.assertTrue(result["utxo_consistent"])
        self.assertTrue(result["pending_outgoing"])
        self.assertEqual(result["confirmed_sats"], 6000)
        self.assertEqual(result["pending_delta_sats"], -6000)

    def test_pending_outgoing_pauses_preview_and_prepare_even_with_other_utxos(self):
        result = scan_wallet(self.wallet, self.stub(mempool_spent=1000, utxos=[
            {"txid": "aa" * 32, "vout": 0, "value": 5000,
             "status": {"confirmed": True}},
        ]))
        self.assertTrue(result["utxo_consistent"])
        self.assertTrue(result["pending_outgoing"])
        with self.assertRaisesRegex(WalletError, "waiting for one confirmation"):
            estimate_fee_preview(self.wallet, result, True)
        with self.assertRaisesRegex(WalletError, "waiting for one confirmation"):
            build_unsigned_psbt(self.wallet, result, self.receive, None,
                                get=self.stub(mempool_spent=1000, utxos=[]),
                                send_all=True)

    def test_pending_incoming_does_not_pause_an_existing_confirmed_output(self):
        result = scan_wallet(self.wallet, self.stub(mempool_spent=0, utxos=[
            {"txid": "aa" * 32, "vout": 0, "value": 6000,
             "status": {"confirmed": True}},
        ]))
        self.assertFalse(result["pending_outgoing"])

    def test_utxos_exceeding_the_totals_is_still_refused(self):
        # The address totals say 6,000 but the UTXO list offers 12,000: the explorer
        # is reporting money it does not count, and nothing should be built on it.
        result = scan_wallet(self.wallet, self.stub(
            mempool_spent=0,
            utxos=[{"txid": "aa" * 32, "vout": 0, "value": 12_000,
                    "status": {"confirmed": True}}]))
        self.assertFalse(result["utxo_consistent"])

    def test_an_unexplained_shortfall_is_still_refused(self):
        result = scan_wallet(self.wallet, self.stub(mempool_spent=100, utxos=[]))
        self.assertFalse(result["utxo_consistent"])


class WalletServiceTests(unittest.TestCase):
    def setUp(self):
        # Exercise the standard BSMS descriptor-template form used to declare
        # separate receive and change paths.
        self.text, _ = test_record(bsms_template=True)
        self.wallet = parse_bsms(self.text)
        self.layout = wallet_layout(self.wallet)
        from embit.networks import NETWORKS
        self.receive = self.layout.receive.derive(0).address(NETWORKS["test"])
        self.change = self.layout.change.derive(0).address(NETWORKS["test"])
        self.previous = transaction.Transaction(
            vin=[transaction.TransactionInput(bytes.fromhex("aa" * 32), 0)],
            vout=[transaction.TransactionOutput(
                6000, self.layout.receive.derive(0).script_pubkey()
            )],
        )
        self.txid = self.previous.txid().hex()

    def fake_get(self, path, *, text=False):
        if path == f"/tx/{self.txid}/hex":
            return self.previous.serialize().hex()
        if path == f"/address/{self.receive}/utxo":
            return [{"txid": self.txid, "vout": 0, "value": 6000,
                     "status": {"confirmed": True}}]
        if path.endswith("/utxo"):
            return []
        if path.startswith("/address/"):
            used = path == f"/address/{self.receive}"
            return {
                "chain_stats": {"funded_txo_sum": 6000 if used else 0,
                                "spent_txo_sum": 0, "tx_count": 1 if used else 0},
                "mempool_stats": {"funded_txo_sum": 0, "spent_txo_sum": 0, "tx_count": 0},
            }
        raise AssertionError(path)

    def test_memory_import_matches_file_import_and_shows_three_public_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wallet.bsms"
            path.write_text(self.text)
            self.assertEqual(load_bsms(path).reference_address, self.wallet.reference_address)
        view = wallet_summary(self.wallet)
        self.assertEqual(len(view["keys"]), 3)
        self.assertEqual(view["receive_address"], self.receive)
        self.assertEqual(view["change_address"], self.change)
        self.assertEqual(view["warning"], "")
        self.assertTrue(view["can_prepare"])
        self.assertTrue(all(key["public_key"].startswith("tpub") for key in view["keys"]))

    def test_scan_finds_synthetic_balance_on_receive_branch(self):
        result = scan_wallet(self.wallet, self.fake_get)
        self.assertEqual(result["confirmed_sats"], 6000)
        self.assertEqual(result["observed_sats"], 6000)
        self.assertEqual(len(result["utxos"]), 1)
        self.assertEqual(result["scanned"], 50)
        self.assertFalse(result["coverage_limited"])
        self.assertEqual(result["used_change_indices"], [])
        address = next(item for item in result["addresses"] if item["address"] == self.receive)
        self.assertEqual(address["confirmed"], 6000)
        self.assertEqual(address["pending_delta"], 0)

    def test_fee_preview_is_conservative_and_uses_confirmed_utxo_count(self):
        data = scan_wallet(self.wallet, self.fake_get)
        preview = estimate_fee_preview(self.wallet, data, send_all=False)
        self.assertEqual(preview["input_count"], 1)
        self.assertEqual(preview["estimated_vbytes"], 202)
        self.assertIn("all confirmed", preview["method"])
        send_all = estimate_fee_preview(self.wallet, data, send_all=True)
        self.assertEqual(send_all["estimated_vbytes"], 159)

    def test_preview_enforces_the_fee_ceiling_for_a_partial_send(self):
        """The builder applies the ceiling unconditionally, so the preview must too.

        A preview that displays a fee the builder will then refuse is worse than
        no preview at all. Four inputs at 25 sat/vB costs more than the ceiling.
        """
        data = scan_wallet(self.wallet, self.fake_get)
        costly = {**data, "utxos": data["utxos"] + [data["utxos"][0]] * 3,
                  "confirmed_sats": 24_000}
        with self.assertRaisesRegex(WalletError, "safety ceiling"):
            estimate_fee_preview(self.wallet, costly, False, amount=8_000,
                                 fee_rate=25)

    def test_unsigned_psbt_has_correct_destination_change_and_prevout(self):
        from embit.networks import NETWORKS
        data = scan_wallet(self.wallet, self.fake_get)
        recipient = self.layout.receive.derive(1).address(NETWORKS["test"])
        result = build_unsigned_psbt(
            self.wallet, data, recipient, 1000, 2, self.fake_get
        )
        packet = psbt.PSBT.from_base64(result["psbt_base64"])
        self.assertEqual(len(packet.inputs), 1)
        self.assertEqual(packet.tx.vout[0].value, 1000)
        self.assertEqual(packet.tx.vout[1].value, result["change_sats"])
        self.assertEqual(result["fee_sats"], 404)
        self.assertEqual(result["estimated_signed_vbytes"], 202)
        self.assertEqual(packet.tx.vout[1].script_pubkey.address(NETWORKS["test"]),
                         self.change)
        self.assertEqual(packet.fee(), result["fee_sats"])
        self.assertIsNotNone(packet.inputs[0].witness_script)
        self.assertEqual(len(packet.inputs[0].bip32_derivations), 3)
        self.assertEqual(len(packet.outputs[1].bip32_derivations), 3)
        self.assertEqual(packet.inputs[0].partial_sigs, {})
        with self.assertRaisesRegex(WalletError, "network differ"):
            build_unsigned_psbt(self.wallet, {**data, "network": None},
                                recipient, 1000, 2, self.fake_get)
        with self.assertRaisesRegex(WalletError, "disagree"):
            build_unsigned_psbt(self.wallet, {**data, "utxo_consistent": False},
                                recipient, 1000, 2, self.fake_get)

    def test_trailing_garbage_in_explorer_transaction_has_clear_refusal(self):
        data = scan_wallet(self.wallet, self.fake_get)

        def malformed(path, *, text=False):
            value = self.fake_get(path, text=text)
            return value + "aa" if path.endswith("/hex") else value

        with self.assertRaisesRegex(WalletError, "invalid previous transaction"):
            build_unsigned_psbt(self.wallet, data, self.receive, 1000, 2, malformed)

    def test_send_all_deducts_fee_uses_every_confirmed_output_and_has_no_change(self):
        data = scan_wallet(self.wallet, self.fake_get)
        recipient = self.layout.receive.derive(1).address(NETWORKS["test"])
        result = build_unsigned_psbt(self.wallet, data, recipient, None, 2,
                                     self.fake_get, send_all=True)
        packet = psbt.PSBT.from_base64(result["psbt_base64"])
        self.assertEqual(result["amount_sats"], 5682)
        self.assertEqual(result["fee_sats"], 318)
        self.assertEqual(result["estimated_signed_vbytes"], 159)
        self.assertEqual(result["total_spend_sats"], data["confirmed_sats"])
        self.assertEqual(result["remaining_confirmed_sats"], 0)
        self.assertTrue(result["send_all"])
        self.assertIsNone(result["change_address"])
        self.assertEqual(result["change_sats"], 0)
        self.assertEqual(len(packet.tx.vout), 1)
        self.assertEqual(packet.tx.vout[0].value, 5682)
        self.assertEqual(packet.fee(), 318)
        self.assertEqual(packet.inputs[0].partial_sigs, {})
        pending = {**data, "utxos": data["utxos"] + [{
            **data["utxos"][0], "value": 2000,
            "status": {"confirmed": False},
        }]}
        pending_result = build_unsigned_psbt(
            self.wallet, pending, recipient, None, 2, self.fake_get, send_all=True
        )
        self.assertEqual(pending_result["total_spend_sats"], 6000)
        self.assertEqual(psbt.PSBT.from_base64(pending_result["psbt_base64"]).fee(), 318)
        with self.assertRaisesRegex(WalletError, "separate amount"):
            build_unsigned_psbt(self.wallet, data, recipient, 6000, 2,
                                self.fake_get, send_all=True)
        with self.assertRaisesRegex(WalletError, "refresh"):
            build_unsigned_psbt(self.wallet, {**data, "confirmed_sats": 7000},
                                recipient, None, 2, self.fake_get, send_all=True)
        with self.assertRaisesRegex(WalletError, "range"):
            build_unsigned_psbt(self.wallet, {**data, "range_limited": True},
                                recipient, None, 2, self.fake_get, send_all=True)

    def test_send_all_requires_every_confirmed_input_and_respects_fee_ceiling(self):
        data = scan_wallet(self.wallet, self.fake_get)
        recipient = self.layout.receive.derive(1).address(NETWORKS["test"])
        second = transaction.Transaction(
            vin=[transaction.TransactionInput(bytes.fromhex("cc" * 32), 0)],
            vout=[transaction.TransactionOutput(
                4000, self.layout.receive.derive(0).script_pubkey()
            )],
        )
        txid = second.txid().hex()
        data["utxos"].append({
            **data["utxos"][0], "txid": txid, "value": 4000,
        })
        data["confirmed_sats"] = 10_000
        def get(path, *, text=False):
            if path == f"/tx/{txid}/hex":
                return second.serialize().hex()
            return self.fake_get(path, text=text)
        result = build_unsigned_psbt(self.wallet, data, recipient, None, 2, get,
                                     send_all=True)
        packet = psbt.PSBT.from_base64(result["psbt_base64"])
        self.assertEqual(len(packet.inputs), 2)
        self.assertEqual(len(packet.outputs), 1)
        self.assertEqual(result["fee_sats"], 528)
        self.assertEqual(result["amount_sats"], 9472)
        self.assertEqual(packet.fee(), 528)
        costly = {**data, "utxos": data["utxos"] + [data["utxos"][0]] * 2,
                  "confirmed_sats": 22_000}
        with self.assertRaisesRegex(WalletError, "fee safety ceiling"):
            build_unsigned_psbt(self.wallet, costly, recipient, None, 25, get,
                                send_all=True)
        with self.assertRaisesRegex(WalletError, "spendable output"):
            build_unsigned_psbt(self.wallet, {**data, "utxos": [{
                **data["utxos"][0], "value": 4000,
            }], "confirmed_sats": 4000},
                                recipient, None, 25, self.fake_get, send_all=True)

    def test_one_explorer_client_routes_by_selected_network(self):
        class Response:
            """A stream, not a static buffer: reading past the body returns b"".

            CT-84 reads in bounded chunks so it can re-check its deadline between
            them, so a stand-in whose ``read`` never drains would look like an
            endless body.
            """
            length = 2
            def __init__(self):
                self.remaining = b"{}"
            def __enter__(self):
                self.remaining = b"{}"
                return self
            def __exit__(self, *_args):
                pass
            def read(self, amount=-1):
                if amount is None or amount < 0:
                    amount = len(self.remaining)
                piece, self.remaining = self.remaining[:amount], self.remaining[amount:]
                return piece
        with patch("wallet_service.urlopen", return_value=Response()) as fetch:
            for chain, config in CHAIN_CONFIGS.items():
                self.assertEqual(explorer_get("/blocks/tip", chain=chain), {})
                self.assertEqual(fetch.call_args.args[0].full_url,
                                 config.explorer_url + "/blocks/tip")
        self.assertEqual(fetch.call_count, len(CHAIN_CONFIGS))

    def test_explorer_rate_limit_is_retried_without_disclosing_address(self):
        private_path = "/address/tb1qtestaddressnotforerrors"
        error = HTTPError("https://example.org" + private_path, 429, "rate limit", {}, None)
        with patch("wallet_service.urlopen", side_effect=error) as fetch, patch(
            "wallet_service.time.sleep"
        ) as pause:
            with self.assertRaises(WalletError) as caught:
                explorer_get(private_path, chain="testnet4")
        self.assertEqual(fetch.call_count, 2)
        pause.assert_called_once()
        self.assertIn("HTTP 429", str(caught.exception))
        self.assertNotIn("tb1qtestaddress", str(caught.exception))

    def test_explorer_tls_failure_has_actionable_safe_message(self):
        error = URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))
        with patch("wallet_service.urlopen", side_effect=error) as fetch:
            with self.assertRaises(WalletError) as caught:
                explorer_get("/address/tb1qtestaddressnotforerrors")
        self.assertEqual(fetch.call_count, 1)
        self.assertIn("HTTPS certificate", str(caught.exception))
        self.assertNotIn("tb1qtestaddress", str(caught.exception))

    def test_rejects_mainnet_destination_and_insufficient_funds(self):
        data = scan_wallet(self.wallet, self.fake_get)
        with self.assertRaisesRegex(WalletError, "tb1"):
            build_unsigned_psbt(self.wallet, data, "bc1qincorrect", 1000, 2, self.fake_get)
        with self.assertRaisesRegex(WalletError, "Not enough"):
            build_unsigned_psbt(self.wallet, data, self.receive, 5999, 2, self.fake_get)

    def test_pending_balance_is_visible_but_not_spendable_yet(self):
        def pending_get(path, *, text=False):
            response = self.fake_get(path, text=text)
            if path == f"/address/{self.receive}":
                response["mempool_stats"] = response["chain_stats"]
                response["chain_stats"] = {
                    "funded_txo_sum": 0, "spent_txo_sum": 0, "tx_count": 0
                }
            if path == f"/address/{self.receive}/utxo":
                response[0]["status"]["confirmed"] = False
            return response
        data = scan_wallet(self.wallet, pending_get)
        self.assertEqual(data["confirmed_sats"], 0)
        self.assertEqual(data["observed_sats"], 6000)
        address = next(item for item in data["addresses"] if item["address"] == self.receive)
        self.assertEqual(address["confirmed"] + address["pending_delta"], 6000)
        with self.assertRaisesRegex(WalletError, "Not enough confirmed"):
            build_unsigned_psbt(self.wallet, data, self.receive, 1000, 2, pending_get)

    def test_rejects_mismatched_reference_before_scan(self):
        lines = self.text.splitlines()
        lines[3] = self.change
        with self.assertRaisesRegex(WalletError, "Reference address"):
            wallet_layout(parse_bsms("\n".join(lines) + "\n"))

    def test_standard_bip48_export_uses_change_on_both_wildcard_shapes(self):
        """The one-file standard flow is shared by Testnet4 and Mutinynet."""
        for short in (False, True):
            with self.subTest(short=short):
                record = parse_bsms(test_record(short_path=short)[0])
                layout = wallet_layout(record)
                self.assertIsNotNone(layout.change)
                summary = wallet_summary(record)
                self.assertTrue(summary["can_prepare"])
                self.assertTrue(summary["can_send_all"])
                self.assertTrue(summary["change_assumed"])
                self.assertIsNotNone(summary["change_address"])
                scan = scan_wallet(record, self.fake_get)
                self.assertEqual(scan["network"], "testnet4")

    def test_equivalent_nunchuk_and_sparrow_exports_derive_same_change(self):
        # Synthetic versions of the owner's two encodings of one wallet.
        nunchuk = wallet_layout(parse_bsms(test_record(short_path=True)[0]))
        sparrow = wallet_layout(parse_bsms(sparrow_record()[0]))
        self.assertTrue(nunchuk.change_assumed)
        self.assertTrue(sparrow.change_declared)
        for index in range(20):
            with self.subTest(index=index):
                self.assertEqual(nunchuk.receive.derive(index).script_pubkey(),
                                 sparrow.receive.derive(index).script_pubkey())
                self.assertEqual(nunchuk.change.derive(index).script_pubkey(),
                                 sparrow.change.derive(index).script_pubkey())

    def test_mainnet_explicit_branches_build_only_unsigned_psbt(self):
        record = parse_bsms(mainnet_record())
        self.assertTrue(wallet_summary(record)["can_prepare"])
        layout = wallet_layout(record)
        receive = layout.receive.derive(0).address(NETWORKS["main"])
        recipient = layout.receive.derive(1).address(NETWORKS["main"])
        previous = transaction.Transaction(
            vin=[transaction.TransactionInput(bytes.fromhex("bb" * 32), 0)],
            vout=[transaction.TransactionOutput(
                100_000, layout.receive.derive(0).script_pubkey()
            )],
        )
        txid = previous.txid().hex()
        def fake_get(path, *, text=False):
            if path == f"/tx/{txid}/hex":
                return previous.serialize().hex()
            if path == f"/address/{receive}/utxo":
                return [{"txid": txid, "vout": 0, "value": 100_000,
                         "status": {"confirmed": True}}]
            if path.endswith("/utxo"):
                return []
            if path.startswith("/address/"):
                used = path == f"/address/{receive}"
                return {
                    "chain_stats": {"funded_txo_sum": 100_000 if used else 0,
                                    "spent_txo_sum": 0, "tx_count": 1 if used else 0},
                    "mempool_stats": {"funded_txo_sum": 0, "spent_txo_sum": 0,
                                     "tx_count": 0},
                }
            raise AssertionError(path)
        data = scan_wallet(record, fake_get)
        self.assertEqual(data["network"], "main")
        self.assertEqual(data["source"], "https://mempool.space/api")
        self.assertTrue(data["utxo_consistent"])
        packet_data = build_unsigned_psbt(record, data, recipient, 10_000, 2, fake_get)
        packet = psbt.PSBT.from_base64(packet_data["psbt_base64"])
        self.assertEqual(packet.tx.vout[0].script_pubkey.address(NETWORKS["main"]), recipient)
        self.assertEqual(packet.tx.vout[1].script_pubkey.address(NETWORKS["main"]),
                         layout.change.derive(0).address(NETWORKS["main"]))
        self.assertEqual(packet.fee(), packet_data["fee_sats"])
        self.assertEqual(packet.inputs[0].partial_sigs, {})
        sweep = build_unsigned_psbt(record, data, recipient, None, 2, fake_get,
                                    send_all=True)
        sweep_packet = psbt.PSBT.from_base64(sweep["psbt_base64"])
        self.assertEqual(len(sweep_packet.tx.vout), 1)
        self.assertEqual(sweep["total_spend_sats"], 100_000)
        self.assertEqual(sweep["remaining_confirmed_sats"], 0)
        with self.assertRaisesRegex(WalletError, "bc1"):
            build_unsigned_psbt(record, data, self.receive, 10_000, 2, fake_get)
        with self.assertRaisesRegex(WalletError, "network differ"):
            build_unsigned_psbt(record, {**data, "network": "testnet4"},
                                recipient, 10_000, 2, fake_get)
        with self.assertRaisesRegex(WalletError, "disagree"):
            build_unsigned_psbt(record, {**data, "utxo_consistent": False},
                                recipient, 10_000, 2, fake_get)

    def test_mainnet_standard_bip48_export_uses_change_without_extra_file(self):
        for suffix in ("/0/*", "/*"):
            with self.subTest(suffix=suffix):
                record = parse_bsms(mainnet_record(suffix))
                layout = wallet_layout(record)
                self.assertIsNotNone(layout.change)
                summary = wallet_summary(record)
                self.assertTrue(summary["can_prepare"])
                self.assertTrue(summary["change_assumed"])
                self.assertTrue(summary["can_send_all"])
        lines = mainnet_record().splitlines()
        other = parse_bsms(mainnet_record("/0/*"))
        lines[3] = other.descriptor.derive(1).address(NETWORKS["main"])
        with self.assertRaisesRegex(WalletError, "Reference address"):
            wallet_layout(parse_bsms("\n".join(lines) + "\n"))
        lines = mainnet_record().splitlines()
        descriptor = lines[1].split("#")[0].replace("/48h/0h/", "/48h/1h/")
        lines[1] = descriptor + "#" + checksum(descriptor)
        with self.assertRaisesRegex(ProbeError, "coin type"):
            parse_bsms("\n".join(lines) + "\n")

    def test_bare_wildcard_matching_directly_does_not_prove_bip48_change(self):
        # With a bare /*, the file's first address can be xpub/0 rather than
        # BIP48's xpub/0/0. An m/48 origin alone must not enable /1/* change.
        lines = mainnet_record("/*").splitlines()
        descriptor = lines[1].split("#", 1)[0]
        lines[3] = Descriptor.from_string(descriptor).derive(0).address(NETWORKS["main"])
        record = parse_bsms("\n".join(lines) + "\n")
        self.assertEqual(record.reference_status, "verified")
        layout = wallet_layout(record)
        self.assertIsNone(layout.change)
        self.assertFalse(wallet_summary(record)["can_prepare"])
        lines[2] = "/0/*,/1/*"
        with self.assertRaisesRegex(WalletError, "restriction disagrees"):
            wallet_layout(parse_bsms("\n".join(lines) + "\n"))

    def test_fee_safety_stops_extreme_fee_and_flags_unusual_rates(self):
        self.assertEqual(check_fee_safety(540, 1000, 2), "")
        self.assertIn("Unusually high", check_fee_safety(2700, 1000, 10))
        with self.assertRaisesRegex(WalletError, "10,000-sat"):
            check_fee_safety(10_001, 100_000, 25)


class _DribbleHandler(http.server.BaseHTTPRequestHandler):
    """Answers every request by dripping bytes far slower than the response.

    One byte every 50 ms never trips a socket timeout armed for a whole second,
    which is exactly the CT-84 scenario: only the caller's total deadline can
    end the call.
    """

    def log_message(self, *_args):
        pass

    def do_GET(self):
        self._dribble()

    def do_POST(self):
        self._dribble()

    def _dribble(self):
        self.send_response(200)
        self.send_header("Content-Length", "4096")
        self.end_headers()
        for _ in range(30):
            try:
                self.wfile.write(b"x")
                self.wfile.flush()
            except OSError:
                return
            time.sleep(0.05)


class OutboundDeadlineTests(unittest.TestCase):
    """CT-84 wiring: the explorer and broadcaster callers really set a budget."""

    def setUp(self):
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _DribbleHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}/api"

    def test_a_dribbling_explorer_returns_within_its_deadline(self):
        # `wallet_service.time` is replaced rather than `time.sleep`, because
        # patching the global sleep would also still the dribble server and the
        # read would finish instantly -- a test that cannot fail.
        with patch("wallet_service.EXPLORER_TIMEOUT_SECONDS", 1.0), \
                patch("wallet_service.time"):
            started = time.monotonic()
            with self.assertRaises(WalletError) as caught:
                explorer_get("/blocks/tip", chain="testnet4", base_url=self.base)
            elapsed = time.monotonic() - started
        self.assertLess(elapsed, 4.0, "the explorer call outlived its deadline")
        # Both attempts must have hit the deadline. A truncated reply would end
        # in "returned invalid data" instead, which is what a dropped deadline
        # looks like from here.
        self.assertIn("Could not connect", str(caught.exception))

    def test_a_dribbling_broadcaster_gives_up_within_its_deadline(self):
        # A withhold-then-answer server is the dangerous case: the transaction
        # may already be relayed, so the outcome must be reported as unknown
        # rather than as a refusal, and it must not hang forever.
        with patch("wallet_service.BROADCAST_TIMEOUT_SECONDS", 1.0):
            started = time.monotonic()
            with self.assertRaises(BroadcastOutcomeUnknown):
                broadcast_transaction("00" * 50, "testnet4", self.base)
            elapsed = time.monotonic() - started
        self.assertLess(elapsed, 4.0, "the broadcast call outlived its deadline")


if __name__ == "__main__":
    unittest.main()

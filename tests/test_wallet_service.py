"""Only synthetic public test-wallet data; no real BSMS export is checked in."""

import tempfile
import unittest
from pathlib import Path

from embit import psbt, transaction

from probe import load_bsms, parse_bsms
from test_probe import test_record
from wallet_service import (
    WalletError, build_unsigned_psbt, scan_wallet, wallet_layout, wallet_summary,
)


class WalletServiceTests(unittest.TestCase):
    def setUp(self):
        self.text, _ = test_record(short_path=True)
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
        self.assertIn("inferred", view["warning"])
        self.assertTrue(all(key["public_key"].startswith("tpub") for key in view["keys"]))

    def test_scan_finds_synthetic_balance_on_receive_branch(self):
        result = scan_wallet(self.wallet, self.fake_get)
        self.assertEqual(result["confirmed_sats"], 6000)
        self.assertEqual(result["observed_sats"], 6000)
        self.assertEqual(len(result["utxos"]), 1)
        self.assertEqual(result["scanned"], 50)
        self.assertFalse(result["coverage_limited"])
        self.assertEqual(result["used_change_indices"], [])

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
        self.assertEqual(packet.tx.vout[1].script_pubkey.address(NETWORKS["test"]),
                         self.change)
        self.assertEqual(packet.fee(), result["fee_sats"])
        self.assertIsNotNone(packet.inputs[0].witness_script)
        self.assertEqual(len(packet.inputs[0].bip32_derivations), 3)
        self.assertEqual(len(packet.outputs[1].bip32_derivations), 3)
        self.assertEqual(packet.inputs[0].partial_sigs, {})

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
        with self.assertRaisesRegex(WalletError, "Not enough confirmed"):
            build_unsigned_psbt(self.wallet, data, self.receive, 1000, 2, pending_get)

    def test_rejects_mismatched_reference_before_scan(self):
        lines = self.text.splitlines()
        lines[3] = self.change
        with self.assertRaisesRegex(WalletError, "Reference address"):
            wallet_layout(parse_bsms("\n".join(lines) + "\n"))


if __name__ == "__main__":
    unittest.main()
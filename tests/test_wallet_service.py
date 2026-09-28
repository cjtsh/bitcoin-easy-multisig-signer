"""Only synthetic public test-wallet data; no real BSMS export is checked in."""

import tempfile
import unittest
from pathlib import Path

from embit import bip32, psbt, transaction
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from probe import ProbeError, load_bsms, parse_bsms
from test_probe import test_record
from wallet_service import (
    WalletError, build_unsigned_psbt, check_fee_safety, scan_wallet, wallet_layout,
    wallet_summary,
)

def mainnet_record(suffix="/<0;1>/*"):
    """Synthetic keys only. No real or uploaded wallet data enters tests."""
    roots = [bip32.HDKey.from_seed(bytes([i]) * 32) for i in (1, 2, 3)]
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
        address = next(item for item in result["addresses"] if item["address"] == self.receive)
        self.assertEqual(address["confirmed"], 6000)
        self.assertEqual(address["pending_delta"], 0)

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
        address = next(item for item in data["addresses"] if item["address"] == self.receive)
        self.assertEqual(address["confirmed"] + address["pending_delta"], 6000)
        with self.assertRaisesRegex(WalletError, "Not enough confirmed"):
            build_unsigned_psbt(self.wallet, data, self.receive, 1000, 2, pending_get)

    def test_rejects_mismatched_reference_before_scan(self):
        lines = self.text.splitlines()
        lines[3] = self.change
        with self.assertRaisesRegex(WalletError, "Reference address"):
            wallet_layout(parse_bsms("\n".join(lines) + "\n"))

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
        with self.assertRaisesRegex(WalletError, "bc1"):
            build_unsigned_psbt(record, data, self.receive, 10_000, 2, fake_get)
        with self.assertRaisesRegex(WalletError, "network differ"):
            build_unsigned_psbt(record, {**data, "network": "testnet4"},
                                recipient, 10_000, 2, fake_get)
        with self.assertRaisesRegex(WalletError, "disagree"):
            build_unsigned_psbt(record, {**data, "utxo_consistent": False},
                                recipient, 10_000, 2, fake_get)

    def test_mainnet_receive_only_and_inferred_branches_cannot_prepare(self):
        for suffix in ("/0/*", "/*"):
            with self.subTest(suffix=suffix):
                record = parse_bsms(mainnet_record(suffix))
                layout = wallet_layout(record)
                self.assertIsNone(layout.change)
                self.assertFalse(wallet_summary(record)["can_prepare"])
                with self.assertRaisesRegex(WalletError, "explicit 2-of-3"):
                    build_unsigned_psbt(record, {"network": "main", "utxo_consistent": True},
                                        record.reference_address, 1000)
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

    def test_fee_safety_stops_extreme_fee_and_flags_unusual_rates(self):
        self.assertEqual(check_fee_safety(540, 1000, 2), "")
        self.assertIn("Unusually high", check_fee_safety(2700, 1000, 10))
        with self.assertRaisesRegex(WalletError, "10,000-sat"):
            check_fee_safety(10_001, 100_000, 25)


if __name__ == "__main__":
    unittest.main()
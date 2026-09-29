"""Change is used only when the wallet export declares it.

Synthetic keys only; no wallet export is ever checked in.
"""

import unittest

from embit import psbt
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from fake_explorer import FakeExplorer, three_output_wallet
from probe import ProbeError, parse_bsms
from test_probe import test_record
from wallet_service import (
    WalletError, build_unsigned_psbt, estimate_fee_preview, scan_wallet,
    wallet_layout, wallet_summary,
)


class ChangeBranchTests(unittest.TestCase):
    """A receive-only export must not demand a technical assertion from the owner."""

    def test_receive_only_wallet_only_allows_no_change_send_all(self):
        record = parse_bsms(test_record(short_path=True)[0])  # bare /* export
        layout = wallet_layout(record)
        summary = wallet_summary(record)
        self.assertFalse(summary["can_prepare"])
        self.assertTrue(summary["can_send_all"])
        self.assertIsNone(layout.change)
        self.assertIsNone(summary["change_address"])
        self.assertIn("send all", summary["prepare_reason"].lower())

    def test_path_qualified_receive_only_wallet_does_not_guess_change(self):
        record = parse_bsms(test_record()[0])  # /0/* only
        summary = wallet_summary(record)
        self.assertFalse(summary["can_prepare"])
        self.assertIsNone(wallet_layout(record).change)

    def test_receive_only_wallet_can_sweep_without_creating_change(self):
        record = parse_bsms(test_record(short_path=True)[0])
        layout = wallet_layout(record)
        network = NETWORKS["test"]
        receive = layout.receive.derive(0).address(network)
        explorer = FakeExplorer(layout, network, [(receive, 10_000, "receive", 0)])
        scan = scan_wallet(record, explorer)
        self.assertTrue(scan["missing_change"])
        self.assertTrue(scan["coverage_limited"])
        self.assertFalse(scan["range_limited"])
        recipient = layout.receive.derive(5).address(network)
        built = build_unsigned_psbt(record, scan, recipient, None, 2,
                                    explorer, send_all=True)
        self.assertEqual(built["change_sats"], 0)
        self.assertEqual(len(psbt.PSBT.from_base64(built["psbt_base64"]).tx.vout), 1)
        with self.assertRaisesRegex(WalletError, "declared change"):
            build_unsigned_psbt(record, scan, recipient, 1_000, 2, explorer)

    def test_declared_paths_are_trusted_and_not_called_an_assumption(self):
        for label, kwargs in (("multipath", {"dual_branch": True}),
                              ("bsms_template", {"bsms_template": True})):
            with self.subTest(shape=label):
                summary = wallet_summary(parse_bsms(test_record(**kwargs)[0]))
                self.assertTrue(summary["can_prepare"])
                self.assertFalse(summary["change_assumed"])
                self.assertEqual(summary["change_note"], "")
                self.assertIn("declared", summary["change_detail"])

    def test_explicit_bsms_restrictions_declare_change_on_receive_descriptor(self):
        text, _ = test_record()
        text = text.replace("No path restrictions", "/0/*,/1/*")
        record = parse_bsms(text)
        summary = wallet_summary(record)
        self.assertTrue(summary["can_prepare"])
        self.assertIsNotNone(wallet_layout(record).change)

    def test_declared_change_branch_uses_the_same_keys(self):
        record = parse_bsms(test_record(bsms_template=True)[0])
        layout = wallet_layout(record)
        self.assertEqual(sorted(k.key.to_base58() for k in layout.change.keys),
                         sorted(k.key.to_base58() for k in layout.receive.keys))
        self.assertNotEqual(layout.change.derive(0).address(NETWORKS["test"]),
                            record.reference_address)

    def test_a_wallet_that_is_not_2_of_3_is_not_prepared(self):
        text, _ = test_record(short_path=True)
        lines = text.splitlines()
        descriptor = lines[1].split("#")[0].replace("sortedmulti(2,", "sortedmulti(3,")
        lines[1] = f"{descriptor}#{checksum(descriptor)}"
        # A consistent reference address for the changed policy.
        canonical = Descriptor.from_string(descriptor.replace("/*", "/0/*"))
        lines[3] = canonical.derive(0).address(NETWORKS["test"])
        summary = wallet_summary(parse_bsms("\n".join(lines) + "\n"))
        self.assertFalse(summary["can_prepare"])
        self.assertIn("2-of-3", summary["prepare_reason"])


class FeePreviewTests(unittest.TestCase):
    """The live preview must describe the transaction the builder will produce."""

    def setUp(self):
        text, _ = test_record(bsms_template=True)
        self.record = parse_bsms(text)
        self.layout = wallet_layout(self.record)
        self.network = NETWORKS["test"]
        self.explorer = three_output_wallet(self.layout, self.network)
        self.scan = scan_wallet(self.record, self.explorer)
        self.recipient = self.layout.receive.derive(5).address(self.network)

    def test_preview_matches_the_built_transaction_for_each_amount(self):
        for amount in (1_000, 50_000, 100_000, 150_000):
            with self.subTest(amount=amount):
                built = build_unsigned_psbt(self.record, self.scan, self.recipient,
                                            amount, 5, self.explorer)
                preview = estimate_fee_preview(
                    self.record, self.scan, False, amount=amount, fee_rate=5,
                    recipient=self.recipient,
                )
                self.assertEqual(preview["estimated_vbytes"],
                                 built["estimated_signed_vbytes"])
                self.assertEqual(preview["input_count"], built["inputs"])
                packet = psbt.PSBT.from_base64(built["psbt_base64"])
                self.assertEqual(preview["selected_sats"],
                                 sum(scope.witness_utxo.value for scope in packet.inputs))
                self.assertEqual(preview["method"], "exact input selection for this amount")

    def test_send_all_preview_matches_the_built_sweep(self):
        built = build_unsigned_psbt(self.record, self.scan, self.recipient, None, 5,
                                    self.explorer, send_all=True)
        preview = estimate_fee_preview(self.record, self.scan, True, fee_rate=5,
                                       recipient=self.recipient)
        self.assertEqual(preview["estimated_vbytes"], built["estimated_signed_vbytes"])
        self.assertEqual(preview["input_count"], built["inputs"])
        self.assertEqual(preview["input_count"], 3)
        self.assertIn("upper estimate", preview["method"])

    def test_preview_refuses_an_unaffordable_amount(self):
        with self.assertRaisesRegex(WalletError, "Not enough confirmed"):
            estimate_fee_preview(self.record, self.scan, False, amount=174_000,
                                 fee_rate=5, recipient=self.recipient)

    def test_preview_enforces_the_fee_rate_bounds(self):
        for rate in (0, 26):
            with self.subTest(rate=rate):
                with self.assertRaisesRegex(WalletError, "between 1 and 25"):
                    estimate_fee_preview(self.record, self.scan, False, amount=1_000,
                                         fee_rate=rate, recipient=self.recipient)

    def test_preview_refuses_a_below_dust_amount(self):
        with self.assertRaisesRegex(WalletError, "546"):
            estimate_fee_preview(self.record, self.scan, False, amount=545,
                                 fee_rate=5, recipient=self.recipient)

    def test_preview_requires_a_complete_consistent_scan(self):
        with self.assertRaisesRegex(WalletError, "complete, consistent"):
            estimate_fee_preview(self.record, {**self.scan, "range_limited": True},
                                 False, amount=1_000, fee_rate=5)
        with self.assertRaisesRegex(WalletError, "complete, consistent"):
            estimate_fee_preview(self.record, {**self.scan, "utxo_consistent": False},
                                 False, amount=1_000, fee_rate=5)


if __name__ == "__main__":
    unittest.main()

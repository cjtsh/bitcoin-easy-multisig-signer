"""Declared change-branch support and fee-preview/builder agreement.

Synthetic keys only; no wallet export is ever checked in.
"""

import unittest

from embit import psbt
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from fake_explorer import three_output_wallet
from probe import ProbeError, parse_bsms
from test_probe import test_record
from wallet_service import (
    WalletError, build_unsigned_psbt, can_declare_change, estimate_fee_preview,
    scan_wallet, wallet_layout, wallet_summary,
)


class DeclaredChangeTests(unittest.TestCase):
    def setUp(self):
        self.text, _ = test_record(short_path=True)  # bare /* + No path restrictions
        self.plain = parse_bsms(self.text)

    def test_receive_only_wallet_is_view_only_and_offers_the_option(self):
        summary = wallet_summary(self.plain)
        self.assertFalse(summary["can_prepare"])
        self.assertTrue(summary["can_declare_change"])
        self.assertFalse(summary["change_declared"])
        self.assertIsNone(wallet_layout(self.plain).change)
        self.assertIn("change", summary["prepare_reason"].lower())
        self.assertIn("change branch below", summary["prepare_reason"])

    def test_confirmed_change_branch_is_derived_from_the_same_keys(self):
        record = parse_bsms(self.text, declared_change=True)
        layout = wallet_layout(record)
        summary = wallet_summary(record)
        self.assertTrue(summary["can_prepare"])
        self.assertTrue(summary["change_declared"])
        self.assertFalse(summary["can_declare_change"])
        self.assertIsNotNone(layout.change)
        # Receive path is still anchored by the reference address.
        self.assertEqual(layout.receive.derive(0).address(NETWORKS["test"]),
                         record.reference_address)
        self.assertNotEqual(layout.change.derive(0).address(NETWORKS["test"]),
                            record.reference_address)
        # Both paths must use exactly the same multisig cosigners.
        self.assertEqual(sorted(k.key.to_base58() for k in layout.change.keys),
                         sorted(k.key.to_base58() for k in layout.receive.keys))
        # The user is told this came from their confirmation, not the file.
        self.assertIn("your own confirmation", layout.warning)

    def test_declaration_is_ignored_when_paths_are_already_declared(self):
        for label, kwargs in (("multipath", {"dual_branch": True}),
                              ("bsms_template", {"bsms_template": True})):
            with self.subTest(shape=label):
                text, _ = test_record(**kwargs)
                record = parse_bsms(text, declared_change=True)
                self.assertFalse(record.change_declared)
                self.assertTrue(wallet_summary(record)["can_prepare"])

    def test_path_qualified_descriptor_cannot_be_declared(self):
        text, _ = test_record()  # /0/* already qualified
        self.assertFalse(can_declare_change(parse_bsms(text)))
        record = parse_bsms(text, declared_change=True)
        self.assertFalse(record.change_declared)
        self.assertFalse(wallet_summary(record)["can_prepare"])

    def test_declaration_is_limited_to_the_2_of_3_policy(self):
        text, _ = test_record(short_path=True)
        three_of_three = text.replace("sortedmulti(2,", "sortedmulti(3,")
        descriptor = three_of_three.splitlines()[1].split("#")[0]
        lines = three_of_three.splitlines()
        lines[1] = f"{descriptor}#{checksum(descriptor)}"
        record = parse_bsms("\n".join(lines) + "\n")
        self.assertFalse(can_declare_change(record))

    def test_declaration_helper_rejects_unsupported_descriptors(self):
        from probe import declare_change_branch
        with self.assertRaisesRegex(ProbeError, "already declares"):
            declare_change_branch("wsh(sortedmulti(2,A/**))")
        with self.assertRaisesRegex(ProbeError, "plain /\\*"):
            declare_change_branch("wsh(sortedmulti(2,A/0/*))")


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
            estimate_fee_preview(self.record, {**self.scan, "coverage_limited": True},
                                 False, amount=1_000, fee_rate=5)
        with self.assertRaisesRegex(WalletError, "complete, consistent"):
            estimate_fee_preview(self.record, {**self.scan, "utxo_consistent": False},
                                 False, amount=1_000, fee_rate=5)


if __name__ == "__main__":
    unittest.main()

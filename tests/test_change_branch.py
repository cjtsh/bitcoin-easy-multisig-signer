"""BIP48 standard change works from one BSMS file; nonstandard paths fail closed.

Synthetic keys only; no wallet export is ever checked in.
"""

import unittest

from embit import bip32, psbt
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
    """A standard export requires no second file or technical assertion."""

    def test_nunchuk_shape_uses_standard_bip48_change(self):
        record = parse_bsms(test_record(short_path=True)[0])  # bare /* export
        layout = wallet_layout(record)
        summary = wallet_summary(record)
        self.assertTrue(summary["can_prepare"])
        self.assertTrue(summary["can_send_all"])
        self.assertTrue(summary["change_assumed"])
        self.assertEqual([key.suffix for key in layout.change.keys], ["/1/*"] * 3)
        self.assertNotEqual(summary["receive_address"], summary["change_address"])

    def test_path_qualified_standard_wallet_uses_same_bip48_change(self):
        record = parse_bsms(test_record()[0])  # /0/* only
        summary = wallet_summary(record)
        self.assertTrue(summary["can_prepare"])
        self.assertEqual([key.suffix for key in wallet_layout(record).change.keys],
                         ["/1/*"] * 3)

    def test_nunchuk_style_two_of_two_does_not_infer_change(self):
        for key_count in (2, 3):
            for threshold in range(1, key_count + 1):
                if (threshold, key_count) == (2, 3):
                    continue  # This exact standard policy retains its tested fallback.
                with self.subTest(threshold=threshold, key_count=key_count):
                    record = parse_bsms(test_record(
                        short_path=True, threshold=threshold, key_count=key_count)[0])
                    summary = wallet_summary(record)
                    self.assertFalse(summary["can_prepare"])
                    self.assertTrue(summary["can_send_all"])
                    self.assertFalse(summary["change_assumed"])
                    self.assertIsNone(wallet_layout(record).change)

    def test_bare_wildcard_reference_at_the_branch_root_never_infers_change(self):
        """AGENTS.md: a bare ``/*`` matching the first address at ``xpub/0`` does
        not anchor the BIP48 ``xpub/0/index`` receive branch, so the standard
        ``/1/*`` change branch must not be inferred from it.

        Every other case in this file anchors the reference at ``xpub/0/0``
        (``receive-branch-only``), where the ``not bare_receive_only`` guard in
        ``wallet_service.wallet_layout`` is unreachable -- deleting the guard
        left this whole file green. This is the shape the guard exists for.
        """
        roots = [bip32.HDKey.from_seed(bytes([i]) * 32) for i in (1, 2, 3)]
        keys = [f"[{root.my_fingerprint.hex()}/48h/1h/0h/2h]"
                f"{root.derive('m/48h/1h/0h/2h').to_public().to_base58()}/*"
                for root in roots]
        descriptor = f"wsh(sortedmulti(2,{','.join(keys)}))"
        # The bare wildcard filled with 0 is the first address directly, not the
        # first index of a receive branch: this is xpub/0, never xpub/0/0.
        reference = Descriptor.from_string(descriptor).derive(0).address(NETWORKS["test"])
        record = parse_bsms(
            f"BSMS 1.0\n{descriptor}#{checksum(descriptor)}\n"
            f"No path restrictions\n{reference}\n"
        )
        self.assertEqual(record.reference_status, "verified")
        self.assertIsNone(wallet_layout(record).change)
        summary = wallet_summary(record)
        self.assertFalse(summary["change_assumed"])
        self.assertFalse(summary["can_prepare"])
        self.assertTrue(summary["can_send_all"])

    def test_nonstandard_wallet_can_only_sweep_without_creating_change(self):
        roots = [bip32.HDKey.from_seed(bytes([i]) * 32) for i in (1, 2, 3)]
        keys = [f"[{root.my_fingerprint.hex()}/48h/1h/0h/3h]"
                f"{root.derive('m/48h/1h/0h/3h').to_public().to_base58()}/*"
                for root in roots]
        descriptor = f"wsh(sortedmulti(2,{','.join(keys)}))"
        reference = Descriptor.from_string(descriptor.replace("/*", "/0/*"))
        address = reference.derive(0).address(NETWORKS["test"])
        record = parse_bsms(
            f"BSMS 1.0\n{descriptor}#{checksum(descriptor)}\nNo path restrictions\n{address}\n")
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
        with self.assertRaisesRegex(WalletError, "supported BIP48 change"):
            build_unsigned_psbt(record, scan, recipient, 1_000, 2, explorer)

    def test_nunchuk_shape_builds_custom_amount_with_change_from_one_file(self):
        record = parse_bsms(test_record(short_path=True)[0])
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        recipient = layout.receive.derive(8).address(NETWORKS["test"])
        built = build_unsigned_psbt(record, scan, recipient, 1_000, 2, explorer)
        packet = psbt.PSBT.from_base64(built["psbt_base64"])
        self.assertGreater(built["change_sats"], 0)
        self.assertEqual(len(packet.tx.vout), 2)
        self.assertEqual(packet.tx.vout[1].script_pubkey.address(NETWORKS["test"]),
                         built["change_address"])

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

    def test_a_wallet_with_more_than_three_keys_is_refused(self):
        text, _ = test_record(key_count=4)
        with self.assertRaisesRegex(ProbeError, "two or three keys"):
            parse_bsms(text)


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

    def test_change_is_never_left_below_dust(self):
        """No successfully built partial send may leave under-dust change.

        The greedy selection stops only when the remainder clears the dust floor
        and the builder re-checks it, so a remainder in 1-545 sats must never
        appear as a change output. The sweep crosses the point where the wallet
        runs out of confirmed sats, so both outcomes are exercised.
        """
        refused = 0
        for amount in range(170_000, 175_001, 25):
            with self.subTest(amount=amount):
                try:
                    built = build_unsigned_psbt(self.record, self.scan,
                                                self.recipient, amount, 5,
                                                self.explorer)
                except WalletError as exc:
                    self.assertIn("Not enough confirmed", str(exc))
                    refused += 1
                    continue
                self.assertGreaterEqual(built["change_sats"], 546)
        self.assertGreater(refused, 0, "the sweep must cross the refusal boundary")

    def test_preview_requires_a_complete_consistent_scan(self):
        with self.assertRaisesRegex(WalletError, "complete, consistent"):
            estimate_fee_preview(self.record, {**self.scan, "range_limited": True},
                                 False, amount=1_000, fee_rate=5)
        with self.assertRaisesRegex(WalletError, "complete, consistent"):
            estimate_fee_preview(self.record, {**self.scan, "utxo_consistent": False},
                                 False, amount=1_000, fee_rate=5)


if __name__ == "__main__":
    unittest.main()

"""Finalising a signed multisig PSBT.

The signatures are not merely re-parsed here: each one is verified cryptographically
against the witness script over the correct BIP143 sighash, and the input is checked
to carry exactly the number of distinct signatures the threshold requires. A
finaliser that produced well-formed but unspendable bytes would fail these tests.
"""

import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embit import psbt as E  # noqa: E402
from embit.networks import NETWORKS  # noqa: E402
from embit.script import Script  # noqa: E402

from fake_explorer import three_output_wallet  # noqa: E402
from probe import parse_bsms  # noqa: E402
from signing import (SigningError, accept_signature_update, finalize_multisig,
                     is_complete, parse_multisig_script, signatures_collected,
                     verified_input_signatures)
from test_probe import test_record  # noqa: E402
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout  # noqa: E402


def prepared_psbt(amount: int = 100_000, fee_rate: int = 5):
    """An unsigned 2-of-3 PSBT from the synthetic wallet, plus its signing keys."""
    text, roots = test_record(bsms_template=True)
    record = parse_bsms(text)
    layout = wallet_layout(record)
    explorer = three_output_wallet(layout, NETWORKS["test"])
    scan = scan_wallet(record, explorer)
    recipient = layout.receive.derive(5).address(NETWORKS["test"])
    result = build_unsigned_psbt(record, scan, recipient, amount, fee_rate, explorer)
    packet = E.PSBT.parse(base64.b64decode(result["psbt_base64"]))
    keys = [root.derive("m/48h/1h/0h/2h/0/0") for root in roots]
    return packet, keys, result


def sign(packet, keys):
    for key in keys:
        packet.sign_with(key)
    return packet


class FinalizeTests(unittest.TestCase):
    def test_every_quorum_with_two_or_three_keys_signs_and_finalizes(self):
        for key_count in (2, 3):
            for threshold in range(1, key_count + 1):
                with self.subTest(threshold=threshold, key_count=key_count):
                    text, roots = test_record(
                        bsms_template=True, threshold=threshold, key_count=key_count)
                    record = parse_bsms(text)
                    layout = wallet_layout(record)
                    explorer = three_output_wallet(layout, NETWORKS["test"])
                    scan = scan_wallet(record, explorer)
                    recipient = layout.receive.derive(5).address(NETWORKS["test"])
                    prepared = build_unsigned_psbt(
                        record, scan, recipient, 100_000, 5, explorer)
                    packet = E.PSBT.parse(base64.b64decode(prepared["psbt_base64"]))
                    keys = [root.derive("m/48h/1h/0h/2h/0/0") for root in roots]
                    sign(packet, keys[:threshold])
                    self.assertTrue(is_complete(packet))
                    self.assertEqual(signatures_collected(packet), (threshold, threshold))
                    final = finalize_multisig(packet, prepared["txid"])
                    self.assertEqual(final["txid"], prepared["txid"])

    def test_a_complete_multisig_psbt_finalises_to_a_valid_transaction(self):
        packet, keys, result = prepared_psbt()
        txid = packet.tx.txid().hex()
        self.assertEqual(txid, result["txid"])
        self.assertFalse(is_complete(packet))
        sign(packet, keys[:2])
        self.assertTrue(is_complete(packet))

        final = finalize_multisig(packet, txid)
        self.assertEqual(final["txid"], txid)
        # A segwit transaction id must not move when signatures are added.
        self.assertGreater(final["vsize"], 0)
        self.assertGreater(final["fee_sats"], 0)

        # Re-parse the bytes that would be broadcast and verify every signature
        # against the witness script over the BIP143 sighash.
        from embit import transaction as T
        raw = bytes.fromhex(final["raw_transaction_hex"])
        rebuilt = T.Transaction.parse(raw)
        self.assertEqual(rebuilt.txid().hex(), txid)

        for index, vin in enumerate(rebuilt.vin):
            items = vin.witness.items
            self.assertEqual(items[0], b"", "CHECKMULTISIG needs the leading empty item")
            witness_script = items[-1]
            threshold, pubkeys = parse_multisig_script(witness_script)
            signatures = items[1:-1]
            self.assertEqual(len(signatures), threshold,
                             "the witness must carry exactly the threshold of signatures")
            amount = packet.inputs[index].witness_utxo.value
            from embit.script import Script
            sighash = rebuilt.sighash_segwit(index, Script(witness_script), amount)
            from embit import ec
            verified = []
            for signature in signatures:
                # A witness signature is DER followed by the sighash-type byte.
                parsed = ec.Signature.parse(signature[:-1])
                for pubkey in pubkeys:
                    if pubkey in verified:
                        continue
                    if ec.PublicKey.parse(pubkey).verify(parsed, sighash):
                        verified.append(pubkey)
                        break
            self.assertEqual(len(verified), threshold,
                             "every signature must verify against a distinct script key")

    def test_signatures_are_ordered_as_the_witness_script_lists_the_keys(self):
        """Wrong order is a valid-looking transaction the network rejects."""
        packet, keys, _ = prepared_psbt()
        # Sign the SECOND and THIRD keys, so signing order differs from script order.
        sign(packet, keys[1:])
        finalize_multisig(packet, packet.tx.txid().hex())
        indices = self.verified_key_indices(packet)
        self.assertEqual(len(indices), 2)
        self.assertEqual(indices, sorted(indices),
                         "signatures must follow the order of the witness script")
        self.assertEqual(indices, [1, 2], "the two keys that actually signed")

    def verified_key_indices(self, packet) -> list[int]:
        """Which witness-script key index each witness signature belongs to."""
        from embit import ec
        from embit.script import Script
        scope = packet.inputs[0]
        items = scope.final_scriptwitness.items
        witness_script = items[-1]
        _, pubkeys = parse_multisig_script(witness_script)
        sighash = packet.tx.sighash_segwit(
            0, Script(witness_script), scope.witness_utxo.value)
        found = []
        for signature in items[1:-1]:
            for index, pubkey in enumerate(pubkeys):
                if ec.PublicKey.parse(pubkey).verify(
                        ec.Signature.parse(signature[:-1]), sighash):
                    found.append(index)
                    break
        return found

    def test_transactions_signal_replaceability(self):
        """A non-replaceable payment that gets stuck cannot be fee-bumped.

        nSequence 0xffffffff means final: the owner's second testnet send sat
        unconfirmed with no remedy. Below 0xfffffffe the same coins can be spent
        again with a higher fee if that is ever needed.
        """
        packet, _keys, _ = prepared_psbt()
        for index, vin in enumerate(packet.tx.vin, start=1):
            self.assertLess(vin.sequence, 0xFFFFFFFE,
                            f"input {index} is not replaceable")
            self.assertEqual(vin.sequence, 0xFFFFFFFD)

    def test_the_built_psbt_publishes_the_cosigner_xpubs(self):
        """A Ledger will not sign a multisig spend without these.

        hwilib rebuilds the wallet policy from the PSBT's global xpubs. Without
        them it skips every input silently: no error, no prompt on the device, and
        the PSBT comes back unchanged. Trezor and Jade do not need them, so this
        only appears when a Ledger is asked to sign.
        """
        packet, _keys, _ = prepared_psbt()
        self.assertEqual(len(packet.xpubs), 3)
        # hwilib's own requirement: the global origin must match the input key's
        # fingerprint and be a prefix of its derivation path.
        for scope in packet.inputs:
            for _pubkey, origin in scope.bip32_derivations.items():
                accepted = any(
                    global_origin.fingerprint == origin.fingerprint
                    and global_origin.derivation == origin.derivation[:len(global_origin.derivation)]
                    for global_origin in packet.xpubs.values()
                )
                self.assertTrue(accepted, "a Ledger would silently skip this input")

    def test_an_under_signed_psbt_is_refused(self):
        packet, keys, _ = prepared_psbt()
        sign(packet, keys[:1])
        self.assertEqual(signatures_collected(packet), (1, 2))
        with self.assertRaises(SigningError) as err:
            finalize_multisig(packet, packet.tx.txid().hex())
        self.assertIn("1 of 2", str(err.exception))

    def test_corrupted_signatures_are_not_counted_or_finalized(self):
        packet, keys, _ = prepared_psbt()
        sign(packet, keys[:2])
        for scope in packet.inputs:
            for pub in list(scope.partial_sigs):
                damaged = bytearray(scope.partial_sigs[pub])
                damaged[5] ^= 1
                scope.partial_sigs[pub] = bytes(damaged)
        with self.assertRaises(SigningError):
            is_complete(packet)
        with self.assertRaises(SigningError):
            finalize_multisig(packet, packet.tx.txid().hex())

    def test_device_can_only_add_valid_signatures(self):
        before, keys, _ = prepared_psbt()
        after = E.PSBT.from_base64(before.to_base64())
        after.sign_with(keys[0])
        accepted = accept_signature_update(before, after)
        self.assertEqual(signatures_collected(accepted), (1, 2))
        changed = E.PSBT.from_base64(after.to_base64())
        changed.inputs[0].witness_utxo.value += 1
        # The device's metadata cannot enter the prepared payment, even when
        # its valid signature remains usable against the original prevout.
        accepted = accept_signature_update(before, changed)
        self.assertEqual(accepted.inputs[0].witness_utxo.value,
                         before.inputs[0].witness_utxo.value)
        self.assertEqual(signatures_collected(accepted), (1, 2))

    def test_device_metadata_and_changed_outputs_cannot_enter_reviewed_payment(self):
        before, keys, _ = prepared_psbt()
        after = E.PSBT.from_base64(before.to_base64())
        after.sign_with(keys[0])
        after.inputs[0].witness_script = None
        after.outputs[0].unknown[b"\xfcdevice"] = b"untrusted"
        accepted = accept_signature_update(before, after)
        self.assertEqual(accepted.outputs[0].unknown, before.outputs[0].unknown)
        self.assertEqual(accepted.inputs[0].witness_script,
                         before.inputs[0].witness_script)
        self.assertEqual(signatures_collected(accepted), (1, 2))
        after.outputs[0].value += 1
        with self.assertRaisesRegex(SigningError, "different transaction"):
            accept_signature_update(before, after)

    def test_invalid_device_signature_is_not_imported(self):
        before, keys, _ = prepared_psbt()
        after = E.PSBT.from_base64(before.to_base64())
        after.sign_with(keys[0])
        scope = after.inputs[0]
        pub = next(iter(scope.partial_sigs))
        damaged = bytearray(scope.partial_sigs[pub])
        damaged[5] ^= 1
        scope.partial_sigs[pub] = bytes(damaged)
        with self.assertRaisesRegex(SigningError, "invalid signature"):
            accept_signature_update(before, after)

    def test_hwi_field_reordering_does_not_erase_a_valid_signature(self):
        """HWI sorts PSBT maps; field order is not part of the payment policy."""
        before, keys, _ = prepared_psbt()
        after = E.PSBT.from_base64(before.to_base64())
        after.sign_with(keys[0])
        after.xpubs = dict(reversed(list(after.xpubs.items())))
        for scope in after.inputs:
            scope.bip32_derivations = dict(
                reversed(list(scope.bip32_derivations.items())))
        self.assertNotEqual(before.serialize(), after.serialize())
        accept_signature_update(before, after)

    def test_a_changed_transaction_id_is_refused(self):
        """If the id moved, this is not the transaction the owner reviewed."""
        packet, keys, _ = prepared_psbt()
        sign(packet, keys[:2])
        with self.assertRaises(SigningError) as err:
            finalize_multisig(packet, "00" * 32)
        self.assertIn("changed while signing", str(err.exception))

    def test_only_sighash_all_is_accepted(self):
        """A signature relabelled to another sighash must not be counted.

        The trailing sighash byte is stripped before ECDSA verification, so
        without the explicit check a genuine ALL signature relabelled as NONE or
        SINGLE would still verify against the ALL digest and be accepted. Only
        SIGHASH_ALL can be assembled into a safe multisig witness here.
        """
        for sighash in (0x00, 0x02, 0x03, 0x81, 0x82, 0x83):
            with self.subTest(sighash=sighash):
                packet, keys, _ = prepared_psbt()
                sign(packet, keys[:2])
                scope = packet.inputs[0]
                pub = next(iter(scope.partial_sigs))
                scope.partial_sigs[pub] = (
                    scope.partial_sigs[pub][:-1] + bytes([sighash])
                )
                with self.assertRaisesRegex(SigningError, "sighash type"):
                    verified_input_signatures(packet)

    def test_removing_a_prior_signature_is_refused(self):
        """A device that drops a signature it was given must not be accepted."""
        before, keys, _ = prepared_psbt()
        sign(before, keys[:2])
        after = E.PSBT.from_base64(before.to_base64())
        scope = after.inputs[0]
        del scope.partial_sigs[next(iter(scope.partial_sigs))]
        with self.assertRaisesRegex(SigningError,
                                    "removed or changed an earlier signature"):
            accept_signature_update(before, after)

    def test_an_altered_prior_signature_is_refused(self):
        """Changing a signature already held is the same failure as dropping it."""
        before, keys, _ = prepared_psbt()
        sign(before, keys[:2])
        after = E.PSBT.from_base64(before.to_base64())
        scope = after.inputs[0]
        victim = next(iter(scope.partial_sigs))
        damaged = bytearray(scope.partial_sigs[victim])
        damaged[5] ^= 1
        scope.partial_sigs[victim] = bytes(damaged)
        with self.assertRaisesRegex(SigningError,
                                    "removed or changed an earlier signature"):
            accept_signature_update(before, after)

    def test_a_script_that_is_not_multisig_is_refused(self):
        with self.assertRaises(SigningError):
            parse_multisig_script(b"\x00\x14" + b"\x11" * 20)
        with self.assertRaises(SigningError):
            parse_multisig_script(b"")

    def test_a_witness_script_that_does_not_own_its_output_is_refused(self):
        """Prevout-ownership pin, part 1 (CT-15): the script hash must match."""
        packet, _keys, _result = prepared_psbt()
        packet.inputs[0].witness_utxo.script_pubkey = Script(b"\x00\x20" + bytes(32))
        with self.assertRaisesRegex(SigningError, "does not own its output"):
            verified_input_signatures(packet)

    def test_a_mismatched_previous_transaction_id_is_refused(self):
        """Prevout-ownership pin, part 2 (CT-15): the prevout txid must match.

        PSBT.tx and InputScope.vin are rebuilt on every access, so the tamper
        must land on the scope's stored txid attribute, not a rebuilt object.
        """
        packet, _keys, _result = prepared_psbt()
        txid = bytearray(packet.inputs[0].txid)
        txid[0] ^= 1
        packet.inputs[0].txid = bytes(txid)
        with self.assertRaisesRegex(
                SigningError, "does not match its verified previous transaction"):
            verified_input_signatures(packet)

    def test_an_out_of_range_output_index_is_refused(self):
        """Prevout-ownership pin, part 3 (CT-15): the vout must exist."""
        packet, _keys, _result = prepared_psbt()
        packet.inputs[0].vout = len(packet.inputs[0].non_witness_utxo.vout) + 10
        with self.assertRaisesRegex(
                SigningError, "does not match its verified previous transaction"):
            verified_input_signatures(packet)

    def test_a_prevout_that_differs_from_the_witness_utxo_is_refused(self):
        """Prevout-ownership pin, part 4 (CT-15): content must match exactly."""
        packet, _keys, _result = prepared_psbt()
        prevout = packet.inputs[0].non_witness_utxo.vout[packet.tx.vin[0].vout]
        prevout.value += 1
        with self.assertRaisesRegex(
                SigningError, "does not match its verified previous transaction"):
            verified_input_signatures(packet)


if __name__ == "__main__":
    unittest.main()

"""Pin the money-path gates cycle 2 found holding but unguarded (CT-28/31/32).

Each test here exists because the corresponding control is correct today and
nothing in the suite would notice if a future edit weakened it. Cycle 3's
referee will break-and-watch every one: weaken the gate, watch this file go red,
restore. A test that cannot fail does not count as a fix.
"""

import base64
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embit import bip32, ec, psbt as E, transaction
from embit.networks import NETWORKS
from embit.script import Script

from fake_explorer import three_output_wallet
from probe import _same_xpub, parse_bsms
from signing import (
    SigningError, parse_multisig_script, virtual_size, verified_input_signatures,
    finalize_multisig,
)
from test_probe import test_record
from wallet_service import WalletError, broadcast_transaction, build_unsigned_psbt, scan_wallet, wallet_layout


# ---------------------------------------------------------------------------
# CT-28 — full-xpub device-identity comparison
# ---------------------------------------------------------------------------

class XpubIdentityPins(unittest.TestCase):
    def test_a_forged_fingerprint_with_the_wrong_key_material_is_refused(self):
        """CT-28: fingerprint-only weakening must not survive this test.

        A counterfeit device can echo the expected fingerprint while returning
        a different account xpub. Only the full comparison (key bytes, chain
        code, depth, fingerprint, child number) refuses it.
        """
        record, roots = test_record()
        wallet = parse_bsms(record)
        expected = wallet.keys[0]
        real = expected.key

        other_root = bip32.HDKey.from_seed(bytes([9]) * 32)
        other = other_root.derive("m/48h/1h/0h/2h").to_public()
        forged = bip32.HDKey(
            key=other.key,
            chain_code=other.chain_code,
            depth=real.depth,
            fingerprint=real.fingerprint,  # echo the real fingerprint
            child_number=real.child_number,
        )
        # The forged xpub matches every metadata field a fingerprint-only
        # check looks at, and disagrees on the actual public key.
        self.assertEqual(forged.fingerprint, real.fingerprint)
        self.assertEqual(forged.depth, real.depth)
        self.assertEqual(forged.child_number, real.child_number)
        self.assertNotEqual(forged.get_public_key().sec(),
                            real.get_public_key().sec())
        self.assertFalse(_same_xpub(expected, forged.to_base58()))

    def test_a_forged_key_with_the_real_fingerprint_field_reencoded_is_refused(self):
        """Second shape: take the real xpub, swap only the key, keep the rest."""
        record, roots = test_record()
        wallet = parse_bsms(record)
        expected = wallet.keys[0]
        real = expected.key
        other = bip32.HDKey.from_seed(bytes([7]) * 32).derive("m/48h/1h/0h/2h").to_public()
        forged = bip32.HDKey(
            key=other.key,
            chain_code=real.chain_code,
            depth=real.depth,
            fingerprint=real.fingerprint,
            child_number=real.child_number,
        )
        self.assertFalse(_same_xpub(expected, forged.to_base58()))

    def test_the_real_account_xpub_still_matches(self):
        """The positive half: the pin must not refuse the genuine key."""
        record, roots = test_record()
        wallet = parse_bsms(record)
        genuine = roots[0].derive("m/48h/1h/0h/2h").to_public().to_base58()
        self.assertTrue(_same_xpub(wallet.keys[0], genuine))

    def test_a_wrong_fingerprint_with_the_right_key_is_also_refused(self):
        """Both sides of the comparison are load-bearing."""
        record, roots = test_record()
        wallet = parse_bsms(record)
        expected = wallet.keys[0]
        real = expected.key
        other = bip32.HDKey.from_seed(bytes([3]) * 32).derive("m/48h/1h/0h/2h").to_public()
        forged = bip32.HDKey(
            key=real.key,
            chain_code=real.chain_code,
            depth=real.depth,
            fingerprint=other.fingerprint,  # right key, wrong parent fingerprint
            child_number=real.child_number,
        )
        self.assertFalse(_same_xpub(expected, forged.to_base58()))


# ---------------------------------------------------------------------------
# CT-31 — four money-path gates
# ---------------------------------------------------------------------------

def prepared():
    text, roots = test_record(bsms_template=True)
    record = parse_bsms(text)
    layout = wallet_layout(record)
    explorer = three_output_wallet(layout, NETWORKS["test"])
    scan = scan_wallet(record, explorer)
    recipient = layout.receive.derive(5).address(NETWORKS["test"])
    result = build_unsigned_psbt(record, scan, recipient, 100_000, 5, explorer)
    packet = E.PSBT.parse(base64.b64decode(result["psbt_base64"]))
    keys = [root.derive("m/48h/1h/0h/2h/0/0") for root in roots]
    return packet, keys, result


class MoneyPathGatePins(unittest.TestCase):
    def test_a_finaliser_refuses_outputs_that_exceed_the_inputs(self):
        """CT-31(a): outputs≤inputs is a gate, not a comment.

        A finaliser that skipped this check would mint value. Build a packet
        whose single output is larger than its single input. The signature
        verifier is stubbed so this test isolates the totals gate; the
        prevout-binding pins cover the verifier itself.
        """
        text, roots = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        # 1 input paying 50_000, 1 output paying 60_000 — an impossible fee.
        tx = transaction.Transaction(
            version=2,
            vin=[transaction.TransactionInput(bytes.fromhex("ab" * 32), 0,
                                              sequence=0xFFFFFFFD)],
            vout=[transaction.TransactionOutput(60_000, Script(b"\x00\x14" + bytes(20)))],
        )
        packet = E.PSBT(tx)
        derived = layout.receive.derive(0)
        packet.inputs[0].witness_utxo = transaction.TransactionOutput(
            50_000, derived.script_pubkey())
        packet.inputs[0].witness_script = derived.witness_script()
        packet.inputs[0].non_witness_utxo = transaction.Transaction(
            vin=[transaction.TransactionInput(bytes.fromhex("cd" * 32), 0)],
            vout=[transaction.TransactionOutput(50_000, derived.script_pubkey())],
        )
        # Dummy signatures so witness assembly reaches the totals gate. The
        # verifier is stubbed, so they need not be cryptographically valid.
        dummy = b"\x30\x44" + b"\x00" * 68 + b"\x01"
        valid = set()
        for cosigner in derived.keys[:2]:
            pubkey = cosigner.get_public_key()
            packet.inputs[0].partial_sigs[pubkey] = dummy
            valid.add(pubkey.sec())
        with patch("signing.verified_input_signatures", return_value=[valid]):
            with self.assertRaisesRegex(SigningError, "outputs exceed the inputs"):
                finalize_multisig(packet, packet.tx.txid().hex())

    def test_signing_refuses_a_witness_script_with_a_single_key(self):
        """CT-31(b): only two- or three-key policies may reach a device signature."""
        packet, _keys, _result = prepared()
        pubkey = next(iter(packet.inputs[0].bip32_derivations)).sec()
        # 1-of-1: OP_1 <33-byte key> OP_1 OP_CHECKMULTISIG
        script = Script(bytes([0x51, 0x21]) + pubkey + bytes([0x51, 0xAE]))
        packet.inputs[0].witness_script = script
        with self.assertRaisesRegex(SigningError, "two or three keys"):
            verified_input_signatures(packet)

    def test_signing_refuses_a_witness_script_with_four_keys(self):
        """CT-31(b) upper bound: four keys are out of policy."""
        packet, _keys, _result = prepared()
        pubs = [pk.sec() for pk in list(packet.inputs[0].bip32_derivations)[:3]]
        extra = bip32.HDKey.from_seed(bytes([4]) * 32).get_public_key().sec()
        pubs.append(extra)
        # 1-of-4: OP_1 <4 pubs> OP_4 OP_CHECKMULTISIG
        script = Script(bytes([0x51]) + b"".join(bytes([0x21]) + p for p in pubs)
                        + bytes([0x54, 0xAE]))
        packet.inputs[0].witness_script = script
        with self.assertRaisesRegex(SigningError, "two or three keys"):
            verified_input_signatures(packet)

    def test_virtual_size_follows_the_bip141_weight_formula(self):
        """CT-31(c): vsize is stripped*4 + witness, rounded up.

        A wrong vsize produces a wrong fee rate. Pin the formula on a real
        finalised transaction from the synthetic wallet.
        """
        packet, keys, result = prepared()
        for key in keys[:2]:
            packet.sign_with(key)
        final = finalize_multisig(packet, result["txid"])
        raw = bytes.fromhex(final["raw_transaction_hex"])
        tx = transaction.Transaction.parse(raw)
        saved = [vin.witness for vin in tx.vin]
        for vin in tx.vin:
            vin.witness = transaction.Witness([])
        stripped_len = len(tx.serialize())
        for vin, witness in zip(tx.vin, saved):
            vin.witness = witness
        weight = stripped_len * 4 + (len(raw) - stripped_len)
        expected_vsize = (weight + 3) // 4
        self.assertEqual(final["vsize"], expected_vsize)
        self.assertEqual(final["size"], len(raw))
        self.assertGreaterEqual(final["vsize"], stripped_len)
        self.assertLessEqual(final["vsize"], len(raw))

    def test_virtual_size_refuses_a_finalised_transaction_smaller_than_its_skeleton(self):
        """CT-31(c) fail-closed half: nonsense sizes must raise, not return 0."""
        packet, keys, result = prepared()
        for key in keys[:2]:
            packet.sign_with(key)
        final = finalize_multisig(packet, result["txid"])
        raw = bytes.fromhex(final["raw_transaction_hex"])
        tx = transaction.Transaction.parse(raw)
        with self.assertRaisesRegex(SigningError, "smaller than its own skeleton"):
            virtual_size(tx, raw[:10])

    def test_broadcast_refuses_odd_length_hex(self):
        """CT-31(d): parity is checked before anything is sent."""
        with patch("wallet_service.urlopen") as send:
            with self.assertRaisesRegex(WalletError, "not valid hex|usable size"):
                broadcast_transaction("00" * 50 + "a")
        send.assert_not_called()

    def test_broadcast_refuses_non_hex_bytes(self):
        with patch("wallet_service.urlopen") as send:
            with self.assertRaisesRegex(WalletError, "not valid hex"):
                broadcast_transaction("zz" * 50)
        send.assert_not_called()

    def test_broadcast_refuses_a_transaction_too_small_to_be_real(self):
        with patch("wallet_service.urlopen") as send:
            with self.assertRaisesRegex(WalletError, "usable size"):
                broadcast_transaction("00" * 10)
        send.assert_not_called()

    def test_broadcast_refuses_a_transaction_over_the_size_cap(self):
        with patch("wallet_service.urlopen") as send:
            with self.assertRaisesRegex(WalletError, "usable size"):
                broadcast_transaction("00" * 1_000_001)
        send.assert_not_called()

    def test_broadcast_accepts_well_formed_hex_after_the_gates(self):
        """The positive half: a plausible transaction reaches the transport."""
        import io
        body = "ab" * 80  # 160 bytes, even, hex
        with patch("wallet_service.urlopen", return_value=io.BytesIO(b"c" * 64)) as send:
            txid = broadcast_transaction(body, chain="testnet4")
        self.assertEqual(txid, "c" * 64)
        self.assertEqual(send.call_count, 1)


# ---------------------------------------------------------------------------
# CT-32 — build-time prevout / ownership binding
# ---------------------------------------------------------------------------

class BuildTimePrevoutPins(unittest.TestCase):
    """The sign-time twin of these checks is CT-15 and is already pinned.

    CT-32 is the same binding at *build* time: the explorer-supplied previous
    transaction must hash to the claimed txid, pay the claimed value, and pay
    the wallet-derived script. A fake explorer that lies here must not produce
    an unsigned PSBT.
    """

    def setUp(self):
        self.text, self.roots = test_record(bsms_template=True)
        self.record = parse_bsms(self.text)
        self.layout = wallet_layout(self.record)
        self.explorer = three_output_wallet(self.layout, NETWORKS["test"])
        self.scan = scan_wallet(self.record, self.explorer)
        self.recipient = self.layout.receive.derive(5).address(NETWORKS["test"])

    def test_a_previous_transaction_whose_txid_does_not_match_is_refused(self):
        def lying(path, *, text=False):
            if path.endswith("/hex"):
                raw = self.explorer(path, text=True)
                # Flip a byte in the serialized tx so its hash no longer
                # matches the txid the UTXO claims — without making it
                # unparseable. Change the locktime.
                tx = transaction.Transaction.parse(bytes.fromhex(raw))
                tx.locktime ^= 1
                return tx.serialize().hex()
            return self.explorer(path, text=text)

        with self.assertRaisesRegex(
                WalletError, "Previous output does not match this wallet"):
            build_unsigned_psbt(self.record, self.scan, self.recipient,
                                10_000, 5, lying)

    def test_a_previous_transaction_paying_a_different_script_is_refused(self):
        """The explorer cannot redirect the spend to a script we do not own."""
        def lying(path, *, text=False):
            if path.endswith("/hex"):
                raw = self.explorer(path, text=True)
                tx = transaction.Transaction.parse(bytes.fromhex(raw))
                # Pay some other scriptPubKey at the claimed vout.
                tx.vout[0] = transaction.TransactionOutput(
                    tx.vout[0].value, Script(b"\x00\x14" + bytes(20)))
                return tx.serialize().hex()
            return self.explorer(path, text=text)

        with self.assertRaisesRegex(
                WalletError, "Previous output does not match this wallet"):
            build_unsigned_psbt(self.record, self.scan, self.recipient,
                                10_000, 5, lying)

    def test_a_previous_transaction_paying_a_different_value_is_refused(self):
        def lying(path, *, text=False):
            if path.endswith("/hex"):
                raw = self.explorer(path, text=True)
                tx = transaction.Transaction.parse(bytes.fromhex(raw))
                tx.vout[0] = transaction.TransactionOutput(
                    tx.vout[0].value + 1, tx.vout[0].script_pubkey)
                return tx.serialize().hex()
            return self.explorer(path, text=text)

        with self.assertRaisesRegex(
                WalletError, "Previous output does not match this wallet"):
            build_unsigned_psbt(self.record, self.scan, self.recipient,
                                10_000, 5, lying)

    def test_the_honest_explorer_still_builds(self):
        result = build_unsigned_psbt(self.record, self.scan, self.recipient,
                                     10_000, 5, self.explorer)
        packet = E.PSBT.parse(base64.b64decode(result["psbt_base64"]))
        self.assertIsNotNone(packet.inputs[0].non_witness_utxo)
        self.assertIsNotNone(packet.inputs[0].witness_utxo)
        self.assertIsNotNone(packet.inputs[0].witness_script)


if __name__ == "__main__":
    unittest.main()

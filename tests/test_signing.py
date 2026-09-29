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

from fake_explorer import three_output_wallet  # noqa: E402
from probe import parse_bsms  # noqa: E402
from signing import (SigningError, finalize_multisig, is_complete,  # noqa: E402
                     parse_multisig_script, signatures_collected)
from test_probe import test_record  # noqa: E402
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout  # noqa: E402


def prepared_psbt(amount: int = 100_000, fee_rate: int = 5):
    """An unsigned 2-of-3 PSBT from the synthetic wallet, plus its signing keys."""
    text, roots = test_record()
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

    def test_a_changed_transaction_id_is_refused(self):
        """If the id moved, this is not the transaction the owner reviewed."""
        packet, keys, _ = prepared_psbt()
        sign(packet, keys[:2])
        with self.assertRaises(SigningError) as err:
            finalize_multisig(packet, "00" * 32)
        self.assertIn("changed while signing", str(err.exception))

    def test_a_script_that_is_not_multisig_is_refused(self):
        with self.assertRaises(SigningError):
            parse_multisig_script(b"\x00\x14" + b"\x11" * 20)
        with self.assertRaises(SigningError):
            parse_multisig_script(b"")


if __name__ == "__main__":
    unittest.main()

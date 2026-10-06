"""Pin the BIP-143 signature digest to Bitcoin's published test vectors.

This is the tripwire cycle 2 asked for (CT-26). The suite's own sign-then-verify
tests cannot catch a digest regression: they call the same function to create and
to check a signature, so a single-SHA256 (or any other) substitution stays green.
These values come from BIP-143 itself (public domain) and are independent of embit.

The last test recomputes the digest from the BIP text without calling
``Transaction.sighash_segwit`` at all. If embit's implementation drifts in any
way — including the exact single-SHA256 substitution cycle 2 demonstrated —
this file goes red before any device is asked to sign.
"""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embit import ec  # noqa: E402
from embit import transaction as T  # noqa: E402
from embit.script import Script  # noqa: E402


# --- Native P2WPKH example (BIP-143, SIGHASH_ALL) ---------------------------
P2WPKH_UNSIGNED = (
    "0100000002fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f"
    "0000000000eeffffffef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57"
    "b90ec68a0100000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85"
    "c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2"
    "f0167faa815988ac11000000"
)
# scriptCode for a P2WPKH input is the P2PKH template around the 20-byte hash,
# not the output's own scriptPubKey.
P2WPKH_SCRIPT_CODE = bytes.fromhex(
    "76a9141d0f172a0ecb48aee1be1f2687d2963ae33f71a188ac"
)
P2WPKH_AMOUNT = 600_000_000  # 6 BTC
P2WPKH_INDEX = 1
P2WPKH_DIGEST = (
    "c37af31116d1b27caf68aae9e3ac82f1477929014d5b917657d0eb49478cb670"
)
P2WPKH_SIGNATURE = (
    "304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a"
    "0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee"
)
P2WPKH_PUBKEY = (
    "025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee6357"
)

# --- Native P2WSH example (BIP-143, SIGHASH_SINGLE) -------------------------
P2WSH_UNSIGNED = (
    "0100000002fe3dc9208094f3ffd12645477b3dc56f60ec4fa8e6f5d67c565d1c6b9216b36e"
    "0000000000ffffffff0815cf020f013ed6cf91d29f4202e8a58726b1ac6c79da47c23d1bee"
    "0a6925f80000000000ffffffff0100f2052a010000001976a914a30741f8145e5acadf23f7"
    "51864167f32e0963f788ac00000000"
)
P2WSH_WITNESS_SCRIPT = bytes.fromhex(
    "21026dccc749adc2a9d0d89497ac511f760f45c47dc5ed9cf352a58ac706453880aeadab"
    "210255a9626aebf5e29c0e6538428ba0d1dcf6ca98ffdf086aa8ced5e0d0215ea465ac"
)
P2WSH_AMOUNT = 4_900_000_000  # 49 BTC
P2WSH_INDEX = 1
P2WSH_SIGHASH_SINGLE = 3
P2WSH_DIGEST = (
    "82dde6e4f1e94d02c2b7ad03d2115d691f48d064e9d52f58194a6637e4194391"
)
P2WSH_SIGNATURE = (
    "3044022027dc95ad6b740fe5129e7e62a75dd00f291a2aeb1200b84b09d9e3789406b6c0"
    "02201a9ecd315dd6a0e632ab20bbb98948bc0c6fb204f2c286963bb48517a7058e27"
)
P2WSH_PUBKEY = (
    "026dccc749adc2a9d0d89497ac511f760f45c47dc5ed9cf352a58ac706453880ae"
)


def sha256d(payload: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()


def compact_size(value: int) -> bytes:
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


def bip143_digest_sighash_all(tx: T.Transaction, input_index: int,
                              script_code: bytes, amount: int) -> bytes:
    """Independent BIP-143 SIGHASH_ALL digest, transcribed from the BIP.

    Deliberately does not call ``Transaction.sighash_segwit`` or any embit
    hash helper. This is the outside oracle.
    """
    hash_prevouts = sha256d(b"".join(
        bytes(reversed(inp.txid)) + inp.vout.to_bytes(4, "little")
        for inp in tx.vin
    ))
    hash_sequence = sha256d(b"".join(
        inp.sequence.to_bytes(4, "little") for inp in tx.vin
    ))
    hash_outputs = sha256d(b"".join(out.serialize() for out in tx.vout))
    inp = tx.vin[input_index]
    preimage = b"".join([
        tx.version.to_bytes(4, "little"),
        hash_prevouts,
        hash_sequence,
        bytes(reversed(inp.txid)),
        inp.vout.to_bytes(4, "little"),
        compact_size(len(script_code)) + script_code,
        int(amount).to_bytes(8, "little"),
        inp.sequence.to_bytes(4, "little"),
        hash_outputs,
        tx.locktime.to_bytes(4, "little"),
        (1).to_bytes(4, "little"),  # SIGHASH_ALL
    ])
    return sha256d(preimage)


class Bip143PublishedVectors(unittest.TestCase):
    def test_p2wpkh_digest_matches_the_published_bip143_value(self):
        tx = T.Transaction.parse(bytes.fromhex(P2WPKH_UNSIGNED))
        digest = tx.sighash_segwit(
            P2WPKH_INDEX, Script(P2WPKH_SCRIPT_CODE), P2WPKH_AMOUNT)
        self.assertEqual(digest.hex(), P2WPKH_DIGEST)

    def test_p2wpkh_published_signature_verifies_over_the_published_digest(self):
        tx = T.Transaction.parse(bytes.fromhex(P2WPKH_UNSIGNED))
        digest = tx.sighash_segwit(
            P2WPKH_INDEX, Script(P2WPKH_SCRIPT_CODE), P2WPKH_AMOUNT)
        signature = ec.Signature.parse(bytes.fromhex(P2WPKH_SIGNATURE))
        self.assertTrue(
            ec.PublicKey.parse(bytes.fromhex(P2WPKH_PUBKEY)).verify(signature, digest))

    def test_p2wsh_digest_matches_the_published_bip143_value(self):
        tx = T.Transaction.parse(bytes.fromhex(P2WSH_UNSIGNED))
        digest = tx.sighash_segwit(
            P2WSH_INDEX, Script(P2WSH_WITNESS_SCRIPT), P2WSH_AMOUNT,
            sighash=P2WSH_SIGHASH_SINGLE)
        self.assertEqual(digest.hex(), P2WSH_DIGEST)

    def test_p2wsh_published_signature_verifies_over_the_published_digest(self):
        tx = T.Transaction.parse(bytes.fromhex(P2WSH_UNSIGNED))
        digest = tx.sighash_segwit(
            P2WSH_INDEX, Script(P2WSH_WITNESS_SCRIPT), P2WSH_AMOUNT,
            sighash=P2WSH_SIGHASH_SINGLE)
        signature = ec.Signature.parse(bytes.fromhex(P2WSH_SIGNATURE))
        self.assertTrue(
            ec.PublicKey.parse(bytes.fromhex(P2WSH_PUBKEY)).verify(signature, digest))

    def test_an_independent_bip143_recomputation_matches_embit(self):
        """The outside oracle: same bytes, no embit hashing on the right-hand side.

        If ``sighash_segwit`` is replaced with a single SHA256 of the preimage —
        the exact break cycle 2 demonstrated leaves 362 tests green — this
        comparison fails.
        """
        tx = T.Transaction.parse(bytes.fromhex(P2WPKH_UNSIGNED))
        oracle = bip143_digest_sighash_all(
            tx, P2WPKH_INDEX, P2WPKH_SCRIPT_CODE, P2WPKH_AMOUNT)
        self.assertEqual(oracle.hex(), P2WPKH_DIGEST)
        embit = tx.sighash_segwit(
            P2WPKH_INDEX, Script(P2WPKH_SCRIPT_CODE), P2WPKH_AMOUNT)
        self.assertEqual(embit, oracle)

    def test_single_sha256_of_the_preimage_is_not_the_published_digest(self):
        """Name the substitution this file exists to catch, and refuse it."""
        tx = T.Transaction.parse(bytes.fromhex(P2WPKH_UNSIGNED))
        # Rebuild the preimage exactly as the oracle does, then hash ONCE.
        hash_prevouts = sha256d(b"".join(
            bytes(reversed(inp.txid)) + inp.vout.to_bytes(4, "little")
            for inp in tx.vin
        ))
        hash_sequence = sha256d(b"".join(
            inp.sequence.to_bytes(4, "little") for inp in tx.vin
        ))
        hash_outputs = sha256d(b"".join(out.serialize() for out in tx.vout))
        inp = tx.vin[P2WPKH_INDEX]
        preimage = b"".join([
            tx.version.to_bytes(4, "little"),
            hash_prevouts,
            hash_sequence,
            bytes(reversed(inp.txid)),
            inp.vout.to_bytes(4, "little"),
            compact_size(len(P2WPKH_SCRIPT_CODE)) + P2WPKH_SCRIPT_CODE,
            int(P2WPKH_AMOUNT).to_bytes(8, "little"),
            inp.sequence.to_bytes(4, "little"),
            hash_outputs,
            tx.locktime.to_bytes(4, "little"),
            (1).to_bytes(4, "little"),
        ])
        single = hashlib.sha256(preimage).digest()
        self.assertNotEqual(single.hex(), P2WPKH_DIGEST,
                            "a single-SHA256 digest must never equal BIP-143")
        self.assertEqual(sha256d(preimage).hex(), P2WPKH_DIGEST)


if __name__ == "__main__":
    unittest.main()

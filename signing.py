"""Finalise a signed multisig PSBT.

embit deliberately has no `finalize()` and no `combine()`: it parses and verifies
PSBTs and signs with a private key, but it never assembles the final transaction.
This app never holds a private key, so the hardware devices sign and this module puts
the result together.

Only native-SegWit m-of-n multisig is supported, which is all this app accepts. The
witness for such an input is:

    [ <empty>, sig1, sig2, ... , witness_script ]

The leading empty item is not padding: CHECKMULTISIG pops one item more than it uses,
a bug preserved in consensus, so the first witness item must be empty. The signatures
appear in the same order as their public keys appear in the witness script, and a
wallet that orders them differently produces a transaction the network rejects.
"""

from __future__ import annotations

from hashlib import sha256

from embit import ec, transaction
from embit.psbt import PSBT

# OP_0..OP_16
_OP_1_TO_16 = {0x50 + n: n for n in range(1, 17)}

# BIP-62 low-S: a signature whose S value exceeds n/2 is valid ECDSA but
# non-canonical. Bitcoin relay treats it as non-standard, so a malicious
# device can hand back a high-S signature that finalizes here and then fails
# to broadcast — an availability attack on the owner's payment.
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_HALF_ORDER = SECP256K1_ORDER // 2


def _is_low_s(der: bytes) -> bool:
    """True only when a DER ECDSA signature carries S <= n/2 (BIP-62).

    Parsed here rather than through embit so the gate is ours: a backend that
    accepts high-S at parse or verify time must not reach finalisation.
    """
    data = bytes(der)
    if len(data) < 8 or data[0] != 0x30 or data[1] != len(data) - 2:
        return False
    if data[2] != 0x02:
        return False
    r_len = data[3]
    if r_len < 1 or r_len > 33 or 4 + r_len >= len(data):
        return False
    if data[4 + r_len] != 0x02:
        return False
    s_len = data[5 + r_len]
    if s_len < 1 or s_len > 33 or 6 + r_len + s_len != len(data):
        return False
    s_bytes = data[6 + r_len:6 + r_len + s_len]
    if s_bytes[0] & 0x80:
        return False
    if s_len > 1 and s_bytes[0] == 0x00 and not (s_bytes[1] & 0x80):
        return False
    s = int.from_bytes(s_bytes, "big")
    return 0 < s <= SECP256K1_HALF_ORDER


class SigningError(Exception):
    """A signing or finalisation problem that should be shown to the user."""


def parse_multisig_script(script: bytes) -> tuple[int, list[bytes]]:
    """Return (threshold, public keys) from a multisig witness script."""
    if not script:
        raise SigningError("This input has no witness script to sign against.")
    data = bytes(script)
    header = data[0]
    if header not in _OP_1_TO_16:
        raise SigningError("This witness script is not a multisig script.")
    threshold = _OP_1_TO_16[header]
    keys: list[bytes] = []
    i = 1
    while i < len(data) and data[i] == 0x21:  # push of a 33-byte compressed key
        key = data[i + 1:i + 34]
        if len(key) != 33:
            raise SigningError("A public key in the witness script is malformed.")
        keys.append(key)
        i += 34
    if i >= len(data) or data[i] not in _OP_1_TO_16:
        raise SigningError("This witness script is not a multisig script.")
    if data[i] - 0x50 != len(keys):
        raise SigningError("The witness script's key count does not add up.")
    if len(data) != i + 2 or data[i + 1] != 0xAE:  # OP_CHECKMULTISIG
        raise SigningError("This witness script is not a multisig script.")
    if not 1 <= threshold <= len(keys):
        raise SigningError("The witness script's threshold is impossible.")
    # CT-72 second gate: the compiled script carries raw public keys, so this is
    # the one place where a duplicate signer cannot hide behind a spelling. A
    # script naming the same key twice is not a real 2-of-N: one device approval
    # fills both slots and the witness carries the same signature twice. The
    # parse-time gate is upstream of this, but the script is the object that
    # actually spends, so it refuses independently of how the PSBT was built.
    if len(set(keys)) != len(keys):
        raise SigningError("The witness script names the same public key more than once.")
    return threshold, keys


def partial_sigs_as_bytes(scope) -> dict[bytes, bytes]:
    """embit keys partial_sigs by PublicKey objects; the witness script is raw bytes.

    Normalising in one place is what lets the two be compared and, more importantly,
    ordered: the signatures must appear in the witness script's key order.
    """
    out: dict[bytes, bytes] = {}
    for key, signature in (scope.partial_sigs or {}).items():
        raw = key.sec() if hasattr(key, "sec") else bytes(key)
        out[bytes(raw)] = bytes(signature)
    return out


def verified_input_signatures(psbt) -> list[set[bytes]]:
    """Verify every BIP143 SIGHASH_ALL signature before calling an input complete.

    HWI output is an untrusted PSBT update. Counting partial-sig entries would
    allow malformed bytes to be described as a finished payment. The immutable
    transaction and verified prevouts are bound to the prepared PSBT in gui.py.
    """
    if len(psbt.inputs) != len(psbt.tx.vin):
        raise SigningError("The signed transaction's input count changed.")
    verified = []
    for index, (scope, txin) in enumerate(zip(psbt.inputs, psbt.tx.vin)):
        if scope.witness_script is None or scope.witness_utxo is None:
            raise SigningError(f"Input {index + 1} is missing its script or previous output.")
        threshold, keys = parse_multisig_script(scope.witness_script.data)
        if not 1 <= threshold <= len(keys) or not 2 <= len(keys) <= 3:
            raise SigningError("Only native-SegWit multisig wallets with two or three keys are supported.")
        expected_script = b"\x00\x20" + sha256(scope.witness_script.data).digest()
        if scope.witness_utxo.script_pubkey.data != expected_script:
            raise SigningError(f"Input {index + 1} has a witness script that does not own its output.")
        if (scope.non_witness_utxo is None
                or scope.non_witness_utxo.txid() != txin.txid
                or txin.vout >= len(scope.non_witness_utxo.vout)
                or scope.non_witness_utxo.vout[txin.vout].serialize()
                   != scope.witness_utxo.serialize()):
            raise SigningError(f"Input {index + 1} does not match its verified previous transaction.")
        valid = set()
        for pubkey, signature in partial_sigs_as_bytes(scope).items():
            if pubkey not in keys or len(signature) < 2 or signature[-1] != 1:
                raise SigningError(f"Input {index + 1} contains an unexpected signature or sighash type.")
            if not _is_low_s(signature[:-1]):
                raise SigningError(
                    f"Input {index + 1} contains a high-S signature (BIP-62 low-S required)."
                )
            try:
                parsed = ec.Signature.parse(signature[:-1])
                digest = psbt.tx.sighash_segwit(
                    index, scope.witness_script, scope.witness_utxo.value)
                if not ec.PublicKey.parse(pubkey).verify(parsed, digest):
                    raise ValueError("signature mismatch")
            except (ValueError, TypeError, RuntimeError) as exc:
                raise SigningError(f"Input {index + 1} contains an invalid signature.") from exc
            valid.add(pubkey)
        verified.append(valid)
    return verified


def accept_signature_update(before, after) -> PSBT:
    """Return the reviewed PSBT with only verified device signatures added.

    Some signers rewrite or add PSBT metadata while signing. Never trust or
    retain that metadata: build the result from the app's original PSBT and
    import only partial signatures, then verify them against its original
    transaction, prevouts and witness scripts. This also handles map reordering.
    """
    if len(before.inputs) != len(after.inputs) or len(before.outputs) != len(after.outputs):
        raise SigningError("The device changed the transaction's input or output count.")
    if before.tx.serialize() != after.tx.serialize():
        raise SigningError("The device returned a different transaction.")
    prior = [partial_sigs_as_bytes(scope) for scope in before.inputs]
    later = [partial_sigs_as_bytes(scope) for scope in after.inputs]
    for old, new in zip(prior, later):
        if any(new.get(key) != sig for key, sig in old.items()):
            raise SigningError("The device removed or changed an earlier signature.")
    try:
        # Make a separate packet so a failed verification cannot mutate the
        # in-memory reviewed payment. All non-signature fields remain ours.
        merged = PSBT.from_base64(before.to_base64())
        for original, received in zip(merged.inputs, after.inputs):
            original.partial_sigs.update(received.partial_sigs)
        verified_input_signatures(merged)
        return merged
    except SigningError:
        raise
    except Exception as exc:
        raise SigningError("The device returned a transaction that cannot be checked.") from exc


def _compact_size(value: int) -> int:
    """Bytes a Bitcoin CompactSize takes for this value."""
    if value < 0xFD:
        return 1
    if value <= 0xFFFF:
        return 3
    if value <= 0xFFFFFFFF:
        return 5
    return 9


def virtual_size(tx, raw: bytes) -> int:
    """BIP141 virtual size.

    embit exposes no size helpers, so the stripped size is computed from the same
    fields its txid preimage uses, and the witness bytes are whatever the full
    serialisation adds on top -- which includes the two marker/flag bytes, exactly as
    the weight formula expects.
    """
    stripped = 4 + _compact_size(len(tx.vin))
    stripped += sum(len(vin.serialize()) for vin in tx.vin)
    stripped += _compact_size(len(tx.vout))
    stripped += sum(len(out.serialize()) for out in tx.vout)
    stripped += 4
    if len(raw) < stripped:
        raise SigningError("The finalised transaction is smaller than its own skeleton.")
    weight = stripped * 4 + (len(raw) - stripped)
    return (weight + 3) // 4


def signatures_collected(psbt) -> tuple[int, int]:
    """(signatures present, threshold) across every input, for progress display."""
    present = None
    threshold = 0
    valid_by_input = verified_input_signatures(psbt)
    for scope, valid in zip(psbt.inputs, valid_by_input):
        need, keys = parse_multisig_script(scope.witness_script.data)
        threshold = max(threshold, need)
        have = [k for k in keys if k in valid]
        present = len(have) if present is None else min(present, len(have))
    return present or 0, threshold


def signed_by_signers(psbt, record) -> list[int]:
    """The wallet's cosigners that have signed, as 1-based signer numbers.

    The PSBT records the fingerprint for every public key that produced a signature,
    so this needs no guesswork about which device did what.
    """
    numbers = {key.fingerprint.hex(): index
               for index, key in enumerate(record.keys, start=1)}
    signed: set[int] | None = None
    for scope in psbt.inputs:
        input_signed: set[int] = set()
        derivations = scope.bip32_derivations or {}
        for pubkey in (scope.partial_sigs or {}):
            path = derivations.get(pubkey)
            if path is None:
                continue
            number = numbers.get(path.fingerprint.hex())
            if number is not None:
                input_signed.add(number)
        signed = input_signed if signed is None else signed & input_signed
    return sorted(signed or set())


def is_complete(psbt) -> bool:
    present, threshold = signatures_collected(psbt)
    return bool(threshold) and present >= threshold


def finalize_multisig(psbt, expected_txid: str) -> dict:
    """Assemble the final transaction, refusing anything that does not add up.

    `expected_txid` is the id shown at review time. SegWit keeps signatures outside
    the transaction id, so it cannot change between review and broadcast; if it has,
    the file is not the transaction that was reviewed and this stops.
    """
    if not psbt.inputs:
        raise SigningError("This transaction has no inputs.")

    valid_by_input = verified_input_signatures(psbt)

    used_signatures = 0
    for index, (scope, valid) in enumerate(zip(psbt.inputs, valid_by_input), start=1):
        if not scope.witness_script:
            raise SigningError(f"Input {index} has no witness script; cannot finalise.")
        threshold, keys = parse_multisig_script(scope.witness_script.data)
        partial = partial_sigs_as_bytes(scope)
        ordered = [partial[key] for key in keys if key in valid]
        if len(ordered) < threshold:
            raise SigningError(
                f"Input {index} has {len(ordered)} of {threshold} required signatures."
            )
        # Signatures must be in witness-script key order; take only what is needed.
        witness_items = [b""] + ordered[:threshold] + [bytes(scope.witness_script.data)]
        used_signatures += len(ordered[:threshold])
        scope.final_scriptwitness = transaction.Witness(witness_items)
        scope.partial_sigs = {}

    tx = psbt.tx
    for index, scope in enumerate(psbt.inputs):
        tx.vin[index].witness = scope.final_scriptwitness

    raw = tx.serialize()
    txid = tx.txid().hex()
    if expected_txid and txid != expected_txid:
        raise SigningError(
            "The transaction id changed while signing, so this is not the transaction "
            "that was reviewed. Nothing should be broadcast."
        )

    total_in = 0
    for scope in psbt.inputs:
        if scope.witness_utxo is None:
            raise SigningError("An input is missing the value it spends.")
        total_in += scope.witness_utxo.value
    total_out = sum(out.value for out in tx.vout)
    if total_out > total_in:
        raise SigningError("The outputs exceed the inputs; refusing to finalise.")

    return {
        "raw_transaction_hex": raw.hex(),
        "txid": txid,
        "vsize": virtual_size(tx, raw),
        "size": len(raw),
        "fee_sats": total_in - total_out,
        "signatures": used_signatures,
    }

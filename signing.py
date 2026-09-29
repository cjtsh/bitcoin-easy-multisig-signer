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

from embit import transaction

# OP_0..OP_16
_OP_1_TO_16 = {0x50 + n: n for n in range(1, 17)}


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
    if len(data) < i + 2 or data[i + 1] != 0xAE:  # OP_CHECKMULTISIG
        raise SigningError("This witness script is not a multisig script.")
    if not 1 <= threshold <= len(keys):
        raise SigningError("The witness script's threshold is impossible.")
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
    present = 0
    threshold = 0
    for scope in psbt.inputs:
        if not scope.witness_script:
            continue
        need, keys = parse_multisig_script(scope.witness_script.data)
        threshold = max(threshold, need)
        have = [k for k in keys if k in partial_sigs_as_bytes(scope)]
        present = max(present, len(have))
    return present, threshold


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

    used_signatures = 0
    for index, scope in enumerate(psbt.inputs, start=1):
        if not scope.witness_script:
            raise SigningError(f"Input {index} has no witness script; cannot finalise.")
        threshold, keys = parse_multisig_script(scope.witness_script.data)
        partial = partial_sigs_as_bytes(scope)
        ordered = [partial[key] for key in keys if key in partial]
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

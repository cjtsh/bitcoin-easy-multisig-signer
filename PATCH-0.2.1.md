# 0.2.1 signer regression and operator feedback

## What happened

The owner's first 0.2.0 Apple Silicon walkthrough found that both Jade and Ledger reached on-device signing, but the app did not count either signature. The opt-in 0.2.0 diagnostic report shows `signer_response: rejected` after device approval on four attempts. It contains no wallet material. No 0.2.0 transaction was broadcast. A prior release had completed Testnet4 payments with Jade + Trezor and Jade + Ledger.

The 0.2.0 implementation compared two **serialized PSBTs** after removing partial signatures. That assumes field order is preserved. HWI 3.2.0 parses the PSBT and serializes its key/value maps in sorted order, so it changes the bytes of an otherwise identical PSBT. The 0.2.0 guard then rejects a valid signature with “The device changed the reviewed transaction or its wallet data.” A local synthetic PSBT passed through the actual HWI 3.2.0 parser/serializer reproduces the rejection before the patch and acceptance afterward.

## Correction and security boundary

`signing._psbt_maps` reads each PSBT map as a set of exact key/value pairs, rejects duplicate keys or trailing data, and ignores insertion order. `accept_signature_update` compares **every** non-signature key and value in the global, input and output maps. Only input partial-signature entries may be added; prior signatures cannot be removed or changed. Every signature must still pass BIP143 ECDSA/SIGHASH_ALL verification against the unchanged script, prevout, amount and transaction. A response changing any reviewed metadata or output still fails. The finalizer and broadcast checks from 0.2.0 remain in place.

The `ui.html` activity bar now uses high-contrast yellow. Device discovery also turns its active button yellow and explains that searching often takes 10–15 seconds. A signing rejection is shown as a red message scrolled into view, instead of seeming to leave the interface idle. An outdated advanced-settings claim that Testnet4 broadcast was unimplemented was corrected.

## Verification and acceptance

The regression test changes PSBT field order after a valid signature and checks that it is accepted. Existing tests continue to reject changed UTXO metadata and malformed signatures. On 2026-09-29, 143 local tests passed and the extracted source archive passed the same 143 tests; JavaScript and shell syntax checks passed. An additional synthetic PSBT round trip through the actual HWI 3.2.0 serializer accepted a valid signature and rejected changed fee metadata. No real wallet data was used. The Apple Silicon CI bundle checks, release hashes and owner hardware test remain pending. Record the successful workflow run and published asset hashes here. Version 0.2.1 remains **unaccepted** until the owner signs one controlled Testnet4 transaction with two real devices, sees both signatures counted, verifies all outputs and fees, broadcasts deliberately, and independently observes confirmation. Do not request wallet files, addresses, xpubs, PSBTs or signed bytes for debugging.

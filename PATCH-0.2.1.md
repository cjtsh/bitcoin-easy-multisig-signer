# 0.2.1 signer regression and operator feedback

## What happened

The owner's first 0.2.0 Apple Silicon walkthrough found that both Jade and Ledger reached on-device signing, but the app did not count either signature. The opt-in 0.2.0 diagnostic report shows `signer_response: rejected` after device approval on four attempts. It contains no wallet material. No 0.2.0 transaction was broadcast. A prior release had completed Testnet4 payments with Jade + Trezor and Jade + Ledger.

The 0.2.0 implementation compared two **serialized PSBTs** after removing partial signatures. That assumes field order is preserved. HWI 3.2.0 parses the PSBT and serializes its key/value maps in sorted order, so it changes the bytes of an otherwise identical PSBT. The 0.2.0 guard then rejects a valid signature with “The device changed the reviewed transaction or its wallet data.” A local synthetic PSBT passed through the actual HWI 3.2.0 parser/serializer reproduces the rejection before the patch and acceptance afterward.

## Correction and security boundary

`signing._psbt_maps` reads each PSBT map as a set of exact key/value pairs, rejects duplicate keys or trailing data, and ignores insertion order. `accept_signature_update` compares **every** non-signature key and value in the global, input and output maps. Only input partial-signature entries may be added; prior signatures cannot be removed or changed. Every signature must still pass BIP143 ECDSA/SIGHASH_ALL verification against the unchanged script, prevout, amount and transaction. A response changing any reviewed metadata or output still fails. The finalizer and broadcast checks from 0.2.0 remain in place.

The `ui.html` activity bar now uses high-contrast yellow. Device discovery also turns its active button yellow and explains that searching often takes 10–15 seconds. A signing rejection is shown as a red message scrolled into view, instead of seeming to leave the interface idle. An outdated advanced-settings claim that Testnet4 broadcast was unimplemented was corrected.

## Verification and acceptance

The regression test changes PSBT field order after a valid signature and checks that it is accepted. Existing tests continue to reject changed UTXO metadata and malformed signatures. On 2026-09-29, 143 local tests passed and the extracted source archive passed the same 143 tests; JavaScript and shell syntax checks passed. An additional synthetic PSBT round trip through the actual HWI 3.2.0 serializer accepted a valid signature and rejected changed fee metadata. No real wallet data was used.

[GitHub workflow run 36581873375](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36581873375) passed every source, Apple Silicon bundle, checksum and publication job. The published [v0.2.1 release](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.2.1) targets `70a10567ed6eb5b26516fa820b2f5633ae304dce`. Published assets were downloaded anew and passed `shasum -a 256 -c SHA256SUMS`; `hdiutil verify` passed on the DMG. SHA-256: DMG `82ff112544eb366f22de1e888a3612922667b791aabe3fcfdd66598ced62911c`; source archive `85e12694df66a583e95bc688080762cdcfdc9dec8e476aa983119fea5e10e719`; SBOM `8f3bedc7c4148aca72be9b0f8e1646a21897cd5972afc09abf14c4bd43edb636`. The CycloneDX 1.6 SBOM lists 39 components and the release commit/run.

**Owner walkthrough, 2026-09-29:** the opt-in 0.2.1 diagnostic report records two `signer_response: verified` events, `final_transaction: verified`, and `broadcast: accepted`. The user provided a public Testnet4 explorer link; the explorer API found the transaction in its mempool, unconfirmed at 14:35 UTC. The report also contains two earlier generic `request: rejected` events; it cannot identify their causes, and they did not stop this payment. The diagnostic file and transaction identifier are not committed to the repository. The successful device models and on-device review details still need the owner's confirmation.

Version 0.2.1 has passed real-device signing and broadcast, but **acceptance remains pending** until the owner confirms device-screen review and the transaction confirms on Testnet4. Do not request wallet files, addresses, xpubs, PSBTs or signed bytes for debugging.

**Next owner check:** after the first payment confirms, refresh the same wallet and make one more small self-owned Testnet4 payment using the Trezor plus one signer already exercised in 0.2.1. Confirm the Trezor contributes a counted signature, review recipient/change/fee on both devices and the final app screen, broadcast deliberately, and independently observe confirmation. If other confirmed UTXOs exist, the app may offer another send before the first confirms; waiting avoids confusing pending change with spendable funds. The app cannot spend unconfirmed change and has no built-in fee bump. Do not enable mainnet broadcast as part of this check.

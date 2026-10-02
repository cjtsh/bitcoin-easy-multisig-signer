# 0.3.1 explicit Send All and Mutinynet default

## Owner report and cause

In the first v0.3.0 Mutinynet walkthrough, the owner imported a funded Nunchuk 2-of-3 wallet and saw Send All checked and unchangeable; the amount box was disabled. The locally inspected test-wallet BSMS has three `/*` suffixes and `No path restrictions`. It verifies the first receive address against `/0/0` but contains no change policy. No wallet identifiers are recorded here or committed. The app correctly refused a partial payment yet incorrectly preselected a full-wallet sweep.

## Correction

- Mutinynet is the opening network. Testnet4 and mainnet remain selectable, using the same wallet, PSBT and signing engine with network-specific parameters.
- When the wallet definition does not establish change, **Send All stays unchecked** and the amount box is disabled. A plain-language note explains why. The owner must choose Send All deliberately before review. The app never silently turns a small intended payment into a sweep.
- The wallet parser and change-path guard remain conservative for every network. BIP48 specifies conventional `/0/*` and `/1/*` paths, but this BSMS file does not commit Nunchuk to the latter. Nunchuk's BSMS implementation emits `/*` for ordinary multisig regardless of the signers' external/internal indices. See [BIP48](https://github.com/bitcoin/bips/blob/master/bip-0048.mediawiki) and [Nunchuk's BSMS writer](https://github.com/nunchuk-io/libnunchuk/blob/33f7dc36b4251cd2042ee1e796c90250b4438979/src/utils/bsms.hpp).
- The Node UI test covers Mutinynet default, a receive-only import that leaves Send All unchecked, and an explicit owner sweep choice. Existing Python tests keep receive-only custom sends blocked.

## Unresolved cross-wallet proof

A custom amount from the owner's current Nunchuk BSMS requires an independent same-wallet receive/change policy. Nunchuk Desktop's generic “As descriptor” export contains only the receiving side for an ordinary multisig wallet. The owner does not want a Coldcard-associated workflow, and no such workflow is included in this patch. No developer should infer `/1/*` merely from the origin path or a matching first receive address: custom internal branch indices are possible. The wallet still needs no new seeds or funding if a full public policy export can be obtained.

## Release and owner gate

The manual [GitHub workflow](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36605051264) passed all five jobs and published [v0.3.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.3.1) from commit `b623c0dbe546510d9241f47b1a7fcabe739185e3`. The checkout and extracted source archive each passed 164 Python tests (8 skipped) plus both Node UI tests. GitHub verified the Apple Silicon DMG, ad-hoc signature, bundled HWI and its stdin path, libusb hash, frozen self-checks and trust store. The source, DMG and SBOM assets were downloaded independently and matched `SHA256SUMS`; `hdiutil verify` passed on the downloaded DMG. The published SHA-256 values are:

```text
94455a1e0265a93a4ad6ca027a32a7558c9dda42a5c461e4d6cc0180b71c62de  bitcoin-easy-multisig-signer-v0.3.1.tar.gz
5a1569b6f2a9931cd7ddb8233659ba8d61b4c8e69aa213aaad447d5ec7b0fb7c  Bitcoin-Easy-Signer-v0.3.1-UNSIGNED-TEST.dmg
e5811e7bd7f9d0ac06f260a78162d407bd520383c3c3eb1ec937b166d7767397  BUILD-SBOM.json
```

Do not ask the owner to install or sweep merely to verify a UI correction. The physical Mutinynet signing/broadcast and second-payment screen-reset checks remain open. Mainnet broadcast remains disabled pending a separate live-network safety gate.

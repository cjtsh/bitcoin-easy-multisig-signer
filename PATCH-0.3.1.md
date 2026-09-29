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

Automated and release evidence will be recorded after the manual 0.3.1 workflow if this patch is published. Do not ask the owner to install or sweep merely to verify a UI correction. The physical Mutinynet signing/broadcast and second-payment screen-reset checks remain open. Mainnet broadcast remains disabled pending a separate live-network safety gate.

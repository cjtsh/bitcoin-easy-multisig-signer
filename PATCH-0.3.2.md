# 0.3.2 — BSMS-only BIP48 change recovery

## Status

Version [0.3.2](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.3.2) is published as an Apple Silicon test build. The owner installed 0.3.0 and 0.3.1 but could not enter a custom amount with their Nunchuk Mutinynet BSMS. The owner subsequently reported **two successful Mutinynet sends** from 0.3.2 using Ledger + Trezor and Jade + Trezor, including a second payment without restarting the app. This is owner-reported physical acceptance of the BSMS-only custom-send and repeated-payment flow; no diagnostics, transaction IDs, or device-screen details were supplied for independent verification. Mainnet broadcasting stays disabled.

## Owner requirement

The recovery operator has **one BSMS file**. A spouse, lawyer or accountant must not need to locate Nunchuk's database or produce a second export. A rejected interim design requested that database; it was removed before release. There is no database picker, importer, committed database, or second-file workflow in 0.3.2. The ordinary Nunchuk BSMS must allow a smaller send when it matches the supported BIP48 policy.

## Standards and source evidence

- [BIP48](https://github.com/bitcoin/bips/blob/master/bip-0048.mediawiki) defines `m/48'/coin_type'/account'/2'/change/index` for native-SegWit multisig and assigns `/0/*` to receiving and `/1/*` to change.
- [BIP129](https://github.com/bitcoin/bips/blob/master/bip-0129.mediawiki) allows a BSMS record with `No path restrictions`; that line does not explicitly commit a change path.
- [Nunchuk's BSMS writer](https://github.com/nunchuk-io/libnunchuk/blob/33f7dc36b4251cd2042ee1e796c90250b4438979/src/utils/bsms.hpp) emits `/*` and `No path restrictions` for ordinary multisig, regardless of custom branch indices. Its [descriptor parser](https://github.com/nunchuk-io/libnunchuk/blob/33f7dc36b4251cd2042ee1e796c90250b4438979/src/descriptor.cpp) defaults an unspecified external/internal pair to `{0,1}` when reconstructing a wallet. Thus the one-file BIP48 recovery policy is also the policy Nunchuk reconstructs from this export.

The last point is a **scope limit**, not proof that every historical/custom Nunchuk wallet used `/1/*`. A custom branch index can be lost in an ordinary BSMS export. This app accepts the standard BIP48 policy for its supported recovery flow and labels change as standard-derived, not BSMS-declared. A custom-layout wallet needs a complete wallet definition and remains outside the one-file fallback.

## Code and safety gates

`wallet_service.wallet_layout` expands a bare `/*` to receive `/0/*` only when the BSMS first address matches. A standard-derived change `/1/*` is enabled only for native-SegWit **sorted 2-of-3 multisig** whose three origins share the same four-level BIP48 account path ending in hardened `2'`. Parser network checks require mainnet coin type `0'` or practice-network coin type `1'`. Both branch descriptors retain the exact public xpubs, fingerprints and threshold. Unsupported origins or an address mismatch fail closed; a nonstandard file can still explicitly choose a no-change Send All of scanned confirmed outputs.

The app visibly distinguishes a standard-derived change from a declared change. The unsigned review and final transaction show its full address and amount, and the operator is told to check change on each signer. Diagnostics use the fixed `change_path: standard` code, without addresses or keys. The same PSBT builder and signer path serve Testnet4, Mutinynet and mainnet; no network-specific engine or extra import was created. The existing mainnet broadcast refusal remains.

## Verification and owner walkthrough

Tests use synthetic keys. They cover bare `/*`, explicit `/0/*`, custom amount and two-output PSBT construction, nonstandard origin rejection, Mutinynet loopback import/scan/estimate/prepare, mainnet coin type `0'`, and UI amount availability while Send All stays unchecked. The actual locally supplied `MultiMutiny.bsms` was parsed without printing or committing its identifiers; the 0.3.2 wallet summary enables a custom amount and labels change as standard-derived. A **read-only live Mutinynet check** using that file found a consistent funded scan with complete configured coverage, then constructed an unsigned 1,000-sat custom-payment PSBT with change to a derived test destination. No PSBT was saved, signed or broadcast. These checks still cannot prove the owner's hardware signer or Nunchuk wallet accepts the exact change address.

**Owner walkthrough, 29 September 2026:** the owner installed 0.3.2 and reported two successful Mutinynet transactions from the Nunchuk BSMS, one signed with Ledger + Trezor and one with Jade + Trezor. The second was prepared and sent without reloading the app, so the previously blocking stale final panel did not prevent a repeated payment. The owner described the second payment as validating almost immediately. The first showed a block-explorer view/link, while the second did not. This visual difference did not block the payment. In `ui.html`, the pending-payment notice and its explorer link are hidden after a scan reports confirmation, so fast confirmation is one possible explanation; the exact screen sequence is unverified. Retain this as a minor UI observation for 0.4.0: show a persistent last-payment receipt with a transaction/explorer link after confirmation. Do not ask the owner for another payment solely to reproduce it. The owner did not supply transaction IDs or a diagnostic report, and their statement does not establish on-device review details or mainnet readiness.

## Release evidence

The manual [GitHub workflow](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36611530169) succeeded in all five jobs and published [v0.3.2](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.3.2) from merge commit `b654d9e99b058f2179236b659d523a98d8f8d7ba`. The checkout and extracted source each passed 166 Python tests (8 skipped) and both Node UI tests. GitHub's Apple Silicon job ran the tests, built the DMG, verified the bundled app and ad-hoc signature, inventoried dependencies, then published the source, DMG, SBOM and checksums. Independently downloaded release assets all matched `SHA256SUMS`; `hdiutil verify` confirmed the downloaded DMG image. SHA-256 values:

```text
9681f03fb7c18747fd4e3c5c4a124ec8a6f63c2c58d455d5b5e189ad04cf37e6  bitcoin-easy-multisig-signer-v0.3.2.tar.gz
79e537512822099b8e25e84e039b7322fff9a11e857c9a77983a89b0c68d07d0  Bitcoin-Easy-Signer-v0.3.2-UNSIGNED-TEST.dmg
9923b0f91d18febca8b667570fd8129de13ca201a22c0131571a7e79d48db0b9  BUILD-SBOM.json
```

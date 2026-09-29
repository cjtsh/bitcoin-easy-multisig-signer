# 0.3.2 — BSMS-only BIP48 change recovery

## Status

This is the 0.3.2 candidate. The owner installed 0.3.0 and 0.3.1 but could not enter a custom amount with their Nunchuk Mutinynet BSMS. **No 0.3.x Mutinynet transaction has yet been signed or broadcast by the owner.** Do not claim physical acceptance based on automated checks. Mainnet broadcasting stays disabled.

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

After publication, the owner should install **one** 0.3.2 DMG and run a small custom Mutinynet payment using only `MultiMutiny.bsms`. Compare destination, amount, fee and change with the hardware displays before approval; get two device signatures, broadcast and confirm. Then prepare another payment to verify the old signing/final panel is cleared. If a step fails, request the privacy-limited diagnostic report and a description of the device screen, not keys, wallet files or signed bytes. Keep the 0.3.x owner gate open until this succeeds.

## Release evidence

Pending manual GitHub workflow and downloaded-asset verification.

# Current handoff — Bitcoin Easy Signer

## Current stop point — 0.4.13, mainnet dry run pending

The current published version is [v0.4.13](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.13), with source version `0.4.13` in `version.py`. The owner has not reported a physical transaction walkthrough on 0.4.13. Do not treat Phase 5 as accepted or enable mainnet broadcast while its gates remain open. Earlier physical Mutinynet payments, including a confirmed 0.4.1 Ledger + Jade payment, are recorded in `RELEASE-HISTORY.md`. No mainnet payment has been prepared, signed, or broadcast by this app.

The owner supplied two BSMS exports of the **same practice wallet**, one from Sparrow and one from Nunchuk. A read-only comparison found identical cosigner keys/origins, first receive address, and receive/change scripts at indices 0–19. Sparrow declares both paths; Nunchuk leaves them unstated and the app uses a strictly gated BIP48 standard inference. `CHANGE-ADDRESS-REVIEW.md` records the limits. These test-wallet exports do not establish the policy of a different live mainnet wallet. No wallet identifiers or files were committed.

**Next owner gate:** complete a **mainnet dry run** with the real wallet: import its BSMS, verify its change policy against the wallet and signer displays, prepare a small payment to an owner-controlled destination, obtain two device approvals, and independently check the finalized inputs, outputs, change, fee, and txid. Keep the signed transaction private and **do not broadcast**. Record the app version and stages completed; if there is an error, use only the privacy-limited diagnostic report. A live send requires separate fee-policy review, a deliberate mainnet-broadcast code change, and explicit authorization. Do not ask the recovery operator for a second wallet file, a Nunchuk database, seed words, or path decisions.

## 0.4.1 accepted on Ledger and Jade; 0.4.3 change-path correction published

The owner's 0.4.0 Jade attempt was rejected twice after transaction preparation. The diagnostic report identifies the signer-response boundary but omits the changed PSBT field. The same signing engine shipped in 0.3.2, which the owner reported worked on Jade; the precise device-side difference is unknown. Ledger then asked for two review rounds; a failed request about 46 seconds after its check is consistent with the old 45-second HWI limit. A later attempt showed HWI “open failed,” before a signature response; its specific device-connection cause is unknown. `PATCH-0.4.1.md` documents the correction: retain the reviewed PSBT and import only signatures that verify against it, allow ten minutes for signing only, and give targeted Ledger reconnect guidance. The owner then reported an installed 0.4.1 Ledger + Jade Mutinynet payment; the privacy-limited report recorded two verified signer responses, verified finalization and accepted broadcast, and Mutinynet subsequently reported confirmation. The owner also found Jade PIN entry during discovery can exceed one minute; 0.4.2 gives discovery and matched-device xpub checks three minutes. That wait change is not yet physically tested. Mainnet broadcast remains disabled.

**Start here for any agent or independent reviewer.** Read `AGENTS.md`, then this file, `RELEASE-HISTORY.md`, `CHANGE-ADDRESS-REVIEW.md`, and the current code. The release-history entries link each version's full evidence record (`PATCH-*.md`, `PLAN-0.3.0.md`, `MUTINYNET-0.3.0.md`, `AUDIT-BASELINE-0.1.27.md`, `SECURITY-REVIEW-0.2.0.md`). `PROJECT-HISTORY.md` and the older phase text in `ROADMAP.md` are historical evidence, not current capability claims.

## Status and version policy

The current published build is [v0.4.13](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.13). The full version-by-version record — including the 0.2.0 hardware-signing failure ("do not use"), the 0.2.1 field-order correction, the 0.3.x Mutinynet and one-file BSMS work, the 0.4.1 physical payment, and the later interface and notarization work — lives in `RELEASE-HISTORY.md`. The owner has not reported a physical transaction walkthrough on 0.4.13. Mainnet broadcast remains refused in code; no mainnet payment has ever been prepared, signed, or broadcast by this app.

Use a new patch version for any correction to a published build. The owner prefers milestone-based Mac installs after extensive automation rather than repeated installs for small revisions. The installed 0.2.1 app showed a new unsigned review above the previous payment's signing/final screen; **never broadcast from such a mixed screen — close the old app before installing a newer release.** The UI regression tests cover that reset. Mutinynet is the fast practice path; Testnet4 remains available for the existing wallet.

## Product goal

The user is a spouse, lawyer, accountant, or estate planner with little Bitcoin knowledge, recovering from an existing multi-vendor 2-of-3 multisig wallet. Keep the screen's decisions plain. Put descriptor and key technicalities in automatic checks or optional wallet details. Never ask this person to certify a derivation path or inspect a PSBT to make the tool work. They must still compare the payment on each hardware device and confirm the final transaction.

## Current behavior and safety boundaries

1. One engine in `wallet_service.py` and `signing.py` serves Testnet4, Mutinynet and mainnet. `network_config.py` selects BIP48 coin type, address prefix, genesis/checkpoint hashes and Esplora endpoint. `gui.py` applies network-specific safety rules and refuses mainnet broadcast.
2. A partial send uses a two-branch descriptor, a BSMS `/**` template with `/0/*,/1/*` restrictions, an explicit restrictions line, or the strict BIP48 standard fallback described in `PATCH-0.3.2.md`. `No path restrictions` does not *declare* change; the standard fallback is labelled as derived. Nunchuk's BSMS importer itself defaults an unspecified signer branch pair to `{0,1}`. Custom historical branch indices can be lost in Nunchuk's ordinary BSMS export; such layouts are outside this fallback. Unsupported files remain explicit no-change Send All only. The scan can still miss funds outside its gap/range.
3. `build_unsigned_psbt` checks each chosen previous transaction's txid, value and derived script. It stores a reviewed recipient, amount, fee, change and txid in local session state. In 0.4.1, `accept_signature_update` copies only device signatures into a clone of the reviewed PSBT, verifies them over BIP143 SIGHASH_ALL against the original transaction and discards signer-returned metadata. A different unsigned transaction or removed prior signature fails. `finalize_multisig` repeats signature and witness/prevout checks. Finalization and broadcast compare every final output and fee against the reviewed state. Broadcast holds the session lock through submission so a concurrent refresh cannot change the payment mid-submit.
4. The final screen shows network, full destination, amount, change address/amount, absolute fee, effective fee rate, signer numbers and txid together. A distinct confirmation submits only on a practice network. Mainnet shows a dry-run conclusion and no broadcast control; the backend also refuses it. A new review clears the entire old signing/final section before preparation begins. In 0.4.0, the confirmed-payment explorer link remains as a receipt in the current browser session; pending and confirmed status still come from the blockchain scan.
5. Diagnostics are opt-in. The UI button saves `bitcoin-easy-signer-diagnostics-0.3.0.json` (or a numbered variant) to Downloads, mode 0600. Events use fixed stage/outcome codes and timestamps only. No addresses, xpubs, fingerprints, PSBTs, raw transactions, amounts, device paths, or exception messages enter this file. Agents may request it after a failed owner walkthrough; never request wallet material.

## Reviewer checklist

- Challenge the BSMS branch logic, especially exports whose descriptor and restrictions disagree. Confirm the strict BIP48 fallback applies only to standard sorted 2-of-3 origins and the checked first receive address; nonstandard layouts must not construct a change output.
- Challenge signer response binding. A different unsigned transaction, removed prior signature, bad DER/ECDSA signature, or non-ALL sighash must fail. Device-returned prevout/script/derivation/global xpub/output metadata must never enter the stored payment, even if Jade rewrites it. Reordered PSBT fields must pass. Confirm legitimate HWI responses from **each** supported physical model; the 0.4.0 Jade rejection and 0.4.1 correction need a new physical walkthrough.
- Verify the final review screen against the exact finalized transaction. Check no stale API request can alter a broadcast in flight. Mainnet broadcast refusal must hold at the API level.
- Verify the diagnostic report's privacy by inspecting the saved file. Check build locks, mandatory `LIBUSB_SHA256`, CycloneDX `BUILD-SBOM.json`, signed bundle structure, test archive, source/DMG hashes and immutable tag.
- Distinguish unit/integration results from a real device walkthrough. A passing test suite cannot establish firmware display behavior.

## Build and owner test

Use Python 3.12; run `python -m unittest discover -s tests -q`, the Node UI regression, Bash syntax checks, source archive tests, and packaged Mac self-checks. The GitHub workflow is manual dispatch only. It installs hash-locked dependencies, requires an expected libusb digest, builds the Apple Silicon DMG, verifies the extracted bundle, inventories its dependencies in `BUILD-SBOM.json`, writes `SHA256SUMS`, and publishes a new tag only if none exists. Per-release runs, commits, hashes and owner gates are recorded in the `PATCH-*.md` evidence files indexed by `RELEASE-HISTORY.md`.

The controlled 0.2.1 Testnet4 payment signed with two devices, was accepted by the broadcaster and later confirmed. The owner began another payment and discovered the stale signing/final-panel bug; no new Trezor signature or second payment result was reported for that older build. With 0.3.2, the owner reports two successful Mutinynet sends from the **existing BSMS alone**. The second proceeded without reloading the app. The first displayed an explorer view/link; the second did not and reportedly validated almost immediately. Current UI hides the pending explorer link once confirmation is observed, which may explain the visual difference. Record a persistent receipt/link as a 0.4.0 UI improvement; do not request a third payment solely for this. If future device signing fails, request only the diagnostic report and a plain-language description of its screen. Do not request signed bytes or keys.

## Remaining Phase 5 dependencies

Current UTXO checks still depend on public explorers (dual-source on mainnet, single-source recheck on practice networks), and fee replacement remains outside this app. Mainnet dry run and a deliberate owner-authorized real send are separate Phase 5 gates; do not enable mainnet broadcast merely because a practice-network walkthrough passes. The plain-language operator guide and the nontechnical-user walkthrough are also unfinished; see `ROADMAP.md` Phase 5 for the full sequence.

## Developer ID signing and notarization — complete for published release

Version 0.4.12 was the first Developer ID-signed and Apple-notarized release. Version 0.4.13 corrected the staple order: the app is stapled before the DMG is built, then the finished image is mounted and the app copy inside is validated. See `RELEASE-HISTORY.md` for the release evidence and artifact checks.

`scripts/build-macos.sh` with `RELEASE=1` signs nested Mach-O files (including bundled `hwi`) with the hardened runtime, seals the `.app`, submits to Apple, staples, validates, and checks Gatekeeper acceptance. `scripts/notary-args.sh` refuses partial or ambiguous credential configuration. The workflow exposes notarization as an explicit dispatch input:

```
gh workflow run build-candidate.yml --ref main -f notarize=true
```

With `notarize` off, a run produces an `-UNSIGNED-TEST.dmg`. With it on, the run **fails closed** unless the signing and notarization credentials are present; it cannot quietly produce an ad-hoc-signed image under a notarized release path. Keep credential values in GitHub Actions secrets/variables or the local keychain, never in this repository or a chat. The separate Apple Developer instructions document is the canonical setup reference.

Do not assess the DMG itself with `spctl`: a disk image is not executable code. Validate both staples and assess the app, including the copy mounted from the finished DMG. The build performs these checks. Keep release notes factual and version-specific; do not reuse claims that applied only to an earlier wallet export or build.

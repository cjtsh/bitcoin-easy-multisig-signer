# Current handoff — Bitcoin Easy Signer

**Start here for any agent or independent reviewer.** Read `AGENTS.md`, then this file, `AUDIT-BASELINE-0.1.27.md`, `SECURITY-REVIEW-0.2.0.md`, and the current code. `PROJECT-HISTORY.md` and the older phase text in `ROADMAP.md` are historical evidence, not current capability claims.

## Status and version policy

The shared wallet/signing engine has completed Phases 1–4 on Testnet4. Earlier versions produced two confirmed Testnet4 payments with Jade + Trezor Safe 3 and Jade + Ledger Nano S Plus. Version **0.2.0** [is published](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.2.0); its automated release checks and downloaded checksums passed. It addresses the hot audit findings and still requires a fresh one-session owner walkthrough on an Apple Silicon Mac. Do not say its physical-device behavior has been verified until that walkthrough is recorded. Mainnet broadcast remains refused. No mainnet payment has been prepared, signed, or broadcast as of this handoff.

Version scheme: **0.2.0 hot fixes**, **0.2.x corrections found after publication**, **0.3.0 warm fixes**, **0.4.0 nice-to-have improvements**. The owner does not want to install every minor CI revision. Finish automated and bundled checks before asking for a Mac installation; request one walkthrough per milestone unless a defect demands a patch release.

## Product goal

The user is a spouse, lawyer, accountant, or estate planner with little Bitcoin knowledge, recovering from an existing multi-vendor 2-of-3 multisig wallet. Keep the screen's decisions plain. Put descriptor and key technicalities in automatic checks or optional wallet details. Never ask this person to certify a derivation path or inspect a PSBT to make the tool work. They must still compare the payment on each hardware device and confirm the final transaction.

## 0.2.0 behavior and safety boundaries

1. One engine in `wallet_service.py` and `signing.py` serves both networks. `network_config.py` selects BIP48 coin type, address prefix, genesis hash and Esplora endpoint. `gui.py` applies network-specific safety rules and refuses mainnet broadcast.
2. A partial send needs a declared receive/change policy: a two-branch descriptor, a BSMS `/**` template with `/0/*,/1/*` restrictions, or an explicit restrictions line that declares both branches. A receive-only export with `No path restrictions` does not prove change ownership. It is sweep-only: Send All creates one recipient output and no change. The scan can still miss funds outside its gap/range.
3. `build_unsigned_psbt` checks each chosen previous transaction's txid, value and derived script. It stores a reviewed recipient, amount, fee, change and txid in local session state. `accept_signature_update` permits only added partial signatures and verifies them over BIP143 SIGHASH_ALL; `finalize_multisig` repeats signature and witness/prevout checks. Finalization and broadcast compare every final output and fee against the reviewed state. Broadcast holds the session lock through submission so a concurrent refresh cannot change the payment mid-submit.
4. The final screen shows network, full destination, amount, change address/amount, absolute fee, effective fee rate, signer numbers and txid together. A distinct confirmation submits only on Testnet4. Mainnet shows a dry-run conclusion and no broadcast control; the backend also refuses it.
5. Diagnostics are opt-in. The UI button saves `bitcoin-easy-signer-diagnostics-0.2.0.json` (or a numbered variant) to Downloads, mode 0600. Events use fixed stage/outcome codes and timestamps only. No addresses, xpubs, fingerprints, PSBTs, raw transactions, amounts, device paths, or exception messages enter this file. Agents may request it after a failed owner walkthrough; never request wallet material.

## Reviewer checklist

- Challenge the BSMS branch declaration logic, especially exports whose descriptor and restrictions disagree. Confirm that a receive-only import cannot construct a change output.
- Challenge signer response binding. A different txid, changed prevout/script/derivation/global xpub/output map, removed prior signature, bad DER/ECDSA signature, or non-ALL sighash must fail. Confirm legitimate HWI responses from **each** supported physical model still pass; strict PSBT metadata comparison may reveal device-specific additions and require a narrowly justified 0.2.1 fix.
- Verify the final review screen against the exact finalized transaction. Check no stale API request can alter a broadcast in flight. Mainnet broadcast refusal must hold at the API level.
- Verify the diagnostic report's privacy by inspecting the saved file. Check build locks, mandatory `LIBUSB_SHA256`, CycloneDX `BUILD-SBOM.json`, signed bundle structure, test archive, source/DMG hashes and immutable tag.
- Distinguish unit/integration results from a real device walkthrough. A passing test suite cannot establish firmware display behavior.

## Build and owner test

Use Python 3.12; run `python -m unittest discover -s tests -q`, JavaScript syntax checking, Bash syntax checking, source archive tests, and the packaged Mac self-checks. The GitHub workflow is manual dispatch only. It installs hash-locked dependencies, requires an expected libusb digest, builds the Apple Silicon DMG, verifies the extracted bundle, inventories its dependencies in `BUILD-SBOM.json`, writes `SHA256SUMS`, and publishes a new tag only if none exists. Record the workflow run, commit, artifact hashes and result in `SECURITY-REVIEW-0.2.0.md` after completion.

For the owner, ask for **one** controlled Testnet4 partial payment to a self-owned address using a wallet export that declares change; check both device screens, the final output summary and confirmation, and then wait for an independently observed confirmation. If a device refuses the new strict PSBT check, stop; ask only for the diagnostic report and a plain-language description of its screen. Do not ask for the BSMS or signed bytes. If the app fails, fix and release 0.2.1 after automated checks, then request one focused retry.

## Still outstanding after 0.2.0

The warm items planned for 0.3.0 include independent current-UTXO/node verification, fee-policy and replacement handling, stronger transaction-state refactoring, and further distribution/privacy work. The nice-to-have items planned for 0.4.0 include fuller operator guidance and scan/recovery refinements. Mainnet dry run and a deliberate owner-authorized real send are separate Phase 5 gates; do not enable mainnet broadcast merely because 0.2.0 or the Testnet4 walkthrough passes. Developer ID enrollment/notarization is pending a human account dependency.

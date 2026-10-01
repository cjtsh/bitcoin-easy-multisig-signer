# Current status — Bitcoin Easy Signer

**Current candidate: 0.5.0. Published version: 0.4.14.** Version 0.4.15 was an owner-test candidate; 0.5.0 adds guarded mainnet broadcasting. Older audit results and release notes remain historical evidence, not claims about the current release.

## What the app does

Bitcoin Easy Signer helps a nontechnical person make a payment from an existing native-SegWit multisig wallet with two or three keys. It follows the BSMS threshold for any valid quorum, checks public wallet and hardware identities, scans through a selected Esplora server, builds a PSBT, requests signatures through Bitcoin Core HWI, verifies the signatures and final transaction, and broadcasts on Testnet4 or Mutinynet after explicit review. One transaction engine serves Testnet4, Mutinynet, and mainnet.

Mainnet preparation, signing, finalization, and broadcast are enabled in candidate 0.5.0. Broadcast requires a separate per-transaction confirmation that explicitly names real Bitcoin. The owner has not yet reported a mainnet transaction sent or confirmed by this candidate. The app remains experimental and is not a production recovery tool; see [`DISCLAIMER.md`](DISCLAIMER.md).

## Evidence

- Automated source and UI checks are recorded per release in [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md). The GitHub v0.4.14 workflow passed the Python suite, UI DOM suite, source archive tests, signed Apple Silicon build, notarization, packaged-app checks, and release artifact publication.
- Owner-reported physical acceptance includes confirmed Testnet4 payments through 0.2.1; two Mutinynet payments on 0.3.2 (Ledger + Trezor, then Jade + Trezor); and a confirmed 0.4.1 Ledger + Jade Mutinynet payment with a privacy-limited diagnostic report recording verified signatures, finalization, and accepted broadcast.
- Direct and bundled HWI 3.2.0 enumerated the OneKey Classic 1S as `type=trezor`, `label=OneKey Classic 1S`, `model=trezor_1`. Candidate 0.4.15 fixes hardened-helper libusb loading, preserves the OneKey label, and preflights USB without opening the wallet. The owner reports it worked perfectly with the new wallet; the mainnet dry run below confirms a OneKey signature.
- A local 0.4.15 candidate was Developer ID signed and accepted by Apple's notary service. Its app and DMG were stapled; the mounted app passed Gatekeeper assessment. The owner-test DMG is in Downloads. This candidate has not been published; OneKey-specific practice-network acceptance has not been reported.
- The owner reports the local v0.4.14 installation works, but has not reported a physical transaction walkthrough using its newly supported quorum types. Automated checks do not establish hardware or mainnet acceptance.
- The owner reports the locally signed and notarized 0.4.15 candidate completed a mainnet dry run using the OneKey Classic 1S and another signer. The privacy-limited report records a declared change path, consistent complete scan, two verified signer responses, and verified finalization. The owner then cleared the signed transaction from the session. No broadcast or on-chain payment occurred; details are recorded without transaction or wallet identifiers in [`PATCH-0.4.15.md`](PATCH-0.4.15.md).
- Candidate 0.5.0 is the first full-Bitcoin-on-LiveNet build. Mainnet broadcast is gated by exact final review and an explicit operator click. Its local Apple Silicon app and DMG passed Developer ID signing, Apple notarization, staple validation and Gatekeeper checks. Packaged bundle, save and test-network HTTPS checks passed; the 0.5.0 owner mainnet walkthrough is next. Artifact evidence is in [`PATCH-0.5.0.md`](PATCH-0.5.0.md).
- The 0.4.3 DeepSeek and Z.ai audits reviewed an earlier source revision, `7d622ef`; neither used a physical device or performed a mainnet transaction. Their findings and the 0.4.4 remediation record remain useful historical review material, not an audit of 0.4.13.
- The 0.4.12 release was the first Developer ID-signed and Apple-notarized build. The 0.4.13 build additionally staples the app before creating the DMG and validates the app copy inside the finished image. See the release history and [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md).

## Open gates and limitations

- Verify the live mainnet wallet's change policy independently before relying on inferred change. Practice-wallet Sparrow/Nunchuk comparison does not prove another wallet's policy; see [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md).
- The owner-reported mainnet dry run is complete and its signed transaction was cleared. The app's own finalization verification and owner's walkthrough are recorded; independent raw-transaction decode evidence was not supplied. The owner has authorized implementing mainnet broadcast, but has not authorized sending a particular payment. Any live send needs a freshly reviewed transaction and the final-screen opt-in.
- Fee policy remains deliberately capped at 25 sat/vB and 10,000 estimated sats. A higher live standard quote stops preparation; wait or use another established wallet. The app has no fee-bump workflow. Transactions signal replaceability so a compatible external wallet may be able to replace a stuck payment.
- No independent end-to-end security review or live mainnet transaction confirmation has been recorded for 0.5.0. The owner walkthrough is the next acceptance step; this candidate is local and unpublished.
- Public Esplora services provide balances, UTXOs, fees, and broadcast. Mainnet outpoints have a second-source check; practice networks use a fresh same-explorer check. A gap-limited scan can miss funds and is not a complete wallet sweep.
- The plain-language operator guide, nontechnical-user walkthrough, and tested device/firmware matrix are still outstanding. The inherited stack (embit, HWI, libusb, pywebview, and PyInstaller) has not received an independent component audit.

## Document map

**Current:** [`CURRENT-STATUS.md`](CURRENT-STATUS.md), [`README.md`](README.md), [`AGENTS.md`](AGENTS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md), [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`HWI-DEPENDENCY.md`](HWI-DEPENDENCY.md).

**Mixed or historical:** [`ROADMAP.md`](ROADMAP.md) has a current status block followed by archived phase notes; [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md), the 0.2.0 and 0.4.3 audits, old patch records, [`PLAN-0.3.0.md`](PLAN-0.3.0.md), and [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md) preserve earlier decisions and evidence. Read dated/versioned claims in those files as historical.

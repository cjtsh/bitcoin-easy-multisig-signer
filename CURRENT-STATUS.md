# Current status — Bitcoin Easy Signer

**Current version: 0.4.13.** This is the published Apple Silicon release. Its release record is in [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md); the code version is set in [`version.py`](version.py). This page summarizes current evidence and open gates. Older audit results and release notes remain historical evidence, not claims about the current release.

## What the app does

Bitcoin Easy Signer helps a nontechnical person make a payment from an existing 2-of-3 native-SegWit multisig wallet. It reads one BSMS file, checks public wallet and hardware identities, scans through a selected Esplora server, builds a PSBT, requests signatures through Bitcoin Core HWI, verifies the signatures and final transaction, and broadcasts on Testnet4 or Mutinynet after explicit review. One transaction engine serves Testnet4, Mutinynet, and mainnet.

Mainnet preparation, signing, and finalization support a controlled dry run. **Mainnet broadcast is refused in code. No mainnet transaction has ever been prepared, signed, or broadcast by this app.** The app is experimental and not a production recovery tool; see [`DISCLAIMER.md`](DISCLAIMER.md).

## Evidence

- Automated source and UI checks are recorded per release in [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md). The 0.4.13 release record reports 229 Python tests and eight Node DOM tests passing.
- Owner-reported physical acceptance includes confirmed Testnet4 payments through 0.2.1; two Mutinynet payments on 0.3.2 (Ledger + Trezor, then Jade + Trezor); and a confirmed 0.4.1 Ledger + Jade Mutinynet payment with a privacy-limited diagnostic report recording verified signatures, finalization, and accepted broadcast.
- The owner has not reported a physical transaction walkthrough on 0.4.13. The 0.4.13 theme, network selector, copy, and release-build corrections are covered by automated checks; those checks do not establish hardware or mainnet acceptance.
- The 0.4.3 DeepSeek and Z.ai audits reviewed an earlier source revision, `7d622ef`; neither used a physical device or performed a mainnet transaction. Their findings and the 0.4.4 remediation record remain useful historical review material, not an audit of 0.4.13.
- The 0.4.12 release was the first Developer ID-signed and Apple-notarized build. The 0.4.13 build additionally staples the app before creating the DMG and validates the app copy inside the finished image. See the release history and [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md).

## Open gates and limitations

- Verify the live mainnet wallet's change policy independently before relying on inferred change. Practice-wallet Sparrow/Nunchuk comparison does not prove another wallet's policy; see [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md).
- Complete the mainnet dry run: verify change policy, prepare a small payment to an owner-controlled destination, obtain two device approvals, independently compare inputs, outputs, change, fee, and txid, then discard the signed transaction. Do not broadcast.
- Decide how to handle fees above the current 25 sat/vB rate and 10,000-sat estimated-fee limits. There is no in-app fee-bump flow.
- Public Esplora services provide balances, UTXOs, fees, and broadcast. Mainnet outpoints have a second-source check; practice networks use a fresh same-explorer check. A gap-limited scan can miss funds and is not a complete wallet sweep.
- The plain-language operator guide, nontechnical-user walkthrough, and tested device/firmware matrix are still outstanding. The inherited stack (embit, HWI, libusb, pywebview, and PyInstaller) has not received an independent component audit.

## Document map

**Current:** [`CURRENT-STATUS.md`](CURRENT-STATUS.md), [`README.md`](README.md), [`AGENTS.md`](AGENTS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md), [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`HWI-DEPENDENCY.md`](HWI-DEPENDENCY.md).

**Mixed or historical:** [`ROADMAP.md`](ROADMAP.md) has a current status block followed by archived phase notes; [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md), the 0.2.0 and 0.4.3 audits, old patch records, [`PLAN-0.3.0.md`](PLAN-0.3.0.md), and [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md) preserve earlier decisions and evidence. Read dated/versioned claims in those files as historical.

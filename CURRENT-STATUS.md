# Current status — Bitcoin Easy Signer

**Read this page first.** Current version, what is proven, what is not, and which
documents are current. [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md) is the per-release
changelog; there is no separate `CHANGELOG.md`.

**Current version: 0.4.6**, a signing-panel checklist on top of 0.4.5
([`PATCH-0.4.6.md`](PATCH-0.4.6.md)). 0.4.4 remediates the two 0.4.3 audits
([`PLAN-0.4.4.md`](PLAN-0.4.4.md)). Both audits reviewed `main` at **`7d622ef`**
and neither exercised a mainnet transaction or a physical device; current source
and tests take precedence over history.

## What is proven

**Independently verified** (third-party review and independent decode; no hardware,
no mainnet transaction):

- Both 0.4.3 audits read the source and ran the suite: **172 automated tests**
  (DeepSeek: 0 failures; Z.ai: 172 passing, 8 platform-dependent skips).
- DeepSeek ran ~100 hostile cases and found **no fund-loss path**; a fully signed
  mainnet transaction is refused at `/api/broadcast`. Z.ai verified input ownership,
  exact fees, non-dust change, the reviewed-equals-broadcast binding, and
  DER/`SIGHASH_ALL`/ECDSA verification; the 0.4.1 import keeps only verified signatures.
- The 0.4.3 bare-`/*` change rule has a synthetic regression test, and the
  Sparrow/Nunchuk comparison corroborates BIP48 change inference **for that practice
  wallet only**. Two independent decoders agreed on every value of a real owner PSBT.

**Owner-reported** (physical acceptance; not independent verification):

- Confirmed Testnet4 payments through 0.2.1, signed by two devices.
- 0.3.2: two Mutinynet sends, Ledger + Trezor then Jade + Trezor, the second without
  restarting the app. No transaction IDs or diagnostics were supplied.
- 0.4.1: a Ledger + Jade Mutinynet payment; the diagnostic recorded two verified
  signer responses, a verified final transaction and an accepted broadcast, and the
  owner-supplied public transaction later confirmed (device identities omitted).
- **0.4.2 and 0.4.3 have not been physically exercised.**

**Recorded in-repo, not independently audited:** the v0.4.3 workflow's source/DMG checks
passed and assets matched `SHA256SUMS` — integrity, not publisher identity or a code audit.

## What is NOT proven / open gates

- **No mainnet transaction has ever been prepared, signed, or broadcast by this app.**
  Mainnet broadcast is refused in code, not merely hidden in the UI.
- **No notarized or Developer ID-signed build.** The DMG is ad-hoc signed and needs
  right-click → Open; no recipient can attribute it to a publisher. The signing and
  notarization path is now wired and fails closed without credentials, so this is
  waiting only on the Apple Developer Program purchase and the certificates; see
  `PHASE-HANDOFF.md` for the exact secrets.
- **The live mainnet wallet's change policy is unverified.** Ambiguous BSMS exports use
  a strictly gated BIP48 `/1/*` inference corroborated only for the practice wallet;
  verify the first unused change address and its derivation before a mainnet send.
- **Fee policy is unresolved.** The 1–25 sat/vB band and 10,000-sat ceiling can refuse
  when a busy mempool demands more, and there is no fee-bump flow.
- **Explorer dependence and scan limits.** Public Esplora instances supply balances,
  UTXOs, fees and broadcast; practice rechecks are single-source, and a gap-limited
  scan is not a complete wallet sweep.
- **Still missing:** the operator guide, the device/firmware matrix, and notarization.
  The inherited stack (embit, HWI, libusb, pywebview, PyInstaller) is not independently audited.

## Document set — current vs archive

**Current:** [`CURRENT-STATUS.md`](CURRENT-STATUS.md) (this page), [`README.md`](README.md), [`AGENTS.md`](AGENTS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md), [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`replit.md`](replit.md), [`PLAN-0.4.4.md`](PLAN-0.4.4.md), [`PATCH-0.4.6.md`](PATCH-0.4.6.md), [`AUDIT-DEEPSEEK-0.4.3.md`](AUDIT-DEEPSEEK-0.4.3.md), [`AUDIT-ZAI-0.4.3.md`](AUDIT-ZAI-0.4.3.md).

**Mixed:** [`ROADMAP.md`](ROADMAP.md) — top status block current, phase sections archive.

**Archive/historical:** [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md), [`AUDIT-BASELINE-0.1.27.md`](AUDIT-BASELINE-0.1.27.md), [`SECURITY-REVIEW-0.2.0.md`](SECURITY-REVIEW-0.2.0.md), the `PATCH-*.md` records ([`PATCH-0.2.1.md`](PATCH-0.2.1.md) onward), [`PLAN-0.3.0.md`](PLAN-0.3.0.md), [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md). Anything not marked **Current** here is history.

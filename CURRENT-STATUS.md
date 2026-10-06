# Current status — Bitcoin Easy Signer

**0.6.6 is published: Color Team cycle-2 remediation.** The cycle-2
five-lane Color Team audit of the 0.6.5 tree (report, plan, lock and index in
this repository's root) graded CONDITIONAL. The four Mediums were release-channel
findings (CT-01/CT-02 manual assets on the v0.6.4 page, CT-27 a second live
0.6.5 Windows set) and an unpinned BIP-143 digest (CT-26). The Lows were
unpinned money-path controls and two deferred design items (CT-13 broadcast
lock scope, CT-14 counterfeit echo). Version 0.6.6 answers all of them in
code: channel cleanup, published BIP-143 vectors, money-path and HWI-identity
pins, BIP-62 low-S, a key-proof before any PSBT is sent, a large-amount prompt
a lying price cannot suppress, broadcast pre-checks outside the session lock,
pinned runners and lock tooling. Every fix is held by a test demonstrated able
to fail. `releases/PATCH-0.6.6.md` is the evidence record. Published as tag
`v0.6.6` on commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` through the
unified pipeline (candidate run 37482475884, promote run 37486264639). The
cycle-3 audit plan is signed to that tag; the panel rerun is pending.

The out-of-gate `v0.6.5-windows-x64` release and tag, and the manually
uploaded Windows/Linux assets on the v0.6.4 page, were deleted (CT-01, CT-02,
CT-27). Supported binaries live only on the version's own release page, under
one `SHA256SUMS` and its `.asc`. A supersession banner on v0.6.4 names what
was removed.

**Linux v0.6.4 owner acceptance is complete.** On 2026-10-05 the owner reports
testing the Linux AppImage through a transaction and says the implementation
worked very well. Hardware discovery and signing felt nearly instantaneous and
faster than on the owner's Mac and Windows computers. This is qualitative
owner-reported experience, not a benchmark; network, hardware models and
transaction details were not recorded. Ubuntu first-launch instructions now
explain how to allow the AppImage to run as a program and then double-click it.
See [`releases/LINUX-0.6.4-ACCEPTANCE.md`](releases/LINUX-0.6.4-ACCEPTANCE.md).

**Latest published version: 0.6.6.** [Download the signed Apple Silicon release](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.6). Published 2026-10-06 as tag `v0.6.6` on commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` by successful candidate run [37482475884](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37482475884) and promote run [37486264639](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37486264639) (`publish=true`, `candidate_run_id=37482475884`). The release page carries macOS, Windows, Linux, the source archive, one `SHA256SUMS` with `SHA256SUMS.asc`, and `BUILD-SBOM*.json`. Not a draft, not a prerelease. Version 0.6.6 is safety hardening only: no new payment capability. Owner practice-network hardware walkthrough passed on candidate 37474707538 (Trezor Safe 3 and Ledger Nano signed; broadcast accepted). The dated AI-generated [Z.ai v0.6.4 report](releases/AUDIT-ZAI-0.6.4.md) assigns Green under its rubric after verifying the automated publication path. This is evidence about that revision and stated coverage, not a certification or guarantee; no independent human end-to-end review is recorded.

**0.6.1 is published** as tag [`v0.6.1`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.1) (2026-10-02), built from commit `2977930` by workflow run 36957927251 on the `dev-mode-0.6.0` branch. The change is where the network choice lives; the transaction and signing engine is unchanged from 0.5.1. The owner opened the first 0.6.0 candidate and required live Bitcoin to be removed from the panel, so 0.6.0 was never published. The published build has not been exercised in a hardware walkthrough. It moves the network choice off the opening screen: the app opens on Bitcoin mainnet and Mutinynet/Testnet4 are reached through an "Enter Developer Mode" gate, whose panel offers those two practice networks only — live Bitcoin is what the gate's own "Return to Bitcoin" button returns to, not one of its cards, and the gate refuses to move the network while a payment is prepared. The transaction and signing engine is unchanged from 0.5.1, so 0.6.1 adds no sending capability. Its record, including what was verified and what was deliberately left out, is [`releases/PATCH-0.6.1.md`](releases/PATCH-0.6.1.md). A signed and notarized candidate build of 0.6.0 was made and is superseded before publication — workflow run [36954844052](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36954844052) from commit `f147141` — and a 0.6.1 candidate was built the same way. **0.6.2 is published** as tag [`v0.6.2`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.2) (2026-10-02), built from commit `7b4db85` by workflow run 36959242210. It retires the network of a finished review together with the review itself: the mainnet opt-in that a broadcast sends can no longer be inherited from an earlier payment. No user-visible behaviour changed. A signed and notarized candidate was built first from commit `8712dca` by run 36958728418 with a non-publishing dispatch. It retires the network together with the rest of a finished review, so the mainnet opt-in a broadcast sends can never be inherited from an earlier payment. The transaction and signing engine is unchanged from 0.5.1. Its record is [`releases/PATCH-0.6.2.md`](releases/PATCH-0.6.2.md).

## What the app does

Bitcoin Easy Signer helps a nontechnical person make a payment from an existing native-SegWit multisig wallet with two or three keys. It follows the BSMS threshold for any valid quorum, checks public wallet and hardware identities, scans through a selected Esplora server, builds a PSBT, requests signatures through Bitcoin Core HWI, verifies the signatures and final transaction, and broadcasts on the selected network after explicit review. One transaction engine serves Testnet4, Mutinynet, and mainnet. From 0.6.1 the app opens on mainnet, and the two practice networks are reached only through an explicit developer-mode gate whose panel offers those two networks alone; the selected network is held in memory for the session and a practice network cannot outlive a restart.

Mainnet preparation, signing, finalization, and broadcast are enabled. Broadcast requires a per-transaction confirmation that explicitly names real Bitcoin, plus a backend opt-in that fails closed. One mainnet transaction has been prepared, signed on two hardware devices, broadcast and confirmed; it is recorded in [`releases/PATCH-0.5.1.md`](releases/PATCH-0.5.1.md). One confirmed transaction does not establish that a later one is safe. Bitcoin Easy Signer is free, open-source software maintained by Bitseeker LLC and provided without warranty or guarantee; see [`DISCLAIMER.md`](DISCLAIMER.md). No independent end-to-end security review of the current release is recorded.

## Evidence

- Automated source and UI checks are recorded per release in [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md). The GitHub v0.4.14 workflow passed the Python suite, UI DOM suite, source archive tests, signed Apple Silicon build, notarization, packaged-app checks, and release artifact publication.
- Owner-reported physical acceptance includes confirmed Testnet4 payments through 0.2.1; two Mutinynet payments on 0.3.2 (Ledger + Trezor, then Jade + Trezor); and a confirmed 0.4.1 Ledger + Jade Mutinynet payment with a privacy-limited diagnostic report recording verified signatures, finalization, and accepted broadcast.
- Direct and bundled HWI 3.2.0 enumerated the OneKey Classic 1S as `type=trezor`, `label=OneKey Classic 1S`, `model=trezor_1`. Candidate 0.4.15 fixes hardened-helper libusb loading, preserves the OneKey label, and preflights USB without opening the wallet. The owner reports it worked perfectly with the new wallet; the mainnet dry run below confirms a OneKey signature.
- A local 0.4.15 candidate was Developer ID signed and accepted by Apple's notary service. Its app and DMG were stapled; the mounted app passed Gatekeeper assessment. The owner-test DMG is in Downloads. This candidate has not been published; OneKey-specific practice-network acceptance has not been reported.
- The owner reports the local v0.4.14 installation works, but has not reported a physical transaction walkthrough using its newly supported quorum types. Automated checks do not establish hardware or mainnet acceptance.
- The owner reports the locally signed and notarized 0.4.15 candidate completed a mainnet dry run using the OneKey Classic 1S and another signer. The privacy-limited report records a declared change path, consistent complete scan, two verified signer responses, and verified finalization. The owner then cleared the signed transaction from the session. No broadcast or on-chain payment occurred; details are recorded without transaction or wallet identifiers in [`releases/PATCH-0.4.15.md`](releases/PATCH-0.4.15.md).
- Candidate 0.5.0 was the first full-Bitcoin-on-LiveNet build; 0.5.1 publishes it. Mainnet broadcast is gated by exact final review and an explicit operator click. The 0.5.0 local Apple Silicon app and DMG passed Developer ID signing, Apple notarization, staple validation and Gatekeeper checks, and the owner then completed the first live mainnet walkthrough with it. Artifact evidence for 0.5.0 is in [`releases/PATCH-0.5.0.md`](releases/PATCH-0.5.0.md).
- The 0.4.3 DeepSeek and Z.ai audits reviewed an earlier source revision, `7d622ef`; neither used a physical device or performed a mainnet transaction. Their findings and the 0.4.4 remediation record remain useful historical review material, not an audit of 0.4.13.
- The 0.4.12 release was the first Developer ID-signed and Apple-notarized build. The 0.4.13 build additionally staples the app before creating the DMG and validates the app copy inside the finished image. See the release history and [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md).

## Open gates and limitations

- Change policy is **settled for the owner's live mainnet wallet**: its BSMS file declares the change branch itself (`<0;1>/*` inside the descriptor plus an explicit `/0/*,/1/*` restrictions line), so the app reads change from the file and never infers `/1/*` for it. Any *other* wallet must still have its change policy established independently before relying on inferred change, because a practice-wallet Sparrow/Nunchuk comparison does not prove another wallet's policy; see [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md). Before funding any wallet, confirm the first receive address on each signer's own screen.
- The owner-reported 0.4.15 mainnet dry run is complete and its signed transaction was cleared. The app's own finalization verification and the owner's walkthrough are recorded; independent raw-transaction decode evidence was not supplied for it. The later 0.5.0 live mainnet payment was separately reviewed, and its confirmed transaction was decoded independently from two explorers. Any further live send needs a freshly reviewed transaction and the final-screen opt-in.
- Fee policy remains deliberately capped at 25 sat/vB and 10,000 estimated sats. A higher live standard quote stops preparation; wait or use another established wallet. The app has no fee-bump workflow. Transactions signal replaceability so a compatible external wallet may be able to replace a stuck payment.
- No independent end-to-end security review has been recorded. One live mainnet transaction has been confirmed by this project. A single confirmed payment is not an audit and does not establish that a later payment is safe.
- Hardware signers in the tested set do not display the change address. The app marks the change output as belonging to the wallet, so those signers accept it silently. The app now says this plainly and directs the operator to the wallet software that holds the wallet file. Whether a given firmware independently re-derives and checks the change script, rather than trusting the host's change marker, has not been established by test.
- Public Esplora services provide balances, UTXOs, fees, and broadcast. Mainnet outpoints have a second-source check; practice networks use a fresh same-explorer check. A gap-limited scan can miss funds and is not a complete wallet sweep.
- The plain-language operator guide and website manual are published. An owner-led nontechnical walkthrough, tested device/firmware matrix, independent end-to-end review, and independent component audit of the inherited stack (embit, HWI, libusb, pywebview, and PyInstaller) remain outstanding.

## Document map

**Current:** [`CURRENT-STATUS.md`](CURRENT-STATUS.md), [`README.md`](README.md), [`AGENTS.md`](AGENTS.md), [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md), [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`HWI-DEPENDENCY.md`](HWI-DEPENDENCY.md).

**Mixed or historical:** [`ROADMAP.md`](ROADMAP.md) has a current status block followed by archived phase notes; [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md), the 0.2.0 and 0.4.3 audits, old patch records, [`releases/PLAN-0.3.0.md`](releases/PLAN-0.3.0.md), and [`releases/MUTINYNET-0.3.0.md`](releases/MUTINYNET-0.3.0.md) preserve earlier decisions and evidence. Read dated/versioned claims in those files as historical.

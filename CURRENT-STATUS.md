# Current status — Bitcoin Easy Signer

**Source revision 0.7.3 answers the ⛔ BLOCKED Color Team audit of the `v0.7.2`
tree.** The v0.7.1 conversion criterion was met by execution — the referee re-broke
CT-22, CT-24 and CT-25 and watched each named pin go red, CT-23 and CT-26 closed by
dated owner acceptance, and all twenty-one earlier findings were carried — but the
code added for CT-22 placed its pause in the wrong place in time. Both halves of the
broadcast pause read a record that was written only after `broadcast_transaction`
returned, and that call is bounded by `BROADCAST_TIMEOUT_SECONDS = 20.0`, so while the
first payment was on the wire a second, separately reviewed and consented payment
passed both halves and was broadcast (CT-27, Medium, grade-binding through threat row
T-11). `_broadcast` now arms a per-wallet in-flight marker inside the same critical
section that checks for it and releases the lock before the network call, so no I/O is
held across it; both halves read the marker, every exit clears it, and a definite
refusal leaves the reviewed payment retryable. The pending record is kept per
transaction and reconciles per transaction on refresh (CT-29), `OSError` joins
`verify_esplora`'s transport tuple so a mid-reply reset is the documented refusal
rather than a fixed 500 (CT-33), and the two inventory gaps are closed (CT-30,
CT-31). Rows `CM-38` and `CM-40`…`CM-45` in `CONTROLS.md` pin it, all eight control
halves break-and-watched on a disposable copy, and `releases/PATCH-0.7.3.md` carries one
closing row per finding. Unlike 0.7.1, this revision is not engine-unchanged: `gui.py`
and `network_settings.py` change behaviour, `wallet_service.py` changes only a
docstring, and no transaction construction, signing, fee or network rule changes with
them.
Version 0.7.2 was the Color Team cycle-8 remediation of the `v0.7.1` tree: it
asserted the unconfirmed-payment pause at the broadcast and again under the pre-submit
lock (`CM-38`), refused a transaction that names the same Bitcoin output twice before
any explorer was asked (`CM-39`), and added `http.client.HTTPException` to the settings,
explorer and broadcast transport tuples (`CM-40`…`CM-42`). It was the first revision
since 0.5.1 to change app behaviour.
Version 0.7.0 was the Color Team cycle-6 build-process remediation of the
`v0.6.9` tree: every finding the cycle's plan scheduled had exactly one
row in `releases/PATCH-0.7.0.md` with a severity and a closing test the
build loads; the value and script limbs of the build-time prevout match
were pinned by tests that fail when their own limb is removed; the loopback
server retired its oldest idle connection instead of refusing the
operator's window when the connection ceiling was full, so no local
process could freeze the app by holding the slots; `CONTROLS.md` gained
rows `CM-27`…`CM-32` for the protections the previous release added
untracked, and its claim-phrase net was widened; the retired-publisher
guard refused when the platform reported more registrations than the one
page it reads; and the Windows startup dialog showed the same bounded
record as the log.
The release is built and published from `main` through the unified
pipeline. The newest published tag is
[`v0.7.2`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.7.2),
published 2026-10-26T21:48:23Z as tag `v0.7.2` on commit
`1e51dcfa45d6f61c83c14aeb1998725fbd705ba9` by candidate run
[40397174519](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/40397174519)
— six attempts: the first five failed inside the macOS DMG job (four on the
Apple staple/validate step, one on `hdiutil`) and published nothing — and
promote run
[40405953511](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/40405953511).
The revision it replaces, `v0.7.1`, was the cycle-7 remediation described
above. Cycle 5 was the conversion re-check of the
`v0.6.8` grade: the panel verified all twelve prior findings fixed **by
execution** — the referee re-broke each fix and watched its new test go
red — and held the grade at **⚠️ CONDITIONAL** on two new Lows, `CT-14`
(two tests named for prevout limbs that actually exercised the txid limb)
and `CT-13` (the new connection ceiling's deliberate availability trade),
with four housekeeping notes; its report, plan, lock and public security
statement are prior-cycle records in this branch. Version 0.6.9 was the
cycle-5 build-process remediation of the `v0.6.8` tree, where the
five-lane panel graded
**⚠️ CONDITIONAL**: it held the money path, the devices, the pipeline and
the published bytes, and named four Low findings — the control inventory
could not detect a citation that moved, three first-line guards were
tested only through the deeper guard behind them, one broadcast branch
had no test that could fail, and the download page was corrected after
the tag instead of before it. `releases/PATCH-0.6.9.md` is that cycle's
evidence record. Version 0.6.7 was the cycle-3 build-process remediation:
the cycle-3 five-lane Color Team audit of the `v0.6.6`
tree — its report, plan, lock and index are no longer in `main` and remain in
the `v0.6.6` tag tree — graded
**⛔ BLOCKED** — not on the app. Red found no breach, Orange recorded its
first LOGIC PROVEN (21/21 invariants), Amber verified the supply chain
end to end. The grade was set by one High finding on the build process,
**CT-48**: the per-platform publish workflows "retired" when Windows and
Linux were added were never deleted, and one had published an unsigned
manifest, while `build-candidate.yml`'s header claimed no second path
existed. Version 0.6.7 answers the ledger in code and in one dated
owner acceptance: the retired workflows are deleted from every branch and
a remote-level sweep gate refuses to start a release if one reappears;
the HWI helper is identified by bytes rather than by what it says about
itself; the interpreter is pinned to one exact patch; the lock-writer is
hash-locked; the source tarball can rebuild a signed Mac app; and the
broadcaster is verified at use on every network. Every fix is held by a
test demonstrated able to fail. `releases/PATCH-0.6.7.md` is the
evidence record; `releases/OWNER-ACCEPTANCE-2026-10-07.md` closes the
by-design observations. **0.6.7 is published** as tag
[`v0.6.7`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.7)
on commit `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b` through the unified
pipeline (candidate run 37644267740, promote run 37655666900), after the
owner installed that candidate's DMG and accepted a practice-network
payment on hardware. Post-publication verification — tag binding, every
asset against `SHA256SUMS`, `SHA256SUMS.asc` against the committed
release key, and a Sigstore attestation — is recorded in
`releases/PATCH-0.6.7.md`.

The prior release, **0.6.6**, is published as tag
[`v0.6.6`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.6)
on commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` through the unified
pipeline (candidate run 37482475884, promote run 37486264639). It was the
Color Team cycle-2 remediation: channel cleanup, published BIP-143
vectors, money-path and HWI-identity pins, BIP-62 low-S, a key-proof
before any PSBT is sent, a large-amount prompt a lying price cannot
suppress, broadcast pre-checks outside the session lock, pinned runners
and lock tooling. `releases/PATCH-0.6.6.md` is its evidence record.

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

**Download the signed Apple Silicon release:**
[all releases](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases).
**Do not restate a "latest published version is X" here** — that is the
CT-46/CT-71 defect class and it goes stale the moment `version.py` moves.
The published set is whatever that page and [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md)
carry. As of 2026-10-26 that is
[v0.7.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.7.1),
published 2026-10-26T18:13:21Z as tag `v0.7.1` on commit
`8923ca0273380a9cb1ea7e7e964c6332dda5a777` by successful candidate run
[40370767634](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/40370767634)
and promote run
[40372606443](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/40372606443)
(`publish=true`, `candidate_run_id=40370767634`). The release page
carries macOS, Windows, Linux, the source archive, one `SHA256SUMS` with
`SHA256SUMS.asc`, and `BUILD-SBOM*.json`. Not a draft, not a prerelease.
Version 0.6.7 is the Color Team cycle-3 build-process remediation: one
publish path with the retired per-platform workflows deleted from every
branch, the HWI helper identified by bytes rather than by its own version
string, the interpreter pinned to a full patch, the lock-writer
hash-locked, the source tarball able to rebuild a signed Mac app, and the
broadcaster verified at use on every network. No wallet, signing or
broadcast policy changed. Owner practice-network hardware walkthrough
passed on candidate 37644267740 before promotion. This is evidence
about that revision and its stated coverage, not a
certification or guarantee; no independent human end-to-end review is
recorded.

**0.6.1 is published** as tag [`v0.6.1`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.1) (2026-10-02), built from commit `2977930` by workflow run 36957927251 on the `dev-mode-0.6.0` branch. The change is where the network choice lives; the transaction and signing engine is unchanged from 0.5.1. The owner opened the first 0.6.0 candidate and required live Bitcoin to be removed from the panel, so 0.6.0 was never published. The published build has not been exercised in a hardware walkthrough. It moves the network choice off the opening screen: the app opens on Bitcoin mainnet and Mutinynet/Testnet4 are reached through an "Enter Developer Mode" gate, whose panel offers those two practice networks only — live Bitcoin is what the gate's own "Return to Bitcoin" button returns to, not one of its cards, and the gate refuses to move the network while a payment is prepared. The transaction and signing engine is unchanged from 0.5.1, so 0.6.1 adds no sending capability. Its record, including what was verified and what was deliberately left out, is [`releases/PATCH-0.6.1.md`](releases/PATCH-0.6.1.md). A signed and notarized candidate build of 0.6.0 was made and is superseded before publication — workflow run [36954844052](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36954844052) from commit `f147141` — and a 0.6.1 candidate was built the same way. **0.6.2 is published** as tag [`v0.6.2`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.2) (2026-10-02), built from commit `7b4db85` by workflow run 36959242210. It retires the network of a finished review together with the review itself: the mainnet opt-in that a broadcast sends can no longer be inherited from an earlier payment. No user-visible behaviour changed. A signed and notarized candidate was built first from commit `8712dca` by run 36958728418 with a non-publishing dispatch. It retires the network together with the rest of a finished review, so the mainnet opt-in a broadcast sends can never be inherited from an earlier payment. The transaction and signing engine is unchanged from 0.5.1. Its record is [`releases/PATCH-0.6.2.md`](releases/PATCH-0.6.2.md).

## What the app does

Bitcoin Easy Signer helps a nontechnical person make a payment from an existing native-SegWit multisig wallet with two or three keys. It follows the BSMS threshold for any valid quorum, checks public wallet and hardware identities, scans through a selected Esplora server, builds a PSBT, requests signatures through Bitcoin Core HWI, verifies the signatures and final transaction, and broadcasts on the selected network after explicit review. One transaction engine serves Testnet4, Mutinynet, and mainnet. From 0.6.1 the app opens on mainnet, and the two practice networks are reached only through an explicit developer-mode gate whose panel offers those two networks alone; the selected network is held in memory for the session and a practice network cannot outlive a restart.

Mainnet preparation, signing, finalization, and broadcast are enabled. Broadcast requires a per-transaction confirmation that explicitly names real Bitcoin, plus a backend opt-in that fails closed. One mainnet transaction has been prepared, signed on two hardware devices, broadcast and confirmed; it is recorded in [`releases/PATCH-0.5.1.md`](releases/PATCH-0.5.1.md). One confirmed transaction does not establish that a later one is safe. Bitcoin Easy Signer is free, open-source software maintained by Bitseeker LLC and provided without warranty or guarantee; its terms of use, warranty disclaimer, and limitation of liability are in [`DISCLAIMER.md`](DISCLAIMER.md), which incorporates the Bitseeker LLC standard legal framework published at [cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer). No independent end-to-end security review of the current release is recorded.

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

**Audit:** [`bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.2.md`](bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.2.md) is the Color Team plan for the published `v0.7.2` revision, a follow-up cycle in the `v0.6.8` lineage; it is signed Bitseeker LLC, 26 Oct 2026, and [`bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.2.md`](bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.2.md) records the plan's SHA-256 at the start of the audit. The plan, lock, report and public security statement of the `v0.7.1` and earlier cycles are prior-cycle records under [`audit-history/`](audit-history/); the artifacts inside the tag trees remain untouched.

**Mixed or historical:** [`ROADMAP.md`](ROADMAP.md) has a current status block followed by archived phase notes; [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md), old patch records and [`releases/MUTINYNET-0.3.0.md`](releases/MUTINYNET-0.3.0.md) preserve earlier decisions and evidence. Read dated/versioned claims in those files as historical.

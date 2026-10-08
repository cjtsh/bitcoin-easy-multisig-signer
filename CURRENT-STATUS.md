# Current status — Bitcoin Easy Signer

**Source revision 0.6.8 is the Color Team cycle-4 audit
remediation.** The cycle-4 five-lane Color Team audit of the `v0.6.7`
tree (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`,
with the plan, lock and index in this repository's root) graded
**⛔ BLOCKED** on two independent grounds. Copper proved its own failure
state: the source-mode hardware-helper payload check could be made to
*pass* while substituted code executed inside the check itself (**CT-90**).
Red found a wallet file that displays as an honest 2-of-2 while one device
approval finalizes it (**CT-72**, the cycle's one High). Version 0.6.8
answers the ledger in code: a BSMS record that lists the same signer key
twice under two origin fingerprints is refused at parse; the payload check
locates the pinned library files and hashes them without executing them, in a
check child that runs `-I -S -P` (no site-packages, no `.pth` hooks, no user
site) while the helper itself runs `-I -P`, keeping site-packages so the pinned
`hwilib` imports; a cached helper identity
is re-hashed before it is believed; the two public reference feeds require
the session token and the token comparison is total for every header value;
the publish-path sweep recognizes REST and third-party publishers, requires
a read-only token from any non-main ref carrying a workflow, and leaves no
private refs behind; each publish refusal is pinned to its own branch and
its own exit; the dispatcher's run id reaches its check through the
environment rather than through shell text; the container proof image is
digest-pinned; every SBOM records the toolchain that built it; and the
source archive ships `signing-key.asc`, and the release credentials are
environment-scoped (CT-97), recoverable only by re-deriving them with
`scripts/provision-release-credentials.sh`. Every fix is held by a test
demonstrated able to fail, and `releases/PATCH-0.6.8.md` is the evidence
record and the round trip of every finding the cycle-4 report carried.
**0.6.8 is not published.** The cycle-5 audit ran against this revision under
`bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` — the cycle-4
plan carried verbatim with the target revision moved to commit
`bc92f054822008510249e743a60033009dc4995a`, and section 9 re-signed by the
owner on 08 OCT 2026 for that revision — and its report,
`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md`, graded **⛔
BLOCKED**: 0 Critical, 1 High, 4 Medium, 10 Low, 5 Info, with Red (CT-72),
Orange (CT-73) and Copper (CT-90) each independently forcing the grade. The
report is published on `main` for anyone to read.

**The tree in front of you is the cycle-5 remediation of that grade**, a
second round on the same 0.6.8 revision. Where cycle 4 closed the
*demonstrations* the audit had used, this round closes the *classes*:
a duplicate signer key is now refused by key material — public point plus
chain code — so re-spelling it under another network version or another
origin fingerprint changes nothing, and a compiled witness script that names
one public key twice is refused independently (CT-72); the source-mode HWI
payload check pins all 115 `.py` files of the tree as literals, runs its
check child with `-I -S -P` so a site-packages `.pth` cannot execute inside
it, hands that child the package roots as argv because `-S` removes the name
it could otherwise resolve, compares the whole set in both directions, and
runs against the real lock in every prepared build environment (CT-90); the
publish-path sweep strips comments before any decision and judges the token
grant from a parsed `permissions:` mapping, so a spaced key is a write grant
and a comment is never evidence (CT-73/CT-102); the credential check derives
its watched names from the workflow text instead of a hand-typed list, which
is how `MAC_NOTARY_KEY_P8_BASE64` was being missed (CT-97); the Windows
helper's trust model is stated honestly rather than claimed away (CT-105);
and a hard link is refused, not only a symlink (CT-92). `releases/PATCH-0.6.8.md`
carries the round in full, including what is *not* closed.

The signed, notarized `publish=false` candidate for the frozen cycle-5
revision is green: run 37783584533 at `1a5e9bf` (documentation only on top of
the frozen revision) passed all seven jobs and published nothing — the
publish step took its documented `publish=false` refusal path before any tag
or release was created. That candidate predates this remediation round, so it
is evidence about the frozen revision and not about the tree in front of you.
The owner hardware walkthrough and a cycle-6 audit of this tree are what gate
promotion now.
The last open item, **CT-97**, is fixed at the repository level: the
release credentials are scoped to the `release-signing` and `apple-signing`
environments, each deployable only from `main` and declaring no human gate, so a
dispatch at a historical tag cannot read them and a promotion never pauses for a
person. The deployment rules were verified against live GitHub settings on
2026-10-08 (`gh api`, transcript in `releases/PATCH-0.6.8.md`); the repository
pins only the job-level `environment:` declaration, so a later change to the
environment's branch policy or reviewers would invalidate this without changing
the tree. All five stored values are environment-scoped and the repository-level
secret list is empty; the last one, `MAC_APP_SPECIFIC_PASSWORD`, which no machine
here can re-derive, was moved on 2026-10-08 without owner action by sealing it to a
key held only locally. The check now derives its watched names from the workflow
text rather than a typed list, so the sixth name the notarize path references,
`MAC_NOTARY_KEY_P8_BASE64`, is reported as a `note:` until the owner stores it
and is refused if it ever appears at repository level or in the wrong environment
(cycle 5, CT-97). `scripts/check-release-credentials.sh` prints
`ok: the release credentials are environment-scoped, main-only, and unreachable
from any tag`; the recovery path is scripted
(`scripts/provision-release-credentials.sh`), and `SIGNING.md` carries the master
copy behind each credential.

The prior release, **0.6.7**, is the Color Team cycle-3 build-process
remediation: the retired per-platform workflows are deleted from every
branch and a remote-level sweep gate refuses to start a release if one
reappears; the HWI helper is identified by bytes rather than by what it
says about itself; the interpreter is pinned to one exact patch; the
lock-writer is hash-locked; the source tarball can rebuild a signed Mac
app; and the broadcaster is verified at use on every network.
`releases/PATCH-0.6.7.md` is its evidence record;
`releases/OWNER-ACCEPTANCE-2026-10-07.md` closes its by-design
observations.

The release before that, **0.6.6**, is published as tag
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
carry. As of 2026-10-07 that is
[v0.6.7](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.7),
published 2026-10-07 as tag `v0.6.7` on commit
`81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b` by successful candidate run
[37644267740](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37644267740)
and promote run
[37655666900](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37655666900)
(`publish=true`, `candidate_run_id=37644267740`), after the owner installed
that candidate's DMG and accepted a practice-network payment on hardware.
Post-publication verification — tag binding, every asset against
`SHA256SUMS`, `SHA256SUMS.asc` against the committed release key, and a
Sigstore attestation on the DMG — is recorded in `releases/PATCH-0.6.7.md`.
The release page carries macOS, Windows, Linux, the source archive, one
`SHA256SUMS` with `SHA256SUMS.asc`, and `BUILD-SBOM*.json`. Not a draft,
not a prerelease. Version 0.6.7 is build-process and helper-identity
hardening only: no new payment capability. The dated
AI-generated [Z.ai v0.6.4 report](releases/AUDIT-ZAI-0.6.4.md) assigns
Green under its rubric after verifying the automated publication path.
This is evidence about that revision and stated coverage, not a
certification or guarantee; no independent human end-to-end review is
recorded.

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

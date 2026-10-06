# Release history and correction record

**The out-of-gate `v0.6.5-windows-x64` release was deleted** (CT-27): it
carried same-named different-byte Windows assets from a retired workflow.
Its owner-reported console-window acceptance is preserved in
`releases/PATCH-0.6.5.md`. Supported binaries live only on each version's
own release page.


This is the consolidated, chronological record of the published versions that
carry a reviewed evidence file: what changed, what the evidence was, and what
was later corrected. Each entry links its full evidence file. The earlier
`0.0.x`–`0.1.26` iteration tags predate that practice and are recorded by tag
and commit subject below rather than given individual entries. **Current status
and next gates live in [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md); current
capabilities live in [`README.md`](README.md).** Two facts govern this record:

- **Mainnet broadcast is refused before 0.5.0 and gated from 0.5.0 onward.**
  Every version before 0.5.0 refused a mainnet broadcast in code — including the
  0.4.15 owner-test candidate, whose mainnet dry run reached that refusal at the
  final screen. 0.5.0 was the first build that could submit one, and 0.5.1 is the
  first release that publishes it, behind a final-screen per-transaction opt-in
  together with a backend flag that fails closed when omitted. One live mainnet
  payment has been confirmed by the 0.5.0 engine, which 0.5.1 publishes
  unchanged. One confirmed payment is not an audit.
- **Never republish under an existing tag.** A bare `vX.Y.Z` tag names a
  published release and is never moved. A suffix marks a build that was not the
  numbered release, but it does not by itself mean the tag is local:
  `v0.0.4-rc1` and `v0.1.0-unsigned-test` are on the remote, the latter as a
  published pre-release. Asset coverage grew over time — releases before 0.1.11
  carry only the source archive and the DMG, `SHA256SUMS` begins at 0.1.11, and
  `BUILD-SBOM.json` begins at 0.2.0 — so read the release page rather than
  assuming.
- **The source archive is a snapshot at the tagged commit.** Its history entry
  may still say "candidate" or "not published" because publication happens
  after that commit is built. The GitHub release page and its checksums record
  the publication; the later main-branch history entry records the final run
  and artifact digests. Do not treat the in-tag status line as live status.

| Version | One-line summary | Evidence |
| --- | --- | --- |
| 0.1.x | Phases 1–4: balance view, send eligibility, unsigned PSBT, testnet signing/broadcast | [`releases/AUDIT-BASELINE-0.1.27.md`](releases/AUDIT-BASELINE-0.1.27.md), [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md) |
| 0.2.0 | Hot-item security fixes; **hardware signing broken — do not use** | [`releases/SECURITY-REVIEW-0.2.0.md`](releases/SECURITY-REVIEW-0.2.0.md) |
| 0.2.1 | HWI field-order repair; confirmed Testnet4 payment | [`releases/PATCH-0.2.1.md`](releases/PATCH-0.2.1.md) |
| 0.2.2 | One-payment-at-a-time confirmation wait | [`releases/PATCH-0.2.2.md`](releases/PATCH-0.2.2.md) |
| 0.3.0 | Warm safety work, Mutinynet, stale-screen fix | [`releases/PATCH-0.3.0.md`](releases/PATCH-0.3.0.md), [`releases/PLAN-0.3.0.md`](releases/PLAN-0.3.0.md), [`releases/MUTINYNET-0.3.0.md`](releases/MUTINYNET-0.3.0.md) |
| 0.3.1 | Send All never preselected; Mutinynet default network | [`releases/PATCH-0.3.1.md`](releases/PATCH-0.3.1.md) |
| 0.3.2 | One-file BIP48 custom sends from a Nunchuk BSMS | [`releases/PATCH-0.3.2.md`](releases/PATCH-0.3.2.md) |
| 0.4.0 | Visual refresh; session-only payment receipt | [`releases/PATCH-0.4.0.md`](releases/PATCH-0.4.0.md) |
| 0.4.1 | Signature-only signer-response import; longer signing window | [`releases/PATCH-0.4.1.md`](releases/PATCH-0.4.1.md) |
| 0.4.2 | Three-minute device discovery/authorization waits (Jade) | [`releases/PATCH-0.4.2.md`](releases/PATCH-0.4.2.md) |
| 0.4.3 | Fail-closed bare-`/*` change inference; same-wallet export proof | [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md) |
| 0.4.4 | Audit remediation: tests for the guards that had none, three fail-closed gaps, MIT licence and third-party notices | [`releases/PLAN-0.4.4.md`](releases/PLAN-0.4.4.md), [`releases/AUDIT-DEEPSEEK-0.4.3.md`](releases/AUDIT-DEEPSEEK-0.4.3.md), [`releases/AUDIT-ZAI-0.4.3.md`](releases/AUDIT-ZAI-0.4.3.md) |
| 0.4.5 | CSP nonce (no `'unsafe-inline'`), Send-All acknowledgement naming the 20-address gap, and a control to clear signed bytes | [`releases/PLAN-0.4.4.md`](releases/PLAN-0.4.4.md) |
| 0.4.6 | One signing box per cosigner, so the missing signer is visible at a glance | — |
| 0.4.7 | Correction: the final signature fills its own box, and completing does not scroll the boxes off screen | — |
| 0.4.8 | Attributable diagnostics, and visible progress that never advertises a wait | — |
| 0.4.9 | A fraction of a Bitcoin no longer needs a leading zero | — |
| 0.4.10 | One progress bar, and only the operation that owns it may change or clear it | — |
| 0.4.11 | The amount box states that a leading zero is optional | — |
| 0.4.12 | The first **notarized** release: installs with a normal double-click | — |
| 0.4.13 | Light and dark themes, one palette of roles, and a toggle | — |
| 0.4.14 | Follow the BSMS quorum for wallets with up to three hardware keys | [`releases/PATCH-0.4.14.md`](releases/PATCH-0.4.14.md) |
| **0.4.15 candidate** | Fix signed HWI/libusb loading; owner reports OneKey Classic 1S support and a cleared, unbroadcast mainnet dry run | [`releases/PATCH-0.4.15.md`](releases/PATCH-0.4.15.md) |
| **0.5.0 candidate — LIVE BTC transactions** | Mainnet transactions with explicit final-screen and backend opt-ins; preserve fee caps and unknown-outcome lockout. Committed as `51ea400`, tagged `v0.5.0-rc1` locally, never pushed or published. **This is the build that made the project's first live mainnet payment** | [`releases/PATCH-0.5.0.md`](releases/PATCH-0.5.0.md) |
| **0.5.1** | First published mainnet-broadcast release: publishes the 0.5.0 engine unchanged, corrects the change-address guidance the live run showed to be wrong, and restates the risk language | [`releases/PATCH-0.5.1.md`](releases/PATCH-0.5.1.md) |
| **0.6.1** | Interface only: the app opens on mainnet and the practice networks move behind an "Enter Developer Mode" gate that offers Mutinynet and Testnet4 only, since live Bitcoin is the network the gate returns to rather than a card in it. The transaction and signing engine is unchanged from 0.5.1. Published 2026-10-02 as tag `v0.6.1` from commit `2977930` (run 36957927251). A first candidate carried the same idea at 0.6.0 from `f147141` in run 36954844052 and is superseded before publication, so no 0.6.0 tag or release exists | [`releases/PATCH-0.6.1.md`](releases/PATCH-0.6.1.md), [`releases/SCOPE-0.6.1.md`](releases/SCOPE-0.6.1.md) |
| **0.6.2** | Internal state fix: retiring a review also retires the network it was bound to, so the mainnet opt-in posted with a broadcast can never be inherited from an earlier payment. No user-visible change; the engine is unchanged from 0.5.1. Published 2026-10-02 as tag `v0.6.2` from commit `7b4db85` (run 36959242210) | [`releases/PATCH-0.6.2.md`](releases/PATCH-0.6.2.md) |
| **0.6.3** | Audit remediation in signing checks, embit, libusb, build inventory, and release controls. Owner-tested Mutinynet payment. Published 2026-10-02 as tag `v0.6.3` from tested app commit `f19bc46` (nonpublishing build run 36969063265); public DMG verified byte-identical to the tested file | [`releases/PATCH-0.6.3.md`](releases/PATCH-0.6.3.md) |
| **0.6.4** | No transaction or signing behavior change. Adds API regression coverage, embit wheel hash to the SBOM, and workflow-only publication of the exact verified candidate bytes. Published 2026-10-02 as tag `v0.6.4` at commit `35cdedb` by candidate run 37008418851 and publishing run 37009396873. The AI-generated Z.ai follow-up report assigns Green under its rubric; no independent human end-to-end review is recorded | [`releases/PATCH-0.6.4.md`](releases/PATCH-0.6.4.md) · [`releases/AUDIT-ZAI-0.6.4.md`](releases/AUDIT-ZAI-0.6.4.md) |
| **0.6.6** | Color Team cycle-2 remediation. BIP-143 published vectors; money-path and HWI-identity pins; BIP-62 low-S; key-proof before any PSBT is sent; large-amount prompt a lying price cannot suppress; broadcast pre-checks outside the session lock; pinned runners and lock tooling; release-channel hygiene. Owner hardware walkthrough required before publication | [`releases/PATCH-0.6.6.md`](releases/PATCH-0.6.6.md) · [`releases/RELEASE-NOTES-0.6.6.md`](releases/RELEASE-NOTES-0.6.6.md) |

## 0.1.x — Phases 1 through 4 on Testnet4

The framework releases: BSMS import and balance view (Phase 1), explained send
eligibility (Phase 2), independently verified unsigned PSBT preparation
(Phase 3), then signing and Testnet4 broadcast with hardware devices
(Phase 4, v0.1.27). Two real Testnet4 payments confirmed, between them using
all three supported devices — Jade, Trezor Safe 3, and Ledger Nano S Plus. The
independent audit of that era, including its hot findings (inferred change
ownership, incomplete final review, unverified finalization signatures,
signer-response binding), is preserved in
[`releases/AUDIT-BASELINE-0.1.27.md`](releases/AUDIT-BASELINE-0.1.27.md); the build and live-use
history is in [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md). Every one of those
hot findings was subsequently fixed and regression-tested — see 0.2.0 through
0.4.1 below.

## 0.0.x–0.1.26 — iteration tags

These tags were rapid prototyping on 27–28 September 2026: 35 tags over two
days, 64 commits by the end, most of them single-purpose fixes. None carries a
separate evidence file, so each is recorded here by tag and by the subject of
the commit it points at; `git show <tag>` remains the authoritative record.
`v0.0.4-rc1` and `v0.1.0-unsigned-test` point at the same commits as `v0.0.4`
and `v0.1.0` respectively.

| Tag | Date | Commit subject |
| --- | --- | --- |
| `v0.0.1` | 2026-09-27 | Add read-only BSMS and USB discovery probe |
| `v0.0.2` | 2026-09-27 | Put experimental software disclaimer on repository front page |
| `v0.0.3` | 2026-09-27 | Add explicit Testnet4 read-only probe and guarded faucet address |
| `v0.0.4` | 2026-09-27 | Add Testnet4 local GUI preview and unsigned PSBT flow |
| `v0.0.4-rc1` | 2026-09-27 | Add Testnet4 local GUI preview and unsigned PSBT flow |
| `v0.0.5` | 2026-09-27 | Show BTC/USD size references and per-address balances |
| `v0.0.6` | 2026-09-27 | Add LiveNet/Testnet4 switch, wallet refresh, and safer fee review |
| `v0.1.0` | 2026-09-27 | Enable unsigned v0.1.0 Mac and source candidate builds |
| `v0.1.0-unsigned-test` | 2026-09-27 | Enable unsigned v0.1.0 Mac and source candidate builds |
| `v0.1.1` | 2026-09-27 | Make BSMS files easy to select in the macOS import dialog (v0.1.1) |
| `v0.1.2` | 2026-09-27 | Make macOS balance lookup resilient and verify bundled Testnet4 HTTPS |
| `v0.1.3` | 2026-09-27 | Fix desktop wallet picker without JavaScript bridge |
| `v0.1.4` | 2026-09-27 | Show BTC first with sats and USD in balance summary |
| `v0.1.5` | 2026-09-28 | Prepare unsigned Apple Silicon test build 0.1.5 with contextual help |
| `v0.1.6` | 2026-09-28 | Restore side-by-side sats and remove unrequested balance copy field |
| `v0.1.7` | 2026-09-28 | Publish v0.1.7 test release after successful builds |
| `v0.1.8` | 2026-09-28 | Add explicit transaction preparation choices and review flow |
| `v0.1.9` | 2026-09-28 | Build transaction review and hardware recognition flow |
| `v0.1.10` | 2026-09-28 | Fix CI paths for Bitcoin Easy Signer app bundle |
| `v0.1.11` | 2026-09-28 | Simplify the interface and add test-first / explorer-confirmation guidance |
| `v0.1.12` | 2026-09-28 | Bump to 0.1.12: one version per published build |
| `v0.1.13` | 2026-09-28 | Resolve the change addresses instead of asking the owner to vouch for them |
| `v0.1.14` | 2026-09-28 | Show the selected fee speed, and show that slow work is happening |
| `v0.1.15` | 2026-09-28 | Make checking the hardware wallets step 3, before a payment is built |
| `v0.1.16` | 2026-09-28 | Pass the icon to PyInstaller where the build actually reads it |
| `v0.1.17` | 2026-09-28 | Make a hardware-wallet problem diagnosable before the first device arrives |
| `v0.1.18` | 2026-09-28 | Report why a detected device cannot be read |
| `v0.1.19` | 2026-09-28 | Accept a Sparrow BSMS record, and show the descriptor checksum |
| `v0.1.20` | 2026-09-28 | Survive a device that locks mid-check, and ship a runnable source archive |
| `v0.1.21` | 2026-09-28 | Install the dependency a Jade needs to unlock, and verify it at build time |
| `v0.1.22` | 2026-09-28 | Tell the owner the one thing that applies to their device |
| `v0.1.23` | 2026-09-28 | Ask HWI for a chain the Jade understands |
| `v0.1.24` | 2026-09-28 | Ship signing.py in the source archive |
| `v0.1.25` | 2026-09-28 | Publish the account xpubs so a Ledger can sign, and refresh the device list itself |
| `v0.1.26` | 2026-09-28 | Stop treating a pending spend as a corrupted balance |

Note `v0.1.24` — "Ship signing.py in the source archive". A root file missing
from the curated archive copy list has now happened three times: `signing.py`,
`safe_http.py` (see the comment in `scripts/build-source.sh`), and
`RELEASE-HISTORY.md` itself. The module list is guarded by an assertion; as of
0.4.3 the document list is too.

## 0.2.0 — hot-item security work; hardware signing broken

Implemented the audit's hot fixes: declared-change eligibility, cryptographic
signature verification in the finalizer, full final-review comparison, the
broadcast session lock, dependency-hash locks, mandatory `LIBUSB_SHA256`,
SBOM, and manual-only publishing. **However, its signer-response check
required byte-equality of the whole returned PSBT, and HWI legitimately
reorders fields: Jade and Ledger reached on-device approval and were then
rejected. No 0.2.0 payment was broadcast. Do not use 0.2.0 for signing.**
Record: [`releases/SECURITY-REVIEW-0.2.0.md`](releases/SECURITY-REVIEW-0.2.0.md).

## 0.2.1 — the field-order correction

Repaired the HWI response comparison. A two-device Testnet4 payment was
broadcast and later **confirmed on 29 September 2026**. The installed 0.2.1
app could show a new unsigned review above a previous signing/final screen;
**never broadcast from a screen that mixes two payments** — close the old app
before installing any newer version. Record:
[`releases/PATCH-0.2.1.md`](releases/PATCH-0.2.1.md).

## 0.2.2 — one payment at a time

After an accepted practice-network broadcast, the app waits for one
confirmation before another payment, and an address scan's mempool spent total
pauses sends as well. Record: [`releases/PATCH-0.2.2.md`](releases/PATCH-0.2.2.md).

## 0.3.0 — warm safety work and Mutinynet

The warm items from the plan: HWI signing moved to `--stdin` (no PSBT in
subprocess argv), the parallel mutable prepare fields replaced by one frozen
`PreparedPayment` bound through signing/finalization/broadcast, selected
outpoints rechecked immediately before prepare and broadcast (a second,
independently operated Esplora on mainnet), unknown broadcast outcomes marked
outcome-unknown with the payment cleared rather than retried, the Mutinynet
practice network added with a block-1 checkpoint pin, and the stale
signing/final panel reset when a new payment is prepared. Design and limits:
[`releases/PLAN-0.3.0.md`](releases/PLAN-0.3.0.md) and
[`releases/MUTINYNET-0.3.0.md`](releases/MUTINYNET-0.3.0.md); release record:
[`releases/PATCH-0.3.0.md`](releases/PATCH-0.3.0.md).

## 0.3.1 — Send All never preselected

The owner's first Mutinynet import was a receive-only Nunchuk BSMS export; the
app safely refused a smaller payment but had preselected Send All — an unsafe
interface choice for a sweep. 0.3.1 leaves Send All unchecked, explains the
missing change path beside the amount, opens on Mutinynet, and keeps custom
amounts blocked when change is absent from the wallet definition. Record:
[`releases/PATCH-0.3.1.md`](releases/PATCH-0.3.1.md).

## 0.3.2 — one-file BIP48 change recovery

The recovery operator has **one BSMS file**, so a second Nunchuk-database
export was rejected as a workflow. For a strict native-SegWit sorted 2-of-3
wallet whose three signers share a four-level BIP48 account origin and whose
first receive address anchors `/0/0`, the app derives standard `/1/*` change
from the BSMS alone and labels it **standard-derived**, never declared.
Custom historical branch layouts remain outside this fallback. The owner then
reported **two successful physical Mutinynet sends** — Ledger + Trezor and
Jade + Trezor, the second without restarting the app. Record and evidence
limits: [`releases/PATCH-0.3.2.md`](releases/PATCH-0.3.2.md).

## 0.4.0 — visual refresh, payment receipt

The quiet slate/teal interface for the nontechnical operator, and a
session-only confirmed-payment receipt with its explorer link (browser memory
only; not history). No change to BSMS parsing, derivation, PSBT construction,
HWI transport, signature verification, fee caps, outpoint checks, or the
mainnet refusal. Record: [`releases/PATCH-0.4.0.md`](releases/PATCH-0.4.0.md).

## 0.4.1 — signature-only signer-response import

Installed 0.4.0 rejected genuine Jade and Ledger signature responses (the
0.2.0-style strict comparison had returned in a weaker form: every
non-signature field had to match byte-for-byte). 0.4.1 clones the app's
reviewed PSBT, imports **only** returned partial signatures, verifies each
cryptographically, and discards all signer-returned metadata; explicit signing
requests get ten minutes because Ledger asks for two review rounds. The owner
then completed a **Ledger + Jade Mutinynet payment**: the privacy-limited
diagnostic recorded two verified signer responses, a verified final
transaction and an accepted broadcast, and the public transaction later
confirmed on Mutinynet. Record:
[`releases/PATCH-0.4.1.md`](releases/PATCH-0.4.1.md).

## 0.4.2 — longer device-authorization waits

Jade PIN entry during device discovery can exceed one minute (HWI constructs
its Jade client and authenticates during `enumerate`). Discovery and matched
device `getxpub` checks now allow 180 seconds each; signing remains 600. The
wallet and transaction engine is unchanged from 0.4.1, and this wait change
has not yet been physically exercised. Record:
[`releases/PATCH-0.4.2.md`](releases/PATCH-0.4.2.md).

## 0.4.3 — fail-closed bare-`/*` change inference

A bare `/*` descriptor whose first address matches directly at `xpub/0` is no
longer accepted as anchoring the BIP48 `/0/0` receive path, so it can never
enable inferred `/1/*` change; such an export stays receive-only, and a
`/0/*,/1/*` restrictions line contradicting the first address is rejected
outtright. The owner also supplied Sparrow and Nunchuk BSMS exports of the
**same practice wallet**: a read-only comparison confirmed identical keys,
origins, first receive address, and identical receive/change scripts at
indices 0–19 — independent corroboration of the BIP48 inference *for that
wallet*, not for every possible wallet. Release evidence and remaining mainnet
gate: [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md). **0.4.3 itself
has no reported physical walkthrough yet; mainnet broadcast remains
disabled.**

## 0.4.4 — audit remediation and hardening

Two independent audits of `main` at `7d622ef` — one by DeepSeek, one by Z.ai —
were reconciled into [`releases/PLAN-0.4.4.md`](releases/PLAN-0.4.4.md). This release carries the
Tier 1 items only: fixes and hardening that need no fee-policy decision, no
hardware and no Apple account. **Mainnet broadcast remains refused in code and
nothing here weakens it.** No mainnet transaction has ever been prepared,
signed or broadcast by this app.

**The suite now covers the guards it previously did not.** Mutation testing had
shown that deleting the mainnet broadcast refusal, the `SIGHASH_ALL` check, the
removed-or-changed-prior-signature check, or the CSP/security headers broke
**no test at all**. The mainnet test in particular set `app.chain` to `main` on
a *testnet4* payment, so an earlier guard raised first and the lock was never
reached. Each of those is now covered, and every mutation was re-checked to
confirm it fails the suite rather than assuming it would.

**Fail-closed gaps closed.**
- `broadcast_transaction` refuses mainnet at the engine boundary as well as in
  the HTTP handler, so a future CLI, extra endpoint or refactor cannot submit
  real Bitcoin by calling the engine directly.
- A broadcast HTTP 5xx raises `BroadcastOutcomeUnknown` rather than "the network
  refused": a server error can arrive after the node accepted and relayed, so
  reporting a refusal stated something the app could not know. 4xx node
  rejections keep their precise message.
- The fee preview enforces the 10,000-sat ceiling for partial sends exactly as
  the builder does, so a preview can never display a fee the builder refuses.
- A frozen build refuses to fall back to a `PATH` lookup for the bundled `hwi`.

**Distribution and supply chain.** The project is MIT-licensed, with
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md); the DMG bundles both and the
frozen-app self-check now fails if either is missing, because the bundle
redistributes libusb under LGPL-2.1-or-later. The double-click launcher installs
from the hash-pinned lock and asserts the `embit` **version** rather than merely
that it imports. `pyyaml` is pinned and CI fails on a skipped test instead of
reporting green. The libusb digest is verified before the library is used, and
an already-present matching copy is preferred so Homebrew is not always invoked.
The SBOM records SPDX licence identifiers and no longer rejects an uppercase
digest *after* a successful build. The release workflow is a single file (the
archive copy is generated), and CI exercises the `RELEASE=1` guard to prove the
notarized path fails closed without credentials.

**Test isolation.** `test_gui_integration` wrote to the real
`~/Library/Application Support/Easy Bitcoin Multisig/settings.json`, silently
resetting a developer's own saved server settings and reporting a false failure
in any environment with a read-only `$HOME`. It is confined to a temporary
directory now.

Suite: **183 tests, 0 failures.** No change to the PSBT construction path, the
signature-verification rules, fee policy, or the set of networks on which
broadcast is possible.

## 0.4.5 — the three deferred interface items

[`releases/PLAN-0.4.4.md`](releases/PLAN-0.4.4.md) held back three Tier 1 items because they change
what the page renders, and 0.4.4 shipped without a browser walkthrough. They land
here, unchanged in intent.

- **`script-src` no longer allows `'unsafe-inline'`.** This server has exactly one
  document and rebuilds it for every request, so the page now carries a fresh
  per-response nonce. Tests assert that the header's nonce matches the injected
  `<script>` tag and that every load gets a new one.
- **Send All requires its own acknowledgement.** It moves every confirmed output
  the scan found, and the generic review checkbox said nothing about that. The
  coverage line now also names the **20-address gap** instead of saying only
  "standard gap scan".
- **A session control to clear the signed transaction.** `POST /api/clear`
  discards the prepared, possibly signed, payment; it is bound to the reviewed
  preparation id and refuses a replay. A signed-but-unbroadcast transaction is
  spend authority in its own right, so ending its life in app state is now a
  deliberate operator action with a visible control.

Suite: **187 tests, 0 failures.** Twelve mutation checks confirm that each guard
added here, and each guard added in 0.4.4, is detected when deleted. Mainnet
broadcast remains refused in code and no mainnet transaction has ever been
prepared, signed or broadcast. No change to the PSBT construction path, the
signature-verification rules, fee policy, or the set of networks on which
broadcast is possible.

## 0.4.6 — one signing box per cosigner

The signing screen listed the devices it had found and reported progress in a
sentence underneath ("Signature 1 of 2 collected…"). The owner's feedback, from
using it on a real payment, was that it is not obvious where you are: nothing
anchors "one down, one to go".

It now draws **one box per cosigner** — three for a 2-of-3, five for a 3-of-5 —
each labelled with the detected device, falling back to the signer number when
that signer's device is not attached.

- A box with a detected device is the button: "Click here to sign with this
  device."
- A box whose signer has signed turns green and reads "Signed ✓".
- A box whose device is missing reads "No device found for this signer", so the
  absent signer is visible rather than merely absent from a list.
- **A box only greys out as "Not needed" once the quota is met.** A 2-of-3 needs
  *any* two, so marking a particular box optional in advance would tell the owner
  something false — and could make them think they are stuck when they are not.
- "Look for more devices" hides once the quota is met.

The box state is read server-side from the signed PSBT on every device check
rather than remembered by the page, so the boxes cannot drift from what has
actually been signed, and they stay correct if the page is reloaded mid-signing.

Suite: **188 tests, 0 failures**, plus three Node DOM tests; a new
`tests/ui_signer_slots.cjs` pins the box states for both 2-of-3 and 3-of-5. The
signing *mechanics* are untouched — only how progress is presented. No change to
the PSBT construction path, the signature-verification rules, fee policy, or the
set of networks on which broadcast is possible.

## 0.4.7 — the last signature fills its own box

Correction to 0.4.6, found by the owner on the first real payment through it.

**The bug.** When the signature that met the quota arrived, `signWith` called
`showFinal` and returned *before* re-rendering the boxes. So the screen read
"Signature 2 of 2 collected. Signers 1 and 2 signed." next to a box still
offering "Click here to sign with this device" — the last signature was accepted
and verified, but its own box never filled. The surplus box also stayed on "No
device found" instead of greying out as no longer needed.

**The jump.** `showFinal` scrolled the final panel to the top of the window,
which pushed the just-completed boxes off screen at the exact moment the operator
wants to see them fill. `renderSignable` also scrolled on every device refresh,
so finding the second device moved the page too.

**Fixed.** The completion path now writes the authoritative signer list into the
boxes and re-renders them *before* handing off to the final panel; `showFinal` no
longer scrolls at all, and the device-refresh path only scrolls when entering the
step. Completing the quota now leaves the operator looking at three boxes — two
green, one greyed — with the final panel immediately below.

`tests/ui_signer_slots.cjs` reproduces the reported sequence exactly (the Ledger
signed first and is no longer attached, then the Jade completes the quota) and
asserts that the last box fills, the earlier one stays filled, the surplus greys,
and the final panel is **not** scrolled into view. Both halves were confirmed by
re-introducing each fault and watching the test fail.

Suite: **188 tests, 0 failures**, plus three Node DOM tests. No change to the
PSBT construction path, the signature-verification rules, fee policy, or the set
of networks on which broadcast is possible. Mainnet broadcast remains refused in
code.

### Also in 0.4.7 — the operator could not see that a payment had been sent

Reported by the owner after several payments: pressing Broadcast made the whole
transaction area disappear, and the only confirmation was the pending banner at
the very top of the page. The viewport had been at the bottom of the send card,
so the screen looked empty. The payments did go out; the app simply never showed
it. In a recovery tool that is a dangerous way to fail — an operator who cannot
tell whether money moved may send it again.

**What changed.** A successful broadcast now shows the outcome **where the
transaction was prepared**, not only in the banner above the fold:

- A "Payment sent · waiting for one confirmation" panel appears in the page where
  the send card was, carrying the transaction ID, a block-explorer link, and a
  **Check again** button.
- An unknown outcome — the transport failed after submission — shows the same
  panel with the do-not-resend wording, in the same place.
- The top banner still appears and remains the refresh-safe tracker; the in-place
  notice is cleared when a new wallet is opened or a new payment is prepared.

The old behaviour relied on `scrollIntoView` successfully moving the window to a
banner that was off screen; whatever defeated that scroll, the fix no longer
depends on scrolling at all.

**Guards added.** `tests/ui_broadcast_outcome.cjs` drives a successful broadcast
and asserts the in-place notice appears with the right transaction ID and link
while the send card is retired. A new static test asserts that **every** `$("id")`
in the served page has a matching element in the markup — the dangerous shape of
this bug class, where a handler touches a node that is not there after doing
something irreversible. CI and the source archive now take the UI tests by glob,
so a new `tests/ui_*.cjs` runs without a workflow edit.

Suite: **189 tests, 0 failures**, plus four Node DOM tests. No change to the
PSBT construction path, the signature-verification rules, fee policy, or the set
of networks on which broadcast is possible.

## 0.4.8 — attributable diagnostics and visible progress

Two threads, both from the owner reading a real 0.4.7 diagnostic report from a
successful two-device Mutinynet payment.

### The report could not say what had been refused

`DIAGNOSTIC_STAGES` used stage names (`transaction_prepare`, `signer_response`)
while the rejection handler derived a *route* name (`prepare`, `sign`). The two
never matched, so **13 of 14 routes** were recorded as an unattributable
`request`. Only `/api/broadcast` lined up, by coincidence. A refused signature
therefore logged exactly like a refused fee estimate: if a device had rejected
that payment, the report could not have said so.

Rejections are now attributed through an explicit `DIAGNOSTIC_ROUTE_STAGES` map.
Routes deliberately absent from it — fee estimates, price, settings, status — are
ordinary interface feedback and now record **nothing**: five of the twenty-one
events in the owner's report were debounced estimate calls, and the buffer holds
only 80 events, so chatter was evicting the events that matter.

### The report had no network and no device

Each event now carries the selected **network** and, where a device was involved,
its **class** — the two things that decide what a failure means, since
"broadcast accepted" differs between a practice network and mainnet, and the
devices behave differently enough that "which one, when" is the first
troubleshooting question. `signer_check` records which classes it saw;
`signer_response` records which one signed or refused. A device *model* is not an
identity: the value passes a token check and anything else is dropped rather than
escaped, so no path, serial, fingerprint, address or error text can be written.
Timestamps stay — the owner's 45-second-versus-46-second timeout catch was made
with them.

### The screen showed nothing during the slowest step

After a device signed, `signWith` waited for a **full device re-enumeration**
before redrawing the boxes. The server had already said which signer signed, so
the box could have filled immediately; instead the operator signed on the device
and the screen kept offering to sign for five to ten seconds, or minutes when the
next device wanted a PIN. That dead zone is manufactured, not inherent, and it is
the most likely reason someone clicks a second time. The box now fills from the
response, and the re-scan happens afterwards.

The progress bar also gains **elapsed seconds**, shown only after five seconds so
a quick step is never made to look slow. Counting up is the one signal that
proves progress instead of asserting it. The slow-step wording now matches the
phase it is actually in.

### No wait duration is advertised anywhere

The Ledger wait used to read "the app will wait up to 10 minutes", and Jade's PIN
entry "may take several minutes". **Both are gone, and a test now forbids
advertising a wait.** The internal timeouts (180s enumeration, 180s identity
check, 600s signature) exist so a slow human is never cut off mid-review —
someone finding their reading glasses should not be raced. Publishing such a
number invites the operator to treat it as a licence to walk away while a signing
ceremony is open. The screen says the app is working and waits; it never says for
how long.

A one-line dismissible note now sets that expectation up front: this app talks to
the Bitcoin network and to signing devices, so a click can take a few seconds —
please wait rather than clicking again.

Suite: **193 tests, 0 failures**, plus five Node DOM tests. Changes are confined
to the diagnostic vocabulary, the progress bar and its copy. No change to the
PSBT construction path, the signature-verification rules, fee policy, or the set
of networks on which broadcast is possible. Mainnet broadcast remains refused in
code.

## 0.4.9 — a fraction of a Bitcoin needs no leading zero

Reported by the owner from the amount box: typing a fraction without a leading
zero left the amount apparently broken. `btcToSats` matched
`/^\d+(?:\.\d{1,8})?$/`, so `.1` and `.0001` were refused outright while `0.1`
worked, and the only feedback was *"Enter a BTC amount of at least 0.00000546,
with up to 8 decimal places"* — which blamed the size for a spelling problem. The
fee estimate then never appeared, so the box looked dead.

**The natural spelling is now accepted rather than taught against.** A leading
bare `.` is normalised to `0.`, and a trailing `.` — what the box holds half-way
through typing `1.5` — is tolerated. Leaving the box rewrites it into the
canonical form, so `.1` visibly becomes `0.1` and the habit teaches itself rather
than being explained.

The rejection message now says what is actually wrong: too many decimal places
says so, unparseable input asks for a number, and only a genuinely below-dust
amount mentions the 546-satoshi floor. That message was previously shown for every
rejected spelling, including amounts far larger than the floor.

`tests/ui_amount_entry.cjs` pins the accepted spellings, the canonical rewrite,
the refusal of genuinely bad input, and each distinct message.

### A successful report, and the one thing it exposed

The owner's first 0.4.8 report is a clean two-device Mutinynet payment — Trezor
then Jade, `signer_response: verified` for each, `final_transaction: verified`,
`broadcast: accepted` — and it confirms the 0.4.8 work: **13 events, none
unattributable, every one carrying its network**, against 21 events with 5
unattributable and no network at all before. Its timings also show the dead zone
closing: the Trezor signature verified at 13:45:40 and the next device re-scan
landed at 13:45:47, so the box would previously have sat offering to sign for
those seven seconds.

It also exposed one ambiguity. Two of its four `signer_check` events carried no
`found` key, which meant "no usable device was visible" — but a reader could not
tell that apart from a field the app does not write. `found` is now written
whenever a check runs, as an explicit `[]` when nothing usable was seen.

Suite: **193 tests, 0 failures**, plus six Node DOM tests; the three mutations that
reintroduce each fault are all detected. No change to the PSBT construction path,
the signature-verification rules, fee policy, or the set of networks on which
broadcast is possible.

## 0.4.10 — the progress bar has an owner

Reported by the owner from the confirmation screen: pressing **Check again** —
the control that asks the explorer whether the payment has confirmed — brought up
the progress bar showing *"connect your Jade"*, an old device-search message,
rather than *"checking the blockchain"*. The payment then showed as confirmed and
the bar disappeared.

The bar had **no owner**. `setBusy` was a single global slot that several
operations wrote to — a balance check, a device search, a signing request, a
broadcast — so whichever spoke last owned the text and whichever finished first
cleared it. Two consequences, both reachable whenever operations overlap:

- a device search could surface **during** a blockchain check, which is the
  message the owner saw; and
- an operation that had already finished could **wipe the message of one still
  running**, so a slow step looked like it had silently stopped.

`setBusy` now returns a handle holding a token, and only the newest holder may
change the text or clear the bar. A late finisher can do neither. Every call site
— the balance refresh, the wallet import, both device searches, signing and
broadcast — claims its own token and finishes through its own handle, and the
signing path uses `busy.say` to move from "waiting for the device" to "signature
verified" without releasing ownership.

`tests/ui_busy_ownership.cjs` reproduces the reported sequence: a device search
still running when Check again is pressed. It asserts the check's message replaces
the device message, that the finished search can neither hide the bar nor blank
nor overwrite it, that the device text is unreachable while the check owns the bar,
and that only the newest holder can end it.

Suite: **193 tests, 0 failures**, plus seven Node DOM tests; each reintroduced
fault is detected by mutation. No change to the PSBT construction path, the
signature-verification rules, fee policy, or the set of networks on which
broadcast is possible.

## 0.4.11 — the form says the leading zero is optional

The owner asked twice for the amount form to say something about the leading zero.
The first request was answered by **0.4.9**, which removed the requirement
entirely: `.001` and `0.001` now both parse, and the box rewrites itself to the
canonical spelling on blur. But the form was left saying nothing about it, so
anyone who had learned to avoid typing `.001` had no way to discover that the rule
was gone. Removing a rule silently is not the same as telling somebody it is gone.

The form now states it:

- the empty-field hint reads *"Enter a BTC amount — .001 and 0.001 both work. The
  minimum is 0.00000546, or tick Send all."*
- the placeholder reads *"e.g. .001 or 0.001"*, showing the optional-zero spelling
  before anything is typed
- the not-a-number hint gives *".001 or 0.001"* as its example

Both spellings are named rather than the rule being asserted, because a rule that
no longer exists must not be taught. `tests/ui_amount_entry.cjs` pins the hint, the
placeholder and both examples, so the guidance cannot quietly disappear again.

Suite: **193 tests, 0 failures**, plus seven Node DOM tests. Copy and hint text
only; no change to the PSBT construction path, the signature-verification rules,
fee policy, or the set of networks on which broadcast is possible.

## 0.4.12 — the first notarized release

**No application behaviour changed.** This release exists so the download can be
installed the way any Mac app is: double-click the DMG, drag the app to
Applications, run it. No right-click → Open, no "unidentified developer" warning.

Everything before this was **ad-hoc signed**. macOS permits that locally, because a
file you built yourself carries no `com.apple.quarantine` attribute and Gatekeeper
never inspects it — which is why every test build has run fine here while a
downloaded copy would not. Downloading is what applies quarantine, and notarization
is the only thing that clears it.

The DMG and the app inside are both signed with the Developer ID certificate for
Bitseeker LLC, sealed with the hardened runtime, notarized by Apple, and **both
stapled**. Stapling the app matters for the recovery case: an unstapled app is
verified by an online lookup, so an operator with no network would be refused.

### What the first real notarized build taught

Two faults, neither visible by reading the script and both found by running it —
and both of which would have broken this release at its final step:

1. **Only the DMG was stapled.** `stapler validate` on the app reported "does not
   have a ticket stapled to it". It stapled successfully from the same submission,
   so the fix cost no extra Apple round trip.
2. **The Gatekeeper gate assessed the DMG.** A disk image is not code-signed, so
   `spctl` reports `rejected, source=no usable signature` even for a correctly
   notarized image — while the app inside reports `accepted, source=Notarized
   Developer ID`. A build that had done everything right would have aborted.

Both are pinned by `ReleaseGateTests`.

### Notarization is slow, in a way worth recording

Apple took **54 minutes**, and `notarytool --wait` never returned while Apple's own
status already read `Accepted`. Apple's developer forums carry a cluster of the same
symptom, one titled *"All notarization submissions stuck In Progress — new Developer
ID account"*, with durations from 20 hours to 5 days. New teams' first submissions
are the known-affected case.

**Consequences, now policy:** judge progress by `notarytool info`, never by the
`--wait` spinner. And do **not** notarize during iteration — develop by running from
source (`python desktop.py`, seconds), package unsigned for bundle testing, and
notarize only to publish.

Suite: **210 tests, 0 failures**, plus seven Node DOM tests.

## 0.4.13 — light and dark, one palette

**No application behaviour changed.** This release is appearance and wording: a light
theme and a dark theme with a **Dark Theme / Light Theme** button in the header, a
colour palette small enough to hold in your head, and three things on the opening
screen rewritten so they say what they mean.

### Why it was worth doing properly

The owner noticed colours changing between revisions without anyone asking. That was
real, and the cause was structural rather than carelessness: every new surface was
written as a fresh hex value instead of reusing a named one, and nothing was watching.
By 0.4.12 `ui.html` held **113 colour literals and 91 distinct values, of which only 10
had ever been chosen.** The other 89 were borders, hover shades, focus rings and
shadows, each reasonable on the day it was added.

Five hues now fill a fixed set of roles:

| Hue | Roles |
|---|---|
| neutral | `--canvas` `--paper` `--sunken` `--header*` `--ink` `--muted` `--line*` |
| accent | `--accent*` `--focus` — the one action colour |
| pending | `--pending*` — waiting and caution |
| done | `--done*` — completed and verified |
| failed | `--failed*` — refused and error |

Every rule names a role. Mainnet stopped being 13 override rules carrying their own
hex values and became the same roles read more loudly, so it themes automatically and
its alarm survives the change from light to dark.

Real Bitcoin wears an **orange frame** and practice networks wear **green**, in both
themes. Mainnet used to repaint the canvas, the header, the borders and the action
colour, which turned "Review payment" burnt orange on a step that signs nothing and
sends nothing. The owner read it exactly as written: *you do not want to click red
things.* `body.live-mode` went from 12 overridden roles to **one** (`--frame`), so the
interior is identical and a button means the same thing on every network.

### Three things the owner could not read

- **The theme control was a crescent moon.** *"It's a little bit too cute for me…
  don't make people guess that it's a sun or a moon."* A crescent means *night*, or
  *make it night*, or *the theme is dark*, depending on who reads it. It now says
  **Dark Theme** or **Light Theme**: the theme you would get, in words.
- **The network was a closed dropdown**, narrower than the file box beside it, so
  neither the options nor the current choice were visible. It is now three labelled
  cards — Mutinynet, Testnet4, Bitcoin LIVE — with the active one highlighted.
  Everything that reads or sets the network goes through one function.
- **The note beneath it was backwards:** *"A Testnet4 wallet needs a new Mutinynet
  wallet and test coins."* It now reads *"Mutinynet and Testnet4 are separate test
  networks. Each needs its own wallet and its own coins to work."*

### The app inside the image is now stapled

The v0.4.12 image was built from a copy of the app taken **before** any staple ran, so
the app a downloader received carried no ticket of its own. Gatekeeper then verified it
by an **online** lookup: accepted when connected, **refused offline** — the wrong way
for a recovery tool to fail.

The app is now notarised and stapled first, and the image is built from it. The build
then **mounts its own finished image** and validates the copy inside, so an unstapled
app fails the build rather than somebody's first offline launch.

Two other faults went with it: `spctl` was assessing the **DMG**, which a disk image
can never pass because it is not code-signed, and an `xattr -cr` on the staged copy was
silently **stripping the staple back off**.

This had been left undone because it needs a second Apple round trip and the first
submission took 54 minutes. Measured: a later submission for the same team took about
**40 seconds**. The objection no longer held.

### Why the theme cannot break the app

The theme code runs in front of every other line, so an exception in it would have
cost the signing screen rather than the theme. It probes each browser API before use
and the whole block is wrapped.

That was not theoretical. The suite's DOM harnesses stub a deliberately minimal
document, and the first version broke **all seven** of them by assuming `window`. The
failure was worth more than the tests it fixed: a decoration reaching for a global
that might not exist, in front of a money-moving app, is the shape of the bug that
does the damage.

### How it stays fixed

`tests/test_palette.py` fails the build when:

- a colour is named anywhere outside the four palette blocks;
- light and dark do not define exactly the same roles — a role missing from dark
  silently inherits the light value, which is exactly how one white border appears on
  a dark screen;
- mainnet overrides a role that does not exist;
- `--ink` falls below 7:1 against `--canvas` or `--paper`, because addresses and
  amounts are read character by character and a theme that makes that harder is wrong
  whatever it looks like.

All four guards are mutation-checked: reintroducing each fault is detected.

One existing test was itself holding the drift in place — `test_slow_work_shows_a_spinner`
asserted the literal `#ffd447`. It now asserts the role.

Suite: **229 tests, 0 failures**, plus eight Node DOM tests.


## 0.4.14 — BSMS quorum, up to three physical keys

This release accepts native-SegWit multisig BSMS wallets with two or three
cosigner keys and follows the threshold recorded in the wallet definition. The
threshold can be any valid value for those key counts. Signing, transaction size
estimates, input selection, signer slots, and finalization use that policy. Wallets
with more than three keys remain unsupported. The opening screen says: “Supports
hardware multisig wallets with up to three physical keys.”

Change handling remains guarded: the standard BIP48 inferred change route is still
limited to its anchored sorted 2-of-3 case. Other partial sends require a declared
change path; otherwise the operator must deliberately choose Send All, which creates
no change output. The app does not build wallets or create keys.

Automated evidence and the local Apple build/notarization checks are recorded in
[`releases/PATCH-0.4.14.md`](releases/PATCH-0.4.14.md). The owner reported the local install worked;
that is not evidence of a physical transaction using every supported quorum.
Mainnet broadcast remained disabled in this release. 0.5.0 is the release that
changes that, behind the final-screen and backend gates recorded below.

## 0.4.15 candidate — OneKey Classic 1S through HWI's Trezor backend

HWI 3.2.0 already enumerates the OneKey Classic 1S through its Trezor-compatible
interface and returns the human-readable label `OneKey Classic 1S`. The installed
Developer ID build's hardened HWI helper could not load its bundled libusb. A
temporary HWI helper signed with Apple's `disable-library-validation` runtime
exception enumerated the device successfully. The candidate scopes that exception
to the HWI helper, leaves the main app's signing policy unchanged, and checks that
libusb can query USB descriptors during the Mac build without opening a wallet. The UI uses HWI's safe model label so the signer
appears as OneKey Classic 1S rather than Trezor 1.

HWI version and Python requirements are unchanged. The owner reports the locally
notarized app worked perfectly with a OneKey Classic 1S and its newly created
wallet. The owner then completed and cleared a mainnet dry run on candidate 0.4.15.
The diagnostics record a declared change path, consistent complete scan, transaction
preparation, two verified signer responses, and verified finalization. The screenshots
show no broadcast and subsequent clearing of the signed transaction. This is an
owner-reported dry run, not an on-chain payment; no independent raw-transaction decode
report was supplied. The candidate is not a published release. Full evidence is in
[`releases/PATCH-0.4.15.md`](releases/PATCH-0.4.15.md).

## 0.5.1 — the first published release that can send real Bitcoin

0.5.1 publishes the 0.5.0 transaction engine unchanged, together with wording
that the first live mainnet payment proved was wrong. No transaction logic in
`wallet_service.py`, `signing.py`, `probe.py`, `network_config.py`, `gui.py` or
`desktop.py` differs from the candidate tagged `v0.5.0-rc1`, so the engine that
sent real Bitcoin is the engine published here. The change is documentation,
interface wording and the version string.

### What the first live payment showed

The owner made the project's first real mainnet payment with the 0.5.0
candidate: a 2-of-3 native-SegWit spend, signed by an OneKey Classic 1S (through
HWI's Trezor backend) and a Ledger Nano S, broadcast through the app and
confirmed on chain. The confirmed transaction was decoded from two independent
explorers, and its change output script was compared against the change script
derived locally from the wallet file. The engine behaved as designed: the fee
stayed inside the 25 sat/vB and 10,000-sat ceilings, the change index chosen was
the first unused one, and the change output was genuinely this wallet's.

The one thing the run exposed is that **neither signer displayed the change
address**. That is normal for that firmware class — the app marks the change
output as belonging to the wallet, and the device folds it into a silent
"change" line — but the app had been telling the operator, in five separate
places, to check the change address on the device. An instruction that cannot be
followed is worse than no instruction, because it manufactures confidence. 0.5.1
replaces all five with plain-language guidance aimed at the person the app is
actually for: the devices show the destination, amount and fee, and the change
address is checked in the wallet software that holds the wallet file.

No transaction identifiers, addresses or amounts are recorded in this
repository. It is public, and this is the owner's live wallet.

### Evidence

The full record, including the artifact hashes, is in
[`releases/PATCH-0.5.1.md`](releases/PATCH-0.5.1.md).

## 0.6.2 — retiring a review also retires its network

**Published 2026-10-02** as tag `v0.6.2` from commit `7b4db85`, built by workflow
run 36959242210: source archive
`a901a66bf7f4ab0144c09ad510720e4443e16f93ff0bb71d7c51c9d29eb5f0d5`, DMG
`5f648aa1728127970c1182760026c742d1c66be400fa171f7a1f19470ef1ab53`. The owner
chose this fix as the next release (m01412), after 0.6.1 was published, and asked
for it to be published once the candidate was verified.

`ui.html`'s `invalidateReview()` cleared `finalTxid` but left `finalChain`, and
the two other places that retire a review had the same gap: the clear-signed
handler and the signer-step reset. `finalChain` is what the broadcast posts as
`mainnet_opt_in`, so a stale value from a retired review was the one way the
mainnet opt-in could be derived from the wrong payment. It was not reachable —
a broadcast also needs a current `finalTxid`, which is only ever set beside
`finalChain` — so this is hygiene and defence in depth rather than a live fund
risk, and it is recorded that way rather than as a vulnerability.

All three sites now clear the chain with the rest of the review, and
`tests/ui_broadcast_outcome.cjs` reads the broadcast request body to pin three
things: a retired review leaves no network behind, a broadcast with no finalized
network sends `mainnet_opt_in: false`, and a payment genuinely finalized on
mainnet still sends `true`. The new assertions were checked against the unfixed
file, where they fail on the first of the three.

Nothing about how a payment is built, signed, finalized or submitted changed;
the engine is unchanged from 0.5.1.

## 0.6.1 — the practice networks move behind a gate

**Published 2026-10-02** as tag `v0.6.1` from commit `2977930`, built by workflow
run 36957927251: source archive
`144df834ecae0f983c5c23bf1a86f85509ce0cf00f7dffc6c5d937451e44f5ca`, DMG
`22f0280fb010fc7595c48a79ae15894a5b24501b351764d99d2f0ccae47cb7d8`. The version moved from
0.6.0 to 0.6.1 before publication: the owner opened the first candidate and
directed that live Bitcoin must not be an option inside developer mode (m01190),
so the gate now offers the two practice networks only and the gate button is the
way back. Nothing was ever published as 0.6.0.

0.6.1 changes where the network is chosen, and nothing about how a payment is
built, signed or sent. The app opens on **Bitcoin mainnet**. Mutinynet and
Testnet4 sit behind a button on the opening screen labelled **Enter Developer
Mode**, which says plainly that the operator is leaving live Bitcoin and, on
confirmation, switches the session to Mutinynet. Mutinynet is the default
practice network because a default must be chosen and its blocks come quickly;
Testnet4 remains selectable for a wallet that already holds Testnet4 coins.

The reason is the operator, not the code. The person this app is written for — a
spouse, executor or accountant — cannot judge a three-network radio control, and
a practice network needs a second wallet file, two or three devices and coins
from somewhere the app does not provide. A control that person cannot use is not
a safety feature; it is a way to pick the wrong network. The capability is kept
and now documented, reached deliberately instead of sitting in the middle of the
opening screen.

The engine is unchanged from 0.5.1, so nothing here may be described as new
transaction capability. What did change, and why each mattered:

- The selected network remains **in-memory for the session only**, exactly as it
  was. The gate must not be paid for with persistence: a practice network that
  survived a restart would be a new way to send from the wrong chain, and the
  gate would have made things worse rather than better.
- Changing network clears the loaded wallet, the scan and any prepared payment,
  and reloads the server settings and fee quote — the same clearing the network
  cards already did.
- The gate refuses to change network while a payment is prepared, and says so. The
  refusal is enforced where the network actually moves, in **both** directions,
  not only on the button: an earlier version guarded the way in and let the way
  out move the chain out from under a prepared payment. `tests/ui_developer_mode.cjs`
  catches that by re-enabling the button by hand and pressing it. An even earlier
  draft disabled the gate on every practice network, which would have stranded the
  operator in developer mode with no way back; the same test covers the exit.
- The orange/green frame and the network badge are never hidden and cannot
  disagree. The frame is the whole signal and the badge names the network, so a
  practice network can never wear the mainnet frame or vice versa.
- One dead field left `gui.py`: `broadcasting_available` was hardcoded `True` and
  read by nothing.

Documents that still said the app opened on a practice network were corrected in
the same change — `AGENTS.md`, `PHASE-HANDOFF.md`, `README.md` and the public
site `docs/index.html` — and developer mode is documented for developers as a
test bench while stating that practice networks are not the app's purpose.

### Evidence

The full record, including what was verified, what the owner decided, and the
items deliberately left out of scope, is in
[`releases/PATCH-0.6.1.md`](releases/PATCH-0.6.1.md). The scope the owner signed
off, with the reasoning and the out-of-scope list, is
[`releases/SCOPE-0.6.1.md`](releases/SCOPE-0.6.1.md).

## 0.5.0 candidate — live mainnet broadcast

0.5.0 removes the stopgap that refused every mainnet broadcast. It is the first
build that can submit a real Bitcoin payment, and it does so behind two gates:
the final review screen requires an explicit confirmation that names real
Bitcoin, and `wallet_service.broadcast_transaction` takes a `mainnet_opt_in`
argument that defaults to `False`, so any caller that omits it fails closed. The
operator sees **one** checkbox; the backend flag is defence in depth against a
caller, not a second human action. Earlier wording in `AGENTS.md` described a
"separate mainnet checkbox" and was corrected here.

The prepared-payment binding, final review, genesis checks, two-source outpoint
recheck and txid confirmation are unchanged, as are the 25 sat/vB and 10,000
estimated-satoshi fee caps. The 0.4.15 OneKey work is included: HWI's own device
label is preferred over the generic model name, the nested HWI helper carries the
`disable-library-validation` entitlement alone, and the Mac build preflights
libusb before sealing.

The DMG is `c1831dde2042c8bebae14d6c545531dcb609a1f2fcedb71a433626bca5f8e056`
and the source archive
`3a65fe936023dcd5b44735648ccec1afc69d73dcdc1f21935960efdb7d5d854f`. The app is
Developer ID signed by Bitseeker LLC (`B8G5L7M8TB`), notarized, stapled and
accepted by Gatekeeper; the nested helper carries the library-validation
entitlement and the main app carries no entitlement at all. A PyInstaller
CArchive extraction of the shipped bundle was compared recursively against the
working-tree sources — `gui.py`, `wallet_service.py`, `version.py`, `probe.py`
and `network_config.py` matched with zero differences, the old refusal string
`not enabled in this build` appears nowhere in the bundle, and the shipped
`ui.html` is byte-identical to the source. The suite runs 238 tests.

An independent pre-broadcast review of this candidate returned a pass. No mainnet
transaction has been sent with it: the owner's live send is the next acceptance
step. The candidate is committed as `51ea400`, tagged `v0.5.0-rc1` locally, and is
neither pushed nor published. Full evidence is in
[`releases/PATCH-0.5.0.md`](releases/PATCH-0.5.0.md).

## Release anchors and artifact provenance

A tag is the only authority for what a release contained. This table records the
commit each tag resolves to, and the SHA-256 of the assets that were actually
published, read back from the `SHA256SUMS` attached to each GitHub release.

| Tag | Resolves to | Published source archive | Published DMG |
| --- | --- | --- | --- |
| `v0.4.12` | `4e85d64` | `f3937c30a69aca4129595d27aac02113508eac801a6b463815a39158fd62c26b` | `21b3c80e3d452ff27343fec011467cc0256b30b4305185337692e51875ba02f8` |
| `v0.4.13` | `351e126` | `f61b58265c4539467fb33e3d0a26d8373a15cbe78301859620b0d4b6ec65f97a` | `d961255d788ef39dbb4b04667bbc73316bedbdb2dce05c685cdd4a3af74a7c0d` |
| `v0.4.14` | `d530a22` | `ca9a999df23054b7cb6f0368550eb1137ba3518472ef84236c5d389684578313` | `d80a1fccd70311b76722e506c86f486b0d807f9778b91fd386586840604e6e1d` |
| `v0.5.1` | `e833162` | `b1b3f7e4018fdd1d94758867ccaa05fd083c35f7624bc1ad2ba8abb1ee1c8ba9` | `73691cc4fd71591cd53acc22f08273a97b20cf09593e6c8009bd5b39706387d0` |
| `v0.6.1` | `2977930` | `144df834ecae0f983c5c23bf1a86f85509ce0cf00f7dffc6c5d937451e44f5ca` | `22f0280fb010fc7595c48a79ae15894a5b24501b351764d99d2f0ccae47cb7d8` |
| `v0.6.2` | `7b4db85` | `a901a66bf7f4ab0144c09ad510720e4443e16f93ff0bb71d7c51c9d29eb5f0d5` | `5f648aa1728127970c1182760026c742d1c66be400fa171f7a1f19470ef1ab53` |

`v0.4.14` resolves to `d530a221de87`, the commit the published assets were built from.

### A bare version tag means a published release

Every `vX.Y.Z` tag on the remote names a GitHub release, and this project's rule is
that such a tag is never moved. (Asset coverage before 0.2.0 is uneven — see the
note at the top of this file.) A build that is committed but not yet released
therefore does not take the bare name:

| Build | Anchor | State |
| --- | --- | --- |
| 0.5.0 | commit `51ea400`, local annotated tag `v0.5.0-rc1` | Signed and notarized, and the build that made the project's first live mainnet payment. Never published under its own number; 0.5.1 publishes the same engine. The bare tag `v0.5.0` is never created, so no published tag has to move. |
| 0.4.15 | source archive only — no commit, no tag | Built, signed, notarized and owner-tested; never published. |

`v0.5.1` was tagged by the release workflow itself (`gh release create`), which
writes a **lightweight** tag, so its artifact hashes and signing and notarization
evidence live in the GitHub release notes, the published `SHA256SUMS` and
`releases/PATCH-0.5.1.md` rather than in a tag object. Teaching the workflow to
create an annotated tag is a candidate change for the next release. Every published
tag in this repository, including the 0.5.1 one, is left exactly as it is, because
correcting it would mean moving a published tag.

### Local build output is not a published asset

`dist/` is not tracked (it is in `.gitignore`), and the 0.4.14 artifacts under it
are a **pre-publication candidate**, not the shipped release. Their status text
still reads "GitHub Actions must repeat the release checks", and their hashes
differ from the published ones:

| Asset | Published | Local `dist/` |
| --- | --- | --- |
| 0.4.14 source archive | `ca9a999df23054b7cb6f0368550eb1137ba3518472ef84236c5d389684578313` | `5102d09f31f40d199d43dc67577d4afbcb5d9f2399aa92bfb9c875495a04a4da` |
| 0.4.14 macOS DMG | `d80a1fccd70311b76722e506c86f486b0d807f9778b91fd386586840604e6e1d` | `c168b41aece1ff66829f57c7fb7aec77543b846e4fb6f59cddbbde5a7ac3969c` |

Never quote a `dist/` hash as the hash of a released artifact. Rebuilding is not
reproducible byte-for-byte, so the published `SHA256SUMS` is the only authority.

### 0.4.15 has no tag, and its source survives only locally

0.4.15 was built, signed, notarized and handed to the owner to test, but it was
never published and **has no commit of its own**: the OneKey work lived in the
working tree alongside the later 0.5.0 changes and was committed once, in
`51ea400`. Its source survives only as
`dist/bitcoin-easy-multisig-signer-v0.4.15.tar.gz`, SHA-256
`261c537b061bf547e4075fde6c15deb4757e3152ffcbdb87621dba0a8af48117`, plus the
0.4.15 portion of the `51ea400` diff. Because `dist/` is untracked, that archive is
not in version control at all. The 0.5.0 source archive is
`dist/bitcoin-easy-multisig-signer-v0.5.0.tar.gz`, SHA-256
`3a65fe936023dcd5b44735648ccec1afc69d73dcdc1f21935960efdb7d5d854f`, and is
likewise local-only until 0.5.0 is published.

Both archives are mirrored, byte-identical and hash-verified, outside the build
tree at `/Users/christerry/Documents/deepseek-harness/default-workspace/besa-release-archive/`
(`bitcoin-easy-multisig-signer-v0.4.15.tar.gz` and
`bitcoin-easy-multisig-signer-v0.5.0.tar.gz`). That mirror is a second copy on the
same machine, not an off-machine backup.

Because 0.4.15 has no release of its own to attach to, its source archive should be
attached to the GitHub 0.5.0 release, clearly labelled as the unpublished 0.4.15
candidate, so its source stops depending on one machine. Preserve both archives
when publishing, or the source for these two builds is lost.

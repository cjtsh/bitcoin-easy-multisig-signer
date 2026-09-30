# Release history and correction record

This is the consolidated, chronological record of the published versions that
carry a reviewed evidence file: what changed, what the evidence was, and what
was later corrected. Each entry links its full evidence file. The earlier
`0.0.x`–`0.1.26` iteration tags predate that practice and are recorded by tag
and commit subject below rather than given individual entries. **Current status
and next gates live in [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md); current
capabilities live in [`README.md`](README.md).** Two standing facts apply to
every version:

- **Mainnet broadcast is refused in code.** No version of this app has ever
  prepared, signed, or broadcast a mainnet transaction.
- Every published release is immutable: one version per build, `SHA256SUMS`
  verified, CycloneDX SBOM attached. Never republish under an existing tag.

| Version | One-line summary | Evidence |
| --- | --- | --- |
| 0.1.x | Phases 1–4: balance view, send eligibility, unsigned PSBT, testnet signing/broadcast | [`AUDIT-BASELINE-0.1.27.md`](AUDIT-BASELINE-0.1.27.md), [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md) |
| 0.2.0 | Hot-item security fixes; **hardware signing broken — do not use** | [`SECURITY-REVIEW-0.2.0.md`](SECURITY-REVIEW-0.2.0.md) |
| 0.2.1 | HWI field-order repair; confirmed Testnet4 payment | [`PATCH-0.2.1.md`](PATCH-0.2.1.md) |
| 0.2.2 | One-payment-at-a-time confirmation wait | [`PATCH-0.2.2.md`](PATCH-0.2.2.md) |
| 0.3.0 | Warm safety work, Mutinynet, stale-screen fix | [`PATCH-0.3.0.md`](PATCH-0.3.0.md), [`PLAN-0.3.0.md`](PLAN-0.3.0.md), [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md) |
| 0.3.1 | Send All never preselected; Mutinynet default network | [`PATCH-0.3.1.md`](PATCH-0.3.1.md) |
| 0.3.2 | One-file BIP48 custom sends from a Nunchuk BSMS | [`PATCH-0.3.2.md`](PATCH-0.3.2.md) |
| 0.4.0 | Visual refresh; session-only payment receipt | [`PATCH-0.4.0.md`](PATCH-0.4.0.md) |
| 0.4.1 | Signature-only signer-response import; longer signing window | [`PATCH-0.4.1.md`](PATCH-0.4.1.md) |
| 0.4.2 | Three-minute device discovery/authorization waits (Jade) | [`PATCH-0.4.2.md`](PATCH-0.4.2.md) |
| 0.4.3 | Fail-closed bare-`/*` change inference; same-wallet export proof | [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md) |
| 0.4.4 | Audit remediation: tests for the guards that had none, three fail-closed gaps, MIT licence and third-party notices | [`PLAN-0.4.4.md`](PLAN-0.4.4.md), [`AUDIT-DEEPSEEK-0.4.3.md`](AUDIT-DEEPSEEK-0.4.3.md), [`AUDIT-ZAI-0.4.3.md`](AUDIT-ZAI-0.4.3.md) |
| 0.4.5 | CSP nonce (no `'unsafe-inline'`), Send-All acknowledgement naming the 20-address gap, and a control to clear signed bytes | [`PLAN-0.4.4.md`](PLAN-0.4.4.md) |
| 0.4.6 | One signing box per cosigner, so the missing signer is visible at a glance | — |
| 0.4.7 | Correction: the final signature fills its own box, and completing does not scroll the boxes off screen | — |
| 0.4.8 | Attributable diagnostics, and visible progress that never advertises a wait | — |
| 0.4.9 | A fraction of a Bitcoin no longer needs a leading zero | — |
| **0.4.10** | **Current.** One progress bar, and only the operation that owns it may change or clear it | — |

## 0.1.x — Phases 1 through 4 on Testnet4

The framework releases: BSMS import and balance view (Phase 1), explained send
eligibility (Phase 2), independently verified unsigned PSBT preparation
(Phase 3), then signing and Testnet4 broadcast with hardware devices
(Phase 4, v0.1.27). Two real Testnet4 payments confirmed, between them using
all three supported devices — Jade, Trezor Safe 3, and Ledger Nano S Plus. The
independent audit of that era, including its hot findings (inferred change
ownership, incomplete final review, unverified finalization signatures,
signer-response binding), is preserved in
[`AUDIT-BASELINE-0.1.27.md`](AUDIT-BASELINE-0.1.27.md); the build and live-use
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
Record: [`SECURITY-REVIEW-0.2.0.md`](SECURITY-REVIEW-0.2.0.md).

## 0.2.1 — the field-order correction

Repaired the HWI response comparison. A two-device Testnet4 payment was
broadcast and later **confirmed on 29 September 2026**. The installed 0.2.1
app could show a new unsigned review above a previous signing/final screen;
**never broadcast from a screen that mixes two payments** — close the old app
before installing any newer version. Record:
[`PATCH-0.2.1.md`](PATCH-0.2.1.md).

## 0.2.2 — one payment at a time

After an accepted practice-network broadcast, the app waits for one
confirmation before another payment, and an address scan's mempool spent total
pauses sends as well. Record: [`PATCH-0.2.2.md`](PATCH-0.2.2.md).

## 0.3.0 — warm safety work and Mutinynet

The warm items from the plan: HWI signing moved to `--stdin` (no PSBT in
subprocess argv), the parallel mutable prepare fields replaced by one frozen
`PreparedPayment` bound through signing/finalization/broadcast, selected
outpoints rechecked immediately before prepare and broadcast (a second,
independently operated Esplora on mainnet), unknown broadcast outcomes marked
outcome-unknown with the payment cleared rather than retried, the Mutinynet
practice network added with a block-1 checkpoint pin, and the stale
signing/final panel reset when a new payment is prepared. Design and limits:
[`PLAN-0.3.0.md`](PLAN-0.3.0.md) and
[`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md); release record:
[`PATCH-0.3.0.md`](PATCH-0.3.0.md).

## 0.3.1 — Send All never preselected

The owner's first Mutinynet import was a receive-only Nunchuk BSMS export; the
app safely refused a smaller payment but had preselected Send All — an unsafe
interface choice for a sweep. 0.3.1 leaves Send All unchecked, explains the
missing change path beside the amount, opens on Mutinynet, and keeps custom
amounts blocked when change is absent from the wallet definition. Record:
[`PATCH-0.3.1.md`](PATCH-0.3.1.md).

## 0.3.2 — one-file BIP48 change recovery

The recovery operator has **one BSMS file**, so a second Nunchuk-database
export was rejected as a workflow. For a strict native-SegWit sorted 2-of-3
wallet whose three signers share a four-level BIP48 account origin and whose
first receive address anchors `/0/0`, the app derives standard `/1/*` change
from the BSMS alone and labels it **standard-derived**, never declared.
Custom historical branch layouts remain outside this fallback. The owner then
reported **two successful physical Mutinynet sends** — Ledger + Trezor and
Jade + Trezor, the second without restarting the app. Record and evidence
limits: [`PATCH-0.3.2.md`](PATCH-0.3.2.md).

## 0.4.0 — visual refresh, payment receipt

The quiet slate/teal interface for the nontechnical operator, and a
session-only confirmed-payment receipt with its explorer link (browser memory
only; not history). No change to BSMS parsing, derivation, PSBT construction,
HWI transport, signature verification, fee caps, outpoint checks, or the
mainnet refusal. Record: [`PATCH-0.4.0.md`](PATCH-0.4.0.md).

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
[`PATCH-0.4.1.md`](PATCH-0.4.1.md).

## 0.4.2 — longer device-authorization waits

Jade PIN entry during device discovery can exceed one minute (HWI constructs
its Jade client and authenticates during `enumerate`). Discovery and matched
device `getxpub` checks now allow 180 seconds each; signing remains 600. The
wallet and transaction engine is unchanged from 0.4.1, and this wait change
has not yet been physically exercised. Record:
[`PATCH-0.4.2.md`](PATCH-0.4.2.md).

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
were reconciled into [`PLAN-0.4.4.md`](PLAN-0.4.4.md). This release carries the
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

Suite: **182 tests, 0 failures.** No change to the PSBT construction path, the
signature-verification rules, fee policy, or the set of networks on which
broadcast is possible.

## 0.4.5 — the three deferred interface items

[`PLAN-0.4.4.md`](PLAN-0.4.4.md) held back three Tier 1 items because they change
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

Suite: **192 tests, 0 failures**, plus five Node DOM tests. Changes are confined
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

## 0.4.10 — the progress bar has an owner (current)

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

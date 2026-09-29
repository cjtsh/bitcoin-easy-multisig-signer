# Release history and correction record

This is the consolidated, chronological record of every published version: what
changed, what the evidence was, and what was later corrected. Each entry links
its full evidence file. **Current status and next gates live in
[`PHASE-HANDOFF.md`](PHASE-HANDOFF.md); current capabilities live in
[`README.md`](README.md).** Two standing facts apply to every version below:

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
| **0.4.3** | **Current.** Fail-closed bare-`/*` change inference; same-wallet export proof | [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md) |

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

## 0.4.3 — fail-closed bare-`/*` change inference (current)

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

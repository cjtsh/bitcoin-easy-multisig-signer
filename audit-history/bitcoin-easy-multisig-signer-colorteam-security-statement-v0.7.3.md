# Bitcoin Easy Signer — Security Statement (v0.7.3)

*One page, nontechnical, release-specific. Read it together with the full audit
report it summarizes.*

## What was reviewed

**Bitcoin Easy Signer v0.7.3** — tag `v0.7.3`, source commit
`a227da4073f705cbb4ca47f939e80fc0921c77d7`, released 2026-10-27. The audit covered
the source at that revision and the ten published release files. Every file's
SHA-256 was checked against the signed `SHA256SUMS`; the macOS app was verified as
signed by **Bitseeker LLC (team B8G5L7M8TB)**, notarized by Apple, and stapled;
build-provenance attestations bind the files to that exact source commit. This
release's build window had five workflow runs and nine attempts — including one
candidate dispatched without notarization by mistake, which the promotion pipeline
**refused at its manifest check** — and nothing was ever published from any failed
or refused attempt (verified against the live build records).

## Who reviewed it

A panel of **six AI examiners** (five specialists plus a referee), run on the ZCode
harness with the GLM model, working from an audit plan written by a **different AI
on a different harness (DeepSeek)**; the plan's scope was **signed by the owner
(Bitseeker LLC, 26 Oct 2026)** before the audit began, and the plan's hash is
unchanged from before the panel ran to after it finished. This is AI-performed
review with human ownership of the scope — **no human audit firm reviewed the
code**.

## What we found — ⚠️ CONDITIONAL

- **The blocking flaw from the last audit (v0.7.2) is fixed and proven fixed by
  execution**: the new payment-sequencing gate was broken on purpose by three
  examiners and the referee, and its alarms rang — the race they used to demonstrate
  the flaw can no longer happen.
- **No way was found to steal, redirect, or spy on the operator's Bitcoin** — in
  this cycle or any of the five before it. All twenty-one earlier findings remain
  fixed with no regressions.
- **Two items keep the grade conditional** (neither is a theft path):
  - **CT-36 (medium):** behind a network server that *accepts* a payment and then
    claims it refused (a lying or misbehaving server — the server address is an
    operator setting), the app believes nothing was sent and allows the next
    payment. Both payments would be ones the operator reviewed and approved. Fix:
    treat any answer received after sending as "result unknown" and tell the user to
    check an explorer.
  - **CT-41 (low):** one half of the new gate has no alarm test yet (the behaviour
    was verified correct; one test fixes it).
- Several smaller items were filed (CT-37…CT-40, CT-42…CT-44 in the technical
  report), including a record-keeping note that this release's own failed build
  attempts are under-counted in the release documents.
- Not checked: physical hardware devices and their firmware (verified through the
  app's own verification code only); the inside of the Windows/Linux downloads
  (verified by hash, signature and attestation); the owner's computers and accounts;
  the width of the lying-server scenario on a live network. An audit is evidence
  about one version on one day — not a guarantee that software contains no bugs,
  malware, or vulnerabilities.

## What you should verify yourself

- Download only from the **official repository's release page**, and where you can,
  compare the file's SHA-256 against the release's signed `SHA256SUMS`.
- **Verify the destination address and the amount on your hardware device's own
  screen, every time.** No software review replaces that habit.
- **If the app ever says "the network refused this transaction," check an explorer
  or your wallet before sending again** — until the CT-36 fix ships and a re-audit
  clears it.

## Read the evidence

Full report: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.3.md` ·
Scope plan and lock: `…colorteam-audit-plan-v0.7.3.md`, `…colorteam-audit-lock-v0.7.3.md` ·
Repository: `github.com/cjtsh/bitcoin-easy-multisig-signer` · Framework:
`github.com/cjtsh/ai-color-team-audit-framework` · All earlier cycles' records:
`audit-history/` in the repository, unedited.

> This review was carried out using AI agents and the tools identified in the audit
> record. We made a good-faith effort to examine the stated security risks and
> document what we found. An audit can reduce uncertainty, but cannot guarantee that
> software contains no bugs, malware, or vulnerabilities. Please review the findings
> and verify the official download and transaction details before using it.
> **Trust, but verify.**

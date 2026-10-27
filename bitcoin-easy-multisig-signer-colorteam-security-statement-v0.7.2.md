# Bitcoin Easy Signer — Security Statement (v0.7.2)

*One page, nontechnical, release-specific. Read it together with the full audit
report it summarizes.*

## ⛔ THIS REVISION IS GRADED BLOCKED — do not rely on v0.7.2 as review-cleared for live funds

The audit of this version found one open blocking issue, described below, and the
audit framework's rules require the blocked grade until it is fixed and re-checked.
This statement describes a blocked revision plainly — it is not an endorsement of
v0.7.2 for use with real funds, and earlier versions' statements are not extended by
it.

## What was reviewed

**Bitcoin Easy Signer v0.7.2** — tag `v0.7.2`, source commit
`1e51dcfa45d6f61c83c14aeb1998725fbd705ba9`, released 2026-10-26. The audit covered
the source at that revision and the ten published release files. Every file's
SHA-256 was checked against the signed `SHA256SUMS`; the macOS app was verified as
signed by **Bitseeker LLC (team B8G5L7M8TB)**, notarized by Apple, and stapled; build
provenance attestations bind the files to that exact source commit. Five earlier
build attempts for this release failed (Apple notary flakes and one disk-timing
error) and **published nothing** — verified against the live build records.

## Who reviewed it

A panel of **six AI examiners** (five specialists plus a referee), run on the ZCode
harness with the GLM model, working from an audit plan written by a **different AI
on a different harness (DeepSeek)**; the plan's scope was **signed by the owner
(Bitseeker LLC, 26 Oct 2026)** before the audit began, and the plan's hash is
unchanged from before the panel ran to after it finished. This is AI-performed
review with human ownership of the scope — **no human audit firm reviewed the
code**.

## What we checked — and what we found

- **The previous audit's finding is fixed and proven fixed.** The v0.7.1 report's
  named remedy (a broadcast-time pending-payment refusal, in both halves, with pins
  that fail when the protection is removed) was implemented, and three examiners
  plus the referee personally broke it and watched the alarms ring.
- **The blocking issue (CT-27):** the new gate reads the pending-payment record,
  but that record is written only **after** a broadcast finishes — so during the
  seconds while a first payment's broadcast is still travelling, a **second,
  separately-approved payment can be sent**, contrary to the app's documented
  promise that it refuses a second payment while one waits for confirmation. Three
  examiners demonstrated this independently and the referee re-ran the
  demonstration personally. **No way to steal or redirect money was found** — both
  payments in every demonstration were fully reviewed on screen and approved on the
  device; this is a sequencing defect between two approved payments, and the fix is
  small and exactly known (the technical report gives the recipe).
- Two minor hardening items and several record-keeping notes were also filed
  (CT-28…CT-35 in the technical report).
- Not checked: physical hardware devices and their firmware (verified through the
  app's own verification code only); the inside of the Windows/Linux downloads
  (verified by hash, signature and attestation); the owner's computers and
  accounts; the window's width on a live network. An audit is evidence about one
  version on one day — not a guarantee that software contains no bugs, malware, or
  vulnerabilities.

## What you should verify yourself

- Download only from the **official repository's release page**, and where you can,
  compare the file's SHA-256 against the release's signed `SHA256SUMS`.
- **Verify the destination address and the amount on your hardware device's own
  screen, every time.** No software review replaces that habit.
- **While any payment is still confirming — including while it is still sending —
  check your wallet before sending another.** Do not rely on the app's gate until
  the fix ships and a re-audit clears it.

## Read the evidence

Full report: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.2.md` ·
Scope plan and lock: `…colorteam-audit-plan-v0.7.2.md`, `…colorteam-audit-lock-v0.7.2.md` ·
Repository: `github.com/cjtsh/bitcoin-easy-multisig-signer` · Framework:
`github.com/cjtsh/ai-color-team-audit-framework` · All earlier cycles' records:
`audit-history/` in the repository, unedited.

> This review was carried out using AI agents and the tools identified in the audit
> record. We made a good-faith effort to examine the stated security risks and
> document what we found. An audit can reduce uncertainty, but cannot guarantee that
> software contains no bugs, malware, or vulnerabilities. Please review the findings
> and verify the official download and transaction details before using it.
> **Trust, but verify.**

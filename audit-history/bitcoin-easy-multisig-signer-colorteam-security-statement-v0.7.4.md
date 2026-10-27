# Bitcoin Easy Signer — Security Statement (v0.7.4)

*One page, nontechnical, release-specific. Read it together with the full audit
report it summarizes.*

## What was reviewed

**Bitcoin Easy Signer v0.7.4** — tag `v0.7.4`, source commit
`9d4d7bb471c80512cac7b7dc6c014855393cac4f`, released 2026-10-27. The audit covered
the source at that revision and the ten published release files. Every file's
SHA-256 was checked against the signed `SHA256SUMS`; the macOS app was verified as
signed by **Bitseeker LLC (team B8G5L7M8TB)**, notarized by Apple, and stapled;
build-provenance attestations bind the files to that exact source commit. This
release's build window had two workflow runs and three attempts — the promotion's
first attempt failed on Apple's notary service and **published nothing**; the retry
published. No partial release, no overwritten tag.

## Who reviewed it

A panel of **six AI examiners** (five specialists plus a referee), run on the ZCode
harness with the GLM model, working from an audit plan written by a **different AI
on a different harness (DeepSeek)**; the plan's scope was **signed by the owner
(Bitseeker LLC, 27 Oct 2026)** before the audit began, and the plan's hash is
unchanged from before the panel ran to after it finished. This is AI-performed
review with human ownership of the scope — **no human audit firm reviewed the
code**.

## What we found — ⚠️ CONDITIONAL (one alarm test away from cleared)

- **No way was found to steal, redirect, or spy on the operator's Bitcoin** — in
  this cycle or any of the seven before it. All twenty-one earlier findings remain
  fixed with no regressions, and **last cycle's two findings are fixed and proven
  fixed by execution** (the examiners and the referee each broke the new protections
  and watched the alarms ring).
- The auditors state plainly that **everything else in this cycle is at cleared
  level**. Two items keep the grade conditional — neither is a theft path:
  - **CT-47 (info):** one branch of the new payment gate (a network address the
    app's own settings rules reject) has no alarm test yet — the behaviour was
    executed and verified correct (it refuses before any byte is sent), but nothing
    fails if the code were quietly changed later.
  - **CT-49 (low):** the existing alarm for that gate checks the refusal *type* but
    not *where in the code* the check sits — a future edit could silently move a
    check past the point where its "nothing was sent" promise is true.
  - **Fix: two one-line alarm tests.** Then a short re-audit.
- Smaller items were filed (CT-45…CT-52 in the technical report), including a
  record-keeping note that this release's own build attempts are recorded on the
  development branch but not yet pinned by an automatic test.
- Not checked: physical hardware devices and their firmware (verified through the
  app's own verification code only); the inside of the Windows/Linux downloads
  (verified by hash, signature and attestation); the owner's computers and accounts;
  live mainnet servers (server behaviours were simulated byte-accurately on a
  loopback). An audit is evidence about one version on one day — not a guarantee
  that software contains no bugs, malware, or vulnerabilities.

## What you should verify yourself

- Download only from the **official repository's release page**, and where you can,
  compare the file's SHA-256 against the release's signed `SHA256SUMS`.
- **Verify the destination address and the amount on your hardware device's own
  screen, every time.** No software review replaces that habit.
- **If a payment's result is ever reported as unknown, check an explorer or your
  wallet before sending again.**

## Read the evidence

Full report: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.4.md` ·
Scope plan and lock: `…colorteam-audit-plan-v0.7.4.md`, `…colorteam-audit-lock-v0.7.4.md` ·
Repository: `github.com/cjtsh/bitcoin-easy-multisig-signer` · Framework:
`github.com/cjtsh/ai-color-team-audit-framework` · All earlier cycles' records:
`audit-history/` in the repository, unedited.

> This review was carried out using AI agents and the tools identified in the audit
> record. We made a good-faith effort to examine the stated security risks and
> document what we found. An audit can reduce uncertainty, but cannot guarantee that
> software contains no bugs, malware, or vulnerabilities. Please review the findings
> and verify the official download and transaction details before using it.
> **Trust, but verify.**

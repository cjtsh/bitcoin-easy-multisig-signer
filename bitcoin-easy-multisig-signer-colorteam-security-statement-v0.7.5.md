# Bitcoin Easy Signer — Security Statement (v0.7.5)

*One page, nontechnical, release-specific. Read it together with the full audit
report it summarizes.*

## What was reviewed

**Bitcoin Easy Signer v0.7.5** — tag `v0.7.5`, source commit
`b254fe6f6fc724f25e0c40658bd430c4bffaedcb`, released 2026-10-27. The audit covered
the source at that revision and the ten published release files. Every file's
SHA-256 was checked against the signed `SHA256SUMS`; the macOS app was verified as
signed by **Bitseeker LLC (team B8G5L7M8TB)**, notarized by Apple, and stapled;
build-provenance attestations bind the files to that exact source commit. This
release's build window had three workflow runs and four attempts — one candidate
was cancelled before producing anything, the promotion's first attempt failed on
Apple's notary service and **published nothing**, and the retry published. No
partial release, no overwritten tag.

## Who reviewed it

A panel of **six AI examiners** (five specialists plus a referee), run on the ZCode
harness with the GLM model, working from an audit plan written by a **different AI
model on the DeepSeek harness**; the plan's scope was **signed by the owner
(Bitseeker LLC, 27 Oct 2026)** before the audit began, and the plan's hash is
unchanged from before the panel ran to after it finished. This is AI-performed
review with human ownership of the scope — **no human audit firm reviewed the
code**.

## What we found — ✅ CLEARED

- **No way was found to steal, redirect, or spy on the operator's Bitcoin** — in
  this cycle or any of the eight before it.
- **Every finding from every earlier audit is now closed** — all 52, each verified
  fixed by breaking the protection on purpose and watching its alarm ring. Nothing
  is open.
- The two small additions this cycle (an input-type guard at the app's engine
  boundary, and an abort path that pauses the wallet *and* tells the host it was
  an abort) were attacked hardest: both hold, both have alarms that were watched
  ringing.
- One-line hardening notes were filed for future maintenance (a stricter input-type
  check at a boundary only direct code can reach; two more alarm shapes; a plan
  wording note) — none is reachable through the app and none blocks anything.
- Not checked: physical hardware devices and their firmware (verified through the
  app's own verification code only); the inside of the Windows/Linux downloads
  (verified by hash, signature and attestation); the owner's computers and
  accounts; live mainnet servers (server behaviours were simulated byte-accurately
  on a loopback). An audit is evidence about one version on one day — not a
  guarantee that software contains no bugs, malware, or vulnerabilities.

## What you should verify yourself

- Download only from the **official repository's release page**, and where you can,
  compare the file's SHA-256 against the release's signed `SHA256SUMS`.
- **Verify the destination address and the amount on your hardware device's own
  screen, every time.** No software review replaces that habit.
- **If a payment's result is ever reported as unknown, check an explorer or your
  wallet before sending again.**

## Read the evidence

Full report: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.5.md` ·
Scope plan and lock: `…colorteam-audit-plan-v0.7.5.md`, `…colorteam-audit-lock-v0.7.5.md` ·
Repository: `github.com/cjtsh/bitcoin-easy-multisig-signer` · Framework:
`github.com/cjtsh/ai-color-team-audit-framework` · All earlier cycles' records:
`audit-history/` in the repository, unedited.

> This review was carried out using AI agents and the tools identified in the audit
> record. We made a good-faith effort to examine the stated security risks and
> document what we found. An audit can reduce uncertainty, but cannot guarantee that
> software contains no bugs, malware, or vulnerabilities. Please review the findings
> and verify the official download and transaction details before using it.
> **Trust, but verify.**

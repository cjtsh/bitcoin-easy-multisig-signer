# Bitcoin Easy Signer — Security Statement (v0.7.1)

*One page, nontechnical, release-specific. Read it together with the full audit
report it summarizes.*

## What was reviewed

**Bitcoin Easy Signer v0.7.1** — tag `v0.7.1`, source commit
`8923ca0273380a9cb1ea7e7e964c6332dda5a777`, released 2026-10-26. The audit covered
the source at that revision and the ten published release files (the macOS `.dmg`,
the Windows `.zip`, the Linux `.AppImage` and `.tar.gz`, the source `.tar.gz`, three
build-provenance SBOMs, and the signed checksum list). Every file's SHA-256 was
checked against the signed `SHA256SUMS`; the macOS app inside the `.dmg` was
verified as signed by **Bitseeker LLC (team B8G5L7M8TB)**, notarized by Apple, and
stapled; build-provenance attestations bind all ten files to that exact source
commit.

## Who reviewed it

A panel of **six AI examiners** (five specialists plus a referee), run on the ZCode
harness with the GLM model, working from an audit plan written by a **different AI
on a different harness (DeepSeek)** so writer and checker cannot share a blind spot;
the plan's scope was read and **signed by the owner (Bitseeker LLC, 26 Oct 2026)**
before the audit began, and the plan's hash is unchanged from before the panel ran
to after it finished. This is AI-performed review with human ownership of the scope
— **no human audit firm reviewed the code**, and no model identity here is an
independent verification.

## What we checked

The paths that matter for a multisig wallet: the transaction review → sign →
finalize → broadcast chain (substitution, tampering, stale state, consent gates);
the signing devices and their proofs of identity; the network servers the app talks
to (redirects, impersonation, wrong-network answers); what the app writes to logs
and diagnostics; every dependency and build step between source and download; and
whether the published files are exactly what the checked build produced. The
specific weaknesses named by the previous audit (v0.7.0) were re-tested by **breaking
each protection on purpose and watching its alarm ring** — all three now hold.

## What we found — ⚠️ CONDITIONAL

- **No way was found to steal, redirect, or spy on the operator's Bitcoin** — in
  this cycle or any of the three before it.
- All three v0.7.0 findings are **fixed and proven fixed by execution**.
- One **new** finding keeps the grade conditional (**CT-22, low severity**): under
  rare timing and a network server that stays silent at the wrong moment, a
  **second, fully reviewed and separately approved** payment can be sent while an
  earlier one is still confirming (it is replaceable and visible; an honest server
  blocks it). No attacker path was demonstrated — the app's own screen cannot
  produce it. **Fix: a one-line pending-payment check at broadcast time.**
- Two minor hardening items and two record-keeping notes (CT-23…CT-26) do not hold
  the grade.
- This release's build history includes **three failed builds** (two Apple notary
  flakes, one security-scan refusal of a test fixture); **none published anything**,
  verified against the live build records.
- Not checked: physical hardware devices and their firmware (verified through the
  app's own verification code only); the inside of the Windows/Linux downloads
  (verified by hash, signature and attestation); the owner's computers and
  accounts. An audit is evidence about one version on one day — not a guarantee
  that the software has no bugs, malware, or vulnerabilities.

## What you should verify yourself

- Download only from the **official repository's release page**, and where you can,
  compare the file's SHA-256 against the release's `SHA256SUMS` (it is signed with
  the project's public key).
- **Verify the destination address and the amount on your hardware device's own
  screen, every time.** No software review replaces that habit.
- While a payment is still confirming, check your wallet before sending again.

## Read the evidence

Full report: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.1.md` ·
Scope plan and lock: `…colorteam-audit-plan-v0.7.1.md`, `…colorteam-audit-lock-v0.7.1.md` ·
Repository: `github.com/cjtsh/bitcoin-easy-multisig-signer` · Framework:
`github.com/cjtsh/ai-color-team-audit-framework` · All earlier cycles' records:
`audit-history/` in the repository, unedited.

> This review was carried out using AI agents and the tools identified in the audit
> record. We made a good-faith effort to examine the stated security risks and
> document what we found. An audit can reduce uncertainty, but cannot guarantee that
> software contains no bugs, malware, or vulnerabilities. Please review the findings
> and verify the official download and transaction details before using it.
> **Trust, but verify.**

# Public Security Statement — Bitcoin Easy Multisig Signer v0.6.8

**What was reviewed.** Release **v0.6.8** of Bitcoin Easy Multisig Signer — source
commit `0d4e01f60c7695d720099f9d8e9e23b38da63102` (tag `v0.6.8`) and all ten
published download files (macOS DMG, Windows zip, Linux AppImage and tarball, source
archive, three SBOMs, `SHA256SUMS` and its GPG signature), published
2026-10-10T21:31:47Z. Every download file was independently re-fetched and
hash-matched to the signed checksum list and to the tamper-evident build record,
which ties the files to the exact source commit above.

**Who reviewed it.** An AI-agent audit panel (five specialist examiners plus a
referee) run in the Kimi Code desktop app, using the Color Team Audit Framework
(tag `v1.5.1`). The audit plan was written by a different tool (the DeepSeek
harness) and signed by the maintainer (Bitseeker LLC, 2026-10-11); the two session
identifiers are on record and differ. No human security firm reviewed the software;
the AI models involved are not independently verified and are recorded as declared
only. This statement is not a certification and not a guarantee.

**What we checked.** The money path (review → sign → broadcast), including a
counterfeit-device attack and poisoned-component attacks; the network and privacy
boundary; the local interface's access controls; the build and release pipeline,
including its own booby-trapped-input defenses; every dependency pin against its
public registry; and the published downloads against their checksums, signature,
notarization, and build record. Hardware wallets themselves, and the Windows/Linux
packages' execution, were not tested — the packages were verified by fingerprint.

**What we found.** Grade: **⚠️ CONDITIONAL** — good software with named work
remaining. No way was found to move, lose, or misdirect funds, leak wallet material,
or ship a tampered download. Four low-severity items remain open, all concerning
tests and records that watch the software rather than what the software does: one
response-checking branch and three backup guards lack their own tripwire tests
(CT-01, CT-02); the shipped control inventory's line-reference claim is not true of
itself (CT-03); and the release's bundled web page briefly linked the previous
version's downloads before the live site was corrected (CT-04). Eight housekeeping
notes (CT-05…CT-12) are listed in the report. Because these items are open, this
release is not labeled "CLEARED"; the named fixes and a short re-check are the path
there. Nothing found prevents ordinary use with the standard precautions below.

**What you should verify yourself.** Download only from the project's official
GitHub Releases page or official website; check your download against the published
`SHA256SUMS` and its signature (`SIGNING.md` in the repository walks you through
it); and always confirm the recipient address and amount on your hardware device's
own screen before approving. Trust, but verify.

**Read the evidence.** The full technical report, plain-English safety review, and
findings ledger: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md` in
the repository root (`github.com/cjtsh/bitcoin-easy-multisig-signer`), alongside the
signed audit plan and the scope lock.

*This review was carried out using AI agents and the tools identified in the audit
record. We made a good-faith effort to examine the stated security risks and
document what we found. An audit can reduce uncertainty, but cannot guarantee that
software contains no bugs, malware, or vulnerabilities. Please review the findings
and verify the official download and transaction details before using it. Trust,
but verify.*

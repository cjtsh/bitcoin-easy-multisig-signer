# Public Security Statement — Bitcoin Easy Multisig Signer v0.6.9

**What was reviewed.** Release **v0.6.9** of Bitcoin Easy Multisig Signer — source
commit `e90e5b93ece284f990ca2b75be1e798baa3efc9c` (tag `v0.6.9`) and all ten
published download files (macOS DMG, Windows zip, Linux AppImage and tarball, source
archive, three SBOMs, `SHA256SUMS` and its GPG signature), published
2026-10-11T15:33:09Z. Every download file was independently re-fetched and
hash-matched to the signed checksum list and to the tamper-evident build records,
which tie the files to the exact source commit above.

**Who reviewed it.** An AI-agent audit panel (five specialist examiners plus a
referee) run in the Kimi Code desktop app, using the Color Team Audit Framework
(tag `v1.5.1`), as a follow-up "conversion re-check" of the v0.6.8 review. The audit
plan was written by a different tool (the DeepSeek harness) and signed by the
maintainer (Bitseeker LLC, 2026-10-11); the two session identifiers are on record
and differ. No human security firm reviewed the software; the AI models involved are
recorded as declared only, not independently verified. This statement is not a
certification and not a guarantee.

**What we checked.** Everything that changed since v0.6.9's predecessor, with proof
the rest is unchanged byte-for-byte: the money path (review → sign → broadcast),
the network and privacy boundary, the local interface's access controls and its new
connection ceiling, the build and release pipeline, every dependency pin, and the
published downloads against their checksums, signature, notarization, and build
records. The referee personally re-ran 23 of the most important checks. Hardware
wallets themselves, and execution of the Windows/Linux packages, were not tested —
those packages were verified by fingerprint.

**What we found.** Grade: **⚠️ CONDITIONAL** — good software with named work
remaining. All twelve findings from the v0.6.8 review are fixed and were verified
fixed by re-testing each one (12 of 12). No way was found to move, lose, or
misdirect funds, leak wallet material, or ship a tampered download. Two low-severity
items are open: two shipped tests have names that promise more coverage than they
deliver — the underlying protection was attacked directly and works (CT-14) — and a
hostile program already on your own computer could deliberately keep the app's
window busy until that program stops, with no risk to funds (CT-13, awaiting an
owner decision). Four housekeeping notes (CT-15…CT-18) are listed in the report.
Because these items are open, this release is not labeled "CLEARED"; the named
fixes and a short re-check are the path there. Nothing found prevents ordinary use
with the standard precautions below.

**What you should verify yourself.** Download only from the project's official
GitHub Releases page or official website; check your download against the published
`SHA256SUMS` and its signature (`SIGNING.md` in the repository walks you through
it); and always confirm the recipient address and amount on your hardware device's
own screen before approving. Trust, but verify.

**Read the evidence.** The full technical report, plain-English safety review, and
findings ledger: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.9.md` in
the repository root (`github.com/cjtsh/bitcoin-easy-multisig-signer`), alongside the
signed audit plan and the scope lock. Earlier cycles' artifacts are archived,
unedited, under `audit-history/`.

*This review was carried out using AI agents and the tools identified in the audit
record. We made a good-faith effort to examine the stated security risks and
document what we found. An audit can reduce uncertainty, but cannot guarantee that
software contains no bugs, malware, or vulnerabilities. Please review the findings
and verify the official download and transaction details before using it. Trust,
but verify.*

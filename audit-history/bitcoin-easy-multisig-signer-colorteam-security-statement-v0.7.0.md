# Public Security Statement — Bitcoin Easy Multisig Signer v0.7.0

**What was reviewed.** Release **v0.7.0** of Bitcoin Easy Multisig Signer — source
commit `4fe8f2955e29cae6838e2ba0b8029c9abae9fdeb` (tag `v0.7.0`) and all ten
published download files (macOS DMG, Windows zip, Linux AppImage and tarball, source
archive, three SBOMs, `SHA256SUMS` and its GPG signature), published
2026-10-16T06:15:36Z. Every download file was independently re-fetched and
hash-matched to the signed checksum list and to the tamper-evident build records,
which tie the files to the exact source commit above.

**Who reviewed it.** An AI-agent audit panel (five specialist examiners plus a
referee) run in the Kimi Code desktop app, using the Color Team Audit Framework
(tag `v1.5.1`), as a follow-up "conversion re-check" of the v0.6.9 review in the
v0.6.8 lineage. The audit plan was written by a different tool (the DeepSeek
harness) and signed by the maintainer (Bitseeker LLC, 16 Oct 2026); the two session
identifiers are on record and differ. No human security firm reviewed the software;
the AI models involved are recorded as declared only, not independently verified.
This statement is not a certification and not a guarantee.

**What we checked.** Everything that changed since v0.6.9, with proof the rest is
unchanged byte-for-byte: the money path (review → sign → broadcast), the network and
privacy boundary, the local interface's access controls and its reworked
flood-handling, the build and release pipeline (including the new guard that watches
the retired build paths), every dependency pin (none moved), and the published
downloads against their checksums, signature, notarization (the stapled ticket was
verified on the actual download), and build records. The referee personally re-ran
18 of the most important checks. The release's interrupted first publish attempt was
verified against the build system's records: it published nothing. Hardware wallets
themselves, and execution of the Windows/Linux packages, were not tested — those
packages were verified by fingerprint.

**What we found.** Grade: **⚠️ CONDITIONAL** — good software with named work
remaining. **All eighteen findings from the previous reviews are fixed and were
verified fixed by re-testing each one (18 of 18)** — including the two that held the
v0.6.9 grade. No way was found to move, lose, or misdirect funds, leak wallet
material, or ship a tampered download. Three informational items are open: one
internal guard has no test proving its alarm works — the guarded behavior was tested
another way and works (CT-21); the project's control checklist cannot "see" one type
of file, so one pipeline guard's claim arrived untracked (CT-20); and a documented
availability trade-off in the window's flood-handling is recorded for the owner's
awareness (CT-19). Because the first two are open without an owner decision, this
release is not labeled "CLEARED"; the named fixes and a short re-check are the path
there. Nothing found prevents ordinary use with the standard precautions below.

**What you should verify yourself.** Download only from the project's official
GitHub Releases page or official website; check your download against the published
`SHA256SUMS` and its signature (`SIGNING.md` in the repository walks you through
it); and always confirm the recipient address and amount on your hardware device's
own screen before approving. Trust, but verify.

**Read the evidence.** The full technical report, plain-English safety review, and
findings ledger: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.0.md` in
the repository root (`github.com/cjtsh/bitcoin-easy-multisig-signer`), alongside the
signed audit plan and the scope lock. Earlier cycles' artifacts are archived,
unedited, under `audit-history/`.

*This review was carried out using AI agents and the tools identified in the audit
record. We made a good-faith effort to examine the stated security risks and
document what we found. An audit can reduce uncertainty, but cannot guarantee that
software contains no bugs, malware, or vulnerabilities. Please review the findings
and verify the official download and transaction details before using it. Trust,
but verify.*

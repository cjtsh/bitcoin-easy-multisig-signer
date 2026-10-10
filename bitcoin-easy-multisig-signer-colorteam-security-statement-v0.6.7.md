# Public Security Statement — Bitcoin Easy Multisig Signer v0.6.7

**For the people this software is for** — fiduciaries, trustees, lawyers, accountants,
spouses, and trusted advisors holding Bitcoin that must survive them. Written 2026-10-10
by the audit that reviewed this release. One page; the full evidence is linked below.

## What was reviewed

**Bitcoin Easy Multisig Signer v0.6.7**, the current public release: tag `v0.6.7`,
source commit `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b`, published 2026-10-07. The
audit tested the source at that exact commit and the actual published download bytes:

| Published artifact | SHA-256 |
|---|---|
| `Bitcoin-Easy-Signer-v0.6.7-macOS.dmg` | `0f9043c88f7a0bbc6b9bbbf8289de9f67bc8c5678b83c7c4358cee68ab14a015` |
| `Bitcoin-Easy-Signer-v0.6.7-windows-x64.zip` | `5062890c348fd130c0c83362435169f113f7f046b4970a72bb4ba255c980a680` |
| `Bitcoin-Easy-Signer-v0.6.7-linux-x86_64.AppImage` | `22ad01ff79ac4a01ce853711e43471846bcb347d2c925959ed58caa39b7f4152` |
| `Bitcoin-Easy-Signer-v0.6.7-linux-x86_64.tar.gz` | `7ce8377b9186b712f8435aa238e029cfc71973f857c1ed35b592e37bac993cdd` |
| `bitcoin-easy-multisig-signer-v0.6.7.tar.gz` (source) | `0c6da58c984c1a9937fcea66ca41b230ac679a6937d4b404f265f57333f294b6` |
| `BUILD-SBOM.json` (+ `-linux-x86_64`, `-windows-x64`) | in `SHA256SUMS` below |
| `SHA256SUMS` / `SHA256SUMS.asc` | `88592ed5…ff9f11` / `5e80f892…fd0ca2` (full digests in the report) |

**These binaries WERE independently verified by the audit**: every downloaded byte
re-hashed and matched (8/8 against the signed manifest, and equal to the digests of the
exact build run that produced them); the GPG signature on `SHA256SUMS` verified Good
against the repository's committed public key (Bitseeker LLC,
`ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7`); the macOS app's Developer ID signature and
Apple notarization verified valid. What was **not** done: the Windows and Linux bundles
were verified by digest only (not executed), and no physical hardware wallet was
attached — device behavior was tested through constructed responses.

## The verdict

**Audit grade: ⛔ BLOCKED.** Read this plainly: the audit's pre-locked rules force this
grade, and it applies to **how releases are built and checked** — not to what the app
does with your Bitcoin. Every attempt to make the app sign, broadcast, or leak something
unapproved **failed and was refused by the app's own code** — that is the strongest
money-path result this framework can report. What blocked the grade: a command-injection
flaw in a release-form field (CT-72), thirteen old frozen release points that today's
safety sweep never inspects (CT-76), a library check that guards less than it claims in
the developer-only source mode (CT-73), and release-safety checks whose tests stay green
when broken (CT-74/75). **Release readiness:** the next release must not be promoted
from this revision until those are fixed and the `environment:` credential wiring is
landed in a tagged revision. None of these flaws was exploited, and the v0.6.7 bytes you
downloaded remain exactly the verified, signed bytes named above.

## What this is and is not (plain language)

The app is a networked loopback desktop program plus hardware-wallet signing plus public
block-explorer servers. It **holds no wallet key, creates no wallet, never asks for seed
words or a PIN, and never signs or broadcasts silently**. You supply one BSMS wallet
file (from someone you trust, over a channel you trust — the app cannot tell whose key
is whose, and says so). Every real-Bitcoin send passes **one deliberate on-screen
confirmation** naming the recipient and amount, and the code refuses any send whose
bytes differ from what that screen showed.

## What you should verify yourself — trust, but verify

1. Download only from the official GitHub release page for this repository.
2. Check the file's hash against `SHA256SUMS` and the GPG signature against the
   repository's `signing-key.asc` (instructions in the release notes).
3. **On the hardware device's own screen**, confirm the recipient address and amount
   before approving — every time. That check is yours; no audit can do it for you.
4. Check where the change came back to, in your own wallet software.

## Who reviewed it, and how far to trust that

This was an **AI-assisted, agentic security review** — five specialist AI agents plus a
referee AI, run by the owner's auditor tooling (ZCode, model GLM-5.3, declared not
verified), against a scope signed off by Bitseeker LLC before the panel ran and
hash-locked before and after. The plan-writing surveyor ran on a different tool (DeepSeek
harness; independence is established as different runs, on declarations). **No human
security firm reviewed this release, and nothing here is a certification, an endorsement,
or a guarantee that the software is free of bugs, malware, or exploitable defects.** An
audit reduces uncertainty; it cannot eliminate it. Coverage limits: no physical devices,
no dispatched workflows, Windows/Linux digest-only. Read the evidence yourself — the
full report is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` in this
repository, the method is the public `ai-color-team-audit-framework`, and the official
download is the GitHub Releases page of `cjtsh/bitcoin-easy-multisig-signer`.

## Distribution policy

This repository is public to read, use, fork, and independently verify (MIT). It is
**not** open to public collaboration: Bitseeker LLC is the sole contributor, release
bytes are built only from `main` by the audited candidate→promote pipeline, and they are
signed under the Bitseeker LLC release key. A fork is someone else's build and is not
covered by this statement.

---

*This statement is a mandatory deliverable of the Color Team audit of v0.6.7
(framework v1.5.0) and must match the technical report in every factual claim. Prepared
2026-10-10 from the public evidence; the grade above is computed, not negotiated.
Trust, but verify.*

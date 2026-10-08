# Audit lock — bitcoin-easy-multisig-signer (cycle 5, target revision 0.6.8)

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` |
| **Plan SHA-256 at the start of the audit** | `4f15a68013ef9e409719f8eb05ecb7f44f4fea2743a127e58c97f4454af4ed19` |
| **Owner sign-off** | `Bitseeker LLC`, 2026-10-08 ("08 OCT 2026") — the plan's section 9, recorded in commit `5d826a1` |
| **Target revision** | commit `bc92f054822008510249e743a60033009dc4995a` on `main` — the 0.6.8 audit-remediation commit. **Deliberately untagged and unpublished**: per the plan §0, the cycle-5 grade comes first, then a `publish=false` candidate, then the owner hardware walkthrough, then publication. Nothing is published for 0.6.8 (live release list verified: latest = v0.6.7) |
| **Candidate run** | 37783584533 — pre-grade `publish=false` candidate at `1a5e9bf` (documentation-only commit after the target), conclusion `success`, publish step took its documented refusal path; recorded by the project, verified by the lead via the Actions API. The plan's intended order was grade-then-candidate; this candidate preceded the grade — a process note for the referee, publishing nothing |
| **CT-97 platform state** | `scripts/check-release-credentials.sh` run live at lock time prints `ok: the release credentials are environment-scoped, main-only, and unreachable from any tag` (exit 0); repository secret list empty; both environments `main`-only, no human gate — claimed by the project, lead-run read-only; deep verification (environment/secret APIs) is Amber's lane |
| **Surveyor** | Kimi Code desktop app (environment variable `__CFBundleIdentifier=com.kimi.code.desktop`) · session `not exposed by the harness` · model `not exposed by the harness` — copied verbatim from the signed plan's section 0 provenance table |
| **Auditor** | ZCode desktop app (`ZCODE_APP_VERSION=3.14.4`) · session `not exposed by the harness` (environment inspected for session/ZCODE variables; only app version and build commit are present) · model `zai-api/GLM-5.3` (declared by the harness system prompt, not verified) |
| **Same session for both?** | cannot be determined — both identifiers read `not exposed by the harness`; the two harnesses differ as declared (Kimi Code vs ZCode), so independence rests on the operator's declaration |
| **Locked at** | 2026-10-08T15:08:06Z (lead auditor, before the first specialist was dispatched; plan hash computed over the signed file at `origin/main` = `5d826a1`, which is the commit that recorded the owner's signature) |
| **Published before the panel ran** | commit `5d826a1` on `origin/main` (public GitHub, fetched 2026-10-08) — the signed plan was public before dispatch; this lock file is written by the lead at dispatch time (untracked until publication) |
| **Plan SHA-256 at the end of the audit** | `4f15a68013ef9e409719f8eb05ecb7f44f4fea2743a127e58c97f4454af4ed19` — re-derived 2026-10-08T16:17:29Z by the referee (⚪ White) from `git show 5d826a1:bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`; **equal to the start hash: the scope never moved.** `origin/main` still resolves to `5d826a1` (`git ls-remote`, same timestamp). The working-tree plan draft differs from the signed blob only in the known hunks (revision name `a98ebc9`→`bc92f05`, blank vs filled sign-off lines, signature-history paragraph) — verified by diff. |

**Prior signature history, for the record:** the owner first signed this plan 2026-10-07
(commit `10df296`) for revision `45076d7`; three code changes moved the frozen revision
(`383623a` → `a98ebc9` → `bc92f05`), each voiding that signature under the plan's own
rule; the audit did not start on 2026-10-08 until the re-signed plan for `bc92f05`
landed at `5d826a1`. The lock hash above is over the re-signed plan.

**Rubric lock.** The grade conditions in force are the owner-adapted rubric in the signed
plan's section 0 (CLEARED / CONDITIONAL / BLOCKED table) plus the rulings of
`PANEL-DESIGN.md` in force at the declared framework tag (v1.3.2). The plan's SHA-256 above
binds them: the rubric does not change after this lock, and any change to the plan file
voids the audit.

**Framework in force.** `colorteam-auditor.md` runbook (SHA-256
`4cbee939d33365733af51e8033f43277bc89c75cdfa7328fcd24e1d215d212f9`, re-fetched for this
cycle and byte-identical to the cycle-4 fetch); `COLOR-TEAM.md` definitions v2.4;
`PANEL-DESIGN.md` (rubric + rulings); `REPORT-TEMPLATE.md`; `SAFETY-REVIEW-TEMPLATE.md`
— framework tag v1.3.2.

**Independence condition (plan §0/§9, binding on every agent):** prior audit reports
(`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history, not inputs — except that the
cycle-4 Color Team report (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`,
published at `3f28ce2`) is available to the **referee** so each CT finding's remedy
(CT-72…CT-104, on top of the CT-01…CT-71 round trip) can be verified, while the
specialist lanes run without it. Per plan §9, the referee also break-and-watches every
tripwire named in `releases/PATCH-0.6.8.md`. A pin that cannot fail is a finding.

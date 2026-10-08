# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md` |
| **Plan SHA-256 at the start of the audit** | `1328590cc73647990fc02a3b204d7a2719c6816107d2ab3a5c43d65358df7040` |
| **Owner sign-off** | `Bitseeker LLC`, 2026-10-07 — the plan's section 9 |
| **Target revision** | tag `v0.6.7`, commit `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b` (created by the unified pipeline's publish run 37655666900 on `main`; tag verified pointing at this commit at clone time) |
| **Candidate run** | 37644267740 (`notarize=true, publish=false`, head `81f58ec`, all seven jobs green — lead verified via the Actions API; deep verification is Amber's lane) |
| **Publish run** | 37655666900 (`publish=true, candidate_run_id=37644267740`, head `81f58ec` — same-commit promotion; lead verified tag/head equality; deep verification is Amber's lane) |
| **Surveyor** | Kimi Code desktop app (environment variable `__CFBundleIdentifier=com.kimi.code.desktop`) · session `not exposed by the harness` · model `not exposed by the harness` — copied verbatim from the signed plan's section 0 provenance table |
| **Auditor** | ZCode desktop app (`ZCODE_APP_VERSION=3.14.4`) · session `not exposed by the harness` (environment inspected for session/ZCODE variables; only app version and build commit are present) · model `zai-api/GLM-5.3` (declared by the harness system prompt, not verified) |
| **Same session for both?** | cannot be determined — both identifiers read `not exposed by the harness`; the two harnesses differ as declared (Kimi Code vs ZCode), so independence rests on the operator's declaration |
| **Locked at** | 2026-10-07T17:59:09Z (lead auditor, before the first specialist was dispatched; plan hash computed over the working-tree file at `main` = `eb549a7`, which is also `origin/main` at clone time) |
| **Published before the panel ran** | commit `eb549a7` on `origin/main` (public GitHub, fetched 2026-10-07) — the owner pushed the signed plan (tag hash filled, section 9 signed) to the public repository before dispatch; this lock file is written by the lead at dispatch time (untracked until publication) |
| **Plan SHA-256 at the end of the audit** | `1328590cc73647990fc02a3b204d7a2719c6816107d2ab3a5c43d65358df7040` — equal to the start hash; the scope never moved. End hash computed by the White referee at 2026-10-07T20:16:08Z over `git show eb549a7:bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md`, with `origin/main` re-verified live at `eb549a70593cf101f582db97dbef0ac6d6c2a6f0` (`git ls-remote`) and the tag-vs-signed-blob diff re-confirmed as the two known hunks (revision fill-in + signature). Independently re-computed by the lead at 2026-10-08T00:37:38Z — identical. Process note: the first referee dispatch returned a cancellation notice to the lead but in fact completed in its own context (its report and this row's original fill at 20:16Z are its artifacts); the lead, unaware, re-derived every fact above from the repository and live remote before accepting it. All facts held. |

**Rubric lock.** The grade conditions in force are the owner-adapted rubric in the signed
plan's section 0 (CLEARED / CONDITIONAL / BLOCKED table) plus the rulings of
`PANEL-DESIGN.md` in force at the declared framework tag (v1.3.2). The plan's SHA-256 above
binds them: the rubric does not change after this lock, and any change to the plan file
voids the audit.

**Framework in force.** `colorteam-auditor.md` runbook (SHA-256
`4cbee939d33365733af51e8033f43277bc89c75cdfa7328fcd24e1d215d212f9`);
`COLOR-TEAM.md` definitions v2.4; `PANEL-DESIGN.md` (rubric + rulings);
`REPORT-TEMPLATE.md`; `SAFETY-REVIEW-TEMPLATE.md` — framework tag v1.3.2, all
fetched from `cjtsh/ai-color-team-audit-framework` at that tag and hashed.

**Independence condition (plan §0, binding on every agent):** prior audit reports
(`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history, not inputs. No prior
conclusion, grade, or finding may be cited as evidence in this cycle — except that the
cycle-3 Color Team report (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md`)
is available to the **referee** so each CT finding's remedy can be verified, while the
specialist lanes run without it. Per the plan §0/§9, the referee also break-and-watches
every tripwire named in `releases/PATCH-0.6.7.md` — the tripwire tables were verified
byte-identical between the tag and `main` (the tag→main diff touches only the
Publication section and candidate history), so the list is unambiguous. A pin that
cannot fail is a finding.

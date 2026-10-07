# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.6.md` |
| **Plan SHA-256 at the start of the audit** | `c8b8531bf36ad2360239bd5c8ab22b37b5538f35d8da5718991de5fc0ab3f37f` |
| **Owner sign-off** | `Bitseeker LLC`, 2026-10-06 ("6OCT2026") — the plan's section 9 |
| **Target revision** | tag `v0.6.6`, commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` (created by the unified pipeline's publish run on `main`) |
| **Publish run** | to be recorded from the release/Actions API by the Amber lane (lead baseline records the receipts it verifies) |
| **Candidate run** | to be recorded from the release/Actions API by the Amber lane |
| **Surveyor** | Kimi Code desktop app (environment variable `__CFBundleIdentifier=com.kimi.code.desktop`) · session `not exposed by the harness` · model `not exposed by the harness` — copied verbatim from the signed plan's section 0 provenance table |
| **Auditor** | ZCode desktop app (`ZCODE_APP_VERSION=3.14.4`) · session `not exposed by the harness` (environment inspected for session/ZCODE variables; only app version and build commit are present) · model `zai-api/GLM-5.3` (declared by the harness system prompt, not verified) |
| **Same session for both?** | cannot be determined — both identifiers read `not exposed by the harness`; the two harnesses differ as declared (Kimi Code vs ZCode), so independence rests on the operator's declaration |
| **Locked at** | 2026-10-06T15:40:42Z (lead auditor, before the first specialist was dispatched; plan hash computed from the working tree at `main` = `491c226`) |
| **Published before the panel ran** | commit `491c226` on `main` (2026-10-06) — the owner pinned the signed plan to the public repository before dispatching the panel; this lock file is written by the lead at dispatch time (untracked until publication) |
| **Plan SHA-256 at the end of the audit** | `c8b8531bf36ad2360239bd5c8ab22b37b5538f35d8da5718991de5fc0ab3f37f` — equal to the start hash; scope never moved (re-hashed at gate time, 2026-10-07) |

**Rubric lock.** The grade conditions in force are the owner-adapted rubric in the signed
plan's section 0 (CLEARED / CONDITIONAL / BLOCKED table) plus the rulings of
`PANEL-DESIGN.md` in force at the declared framework tag (v1.3.2). The plan's SHA-256 above
binds them: the rubric does not change after this lock, and any change to the plan file
voids the audit.

**Framework in force.** `colorteam-auditor.md` runbook (SHA-256
`4cbee939d33365733af51e8033f43277bc89c75cdfa7328fcd24e1d215d212f9`, byte-identical to the
cycle-2 fetch); `COLOR-TEAM.md` definitions; `PANEL-DESIGN.md` (rubric + rulings);
`REPORT-TEMPLATE.md`; `SAFETY-REVIEW-TEMPLATE.md` — framework tag v1.3.2.

**Independence condition (plan §0, binding on every agent):** prior audit reports
(`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history, not inputs. No prior
conclusion, grade, or finding may be cited as evidence in this cycle — except that the
cycle-2 Color Team report (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md`)
is available to the **referee** so each CT finding's remedy can be verified, while the
specialist lanes run without it. Per the plan §0/§9, the referee also break-and-watches
every tripwire named in `releases/PATCH-0.6.6.md` (CT-13/14/29/30/33/34/46): a pin that
cannot fail is a finding.

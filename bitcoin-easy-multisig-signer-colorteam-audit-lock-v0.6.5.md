# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.5.md` |
| **Plan SHA-256 at the start of the audit** | `ecc1b42ea0ff581cf81fcae2d835052083753d7f5ae516a7c924321effe80c69` |
| **Owner sign-off** | `Bitseeker LLC`, 2026-10-06 ("6OCT2026") — the plan's section 9 |
| **Target revision** | tag `v0.6.5`, commit `29c8002b154a4e968308376b1e514a965ffa92d8` (published by the unified pipeline's publish run; tag created on that commit) |
| **Publish run** | [37411746360](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37411746360) — `notarize=true, publish=true`, candidate run 37409812638, commit `29c8002` |
| **Candidate run** | [37409812638](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37409812638) — `notarize=true, publish=false`, same commit |
| **Surveyor** | *(filled by the surveyor at lock time)* |
| **Auditor** | *(filled by the lead harness at lock time)* |
| **Same session for both?** | *(filled at lock time)* |
| **Locked at** | *(set when the panel starts; this file is the binding record)* |
| **Published before the panel ran** | *(witnessed at lock time)* |
| **Plan SHA-256 at the end of the audit** | *(re-hashed by the referee at gate time)* |

**Rubric lock.** The grade conditions in force are the owner-adapted rubric in the signed
plan's section 0 (CLEARED / CONDITIONAL / BLOCKED table) plus the rulings of
`PANEL-DESIGN.md` in force at the declared framework tag. The plan's SHA-256 above
binds them: the rubric does not change after this lock, and any change to the plan file
voids the audit.

**Framework in force.** `colorteam-auditor.md` runbook; `COLOR-TEAM.md` definitions;
`PANEL-DESIGN.md` (rubric + rulings); `REPORT-TEMPLATE.md`; `SAFETY-REVIEW-TEMPLATE.md`
— from the framework tag the surveyor declares in the plan's section 0.

**Independence condition (plan §0, binding on every agent):** prior audit reports
(`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history, not inputs. No prior
conclusion, grade, or finding may be cited as evidence in this cycle — except that the
cycle-1 Color Team report (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md`)
is available to the **referee** so each CT finding's remedy can be verified, while the
specialist lanes run without it.

# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.4.md` |
| **Plan SHA-256 at the start of the audit** | `ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8` |
| **Owner sign-off** | Bitseeker LLC, 27 Oct 2026 — the plan's last section |
| **Target revision** | tag `v0.7.4` → commit `9d4d7bb471c80512cac7b7dc6c014855393cac4f` |
| **Surveyor** | DeepSeek Harness (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` — copied verbatim from the plan's §0 agent provenance |
| **Auditor** | declared by the operator at dispatch time; the previous cycle's panel ran on ZCode 3.16.3 · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)`. If the operator dispatches a different auditor or model, that declaration supersedes this row and is recorded in the panel's report. |
| **Same session for both?** | no — the surveyor's session identifier is present and names a DeepSeek Harness session; the auditor runs outside this repository's tooling and its session identifier, if any, is not available to the surveyor. The identifiers cannot be identical: different runs. This establishes different runs, not different models — independence rests on the operator's declaration that the surveyor seat ran on the DeepSeek Harness. |
| **Locked at** | `2026-10-27T12:34:45Z` |
| **Published before the panel ran** | yes — this file is committed on `main` before any specialist is dispatched; the operator confirms the push and then dispatches the panel |
| **Plan SHA-256 at the end of the audit** | `ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8` — written at lock time, before the panel runs; the referee re-hashes the file at the end of the audit and enters the observed value here. Unequal to the start hash means the audit is void: **DO NOT PUBLISH** |

Cycle: `v0.7.4` — a follow-up (conversion re-check) in the `v0.6.8` lineage. Scope
continuity was verified at lock time against the immediately prior signed plan
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.3.md`, SHA-256
`83534f9ee9909fcdbb6f09505d1dc26b883aae2b1dd6a6a76b1b557a84dfa64c`) and the lineage's original plan (`…audit-plan-v0.6.8.md`, SHA-256
`20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1`): the declared assets, unforgivable acts, adapted rubric, the
31 in-scope threat rows, the out-of-scope list and the not-examined list are carried
forward unchanged; the only differences are the declared revision-pointer updates and
the cycle-lineage fields. The plan names the immediately prior report and accounts for
every finding ID `CT-01`…`CT-44`.

The referee re-hashes the plan file at the end and compares. Equal means the scope never
moved. Unequal means the audit is void: **DO NOT PUBLISH**.

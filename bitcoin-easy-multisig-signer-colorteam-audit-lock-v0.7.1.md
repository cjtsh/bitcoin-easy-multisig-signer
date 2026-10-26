# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.1.md` |
| **Plan SHA-256 at the start of the audit** | `6137530d0117fa31a076e0738cc9e82ecbc73825ba688785b64951f0d711d88c` |
| **Owner sign-off** | Bitseeker LLC, 26 Oct 2026 — the plan's last section |
| **Target revision** | tag `v0.7.1` → commit `8923ca0273380a9cb1ea7e7e964c6332dda5a777` |
| **Surveyor** | DeepSeek Harness (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` — copied verbatim from the plan's §0 agent provenance |
| **Auditor** | ZCode 3.16.3 · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` |
| **Same session for both?** | no — the surveyor's session identifier is present and names a DeepSeek Harness session; the auditor runs in ZCode, which exposes no session identifier. The identifiers cannot be identical: different runs. This establishes different runs, not different models — independence rests on the operator's declaration that the surveyor seat ran on the DeepSeek Harness. |
| **Locked at** | `2026-10-26T18:43:52Z` |
| **Published before the panel ran** | this file, committed to `main` before the first specialist was dispatched |
| **Plan SHA-256 at the end of the audit** | _(to be filled by the referee)_ |

Cycle: `v0.7.1` — a follow-up (conversion re-check) in the `v0.6.8` lineage. Scope
continuity was verified at lock time against the immediately prior signed plan
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.0.md`, SHA-256
`0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5`) and the lineage's
original plan (`…audit-plan-v0.6.8.md`, SHA-256
`20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1`): the declared
assets, unforgivable acts, adapted rubric, the 31 in-scope threat rows, the
out-of-scope list and the not-examined list are carried forward unchanged; the only
differences are the declared revision-pointer updates and the cycle-lineage fields.
The plan names the immediately prior report and accounts for every finding ID
`CT-01`…`CT-21`.

The referee re-hashes the plan file at the end and compares. Equal hashes mean the
scope never moved. Unequal means the audit is void: **DO NOT PUBLISH**.

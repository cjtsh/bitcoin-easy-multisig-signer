# Audit lock — bitcoin-easy-multisig-signer

Cycle **`v0.6.9`** — a follow-up cycle in the `v0.6.8` lineage (conversion re-check,
delta-scoped to the prior cycle's four conversion-gating Low findings, per the signed
plan's section 0).

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.9.md` (on `main`, commit `bd8464f283b0b0c3715cf028abe7a6fa61d69c26`) |
| **Plan SHA-256 at the start of the audit** | `133ce23afe0bca80d884bcff7b9cfa428d2f8bbb965a7d2ff84182aa0be8a8c3` |
| **Owner sign-off** | `Bitseeker LLC, 2026-10-11` — section 9, the plan's last section (corrections: "None") |
| **Target revision** | Release **`v0.6.9`** — tag `e90e5b93ece284f990ca2b75be1e798baa3efc9c` (`e90e5b9`), committed 2026-10-11T11:12:08-04:00 — together with the ten release artifacts published 2026-10-11T15:33:09Z. Prior revision: `v0.6.8` = `0d4e01f60c7695d720099f9d8e9e23b38da63102`. Tag resolution re-confirmed at lock time via `gh api repos/cjtsh/bitcoin-easy-multisig-signer/git/refs/tags/v0.6.9` → `e90e5b9…`, and the prior tag `v0.6.8` still resolves to `0d4e01f…`; `main` at lock time is `bd8464f283b0b0c3715cf028abe7a6fa61d69c26`. Scope continuity with the original signed plan verified mechanically: declared-assets table, unforgivable acts, and all threat-row headings are byte-identical; the rubric is identical modulo the revision pointer; every prior finding ID (`CT-01`…`CT-12`) is enumerated for re-check. |
| **Surveyor** | `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh) · session session-64472385-85c1-422e-bc6c-f889c8d8c3d5 · model not exposed by the harness` (copied verbatim from the plan's section 0 "Agent provenance" table; declared by operator handle `cjtsh`, Bitseeker LLC; survey date 2026-10-11) |
| **Auditor** | `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop) · session 1d323ae6-8fdf-4cba-993f-5bb46154a778 (no session environment variable exists in this harness; the identifier is the harness's own session directory name as exposed in this session's tool-output paths) · model not exposed by the harness` |
| **Same session for both?** | `no` — different harnesses (DeepSeek DSH vs Kimi Code) and different session identifiers (`session-64472385…` vs `1d323ae6…`). Different runs are established by the identifiers; different models rest on the two harnesses' declarations, not on independent verification. |
| **Locked at** | `2026-10-11T16:05:00Z` |
| **Published before the panel ran** | this lock file, committed to public `main` immediately after writing (commit hash recorded in the cycle's report and index row) |
| **Plan SHA-256 at the end of the audit** | `(filled by the White referee at re-check)` |

The plan's rubric (section 0, "The rubric as adapted to this target (the owner's
statements, §3)") is the locked rubric for this cycle — carried forward unchanged from
the signed `v0.6.8` plan with only the revision pointer moved. ✅ **CLEARED** requires
the panel to find no path, in in-scope code at `e90e5b9`, to: (a) sign or broadcast
transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet
without both the per-transaction final-screen consent and the fail-closed backend
opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts;
(d) publish release bytes other than the verified candidate's; (e) expose a credential
value — with the `AGENTS.md` invariants holding as stated, with the test evidence the
repo claims, and every §5 threat row resolved HOLDS/BROKEN/UNPROVEN with evidence (an
UNPROVEN row blocks CLEARED). For this conversion re-check, CLEARED additionally
requires every prior-cycle finding (`CT-01`…`CT-12`) verified fixed or closed by dated
owner acceptance — the conversion criteria verified **by execution, not acceptance** —
and no new Critical/High introduced by the delta. ⚠️ **CONDITIONAL** and ⛔ **BLOCKED**
as written in the plan, including any demonstrated path to an unforgivable act, any
handling of seeds/PINs/private keys, any credential value exposed, a pipeline able to
publish unverified/unsigned/unnotarized bytes, or any scope/lock mismatch at re-check.
The grade is the floor of the panel, never the average.

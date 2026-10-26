# Audit lock — bitcoin-easy-multisig-signer

Cycle **`v0.7.0`** — a follow-up cycle in the `v0.6.8` lineage (conversion re-check,
delta-scoped to the prior cycle's two conversion-gating Low findings CT-13/CT-14, with
CT-01…CT-12 carried regression re-checks and CT-15…CT-18 re-checked, per the signed
plan's section 0).

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.0.md` (on `main`, commit `e2daf430e877b556554885fe100b2a7fb9424eac`) |
| **Plan SHA-256 at the start of the audit** | `0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5` |
| **Owner sign-off** | `Bitseeker LLC, 16 Oct 2026` — section 9, the plan's last section (corrections: "None"). Sign-off commit history: `8273891` filled the signature lines, `e2daf43` added the corrections bullet; the locked file is the final state at `e2daf43`. |
| **Target revision** | Release **`v0.7.0`** — tag `4fe8f2955e29cae6838e2ba0b8029c9abae9fdeb` (`4fe8f29`), committed 2026-10-16 — together with the ten release artifacts published 2026-10-16T06:15:36Z. Prior revision: `v0.6.9` = `e90e5b93ece284f990ca2b75be1e798baa3efc9c`. Tag resolution re-confirmed at lock time via `gh api repos/cjtsh/bitcoin-easy-multisig-signer/git/refs/tags/v0.7.0` → `4fe8f29…`; `main` at lock time is `e2daf430e877b556554885fe100b2a7fb9424eac`. Scope continuity with the original signed plan verified mechanically: declared-assets table, unforgivable acts, and all threat-row headings byte-identical to the v0.6.8 baseline; the rubric identical modulo the revision pointer; every prior finding ID (`CT-01`…`CT-18`) enumerated for re-check. |
| **Surveyor** | `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh) · session session-64472385-85c1-422e-bc6c-f889c8d8c3d5 · model not exposed by the harness` (copied verbatim from the plan's section 0 "Agent provenance" table; declared by operator handle `cjtsh`, Bitseeker LLC; survey date 2026-10-16) |
| **Auditor** | `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop) · session 1d323ae6-8fdf-4cba-993f-5bb46154a778 (no session environment variable exists in this harness; the identifier is the harness's own session directory name as exposed in this session's tool-output paths) · model not exposed by the harness` |
| **Same session for both?** | `no` — different harnesses (DeepSeek DSH vs Kimi Code) and different session identifiers (`session-64472385…` vs `1d323ae6…`). Different runs are established by the identifiers; different models rest on the two harnesses' declarations, not on independent verification. |
| **Locked at** | `2026-10-16T14:20:00Z` |
| **Published before the panel ran** | this lock file, committed to public `main` immediately after writing (commit hash recorded in the cycle's report and index row) |
| **Plan SHA-256 at the end of the audit** | `0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5` — re-hashed by the White referee 2026-10-25 (UTC 2026-10-26T01:23Z at write); **equal to the start hash: the scope never moved**. Tag re-confirmed `v0.7.0` → `4fe8f29`, `main` still `a487049` (no movement under the audit beyond the audit's own artifacts). |

The plan's rubric (section 0, "The rubric as adapted to this target") is the locked
rubric for this cycle — carried forward unchanged from the signed `v0.6.8` baseline with
only the revision pointer moved. ✅ **CLEARED** requires the panel to find no path, in
in-scope code at `4fe8f29`, to: (a) sign or broadcast transaction bytes that differ from
what the operator reviewed; (b) broadcast on mainnet without both the per-transaction
final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying
material to diagnostics, logs, or artifacts; (d) publish release bytes other than the
verified candidate's; (e) expose a credential value — with the `AGENTS.md` invariants
holding as stated, with the test evidence the repo claims, and every §5 threat row
resolved HOLDS/BROKEN/UNPROVEN with evidence (an UNPROVEN row blocks CLEARED). For this
conversion re-check, CLEARED additionally requires every prior-cycle finding
(`CT-01`…`CT-18`) verified fixed or closed by dated owner acceptance — the conversion
criteria verified **by execution, not acceptance** — and no new Critical/High introduced
by the delta. ⚠️ **CONDITIONAL** and ⛔ **BLOCKED** as written in the plan, including any
demonstrated path to an unforgivable act, any handling of seeds/PINs/private keys, any
credential value exposed, a pipeline able to publish unverified/unsigned/unnotarized
bytes, or any scope/lock mismatch at re-check. The grade is the floor of the panel,
never the average.

**Recorded incident for the panel's verification (plan §0):** promote attempt
`38855337226` failed in the DMG job on an Apple stapler/CloudKit network error
(exit 68) *after* notarization was accepted; it published nothing. The publishing
promote run is `38857329074` (candidate `38854414566`). The panel verifies this account
independently under T-23/T-24.

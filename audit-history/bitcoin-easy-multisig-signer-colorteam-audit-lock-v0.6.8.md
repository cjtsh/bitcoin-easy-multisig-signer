# Audit lock — bitcoin-easy-multisig-signer

Cycle **`v0.6.8`** — the first cycle of this plan lineage (fresh baseline; the plan's
section 0, "Cycle lineage", declares no carried-forward plan and no prior ledger as an
input).

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` (on `main`, commit `488a51c272e0b321cac66f6cc633812611852ab1`) |
| **Plan SHA-256 at the start of the audit** | `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` |
| **Owner sign-off** | `Signed by maintainer, Bitseeker LLC, 2026-10-11` — section 9, the plan's last section (corrections: "None") |
| **Target revision** | Release **`v0.6.8`** — tag `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`), committed 2026-10-10T17:13:08-04:00 — together with the ten release artifacts published 2026-10-10T21:31:47Z. Tag resolution re-confirmed at lock time via `gh api repos/cjtsh/bitcoin-easy-multisig-signer/git/refs/tags/v0.6.8` → `0d4e01f…`; `main` at lock time is `488a51c272e0b321cac66f6cc633812611852ab1`. |
| **Surveyor** | `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh) · session session-9dc3f632-29dc-4ce5-adc8-4a79a72b6a98 (read verbatim from the environment variable DSH_SESSION_ID) · model not exposed by the harness` (copied verbatim from the plan's section 0 "Agent provenance" table; declared by operator handle `cjtsh`, Bitseeker LLC; survey date 2026-10-11) |
| **Auditor** | `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop) · session 1d323ae6-8fdf-4cba-993f-5bb46154a778 (no session environment variable exists in this harness — the same absence the cycle-v0.6.7 surveyor recorded; the identifier is the harness's own session directory name as exposed in this session's tool-output paths) · model not exposed by the harness` |
| **Same session for both?** | `no` — different harnesses (DeepSeek DSH vs Kimi Code) and different session identifiers (`session-9dc3f632…` vs `1d323ae6…`). Different runs are established by the identifiers; different models rest on the two harnesses' declarations, not on independent verification. |
| **Locked at** | `2026-10-11T05:30:00Z` |
| **Published before the panel ran** | this lock file, committed to public `main` immediately after writing (commit hash recorded in the cycle's report and index row) |
| **Plan SHA-256 at the end of the audit** | `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — re-hashed by the White referee on 2026-10-11 (`shasum -a 256` over the plan file on `main` at `f4c7863`): **equal** to the start hash; the scope never moved. |

The plan's rubric (section 0, "The rubric as adapted to this target (the owner's
statements, §3)") is the locked rubric for this cycle. ✅ **CLEARED** requires the panel
to find no path, in in-scope code at `0d4e01f`, to: (a) sign or broadcast transaction
bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both
the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write
wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release
bytes other than the verified candidate's; (e) expose a credential value — with the
`AGENTS.md` invariants holding as stated, with the test evidence the repo claims, and
every §5 threat row resolved HOLDS/BROKEN/UNPROVEN with evidence (an UNPROVEN row blocks
CLEARED). ⚠️ **CONDITIONAL** and ⛔ **BLOCKED** as written in the plan, including:
any demonstrated path to an unforgivable act, any handling of seeds/PINs/private keys,
any credential value exposed, a pipeline able to publish unverified/unsigned/
unnotarized bytes, or any scope/lock mismatch at re-check. The grade is the floor of the
panel, never the average.

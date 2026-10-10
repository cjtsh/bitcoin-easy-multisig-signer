# Audit lock — bitcoin-easy-multisig-signer

Cycle **`v0.6.7`** (the second plan signed for this cycle; the plan carrying it is named
for the surveyed commit — see the plan's section 1, "Why this file is named for the
commit").

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md` |
| **Plan SHA-256 at the start of the audit** | `ab5c7dbb4b89ed4f485d1e6851ddab20a5950e57bd4aae5d852667d22c5fbed8` |
| **Owner sign-off** | `Bitseeker LLC, 2026-10-10` — section 9, the plan's last section (revision 8, "final — frozen for the incoming review") |
| **Target revision** | Release **`v0.6.7`** — tag `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b` (`81f58ec`) — together with the release artifacts published 2026-10-07T17:10:37Z. Reconnaissance revision `d525f31b600d5aedd2f7a219ec848df540707ffc` (`d525f31`); the two trees differ in six Markdown files and no executable file (verified in the auditor's fresh clone: `git diff --name-only 81f58ec d525f31` → `CURRENT-STATUS.md`, `PHASE-HANDOFF.md`, `RELEASE-HISTORY.md`, `ROADMAP.md`, `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md`, `releases/PATCH-0.6.7.md`). |
| **Surveyor** | `DeepSeek Harness desktop app (__CFBundleIdentifier=com.deepseek.dsh) · session session-5d5422fc-382b-428d-93f1-71eb00cd083b · model not exposed by the harness` (copied verbatim from the plan's section 0 provenance table) |
| **Auditor** | `ZCode desktop app (dev.zcode.app, v3.14.4) · session not exposed by the harness · model zai-api/GLM-5.3 (declared by the harness)` |
| **Same session for both?** | `no` — different harnesses (DeepSeek DSH vs ZCode) and different recorded session identifiers; the surveyor's session id is exposed and differs from this harness's, which exposes none. Different sessions are established; different models rest on the two harnesses' declarations (DeepSeek harness vs Z.ai GLM), not on independent verification. |
| **Locked at** | `2026-10-10T14:21:23Z` |
| **Published before the panel ran** | this lock file, committed to public `main` immediately after writing (commit hash recorded in the cycle's report and index row) |
| **Plan SHA-256 at the end of the audit** | `ab5c7dbb4b89ed4f485d1e6851ddab20a5950e57bd4aae5d852667d22c5fbed8` (re-hashed by the White referee from `main:bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`, 2026-10-10 — **equal to the start hash: the scope never moved; the audit is not void**) |

The plan's rubric (section 0, "The rubric as adapted to this target") is the locked
rubric for this cycle: CLEARED requires no path in in-scope code at the target revision
to (a) sign/broadcast unreviewed transaction bytes, (b) mainnet broadcast without both
consent gates, (c) write wallet-identifying material to diagnostics/logs/artifacts,
(d) publish bytes other than the verified candidate's, (e) expose a credential value —
plus, new this cycle, no `releases/PATCH-0.6.7.md` closing-evidence pin that cannot
fail and no defeatable claimed control. CONDITIONAL and BLOCKED as written in the plan.
The grade is the floor of the panel, never the average.

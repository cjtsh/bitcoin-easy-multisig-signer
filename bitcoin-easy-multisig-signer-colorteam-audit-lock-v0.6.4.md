# Audit lock — bitcoin-easy-multisig-signer

| | |
|---|---|
| **Plan file** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.4.md` |
| **Plan SHA-256 at the start of the audit** | `250632959641571e5c769f2590132b349e57b1ce1dc27a6e97b7962b90a47aaf` |
| **Owner sign-off** | `Bitseeker LLC`, 2026-10-05 ("5OCT2026") — the plan's section 9 |
| **Target revision** | tag `v0.6.4`, commit `35cdedb150cef6d047c39537324faf1321be3c8d` (verified: fresh clone checked out at the tag resolves to exactly this commit; working tree clean) |
| **Surveyor** | Kimi Code desktop app (`__CFBundleIdentifier=com.kimi.code.desktop`) · session `not exposed by the harness` · model `not exposed by the harness` — copied verbatim from the plan's section 0 provenance table |
| **Auditor** | ZCode desktop app (`ZCODE_APP_VERSION=3.14.4`) · session `not exposed by the harness` (environment scanned: no session-identifier variable present) · model `zai-api/GLM-5.3`, declared by the harness system prompt |
| **Same session for both?** | cannot be determined — both session identifiers read "not exposed by the harness"; the two harnesses differ as declared (Kimi Code vs ZCode), so independence rests on the operator's declaration |
| **Locked at** | 2026-10-05T17:55:34Z |
| **Published before the panel ran** | not published, order unwitnessed |
| **Plan SHA-256 at the end of the audit** | `250632959641571e5c769f2590132b349e57b1ce1dc27a6e97b7962b90a47aaf` — re-hashed by the referee (White) at gate time, 2026-10-05: **equal to the start hash; the scope never moved.** Verified with `shasum -a 256` immediately before this append. |

**Rubric lock.** The grade conditions in force are the owner-adapted rubric in the signed
plan's section 0 (CLEARED / CONDITIONAL / BLOCKED table) plus the eight rulings of
`PANEL-DESIGN.md` v1.3.2. The plan's SHA-256 above binds them: the rubric does not
change after this lock, and any change to the plan file voids the audit.

**Framework in force.** `colorteam-auditor.md` v1.3.2 runbook; `COLOR-TEAM.md`
definitions v2.4; `PANEL-DESIGN.md` (rubric + rulings); `REPORT-TEMPLATE.md`;
`SAFETY-REVIEW-TEMPLATE.md` — all from framework tag `v1.3.2`.

**Independence condition (plan §0, binding on every agent):** prior audit reports
(`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history, not inputs. No prior
conclusion, grade, or finding may be cited as evidence in this cycle.

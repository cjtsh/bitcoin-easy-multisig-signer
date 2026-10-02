# Z.ai Security Audit — v0.6.4 — The Conversion Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.4`, commit `35cdedb150cef6d047c39537324faf1321be3c8d`, published 2 October 2026 |
| **Auditor** | Z.ai (GLM-5.3, via ZCode) — Color Team conversion re-check: three specialists (Red, Blue, Amber) dispatched simultaneously, then the White referee |
| **Prior grade** | v0.6.3: 🟡 Yellow — one Medium finding (BESA-33: the release was published through the manual path, so the project's own automated gates never executed). The referee defined the conversion: one future release published through the automated gates, then re-run the panel |
| **This grade** | **🟢 GREEN** — the conversion is demonstrated. This release was published *by the gates themselves* |
| **Verification** | All artifact hashes recomputed and matching; test suite re-run at the audited commit (261 tests, up from 253, zero deleted); the publication evidence re-derived from run logs, timestamps, and the release API by the referee personally |

## The grade: Green — the conversion, demonstrated

The single finding that held the last grade at Yellow was that v0.6.3's publication
bypassed the project's own machine-enforced release gates. The locked conversion
criterion was execution, not intention: one release actually published through the
automated path, end to end.

v0.6.4 is that release, and the referee re-derived every step from primary evidence:

- A **non-publishing candidate run** (run [37008418851](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37008418851)) built and notarized the release from commit `35cdedb` and produced its checksums.
- Eight minutes later, a **publishing run** (run [37009396873](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37009396873), same commit) machine-verified the candidate — same workflow, same commit, manifest checked line by line, artifact digests re-verified — then executed **"Verify downloaded release bytes"** (checksums: all OK) and the **tag guard** *before* creating the release at 13:01:38 UTC. The release author is `github-actions[bot]`, not a human.
- The published files are **byte-identical to the tested candidate's checksums**, verified independently by two panel agents from three directions (candidate artifact, published asset, local download).
- The gates are demonstrably real: two earlier rehearsal attempts failed — fail-closed, creating nothing — before the clean pair.

The optional fallback item from the remediation order (a dated owner-acceptance note
for manual publication) was superseded by something stronger: the project's release
process now **prohibits manual publication outright** ("if the workflow is unavailable,
wait to publish"), which moots the acceptance it was meant to provide. The referee
records the residual honestly (BESA-45): a policy on paper cannot machine-prevent a
credentialed owner — which is precisely why the grade rests on the demonstrated
execution above, not on the policy.

## The panel

**🔴 Red — no breach found on the delta.** The change surface since v0.6.3 touches
no application code (the money path is byte-identical — provable by blob hash across
v0.6.2, v0.6.3, and v0.6.4). Red attacked the new candidate-to-publish linkage —
wrong-commit promotion, byte substitution, cross-repo candidates, unsigned
publication, tag races — and every path failed closed. Two informational notes.

**🔵 Blue — defenses hold.** Every work-order item from the remediation is met and
mutation-verified: Blue surgically reverted each new guard in a scratch clone and
confirmed the matching test goes red — the three refusal-branch pins, the
returned-transaction-ID pin, and the SBOM hash all genuinely bite. Suite grew
253 → 261 with nothing deleted.

**🟡 Amber — chain holds.** BESA-33 closed by the machine-path criterion with primary
evidence (timestamps, step logs, SHA equalities); record-keeping compliant; the SBOM
now carries the vendored cryptography wheel's hash. One recurring quirk recorded for
future auditors: GitHub's release "created_at" field mirrors the commit date, not the
publication instant — the asset timestamps and job logs carry the truth.

**⚪ White — the referee.** Re-derived all load-bearing claims personally, ran its own
mutation test, corrected three citation drifts, merged the findings into the final
ledger (BESA-45…53: two Low, seven Info), applied the locked Green rubric clause by
clause, and ruled: **Green — earned, not given.** Publication approved.

## Honest ledger — what remains open

Green does not mean "nothing left." Carried forward, explicitly **not** claimed fixed:
the physical device-swap window bounded to denial-of-service (BESA-26), the hardware
helper's entitlement and extraction surface (BESA-29), the vendored USB binary's
repo-circular trust anchors (BESA-30), the tag-check timing window (BESA-32), plus
this cycle's new Lows — the unsigned owner sign-off on the manual-publication
prohibition (BESA-45) and the source-archive allowlist note (BESA-46) — and the
informational entries BESA-47…53. None blocks under the locked rubric; all stay on
the books for the next cycle.

## What this audit did not do

No panel agent attached hardware (the owner's prior physical acceptance covers
unchanged app behavior; this release changed none). The automated publish path has
now been demonstrated in execution exactly once — one clean pair of runs. The
publishing run's own rebuilt artifacts were discarded without bit-comparison to the
candidate (published bytes are provably the candidate's; notarized builds are not
reproducible). The vendored cryptography patch remains unmerged upstream; the
re-audit obligation at every future library bump stands. "No finding" means "none
found within this coverage," not "none exist."

---

*Audit performed 2 October 2026 by Z.ai on the public repository and published
artifacts only, under grade rules locked before each cycle began and applied as
written. The progression Yellow → remediation → Green is documented across this
report and its two predecessors, each carrying the grade its evidence supported on
the day. No wallet material, addresses, or transaction identifiers appear in this
report. An audit is not a certification of safety; it is dated evidence about one
revision, and its coverage limits are stated above.*

# ZCode Color Team Audit — Bitcoin Easy Signer v0.7.5 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.5`, commit `b254fe6f6fc724f25e0c40658bd430c4bffaedcb`, release published 2026-10-27T16:54:31Z (ten assets, immutable releases live) |
| **Assets declared** | (1) The Bitcoin in the operator's multisig wallet — no transaction signed or broadcast that the operator did not review and approve; (2) signing and CI credentials and the release workflow; (3) the reviewed-transaction integrity chain; (4) release artifact integrity — only the verified candidate's exact bytes publish; (5) wallet privacy. No asset is optional; the ranking orders severity, not attention |
| **Auditor** | ZCode — a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber — one fresh context each, dispatched as one wave) plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness` (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-10672503-1cfb-435b-90a5-0cc26a3fad0c` · model **`deepseek-flash`, declared by the harness** (a lineage first — prior cycles' harnesses exposed no model name; declared, never independently verified) — declared by operator handle `cjtsh`, Bitseeker LLC |
| **Auditor identity** | Harness `ZCode 3.16.3` · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` — the same auditor seat as the prior cycles, as the lock's auditor row anticipated |
| **Independence** | Surveyor and auditor ran in different sessions: **yes — different runs**. **Different models is NOT established** — the surveyor's model name is a harness declaration and the auditor's is self-description; independence beyond different runs rests on the operator's declaration |
| **Cycle** | `v0.7.5` — a **conversion re-check** of the `v0.6.8` lineage (delta-scoped wave; carried domains carried by verified blob identity, the delta's two production files re-established in full) |
| **Prior audit** | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.4.md`, SHA-256 `6bf67462f2953bba1d56f462d7ed6047c3112b2af6bf7e4b0829b16f6a018a65`, grade **⚠️ CONDITIONAL** (held by CT-47 and CT-49) |
| **Original scope plan** | `audit-history/bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — scope carried forward **unchanged**; lead- and referee-verified against the prior plan (`…plan-v0.7.4.md`, SHA-256 `ae9f5574…8e8`): §2–§3 byte-identical, 31 threat-row titles identical, §5 differs in citation refreshes and T-10's row extended for the abort re-raise (the conversion-target row, strengthened) |
| **Verification** | Independently re-derived: ten release assets hash-checked against `SHA256SUMS`; `SHA256SUMS.asc` = Good signature `Bitseeker LLC <release@bitseeker.llc>` (RSA `ACCC2F1C…D6D7`); three Sigstore attestations bind the digests to `b254fe6`; DMG app codesign-strict OK, spctl accepted, TeamID `B8G5L7M8TB`, staple valid; suite re-run at the audited revision (**744 tests, OK** on Python 3.12.15, hash-locked deps; CI pins 3.12.10 — recorded; 11/11 page-script suites); the run ledger re-read live (three runs, four attempts — a cancelled run that published nothing and had **zero artifacts**, a staple-flaked promote attempt that published nothing, then the publishing attempt); the referee personally re-broke the two conversion pins (the settings-refusal conversion and the Request-position pin), re-ran the abort-propagation drive and the RED-1 demonstration, and re-derived the grade from the rubric |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.5.md`, SHA-256 `13107186d9a12ff03bf1cd4efe18521691d96554aca4118ed3ceb8cee3dd2e7b` before the first agent ran and `13107186d9a12ff03bf1cd4efe18521691d96554aca4118ed3ceb8cee3dd2e7b` at the end — **equal: the scope never moved**. Owner-signed **Bitseeker LLC, 27 Oct 2026**. The lock was **pre-published by the operator's side** (commit `4a60be5`; locked-at `2026-10-27T16:58:20Z`, before this panel was dispatched); its Surveyor row matches the plan's §0 verbatim (the v0.7.4 cycle's provenance defect did not recur); the referee entered the observed end hash |

## The grade: ✅ CLEARED — no path to any prohibited outcome was found; every defense is present, effective, fail-closed, and held by an alarm that was personally watched ringing

**This grade is computed, and here is the arithmetic in full.** The five specialists
returned: Red **NO BREACH DEMONSTRATED** (per asset: all five held), Blue **DEFENSES
HOLD**, Orange **LOGIC PROVEN**, Copper **EDGE TRUST HOLDS** (no findings), Amber
**CHAIN HOLDS** (no findings). No lane proved a failure state, so the BLOCKED
mechanism does not fire. The CLEARED clause list was then worked item by item, with
the referee testing the one genuinely contestable reading in both directions and
recording the reasoning (a reviewer reading the tension rule the other way would
land CONDITIONAL on exactly one Info finding — CT-56 below — and the written
reasoning for that step is in the referee's section so the ruling is auditable):

1. **Zero open Critical/High** — met: the only new findings are one Low (CT-53,
   unreachable through the product) and five Info (CT-54…CT-57), none calibrated
   higher by the referee.
2. **Every prior finding converted or closed** — met: all 52 prior IDs (CT-01…CT-52)
   are accounted for in the Appendix. The v0.7.4 CONDITIONAL's two grade-binding
   findings are **closed by execution**: CT-47's settings-refusal alarm and CT-49's
   position alarm both exist, both discriminate (Blue's vacuity probe — moving a
   check below the `Request` construction — reddens the new position pin while the
   old class-only pin stays green, proving the new pin sees what the old one could
   not), and the referee personally re-broke both (the settings conversion
   reverted → CT-47's pin red; a `Request` constructed above the gate → CT-49's pin
   red; each restored byte-identical and watched green). CT-45 and CT-46 are fixed
   and pinned the same way; CT-51's rolling window pin guards the newest record
   (watched red on a renamed run id).
3. **Every defense held by a test that can fail** — met: the two candidates that
   could have bound (CT-56, the position pin's five-shape tuple not covering the
   two new type-guard shapes; CT-54, the newest window row unpinned at the tag)
   were ruled coverage notes under ruling 5's carve-out, with written reasoning:
   in CT-56's case the alarm over the actual defect class exists and fires (the
   referee watched it), and the unpinned band is provably behaviour-preserving; in
   CT-54's case the tag structurally predates its own window's closure, the pin's
   mechanism is proven working, and the record on `main` is verified accurate
   against the live ledger.
4. **Suites green, artifacts verified** — met: 744 tests + 11/11 page suites; the
   published bytes re-hashed, signed, notarized, and attested to `b254fe6`; every
   failed or cancelled build attempt in the release window published nothing.

**What this cycle's delta added** (tiny, and re-established in full): the CT-45
argument-type guards (`wallet_service.py:106-122` — non-string `chain` or hex now
raise the provable not-sent refusal instead of raw `TypeError`/`AttributeError`,
both before any byte is written), the CT-46 abort re-raise (`gui.py:1400-1401` — a
deliberate abort arms the pause *and* propagates the abort type unchanged, so a
host can tell an abort from a lost reply), and six new alarm tests. Seven engine
files, `vendor/`, `scripts/`, and all dependency locks are blob-identical to
`v0.7.4` — the referee recomputed every hash.

**The one Low finding (CT-53), for completeness:** the new type guard admits `str`
*subclasses*, and a hostile `str` subclass with a stateful `__eq__` can slip the
mainnet consent gate at the *engine-function* boundary — demonstrated by Red and
reproduced by the referee. The missing hop is named: reaching it requires attacker
code already executing inside the Python process, which no declared attacker
capability grants and every in-product input source yields exact `str`. Recorded
as hardening debt with a one-line remedy (`type(chain) is not str`); it defeats no
documented control that any product input can reach.

## The four questions that matter

1. **Could this software send the operator's Bitcoin somewhere they did not
   approve?** **No — no path was found, in this cycle or any of the eight before
   it.** Every attack on the money path — lying devices, forged proofs, lying
   servers, racing payments, hostile input types, tampered responses — was refused
   or safely classified, and the exact reviewed bytes went out every time an honest
   path completed.
2. **Could it leak the wallet's addresses and xpubs?** **No.** Diagnostics remain a
   fixed vocabulary; no message carries transaction hex or wallet material; the
   outbound boundary refuses redirects (target receives zero connections) and
   verifies TLS.
3. **Could a remote party, a dependency, or a local process act invisibly?** **No
   new surface.** The release workflow is byte-identical to the prior audited
   revision; the published bytes are attested to `b254fe6`; every failed or
   cancelled build attempt in the window published nothing (the cancelled run left
   zero artifacts).
4. **What should be fixed first?** Nothing blocks anything. The one-line hardening
   items (CT-53's exact-`str` check, CT-56's tuple widening) and the record notes
   (CT-54/55/57) are next-cycle ordinary maintenance, not gate repairs.

## The prior audit's findings: 52/52 accounted for — 5 converted by execution this cycle, 3 closed by written dated owner acceptance, 44 carried with no regression

The prior report (`v0.7.4`, SHA-256 `6bf67462…a65`) carried `CT-01`…`CT-52`. Every
ID is accounted for in the Appendix: `CT-47` and `CT-49` — **the two findings that
held v0.7.4 at CONDITIONAL — closed by execution** (the referee personally broke
both new pins); `CT-45`, `CT-46`, `CT-51` — **converted by execution**; `CT-38`,
`CT-42`, `CT-44` — closed as recorded notes under **written, dated owner
acceptance** (ruling 2: the owner-signed plan of 27 Oct 2026 declares the notes
recorded rather than scheduled; each note's substance verified — CT-38's
citations corrected in this cycle's plan, CT-42's residual re-demonstrated
unchanged and fail-closed, CT-44's sweep re-run green); `CT-01`…`CT-35` and
`CT-36/37/39/40/41/43` — carried with no regression (blob identity recomputed;
744 tests green; spot re-breaks). Nothing dropped; the ledger is a round trip.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (per asset: all five held). Red enumerated the
full input surface and attacked the two small deltas hardest: the type guards pass
every valid input unchanged and refuse every non-contract type with zero network
I/O (connection and DNS counters at zero); the abort re-raise arms the pause
before propagating, with a spy on every observable showing exactly one operation
between catch and raise; the classification boundary re-attacked across twelve
post-POST shapes and five not-sent shapes — all held. The stateful-`__eq__`
subclass demonstration (CT-53) is executed at the engine boundary with the missing
hop named.

**🔵 Blue — DEFENSES HOLD.** Every control on the table passed all five tests: the
five new tests were each personally broken and watched red (including the
non-vacuity probe proving the new position pin discriminates — the old class-only
pin stayed green under the same break), plus three sampled carried controls (all
red). The claims inventory (50 rows) found no claimed protection outside the
inventory. Two Infos: CT-54 (the newest window row's record is unpinned at the
tag) and CT-55 (CT-51's negative half is string arithmetic — same accepted shape
as CT-48).

**🟠 Orange — LOGIC PROVEN** (INV-A″ the not-sent boundary extended with the type
guards — 49/49 checks including `str`-subclass passthrough and exactly-at-limit
sizes; INV-A″ unknown half — 18/18 post-POST shapes; INV-E the new abort
propagation invariant — 20/20 at the real route with abort-identity preservation;
INV-B′/C′ marker lifecycle and per-txid persistence; INV-D the carried engine with
two limbs re-derived). The dependency delta is **empty** (shown, not cited). The
position analysis: the two-name patch (`Request` + `urlopen`) proves position for
its claim, with the CT-45/CT-49 seam recorded as CT-56.

**🟤 Copper — EDGE TRUST HOLDS** (five interfaces, no findings). 78 + 86 executed
drive cases against a live loopback Esplora counting connections and bytes; every
hostile shape lands unknown with the pause armed; the pre-POST refusals proven at
zero connections and zero bytes at the server; `str` subclasses pass the type
guard with wire identity intact; an interrupt mid-submit (with the real 1368 bytes
already on the wire) arms the pause before the abort surfaces; device edge
re-proven on real bytes; state files 0600/0700 executed; every documentation link
resolves to hash-matching `v0.7.5` assets; published app identity internally
consistent.

**🟡 Amber — CHAIN HOLDS** (twelve links). The workflow is byte-identical to the
prior audited revision; all five Actions SHA-pinned; the source tarball
`diff -r`-matches `git archive b254fe6` exactly; three SBOMs bind version 0.7.5 to
`b254fe6` and the candidate run; attestations bind the bytes to both producing
runs; the run ledger — three runs, four attempts, including the cancelled run with
**zero artifacts** — reconciled exactly against the records, and the rolling
window pin matches live. No findings.

**⚪ White — PUBLISH.** Every load-bearing claim re-derived personally: the
conversion pins re-broken (settings conversion; Request-above-gate), the vacuity
probe re-run, the abort drive and the RED-1 demonstration re-executed, the run
ledger re-pulled, the plan re-hashed at start and end. One candidate binding ruled
a coverage note with written reasoning (CT-56); one baseline detail corrected
(ORANGE-1's zero-POST claim was broader than the pin evidence — narrowing, not
widening); the process incident ruled audit-infrastructure only with evidence
validity confirmed independently (see the method disclosure). Session identifiers:
different runs; the surveyor's model is a harness declaration; models not
established. No dissent (a contestable step recorded for auditability).

## What this audit did not examine

- **No live mainnet Esplora broadcast** (production side effects forbidden): the
  post-POST shapes were exercised against loopback fakes; the classification is
  chain-blind after the opt-in check (verified by read), so live-chain behaviour is
  inference, not execution.
- **No physical hardware wallet or device firmware** (plan assumption; device edge
  proven through the app's verification code on synthetic bytes).
- **The Windows/Linux bundles verified as bytes only** (hash, signature,
  attestation); only the macOS DMG was opened.
- **Suite interpreter 3.12.15** vs CI pin 3.12.10 (recorded, not graded).
- **Cryptographic DSSE verification of attestations** (binding verified; Sigstore
  service trusted per plan); **rebuild-from-source reproducibility** not performed
  (re-hash + attestation binding instead); **registry-level per-package dependency
  identity** carried by delta-emptiness.
- **44 carried controls not all freshly broken** (the charter's sampling rule: the
  delta set + three samples, all discriminating; the carried execution conversions
  are recorded in the signed plan).
- **The plan's not-examined list, carried unchanged**: owner machine/account state
  (untested — owner-declared); adversarial firmware; the practice-network second
  source (absent by design, owner ruling); the two retired input workflows beyond
  publish-nothing. Real-Esplora `/outspend` mempool semantics remain open (the
  marker no longer depends on the answer).
- **Method disclosure (panel process, not a product finding):** during the wave,
  Copper's first break-and-write accidentally travelled a symlink into the shared
  clone's directory, transiently modifying two files (an exact revert of the
  cycle's fixes); Copper detected it, restored byte-identical, discarded the
  affected results, and re-established all cited evidence after restoration;
  Orange independently observed the mutation, re-established its evidence on a
  private archive copy, and flagged it. The referee verified the clone clean at
  `b254fe6`, ruled no lane's cited product evidence depends on the mutated window,
  and re-derived every load-bearing claim from its own independent copy. Remedy
  recorded: lanes break controls only under their own scratch directories.

"No finding" means "none found within this coverage."

## Appendix — findings ledger

**Prior ledger (round trip, ruling 8 — prior report SHA-256 `6bf67462f2953bba1d56f462d7ed6047c3112b2af6bf7e4b0829b16f6a018a65`):**

| ID | Sev | Status at `b254fe6` | Evidence |
|---|---|---|---|
| CT-01…CT-35 | Low/Info | carried, verified fixed; **no regression** | Blob identity recomputed at both tags; 744 green; delta reviewed line-by-line |
| CT-36 (Med), CT-37, CT-39, CT-40, CT-41, CT-43 | Med/Low/Info | converted v0.7.4; carried, **no regression** | Classification boundary and money-path shapes re-executed by Red and Copper; inventory tests green |
| CT-38, CT-42, CT-44 | Info | closed by **written, dated owner acceptance** (ruling 2); substances verified | CT-38: this cycle's plan cites real test names; CT-42: residual re-demonstrated fail-closed; CT-44: sweep re-run green (46 tags) |
| **CT-45** | Low | **CONVERTED (closed) by execution** | Type guards implemented before any byte is written; the type pin watched red by Blue and the referee (guard removed → raw `TypeError` → restore → green); Copper's 14 live shapes at zero connections |
| **CT-46** | Info | **CONVERTED (closed) by execution** | The abort re-raise implemented (pause armed before propagation); the interrupt pin watched red by Blue and Orange; the referee's own drive confirmed abort-identity preservation |
| **CT-47** | Info | **CONVERTED (closed) by execution** — the v0.7.4 ruling-1 bind discharged | The settings alarm exists and discriminates (real validator, message asserted, `urlopen` never called); re-broken by the referee → red → restore → green |
| CT-48, CT-50, CT-52 | Info | closed by **written, dated owner acceptance** (ruling 2); substances verified | Owner-signed plan declares notes recorded rather than scheduled; CT-48's composition re-verified by read; CT-50's residual re-demonstrated; CT-52's window facts re-pulled live |
| **CT-49** | Low | **CONVERTED (closed) by execution** — the v0.7.4 ruling-5 sustain discharged | The position pin exists and discriminates position (the vacuity probe: moving a check below the `Request` reddens the new pin while the old pin stays green); re-broken by the referee |
| CT-51 | Info | **CONVERTED (closed) by execution** | The rolling `LATEST_WINDOW` pin (watched red on a renamed run id); the 0.7.4 row correctly guarded at the tag; `main`'s 0.7.5 record verified accurate against the live ledger |
| CT-52 | Info | closed by **written, dated owner acceptance** (ruling 2) | Window facts re-pulled live (three runs, four attempts; the staple failure; nothing published from any failure) |

**New findings this cycle (final IDs; severities calibrated by the referee):**

| ID | Sev | Claim | Location @ `b254fe6` | Why this severity |
|---|---|---|---|---|
| CT-53 | Low | The CT-45 type guard admits `str` subclasses; a stateful-`__eq__` str slips the mainnet gate (comparison-split from the lookup) and a POST to the mainnet explorer is built with `mainnet_opt_in=False` — at the direct-engine boundary only | `wallet_service.py:106,108,120` | Reaching it requires attacker code already executing in-process (the hop rule records this as an exclusion); fail-closed outcome (post-POST unknown); identical family and severity to CT-45 itself |
| CT-54 | Info | The 0.7.5 window record is unpinned at its own tag (`LATEST_WINDOW` pins 0.7.4; the tag's 0.7.5 row names no run ids); `main`'s record verified complete and matches live | `tests/test_hardening_pins.py:936` | Record precision, structurally self-closing at the next constant roll; coverage note per ruling 5 |
| CT-55 | Info | CT-51's negative half is static string arithmetic and never reads the record; enforcement rests on the main pin alone | `tests/test_hardening_pins.py:968-975` | Same accepted shape as recorded CT-48; main pin discriminates |
| CT-56 | Info | Pin-coverage seam: CT-49's five-shape tuple omits the two type-guard shapes and CT-45's test watches only `urlopen`, so the type guards' Request-construction position is unpinned | `tests/test_wallet_service.py:117-156` | Ruled a coverage note under ruling 5's carve-out, with written reasoning: the defect-class motion is caught by a watched pin, and the unpinned band is provably behaviour-preserving (cannot reach a declared asset without a different, watched pin firing) |
| CT-57 | Info | Plan T-10's "exactly 64 lowercase hex" is stricter than the code (64 uppercase accepted, normalized); the lying-txid backstop catches any wrong value | `wallet_service.py:163-168`; plan T-10 | Wording precision; no wrong answer reachable |

**Lane cannot-determine lists** (reproduced in substance): *Red* — RED-1's
in-process exploitation hop (outside the repository); abort-during-lock-wait
judged by reading (fail-closed either way); live platform state and published
bytes outside its delta-scoped charter. *Blue* — 41 carried controls not freshly
broken (charter sampling); page scripts not re-run in-lane; the post-publication
constant roll not determinable at the audited revision. *Orange* — could not
attribute the clone mutation or bound it beyond its timeline; INV-D beyond two
re-derived limbs rests on identity + green suite. *Copper* — no physical device;
the frozen helper's runtime version exchange not executed (identity by hashes);
stall shapes beyond one point rest on the repo's pins. *Amber* — the "503 egress"
event uncorroborated (recorded uncorroborated; the promote's gate verified from
the artifact regardless); five pinned actions' upstream source carried (identical
SHAs); the two lead downloads re-hashed not re-downloaded.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.7.5 · 2026-10-27 · reviewed by the ZCode Color Team panel**

## ✅ CLEARED — the audit's rules were applied mechanically, every clause was met, and for the first time in this lineage the computed grade is cleared

**Read this first:** across nine audits of this software, no examiner — attacking
it full-time with lying devices, forged proofs, hostile servers, and racing
payments — ever found a way to steal, redirect, or spy on the operator's Bitcoin.
This cycle, for the first time, the panel also found nothing left to fix: every
safety behaviour has a working alarm, every earlier finding is verified closed,
and the release pipeline published exactly the checked build's bytes.

## The questions that matter

**Can this app steal or redirect the money?**
No. Nine audits of adversarial testing — lying signing devices, forged proofs,
hostile servers that lie about whether they accepted a payment, racing payments,
tampered files — and the exact reviewed bytes went out every time an honest path
completed, and nothing went out any other way.

**What was checked this time?**
The two small additions since the last audit: a guard that refuses malformed
inputs at the app's engine boundary (verified to refuse before anything is sent,
and to leave valid inputs untouched), and an abort path (verified to pause the
wallet *and* tell the host it was an abort, not a network failure). Both were
broken on purpose by the examiners and the alarms rang. The full money path, the
devices, the network servers, and the release pipeline were re-attacked and held.

**What does "cleared" mean — and not mean?**
It means: under rules locked before anyone looked at the code, applied
mechanically by a referee who re-derived the evidence personally, this version of
this software passed every check the audit defines — no critical or high findings,
every earlier finding verified closed by execution, every claimed protection held
by an alarm that demonstrably rings. It does not mean the software is perfect or
that future versions are cleared in advance; it is evidence about one version on
one day. The one thing you must always do yourself: verify the destination address
and amount on your hardware device's own screen, every time.

## How this review was done

Several independent AI examiners reviewed the software separately, each with one
job and none seeing the others' work until the end; the pass/fail rules were locked
before anyone looked at the code, and the final grade is the *lowest* score on the
team. A different AI model on a different harness wrote the audit's scope than ran
its panel. The referee re-derived every load-bearing claim personally — including
re-breaking two protections and re-running two attack demonstrations — before
allowing this report out.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | Steal, redirect, or damage; find any path to the money | No breach demonstrated; the prior cycle's attack scenario confirmed fails closed |
| BLUE · The defender | Prove every claimed protection holds, and that its alarm actually rings | Defenses hold — every new alarm personally tripped and rang |
| ORANGE · The logic specialist | Check the math and rules that must never be wrong | Logic proven — every boundary case executed as derived; the corrected sending rule holds |
| COPPER · The edge specialist | Attack every connection the app must trust | Edge trust holds — no findings; every hostile server shape refused or safely classified |
| AMBER · The supply inspector | Check how the downloads are built and whether they are what they claim | Chain holds — published bytes match the checked build exactly; every failed or cancelled build published nothing |
| WHITE · The referee | Distrust everyone; re-derive the evidence; compute the grade | Re-broke two protections and re-ran two attack demonstrations personally; computed the grade from the locked rules: **CLEARED** |

## The audit trail

**Read this first:** across all nine reviews, no way was ever found to steal,
redirect, or spy on the operator's Bitcoin. This cycle found no new issues beyond
one-line hardening notes for future maintenance.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| DANGER SIGN | **None found — in any review.** | — |
| MINOR IMPROVEMENT (future maintenance) | One boundary check could be stricter about input *types* (unreachable through the app itself); one alarm could cover two more input shapes; a release-record test should roll forward each cycle; a plan wording note. All one-liners for future cycles — nothing blocks anything. | CT-53, CT-56, CT-54, CT-57 |
| HOUSEKEEPING | Two residual behaviours restated (fail-closed); a test's negative half is a string check (noted, not fixed); the recurring Apple notary flake (always fail-closed; nothing ever published from a failed attempt). | CT-50, CT-55, CT-52 |
| IMPORTANT TO FIX — RESOLVED | Last audit's two findings — the missing alarm tests over the payment gate — are fixed and *proven* fixed by breaking them and watching the alarms ring. | CT-47, CT-49 |
| RESOLVED | All 44 earlier findings: carried clean, no regressions. The whole ledger — 52 findings across nine audits — is now closed. | CT-01…CT-46, CT-48, CT-50–52 |

## What this review does not cover

This grade is about version 0.7.5 exactly, as published on 2026-10-27. Hardware
devices were tested through the app's verification code, not physically; the
Windows and Linux downloads were verified by hash, signature and build
attestation; no live mainnet server was contacted (server behaviours were
simulated byte-accurately on a loopback). AI review complements — it does not
replace — a qualified human audit. "Nothing found" means "nothing found within
this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.5.md` in the repository |
| The one-page security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.5.md` in the repository |
| The audit rulebook and scorecard | `…colorteam-audit-plan-v0.7.5.md` and `…colorteam-audit-lock-v0.7.5.md` in the repository; the framework at `cjtsh/ai-color-team-audit-framework` |
| Every earlier cycle (unedited) | `audit-history/` in the repository |

---

*Audit performed 2026-10-27 by the ZCode Color Team panel on the public repository
(tag `v0.7.5` = `b254fe6f6fc724f25e0c40658bd430c4bffaedcb`) and the published
release artifacts only. The grade rules were locked before the audit began and
applied as written; the scope plan was owner-signed (Bitseeker LLC, 27 Oct 2026)
and its hash unchanged from before the first specialist ran to after the last
(`13107186d9a12ff03bf1cd4efe18521691d96554aca4118ed3ceb8cee3dd2e7b`; the lock was
pre-published by the operator at commit `4a60be5`). No credential values, seed
material, or private keys appear in this report. An audit is evidence about one
revision on one day, produced by the agents named above — not a certification of
safety, and not a promise about any future version. Coverage limits are stated
above; the surveyor and auditor identities are declarations, not independent
verifications.*

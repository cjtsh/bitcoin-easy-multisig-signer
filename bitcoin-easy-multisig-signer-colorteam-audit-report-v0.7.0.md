# Kimi Code Security Audit — Bitcoin Easy Multisig Signer v0.7.0 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.0`, commit `4fe8f2955e29cae6838e2ba0b8029c9abae9fdeb` (`4fe8f29`), committed 2026-10-16T01:10:30-04:00; ten release assets published 2026-10-16T06:15:36Z |
| **Assets declared** | 1. The Bitcoin in the operator's multisig wallet · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain · 4. Release artifact integrity · 5. Wallet privacy (xpubs, addresses, BSMS contents, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White referee, run by the Kimi Code desktop agent; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh)` · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` — declared by operator `cjtsh` (Bitseeker LLC) |
| **Auditor identity** | Harness `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop)` · session `1d323ae6-8fdf-4cba-993f-5bb46154a778` (harness session-directory identifier, visible in the session's own tool-output paths; no session environment variable exists) · model `not exposed by the harness` |
| **Independence** | Surveyor and auditor ran in different sessions: **yes** — the identifiers differ (`session-64472385…` vs `1d323ae6…`) and the harnesses differ. Different runs established by the identifiers; different models rest on the two harnesses' declarations, not independent verification. (The auditor's identifier matches the earlier cycles' auditor session; the independence rule binds surveyor-vs-auditor within a cycle, not the auditor across cycles.) |
| **Cycle** | `v0.7.0` — a **conversion re-check** (follow-up cycle) in the `v0.6.8` lineage; this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.0.md` |
| **Prior audit** | Cycle `v0.6.9`: report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.9.md` (archived at `audit-history/` after this cycle's publication), grade ⚠️ CONDITIONAL |
| **Original scope plan** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` (archived at `audit-history/`) — scope carried forward **unchanged**, verified mechanically: the declared-assets table, the unforgivable acts, and every threat-row heading are byte-identical between the baseline and this cycle's plan; the rubric differs only in the revision pointer |
| **Verification** | Independently re-derived: all ten v0.7.0 asset digests against `SHA256SUMS` (8/8 listed files OK), the attestation subjects, and the release API's recorded digests; `SHA256SUMS.asc` GPG-verified against the committed `signing-key.asc`; three attestations (two SLSA-v1, one in-toto release) bound to `gitCommit 4fe8f29…`; the DMG's Apple signature, notarization, and stapled ticket verified by mounting; the full test suite re-run at the tag (713 tests OK + 11/11 JS suites); the live platform posture re-read (rulesets, environments, immutable releases enabled, registrations); the publish-path sweep re-run against the live remote; the stapler incident independently verified |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.0.md`, SHA-256 `0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5` before the first specialist ran and the same hash at the referee's re-check — **equal: the scope never moved**. Owner-signed: Bitseeker LLC, 16 Oct 2026. The lock (`bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.0.md`) was published to `main` at commit `a487049` before the panel ran — order witnessed |

## The grade: ⚠️ CONDITIONAL — the v0.6.9 hold is cleared (both conversion-gating findings verified fixed by execution), and two new same-family Informational findings keep the grade honest

This cycle was the framework's conversion re-check, and the conversion gate was **met
by execution, not acceptance**: the referee personally re-broke the CT-13
fair-admission server in both directions and removed each of CT-14's three prevout
limbs, watching the discriminating tests fail. The delta introduced no new Critical or
High. The prior ledger's round trip is complete: **18 of 18 findings verified fixed,
none dropped, none closed by acceptance.**

The grade is held below CLEARED by two new Informational findings in the lineage's
pin-accuracy family:

- **CT-21** — the fair-admission rework's retired-set execution guard
  (`gui.py:669-679`) has no test that can fail. The referee deleted it and watched the
  full integration suite stay green. The guarded *behavior* (a retired connection is
  never answered) was established independently by direct experiment, and the guard's
  precondition is unobservable under the server's HTTP/1.0 semantics — but the repo's
  own discipline claims a demonstrated-failing test for exactly this class, and the
  locked rubric's CONDITIONAL clause names "stated invariants that lack the test
  coverage the repo claims."
- **CT-20** — the control inventory's claim-phrase net is blind to
  `.github/workflows/*.yml` (and `ui.html`): the referee demonstrated that a "fail
  closed" claim comment added to the workflow passes the inventory suite unseen, and
  the CT-16 guard's own claim comment arrived untracked. The guard itself is present,
  effective, fail-closed, and pinned — the gap is in the tracking layer.

Floor set by the Copper lane (CT-21), corroborated by Blue (CT-20); bound by the
rubric-tension ruling (ambiguity never resolves in CLEARED's favor). The exact path
to CLEARED: pin CT-21 (or drop the guard and record the reliance on shutdown
semantics — owner decision), add the CM-33 row and extend the inventory's file set
(or record a scoped no-control-claimed rationale — owner decision), then a
delta-scoped re-check.

## The four questions that matter

1. **Could this software sign or broadcast a transaction the operator did not review
   and approve?** — **No path found.** The money path is byte-identical to the
   previous cycle (verified blob-for-blob, not assumed); the one substantive logic
   change (the loopback server's admission policy) was attacked with floods, drips,
   mid-service eviction attempts, and lock races — an in-flight signing or broadcast
   request cannot be evicted, truncated, or answered for. Red: NO BREACH
   DEMONSTRATED; Orange: LOGIC PROVEN, with the chain constants re-matched live
   against Bitcoin Core and the Mutinynet checkpoint this cycle.
2. **Could it leak the wallet's addresses, xpubs, or the credentials?** — **No path
   found.** The token gate was personally re-broken by the referee (17 named tests
   went red); diagnostics remain drop-not-escape under a fresh smuggle battery; the
   startup-failure dialog and log are both bounded; no credential value appears in
   the tree, the archive, the artifacts, or the publish logs.
3. **Could a remote party, a dependency, or a local process act invisibly?** — **No
   demonstrated path.** The dependency delta is empty (verified); the poisoned-HWI
   and counterfeit-device pins are byte-identical and green; the pipeline's new
   pagination guard refuses 27/27 hostile shapes and both its pins were watched red;
   the recorded stapler incident was verified as a clean failure — the failed runs
   published nothing, and the published bytes trace to candidate `38854414566` →
   promote `38857329074` (attempt 3) at `4fe8f29`. Residual: a *sustained* local
   busy-flood can still occupy all 32 connection slots (CT-19) — availability of the
   window only, self-healing, no asset reachable, and the design's stated trade.
4. **What should be fixed first?** — CT-21 and CT-20, the two pin-accuracy items, and
   then the honest answer to the recurring family: the tripwire habit at writing time
   (see the private briefing).

## The prior audits' findings: 18 of 18 verified fixed by execution

The referee enumerated the v0.6.9 report's ledger (CT-01…CT-18) and re-derived every
disposition personally — a round trip, not a summary:

| IDs | Disposition |
|---|---|
| CT-01, CT-02, CT-04, CT-05, CT-06, CT-12 | **Verified fixed — carried, no regression** (pin files byte-identical; suites green) |
| CT-03, CT-11 | **Verified fixed — carried and strengthened** (the inventory net widened; the retired-publisher guard now fails closed on pagination) |
| CT-07 | **Verified fixed — carried** (the named omissions gained rows CM-21…CM-26) |
| CT-08, CT-10 | **Verified fixed — re-derived live** (the referee's own token-gate break; immutable releases re-read from the API) |
| CT-09 | **Verified fixed — superseded** by the CT-13 shape change (the ceiling is still a ceiling) |
| **CT-13, CT-14** | **CONVERTED — verified fixed by execution** (the conversion-gating pair; the referee's own breaks above) |
| **CT-15, CT-16, CT-17, CT-18** | **CONVERTED — verified fixed by execution** (CT-18: the record was corrected, and the corrected claim re-verified true) |

## The panel

**🔴 Red — NO BREACH DEMONSTRATED (itemized: all five declared assets).** Red
re-enumerated the surface (the delta adds no new input or route) and attacked the
fair-admission server end to end: eviction of a busy in-flight request (blocked),
answers on retired sockets (blocked), completing a head after mid-read retirement
(blocked), lock races (4,000-cycle fuzz, zero violations), and keep-alive abuse (not
present — the server speaks HTTP/1.0). The pagination guard survived 20 hostile JSON
shapes. One Informational (CT-19): the sustained busy-flood residual.

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Every asset-protecting control passes all five
tests — present, reachable, effective, fail-closed, pinned — and every control Blue
broke went red in its named test, including the CT-13 server (both directions), the
CT-14 limbs, the CT-16/CT-17 pins, and the inventory self-bindings. The gap (CT-20):
the tracking net cannot see workflow files.

**🟠 Orange — LOGIC PROVEN (nine invariants).** The money-path files and their pin
files are byte-identical to the prior revision (blob hashes shown); oracles
re-matched live this cycle (Bitcoin Core chainparams for all three networks; the
Mutinynet block-1 checkpoint). CT-14's rework was judged as logic before execution —
the new discriminating cases were read against `_utxos_agree_with_totals` and the
build path, then each limb was removed and watched red.

**🟤 Copper — EDGE TRUST HOLDS (six interfaces).** The loopback server survived the
full behavioural battery (11/11 live checks: admission under flood, drip retirement,
busy-connection immunity, surplus refusal, retired-socket silence, churn recovery);
the published DMG verifies codesigned, notarized, and stapled; both published
bundles' helpers byte-match their sidecars and payload manifests. One Informational
(CT-21): the retired-set execution guard is unpinned.

**🟡 Amber — CHAIN HOLDS (per link).** The v0.7.0 chain re-established independently:
ten assets re-downloaded, re-hashed, GPG-verified, attestation-bound (three
attestations to `4fe8f29`, all subject digests recomputed); producing runs
identified and input-bound; the stapler incident verified against run logs (the
failed attempts published nothing); the live site byte-matches its three offered
downloads to the release assets; the sweep re-run live (exit 0); the platform re-read
live with immutable releases enabled; the CT-18 record correction verified against
the actual diff. No findings.

**⚪ White — PUBLISH.** The referee re-derived 18 load-bearing claims personally —
the baseline suite, both conversion breaks, every new finding's evidence, the
stapler-incident account, the token gate (attacked as a false-clean-bill check — 17
tests red), the byte-identity carry-forward table, the artifact chain, and the timing
re-confirmations. 18 CONFIRMED, 0 CORRECTED, 0 UNVERIFIABLE. Grade computed from the
rulings: the conversion gate is met; CONDITIONAL binds on CT-21/CT-20 via the
rubric-tension ruling. No dissent. Round trip complete: 18/18.

## What this audit did not do

- **The panel spanned 2026-10-16 → 2026-10-25** because of auditor-side quota pauses;
  the tag resolution, plan hash, and `main` were re-confirmed at re-check time
  (nothing moved under the audit).
- Delta-scoped per the conversion re-check: unchanged domains were carried on shown
  blob identity plus re-execution at the tag — never on assumption.
- The AppImage's squashfs internals were not extracted (the Linux tarball verifies;
  the AppImage is checksum-, signature-, and attestation-bound). Windows Authenticode
  is not verifiable on macOS; the Windows helper is byte-matched via its sidecar.
- No hardware-wallet devices were attached; device firmware is the owner's exclusion.
- The platform read is a point-in-time read; platform state can change invisibly to
  git between checks.
- The owner's machine, account, and outside-repository automation are *untested —
  owner-declared* assumptions per the signed plan. The practice-network
  single-explorer residual (T-07) and the 46 legacy-tag publishers residual (T-25)
  stand as recorded.
- Environment states, not defects: suite interpreter 3.12.14 vs CI's pinned 3.12.10;
  the plan §0's "12 page-script suites" vs the tree's 11 `tests/ui_*.cjs`
  (document-state note).
- "No finding" means none found within this coverage — not that none exist.

---

# Bitcoin Easy Multisig Signer — Plain-English Safety Review

**Bitcoin Easy Multisig Signer v0.7.0 · 2026-10-25 · reviewed by a six-examiner AI
panel run by the Kimi Code agent**

> ## ⚠️ CONDITIONAL — everything the previous reviews asked for is done and verified (all eighteen items), the downloads check out completely, and two small pieces of test paperwork — plus the honest habit behind them — are what remain

This review was written for the person this software is actually for: a spouse,
trustee, lawyer, accountant, or advisor settling an estate that includes Bitcoin.
Every statement here traces to the technical report above it in this same file. The
evidence is public; the last section tells you where.

## The questions that matter

**Can this app move your Bitcoin somewhere you didn't approve?** Across three full
reviews now, no way has ever been found. This version changed almost nothing in the
money path — the examiners proved the code is byte-for-byte identical — and the one
real change (how the app's window handles a flood of junk connections) was attacked
directly: a payment in progress cannot be evicted, cut off, or answered by anyone
else. Keep doing the one thing that protects you no matter what: **read the
recipient and amount on your hardware device's own screen before approving.**

**Could it leak your wallet's addresses or other secrets?** No path was found. The
examiner in charge of this personally switched off the token check and watched
seventeen alarms fire. The crash log and the Windows error popup now both show only
a short, bounded description.

**Could someone tamper with the app or its download?** The v0.7.0 download was
re-downloaded and re-checked from scratch: checksums, the publisher's signature, the
tamper-evident build records, and Apple's notarization all verify — including the
stapled ticket on the actual download. You may have heard the release needed a
second attempt: the examiners checked that story against the build system's own
records, and it is exactly what happened — an Apple network hiccup stopped the first
attempt, which published nothing; the successful run's records match the published
bytes.

**What does the grade mean — and not mean?** CONDITIONAL this time means: the
software itself passed everything, and the hold is about the *watchdogs' paperwork* —
one internal guard has no test proving its alarm works (its job was tested another
way and it works), and the project's control checklist can't "see" one type of file.
The rules were locked before anyone looked at the code, the grade is the *lowest*
score on the team, and the referee explained in writing why the rules don't allow
rounding up. This grade covers **v0.7.0 only**, and no audit is a guarantee.

## How this review was done

Five independent specialist examiners each checked only what changed since the last
review, plus proof that the unchanged parts really are unchanged (byte for byte). A
sixth, the referee, personally re-did 18 of the most important checks — including
breaking each new fix to make sure its alarm fires — and computed the grade from the
locked rules.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | break in and move the money | Flooded, stalled, and raced the new connection handling; attacked the pipeline's new guard with 20 hostile inputs. Nothing moved. |
| BLUE · The defender | prove every lock actually locks | Every lock broken and watched; all prior fixes re-verified. Found the checklist's blind spot (CT-20). |
| ORANGE · The logic specialist | check the math against the rulebooks | Money path proven unchanged byte-for-byte; the new prevout tests verified to test what they claim (CT-14 closed). |
| COPPER · The edge specialist | test what the app must trust but can't control | The window's flood handling, the downloads' signatures, the bundled parts — all held. Found one unpinned guard (CT-21). |
| AMBER · the supply inspector | follow the app from source to your download | The whole chain re-verified; the failed release attempt confirmed to have published nothing. |
| WHITE · the referee | distrust everyone; compute the grade | Re-did 18 key checks personally; all held; computed the grade with the arithmetic shown. |

## The audit trail

**Read this first:** across all three reviews, no way has ever been found to take,
redirect, or mislead a payment, leak wallet material, or publish a tampered
download. Everything below is paperwork and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| DANGER SIGN | **None found — in any review, in any version.** | threat-row table |
| IMPORTANT TO FIX — RESOLVED | **All eighteen findings from the previous reviews are fixed and verified fixed** (CT-01…CT-18): the flood-proofing, the prevout tests, the checklist's self-check, the website version guard, the token history, the crash log, the open endpoints, the connection ceiling, release immutability, the retired build paths, and the libusb provenance record. | prior-findings table |
| MINOR IMPROVEMENT | None open at this level this cycle. | — |
| HOUSEKEEPING | Three notes for the maintainers (CT-19…CT-21): the documented flood trade-off, the checklist's file-class blind spot, and the one guard without its own alarm. | ledger |

## What this review does not cover

This grade applies to **v0.7.0 only**. Physical hardware wallets were not tested
(the owner does that); the Windows and Linux packages were verified by fingerprint
and the macOS package was executed and signature-checked. The review was performed
by AI agents and complements — it does not replace — a qualified human security
firm. The panel ran over several days; the code did not change during the review.
"Nothing found" means "nothing found within this coverage," never "nothing exists."

## Check our homework

| Document | Where |
|---|---|
| This report (technical detail + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.0.md` in the repository root |
| The one-page public security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.0.md`, same place |
| The audit plan (signed) and the scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.0.md` / `…-audit-lock-v0.7.0.md`, same place |
| Earlier cycles' artifacts | `audit-history/` (archived, unedited) |
| The method | `github.com/cjtsh/ai-color-team-audit-framework`, tag `v1.5.1` |

You can read every page of the evidence yourself.

*Prepared 2026-10-25 by the Kimi Code audit panel from the public repository and
published artifacts of v0.7.0. Every statement above traces to the technical report.
A safety review is evidence about one version on one day — not a guarantee.*

---

# Appendix — findings ledger

**Prior cycles (v0.6.8 + v0.6.9 reports):** CT-01…CT-18 — all **verified fixed**
(dispositions and evidence in the round-trip table above; 18/18, none dropped, none
closed by acceptance).

**New findings this cycle (locations `@ 4fe8f29`):**

| ID | Severity | Location | Claim | Status |
|---|---|---|---|---|
| CT-19 | Info | `gui.py:163-176, 183-189` | A sustained tokenless busy-flood can still hold all 32 connection slots; availability-only, self-healing within the 15 s read budget, no declared asset reachable — the design's stated trade. (Docstring nuance: busy requires a complete head, not the token.) | Open — observation; owner may accept or adjust |
| CT-20 | Info | `tests/test_controls_inventory.py:34-39` | The inventory's claim-phrase net is blind to `.github/workflows/*.yml` (and `ui.html`); the CT-16 guard's claim comment arrived untracked — a tracking-layer gap; the guard itself is present, effective, fail-closed, and pinned | **Open — needs an owner decision** (CM-33 + extend `SHIPPED`, or a scoped no-control-claimed rationale) |
| CT-21 | Info | `gui.py:669-679` | The retired-set execution guard has no test that can fail; its precondition is unobservable under the server's HTTP/1.0 semantics and the guarded behavior is established independently — the lineage's unpinned-guard family | **Open — needs an owner decision** (pin it synthetically, or drop it and record the reliance) |

**Referee referral (not a finding):** none this cycle.

---

*Audit performed 2026-10-16 → 2026-10-25 on the public repository and published
artifacts only. The grade rules were locked before the audit began and applied as
written. No wallet material, seed, PIN, private key, or credential value appears in
this report. An audit is not a certification of safety; coverage limits are stated
above. The mandatory one-page Public Security Statement for this release is
`bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.0.md`.*

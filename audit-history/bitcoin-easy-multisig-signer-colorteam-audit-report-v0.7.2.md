# ZCode Color Team Audit — Bitcoin Easy Signer v0.7.2 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.2`, commit `1e51dcfa45d6f61c83c14aeb1998725fbd705ba9`, release published 2026-10-26T21:48:23Z (ten assets, immutable releases live) |
| **Assets declared** | (1) The Bitcoin in the operator's multisig wallet — no transaction signed or broadcast that the operator did not review and approve; (2) signing and CI credentials and the release workflow; (3) the reviewed-transaction integrity chain; (4) release artifact integrity — only the verified candidate's exact bytes publish; (5) wallet privacy. No asset is optional; the ranking orders severity, not attention |
| **Auditor** | ZCode — a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber — one fresh context each, dispatched as one wave) plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness` (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` (declared by operator handle `cjtsh`, Bitseeker LLC) |
| **Auditor identity** | Harness `ZCode 3.16.3` · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` — the same auditor seat as the prior cycle, as the pre-published lock's auditor row anticipated |
| **Independence** | Surveyor and auditor ran in different sessions: **yes — different runs** (the surveyor's identifier is present and names a DeepSeek Harness session; the auditor's harness exposes none). **Different models is NOT established** — it rests on the operator's declaration |
| **Cycle** | `v0.7.2` — a **conversion re-check** of the `v0.6.8` lineage (delta-scoped wave; carried domains carried by verified blob identity, the delta's three app files re-established in full) |
| **Prior audit** | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.1.md`, SHA-256 `1f22846c0002cfa39e506912ffc4652e1f67e3c103a7d620ae1800eb1fb57eea`, grade **⚠️ CONDITIONAL** (held by CT-22) |
| **Original scope plan** | `audit-history/bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — scope carried forward **unchanged** into this cycle's plan; lead-verified against the prior plan (`…plan-v0.7.1.md`, SHA-256 `6137530d…d88c`): §2–§3 byte-identical; §5 differs only in T-11's entry/evidence fields (updated to name the new gate sites and pins, and to mandate breaking each half — a strengthening) plus declared revision pointers |
| **Verification** | Independently re-derived: ten release assets hash-checked against `SHA256SUMS`; `SHA256SUMS.asc` = Good signature `Bitseeker LLC <release@bitseeker.llc>` (RSA `ACCC2F1C…D6D7`); three Sigstore attestations bind the digests to `1e51dcf` from `build-candidate.yml` @ `refs/heads/main`; DMG app codesign-strict OK, spctl accepted, TeamID `B8G5L7M8TB`, staple valid; suite re-run at the audited revision (**727 tests, OK** on Python 3.12.15, hash-locked deps; CI pins 3.12.10 — recorded); the run ledger re-read live (candidate run 40397174519: attempts 1–5 failed — every failure in the DMG job; publish jobs skipped each time, **nothing published from any failure** — attempt 6 succeeded; promote 40405953511 attempt 1 published); the referee personally re-broke the CT-22 early half, the CT-22 in-lock half and CM-39, re-ran the in-flight-window attack end-to-end, and re-derived the grade from the rubric |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.2.md`, SHA-256 `36d30916b2447b2b26cf82353fe478ef543139e3b2856e6b573d496bd03913b4` before the first agent ran and `36d30916b2447b2b26cf82353fe478ef543139e3b2856e6b573d496bd03913b4` at the end — **equal: the scope never moved**. Owner-signed **Bitseeker LLC, 26 Oct 2026**. The lock was **pre-published by the operator's side** (commit `3331c93`, amended `d88fa6f` to record its own commit; locked-at `2026-10-26T21:55:00Z`, before this panel was dispatched) with the same hash the lead independently verified — the order of events is witnessed by the repository itself |

## The grade: ⛔ BLOCKED — the payment-sequencing gate added this cycle still has a demonstrated hole: a second payment can be broadcast while the first is in flight

**First, what this audit confirmed:** the `v0.7.1` conversion path was executed exactly as
that report named it. The broadcast-time refusal exists in both halves (an early
refusal before any explorer pre-check, `gui.py:1219-1230` @ `1e51dcf`, and a
re-assertion inside the pre-submit lock, `gui.py:1265-1272`), each half is pinned by
its own independent test, and those pins are **demonstrated able to fail** — Red,
Blue and Orange each broke them and watched them go red; the referee re-broke two of
them personally. **The referee rules the conversion criterion MET BY EXECUTION:
CT-22 (and CT-24, CT-25) are closed, and the `v0.7.1` CONDITIONAL is discharged on
its own terms.** CT-24's duplicate-input refusal and CT-25's transport-failure
contract held under every hostile shape thrown at them.

**What blocks the grade.** The new gate guards the *record* of a pending payment —
and that record is written only **after** `broadcast_transaction` returns. While the
first payment's broadcast is in flight (`pending_broadcast_txid` still `None`; the
window is bounded by `BROADCAST_TIMEOUT_SECONDS = 20.0`, `wallet_service.py:40`), a
second, *differently* reviewed payment passes **both** gate halves and is broadcast.
Red demonstrated this end-to-end through the real HTTP entry points; Orange
demonstrated it independently; **the referee re-ran the attack personally and
confirmed it** (both raw transactions reached the broadcaster; they shared an input;
the arming was observed only after the first broadcast returned).

Because the invariant is part of Orange's lane — "no second outbound payment while
one is unconfirmed," the frozen T-11 prohibition verbatim — Orange's computed
sub-verdict is **LOGIC WRONG**, and the framework's ruling 4 is mechanical: *"The
grade is ⛔ BLOCKED — no severity calibration, no rubric judgment, no weighing it
against clean lanes."* The referee re-derived the violation personally and it
stands. The finding itself is calibrated **CT-27, Medium** (a control weaker than
documented — the user manual's step-7 claim that "the app refuses that second
payment" is false inside the window; but no unforgivable act: both payments were
individually reviewed, device-signed and separately consented) — and that
calibration plays no part in the grade, as ruling 4 requires. The plan's T-11 row
("failure blocks: CLEARED") is honoured as written — the grade is not CLEARED — and
the plan's BLOCKED row does not fire (there is no unforgivable act, no broken lock,
no unverified published byte); the framework's lane-failure table is the binding
instrument, per PANEL-DESIGN's authority clause ("a demonstrated in-scope exploit or
broken protective control still blocks regardless of severity averaging").

**The exact path back** (each item small; the first is the grade-setter):

1. Arm a per-wallet **in-flight marker under the pre-submit lock, before** the
   broadcast call (and before releasing the lock), clearing/reconciling it on a
   definite `WalletError` refusal — this closes the window without holding the lock
   across I/O, preserving the CT-13 design; or have both gate halves test *intent*
   (a submission in progress) as well as *record*.
2. Pin the window with a test demonstrated able to fail (break-and-watch before
   committing — the discipline this lineage has already made habitual).
3. Correct the `gui.py:1266-1268` comment ("cannot both submit" is false as
   written) and the USER-MANUAL step-7 claim — or make them true.
4. Add `OSError` to `verify_esplora`'s catch tuple (CT-33: a pure RST mid-response
   still escapes as `ConnectionResetError`, losing the documented message — the one
   surviving variant of the CT-25 class); reconcile the pending record per-txid
   (CT-29); track the CM-38 in-lock half in its own inventory row (CT-30) and the
   secret-scan control (CT-31); record this release window's five failed candidate
   attempts (CT-35); refresh the next plan's stale §4/§5 citations (CT-32).
5. Run the next delta-scoped cycle.

## The four questions that matter

1. **Could this software send the operator's Bitcoin somewhere they did not
   approve?** **No — no path to an unforgivable act was demonstrated, in this cycle
   or any before it.** Every broadcast demonstrated (including both transactions in
   the CT-27 window) carried operator-reviewed, device-signed, separately-consented
   bytes; substitution, metadata injection, consent bypass and stale-payment swap
   all held. CT-27 is a *sequencing* defect between two approved payments, not a
   path to unapproved ones.
2. **Could it leak the wallet's addresses and xpubs?** **No** — the diagnostics
   vocabulary held under every smuggling attempt; the new refusal messages carry no
   wallet material (Orange checked every mapped error text).
3. **Could a remote party, a dependency, or a local process act invisibly?** **No
   new surface.** The workflow is byte-identical to the prior audited revision; the
   published bytes are attested to `1e51dcf`; five failed build attempts published
   nothing.
4. **What should be fixed first?** **CT-27's in-flight marker** (item 1 of the path
   back) — everything else is a one-line or documentation item.

## The prior audit's findings: 26/26 accounted for — 3 converted by execution, 2 closed by written dated owner acceptance, 21 carried with no regression

The prior report (`v0.7.1`, SHA-256 `1f22846c…b57eea`) carried `CT-01`…`CT-26`.
Every ID is accounted for in the Appendix: `CT-22` (the conversion gate), `CT-24`,
`CT-25` — **converted by execution**; `CT-23`, `CT-26` — closed as recorded notes
under **written, dated owner acceptance** (ruling 2: the owner-signed plan of
26 Oct 2026 — post-dating both findings — declares the notes recorded rather than
scheduled; CT-26's record was additionally verified accurate against the live
prior-window run ledger); `CT-01`…`CT-21` — carried, no regression (blob identity
recomputed; 727 tests green; the referee's and lanes' spot re-breaks). Nothing
dropped; the ledger is a round trip.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (per asset: all five held; no unforgivable act).
Red enumerated the full input surface and attacked the new gate hardest: the early
half's TOCTOU is caught by the in-lock half; the outcome-unknown arming held on all
five shapes (every unknown arms, HTTP 400 correctly does not); the CT-24 refusal
fires before any explorer call with zero false positives; four break-and-watches all
went red on demand. The in-flight window (CT-27) was demonstrated end-to-end with
real HTTP flows; the same-payment double-submit falsified the gate comment (CT-28);
the last-recorder-wins pending overwrite is CT-29.

**🔵 Blue — DEFENSES HOLD.** Nine break-and-watches (nine reds, nine byte-identical
restores, nine greens) across the new CM-38–42 controls and sampled carried controls
(mainnet consent layered defence, final-vs-review, the retired-set guard — whose row
needed no retarget). All 42 inventory rows pass the five tests. Three Infos: CT-30
(the CM-38 row tracks only the early half — Blue proved the row's named test stays
green when the in-lock half breaks), CT-31 (the secret-scan control untracked), CT-32
(plan citation staleness — the referee partially corrected Blue's specifics).

**🟠 Orange — LOGIC WRONG** (INV-A, the frozen T-11 invariant, violated in the
in-flight window — confirmed by the referee's own re-execution). Every other
invariant is **LOGIC PROVEN**: the outcome classification (a lost broadcaster reply
is an unknown outcome, never a retryable failure — 7/7 boundary cases; HTTP 400 with
a body correctly remains a plain refusal), the duplicate-input refusal (7/7), the
explorer failure contract (6/6, no wallet material in any message), and the 14
carried invariants (blob identity + the two re-derived prevout limbs + four watched
reds). The dependency delta is **empty** (shown, not cited).

**🟤 Copper — EDGE TRUST HOLDS** (six interfaces). The changed transport contract was
re-verified with 15 hostile socket shapes: broadcast-side failures produce
**outcome-unknown in every die/stall shape** (the safety-critical direction,
confirmed end-to-end through the real route with no broadcaster mocks — HTTP 409,
pause armed); redirects refuse with zero requests at the target; TLS impostors named
and refused; device edge re-proven on real bytes (one flipped bit → refusal); state
files 0600/0700; every documentation link resolves to hash-matching `v0.7.2` assets.
CT-33: the pure-RST shape still escapes `verify_esplora`'s tuple (fail-closed
throughout); CT-34: bounded-read truncation relies on callers' format checks.

**🟡 Amber — CHAIN HOLDS** (15 links, each named/pinned/real/read/matched). The
workflow is byte-identical to the prior audited revision; all five Actions SHA-pinned
and version-matched; the source tarball `diff -r`-matches `git archive 1e51dcf`
exactly; both producing runs attest the same digests from `1e51dcf`; the candidate
run's five failed attempts published nothing (publish jobs skipped each time); the
prior window's three failure events are recorded per CT-26's conversion and verified
against the live ledger. CT-35: this window's own five attempts are recorded nowhere.

**⚪ White — PUBLISH.** Every load-bearing claim CONFIRMED (two sub-instances
corrected, stated in the ledger; none unverifiable). The grade follows from the
rulings with the arithmetic shown: conversion gate met by execution → the v0.7.1
CONDITIONAL discharged; Orange's LOGIC WRONG confirmed by the referee's own
execution → ruling 4 forces **⛔ BLOCKED**; the plan's narrower BLOCKED row and the
T-11 "failure blocks: CLEARED" field are honoured as written and do not soften or
harden the ruling. Session identifiers: different runs; models not established.
No dissent.

## What this audit did not examine

- **No physical hardware wallets or device firmware** (plan assumption; device edge
  proven through the app's verification code on synthetic keys).
- **The Windows/Linux bundles verified as bytes only** (hash, signature,
  attestation); only the macOS DMG was opened.
- **Suite interpreter 3.12.15** vs CI pin 3.12.10 (recorded, not graded).
- **The honest-network width of CT-27's window** — bounded ≤ 20 s by
  `BROADCAST_TIMEOUT_SECONDS`, unbounded only behind a withholding broadcaster
  (T-10's in-model adversary); no production-network contact was made.
- **Real-Esplora `/outspend` mempool semantics** remain recorded open (plan §9) —
  noted by the referee as no longer load-bearing once CT-27's remedy lands.
- **Cryptographic DSSE verification of attestations** (binding verified; Sigstore
  service trusted per plan); **runner-image bytes** (GitHub-operated, declared
  assumption); the frozen helper's embedded hwilib files verified via a
  reconstructed copy through the real verifier.
- **The plan's not-examined list, carried unchanged**: owner machine/account state
  (untested — owner-declared); adversarial firmware; the practice-network second
  source (absent by design, owner ruling); the two retired input workflows beyond
  publish-nothing.
- **The plan's own recorded defects** (documentation precision, next-plan items):
  §0's "In scope" paragraph cites the prior revision's commit where the revision
  rule says `1e51dcf`; two §4/§5 `gui.py` citations stale (CT-32 — one instance
  corrected by the referee); the §0 lineage sentence "verified CT-01…CT-26 fixed"
  contradicts its own next sentence.

"No finding" means "none found within this coverage."

## Appendix — findings ledger

**Prior ledger (round trip, ruling 8 — prior report SHA-256 `1f22846c0002cfa39e506912ffc4652e1f67e3c103a7d620ae1800eb1fb57eea`):**

| ID | Sev | Status at `1e51dcf` | Evidence |
|---|---|---|---|
| CT-01…CT-18 | Low/Info | carried, verified fixed; **no regression** | Blob identity recomputed at both tags; 727 green; referee/Amber spot re-breaks |
| CT-19…CT-21 | Info | converted v0.7.1; carried, no regression | CT-21's guard re-broken → red → green (Blue) |
| CT-22 | Low | **CONVERTED (closed) by execution** | Both halves implemented as named; two independent pins; referee personally re-broke both → red → byte-identical restore → green |
| CT-23 | Info | closed by **written, dated owner acceptance** (ruling 2) | Owner-signed plan §0/§6 (26 Oct 2026) declares notes recorded rather than scheduled; PATCH-0.7.2 §Observations |
| CT-24 | Low | **CONVERTED (closed) by execution** | CM-39; duplicate refused before any explorer call; referee re-broke → red → green |
| CT-25 | Low | **CONVERTED (closed) by execution** for the demonstrated shapes | CM-40/41/42 socket-level pins, three lanes break-and-watched; surviving one-shape variant → CT-33 |
| CT-26 | Info | closed by **written, dated owner acceptance** (ruling 2), record verified accurate | Amber + referee vs live prior-window ledger |

**New findings this cycle (final IDs; severities calibrated by the referee):**

| ID | Sev | Claim | Location @ `1e51dcf` | Why this severity |
|---|---|---|---|---|
| **CT-27** | **Medium — the block's subject (ruling 4)** | Both gate halves read `pending_broadcast_txid`, written only after `broadcast_transaction` returns — a second, differently-reviewed payment submits while the first is in flight (≤ 20 s; demonstrated end-to-end by Red and Orange, re-executed by the referee) | `gui.py:1265-1307`; bound `wallet_service.py:40` | Control weaker than documented (USER-MANUAL step 7 false in the window); below High — no unforgivable act, both payments individually reviewed/signed/consented; above Low — a demonstrated refusal gap, and the prior Low's honest-explorer backstop does not exist for a second payment spending different coins. **Calibration plays no part in the grade** (ruling 4) |
| CT-28 | Info | The CM-38 comment "cannot both submit" is false (concurrent same-payment submits both 200; consensus-idempotent) | `gui.py:1266-1268` | Documentation mismatch |
| CT-29 | Low | Last-recorder-wins on the pending record can stick the pause for the session (restart clears; reachable only via CT-27) | `gui.py:1299-1307` | Availability-only |
| CT-30 | Info | CM-38's inventory row cites only the early half; the in-lock half's marker and independent pin are in no row | `CONTROLS.md:62`; `gui.py:1268` | Inventory coverage (Blue proved the row's test stays green when the in-lock half breaks) |
| CT-31 | Info | The source-archive secret-scan control is untracked in the inventory (CT-07/15 class) | `RELEASE-PROCESS.md:201-210`; `tests/test_secret_scan.py` | Inventory coverage |
| CT-32 | Info | Plan §4/§5 stale `gui.py` citations (one instance corrected by the referee — `:1398-1399` binds) | `plan-v072-SIGNED.md` §4/§5 | Fix-input precision; CT-23's class |
| CT-33 | Low | Pure RST mid-response raises `ConnectionResetError` (OSError), absent from `verify_esplora`'s catch tuple — documented message + stage diagnostic lost for one shape; fail-closed throughout | `network_settings.py:154` | The CT-25 class surviving in one variant |
| CT-34 | Info | `explorer_get`'s bounded read returns truncated bodies as success; callers' format checks demonstrated fail-closed | `wallet_service.py:178-191` | Contract documentation |
| CT-35 | Info | This release window's five failed candidate attempts (run 40397174519 attempts 1–5, all in the DMG job; publish jobs skipped each time) are recorded nowhere; CT-26's class | `RELEASE-HISTORY.md`/`CURRENT-STATUS.md` vs the live run ledger | Audit-record accuracy; nothing published from any failure |

**Lane cannot-determine lists** (reproduced in substance): *Red* — honest-network
window width unmeasured; page scripts relied on as claims; desktop shell read not
executed; real hardware outside the boundary. *Blue* — page-script suites not run;
33 carried rows not individually re-broken; live platform state and published bytes
outside its duties. *Orange* — natural window length not measured against a real
broadcaster; the T-11 "outbound payment" reading flagged for the referee (resolved:
the fail-closed reading governs); the duplicate-`sendrawtransaction` behaviour
verified against Bitcoin semantics, not a live node; four pins broken, the rest
carried. *Copper* — the frozen helper's 157 embedded payload files verified on a
reconstructed copy; no Esplora version handshake exists by design; zip/AppImage
verified as bytes only; no physical device. *Amber* — PATCH-0.7.2.md untouched
(White-only); DSSE cryptography not verified (service trusted); runner-image bytes
(GitHub-operated); Apple-side root cause of the staple flakes unobservable;
re-run-failed-jobs mechanics inferred from timestamps.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.7.2 · 2026-10-26 · reviewed by the ZCode Color Team panel**

## ⛔ BLOCKED — this means: do not treat this revision as review-cleared. The money-path sequencing gate added in this release still has a demonstrated hole, and the framework's rules force the grade down until it is fixed

**Read this first:** this is not a finding that anyone can steal from you, and it is
not a walk-back of the good news — every protection the previous reviews verified
still holds, and the fix your team shipped for the last audit's finding is real and
proven. What this audit found, with a working demonstration repeated by three
independent examiners and the referee, is that the new "wait for confirmation" gate
does not cover the few seconds while a payment's broadcast is still travelling: a
second payment — one you fully reviewed and separately approved on the screen and
your device — can be sent during that window, when the rule the app now documents
says it should refuse it. Two approved payments can then race each other. The fix is
small and exactly known; until it ships and is re-audited, this revision stays
blocked.

## The questions that matter

**Can this app steal or redirect the money?**
No way was found — in any review — to make this app send a transaction the operator
did not review and approve. Every transaction in every demonstration, including both
sides of the flaw found this cycle, was one the operator had reviewed on screen and
approved on their device.

**So what is blocked about it?**
The app now promises: "while a payment is waiting for its first confirmation, the
app refuses a second payment." The promise is true from the moment the first
payment's broadcast comes back — but during the broadcast itself (up to about twenty
seconds, longer only if the network server stalls) the app does not yet count the
first payment as pending, and a second, separately-approved payment can go through.
The examiners proved this three independent times, and the referee ran the
demonstration personally. It is a gap between what the app now promises and what it
does — in a safety feature whose whole job is sequencing your payments.

**Was anything else wrong?**
Small items only: one network-error message that can still be skipped in a rare
disconnection shape (the app still fails safely — nothing is sent); a comment and a
manual sentence that overstate what the new gate covers; inventory and
record-keeping notes. The build pipeline itself was clean: five failed build
attempts during this release (Apple notary flakes and a disk-timing error) published
nothing at all.

**What does the grade mean — and not mean?**
"Blocked" is this framework's mechanical rule: when an examiner proves the code
violates a promise the audit scope froze in writing, the grade is blocked — no
weighing against the clean sections, in neither direction. It is evidence about one
version on one day, not a guarantee. The one thing you must always do yourself:
verify the destination address and amount on your hardware device's own screen,
every time — and while any payment is still confirming, check your wallet before
sending another.

## How this review was done

Several independent AI examiners reviewed the software separately, each with one
job and none seeing the others' work until the end; the rules for what passes and
what fails were locked before anyone looked at the code. The final grade is the
*lowest* score on the team. A different AI model wrote the audit's scope than ran
its panel. The referee re-derived every load-bearing claim personally — including
re-running the attack demonstration — before allowing this report out.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | Steal, redirect, or damage; find any path to the money | No breach demonstrated; found and demonstrated the in-flight window |
| BLUE · The defender | Prove every claimed protection holds, and that its alarm actually rings | Defenses hold — nine alarms personally tripped, all rang |
| ORANGE · The logic specialist | Check the math and rules that must never be wrong | One rule demonstrated violated in a narrow window (the payment-sequencing promise); all other logic proven |
| COPPER · The edge specialist | Attack every connection the app must trust | Edge trust holds — lying, dying, stalling, replaying and substitute servers all refused or safely classified |
| AMBER · The supply inspector | Check how the downloads are built and whether they are what they claim | Chain holds — published bytes match the checked build; five failed builds published nothing |
| WHITE · The referee | Distrust everyone; re-derive the evidence; compute the grade | Re-ran the attack personally; computed the grade from the locked rules: **BLOCKED** |

## The audit trail

**Read this first:** no way was ever found to steal, redirect, or spy on the
operator's Bitcoin. The blocked grade is about a sequencing promise the app now
makes and does not quite keep.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| BLOCKING (open) | The new "wait for confirmation" gate does not cover the seconds while a payment's broadcast is in flight; a second, separately-approved payment can slip out. One small code change closes it; the fix recipe is in the technical report. | CT-27 |
| MINOR IMPROVEMENT (open) | A rare disconnection shape can still skip one error message (app stays fail-safe); a pending record that two racing payments can overwrite. | CT-33, CT-29 |
| HOUSEKEEPING (open) | Comment and manual sentence overstate the gate; inventory rows and plan citations to refresh; this release's five failed build attempts should be recorded like the last cycle's were. | CT-28, CT-30–32, CT-34, CT-35 |
| RESOLVED | The last audit's finding (CT-22) and both hardening items (CT-24, CT-25) are fixed and *proven* fixed by breaking them and watching the alarms ring — confirmed by three examiners and the referee. | CT-22, CT-24, CT-25 |
| RESOLVED | The 21 earlier findings: all carried clean, no regressions. | CT-01…CT-21 |

## What this review does not cover

This grade is about version 0.7.2 exactly, as published on 2026-10-26. Hardware
devices were tested through the app's verification code, not physically; the
Windows and Linux downloads were verified by hash, signature and build attestation;
the width of the in-flight window on a live network was not measured. AI review
complements — it does not replace — a qualified human audit. "Nothing found" means
"nothing found within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.2.md` in the repository |
| The one-page security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.2.md` in the repository |
| The audit rulebook and scorecard | `…colorteam-audit-plan-v0.7.2.md` and `…colorteam-audit-lock-v0.7.2.md` in the repository; the framework at `cjtsh/ai-color-team-audit-framework` |
| Every earlier cycle (unedited) | `audit-history/` in the repository |

---

*Audit performed 2026-10-26 by the ZCode Color Team panel on the public repository
(tag `v0.7.2` = `1e51dcfa45d6f61c83c14aeb1998725fbd705ba9`) and the published
release artifacts only. The grade rules were locked before the audit began and
applied as written; the scope plan was owner-signed (Bitseeker LLC, 26 Oct 2026) and
its hash unchanged from before the first specialist ran to after the last
(`36d30916b2447b2b26cf82353fe478ef543139e3b2856e6b573d496bd03913b4`; the lock was
pre-published by the operator at commit `3331c93`). No credential values, seed
material, or private keys appear in this report. **This revision is graded ⛔
BLOCKED: the audited revision demonstrated a violated invariant in the
payment-sequencing gate; do not treat it as review-cleared for live funds.** An
audit is evidence about one revision on one day, produced by the agents named above
— not a certification of safety, and not a promise about any future version.
Coverage limits are stated above; the surveyor and auditor identities are
declarations, not independent verifications.*

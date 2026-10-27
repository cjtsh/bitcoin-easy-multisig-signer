# ZCode Color Team Audit — Bitcoin Easy Signer v0.7.4 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.4`, commit `9d4d7bb471c80512cac7b7dc6c014855393cac4f`, release published 2026-10-27T12:26:15Z (ten assets, immutable releases live) |
| **Assets declared** | (1) The Bitcoin in the operator's multisig wallet — no transaction signed or broadcast that the operator did not review and approve; (2) signing and CI credentials and the release workflow; (3) the reviewed-transaction integrity chain; (4) release artifact integrity — only the verified candidate's exact bytes publish; (5) wallet privacy. No asset is optional; the ranking orders severity, not attention |
| **Auditor** | ZCode — a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber — one fresh context each, dispatched as one wave) plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness` (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-85510ac1-f0ee-4aeb-9147-8c3148935918` · model `not exposed by the harness` (declared by operator handle `cjtsh`, Bitseeker LLC). *(Correction recorded at publication: the operator's lock originally cited `session-64472385…` — the v0.7.3 plan's §0 session id; the signed v0.7.4 plan's §0 reads `session-85510ac1…` and the lock row now carries the plan's verbatim value. Found by the referee, corrected by the lead before publication.)* |
| **Auditor identity** | Harness `ZCode 3.16.3` · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` — the same auditor seat as the prior cycles, as the lock's auditor row anticipated |
| **Independence** | Surveyor and auditor ran in different sessions: **yes — different runs**. **Different models is NOT established** — it rests on the operator's declaration |
| **Cycle** | `v0.7.4` — a **conversion re-check** of the `v0.6.8` lineage (delta-scoped wave; carried domains carried by verified blob identity, the delta's files re-established in full) |
| **Prior audit** | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.3.md`, SHA-256 `3682471ba8fc37ebfb1f43a8cf0f20487a5ec1bb36c3fbdbebded1e7f174da3d`, grade **⚠️ CONDITIONAL** (held by CT-36 and CT-41) |
| **Original scope plan** | `audit-history/bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — scope carried forward **unchanged**; lead- and referee-verified against the prior plan (`…plan-v0.7.3.md`, SHA-256 `83534f9e…4c`): §2–§3 byte-identical, 31 threat-row titles identical, §5 differs in the surveyor's declared citation refresh (including T-10's evidence now citing real test names — the CT-38 fix) |
| **Verification** | Independently re-derived: ten release assets hash-checked against `SHA256SUMS`; `SHA256SUMS.asc` = Good signature `Bitseeker LLC <release@bitseeker.llc>` (RSA `ACCC2F1C…D6D7`); three Sigstore attestations bind the digests to `9d4d7bb`; DMG app codesign-strict OK, spctl accepted, TeamID `B8G5L7M8TB`, staple valid; suite re-run at the audited revision (**738 tests, OK** on Python 3.12.15, hash-locked deps; CI pins 3.12.10 — recorded; 11/11 page-script suites); the run ledger re-read live (two runs, three attempts; promote attempt 1 failed on the Apple staple with publish jobs skipped — **nothing published from any failure**; attempt 2 published); the referee personally re-broke the 4xx→unknown branch and the unknown-conversion branch (red → byte-identical restore → green), reproduced RED-1's raw-exception boundary, and re-derived the grade from the rubric |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.4.md`, SHA-256 `ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8` before the first agent ran and `ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8` at the end — **equal: the scope never moved**. Owner-signed **Bitseeker LLC, 27 Oct 2026**. The lock was **pre-published by the operator's side** (commit `27d04f6`; locked-at `2026-10-27T12:34:45Z`, before this panel was dispatched); the referee entered the observed end hash |

## The grade: ⚠️ CONDITIONAL — everything else in this cycle is at CLEARED level; the grade is held by two missing alarm tests on one control

**First, what this audit confirmed.** The `v0.7.3` CONDITIONAL's two findings are
**fixed and proven fixed by execution**. CT-36 (the floor-setter): `broadcast_transaction`
now raises a new `BroadcastNotSent` *only* for the five checks that run before any
byte of the transaction is written (unsupported network, missing mainnet opt-in,
unusable size, invalid hex, settings-refused endpoint — `wallet_service.py:102-116`
@ `9d4d7bb`), and **every answer received after the POST — HTTP 4xx included —
raises `BroadcastOutcomeUnknown`** carrying the server's own words as evidence
(`CM-49`); the GUI handler asks the exception type (`CM-46`): only a provable
not-sent refusal leaves the payment retryable, everything else records the payment
as pending-unknown and arms the pause. The exact scenario the last audit
demonstrated — a broadcaster that receives the complete signed bytes and then
answers 400, letting a second payment leave with no pause — **now fails closed**:
Red re-attacked it end-to-end and it is refused; Copper re-verified all ten hostile
server shapes at the wire level; Orange executed 31 boundary cases with the
classification derived before the implementation was read; the referee personally
reverted the 4xx branch to the old classification and watched the pin go red.
CT-41 (the missing alarm) is fixed: the new pin
(`test_a_broadcast_racing_an_in_flight_submit_asks_no_explorer`) fails non-vacuously
when the early half is removed — Blue broke it and the zero-explorer-call assertion
fired, proving the request reached the in-lock half. **The referee rules the
conversion criterion MET BY EXECUTION for both findings (and for CT-37, CT-43,
CT-39, CT-40 beside them). The delta introduced no new Critical or High.**

**What holds the grade now** — two pin-coverage gaps on one control (CM-50, the
not-sent boundary), each with a one-line remedy:

- **CT-47 (Info, binds CONDITIONAL under ruling 1).** CM-50's settings-refusal
  branch (`wallet_service.py:113-116`) is **held by no test that can fail**: no test
  in the suite drives a settings-rejected endpoint through `broadcast_transaction`
  (the referee verified by grep and by execution — the branch is enforced,
  fail-closed, and provably pre-POST). Its regression — raising a plain
  `WalletError`, or deletion → over-pause via the conversion arm — would leave the
  suite green. This is the v0.7.1 CT-21 family verbatim: enforced, backstopped, and
  unalarmed; ruling 1 forbids resolving that ambiguity toward CLEARED.
- **CT-49 (Low, independently sustaining CONDITIONAL under ruling 5).** CM-50's pin
  asserts the exception *class* per input shape but not the checks' *position
  relative to the POST* — the property that makes a `BroadcastNotSent` claim true.
  Position is pinned for the mainnet, size, and hex shapes (`tests/test_money_path_pins.py:223-246`
  assert zero sends) but unpinned for the chain and settings branches. No reachable
  defect exists at this revision (the referee verified all five raise sites precede
  the `Request` construction), but an uncaught regression there is CT-36's exact
  fail-open class. *Remedy:* an alarm-style pin asserting zero socket activity for
  each of the five shapes.

**The exact path to CLEARED** (two one-line tests, then one delta cycle):
(1) a pin driving a settings-rejected URL through `broadcast_transaction` asserting
`BroadcastNotSent`; (2) a pin asserting the no-POST property for the chain and
settings branches (the `tests/test_money_path_pins.py:225-228` pattern, or a socket
counter) — each watched red on a deliberate break before committing. Recommended,
not binding: extend `ReleaseWindowDisclosureTests` to the 0.7.4 row (CT-51).
Everything else this cycle — the conversion, the ledger (44/44 accounted), the
suites, the artifacts, the pipeline — is at CLEARED level, and the report says so
plainly: the grade cannot be sweetened past the two missing pins, and it was not.

## The four questions that matter

1. **Could this software send the operator's Bitcoin somewhere they did not
   approve?** **No — no path to an unforgivable act was demonstrated, in this cycle
   or any of the six before it.** The CT-36 scenario is now fail-closed (re-attacked
   by Red end-to-end and re-executed by the referee); substitution, metadata
   injection, consent bypass, stale payment, duplicate input, and lying-txid all
   held.
2. **Could it leak the wallet's addresses and xpubs?** **No.** Diagnostics remain a
   fixed vocabulary; every refusal and unknown-outcome message was checked — the tx
   hex appears in none of them; the server's own words are capped at 300 characters
   and surfaced as evidence for the operator's own explorer check.
3. **Could a remote party, a dependency, or a local process act invisibly?** **No
   new surface.** The workflow is unchanged this cycle (verified by diff); the
   published bytes are attested to `9d4d7bb`; the promote's attempt 1 failed on the
   Apple staple and **nothing was published from it** — the pipeline's fail-closed
   behaviour held.
4. **What should be fixed first?** **CT-47 and CT-49** — two one-line alarm tests on
   the not-sent boundary, each break-and-watched before committing. That is the
   entire distance to CLEARED.

## The prior audit's findings: 44/44 accounted for — 6 converted by execution, 3 closed by written dated owner acceptance, 35 carried with no regression

The prior report (`v0.7.3`, SHA-256 `3682471b…3d`) carried `CT-01`…`CT-44`. Every ID
is accounted for in the Appendix: `CT-36`, `CT-37`, `CT-41`, `CT-43`, `CT-39`,
`CT-40` — **converted by execution** (multi-lane break-and-watch + the referee's own
re-breaks); `CT-38`, `CT-42`, `CT-44` — closed as recorded notes under **written,
dated owner acceptance** (ruling 2: the owner-signed plan of 27 Oct 2026 declares
the notes recorded rather than scheduled; CT-38's substance verified — this cycle's
plan cites real test names; CT-42's residual re-demonstrated unchanged and
fail-closed; CT-44's sweep re-run green); `CT-01`…`CT-35` — carried with no
regression (blob identity recomputed at both tags; 738 tests green; the referee's
and lanes' spot re-breaks). Nothing dropped; the ledger is a round trip.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (per asset: all five held). Red enumerated the
full input surface and attacked the new classification boundary hardest: eleven
hostile post-POST server shapes (400 with detail, 499, 409 "already in mempool",
302, garbage/short/empty 200, RST, close, dribble, lying txid) — every one lands
unknown with the pause armed; seventeen not-sent shapes — every one provable with
zero network I/O (connection and DNS counters at zero); the `except BaseException`
arm hammered with seven raw exception types — every one converts to unknown and arms
the pause; the exact CT-36 race re-run end-to-end over real sockets — **fails
closed**. CT-36/37 are confirmed converted. Findings: CT-45 (Low — raw
`TypeError`/`AttributeError` for non-contract input types at the function boundary;
proven unreachable through the HTTP surface) and CT-46 (Info —
`KeyboardInterrupt`/`SystemExit` are converted to unknown; embedding ergonomics).

**🔵 Blue — DEFENSES HOLD.** Eleven break-and-watches — every new control (CM-46…50)
and the CT-43 disclosure pin with its negative half, plus three sampled carried
controls — all red → byte-identical restore → green, with the suite green before and
after. The CM-38 alarm pin proved **non-vacuous**: breaking the early half still let
the request reach the in-lock half (the 400 assertions passed), so the pin's red
came from the zero-explorer-call assertion — exactly the discrimination CT-41
required. Two Infos: CT-47 (the settings-refusal branch of CM-50 untested) and CT-48
(CT-43's negative half is static string arithmetic — substance verified by Blue's
own composition).

**🟠 Orange — LOGIC PROVEN** (INV-A″ the corrected outcome classification — derived
*before* implementation reading and matched by 31 executed boundary cases across the
status, body, transport, and exception axes; INV-B′ pause persistence; INV-C′ marker
lifecycle with the new refusal exit; INV-D the carried engine — two invariants
re-derived by execution). The dependency delta is **empty** (shown, not cited —
including `network_settings.py` unchanged and `wallet_service.py`'s only behavioural
delta being the classification). CT-49 (the pin narrower than the invariant — the
referee corrected its width downward and confirmed the substance) and CT-50 (Info —
the CT-42 residual, fail-closed, re-demonstrated). The boundary analysis: all five
`BroadcastNotSent` sites precede the `Request` construction; no post-POST path can
raise it; no pre-POST check raises plain `WalletError`.

**🟤 Copper — EDGE TRUST HOLDS** (seven interfaces, **no findings**). Ten hostile
broadcaster shapes at the wire (every post-POST shape → unknown with pause armed;
exactly one connection per shape; the tx hex appears in no message); all five
pre-POST refusals proven at **zero connections and zero bytes at the server**; the
new unknown-outcome driven end-to-end through the real route (HTTP 409, server's
words in the payload, `/api/status` reports `broadcast_outcome_unknown: true`); the
wrong-genesis refusal demonstrated live during harness bring-up; device edge
re-proven on real bytes (one changed token → refusal); download surface fully
resolved to hash-matching `v0.7.4` assets; published app identity internally
consistent.

**🟡 Amber — CHAIN HOLDS** (twelve links). The workflow is unchanged this cycle
(verified by diff); all five Actions SHA-pinned and version-matched; the source
tarball `diff -r`-matches `git archive 9d4d7bb` exactly; the DSSE attestation
payloads were decoded and bind all ten digests to the two producing runs at
`9d4d7bb`; the promote downloaded and verified the candidate's manifest (five grep
lines read — including `notarize=true`); the run ledger — two runs, three attempts —
reconciled for **both** windows: the 0.7.3 records match the live ledger exactly
(five runs, nine attempts), and this window's records (on `main`, post-release per
the disclosed pattern) match the live ledger too. CT-51 (Info — this window's
disclosure is unpinned and absent at the tag; the pin guards only the 0.7.3 row) and
CT-44's residual restated (46 legacy tags, sweep green).

**⚪ White — PUBLISH.** Every load-bearing claim re-derived personally: the 4xx and
conversion branches re-broken (red → byte-identical restore → green); RED-1's raw
exceptions reproduced at the function boundary; Orange's boundary executions re-run
(409-with-bytes → unknown; pre-POST → `BroadcastNotSent` at zero I/O; all five raise
sites read — all precede the `Request`); Amber's ledger re-pulled and the
disclosure-pin break re-run. One baseline detail CORRECTED (ORANGE-1's zero-POST
assertion is broader than Orange reported — narrowing, not widening, the finding);
one lock defect found and corrected (the Surveyor row cited the prior cycle's
session id; now carries the signed plan's verbatim value — recorded above). The
grade follows from the rulings with the arithmetic shown: conversion gate MET by
execution; ruling 4 does not fire; CLEARED fails only on the "held by a test that
can fail" clause via CT-47 and CT-49 (rulings 1 and 5). Session identifiers:
different runs; models not established. No dissent (a recorded note: CLEARED was
arguable on one reading; ruling 1 and the lineage's own precedents decide otherwise,
and the two one-line pins are the lineage's established answer).

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
  identity** carried by delta-emptiness; **exactly-at-limit size limbs** not
  separately executed (shared raise site).
- **44 carried controls not all freshly broken** (the charter's sampling rule: the
  delta set + three samples, all discriminating).
- **The plan's not-examined list, carried unchanged**: owner machine/account state
  (untested — owner-declared); adversarial firmware; the practice-network second
  source (absent by design, owner ruling); the two retired input workflows beyond
  publish-nothing. Real-Esplora `/outspend` mempool semantics remain open (recorded;
  not load-bearing for the marker).

"No finding" means "none found within this coverage."

## Appendix — findings ledger

**Prior ledger (round trip, ruling 8 — prior report SHA-256 `3682471ba8fc37ebfb1f43a8cf0f20487a5ec1bb36c3fbdbebded1e7f174da3d`):**

| ID | Sev | Status at `9d4d7bb` | Evidence |
|---|---|---|---|
| CT-01…CT-35 | Low/Info | carried, verified fixed; **no regression** | Blob identity recomputed at both tags; 738 green; referee/lane spot re-breaks |
| CT-36 | Med | **CONVERTED (closed) by execution** | The not-sent/unknown split implemented as named; the CT-36 scenario re-attacked end-to-end — fails closed; CM-49 pin re-broken by the referee → red → restore → green |
| CT-37 | Low | **CONVERTED (closed) by execution** | Raw escapes convert to unknown and arm the pause; CM-46 pin re-broken by the referee → red → green |
| CT-38 | Info | closed by **written, dated owner acceptance** (ruling 2) | Owner-signed plan (27 Oct 2026) declares notes recorded rather than scheduled; substance verified — this cycle's plan cites real test names |
| CT-39 | Info | **CONVERTED (closed) by execution** | CM-43's citation now contains the arm (`gui.py:1354`); the inventory test binds it |
| CT-40 | Info | **CONVERTED (closed) by execution** | CM-47/CM-48 rows with markers and pins; Blue watched both red |
| CT-41 | Low | **CONVERTED (closed) by execution** | The new alarm pin fails non-vacuously (Blue's break: zero-explorer assertion fired while the in-lock refusal still passed) |
| CT-42 | Info | closed by **written, dated owner acceptance** (ruling 2); residual re-demonstrated unchanged and fail-closed | Orange's re-demonstration; the plan records it as an accepted residual |
| CT-43 | Low | **CONVERTED (closed) by execution** | The disclosure record matches the live ledger (referee re-pull); the pin breaks red on a removed run id and its negative half discriminates |
| CT-44 | Info | closed by **written, dated owner acceptance** (ruling 2) | Sweep re-run green; 46 legacy tags restated |

**New findings this cycle (final IDs; severities calibrated by the referee):**

| ID | Sev | Claim | Location @ `9d4d7bb` | Why this severity |
|---|---|---|---|---|
| CT-45 | Low | Raw `TypeError`/`AttributeError` for non-contract input types at the engine boundary (pre-POST provable not-sent refusals that are not `BroadcastNotSent`; would over-pause via the conversion arm if ever reached) | `wallet_service.py:102-112` | Proven unreachable through the audited HTTP surface (`gui.py:978` pins `chain`; hex comes from `finalize_multisig` as a str — demonstrated); fail-safe if reached |
| CT-46 | Info | `KeyboardInterrupt`/`SystemExit` in the submit window are converted to unknown (exception type replaced) | `gui.py:1374-1399` | Fail-closed, per the stated invariant; embedding ergonomics |
| **CT-47** | **Info — binds CONDITIONAL (ruling 1)** | CM-50's settings-refusal branch (`validate_esplora_url` → `BroadcastNotSent`) is held by no test that can fail; its regression leaves the suite green | `wallet_service.py:113-116` | Enforced, fail-closed, provably pre-POST (executed at zero I/O) — but the CLEARED clause "held by a test that can fail" binds under ruling 1 (the v0.7.1 CT-21 family) |
| CT-48 | Info | CT-43's negative half is static string arithmetic on an embedded record, not an execution of the pin against it | `tests/test_hardening_pins.py:923-931` | Substance holds (the referee executed the composition; the main pin discriminates) |
| **CT-49** | **Low — independently sustaining CONDITIONAL (ruling 5)** | CM-50's pin asserts the exception class but not the checks' position relative to the POST; position is unpinned for the chain and settings branches — an uncaught regression there is CT-36's fail-open class | `tests/test_wallet_service.py:73-93` vs `wallet_service.py:103,116` | Pin narrower than the invariant (the referee narrowed Orange's report — the zero-POST assertion exists for four other shapes); no reachable defect at this revision; "behaviour right, alarm absent" bound CONDITIONAL as CT-41 last cycle and was discharged by writing the test |
| CT-50 | Info | The CT-42 residual re-demonstrated unchanged (lying-txid pause persists, fail-closed) | `gui.py:1363-1372` | Accepted residual (owner-accepted last cycle); no regression |
| CT-51 | Info | This window's disclosure is unpinned and absent at the tag (the pin guards only the 0.7.3 row); the record on `main` is complete and verified accurate | `RELEASE-HISTORY.md` 0.7.4 row; `CURRENT-STATUS.md` @ `27d04f6` | Record opacity only; the tag structurally predates its release; coverage note per ruling 5 |
| CT-52 | Info | The Apple staple flake recurred (this window's promote attempt 1; also 0.7.2 and 0.7.3) — always fail-closed, publication-delay only | promote run `40500477931` attempt 1 | Restated residual |

**Lane cannot-determine lists** (reproduced in substance): *Red* — no live mainnet
Esplora broadcast (chain-blind inference after the opt-in check); the 20 s budget
not waited out (parameter patched to 1 s in the disposable copy); pre-existing
scratch-lane entries not read. *Blue* — 44 carried controls not freshly broken
(charter sampling); no live 4xx end-to-end against a real broadcaster; White-only
transcripts unread; live platform/artifacts outside its scope. *Orange* —
exactly-at-limit size limbs not separately executed (shared raise site); one
load-related suite flake (clean 738/738 immediately after); loopback-only evidence.
*Copper* — no physical device; one 20 s RST classification explained by its own
harness race (focused probe: 0.01 s); no >20 s stall driven through the GUI route;
explorer implementation identity is chain identity by protocol design. *Amber* —
DSSE signatures not cryptographically verified (service excluded); no rebuild from
source; registry-level dependency identity carried by delta-emptiness; `spctl`
assessment text rested on the lead's Phase 0.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.7.4 · 2026-10-27 · reviewed by the ZCode Color Team panel**

## ⚠️ CONDITIONAL — one missing alarm test away from cleared: the money path, the fix from last cycle, and every earlier promise all verified; what remains is two one-line tests

**Read this first:** no way was found — in this cycle or any of the seven before it —
for this app to steal, redirect, or spy on the operator's Bitcoin. This cycle's
examiners specifically re-attacked last cycle's finding and confirmed it is fixed:
the trick that used to let a second payment slip out behind a lying server now
fails closed, every time, in every shape they could construct.

## The questions that matter

**Can this app steal or redirect the money?**
No. Every attack on the money path — lying devices, forged proofs, lying servers,
racing payments, tampered responses — was refused or safely classified, and the
exact reviewed bytes went out every time an honest path completed.

**So why isn't the grade "cleared" yet?**
Because of how this audit framework earns that word. One of its rules says every
safety behaviour must be held by an alarm that actually rings if the behaviour is
broken. The app's new payment-safety gate has five parts; four have ringing alarms
that the examiners personally tripped. Two alarm-related gaps remain: one of the
five parts has no alarm test at all (the behaviour is verified correct — it was
executed and watched refuse with zero network activity — but nothing fails if the
code were quietly changed later), and the existing alarm doesn't check *where* one
of the checks sits in the code (a future edit could silently move it past the point
where its "nothing was sent" promise is true). Each fix is a one-line test. Until
they land and a re-audit confirms, the honest grade is "conditional."

**Was anything else wrong?**
Small items only: an unexpected-error shape classified the same safe way; this
release's own build history (five workflow runs, three attempts — one failed on
Apple's notary service with nothing published) is accurately recorded on the
development branch but not pinned by an automatic test yet. The pipeline itself was
clean: the one failed attempt published nothing.

**What does the grade mean — and not mean?**
"Conditional" here is unusually strong: the auditors state plainly that everything
else in this cycle is at cleared level. The grade is evidence about one version on
one day, produced by locked rules applied mechanically — not a guarantee. The one
thing you must always do yourself: verify the destination address and amount on
your hardware device's own screen, every time.

## How this review was done

Several independent AI examiners reviewed the software separately, each with one job
and none seeing the others' work until the end; the pass/fail rules were locked
before anyone looked at the code, and the final grade is the *lowest* score on the
team. A different AI model wrote the audit's scope than ran its panel. The referee
re-derived every load-bearing claim personally — including re-breaking two
protections and re-running the boundary tests — before allowing this report out.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | Steal, redirect, or damage; find any path to the money | No breach demonstrated; the last cycle's attack now fails closed in every shape tried |
| BLUE · The defender | Prove every claimed protection holds, and that its alarm actually rings | Defenses hold — eleven alarms personally tripped, all rang; found one part still missing its alarm |
| ORANGE · The logic specialist | Check the math and rules that must never be wrong | The corrected sending rule is proven — 31 boundary cases executed, every one as derived before the code was read |
| COPPER · The edge specialist | Attack every connection the app must trust | Edge trust holds — no findings; every hostile server shape refused or safely classified |
| AMBER · The supply inspector | Check how the downloads are built and whether they are what they claim | Chain holds — published bytes match the checked build exactly; the failed build attempt published nothing |
| WHITE · The referee | Distrust everyone; re-derive the evidence; compute the grade | Re-broke two protections and re-ran the boundary tests personally; computed the grade from the locked rules: **CONDITIONAL** |

## The audit trail

**Read this first:** across all reviews, no way was ever found to steal, redirect,
or spy on the operator's Bitcoin. The items below are about manufacturing discipline
and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| IMPORTANT TO FIX (open) | One part of the payment gate has no alarm test, and the existing alarm doesn't check where a safety check sits in the code — both one-line tests. | CT-47, CT-49 |
| MINOR IMPROVEMENT (open) | A rare unexpected-error shape classified the same safe way (nothing leaves); this release's own build attempts should be pinned by the automatic record test like last cycle's are. | CT-45, CT-43's shape via CT-51 |
| HOUSEKEEPING (open) | Citation and inventory precision; two documented residual behaviours restated for the owner. | CT-38 family, CT-42, CT-44, CT-46, CT-48, CT-52 |
| IMPORTANT TO FIX — RESOLVED | Last audit's two findings: the lying-server gap in the payment gate, and the missing alarm — both fixed and *proven* fixed by breaking them and watching the alarms ring, by multiple examiners and the referee. | CT-36, CT-41 (+ CT-37, CT-39, CT-40, CT-43) |
| HOUSEKEEPING — RESOLVED | Last cycle's three record-keeping notes recorded as promised. | CT-38, CT-42, CT-44 |
| RESOLVED | All 35 earlier findings: carried clean, no regressions. | CT-01…CT-35 |

## What this review does not cover

This grade is about version 0.7.4 exactly, as published on 2026-10-27. Hardware
devices were tested through the app's verification code, not physically; the Windows
and Linux downloads were verified by hash, signature and build attestation; no live
mainnet server was contacted (the server behaviours were simulated byte-accurately
on a loopback). AI review complements — it does not replace — a qualified human
audit. "Nothing found" means "nothing found within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.4.md` in the repository |
| The one-page security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.4.md` in the repository |
| The audit rulebook and scorecard | `…colorteam-audit-plan-v0.7.4.md` and `…colorteam-audit-lock-v0.7.4.md` in the repository; the framework at `cjtsh/ai-color-team-audit-framework` |
| Every earlier cycle (unedited) | `audit-history/` in the repository |

---

*Audit performed 2026-10-27 by the ZCode Color Team panel on the public repository
(tag `v0.7.4` = `9d4d7bb471c80512cac7b7dc6c014855393cac4f`) and the published
release artifacts only. The grade rules were locked before the audit began and
applied as written; the scope plan was owner-signed (Bitseeker LLC, 27 Oct 2026) and
its hash unchanged from before the first specialist ran to after the last
(`ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8`; the lock was
pre-published by the operator at commit `27d04f6`; one provenance correction
recorded above). No credential values, seed material, or private keys appear in
this report. An audit is evidence about one revision on one day, produced by the
agents named above — not a certification of safety, and not a promise about any
future version. Coverage limits are stated above; the surveyor and auditor
identities are declarations, not independent verifications.*

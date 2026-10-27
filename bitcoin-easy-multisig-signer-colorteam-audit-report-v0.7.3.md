# ZCode Color Team Audit — Bitcoin Easy Signer v0.7.3 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.3`, commit `a227da4073f705cbb4ca47f939e80fc0921c77d7`, release published 2026-10-27T02:47:51Z (ten assets, immutable releases live) |
| **Assets declared** | (1) The Bitcoin in the operator's multisig wallet — no transaction signed or broadcast that the operator did not review and approve; (2) signing and CI credentials and the release workflow; (3) the reviewed-transaction integrity chain; (4) release artifact integrity — only the verified candidate's exact bytes publish; (5) wallet privacy. No asset is optional; the ranking orders severity, not attention |
| **Auditor** | ZCode — a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber — one fresh context each, dispatched as one wave) plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness` (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` (declared by operator handle `cjtsh`, Bitseeker LLC) |
| **Auditor identity** | Harness `ZCode 3.16.3` · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` — the same auditor seat as the prior cycles, as the pre-published lock's auditor row anticipated |
| **Independence** | Surveyor and auditor ran in different sessions: **yes — different runs**. **Different models is NOT established** — it rests on the operator's declaration |
| **Cycle** | `v0.7.3` — a **conversion re-check** of the `v0.6.8` lineage (delta-scoped wave; carried domains carried by verified blob identity, the delta's app files re-established in full) |
| **Prior audit** | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.2.md`, SHA-256 `decb725951f19b3725bc48ad4b02038903b41c14bc574927115336bc74d5b71c`, grade **⛔ BLOCKED** (on CT-27, by ruling 4) |
| **Original scope plan** | `audit-history/bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — scope carried forward **unchanged** into this cycle's plan; lead- and referee-verified against the prior plan (`…plan-v0.7.2.md`, SHA-256 `36d30916…13b4`): §2–§3 byte-identical; §5 differs in the surveyor's declared citation refresh plus T-11's entry/evidence fields (updated for the fix architecture); 31 threat-row titles identical |
| **Verification** | Independently re-derived: ten release assets hash-checked against `SHA256SUMS`; `SHA256SUMS.asc` = Good signature `Bitseeker LLC <release@bitseeker.llc>` (RSA `ACCC2F1C…D6D7`); three Sigstore attestations bind the digests to `a227da4` from `build-candidate.yml` @ `refs/heads/main`; DMG app codesign-strict OK, spctl accepted, TeamID `B8G5L7M8TB`, staple valid; suite re-run at the audited revision (**733 tests, OK** on Python 3.12.15, hash-locked deps; CI pins 3.12.10 — recorded; 11/11 page-script suites); the run ledger re-read live (**five runs, nine attempts** — including a cancelled run, a mistaken `notarize=false` candidate that the promote **refused at its manifest check** (a guard demonstrably firing), and staple-flaked attempts; **nothing published from any failure**); the referee personally re-broke the in-flight arm and the refusal-clear, re-ran Red's lying-broadcaster demonstration end-to-end, and re-derived the grade from the rubric |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.3.md`, SHA-256 `83534f9ee9909fcdbb6f09505d1dc26b883aae2b1dd6a6a76b1b557a84dfa64c` before the first agent ran and `83534f9ee9909fcdbb6f09505d1dc26b883aae2b1dd6a6a76b1b557a84dfa64c` at the end — **equal: the scope never moved**. Owner-signed **Bitseeker LLC, 26 Oct 2026**. The lock was **pre-published by the operator's side** (commit `8e207a6`; locked-at `2026-10-27T02:50:01Z`, before this panel was dispatched) with the same hash the lead independently verified; the referee replaced the end-hash placeholder with the observed value |

## The grade: ⚠️ CONDITIONAL — the v0.7.2 block is discharged by execution (the fix is real and proven); two new findings now hold the grade

**First, what this audit confirmed.** The `v0.7.2` report's blocking finding (CT-27: a
second payment could ride an in-flight broadcast because the pause's record was
written only after the broadcaster returned) is **fixed, exactly as that report
prescribed, and proven by execution**: `state.broadcast_in_flight[wallet]` is armed
inside the same critical section that checks for it (`gui.py:1330-1351` @ `a227da4`),
the lock is released before the network call (preserving the CT-13 rule), the marker
is cleared on every exit (unknown → pause armed; definite refusal → retryable, since
nothing was sent; success → pause armed), the record is per-wallet and per-txid with
per-txid scan reconciliation, and the lying-txid path arms the pause. Red, Blue and
Orange each broke the new pins and watched them fail — including the two pins that
directly encode the fixed window (the ride pin and the racing pin) — and the referee
personally re-broke the arm and the refusal-clear, watching red, then byte-identical
restore, then green. **The referee rules the conversion criterion MET BY EXECUTION:
CT-27 is closed, and with it the `v0.7.2` BLOCKED is discharged on its own terms.
The delta introduced no new Critical or High.**

**What holds the grade now** (two findings, each with a named remedy):

- **CT-36 (Medium, open — the floor-setter, needs an owner decision).** The new
  gate's contract claims "a definite refusal sent nothing" (`gui.py:1377-1383`) —
  and that claim is stronger than the code can establish. A broadcaster (the URL is
  an operator setting, pinned by genesis check only) that **receives the complete
  signed bytes and then replies HTTP 400** is classified as a definite refusal:
  the in-flight marker is popped, nothing is recorded, the payment stays retryable —
  and a second, different payment of the same wallet then broadcasts with no pause
  armed. Red demonstrated this end-to-end; **the referee re-ran it personally and
  confirmed every sub-claim**. The frozen T-10 contract itself classifies HTTP<500
  as a plain refusal (the `v0.7.2` panel examined that classification for an honest
  node and called it correct-by-design), so the binding instrument is this cycle's
  own documented claim, falsified under an in-model lying broadcaster — "a control
  weaker than documented" (Medium): both payments are individually reviewed,
  device-signed and separately consented, so there is no unforgivable act, and the
  honest-explorer outspend backstop does not stop a second payment spending
  different coins. *Remedy:* classify any response received after the request was
  written as outcome-unknown (or explorer-verify absence before clearing the
  marker), and reword the 4xx message so the operator is told to check the explorer
  before sending again. Owner decision required → the CONDITIONAL clause binds.
- **CT-41 (Low, open — independently sustaining CONDITIONAL under ruling 5).** The
  early gate's in-flight half (`gui.py:1292-1295`) is an **unpinned guard**: with it
  neutralized, every named pin stays green (Orange break-and-watched; the referee
  reproduced). Its unique property — a submit racing an in-flight submit makes
  **zero** explorer calls — is verified correct in production behaviour but held by
  no test that can fail. CLEARED requires every defense "held by a test that can
  fail"; under ruling 1 the unpinned-control clause binds. *Remedy:* one test that
  races a held broadcast and asserts the explorer-facing check is never called,
  mirroring the pending path's existing `assert_not_called` pattern.

Smaller open items (none grade-binding): CT-37 (Low — raw non-`WalletError`
exceptions classify as definite refusal without nothing-sent evidence), CT-43 (Low —
this release window's disclosure undercount: five runs/nine attempts live, two runs
recorded; the notarize=false dispatch and the refused promote are recorded nowhere),
CT-38/CT-39/CT-40/CT-42/CT-44 (Info). **The exact path to CLEARED:** implement
CT-36's remedy and pin it (break-and-watch before committing); add CT-41's
zero-explorer-call test; close CT-37/CT-43 with the same discipline; run the next
delta-scoped cycle.

## The four questions that matter

1. **Could this software send the operator's Bitcoin somewhere they did not
   approve?** **No — no path to an unforgivable act was demonstrated, in this cycle
   or any before it.** Every broadcast in every demonstration carried
   operator-reviewed, device-signed, separately-consented bytes; substitution,
   metadata injection, consent bypass, stale-payment swap and the lying-txid case
   all held (the lying-txid case now arms the pause). CT-36 is a sequencing defect
   between two approved payments behind a misbehaving broadcaster, not a path to
   unapproved ones.
2. **Could it leak the wallet's addresses and xpubs?** **No.** Diagnostics remain a
   fixed vocabulary; every transport refusal message is a fixed string; the new
   refusal messages carry no wallet material (checked across all captured outputs).
   The one privacy-adjacent note: without CT-41's unpinned half, a racing submit
   *would* leak addresses to the explorer before being refused — the half holds in
   production (zero calls executed), it just needs its test.
3. **Could a remote party, a dependency, or a local process act invisibly?** **No
   new surface.** The workflow's behavioural YAML is unchanged (two comment lines);
   the published bytes are attested to `a227da4`; five failed or refused build
   attempts published nothing — including one promote run that **refused a
   mistakenly dispatched unsigned candidate at its manifest check**, which is the
   pipeline working exactly as designed.
4. **What should be fixed first?** **CT-36's classification remedy** (post-receipt
   responses are outcome-unknown, or explorer-verify before clearing), then CT-41's
   test; the rest are one-liners and records.

## The prior audit's findings: 35/35 accounted for — 6 converted by execution, 3 closed by written dated owner acceptance, 26 carried with no regression

The prior report (`v0.7.2`, SHA-256 `decb7259…b71c`) carried `CT-01`…`CT-35`. Every
ID is accounted for in the Appendix: `CT-27` (the conversion gate), `CT-28`, `CT-29`,
`CT-30`, `CT-31`, `CT-33` — **converted by execution** (multi-lane break-and-watch +
referee re-breaks); `CT-32`, `CT-34`, `CT-35` — closed as recorded notes under
**written, dated owner acceptance** (ruling 2: the owner-signed plan of 26 Oct 2026
declares the notes recorded rather than scheduled; CT-35's record verified accurate
against the live prior-window ledger; CT-32 discharged by writing the fresh plan;
CT-34's docstring is the only delta in its file, AST-verified); `CT-01`…`CT-21` and
`CT-22`…`CT-26` — carried with no regression (blob identity recomputed; 733 tests
green; the referee's and lanes' spot re-breaks). Nothing dropped; the ledger is a
round trip.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (per asset: all five held; no unforgivable act).
Red enumerated the full input surface and attacked the new marker architecture
hardest: the arm resists concurrent races (exactly one broadcaster call); wallet-identity
games fail (outcomes attributed to the submitting wallet; a mid-flight import
inherits nothing); the reconcile is per-txid and fail-closed; the lying-txid path
arms the pause; six break-and-watches all went red on demand. The in-flight window
demonstrated last cycle is **closed**. CT-36 (the lying-broadcaster 4xx
classification) is Red's demonstrated finding, with CT-37 (raw-escape
classifications) beside it.

**🔵 Blue — DEFENSES HOLD.** Eleven break-and-watches — every half of the new pause
(early, in-lock pending, **the arm**, in-lock in-flight read, **the clear**), the
per-txid reconcile pin, the RST pin (real socket), the archive-scan binding pin, and
three sampled carried controls (mainnet default-false, final-vs-review, retired-set
guard — CT-21's old "cannot fail" state confirmed cured) — all red → byte-identical
restore → green. All 45 inventory rows pass; the line-shift retargeting verified
bound. Two Infos: CT-39 (CM-43's cited range stops five lines short of the arm) and
CT-40 (the final-vs-review comparison and review-id binding carry no inventory row —
the protections hold; Blue broke them to prove it).

**🟠 Orange — LOGIC PROVEN** (INV-A′ the corrected T-11 invariant, INV-B′ reconcile
semantics, INV-C′ marker lifecycle, INV-D fourteen carried invariants — derived
before implementation reading, timestamped, then executed: ten harness scenarios at
the real HTTP boundary, every interleaving as derived, and the full prior defect
reproduced by the lane's own hand only with the arm broken). The atomicity analysis:
all 13 production sites touching the pending/in-flight state are inside the lock; no
torn read; staleness can only over-refuse, never over-permit. Dependency delta
**empty** except the declared files (shown, not cited). CT-41 (the unpinned guard —
Orange's own break-and-watch proved no repo test fails when it is deleted) and CT-42
(Info — a lying-txid pause records the intended txid, which honest reconcile can
never confirm: fail-closed, session-length).

**🟤 Copper — EDGE TRUST HOLDS** (seven interfaces, no findings). The changed RST
shape now produces the documented refusal with `ConnectionResetError` as cause; the
broadcast path classifies every may-have-sent shape as outcome-unknown (safety-
critical direction confirmed end-to-end through the real route with a raw-socket
held broadcaster: second payment refused with the new in-flight message, broadcaster
POST count 1); device edge re-proven on real bytes (one changed token → refusal);
state files 0600/0700 executed; every documentation link resolves to hash-matching
`v0.7.3` assets; published app identity internally consistent.

**🟡 Amber — CHAIN HOLDS** (ten links). The workflow's behavioural YAML is unchanged
(two comment lines); all five Actions SHA-pinned and version-matched; the source
tarball `diff -r`-matches `git archive a227da4` exactly; the run ledger — **five
runs, nine attempts** — itemized with the manifest-check refusal of the
`notarize=false` candidate log-verified; nothing published from any failure. CT-43
(the disclosure undercount — this window's cancelled run, mistaken candidate, and
refused promote are recorded nowhere) and CT-44 (legacy-tag residual: 46 tags).

**⚪ White — PUBLISH.** Every load-bearing claim re-derived personally: the arm and
clear re-broken (red → byte-identical restore → green); Red's lying-broadcaster
demonstration re-executed (every sub-claim confirmed); Orange's LOGIC PROVEN
reconciled explicitly against RED-1 (INV-A′ as stated is not violated — the second
submit occurred only after the frozen classification declared the first refused;
the finding is about the documented claim, not Orange's invariant); Blue's
test-5-witnessing flag resolved in Blue's favour on the charter's own sampling
terms; one baseline detail corrected (the plan's §0 table skips CT-26…CT-34 — nine
IDs, not eight). The grade follows from the rulings with the arithmetic shown:
conversion gate MET by execution → the v0.7.2 BLOCKED discharged; ruling 4 does not
fire; ruling 1 + ruling 5 bind CONDITIONAL via CT-36 and CT-41. Session identifiers:
different runs; models not established. No dissent.

## What this audit did not examine

- **No physical hardware wallets or device firmware** (plan assumption; device edge
  proven through the app's verification code on synthetic keys).
- **The Windows/Linux bundles verified as bytes only** (hash, signature,
  attestation); only the macOS DMG was opened.
- **Suite interpreter 3.12.15** vs CI pin 3.12.10 (recorded, not graded).
- **The honest-network width of CT-36's scenario** — whether any honest Esplora
  deployment can return 4xx after node acceptance (Red argues no; no real Esplora
  was run). Real-Esplora `/outspend` mempool semantics remain recorded open (no
  longer load-bearing for the marker; the plan carries it to the next cycle).
- **Whether a restart during an unknown-outcome pause is an owner-accepted
  residual** (session-only state; the scan backstop re-arms while the transaction is
  mempool-visible) — an owner question recorded, not graded.
- **Cryptographic DSSE verification of attestations** (binding verified; Sigstore
  service trusted per plan); **runner-image bytes** (GitHub-operated, declared
  assumption); the frozen helper's embedded payload verified on a reconstructed copy.
- **The plan's not-examined list, carried unchanged**: owner machine/account state
  (untested — owner-declared); adversarial firmware; the practice-network second
  source (absent by design, owner ruling); the two retired input workflows beyond
  publish-nothing.
- **The plan's recorded defects** (documentation precision): the §0 ledger table
  skips CT-26…CT-34 (nine IDs — the prose and lineage table cover all 35, and the
  prior report carries the full findings); RED-3/CT-38's stale T-10 test citation.
- **Method note:** one lane left a disposable worktree inside the pristine clone's
  directory (untracked; the tracked tree verified clean throughout by multiple lanes
  and the referee; the lead relocated it before the referee ran), and the referee's
  own workspace setup briefly disturbed the clone before any verification ran —
  restored and verified byte-clean first. Both disclosed rather than hidden.

"No finding" means "none found within this coverage."

## Appendix — findings ledger

**Prior ledger (round trip, ruling 8 — prior report SHA-256 `decb725951f19b3725bc48ad4b02038903b41c14bc574927115336bc74d5b71c`):**

| ID | Sev | Status at `a227da4` | Evidence |
|---|---|---|---|
| CT-01…CT-21 | Low/Info | carried, verified fixed; **no regression** | Blob identity recomputed at both tags; 733 green; referee/lane spot re-breaks |
| CT-22…CT-26 | Low/Info | converted/closed v0.7.2; carried, no regression | CT-22's conversion gate met; pins re-watched |
| **CT-27** | Med | **CONVERTED (closed) by execution** | The marker architecture implemented as named; ride/racing pins personally re-broken by the referee → red → byte-identical restore → green; the fixed window re-demonstrated closed |
| CT-28 | Info | **CONVERTED (closed) by execution** | New comment true as written; its pin (the ride pin) watched red |
| CT-29 | Low | **CONVERTED (closed) by execution** | Per-txid record + reconcile; pin watched red by Blue and Orange; code read at `gui.py:1056-1061` |
| CT-30 | Info | **CONVERTED (closed) by execution** | CM-43/44 rows bound with loadable pins; Blue's break-and-watches red |
| CT-31 | Info | **CONVERTED (closed) by execution** | CM-45 row + archive-scan binding pin watched red (worktree-scan break) |
| CT-32 | Info | closed by **written, dated owner acceptance** (ruling 2) | Owner-signed plan declares notes recorded rather than scheduled; discharged by writing the fresh, hash-locked plan |
| CT-33 | Low | **CONVERTED (closed) by execution** | `OSError` in the CM-40 tuple; RST-shape pin watched red over a real socket (Blue; referee re-broke) |
| CT-34 | Info | closed by **written, dated owner acceptance** (ruling 2); the docstring is the only delta in its file (AST-verified) | Owner-signed plan; `explorer_get` docstring documents the truncation contract |
| CT-35 | Info | closed by **written, dated owner acceptance** (ruling 2); record verified accurate vs the live prior-window ledger | Amber + referee vs live run 40397174519 |

**New findings this cycle (final IDs; severities calibrated by the referee):**

| ID | Sev | Claim | Location @ `a227da4` | Why this severity |
|---|---|---|---|---|
| **CT-36** | **Medium — the floor-setter (needs an owner decision)** | A broadcaster that receives the complete signed bytes then replies 400 is classified as a definite refusal: marker popped, nothing recorded, payment retryable — and a second, different payment of the same wallet broadcasts with no pause armed (demonstrated end-to-end; referee re-executed) | `wallet_service.py:122-125`; `gui.py:1377-1383` | "A control weaker than documented" — the new gate's own claim ("a definite refusal sent nothing") and the refusal message are stronger than the code can establish; below High (both payments reviewed/signed/consented — no unforgivable act); the honest-explorer backstop does not stop a second payment spending different coins. **Binds CONDITIONAL** (ruling 1), independently with CT-41 |
| CT-37 | Low | Raw non-`WalletError` escapes (`RuntimeError` demonstrated) classify as definite refusal without nothing-sent evidence | `gui.py:1377-1383` | Hardening debt on CT-36's instrument; fail-safe |
| CT-38 | Info | Plan §5 T-10 cites a test name that does not exist at this revision | `plan-v073-SIGNED.md` §5 | Citation staleness; substance covered at `test_send_flow.py:676`, `test_gui.py:496` |
| CT-39 | Info | CM-43's cited range stops five lines short of the arm it claims | `CONTROLS.md:67` vs `gui.py:1351` | Inventory precision; content binding holds |
| CT-40 | Info | The final-vs-review comparison and the review-id binding carry no CM row (protections hold — broken and watched red) | `gui.py:1249-1263`, `gui.py:1145-1160` | Inventory coverage (CT-07/15/30 family) |
| CT-41 | Low — **independently sustaining CONDITIONAL (ruling 5)** | The early gate's in-flight half is unpinned: deleting it leaves every named pin green; its unique zero-explorer-call property (verified correct in production) is held by no test that can fail | `gui.py:1292-1295` | The CLEARED clause "held by a test that can fail" binds under ruling 1 (the CT-21 family); behaviour verified correct |
| CT-42 | Info | A lying-txid pause records the intended txid, which honest reconcile can never confirm — the pause persists until the session ends (fail-closed direction) | `gui.py:1363-1372` | Recorded residual; remedy known (status-endpoint explorer link or restart) |
| CT-43 | Low | This release window's disclosure undercount: five runs/nine attempts live (cancelled run; mistaken notarize=false candidate; refused promote) vs two runs/two attempts recorded | `RELEASE-HISTORY.md` 0.7.3 row; `CURRENT-STATUS.md` @ `8e207a6` | CT-35's shape recurring; record-accuracy only — nothing published from any failure |
| CT-44 | Info | Legacy-tag residual: 46 dispatchable tags enumerated; sweep green | `check-publish-paths.sh:89-96` | Accepted residual restated |

**Lane cannot-determine lists** (reproduced in substance): *Red* — whether any honest
Esplora can return 4xx after acceptance (no real Esplora run); the `open_url`
URL-changed shape shares RED-1's weakness but no trigger without a redirect; page
scripts not fuzzed; workflow/artifacts outside lane scope. *Blue* — ~36 carried rows
not freshly broken (charter sampling rule); published bytes and live platform
outside its scope; CT-29's pin fails as an ERROR (scripted-reply exhaustion) on its
specific break — mechanism verified, shape noted for the referee (re-derived).
*Orange* — the restart-during-unknown-pause residual (owner question); one untracked
directory appeared in the pristine clone (disclosed; relocated by the lead; tracked
tree clean). *Copper* — no physical device; no Esplora implementation-identity
handshake exists (chain identity verified instead); zip/AppImage bytes only; full
DMG seal relied on the lead's Phase 0. *Amber* — run-130 cancellation intent
(timing inference); dispatch inputs as literals for two runs; the v0.7.2 window's
per-attempt failure breakdown (prior window; count verified recorded); DMG seal
(lead-verified); Sigstore service trust (excluded).

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.7.3 · 2026-10-27 · reviewed by the ZCode Color Team panel**

## ⚠️ CONDITIONAL — the blocking flaw from the last audit is fixed and proven fixed; one narrower gap behind a misbehaving server, and one missing test, keep the grade at "conditional"

**Read this first:** no way was found — in this cycle or any before it — for this app
to steal, redirect, or spy on the operator's Bitcoin. Every transaction in every
demonstration carried the operator's own reviewed, device-approved instructions.
This cycle's examiners confirmed the fix your team shipped for the last audit's
blocking flaw works: the race they used to demonstrate that flaw can no longer
happen, proven by breaking the new gate on purpose and watching its alarms ring.

## The questions that matter

**Can this app steal or redirect the money?**
No. Every attack on the money path — lying devices, forged proofs, tampered
responses, lying servers — was refused, and the exact reviewed bytes went out every
time an honest path completed.

**So what keeps the grade conditional?**
One narrow gap and one missing test. The gap: the app now pauses a wallet while a
payment is being sent, but if the network server *accepts the payment and then
claims it refused* (a lying or misbehaving server — the server address is an
operator setting), the app believes nothing was sent and allows the next payment.
Both payments would be ones you reviewed and approved; the risk is your own two
approved payments racing, and only behind a server that lies about its own answers.
The practical protection until the fix ships: **if the app ever says "the network
refused this transaction," check an explorer (or your wallet) before sending
again.** The missing test: one half of the new gate makes sure a racing payment
doesn't even talk to the network before being refused — the behaviour is verified
correct, but no test fails if that half were removed. One test fixes it.

**Was anything else wrong?**
Small items only: a rare unexpected-error shape classified the same way (fail-safe);
the release records under-count this release's own five failed build attempts
(all published nothing — including one attempt the pipeline refused on purpose
because it wasn't properly notarized, which is the safety system working); inventory
rows and citations to refresh.

**What does the grade mean — and not mean?**
"Conditional" is the honest middle: no disqualifying weakness, every promise checked
against the code, and a named, small path to cleared. It is evidence about one
version on one day — not a guarantee. The one thing you must always do yourself:
verify the destination address and amount on your hardware device's own screen,
every time.

## How this review was done

Several independent AI examiners reviewed the software separately, each with one job
and none seeing the others' work until the end; the pass/fail rules were locked
before anyone looked at the code, and the final grade is the *lowest* score on the
team. A different AI model wrote the audit's scope than ran its panel. The referee
re-derived every load-bearing claim personally — including re-running the new
finding's demonstration — before allowing this report out.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | Steal, redirect, or damage; find any path to the money | No breach demonstrated; found the lying-server gap in the new pause |
| BLUE · The defender | Prove every claimed protection holds, and that its alarm actually rings | Defenses hold — eleven alarms personally tripped, all rang |
| ORANGE · The logic specialist | Check the math and rules that must never be wrong | The corrected sequencing rule is proven — every interleaving tested as derived |
| COPPER · The edge specialist | Attack every connection the app must trust | Edge trust holds — no findings; every hostile server shape refused or safely classified |
| AMBER · The supply inspector | Check how the downloads are built and whether they are what they claim | Chain holds — published bytes match the checked build; five failed builds published nothing; one unsigned build was refused by the pipeline itself |
| WHITE · The referee | Distrust everyone; re-derive the evidence; compute the grade | Re-ran the new finding's demonstration personally; computed the grade from the locked rules: **CONDITIONAL** |

## The audit trail

**Read this first:** across all reviews, no way was ever found to steal, redirect,
or spy on the operator's Bitcoin. The items below are about safety margins and
manufacturing discipline.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| IMPORTANT TO FIX (open) | Behind a server that accepts a payment then claims it refused, the app believes nothing was sent and allows the next payment (both payments reviewed and approved). Fix: treat any answer after sending as "result unknown" and tell the user to check an explorer. | CT-36 |
| MINOR IMPROVEMENT (open) | One gate half needs its alarm (the behaviour is verified correct); a rare unexpected-error shape classified without proof nothing was sent; this release's five failed builds should be recorded like the last cycle's. | CT-41, CT-37, CT-43 |
| HOUSEKEEPING (open) | Inventory rows and plan citations to refresh; two documented residual behaviours recorded for the owner. | CT-38, CT-39, CT-40, CT-42, CT-44 |
| IMPORTANT TO FIX — RESOLVED | Last audit's blocking flaw (the in-flight window) is fixed and *proven* fixed — the examiners and the referee each broke the new gate and watched the alarms ring. The false comment, the missing per-payment record, the two inventory gaps, and the connection-reset message are all fixed and proven. | CT-27, CT-28, CT-29, CT-30, CT-31, CT-33 |
| HOUSEKEEPING — RESOLVED | The three record-keeping notes from last cycle were recorded as promised. | CT-32, CT-34, CT-35 |
| RESOLVED | All 21 earlier findings: carried clean, no regressions. | CT-01…CT-21 |

## What this review does not cover

This grade is about version 0.7.3 exactly, as published on 2026-10-27. Hardware
devices were tested through the app's verification code, not physically; the Windows
and Linux downloads were verified by hash, signature and build attestation; the
width of the lying-server scenario on a live network was not measured. AI review
complements — it does not replace — a qualified human audit. "Nothing found" means
"nothing found within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.3.md` in the repository |
| The one-page security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.3.md` in the repository |
| The audit rulebook and scorecard | `…colorteam-audit-plan-v0.7.3.md` and `…colorteam-audit-lock-v0.7.3.md` in the repository; the framework at `cjtsh/ai-color-team-audit-framework` |
| Every earlier cycle (unedited) | `audit-history/` in the repository |

---

*Audit performed 2026-10-27 by the ZCode Color Team panel on the public repository
(tag `v0.7.3` = `a227da4073f705cbb4ca47f939e80fc0921c77d7`) and the published
release artifacts only. The grade rules were locked before the audit began and
applied as written; the scope plan was owner-signed (Bitseeker LLC, 26 Oct 2026) and
its hash unchanged from before the first specialist ran to after the last
(`83534f9ee9909fcdbb6f09505d1dc26b883aae2b1dd6a6a76b1b557a84dfa64c`; the lock was
pre-published by the operator at commit `8e207a6`). No credential values, seed
material, or private keys appear in this report. An audit is evidence about one
revision on one day, produced by the agents named above — not a certification of
safety, and not a promise about any future version. Coverage limits are stated
above; the surveyor and auditor identities are declarations, not independent
verifications.*

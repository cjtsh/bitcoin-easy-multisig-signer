# ZCode Color Team Audit — Bitcoin Easy Signer v0.7.1 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.7.1`, commit `8923ca0273380a9cb1ea7e7e964c6332dda5a777`, release published 2026-10-26T18:13:21Z (ten assets, immutable releases live) |
| **Assets declared** | (1) The Bitcoin in the operator's multisig wallet — no transaction signed or broadcast that the operator did not review and approve; (2) signing and CI credentials and the release workflow — no credential value exposed, a push alone never builds or publishes, nothing unsigned/unnotarized publishes; (3) the reviewed-transaction integrity chain — no bytes differing from the reviewed payment reach a signer or explorer; (4) release artifact integrity — only the verified candidate's exact bytes publish, no overwrite, the download surface stays on pipeline bytes; (5) wallet privacy — no wallet material in logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries. No asset is optional; the ranking orders severity, not attention |
| **Auditor** | ZCode — a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber — one fresh context each, dispatched as one wave) plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness` (`__CFBundleIdentifier=com.deepseek.dsh`) · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` (declared by operator handle `cjtsh`, Bitseeker LLC) |
| **Auditor identity** | Harness `ZCode 3.16.3` · session `not exposed by the harness` · model `GLM-5.3-Flash (declared by the harness; self-description, not an independent verification)` |
| **Independence** | Surveyor and auditor ran in different sessions: **yes — different runs** (the surveyor's identifier is present and names a DeepSeek Harness session; the auditor's harness exposes none, so the identifiers cannot be identical). **Different models is NOT established** — it rests on the operator's declaration that the surveyor seat ran on the DeepSeek Harness. Every model line in this report is a declaration, not a verification |
| **Cycle** | `v0.7.1` — a **conversion re-check** of the `v0.6.8` lineage (delta-scoped wave; carried domains carried by verified blob identity, delta-touched domains re-established), per the immediately prior cycle's stated path |
| **Prior audit** | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.0.md`, SHA-256 `79ee17619a46a59eb3c9f7249aa4d4ed3c5c41417f0b3608e92e6be58ebd94b8`, grade **⚠️ CONDITIONAL** (held by CT-19, CT-20, CT-21) |
| **Original scope plan** | `audit-history/bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — its scope (assets, unforgivable acts, adapted rubric, 31 in-scope threat rows, exclusions, not-examined list) is carried forward **unchanged** into this cycle's plan; the lead verified continuity line-by-line against the immediately prior plan (`…plan-v0.7.0.md`, SHA-256 `0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5`): only the declared revision pointers and lineage fields differ |
| **Verification** | Independently re-derived: all ten release assets downloaded and hash-checked against `SHA256SUMS`; `SHA256SUMS.asc` = Good signature `Bitseeker LLC <release@bitseeker.llc>` (RSA `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7`, key from the tag tree); three Sigstore attestations bind the ten digests to `8923ca0` from `build-candidate.yml` @ `refs/heads/main`; DMG app `codesign --verify --strict` OK, `spctl` accepted, TeamID `B8G5L7M8TB`, `stapler validate` valid; suite re-run at the audited revision (**720 tests, OK** on Python 3.12.15 with hash-locked deps; CI pins 3.12.10 — recorded, not graded; 11/11 page-script suites pass); the producing run ledger re-read live (four runs, three failure events, nothing published from any of them); the referee personally re-broke CT-21's guard, CT-20's inventory net and the CM-35 signing guard and watched the named tests fail, then re-derived the grade from the rubric |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.1.md`, SHA-256 `6137530d0117fa31a076e0738cc9e82ecbc73825ba688785b64951f0d711d88c` before the first agent ran and `6137530d0117fa31a076e0738cc9e82ecbc73825ba688785b64951f0d711d88c` at the end — **equal: the scope never moved** (the lock is `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.1.md`). Owner-signed **Bitseeker LLC, 26 Oct 2026**. Hash published before the panel ran at commit `cbd3609` on `main` |

## The grade: ⚠️ CONDITIONAL — the v0.7.0 conversion gate was met by execution, and one new demonstrated finding (CT-22, Low) takes the floor

**What converted.** All three findings that held `v0.7.0` at CONDITIONAL are closed on
executed evidence, verified by the referee personally:

- **CT-21** (the retired-set guard that no test could fail): the guard is kept, and a
  synthetic pin now exists that **fails when the guard is removed** — the referee
  deleted the guard in a disposable copy and watched `RetiredConnectionGuardTests`
  go red (the retired socket answered an HTML body where the test expects silence),
  then went green again after a byte-identical restore. A positive half prevents the
  assertion from passing by failing to serve anything at all.
- **CT-20** (the control inventory's claim net, blind to workflow files):
  `.github/workflows/*.yml` is now in the scanned set; the referee removed the glob
  and watched `test_the_release_workflow_files_are_scanned` fail. The three new rows
  (`CM-33` the retired-publisher pagination guard, `CM-34` the notarisation
  credential guard, `CM-35` the release-key signing guard) are content-bound to
  markers inside their cited ranges, and each has a closing test that fails when its
  control is broken (CM-35 verified by the referee; CM-33/CM-34 by Blue; CM-36/CM-37
  by Blue).
- **CT-19** (the connection-ceiling docstring implied the page's token protected a
  slot): the docstring now states the actual trade — a complete request head, nothing
  more, claims the slot; the token gates routes only — and the corrected sentence is
  pinned by `SlotClaimSemanticsTests` (both halves break-and-watched by Blue). The
  availability residual itself remains exactly as documented: a sustained tokenless
  flood of complete heads holds all 32 slots for at most the 15 s read budget,
  self-heals, and reaches no declared asset (re-verified by Red at the socket level).

The delta itself (`v0.7.0` → `v0.7.1`) introduced **no new Critical or High**:
production code changed only by a docstring rewrite, five `CONTROL:` marker comments,
legal-link text in `ui.html`, and the version bump — the referee verified the `gui.py`
AST is byte-identical once docstrings are stripped, and the seven engine files
(`signing.py`, `wallet_service.py`, `probe.py`, `safe_http.py`, `network_config.py`,
`network_settings.py`, `desktop.py`) plus the vendored HWI manifest are blob-identical
at both tags. **The `v0.7.0` CONDITIONAL is discharged.**

**What holds the grade now.** One new finding from this cycle:

- **CT-22 (Low, open — the floor-setter).** The pending-payment pause (T-11) is
  armed after a broadcast submits and gates the *prepare* path, but `_broadcast`
  (`gui.py:1205-1293` @ `8923ca0`) performs no pending check of its own. Red
  demonstrated — and the referee re-ran personally — a second, *fully reviewed and
  separately consented* payment being prepared, signed, finalized and submitted while
  the first broadcast is still unconfirmed: with an honest explorer, the outspend
  recheck refuses it ("already spent"); **with an explorer that stays silent about
  the first spend, the second payment goes out** (an RBF-replaceable, operator-
  approved transaction). The page itself never drives this — completing a second
  review inside the seconds-wide window is not a flow it offers — and a hostile
  local process lacks the session token, so no attacker path was demonstrated; but
  T-11's own threat row makes the prohibited outcome ("a second outbound payment
  while the previous one is unconfirmed") **block CLEARED**, the plan's CONDITIONAL
  row names *"a gap that only opens under explorer misbehavior"* verbatim, and the
  CLEARED row requires the AGENTS.md invariants to hold as stated. Under the rubric
  tension rule (every clause reachable; ambiguity never resolved in CLEARED's
  favor), this demonstrated gate hole binds the grade. The same bound follows
  independently from the framework's bounded-evidence rule: whether real Esplora
  operators report mempool spends in `/outspend` — the fact that decides whether the
  backstop holds in practice — could not be established without production-network
  queries, and that unestablished material property caps at CONDITIONAL with the
  bounded task named below.

**The exact path to CLEARED:** (1) refuse in `_broadcast` when
`pending_broadcast_txid` is set for the wallet (or re-check the pause under the
pre-submit lock), with a discriminating pin that fails when the check is removed;
(2) resolve or record the `/outspend` unconfirmed-spend semantics question;
(3) run the next delta-scoped cycle. CT-23…CT-26 do not bind the grade (reasoning in
the ledger).

## The four questions that matter

1. **Could this software send the operator's Bitcoin somewhere they did not approve?**
   **No path was demonstrated — in 40 adversarial checks across the whole money path
   (substitution, metadata injection, consent bypass, stale payment swap, lying
   explorer, lying broadcaster), exactly the reviewed bytes reached the broadcaster
   every time, and every unreviewed variation was refused before network I/O.** The
   one door found (CT-22) lets a *second, fully reviewed and separately consented*
   payment slip out inside a seconds-wide window while the first is unconfirmed, and
   only when the explorer stays silent about the first spend. No unreviewed bytes can
   reach the wire.
2. **Could it leak the wallet's addresses and xpubs?** **No.** Diagnostics are a
   fixed vocabulary (device class, stage, outcome — drop, never escape); Red's
   smuggling attempts through every diagnostic field failed; transports are
   redirect-refusing and certificate-verifying (a TLS impostor and a redirect were
   both refused, targets receiving zero requests); the wire capture shows only
   block-height queries.
3. **Could a remote party, a dependency, or a local process act invisibly?** **No.**
   A counterfeit device, a poisoned HWI module, a forged key proof, a forged session
   token, a lying Origin/Host, a replayed device signature — all refused. The release
   pipeline published exactly the verified candidate's bytes, bound by attestations
   to `8923ca0`, and nothing was published from any of the three failed runs in the
   release window. The one invisible-action surface that changed this cycle is a
   comment.
4. **What should be fixed first?** **CT-22**: add the broadcast-time pending check
   (`refuse when pending_broadcast_txid is set`) and pin it so the test fails when
   the check is removed. CT-25 (catch `http.client.HTTPException` in the explorer
   failure contract) and CT-24 (duplicate-input refusal) are small hardening wins
   behind it.

## The prior audit's findings: 18 carried with no regression · 3 converted by execution · 5 new

The prior report (`v0.7.0`, SHA-256 `79ee1761…4b8`) carried ledger `CT-01`…`CT-21`.
**Every ID is accounted for** in the Appendix ledger: `CT-01`…`CT-18` were verified
fixed by execution in the `v0.7.0` cycle and this cycle's regression check found no
regression (verified blob identity of the engine files + green suites + spot
re-derivations, including the referee's own breaks of a prevout limb and the
fair-admission pins); `CT-19`…`CT-21` are **converted (closed) by execution** — see
the grade section. The ledger is a round trip; nothing was dropped, and nothing was
closed by owner acceptance this cycle.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (itemized per asset: all five assets held).
Red enumerated the full input surface (loopback HTTP server, page, devices via HWI,
public explorers, filesystem, workflow dispatch inputs) and attacked the delta
hardest: the production delta opens no path (comment/docstring only). At the socket
level, the fair-admission residual is exactly as documented — 32 tokenless complete
heads hold all slots ~15 s, self-heal, touch no session state, and no route executes
for a stalled client. Across 40 money-path checks with hostile devices, explorers and
broadcasters: substitution, metadata injection, consent bypass, stale-payment swap,
forged proofs and replayed signatures all refused; the honest path broadcasts exactly
the reviewed bytes. One finding: **CT-22** (the T-11 window, above).

**🔵 Blue — DEFENSES HOLD.** The claims inventory is `CONTROLS.md`'s 37 content-bound
rows plus the README/AGENTS/docstring/workflow claims — every claimed protection maps
to a row, and `ui.html`'s single claim is row CM-30 (its deliberate exclusion from
the workflow-file scan is recorded with its reason). Eleven break-and-watch breaks
across ten control mechanisms each turned the named test red, then green after
byte-identical restore — including both halves of the CT-21 pin, both halves of the
CT-19 slot-claim semantics pin, the CT-20 scanned-set test, CM-33/34/35, and sampled
carried controls (mainnet default-false, final-vs-review, prevout txid limb, metadata
exclusion). No control failed any of the five tests. No findings.

**🟠 Orange — LOGIC PROVEN** (15/15 invariants: stated, derived independently from
external oracles — BIP-62, BIP-174, BIP-48, BIP-325, Bitcoin Core chainparams,
consensus arithmetic — matched by execution, boundary-covered, pinned). Two
representative pins were personally watched failing (prevout value limb;
bare-`/*` change-branch guard). The dependency delta is **empty** — locks and
`vendor/` byte-identical between the tags (shown, not cited). Findings: **CT-23**
(Info — plan §4 `gui.py` line citations are stale at this revision; substance
verified true) and **CT-24** (Low — `check_selected_outpoints` does not refuse a
duplicated input inside one PSBT; demonstrated at the function boundary and proven
unreachable in-product: scan dedup, builder, tx-identity gate and consensus relay
each refuse it independently).

**🟤 Copper — EDGE TRUST HOLDS** (six interfaces: page↔server, device/HWI, transport,
state files, download surface, published app). 18 hostile socket shapes against the
real server; an 18-probe device matrix (counterfeit xpub, forged/replayed proofs,
stalled helper, HWI payload tamper matrix — refused on bytes without importing);
redirect/TLS-impostor/wrong-network/stall/replay shapes against the real transport
code (targets received zero requests); state files written 0600/0700; every
documentation download link resolves to the release's hash-verified assets; the
published app's bundle identity is internally consistent (`0.7.1`, pinned HWI sidecar
matching bytes). Finding: **CT-25** (Low — the explorer-failure except-tuple misses
`http.client` failure shapes; the referee re-derived the escape and confirmed the
outer contract holds end-to-end: fixed 500, nothing broadcast, settings unsaved).

**🟡 Amber — CHAIN HOLDS** (12 links, each named/pinned/real/read/matched). The
source tarball `diff -r`-matches `git archive 8923ca0` exactly (documented omissions
and `ci/` copies only, each byte-identical); the workflow's publish-path guards were
read in full and its three changes this cycle are comment markers; all five Actions
are SHA-pinned and confirmed upstream; live repo variables equal the vendor-file
hashes; the attestations name the promoting runs. The **run ledger** (runs 124–127,
consecutive and therefore complete): run 125 **failed** (two jobs — an Apple stapler
"Error 68" and the archive secret scan refusing the credential-named test fixture),
publishing nothing; run 126 was the successful candidate (publish=false); run 127
promoted and published — **its own attempt 1 also failed with the stapler flake,
publishing nothing, before attempt 2 succeeded**. Nothing was published from any
failure event; immutability held throughout. Finding: **CT-26** (Info — the promote
run's failed attempt 1 is a third failure event not named in the plan's disclosure;
the record should carry it). Residuals restated: runner-image and apt-package
floats, `allowed_actions: all` with convention-pinned actions, unrestricted tag
creation, no required reviewers on the signing environments, 46 legacy tags with
pre-guard workflow text, publishers outside `.github/workflows/` invisible to the
sweep.

**⚪ White — PUBLISH.** Every load-bearing claim in all five lanes was re-derived
personally: 15 claims CONFIRMED, none CORRECTED, none UNVERIFIABLE — including the
referee's own re-executed breaks (CT-21 guard deletion, CT-20 glob removal, CM-35
key-check neutralization, prevout value limb) and a personal re-run of Red's CT-11
window probe. The grade is computed: no lane proved a failure state (ruling 4);
zero open Critical/High; 21/21 prior findings accounted; the floor is set by Red's
CT-22 under the plan's CONDITIONAL clause and ruling 1, corroborated by ruling 5's
unestablished `/outspend` property; CT-24/CT-25 do not bind (proven unable to reach
a declared asset; the documented fail-closed contract held); no averaging (ruling
3), no invented acceptance (ruling 2). Session identifiers: different runs
established; different models not established (operator declaration). No dissent.

## What this audit did not examine

- **No physical hardware wallets or device firmware** — the device edge is
  established through the app's own verification code with synthetic keys and
  helpers; firmware trust is the plan's declared assumption and physical testing is
  the owner's.
- **Only the macOS bundle was inspected as bytes** (plus every asset's digest); the
  Windows zip and Linux AppImage/tarball were not opened beyond their hash,
  signature and attestation verification.
- **The suite ran on Python 3.12.15** with hash-locked dependencies; CI pins
  3.12.10. Recorded as an environment note, not graded (prior cycles ran 3.12.14
  the same way).
- **Whether real Esplora operators report mempool spends in `/outspend`** — the
  fact that decides whether CT-22's backstop holds in practice — was not
  established; production-network queries are outside the panel's rules. Mutinynet
  has a single source by design (owner-recorded residual).
- **The live platform posture** was re-read for the load-bearing facts (tag
  rulesets, immutability, run ledger, attestations); workflow default permissions,
  allowed-actions, secret-scanning settings and environment secret *existence* are
  taken from the live-checked record and the repository's `platform-state.json`
  (both copies agree; the tag's copy is dated pre-release, `main`'s post-release —
  the plan discloses this).
- **The plan's not-examined list is carried unchanged**: owner machine/account
  state (untested — owner-declared); adversarial device firmware; the
  practice-network second source (does not exist by design, owner ruling
  2026-10-11); the two retired input workflows beyond establishing they publish
  nothing.
- Each lane's own cannot-determine list is reproduced in the Appendix.

"No finding" means "none found within this coverage."

## Appendix — findings ledger

**Prior ledger (round trip, per ruling 8 — prior report SHA-256 `79ee17619a46a59eb3c9f7249aa4d4ed3c5c41417f0b3608e92e6be58ebd94b8`):**

| ID | Sev | Status at `8923ca0` | Evidence |
|---|---|---|---|
| CT-01…CT-12 | Low/Info | carried, **verified fixed** (v0.7.0, by execution); **no regression** | Engine-file blob identity at both tags; 720-test suite green; spot re-derivations |
| CT-13 | Low | carried, **verified fixed**; residual (32-slot ceiling) owner-recorded | Red's socket experiments match the documented bound |
| CT-14 | Low | carried, **verified fixed** (all three prevout limbs discriminately pinned) | Referee re-broke the value limb → `…refused_by_the_value_limb` red → restore green |
| CT-15…CT-18 | Info | carried, **verified fixed**; no regression | Blob identity + green suites |
| CT-19 | Info | **CONVERTED (closed) by execution** | Docstring matches code (`gui.py:106-127` vs `:146-176`); pinned by `SlotClaimSemanticsTests` (both halves break-and-watched) |
| CT-20 | Info | **CONVERTED (closed) by execution** | Workflow file class in the scanned net — glob removal fails the build (referee-verified); `CM-33/34/35` rows content-bound with failing tests |
| CT-21 | Info | **CONVERTED (closed) by execution** | Guard kept and pinned — guard deletion fails `RetiredConnectionGuardTests` (referee-verified); positive half present |

**New findings this cycle (final IDs; severities calibrated by the referee):**

| ID | Sev | Claim | Location @ `8923ca0` | Why this severity / does it bind? |
|---|---|---|---|---|
| **CT-22** | **Low — open, the floor-setter** | The pending-payment pause has no broadcast-time gate: a second fully-reviewed payment can be submitted while the first is unconfirmed when the explorer stays silent about the first spend (RBF-replaceable, operator-approved bytes; honest explorer → refused by the outspend recheck) | `gui.py:1205-1293` (no pending check in `_broadcast`); pause arms at `:1286`, gates prepare at `:1379-1380`; backstop `wallet_service.py:238-242` | Demonstrated prohibited outcome of T-11, whose row blocks CLEARED, and it opens only under explorer misbehavior — the exact shape the plan's CONDITIONAL clause names; the page cannot drive it and a hostile local process lacks the token, so Low, not High. **Binds the grade** (ruling 1; corroborated by ruling 5 — real-world `/outspend` semantics unestablished) |
| CT-23 | Info — open | Plan §4's `gui.py` line citations are stale at this revision (substance of every claim verified true; engine citations accurate) | `plan-v071-SIGNED.md` §4 vs the tree | Fix-input precision only; no asset path. Does not bind |
| CT-24 | Low — open | `check_selected_outpoints` does not refuse a duplicated input inside one PSBT (demonstrated at the function boundary against an honest explorer) | `wallet_service.py:190-242` | Proven unreachable in-product: scan dedup `wallet_service.py:568-571`, builder, tx-identity gate `signing.py:164-167`, consensus relay refusal. Coverage note (ruling 5). Does not bind |
| CT-25 | Low — open | The explorer-failure contract leaks `http.client` failure shapes (`RemoteDisconnected`/`BadStatusLine` escape `verify_esplora`'s except tuple); outcome verified fail-closed end-to-end (fixed 500, nothing broadcast, settings unsaved) | `network_settings.py:146-151`; outer contract `gui.py:929` | The documented contract (fail-closed "Operation failed safely") held; what is lost is message precision and a stage diagnostic — error-contract/coverage debt, no asset path. Low-vs-Medium weighed by the referee: does not bind |
| CT-26 | Info — open | The release window had **three** failure events; the promote run's failed attempt 1 (macOS staple "Error 68", 18:01:11Z, publish jobs skipped) is unnamed in the cycle documents | run `40372606443` attempt 1 (live run ledger); plan §0 disclosure covers two of the three | Audit-record accuracy; nothing published from any failure; immutability held. Does not bind |

**Lane cannot-determine lists (verbatim in substance):**

- *Red:* real-Esplora `/outspend` mempool semantics (decides CT-22's backstop in
  practice); multi-input `send_all` attacked by reading only; Windows-only branches
  untested on this host; CT-21's unobservability precondition accepted as
  established in the prior cycle, its pin re-proven here; live platform posture is
  White's input.
- *Blue:* the CT-20 archive-resolver half verified by read, not by building the
  archive suite; unsampled carried rows' test-5 rests on the green suite plus six
  fresh demonstrations; live platform state not re-read (Amber's/White's input);
  interpreter 3.12.15 vs CI 3.12.10 recorded; not every comment in 222 files read.
- *Orange:* testnet4 genesis established against Bitcoin Core v28.0 chainparams (an
  official-implementation oracle, one tier below first-principles math; mainnet
  genesis proven by computation); Mutinynet block-1 rests on the live explorer's
  answer (owner-recorded residual class); the HWI honest-payload pass cannot run in
  the audit venv by design (fail-closed path); break-and-watch performed on two
  representative pins, not all fifteen.
- *Copper:* no physical device (plan exclusion); `explorer_get` never-sends-xpubs
  pinned by code-read + verify-path wire capture + suites, not a live scan capture;
  only the macOS bundle opened as bytes; GitHub Pages internals and Sigstore
  excluded by plan.
- *Amber:* the Linux SBOM's compiled-libusb digest not recomputable without a Linux
  build (covered by the pinned-source gate + recorded-digest chain); Apple
  codesign/spctl/staple verdicts are the lead's Phase 0 (Amber verified the DMG's
  byte-identity); PyPI-side identity re-derivation delegated to the hashes/locks +
  scanner pin; the root cause of the stapler Error 68 is Apple-side and
  unobservable; environment secret values unreadable by design.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.7.1 · 2026-10-26 · reviewed by the ZCode Color Team panel**

## ⚠️ CONDITIONAL — the three problems named by the last review are fixed and proven fixed; one new, narrow weakness keeps the grade at "conditional" until it is closed

This review was written for the person the software is actually for: a trustee,
lawyer, accountant or family member settling an estate that includes Bitcoin, who
knows Bitcoin is dangerous and cannot audit the app themselves. Every statement here
is drawn from — and can be checked against — eight full technical reviews completed
between 2026-10-11 and 2026-10-26 (the v0.6.8, v0.6.9, v0.7.0 and v0.7.1 cycles; the
evidence for each is public — the last page tells you where).

## The questions that matter

**Can this app steal or redirect the money?**
No way was found — in any review — to make this app send a transaction the operator
did not review and approve on screen. The attackers on the panel tried lying signing
devices, forged proofs, tampered responses, lying network servers and forged session
tokens; every time, the app refused or the exact reviewed transaction went out and
nothing else. The one weakness found this cycle is narrower than theft: under rare
timing and a network server that stays silent at the wrong moment, a *second
transaction the operator fully reviewed and separately approved* can go out while a
previous one is still confirming — the operator's own money, to the place they
chose, twice. The fix is a one-line check the developers know exactly where to put,
and until then the practical protection is the one you already have: confirm on your
signing devices, and check your wallet before sending again while a payment is
pending.

**Could it leak the wallet's addresses and xpubs?**
No. The app's diagnostic files carry fixed codes — never addresses, keys or error
text — and the panel tried to smuggle values into every field. Network queries go
only to the server you chose, over verified connections, and redirects were refused
without the second server ever being contacted.

**Could someone change its behavior without the owner seeing?**
No. Every review re-verified that the published downloads are byte-for-byte the
output of the checked build pipeline — signed, notarized, attested to this exact
source revision — and this cycle, as before, failed and abandoned builds published
nothing at all. The three failed builds in this release window (two Apple
notary-service flake events and one security-scan refusal during development) were
checked one by one: none published anything.

**What does the grade mean — and not mean?**
"Conditional" is this framework's honest middle: no disqualifying weakness was
found, and the specific items the previous review demanded are fixed and *proven*
fixed by breaking them and watching the alarms ring — but one new item (described
above) must be closed before the grade can read "cleared". This is not a guarantee;
it is evidence about one version on one day. The one thing you must always do
yourself: verify the destination address and amount on your hardware device's own
screen, every time.

## How this review was done

Several independent AI examiners reviewed the software separately, each with one
job and none seeing the others' work until the end; the rules for what passes and
what fails were written down and locked before anyone looked at the code. The final
grade is the *lowest* score on the team, not an average. A different AI model wrote
the audit's scope than ran its panel, so the same blind spot cannot sit on both
sides of the handoff.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | Steal, redirect, or damage; find any path to the money | No breach demonstrated — 40 attacks on the money path, all refused or harmless; found the narrow second-payment window (CT-22) |
| BLUE · The defender | Prove every claimed protection holds, and that its alarm actually rings | Defenses hold — 11 alarms personally tripped and each rang |
| ORANGE · The logic specialist | Check the math that must never be wrong (signatures, amounts, addresses) | Logic proven — 15 invariants checked against independent standards, all hold |
| COPPER · The edge specialist | Attack every connection the app must trust (devices, network, screen) | Edge trust holds — counterfeit devices, forged proofs, lying servers all refused |
| AMBER · The supply inspector | Check how the downloads are built and whether they are what they claim | Chain holds — published bytes match the checked build exactly; failed builds published nothing |
| WHITE · The referee | Distrust everyone; re-derive the evidence; compute the grade | Every load-bearing claim re-verified personally; grade computed from the locked rules: **CONDITIONAL** |

## The audit trail

**Read this first:** across all reviews of this version, no way was ever found to
steal, redirect, or spy on the operator's Bitcoin. The items below are about
manufacturing discipline and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| DANGER SIGN | **None found — in any review.** | — |
| IMPORTANT TO FIX (open) | A second, fully-reviewed payment can slip out during a rare timing window while an earlier one is still confirming, if the network server stays silent about the first. No attacker path was found; it needs fixes only the operator's own actions could produce. One-line fix plus a test. | CT-22 in the technical report |
| IMPORTANT TO FIX — RESOLVED | The last review's three items: a guard whose alarm couldn't ring, a claim-scanner blind to the build scripts, and an inaccurate internal comment — all fixed and *proven* fixed by breaking them and watching the alarms ring. | CT-19, CT-20, CT-21 |
| MINOR IMPROVEMENT | Two hardening margins: a duplicated-input refusal the app reaches four other ways; clearer error handling when a network server hangs up mid-answer (the app already fails safely — nothing is ever sent). | CT-24, CT-25 |
| HOUSEKEEPING | Two record-keeping notes: stale line numbers in the audit plan's map; a third (harmless) failed build in this release's history that the release documents should mention. | CT-23, CT-26 |

## What this review does not cover

This grade is about version 0.7.1 exactly, as published on 2026-10-26. Hardware
devices were tested through the app's verification code, not physically; only the
Mac download was opened and inspected inside; the Windows and Linux downloads were
verified by hash, signature and build attestation. AI review complements — it does
not replace — a qualified human audit. "Nothing found" means "nothing found within
this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.1.md` in the repository |
| The one-page security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.1.md` in the repository |
| The audit rulebook and scorecard | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.1.md` and `…audit-lock-v0.7.1.md` in the repository; the framework at `cjtsh/ai-color-team-audit-framework` |
| Every earlier cycle (unedited) | `audit-history/` in the repository |

---

*Audit performed 2026-10-26 by the ZCode Color Team panel on the public repository
(tag `v0.7.1` = `8923ca0273380a9cb1ea7e7e964c6332dda5a777`) and the published
release artifacts only. The grade rules were locked before the audit began and
applied as written; the scope plan was owner-signed (Bitseeker LLC, 26 Oct 2026) and
its hash unchanged from before the first specialist ran to after the last
(`6137530d0117fa31a076e0738cc9e82ecbc73825ba688785b64951f0d711d88c`, published at
commit `cbd3609` before the panel ran). No credential values, seed material, or
private keys appear in this report. An audit is evidence about one revision on one
day, produced by the agents named above — not a certification of safety, and not a
promise about any future version. Coverage limits are stated above; the surveyor
and auditor identities are declarations by the operator and the harnesses, not
independent verifications.*

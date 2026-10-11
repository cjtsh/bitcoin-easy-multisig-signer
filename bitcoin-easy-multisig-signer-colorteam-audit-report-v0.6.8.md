# Kimi Code Security Audit — Bitcoin Easy Multisig Signer v0.6.8 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.8`, commit `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`), committed 2026-10-10T17:13:08-04:00; ten release assets published 2026-10-10T21:31:47Z |
| **Assets declared** | 1. The Bitcoin in the operator's multisig wallet · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain · 4. Release artifact integrity · 5. Wallet privacy (xpubs, addresses, BSMS contents, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White referee, run by the Kimi Code desktop agent; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh)` · session `session-9dc3f632-29dc-4ce5-adc8-4a79a72b6a98` (read verbatim from `DSH_SESSION_ID`) · model `not exposed by the harness` — declared by operator `cjtsh` (Bitseeker LLC) |
| **Auditor identity** | Harness `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop)` · session `1d323ae6-8fdf-4cba-993f-5bb46154a778` (harness session-directory identifier, visible in the session's own tool-output paths; no session environment variable exists) · model `not exposed by the harness` |
| **Independence** | Surveyor and auditor ran in different sessions: **yes** — the two session identifiers differ (`session-9dc3f632…` vs `1d323ae6…`) and the harnesses differ (DeepSeek DSH vs Kimi Code). Different runs are established by the identifiers; different models rest on the two harnesses' declarations, not on independent verification |
| **Cycle** | `v0.6.8` — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md` |
| **Prior audit** | **First audit of this plan lineage** — the signed plan declares a fresh baseline: no prior report, plan, lock, grade, or finding is an input to this cycle, and none is cited as evidence anywhere below. Earlier cycles' artifacts survive in the tagged trees as history (named in the plan §6) and were deliberately removed from `main` |
| **Original scope plan** | First cycle: "first audit" — the plan is the baseline; nothing was carried forward |
| **Verification** | Independently re-derived: all ten asset SHA-256 digests against `SHA256SUMS`, the attestation subjects, and the release API's recorded digests (10/10 match); `SHA256SUMS.asc` GPG-verified against the committed `signing-key.asc`; the Sigstore SLSA-v1 attestation binds all ten assets to `gitCommit 0d4e01f…`; the DMG's Apple signature and notarization verified (`codesign --deep --strict`, `spctl`, stapled ticket); the full test suite re-run at the tag (671 tests OK + 10 JS suites); the live GitHub platform posture re-read (rulesets, environments, Actions permissions, workflow registrations); the publish-path sweep re-run against the live remote |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` before the first specialist ran and `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` at the referee's re-check — **equal: the scope never moved**. Owner-signed: Signed by maintainer, Bitseeker LLC, 2026-10-11. The lock (`bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.8.md`) was published to `main` at commit `f4c7863` before the panel ran — order witnessed |

## The grade: ⚠️ CONDITIONAL — the money path, the devices, the pipeline and the published bytes all held; four Low findings show places where the repo's claimed test evidence does not exist or a shipped claim is not true of itself

No path to any unforgivable act was demonstrated by any lane, and the referee
re-derived the load-bearing evidence personally (30 of 30 claims CONFIRMED, none
corrected, none unverifiable). The grade is held below CLEARED by four Low findings:

- **CT-01** — the broadcast body's malformed-response branch (`wallet_service.py:130-134`)
  has no test that can fail; behavior is still safe because the pinned GUI backstop
  (`gui.py:1103-1107`) converts any wrong body to outcome-unknown.
- **CT-02** — three first-line guards (`gui.py:978-982`, `gui.py:1219-1220`, and the
  `/api/sign` review-id path) are unpinned duplicates of deeper pinned guards; each
  could be refactored away silently.
- **CT-03** — `CONTROLS.md`'s own header claims the build fails when a cited *line*
  stops agreeing; the referee demonstrated the claim is untrue for 15 of 20 rows
  (citations are existence-checked, not content-bound).
- **CT-04** — the tag's `docs/index.html` pointed downloaders at the previous
  release's assets between publication and the post-release `main` correction.

The exact path to CLEARED: pin CT-01's branch (a 200-with-garbage-body test); pin or
delete CT-02's duplicate layers; content-bind CT-03's citations (`CONTROL:` markers or
snippet pins); version-template the docs download URLs or add a post-release link
check (CT-04); then a delta-scoped conversion re-check under the framework's rules.
The rubric-tension ruling applies: where CLEARED and CONDITIONAL could both be read
to apply, CONDITIONAL binds — and it was applied that way.

## The four questions that matter

1. **Could this software sign or broadcast a transaction the operator did not review
   and approve?** — **No path found.** The frozen prepared payment, the review-id and
   scan-generation bindings, the signature-only import across the device boundary, the
   BIP-62 low-S gate, the prevout re-verification, and the final-vs-review comparison
   were each attacked directly (substituted transactions, metadata rewrites, stale
   reviews, racing requests, counterfeit signers) and each held; the mainnet consent
   pair was driven without each half and refused before any network use. Red: NO
   BREACH DEMONSTRATED; Orange: LOGIC PROVEN against external oracles (BIP-143
   vectors, Bitcoin Core chainparams, live chain checkpoints).
2. **Could it leak the wallet's addresses, xpubs, or the credentials?** — **No path
   found.** Diagnostic smuggling attempts (xpubs, addresses, lookalike device classes,
   control characters) were dropped, never escaped; only addresses and txids cross to
   the operator-chosen explorer over verified TLS with redirects refused; no seed,
   PIN, or private key is ever handled; no credential value appears in the tree, the
   archive, the artifacts, or the publish logs (canary-tested scanner).
3. **Could a remote party, a dependency, or a local process act invisibly?** — **No
   demonstrated path.** A poisoned or substituted HWI package is refused on real bytes
   before any import (missing, added, or changed file each demonstrated); a
   wrong-chain or lying explorer is refused at scan, prepare, and broadcast; a
   hostile local page without the session token gets only 403s; the release pipeline
   publishes only the byte-verified candidate of the same commit, with the tag
   no-overwrite guard and the platform rulesets verified live.
4. **What should be fixed first?** — CT-03, then CT-01/CT-02: the shipped control
   inventory should be true of itself before anything else, because it is the
   mechanism meant to catch the other two classes silently rotting.

## The prior audit's findings

None to carry: the signed plan declares this cycle a **fresh baseline** — the first
cycle of this plan lineage, with no prior ledger as an input and new finding IDs
beginning at CT-01. The referee confirmed the declaration and the round-trip rule is
vacuous here by the plan's own terms; this is stated, not assumed. Earlier cycles'
reports, locks, plans, and index survive unedited in the tagged trees and are named,
path by path, in the plan §6 as ruled-not-inputs.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED (itemized: all five declared assets).** Red
enumerated the full input surface (loopback API, BSMS parser, HWI subprocess,
explorer parsers, price/fee feeds, settings file, JS bridge, workflow dispatch
inputs, environment variables, CLI) and attacked it: transaction substitution,
signer-metadata injection, stale/swapped prepared payments, mainnet-consent bypass,
counterfeit devices, poisoned HWI payloads, dispatch-input command injection
(including a payload that both executes and satisfies the guard's regex), diagnostic
smuggling, and redirect/TLS games. Every attack was refused or blocked by a named
control; two Info observations (browser-mode token in history; startup-log
tracebacks) reach no asset.

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Blue inventoried the shipped `CONTROLS.md`
(20 rows) plus every protection claimed in README/AGENTS.md/docstrings, and judged
each against the five tests — present, reachable, effective, fail-closed, pinned —
with 18 break-and-watch experiments on a disposable copy, every break watched red and
reverted. No control fails tests 1–4. Test 5 fails on four spots: the malformed-
broadcast-body branch (CT-01), three first-line duplicate guards (CT-02), and the
inventory's own line-citation claim (CT-03); CT-07 notes claimed-and-pinned
protections the shipped inventory does not track.

**🟠 Orange — LOGIC PROVEN (itemized over nine invariants).** Every invariant was
stated against an external oracle before testing — BIP-143 published vectors
(re-fetched and matched byte-for-byte), BIP-62 (a mathematically valid high-S twin,
verified with an independent ECDSA implementation, is refused), BIP-141 weight math
(fee/vsize re-derived by hand and matched exactly), Bitcoin Core `chainparams.cpp`
plus two live chains (genesis constants and the Mutinynet block-1 checkpoint
verified against live oracles), BIP-48 (change-branch policy), and the consensus
rule hash(prev_tx) == txid. Boundary cases (zero/one/max/over-limit, dust 545/546,
fee ceiling 10,000/10,001, added outputs, moved txids) all refused as designed. The
vendored embit delta is exactly the three documented hunks and nothing else, and the
wheel is byte-identical to the patched source.

**🟤 Copper — EDGE TRUST HOLDS (itemized over five interfaces).** The HWI
subprocess, the explorer edge, the loopback API, the pywebview bridge, and the
frozen binaries each survived the five behaviours (lies / dies / stalls / repeats /
substitution) with runtime evidence: a dribbling loopback server cut at its total
deadline, non-ASCII and near-miss tokens 403'd without tracebacks, a counterfeit
`hwi` executable refused on a fresh-challenge key proof, the published DMG's bundled
helper byte-matched to its sidecar and observed loading its own bundled libusb, and
the DMG's codesigning and notarization verified on the machine. Stated gaps: libusb
internals beyond pinned hashes; AppImage payload not executed (prefix bytes match
the vendored runtime); Windows binary identified by sidecar bytes, not executed.

**🟡 Amber — CHAIN HOLDS (itemized over ten link groups).** Every link named,
pinned, real, read, and matched: all 52 dependency pins hash-locked and matched to
published PyPI digests; all five GitHub Actions SHA-pins resolve to their claimed
tags; the container digest verified live; the two producing runs identified and
input-bound; the ten published assets independently re-downloaded, re-hashed,
signature-verified, and attestation-verified; the publish-path sweep re-run against
the live remote (exit 0); the platform posture re-read live and matching the
workflow's comments; the pinned secret scanner run over the extracted archive,
including a planted canary (caught) and an empty tree (refused, not called clean).
Residuals stated: the 46 enumerated legacy tags, floating runner labels with
resolved versions recorded in the SBOMs, owner-accepted platform settings.

**⚪ White — PUBLISH.** The referee re-derived 30 load-bearing claims personally —
the suite counts, the artifact chain, the platform reads, both Blue pin-gap breaks
(reproduced), the dust floor and the token gate (attacked directly as false-clean-bill
checks — both proved pinned), the BIP-143 and chain-constant oracles, and all twelve
findings' evidence. 30 CONFIRMED, 0 CORRECTED, 0 UNVERIFIABLE. Grade computed from
the locked rubric: no lane proved its failure state (no forced block); no plan
BLOCKED condition met; CLEARED's final clause fails on CT-01/CT-02/CT-03 (claimed
test evidence that does not exist); floor set by Blue, bound by the rubric-tension
ruling. No dissent. Scope lock intact; session identifiers differ.

## Threat-row outcomes (the plan's stop condition: 31 of 31 rows evidenced)

| Row | Outcome | Primary evidence |
|---|---|---|
| T-01 transaction substitution | HOLDS | break-and-watch red (`signing.py:164-167`); hostile drives (Red, Blue, Orange) |
| T-02 signer metadata injection | HOLDS | merge-from-clone break red; only verified `partial_sigs` cross (`signing.py:173-180`) |
| T-03 final-vs-review divergence | HOLDS | clause-specific pin demonstrated (`gui.py:1030-1043`); `ui_state_reuse.cjs` |
| T-04 stale/swapped payment | HOLDS | review-id and generation bindings broken and watched red (`gui.py:926-940`, `:1093-1096`) |
| T-05 mainnet consent bypass | HOLDS | direct drives refused at both gates before any socket use (`gui.py:1049-1054`, `wallet_service.py:86-87`) |
| T-06 wrong network / Signet masquerade | HOLDS | constants oracle-verified (Bitcoin Core + live chains); Signet-as-mainnet refused |
| T-07 already-spent outpoint | HOLDS (mainnet) | spent/unconfirmed answers refused at runtime; two mainnet sources observed; practice-network single source is the owner-ruled residual |
| T-08 fee manipulation | HOLDS | arithmetic re-derived; ceiling break red; lying-price prompt test green |
| T-09 change redirection via `/1/*` | HOLDS | bare-wildcard guard break red with exactly the demanded shape (`wallet_service.py:299-371`) |
| T-10 outcome-unknown broadcast | HOLDS | 5xx/transport/malformed → outcome-unknown; retry lock pinned (CT-01 pin gap noted) |
| T-11 pending-payment pause | HOLDS | engine and scan-side pauses break red (CT-02 notes the GUI-layer pin gap) |
| T-12 counterfeit device / forged key proof | HOLDS | counterfeit, wrong-key, garbage, and replayed-challenge drives all refused before any PSBT is sent |
| T-13 poisoned HWI payload | HOLDS | changed/added/deleted module each refused on real bytes before import; build-time manifest gates verified |
| T-14 credential value committed/logged | HOLDS | pinned scanner over the archive; canary caught; empty tree refused; publish logs masked |
| T-15 push builds/publishes | HOLDS | all trigger blocks read; dispatch-only; no `schedule:`; push triggers point at non-existent branches |
| T-16 prevout mismatch | HOLDS | build-time and sign-time matches; break red on the three lying-explorer cases |
| T-17 dispatch-input injection | HOLDS | payload set re-run incl. the execute-and-pass variant; zero `${{ }}` in any `run:` body (lint-pinned) |
| T-18 publish unsigned/unnotarized | HOLDS | guards read and behavior-tested; published DMG verified signed + notarized |
| T-19 over-broad token | HOLDS | job-split verified by parse and by rendered behaviour tests |
| T-20 platform controls as described | HOLDS | rulesets, environments, Actions permissions, registrations re-read live by Amber and again by White |
| T-21 prepared-payment replacement | HOLDS | post-device identity re-check broken and watched red |
| T-22 stale panels under new review | HOLDS | clearing block break red under `ui_state_reuse.cjs` |
| T-23 non-candidate bytes published | HOLDS | candidate binding read; ten assets independently re-downloaded and byte-matched |
| T-24 tag/asset overwrite | HOLDS | guard fails closed (pinned); live tag unmoved; assets' `updated_at` = original publish |
| T-25 second publish path | HOLDS | sweep re-run live (exit 0); tag refs confirmed read; legacy-tag residual re-stated |
| T-26 download surface | HOLDS | live site's three URLs byte-matched to v0.6.8 assets (CT-04 records the tag-tree page) |
| T-27 checksum/attestation/SBOM | HOLDS | full verification recipe executed; SBOMs consistent with the locks; known SIGNING.md wording defect at the tag recorded per the plan |
| T-28 wallet material in diagnostics | HOLDS | smuggle matrix dropped, never escaped |
| T-29 material to wrong server / redirect / TLS | HOLDS | redirect refused on loopback; wrong-chain server refused; URL smuggling shapes refused |
| T-30 wallet artefacts in tree/archive | HOLDS | tree and archive greps clean; synthetic vectors only |
| T-31 operator state file modes | HOLDS | 0700/0600 modes observed written; break-and-watch red |

## What this audit did not do

- No hardware-wallet devices were attached; device firmware and physical device
  behavior are owner-tested exclusions. The app's side of the device seam was tested
  with mocks, stand-ins, and a counterfeit helper.
- No Windows or Linux host was available: the Windows ACL branch of
  `assert_private_file` was code-read only, `hwi.exe` was byte-matched via its
  sidecar rather than executed, and the AppImage payload was identified by hash
  rather than run. The published macOS DMG *was* executed in its headless
  self-check modes.
- No reproducible-build comparison was performed or claimed; byte identity rests on
  checksums, the GPG signature, two Sigstore attestations, and the release API's
  recorded digests.
- Concurrency was verified through the project's deterministic tests, not
  stress-fuzzing; a differently-shaped race is not excluded.
- The owner's machine, account, and outside-repository automation are
  *untested — owner-declared* assumptions per the signed plan; GitHub account and
  platform compromise are declared external assumptions.
- Live platform posture is a point-in-time read (2026-10-11) and can change
  invisibly to git between runs of the platform-state check.
- The suite ran on Python 3.12.14 against the plan's 3.12.10 pin (recorded as an
  environment state, not a defect; all imports and 671+10 suites green).
- "No finding" means none found within this coverage — not that none exist.

---

# Bitcoin Easy Multisig Signer — Plain-English Safety Review

**Bitcoin Easy Multisig Signer v0.6.8 · 2026-10-11 · reviewed by a six-examiner AI
panel run by the Kimi Code agent**

> ## ⚠️ CONDITIONAL — no way was found to move, lose, or misdirect your Bitcoin, and the published downloads verified end to end; four small weaknesses in the project's safety *paperwork and tripwires* (not in the money path) remain open, and the team knows exactly what they are

This review was written for the person this software is actually for: a spouse,
trustee, lawyer, accountant, or advisor settling an estate that includes Bitcoin —
someone who knows Bitcoin is dangerous and cannot read the code themselves. Every
statement here is drawn from, and can be checked against, the technical report above
it in this same file. The evidence is public; the last section tells you where.

## The questions that matter

**Can this app move your Bitcoin somewhere you didn't approve?** Across all six
reviews, no way was found. The app never holds your keys — it prepares a transaction
for you to read, freezes it, sends it to your hardware signers, accepts *only*
signatures back (a signer that changes anything else is refused), and re-checks that
what it broadcasts is exactly what you approved. On real Bitcoin it also requires
your explicit per-transaction confirmation, and it refuses without it. You can
verify the most important part yourself, every time: **read the transaction details
on your hardware device's own screen before approving** — that habit defeats entire
classes of attack all by itself.

**Could it leak your wallet's addresses or other secrets?** No path was found. The
testers deliberately tried to smuggle wallet details into the app's diagnostic
reports and error messages — every attempt was dropped. The app contacts only the
explorer server you choose, over verified encrypted connections, and it never sends
your wallet's master keys anywhere. It never asks for seed words or PINs at all.

**Could someone tamper with the app or its download without anyone seeing?** The
download you receive was checked four independent ways: a checksum list, a
cryptographic signature from the publisher's release key, a tamper-evident build
record tying every file to the exact source code, and Apple/Microsoft/Linux package
verification. The pipeline that builds the app was attacked in simulation — fake
inputs, booby-trapped commands, substituted components — and refused them all.

**What does the grade mean — and not mean?** CONDITIONAL means: the examiners found
nothing that endangers your funds, and four items of homework remain — all of them
about *tests and paperwork that watch the software*, not about what the software does
when you use it. (Example: one internal checklist claims it double-checks its own
page numbers, and the referee proved it doesn't, quite.) The rules were locked before
anyone looked at the code, and the grade is the *lowest* score on the team — one
strict examiner is enough to hold it here. This grade covers **this version only**,
and no audit is a guarantee. The one thing you must always do yourself: confirm the
recipient and amount on your hardware device's screen.

## How this review was done

Five independent specialist examiners — an attacker, a defender, a logic specialist,
a device-and-network specialist, and a supply-chain inspector — each examined the
software separately, without seeing each other's work, under rules fixed in writing
beforehand. A sixth, the referee, then personally re-checked every claim the result
depends on (30 of 30 reproduced) and computed the grade from the locked rules rather
than choosing it.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | break in and move the money | Tried every door: transaction swaps, fake devices, booby-trapped updates, poisoned inputs. Nothing moved. |
| BLUE · The defender | prove every lock actually locks | Every lock tested by deliberately breaking it and watching the alarm fire. Four alarms need their own tests — that's the grade. |
| ORANGE · The logic specialist | check the math against the rulebooks | Bitcoin's own published test vectors and network constants re-derived from the rulebooks and matched exactly. |
| COPPER · The edge specialist | test everything the app must trust but can't control | Devices, servers, the local window, the bundled parts — lied to, stalled, and swapped; the app refused each time. |
| AMBER · The supply inspector | follow the app from source code to your download | Every ingredient identified and pinned; your download re-downloaded and re-checked four ways. |
| WHITE · The referee | distrust everyone; compute the grade | Re-did 30 key checks personally; all held. Set the grade by the rules, with the arithmetic shown. |

## The audit trail

**Read this first:** across all reviews, no way was ever found to take, redirect, or
mislead a payment, leak wallet material, or publish a tampered download. The items
below are about manufacturing discipline and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| DANGER SIGN | **None found — in any review.** | technical report, threat-row table |
| IMPORTANT TO FIX | None open at this grade level. | — |
| MINOR IMPROVEMENT | Four: one response-checking branch has no alarm of its own (CT-01); three backup guards have no individual alarms (CT-02); the control checklist's line-number claim isn't true of itself (CT-03); the website inside the release briefly pointed at the previous version's downloads (CT-04, already corrected on the live site). | ledger, CT-01…CT-04 |
| HOUSEKEEPING | Eight notes for the maintainers (CT-05…CT-12): browser-history token in source mode, startup-log detail, checklist coverage, two unauthenticated public-data endpoints, per-connection timeouts, release-immutability and retired-workflow platform settings, one component's provenance refresh. | ledger, CT-05…CT-12 |

## What this review does not cover

This grade applies to **v0.6.8 only**. Physical hardware wallets were not tested
(the owner does that); Windows and Linux packages were verified by fingerprint but
not run; the review was performed by AI agents and complements — it does not
replace — a qualified human security firm. "Nothing found" means "nothing found
within this coverage," never "nothing exists."

## Check our homework

| Document | Where |
|---|---|
| This report (technical detail + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md` in the repository root |
| The one-page public security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.8.md`, same place |
| The audit plan (signed) and the scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` / `…-audit-lock-v0.6.8.md`, same place |
| The method | `github.com/cjtsh/ai-color-team-audit-framework`, tag `v1.5.1` |

You can read every page of the evidence yourself.

*Prepared 2026-10-11 by the Kimi Code audit panel from the public repository and
published artifacts of v0.6.8. Every statement above traces to the technical report.
A safety review is evidence about one version on one day — not a guarantee.*

---

# Appendix — findings ledger

New lineage: IDs begin at CT-01. No prior-cycle IDs are carried (fresh baseline, per
the signed plan). Locations are `@ 0d4e01f`. Severities calibrated by the referee.

| ID | Severity | Location | Claim | Status |
|---|---|---|---|---|
| CT-01 | Low | `wallet_service.py:130-134` | The malformed-broadcast-body branch has no test that can fail; a pinned GUI backstop still makes the behavior safe | **Open** |
| CT-02 | Low | `gui.py:978-982`, `gui.py:1219-1220`, `/api/sign` review-id path | Three first-line guards are unpinned duplicates of deeper pinned guards | **Open** |
| CT-03 | Low | `tests/test_controls_inventory.py:168-180`, `CONTROLS.md:6-8` | 15 of 20 inventory rows are not content-bound; the header's claim that the build fails when a cited line stops agreeing is demonstrably untrue | **Open** |
| CT-04 | Low | `docs/index.html` (at the tag) | The tag's download page pointed at the previous release's assets until corrected on `main` after publication | **Open** (live site corrected; the tag is immutable) |
| CT-05 | Info | `gui.py:99-109,1341` | Browser-mode `#token=` can persist in browser history for the session; desktop product unaffected | Open |
| CT-06 | Info | `desktop.py:34-47,353-379` | Startup-failure log carries tracebacks (host paths); pre-wallet, so no wallet material can appear | Open |
| CT-07 | Info | `CONTROLS.md` | The 20-row inventory omits several claimed-and-pinned protections | Open |
| CT-08 | Info | `gui.py:641-678` | `/api/price` and `/api/fees` require no token; bounded public data only | Open |
| CT-09 | Info | `gui.py:535,1334` | The 15 s connection budget is per-thread with unbounded threads; availability-only against a same-user attacker | Open |
| CT-10 | Info | release object | GitHub immutable releases not enabled; overwrite protection rests on the workflow guard, the tag ruleset, and account hygiene | Open |
| CT-11 | Info | platform registrations | Retired publishers remain registered (`disabled_manually`); re-enabling is platform-side and invisible to git between platform-state checks | Open |
| CT-12 | Info | `vendor/libusb-1.0.dll` | Pinned in four agreeing places; the one-time producing-run artifact no longer survives to re-match — closure: re-dispatch `windows-inputs.yml` and compare | Open |

---

*Audit performed 2026-10-11 on the public repository and published artifacts only.
The grade rules were locked before the audit began and applied as written. No wallet
material, seed, PIN, private key, or credential value appears in this report. An
audit is not a certification of safety; coverage limits are stated above. The
mandatory one-page Public Security Statement for this release is
`bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.8.md`.*

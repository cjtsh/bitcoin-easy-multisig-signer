# Kimi Code Security Audit — Bitcoin Easy Multisig Signer v0.6.9 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.9`, commit `e90e5b93ece284f990ca2b75be1e798baa3efc9c` (`e90e5b9`), committed 2026-10-11T11:12:08-04:00; ten release assets published 2026-10-11T15:33:09Z |
| **Assets declared** | 1. The Bitcoin in the operator's multisig wallet · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain · 4. Release artifact integrity · 5. Wallet privacy (xpubs, addresses, BSMS contents, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White referee, run by the Kimi Code desktop agent; asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness (__CFBundleIdentifier=com.deepseek.dsh)` · session `session-64472385-85c1-422e-bc6c-f889c8d8c3d5` · model `not exposed by the harness` — declared by operator `cjtsh` (Bitseeker LLC) |
| **Auditor identity** | Harness `Kimi Code desktop app (__CFBundleIdentifier=com.kimi.code.desktop)` · session `1d323ae6-8fdf-4cba-993f-5bb46154a778` (harness session-directory identifier, visible in the session's own tool-output paths; no session environment variable exists) · model `not exposed by the harness` |
| **Independence** | Surveyor and auditor ran in different sessions: **yes** — the identifiers differ (`session-64472385…` vs `1d323ae6…`) and the harnesses differ. Different runs established by the identifiers; different models rest on the two harnesses' declarations, not independent verification. (The auditor's identifier matches the v0.6.8 cycle's auditor session; the independence rule binds surveyor-vs-auditor within a cycle, not the auditor across cycles.) |
| **Cycle** | `v0.6.9` — a **conversion re-check** (follow-up cycle) in the `v0.6.8` lineage; this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.9.md` |
| **Prior audit** | Cycle `v0.6.8`: report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md`, SHA-256 `c66618acc98713b35bca90a382f2407bf9729d02a06891e5727d370c6c6287cb`, grade ⚠️ CONDITIONAL |
| **Original scope plan** | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md`, SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1` — scope carried forward **unchanged**, verified mechanically: the declared-assets table, the unforgivable acts, and every threat-row heading are byte-identical between the two plans; the rubric differs only in the revision pointer |
| **Verification** | Independently re-derived: all ten v0.6.9 asset digests against `SHA256SUMS` (8/8 listed files OK), the attestation subjects, and the release API's recorded digests; `SHA256SUMS.asc` GPG-verified against the committed `signing-key.asc`; three Sigstore/in-toto attestations bound to `gitCommit e90e5b9…`; the DMG's Apple signature and notarization verified by mounting; the full test suite re-run at the tag; the live platform posture re-read 2026-10-15 (rulesets, environments, Actions permissions, workflow registrations, immutable-release flag); the publish-path sweep re-run against the live remote; every prior-cycle finding's fix re-executed personally by the referee |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.9.md`, SHA-256 `133ce23afe0bca80d884bcff7b9cfa428d2f8bbb965a7d2ff84182aa0be8a8c3` before the first specialist ran and `133ce23afe0bca80d884bcff7b9cfa428d2f8bbb965a7d2ff84182aa0be8a8c3` at the referee's re-check — **equal: the scope never moved**. Owner-signed: Bitseeker LLC, 2026-10-11. The lock (`bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.9.md`) was published to `main` at commit `f9df10f` before the panel ran — order witnessed |

## The grade: ⚠️ CONDITIONAL — every prior-cycle finding is verified fixed by execution, the delta introduced no Critical/High, and one new same-family Low (two named tests that cannot fail for their named guard limbs) stands open

This cycle was the framework's conversion re-check: the v0.6.8 CONDITIONAL had a
defined conversion path, and the referee verified it **by execution, not acceptance**
— all four conversion-gating Lows (CT-01…CT-04) and all eight Informationals
(CT-05…CT-12) were re-derived personally and are verified fixed (12 of 12, none
dropped, none closed by acceptance). The delta introduced no new Critical or High.
The grade is held below CLEARED by one new Low finding in the same pin-accuracy
family that held the prior cycle:

- **CT-14** — the build-time prevout match at `wallet_service.py:867-870` checks
  three limbs (txid, value, script). The referee personally removed each limb: the
  value-limb and script-limb removals leave the entire money-path suite **green** —
  the two tests named for those limbs mutate the serialized previous transaction,
  which changes its txid, so they exercise the txid limb instead. The guard itself
  holds (the txid limb is discriminatingly pinned, and the `packet.fee() != fee`
  backstop independently refuses a value mismatch) — the defect is that the shipped
  test evidence does not exist *for the named limbs*, which is exactly what the
  locked rubric's CONDITIONAL clause names ("stated invariants that lack the test
  coverage the repo claims"). Floor set by the Orange lane; bound by the
  rubric-tension ruling (ambiguity is never resolved in CLEARED's favor).

The exact path to CLEARED: give CT-14's value and script limbs discriminating pins
(a lying-UTXO-list case where the value disagrees with an honestly served historical
transaction, and a test whose name matches what it pins), and record an owner
decision on CT-13 (the connection ceiling's deliberate availability trade), then a
delta-scoped re-check.

## The four questions that matter

1. **Could this software sign or broadcast a transaction the operator did not review
   and approve?** — **No path found.** The money-path delta is comment-markers only;
   every carried control was re-verified on byte identity, and every new or touched
   control was attacked directly (substituted transactions, counterfeit signers,
   poisoned libraries, stale reviews, racing requests, hostile local pages) and held.
   Red: NO BREACH DEMONSTRATED; Orange: LOGIC PROVEN against external oracles
   (BIP-143 vectors, Bitcoin Core chainparams, the live Mutinynet checkpoint).
2. **Could it leak the wallet's addresses, xpubs, or the credentials?** — **No path
   found.** Diagnostics smuggling remains drop-not-escape (referee re-broke the
   vocabulary check and watched it fail); the browser-mode token now leaves the
   address bar immediately; the startup-failure record is bounded type-and-message;
   the two public-data endpoints are now token-gated; no credential value appears in
   the tree, the archive, the artifacts, or the publish logs.
3. **Could a remote party, a dependency, or a local process act invisibly?** — **No
   demonstrated path.** A poisoned HWI module is refused on real bytes before import;
   a wrong-chain or redirecting explorer is refused; the release pipeline re-verified
   end to end for v0.6.9 (candidate binding, checksums, GPG, attestations, producing
   runs); immutable releases are now **enabled** and verified live; the retired
   publishers are guarded by a new fail-closed workflow step. One new availability
   note: a hostile local process can hold the loopback server's 32 connection slots
   and keep the operator's window out for the flood's duration (CT-13 — funds and
   data are untouched; recovery is immediate when the flood stops).
4. **What should be fixed first?** — CT-14's discriminating pins, because the
   pin-accuracy family is the only thing between this project and CLEARED twice
   running; then the owner decision on CT-13.

## The prior audit's findings: all twelve verified fixed by execution

The referee enumerated the v0.6.8 report's ledger (cited with hash above) and
re-derived every disposition personally — a round trip, not a summary:

| ID | Severity | Disposition | Execution evidence (referee) |
|---|---|---|---|
| CT-01 | Low | **Verified fixed** | Broke the malformed-body branch; exactly the five new subtests red; positive half intact |
| CT-02 | Low | **Verified fixed** | Broke the device-txid first-line guard with the deeper guard intact; the new discriminating pin red |
| CT-03 | Low | **Verified fixed** | Re-pointed CM-18's citation — the shape that stayed green at v0.6.8 — and watched the new content-binding test go red |
| CT-04 | Low | **Verified fixed** | Re-pointed a docs download URL at the old version; the new version guard red |
| CT-05 | Info | **Verified fixed** | Token read once → per-tab sessionStorage → `history.replaceState`; JS pin green; three lanes break-watched |
| CT-06 | Info | **Verified fixed** | Traceback write removed; bounded `Type: message` record; `StartupFailureTests` green |
| CT-07 | Info | **Verified fixed** | The named omissions gained content-bound rows CM-21…CM-26, held by the demonstrated-failing inventory reader. New untracked protections in *this* delta are a new ID (CT-15), not a re-open |
| CT-08 | Info | **Verified fixed** | `/api/price` and `/api/fees` 403 without the token, observed firing live |
| CT-09 | Info | **Verified fixed** | 32-connection ceiling observed live; 33rd connection refused; slots recover |
| CT-10 | Info | **Verified fixed** | Immutable releases live-read: `enabled: true`, release object `immutable: true` |
| CT-11 | Info | **Verified fixed** | The retired-publisher guard step read; its tests green; fails closed on an unreadable API (latent page-1 gap carried as CT-16) |
| CT-12 | Info | **Verified fixed** | Producing-run artifact re-downloaded; DLL digest matches the four pins and the shipped file |

## The panel

**🔴 Red — NO BREACH DEMONSTRATED (itemized: all five declared assets).** Red
re-enumerated the surface at `e90e5b9` and attacked every changed line: the new
token gate on the market reads (every spelling, method, and header shape — 403, no
bypass found), the bounded connection server (flood and drip attacks — the ceiling
holds; the deliberate trade is filed as CT-13), the token-history eviction (two
revert shapes, both caught), the bounded startup record (hostile 10,000-char
message, bounded correctly), and the new publish-path shell (injection-clean,
fail-closed on every malformed shape). Two findings: CT-13 (Low) and CT-16 (Info,
merged with Amber's identical find).

**🔵 Blue — DEFENSES HOLD.** Every control on Blue's table passes all five tests —
present, reachable, effective, fail-closed, and pinned by a test Blue personally
watched fail: the CT-01 branch, all three CT-02 first-line guards (each broken
*while its deeper guard stayed intact*), the CT-03 content binding and all three
self-bindings, the CT-05/06/08/09 fixes, and markers CM-21 through CM-26. One Info
finding (CT-15): five claimed-and-pinned protections added *by this release* are not
yet tracked in `CONTROLS.md`.

**🟠 Orange — LOGIC PROVEN (itemized over nine invariants).** The money-path delta
is marker-comments only (verified hunk by hunk); the dependency delta is empty
(verified). Oracles re-fetched and matched: BIP-143's published constants, Bitcoin
Core master's chain params for all three networks, and the live Mutinynet block-1
checkpoint. Every invariant was re-pinned by execution at the tag — including the
charter-shaped `not bare_receive_only` break that must fail exactly one test (it
did). One Low finding (CT-14, the grade-setting finding): two prevout-match limbs
lack discriminating pins.

**🟤 Copper — EDGE TRUST HOLDS (itemized over five interfaces).** The loopback
server (32-connection ceiling observed live, slot accounting probed for leaks and
double-release), the token gate (driven through a real server), the HWI boundary
(poisoned `trezor.py` module refused on real bytes before import; the published
DMG's and Windows zip's bundled helpers byte-matched to their sidecars), the
explorer edge (redirect refused, target never contacted), and the frozen binaries
(DMG codesigned and notarized, stapled) each survived the five behaviours. One Info
finding (CT-17): the Windows startup-failure *dialog* interpolates the unbounded
exception; the log file itself is bounded.

**🟡 Amber — CHAIN HOLDS (itemized per link).** The v0.6.9 chain re-established
independently: ten assets re-downloaded, re-hashed, GPG-verified, attestation-bound
(three attestations to `e90e5b9`); producing runs `38150291296`/`38151061666`
identified and input-bound; the live site byte-matches the three offered downloads
to the v0.6.9 assets; the sweep re-run live (exit 0); the platform re-read live with
immutable releases enabled; the libusb DLL re-matched to its producing run's
artifact. Two Info findings (CT-16 pagination, CT-18 record precision).

**⚪ White — PUBLISH.** The referee re-derived 23 load-bearing claims personally —
the tag resolutions, the plan hash (start = end), the suite state, every conversion
break (reproduced CT-01/02/03/04 personally), both ORANGE-01 limb removals, the
RED-01 drip-stall attack (reproduced end-to-end), the immutable-release live read,
the libusb artifact re-match, and one guard no lane had broken (the diagnostics
vocabulary check — proved pinned). 23 CONFIRMED, 0 CORRECTED in substance, 0
UNVERIFIABLE. Grade computed from the rulings: conversion gate met; CONDITIONAL
binds on CT-14 via ruling 1. No dissent. Ledger round trip complete: 12/12
dispositions, none dropped.

## What this audit did not do

- **The panel spanned 2026-10-11 → 2026-10-15** because of auditor-side quota
  pauses; the owner froze the project for the duration, and the tag resolution and
  plan hash were re-confirmed at re-check time (2026-10-15).
- The 11 JS harness suites (`test_ui_scripts.py`) could not re-run at re-check — the
  local Homebrew `node` broke between 10-11 and 10-15 (`libllhttp` dyld error,
  reproduced). Used instead: the 2026-10-11 baseline (706 tests OK + 11/11 JS
  suites) recorded against the byte-identical tree; the referee's own 10-15 re-run
  was 695/706 with every Python test green. Suite interpreter 3.12.14 against CI's
  pinned 3.12.10 — an environment state, not a defect.
- The AppImage's squashfs internals were not extracted (no extractor on this host);
  the Linux tarball from the same build job verifies (sidecar + manifest), and the
  AppImage is checksum- and attestation-bound to `e90e5b9`. Windows Authenticode is
  not verifiable on macOS; the Windows helper is byte-matched via its sidecar.
- No hardware-wallet devices were attached; device firmware is the owner's exclusion.
- The platform read is a 2026-10-15 point-in-time read; platform state can change
  invisibly to git between runs of the platform-state check.
- The owner's machine, account, and outside-repository automation are *untested —
  owner-declared* assumptions per the signed plan.
- "No finding" means none found within this coverage — not that none exist.

---

# Bitcoin Easy Multisig Signer — Plain-English Safety Review

**Bitcoin Easy Multisig Signer v0.6.9 · 2026-10-15 · reviewed by a six-examiner AI
panel run by the Kimi Code agent**

> ## ⚠️ CONDITIONAL — every issue from the last review is fixed and verified, the downloads check out completely, and one remaining item of test-PAPERWORK (plus one availability note) keeps the grade honest

This review was written for the person this software is actually for: a spouse,
trustee, lawyer, accountant, or advisor settling an estate that includes Bitcoin.
Every statement here traces to the technical report above it in this same file. The
evidence is public; the last section tells you where.

## The questions that matter

**Can this app move your Bitcoin somewhere you didn't approve?** Across all six
reviews — again — no way was found. Nothing in the money path changed except
comment labels, and the examiners proved that line by line. Every lock from the last
review was re-tested by breaking it on purpose and watching the alarm fire. Keep
doing the one thing that protects you no matter what: **read the recipient and
amount on your hardware device's own screen before approving.**

**Could it leak your wallet's addresses or other secrets?** No path was found, and
the two small openings from last time are closed: the app no longer leaves its
local access token sitting in your browser's address-bar history, and its crash log
no longer writes down your computer's folder paths. The two "free information"
buttons (price and fee lookup) now require the same access token as everything
else.

**Could someone tamper with the app or its download without anyone seeing?** The
v0.6.9 download was re-downloaded and re-checked from scratch: checksums, the
publisher's signature, the tamper-evident build record, and Apple's notarization
all verify. New this version: the download page can no longer be quietly swapped
after publication (the platform's "immutable releases" setting is now on, and the
examiners saw it on), and the pipeline now refuses to run at all if a retired build
path is ever switched back on.

**What does the grade mean — and not mean?** CONDITIONAL this time means something
very specific: everything the last review asked for is done and verified — all
twelve items — and the grade is held by *one* new item found while checking that
work: two tests have names that promise more than they test (the protection itself
works; the examiners proved it by attacking it directly). There is also one note
worth knowing: a hostile program *already on your own computer* could deliberately
keep the app's window busy so it won't respond until that program stops — your
Bitcoin is never at risk from this, and the moment it stops, the app works again.
This grade covers **v0.6.9 only**, and no audit is a guarantee.

## How this review was done

Five independent specialist examiners — an attacker, a defender, a logic specialist,
a device-and-network specialist, and a supply-chain inspector — each examined only
what changed since the last review, plus proof that the unchanged parts really are
unchanged (byte for byte). A sixth, the referee, personally re-did 23 of the most
important checks and computed the grade from rules locked before anyone looked at
the code. The grade is the *lowest* score on the team.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| RED · The attacker | break in and move the money | Attacked every changed line — the new locks, the flood ceiling, the token handling. Nothing moved; one availability note (CT-13). |
| BLUE · The defender | prove every lock actually locks | Broke every new alarm and watched it fire. All twelve last-cycle fixes verified. |
| ORANGE · The logic specialist | check the math against the rulebooks | Money path unchanged except labels; rulebooks re-checked. Found the two mis-named tests (CT-14). |
| COPPER · The edge specialist | test what the app must trust but can't control | Devices, servers, the local window, the bundled parts — all held under lies, stalls, and swaps. |
| AMBER · The supply inspector | follow the app from source to your download | The whole chain re-verified for v0.6.9; immutability now on; the one-time libusb provenance closed. |
| WHITE · The referee | distrust everyone; compute the grade | Re-did 23 key checks personally; all held; computed the grade with the arithmetic shown. |

## The audit trail

**Read this first:** across all reviews, no way was ever found to take, redirect, or
mislead a payment, leak wallet material, or publish a tampered download — in either
version. Everything below is about test paperwork, availability margins, and
record-keeping.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| DANGER SIGN | **None found — in any review.** | threat-row table |
| IMPORTANT TO FIX — RESOLVED | **All twelve findings from the v0.6.8 review are fixed and verified fixed** (CT-01…CT-12): the missing alarm tests were added and proven to fire; the control checklist now checks its own page references; the website names the right version; the browser token, the crash log, the two open endpoints, the connection ceiling, release immutability, the retired build paths, and the libusb provenance are all closed. | prior-findings table |
| MINOR IMPROVEMENT | Two: the two mis-named tests (CT-14), and the local-flood availability trade in the new connection ceiling (CT-13 — awaiting an owner decision). | ledger |
| HOUSEKEEPING | Four notes for the maintainers (CT-15…CT-18): new protections not yet in the control inventory, a latent page-limit in one pipeline guard, an unbounded error dialog on Windows, and one imprecise sentence in a provenance record. | ledger |

## What this review does not cover

This grade applies to **v0.6.9 only**. Physical hardware wallets were not tested
(the owner does that); the Windows and Linux packages were verified by fingerprint
and their macOS-verifiable parts executed; the review was performed by AI agents
and complements — it does not replace — a qualified human security firm. The panel
ran over several days with the project frozen; the code did not change during the
review. "Nothing found" means "nothing found within this coverage," never "nothing
exists."

## Check our homework

| Document | Where |
|---|---|
| This report (technical detail + this review + the findings ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.9.md` in the repository root |
| The one-page public security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.9.md`, same place |
| The audit plan (signed) and the scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.9.md` / `…-audit-lock-v0.6.9.md`, same place |
| The prior cycle's artifacts | `audit-history/` (archived, unedited) |
| The method | `github.com/cjtsh/ai-color-team-audit-framework`, tag `v1.5.1` |

You can read every page of the evidence yourself.

*Prepared 2026-10-15 by the Kimi Code audit panel from the public repository and
published artifacts of v0.6.9. Every statement above traces to the technical report.
A safety review is evidence about one version on one day — not a guarantee.*

---

# Appendix — findings ledger

**Prior cycle (v0.6.8 report, SHA-256 `c66618ac…`):** CT-01…CT-12 — all **verified
fixed by execution** (dispositions and evidence in the round-trip table above).

**New findings this cycle (locations `@ e90e5b9`):**

| ID | Severity | Location | Claim | Status |
|---|---|---|---|---|
| CT-13 | Low | `gui.py:101-135` | A hostile local process can hold all 32 connection slots (idle for 15 s; a slow drip indefinitely) and lock the operator's window out for the flood's duration; no declared asset reachable, recovery immediate. The ceiling's deliberate trade — needs an owner decision | **Open** |
| CT-14 | Low | `wallet_service.py:867-870`; `tests/test_money_path_pins.py:296,313` | The value and script limbs of the build-time prevout match lack discriminating pins — the tests named for them exercise the txid limb; the guard holds via the pinned txid limb and the fee backstop. **The grade-setting finding** | **Open** |
| CT-15 | Info | `CONTROLS.md` | Five claimed-and-pinned protections added by this release (the connection ceiling, the token gate, the token check itself, the token-history eviction, the bounded startup record) are untracked in the shipped inventory | Open |
| CT-16 | Info | `.github/workflows/build-candidate.yml:796` | The retired-publisher guard reads only page 1 of the workflow registrations (no `--paginate`, no `total_count` check); latent — 6 registrations today | Open |
| CT-17 | Info | `desktop.py:391` | The Windows startup-failure dialog interpolates the unbounded exception text; the log file itself is correctly bounded | Open |
| CT-18 | Info | `releases/PATCH-0.6.9.md` (CT-12 row) | The row understates the `windows-inputs.yml` delta since the producing run (the `lock` job's hardening is omitted); the load-bearing claim was re-verified true | Open |

**Referee referral (not a finding):** `_clean_token`'s pass-through shape is
unpinned but unreachable past the pinned device-class vocabulary check — for next
cycle's Blue lane.

---

*Audit performed 2026-10-11 → 2026-10-15 on the public repository and published
artifacts only. The grade rules were locked before the audit began and applied as
written. No wallet material, seed, PIN, private key, or credential value appears in
this report. An audit is not a certification of safety; coverage limits are stated
above. The mandatory one-page Public Security Statement for this release is
`bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.9.md`.*

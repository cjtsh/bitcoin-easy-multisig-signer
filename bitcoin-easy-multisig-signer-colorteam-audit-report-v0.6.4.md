# Color Team Security Audit — Bitcoin Easy Signer v0.6.4 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.4`, commit `35cdedb150cef6d047c39537324faf1321be3c8d` (the commit the published, signed and notarized macOS DMG was built from); release `v0.6.4` created 2026-10-02 |
| **Assets declared** | 1. The operator's Bitcoin (reviewed-approved transactions only) · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) · 4. Release artifact integrity (only verified candidate bytes for the same commit; no asset ever overwritten) · 5. Wallet privacy (xpubs, addresses, BSMS, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel plus a White referee; asset declaration, charters, and grade rules locked in writing **before** the build was examined (owner-signed plan hashed before the first specialist ran) |
| **Surveyor** | Harness `Kimi Code desktop app` · session `not exposed by the harness` · model `not exposed by the harness` |
| **Auditor identity** | Harness `ZCode desktop app (3.14.4)` · session `not exposed by the harness` · model `zai-api/GLM-5.3` (declared by the harness, not verified) |
| **Independence** | Surveyor and auditor ran in different harnesses as declared; both session identifiers read "not exposed by the harness", so independence **rests on the operator's declaration** (two harnesses, survey ≠ audit model by methodology) |
| **Cycle** | `v0.6.4` — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md` |
| **Prior audit** | First audit under this methodology. The repository's earlier AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) were **excluded as inputs** by the owner's signed plan (independence condition); this ledger is fresh and cites no prior conclusion. |
| **Verification** | Published macOS artifacts re-downloaded and re-hashed against `SHA256SUMS` (all match); DMG code signature, Gatekeeper, and stapled notarization ticket verified (Developer ID: Bitseeker LLC, B8G5L7M8TB); full suite re-run at the tag (261 tests OK, 0 skipped; 9/9 UI DOM tests); referee personally re-derived every load-bearing claim — all CONFIRMED, zero UNVERIFIABLE, one severity/conclusion CORRECTED inside a merge (CT-04) |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.4.md`, SHA-256 `250632959641571e5c769f2590132b349e57b1ce1dc27a6e97b7962b90a47aaf` before the first specialist ran and the same hash at the end — **equal: the scope never moved**. Owner-signed `Bitseeker LLC, 2026-10-05`. Order not witnessed publicly. |

## The grade: ⛔ BLOCKED — unsigned, unverified Windows bytes from an unmerged commit were manually published onto the tagged v0.6.4 release, past every stated gate

The grade is about the **release channel**, not the macOS application. The audited
macOS app at `35cdedb` was examined money-path deep: no path was found, by any lane or
by the referee's independent probes, to sign or broadcast a transaction the operator
did not review, and the macOS build → notarize → publish chain was verified end-to-end
gate-by-gate. The BLOCKED arises because the v0.6.4 release page additionally carries
**Windows assets uploaded at 18:17Z on 2026-10-02 with no workflow run in existence at
that moment** — unsigned bytes built from unmerged branch commit `bb1f630`, attached
with a hand-rewritten checksum file (CT-01, High) — and **Linux assets attached by a
run that ended in failure** from another unmerged commit `53da293` (CT-02, Medium).
Under the owner-locked rubric, "a pipeline able to publish unverified, unsigned, or
notarization-skipping bytes" is a BLOCKED condition, and an actual occurrence is the
strongest proof of ability. A second lane (Copper) independently forced the same floor
by proving its failure state: the source-mode launcher's substituted-library guard
checks for the wrong embit version and therefore guards nothing (CT-04, Medium).

**The shortest path to CLEARED:** (1) remove the Windows and Linux assets from the
v0.6.4 release (or re-publish them, from a merged commit, through the audited
automated gates under their own tag and audit); (2) fix the launcher's embit version
check to the pinned `0.8.2+besa.1`; (3) pin the unpinned on-path controls — above all
`_check_final_review`, whose deletion today leaves all 261 tests green (CT-03), and
the review-id binding (CT-05) and prevout-ownership refusals (CT-15); (4) cut a new
revision and run the next cycle. The rubric's CLEARED conditions were unreachable this
cycle under rulings 1 and 5 regardless, because those unpinned controls sit on the path
to declared assets.

## The four questions that matter

1. **Could this software get the operator to sign or broadcast a transaction they did not approve — recipient, amount, fee, or change altered between review and broadcast?** — **No path found.** Red ran 60+ live adversarial probes against the real loopback API (swapped recipients, inflated amounts, forged/non-wallet/replayed signatures, dropped signatures, rewritten scripts and prevouts, lying broadcaster txids, four race scenarios); every money-path attack was blocked, and the referee independently re-ran the signature-tamper and broadcast-recheck probes with the same results. Orange proved the signature/derivation/encoding logic against outside standards (BIP-143/173/67/48 vectors) — LOGIC PROVEN on all 20 invariants; the vendored embit differs from upstream by exactly its two documented, behavior-preserving edits.
2. **Could it leak the unspeakable thing — xpubs, addresses, wallet activity, or the owner's signing credentials?** — **No leak path found in the audited app.** Amber verified every dependency hash against PyPI (37/37, no squatting), found no credential value anywhere in the repo, artifacts, or visible logs, and verified the vendored binaries' provenance to the byte. Remaining items are bounded hardening (diagnostics tokens are pattern-sanitized rather than class-whitelisted, CT-06; a physically substituted echo device receives the PSBT it is asked to sign, though its signatures are still refused, CT-14).
3. **Could a remote party, a dependency, or a local process act invisibly — alter behavior or bytes without the operator seeing it?** — **Not inside the app: lying explorers produce outcome-unknown refusals, redirects are doubly refused, TLS is always on, and the frozen-payment binding held under every race Red and Copper threw at it. But invisibility is exactly what happened on the release page:** Windows bytes appeared on the tagged release outside every automated gate (CT-01), and the Linux attach came from a run that failed (CT-02). The publication channel, not the application, is where unaudited action occurred.
4. **What should be fixed first?** — In order: CT-01 (Windows assets on v0.6.4), CT-02 (Linux assets), CT-04 (dead embit version guard in `Start Easy Multisig.command`), CT-03 (pin `_check_final_review` with a fail-capable test), then CT-05/CT-15 and the remaining Low/Info items. Every finding below carries its exact location and remedy, written to serve directly as fix-it input.

## The prior audit's findings

This is the first cycle under this methodology, and the owner's signed plan excluded
the repository's earlier AI audit reports as inputs (fresh audit, fresh methodology —
the methodology itself under test as much as the code). This ledger is therefore fresh:
**no prior IDs are carried forward or owed.** That exclusion is a recorded fact of
this audit, not an omission.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (itemized: all five assets held). Red enumerated the full input surface (loopback API + session token, BSMS file, HWI device responses, explorer/fee/price HTTP, settings file, WebView/JS bridge, concurrent requests) and attacked it live with synthetic vectors: hostile BSMS variants, device-response tampering, forged signatures, broadcast-gate bypasses, lying broadcasters, races, diagnostics leakage, redirect/TLS abuse. Every money-path attempt was blocked by a control (BIP-143-verified signatures only, metadata discarded, broadcast re-derives and re-checks everything under lock). Residuals are bounded Lows/Infos (CT-06, CT-18, CT-19, CT-20). Exclusions named per the hop rule: same-user process attacks (machine, not software) and the Windows/Linux release path (not in the audited tree — Amber's lane, where it became CT-01/02).

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Inventory of 39 claimed controls (from `AGENTS.md`, README, RELEASE-PROCESS, the plan, and code comments): all 39 are present, reachable where they matter, effective, and fail-closed — none fails tests 1–4. Break-and-watch pinned 22+ controls red (session token, signature import/verify chain, txid binding, device binding + signing-time identity recheck, explorer-txid mismatch → outcome-unknown, mainnet opt-in at both layers, broadcast lock, outpoint recheck, pending pause, change-path boundary, developer-mode gate, busy-bar ownership, palette, redirect refusal, diagnostics scrub, overwrite refusal, dispatch-only workflow, SBOM provenance, archive allowlist). Six gaps stayed green when broken — worst: `_check_final_review`, the documented final-vs-review backstop, can be deleted with no test failing (CT-03); the review-id binding's apparent pin passes only incidentally because `hwi` is absent from the test venv (CT-05); plus size bounds, diagnostics cap, stored-state revalidation, and the no-retry/`LIBUSB_SHA256` script halves (CT-07–CT-12). Test-0 sweep: nothing missing — every asset-declared protection is claimed somewhere.

**🟠 Orange — LOGIC PROVEN** (20 invariants, itemized; full-scope review — no prior audited version exists to delta against). All three published BIP-143 sighash vectors matched by the vendored embit and cross-verified with an independently written ECDSA implementation; BIP-173 address vectors, BIP-67 sorting, BIP-48/bare-`/*` change policy, amount/fee/dust boundaries, network pins (Mutinynet's block-1 verified live and proven to distinguish it from ordinary Signet), and broadcast semantics all matched their outside oracles. The vendored wheel differs from pinned upstream by exactly the two documented edits, and the nSequence-0 parser fix is correct and behavior-preserving on every reachable path (the app writes `0xFFFFFFFD`). Fourteen break-and-watch pins went red as required. Residuals: coverage debt (CT-15, CT-21) and fail-closed strictness observations (CT-22).

**🟤 Copper — EDGE TRUST BROKEN at the source-mode dependency edge** (5 of 6 interfaces HOLD). The five hostile-behaviour lanes that ship in the product survived Lies/Dies/Stalls/Repeats/Substituted with runtime evidence — a 42-check adversarial battery (fake HWI subprocess + synthetic Esplora driving the real server) passed 42/42; loader experiments with the shipped bytes prove the bundled libusb binding is enforced and any other copy fails closed; shipped digests match the SBOM; the embedded hwi_entry is code-identical to repo source; TLS/redirect refusal and dual-source outpoint checks verified. The breaker: `Start Easy Multisig.command:20` asserts embit `== "0.8.0"` while the lock pins `0.8.2+besa.1` — the claimed substituted-embit guard validates the wrong version, so a stale public-registry 0.8.0 venv passes it and skips the hash-verified install (CT-04; source mode only, the shipped DMG is unaffected). Also: broadcast holds the session lock across explorer I/O (CT-13), device identity is key-material only so a counterfeit echo device receives the full PSBT (CT-14).

**🟡 Amber — CHAIN BROKEN at the Windows and Linux release links** (macOS chain HOLDS end-to-end). Every lock file fully hash-pinned and verified against PyPI (37/37); vendored embit triple and libusb provenance verified to the byte including embedded copies re-hashed inside the published DMG; actions SHA-pinned; candidate run 37008418851 → publish run 37009396873 verified gate-by-gate in the run logs, published macOS bytes identical to candidate bytes. The break is on the release page itself: Windows assets were uploaded manually at 18:17:55Z with no run active, from unmerged commit `bb1f630` (63 files changed vs the tag, including `desktop.py`/`gui.py`), unsigned, with a hand-rewritten sums file, and an interim tag/release `v0.6.4-windows-x64` was created and deleted (CT-01, High); Linux assets came from unmerged commit `53da293` via a run whose attach step itself **failed** mid-publication (CT-02, Medium). Code the owner never merged reached tagged v0.6.4 artifacts without a reviewable version bump — the definition of a broken chain. Plus: release notes rewritten outside any run (CT-16), floating runner images (CT-17), stale build-script comment (CT-24).

**⚪ White — PUBLISH.** Every load-bearing claim re-derived personally (the money-path probes re-run; both Blue breaks re-run and watched staying green with 261 OK each; the embit diff re-extracted and re-hashed; the Windows/Linux run histories pulled from the Actions API with the manifest artifact showing `allow_unsigned=true` from `bb1f630`; baseline hashes, notarization, and suite counts reproduced): **all CONFIRMED, zero UNVERIFIABLE, one severity CORRECTED inside a merge** (Red's "no impact" on the launcher guard superseded by Copper's confirmed stronger reading — CT-04). Scope lock re-hashed: **H_end = H_start — the scope never moved**; the audit is not void. Grade computed, not chosen: floor set by Amber (ruling 4 + the plan's BLOCKED clause 4), independently forced by Copper (ruling 4); rubric-tension resolved so every clause stays reachable; the owner's §9 note about the deliberate docs tail was weighed and **does not accept** manual unsigned publication from unmerged commits (ruling 2 — no invented acceptance); no dissents. Counterfactually, even without the two BROKEN lanes, ruling 5 would have capped this cycle at CONDITIONAL via the unpinned on-path controls (CT-03/05/15) — CLEARED was unreachable this cycle under any reading.

## What this audit did not do

1. **The BLOCKED grade's substance:** the macOS application at the audited revision was examined money-path deep and its build→notarize→publish chain verified end-to-end; the grade arises from the release page tagged v0.6.4 also carrying Windows and Linux bytes never produced by the audited pipeline (unsigned, from unmerged commits, one path entirely outside automation), plus the source-mode launcher defect (CT-04). Both halves are stated plainly.
2. **Windows/Linux application code was not audited** (out of the locked scope — the plan audits the tag). The windows-port (`bb1f630`) and linux-port (`53da293`) deltas are unreviewed-on-main code; users of the Windows/Linux assets must not treat them as covered by this audit, and the Windows sums file was rewritten outside any run.
3. **No real-device interaction** beyond the suite's own bridge check (one real device attached to the host was enumerated only by the suite, in the same envelope as the lead's Phase 0 run); counterfeit-device behavior was established by synthetic emulation only.
4. **Static plus local-dynamic coverage:** the live WebKit window was not driven; mainnet dual-source outpoint checking was exercised at unit level, not through a live mainnet session; notarization was verified post-hoc on the published DMG (codesign/spctl/stapler), not performed by the panel.
5. **Dependency internals out of scope** (hwi 3.2.0, pywebview 6.2.1, requests, certifi, pyyaml, pyinstaller, upstream embit beyond the documented two-edit delta); the vendored libusb dylib is pinned by hash, signature, and SBOM digests but its internals were not reviewed.
6. **GitHub repository variable values** (`LIBUSB_SHA256`, signing identities) are unreadable read-only; their equality with in-script pins is evidenced by runs that passed, not directly verified.
7. **Deleted evidence:** the interim tag/release `v0.6.4-windows-x64` and its assets can no longer be audited; related run artifacts will age out of GitHub retention (~90 days default).
8. **Prior AI audit reports were excluded as inputs** by the owner's signed independence condition; no prior conclusion, grade, or finding was cited. The ledger is fresh.
9. **Independence rests on the operator's declaration** (both session identifiers "not exposed by the harness"; harnesses differ as declared); model names are declarations, never verified facts.
10. **Best-effort, not a guarantee.** The report serves a nontechnical fiduciary reader and the fixing agent; "the operator should have noticed" was treated as a weakness to report, never a mitigation to assume. "No finding" means "none found within this coverage."

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.6.4 · 2026-10-05 · reviewed by a five-specialist Color Team panel with an independent referee (AI audit, framework v1.3.2)**

## ⛔ BLOCKED — but read what that means: the Mac app passed every money-safety test; the FAILURE is on the project's own download page, where Windows and Linux files were posted outside every safety check

This review was written for the person this software is actually for: a spouse, lawyer,
trustee, accountant, or trusted advisor settling an estate that includes Bitcoin, who
knows Bitcoin is dangerous and cannot review the software themselves. Every statement
here is drawn from — and can be checked against — the full technical report above,
completed 2026-10-05 by a five-specialist panel plus a referee, working from rules
locked in writing before anyone looked at the code. The evidence and the rulebook are
public; the last section tells you where.

## The questions that matter

**Can this app get my Bitcoin sent somewhere I didn't approve?**
**No path to that was found — none.** A dedicated attacker-examiner tried more than
sixty ways to trick the app into signing or broadcasting an altered transaction
(swap the recipient, change the amount, forge a signature, replay an old approval,
confuse it with simultaneous requests), and every single one was blocked. A second,
independent examiner re-ran the cruelest of those attacks himself and watched them
fail again. A third examiner proved the underlying signature and address math against
Bitcoin's official published test standards. The protection you can verify yourself:
the app never holds your keys — your hardware wallets do — and it displays the
transaction for your approval on those devices' own screens.

**Could it leak the unspeakable — our addresses, wallet details, the family's holdings pattern?**
**No leak path was found in the app.** The examiners checked what the app writes to
its logs and diagnostics (only fixed codes, never addresses or wallet details), what
it sends over the network (to block explorers, only what the operator chose to ask),
and where its publishing credentials live (nowhere in the public materials). Two
small hardening items remain (noted below), but nothing was found that exposes you.

**Could someone act invisibly — change the software or its downloads without anyone seeing?**
**Inside the app: no. On the project's download page: yes — and that is exactly what
this audit caught.** The release page for v0.6.4 was supposed to contain only files
produced and verified by an automated, tamper-checked pipeline. The audit proved that
the **Windows download files were put there by hand** — built from unfinished,
never-merged code, with no digital signature, with a checksum list rewritten to
match — and the **Linux files were posted by a process that had actually failed**.
The Mac download was re-verified byte-for-byte against the automated pipeline's
records and is clean. If your family uses the **Mac** app, your download is not the
problem. If anyone in the family would download the **Windows or Linux** versions:
do not use the ones currently on the v0.6.4 page.

**What does the grade mean — and not mean?**
The grade rules were written down and locked **before** the examination started, and
the final grade is the **lowest** score any examiner earned — never an average, never
negotiated. BLOCKED here means: *the project's own publishing discipline broke its own
stated rules, and until the download page is fixed, this version cannot be called
cleared.* It does not mean the Mac app was found dangerous — no examiner found any way
for it to move money wrongly. It also does not mean any future version is safe: an
audit is evidence about one version on one day, not a guarantee. And one thing always
stays yours to do: read the transaction on your hardware wallet's screen before you
approve it. That screen — not this app, not this report — is where the final check
lives.

## How this review was done

Five independent examiners, each with exactly one job, worked separately on the same
code — none saw another's findings until the end — plus a sixth, the referee, whose
only job was to distrust everyone: he re-ran the load-bearing checks himself and
computed the grade mechanically from the locked rules. The grade is the lowest score
on the team.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Try every way to steal or alter the assets | 60+ live attacks, all blocked; no breach of any of the five protected assets |
| 🔵 BLUE · The defender | Prove every claimed protection actually holds and is guarded by a test that fails if broken | 39 protections verified; 22+ proven by breaking them and watching tests go red; 6 lack a guarding test — flagged |
| 🟠 ORANGE · The logic specialist | Prove the signature and money math against outside official standards | All 20 critical rules proven against Bitcoin's published standards; the bundled crypto library verified as exactly the reviewed version |
| 🟤 COPPER · The edge specialist | Assume every device, network service, and bundled binary is hostile or broken | 5 of 6 boundaries survived everything; 1 break found: the source-code-mode startup guard checks the wrong library version (doesn't affect the downloaded Mac app) |
| 🟡 AMBER · The supply inspector | Verify how the software is built, signed, and published | Mac chain verified end-to-end; **found the Windows/Linux download files were posted outside every check — the finding that set the grade** |
| ⚪ WHITE · The referee | Distrust everyone; re-derive every load-bearing claim; compute the grade from the locked rules | Every claim re-checked personally — all confirmed; grade computed mechanically: BLOCKED, set by Amber's finding; report cleared for publication |

## The audit trail

**Read this first:** across every examiner and every re-check, **no way was ever found
to move your Bitcoin wrongly**. The items below are about publishing discipline and
safety margins — real, fixable, and none of them a demonstrated path to your funds.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| ⛔ DANGER SIGN | **The Windows download files on the v0.6.4 page were posted by hand, unsigned, from unfinished code, with the checksum list rewritten to match — outside every automated safety check. The Linux files were posted by a process that had failed. Anyone downloading those versions gets unaudited, unverified bytes.** No danger sign of any kind was found in the Mac app itself. | CT-01 (High), CT-02 (Medium) |
| 🟠 IMPORTANT TO FIX | The source-code-mode startup guard claims to detect a swapped cryptography library but checks for the wrong version number, so it guards nothing (downloaded Mac app unaffected). | CT-04 |
| 🟠 IMPORTANT TO FIX | The app's final double-check (screen vs actual transaction before sending) is real and works — but no automated test would notice if someone accidentally deleted it. Same for a few other backstops: they hold, yet are unguarded against future rot. | CT-03, CT-05, CT-15 |
| 🟡 MINOR IMPROVEMENT | Thirteen smaller hardening items: unguarded size limits and diagnostics caps, a lock held during network waits, a counterfeit device receiving the (still-refused) transaction data, floating build-machine versions, release notes edited outside the automated process. | CT-06 → CT-17 (Lows) |
| ⚪ HOUSEKEEPING | Eight notes for maintainers: stale comments, an overconfident documentation line, dead code, design observations. | CT-18 → CT-25 (Infos) |

Severity badges: **⛔ DANGER SIGN** — could put the assets at risk (here: the download
channel, not the Mac app). **🟠 IMPORTANT TO FIX** — a weakness in how the software is
built or released, not in what it does when used. **🟡 MINOR IMPROVEMENT** — extra
safety margin. **⚪ HOUSEKEEPING** — notes for maintainers.

## What this review does not cover

It covers **version 0.6.4 only** — one version, one day. It does not cover the Windows
or Linux applications (their code was outside the locked scope, and the bytes on the
page are not what the audited pipeline produced). No real hardware wallets were
manipulated by the examiners (simulated devices only). Internals of the pinned
third-party libraries were not re-reviewed (they are hash-locked; a separate
component audit is the right tool). This is an AI-panel audit: it complements, and
does not replace, a qualified human security firm. "Nothing found" always means
"nothing found within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + full ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md` |
| The owner-signed audit plan + scope lock (hashes inside) | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.4.md`, `…-audit-lock-v0.6.4.md` |
| The rulebook (framework, public) | github.com/cjtsh/ai-color-team-audit-framework @ v1.3.2 |
| The exact code examined | github.com/cjtsh/bitcoin-easy-multisig-signer @ tag v0.6.4 (`35cdedb`) |

You can read every page of the evidence yourself.

---

## Appendix — findings ledger (final IDs, referee-numbered)

25 entries covering all 28 lane findings (3 merges: CT-04, CT-05, CT-20). By severity: **1 High · 3 Medium · 13 Low · 8 Info · 0 Critical.** Prior-cycle ledger: none (first cycle under this methodology; earlier reports excluded by the owner's signed plan).

| ID | Lane | Severity | Location @ `35cdedb` | Claim |
|---|---|---|---|---|
| CT-01 | Amber | **High** | Release v0.6.4 windows assets (created 2026-10-02T18:17:55Z); runs 37043106853/37038778334; commit `bb1f630` (unmerged) | Unsigned Windows bytes from an unmerged commit manually uploaded past every gate, checksum file rewritten by hand, interim tag `v0.6.4-windows-x64` created and deleted |
| CT-02 | Amber | Medium | Release v0.6.4 linux assets; runs 37053627275 (failed) / 37053094080; commit `53da293` (unmerged) | Linux bytes from a different unmerged commit attached by a failure-concluded run — same-commit/success/signed clauses all unmet |
| CT-03 | Blue | Medium | `gui.py:888-901` | `_check_final_review` (final-vs-review recipient/amount/change/fee backstop, documented in AGENTS.md) is unpinned — deleting it leaves all 261 tests green |
| CT-04 | Copper+Red | Medium | `Start Easy Multisig.command:20` vs `requirements.lock:7` | Source-mode embit guard validates `== "0.8.0"` while the lock pins `0.8.2+besa.1` — a stale registry 0.8.0 venv passes it and skips the hash-verified install; comment claims the opposite (shipped DMG unaffected) |
| CT-05 | Blue+Orange | Low | `gui.py:792-795` | `_current_prepared` binding (wallet/chain/generation/review-id) unpinned; its apparent pin passes only because `hwi` is absent from the test venv (gate itself enforced and backstopped by two pinned gates) |
| CT-06 | Red | Low | `gui.py:341-349, 439-448` | Diagnostics device tokens pattern-sanitized (≤20 chars) rather than a whitelisted device-class vocabulary |
| CT-07 | Blue | Low | `gui.py:450` | 80-event diagnostics buffer cap unpinned |
| CT-08 | Blue | Low | `gui.py:49,562-566`; `probe.py:284-286` | Request-size and 2 MB PSBT bounds unpinned |
| CT-09 | Blue | Low | `network_settings.py:93-103` | settings.json 0600/atomic-write permissions unpinned |
| CT-10 | Blue | Low | `gui.py:281-286` | `checked_psbt()` stored-state revalidation unpinned |
| CT-11 | Blue | Low | `probe.py`/`gui.py` `_sign` | No-retry-after-timeout half of the HWI rule lacks a fail-capable test (device-open half pinned) |
| CT-12 | Blue | Low | `scripts/build-macos.sh:122-139` | `LIBUSB_SHA256` mandatory refusal enforced only by CI execution; no suite test pins the script |
| CT-13 | Copper | Low | `gui.py:917-967`; `wallet_service.py:142-173` | Broadcast holds the session lock across explorer network I/O — a stalling explorer freezes state-touching endpoints (fail-closed, availability only) |
| CT-14 | Copper | Low | `probe.py:306-336`; `gui.py:819-826` | Device identity is key-material only; a counterfeit echo device passes identity and receives the full PSBT (its signatures still refused) |
| CT-15 | Orange | Low | `signing.py:91-99` | Prevout-ownership refusals (script-owns-output, prevout match, vout range) have no in-repo pin |
| CT-16 | Amber | Low | Release v0.6.4 body | Release notes rewritten outside any run (workflow's own notes step failed; later notes are more candid, not deceptive) |
| CT-17 | Amber | Low | `.github/workflows/build-candidate.yml:32,60,120,341,426` | Runner images float (`ubuntu-latest`, `macos-15`); actions SHA-pinned and deps hash-pinned |
| CT-18 | Red | Info | `gui.py:85-92` | Launch-URL docstring overstates fragment confidentiality (browser-mode history can retain the fragment) |
| CT-19 | Red | Info | `gui.py:501` | Dead `__LOCAL_TOKEN__` strip in `GET /` (placeholder absent from ui.html) |
| CT-20 | Red+Orange | Info | `gui.py:674-678, 1059-1061` | Built-in mainnet/testnet4 explorer URLs not genesis-verified at scan (custom URLs and Mutinynet are) |
| CT-21 | Orange | Info | `wallet_service.py:868`; `signing.py:148-175` | Build-fee consistency check and vsize math unpinned in-repo (Orange pinned both externally; bounded by exact-fee-at-finalize and the absolute cap) |
| CT-22 | Orange | Info | vendored embit | Fail-closed strictness observations (uppercase bech32 refused, high-S refused, v1+ programs fail closed) — no defect |
| CT-23 | Copper | Info | `gui.py:495-547`; `probe.py:193-207`; `vendor/README.md` | Tokenless price/fees/`GET /` carry no wallet data; hwi version never queried at runtime; dylib install-name provenance worth a comment |
| CT-24 | Amber | Info | `scripts/build-macos.sh:295-307` | Stale self-contradicting comment ("stays unstapled") vs the actual staple-then-image order |
| CT-25 | Blue | Info | `safe_http.py:43-68, 143-154` | Positive: redirect refusal doubly enforced (two independently sufficient layers, one pinned red) |

*Fix-it input: each lane's full report — with exact evidence, commands, constructed
inputs, break-and-watch transcripts, and remedies — is preserved in the owner's private
record for this cycle (`bitcoin-easy-multisig-signer-colorteam-audit-private-v0.6.4.md`),
never published.*

---

*Audit performed 2026-10-05 on the public repository and published artifacts only, by
a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White
referee, under framework v1.3.2 with definitions v2.4. The grade rules were locked in
the owner-signed plan (SHA-256 recorded above) before the audit began and applied as
written; the plan was re-hashed at the end and the scope never moved. No wallet
material, credentials, or private data appears in this report. An audit is evidence
about one revision on one day — not a certification, not a guarantee, and not a
promise about any future version. Coverage limits are stated above.*

# Color Team Security Audit — Bitcoin Easy Signer v0.6.6 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.6`, commit `93cf67af63a15aac0912a6fbc270f7e5485e2fc1` (built by the unified three-platform pipeline); release `v0.6.6` published 2026-10-06 |
| **Assets declared** | 1. The operator's Bitcoin (reviewed-approved transactions only) · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) · 4. Release artifact integrity (only verified candidate bytes for the same commit; no asset ever overwritten) · 5. Wallet privacy (xpubs, addresses, BSMS, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined (owner-signed plan hashed before the first specialist ran) |
| **Surveyor** | Harness `Kimi Code desktop app` · session `not exposed by the harness` · model `not exposed by the harness` |
| **Auditor identity** | Harness `ZCode desktop app (3.14.4)` · session `not exposed by the harness` · model `zai-api/GLM-5.3` (declared by the harness, not verified) |
| **Independence** | Surveyor and auditor ran in different harnesses as declared; both session identifiers read "not exposed by the harness", so independence **rests on the operator's declaration**. Panel/referee arrangement disclosure: the five specialists ran as independent fresh contexts; the referee sub-agent exhausted the operator's model quota mid-audit after the wave completed, and the referee duties were executed by the lead auditor in the lead's session — the runbook's disclosed weaker arrangement (see *What this audit did not do*, item 11) |
| **Cycle** | `v0.6.6` — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md` |
| **Prior audit** | Cycle `v0.6.5`: report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md`, SHA-256 `eba128c1747f42bfd32d73e84f384b0f64c66b964f8104cd56855146e984dfa0`, grade ⚠️ CONDITIONAL (4 Mediums: BIP-143 pin, superseded dual release, CT-01/CT-02 channel residue). All 47 prior findings accounted for below — none dropped |
| **Verification** | Suite re-run at the tag in four independent environments: **416 tests OK, 0 skipped** (+9/9 UI DOM); all 8 release assets match the CI-generated `SHA256SUMS` (two independent downloads); `SHA256SUMS.asc` good GPG signature (Bitseeker LLC, `ACCC2F1C…D6D7`, 15:25:41Z); the app bundle inside the DMG passes codesign/Gatekeeper/stapled-notarization (Developer ID Bitseeker LLC, B8G5L7M8TB); 2 Sigstore attestations per asset bound to candidate run 37482475884 and publish run 37486264639, both at `93cf67a`; the referee personally re-derived every load-bearing claim (all CONFIRMED), including breaking all seven tripwires the signed plan ordered tested |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.6.md`, SHA-256 `c8b8531bf36ad2360239bd5c8ab22b37b5538f35d8da5718991de5fc0ab3f37f` before the first specialist ran and the same hash at gate time — **equal: the scope never moved**. Owner-signed `Bitseeker LLC, 2026-10-06`. Order witnessed publicly: the signed plan was pinned to `main` at commit `491c226` before the panel ran |

## The grade: ⛔ BLOCKED — the application, its published artifacts, and its release page are clean; the block is two workflow files still alive on the `windows-port` and `linux-port` branches that can publish unsigned, unverified bytes outside every gate — the exact ability the rubric names, standing today

Read this grade the way cycle 1's BLOCKED should be read: **the software passed everything.** For the first time under this methodology the
panel's verdicts include **LOGIC PROVEN** — every money-math invariant, including the new
device key-proof, verified against Bitcoin's published standards and Bitcoin Core's own
message-signing code, with every pin demonstrated able to fail. The attacker lane ran its
cruellest test yet — a counterfeit device that passed identity *and* the new key-proof
returning a correctly-signed thief transaction through the real endpoint — and the app
refused it, because the app verifies what returns against what was reviewed, not who says
so. All 22 cycle-2 Mediums/Lows that the release set out to fix are verified fixed with
fail-capable tests (the referee re-broke all seven plan-ordered tripwires and watched
each go red). The published v0.6.6 bytes, their signatures, notarization, attestations,
and the release pages — including cycle-2's two channel findings — are verified clean.

What blocks the grade is one finding, CT-48: the "retired" per-platform publish
workflows **were never deleted from the repository** — they live on, dispatchable, on the
`windows-port` and `linux-port` branches, carrying release jobs with `contents: write`
that publish **unsigned, unattested** checksum manifests built from unreviewed branch
code. One of them was actually dispatched on 2026-10-05, creating the stray
`v0.6.5-windows-x64` release that cycle 2 graded CT-27 — the panel then believed the
workflows deleted from the tree, and cycle-2's "the ability is closed" ruling was built
on that false premise. The audited pipeline's own header comment still asserts "no
second path can attach bytes to a release." Under the owner-locked rubric — "a pipeline
able to publish unverified, unsigned, or notarization-skipping bytes" is a BLOCKED
condition — the ability, standing and demonstrated, binds the grade. The fix is a
deletion, not a code change: remove the two branch workflow files, correct the comment,
and the condition closes.

**The shortest path to CLEARED:** (1) delete `build-windows.yml` and `build-linux.yml`
from the `windows-port`/`linux-port` branches (or strip their release jobs) and correct
the build-candidate.yml header — owner/CI action, no app code; (2) close CT-35 and the
carried Infos with a dated acceptance note in the repo (ruling 2); (3) add the four
small pins CT-50–CT-53 (UI mirror, log suppression, guard bodies, BSMS header); (4)
work the remaining Lows (CT-49's helper hash-pin, CT-54–CT-60) as capacity allows;
(5) cut v0.6.7 and re-run.

## The four questions that matter

1. **Could this software get the operator to sign or broadcast a transaction they did not approve?** — **No path found — and this cycle proved the strongest version of that yet.** Red's end-to-end counterfeit attack (correctly-signed thief transaction through the real `/api/sign`) was refused; the new key-proof means an echoing counterfeit can no longer even receive the PSBT; Orange proved all 21 invariants against outside oracles (LOGIC PROVEN, first time); the engine diff between the audited tags is first-party hardening only (dependencies byte-identical, `wallet_service.py` unchanged).
2. **Could it leak the unspeakable thing?** — **No leak path found.** Diagnostics stay fixed-vocabulary under hostile input; only derived addresses/txids reach explorers; no credential value exists anywhere in repo, artifacts, or run logs (masked, verified across both runs). The one bounded item: in source mode, a same-user attacker's planted HWI helper receives the derivation path and challenge — never the xpub or PSBT (CT-49, Medium).
3. **Could a remote party, a dependency, or a local process act invisibly?** — **Inside the app and on the release pages: no.** Lying explorers, replayed challenges, races, stalls — all refused or fail-closed (the lock-scope change was race-tested by Copper and pin-verified by the referee). **But in the repository: yes — CT-48.** Two dispatchable publish paths outside every gate remain alive on branches, and the audited pipeline's comment claims they don't exist. That is the invisibility this audit caught.
4. **What should be fixed first?** — CT-48 (delete the branch workflows + fix the comment), then the dated acceptance note closing CT-35/Infos, then the four pins CT-50–53, then CT-49's hash-pin. Every finding carries its exact location and remedy in the ledger.

## The prior audit's findings: 30+ verified fixed, the round trip corrected the record, none dropped

The referee enumerated cycle-2's ledger (hash cited above) and accounted for every ID.
**Verified fixed at v0.6.6 with fail-capable evidence:** CT-03…12, CT-15, CT-18, CT-19,
CT-24 (carried fixed, pins re-cited) · CT-13 (pre-checks outside the lock — referee
broke it back red) · CT-14 (key-proof — broken red) · CT-17 (runners pinned) · CT-20
(genesis on every scan) · CT-21's vsize half · CT-26 (BIP-143 vectors) · CT-27
(superseded release deleted) · CT-28 (forged-xpub pin) · CT-29 (HWI identity pin) ·
CT-30 (floors) · CT-31 (a–d) · CT-32 (prevout pin) · CT-33 (pip-tools pin) · CT-34
(low-S) · CT-43 (-signed naming) · CT-45 (README) · CT-46 (version strings) · CT-02
(channel cleanup complete).
**Partially fixed:** CT-01 — its channel half is remedied, but its root cause (the
second publish path) was never actually deleted; it returns as CT-48.
**Closed as observation:** CT-22. **Open (awaiting fixes or a dated owner acceptance
note):** CT-35 and nine carried Infos (CT-36–42, CT-44, CT-47).
The ledger did not shrink — and the round trip did what it exists to do: it caught a
prior cycle's false premise.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (all five assets itemized). Full surface enumerated; every HTTP-boundary, signer-response (16 hostile classes), binding, race, BSMS, privacy, and workflow attack blocked — including the end-to-end counterfeit-device theft attempt. Residuals: R-01 (merged into CT-49), R-02 (=CT-35), R-03…R-06 (CT-61…64).

**🔵 Blue — DEFENSES HOLD WITH GAPS.** 46 claimed controls inventoried; all pass present/reachable/effective/fail-closed; 21 of 22 break-and-watch pins went red (including every plan-ordered tripwire). Three gaps: the UI large-amount mirror (CT-50), log-suppression (CT-51), and string-assertion guard pins (CT-52).

**🟠 Orange — LOGIC PROVEN.** First LOGIC PROVEN under this methodology: 21 invariants (signature math, the new key-proof family against Bitcoin Core's MessageHash, derivation, BSMS anchoring, arithmetic, broadcast gates) each stated against an outside oracle, independently derived, executed, boundary-covered, and pinned — 23 breaks, all red. Residuals: CT-53 (BSMS header pin) and documentation-level Infos.

**🟤 Copper — EDGE TRUST HOLDS.** Seven mapped interfaces + two beyond the map, each attacked with Lies/Dies/Stalls/Repeats/Substituted at runtime; the echo-only counterfeit received the challenge and never the transaction (`signtx` reached zero times); the shipped bundle's binary chain verified into the DMG bytes; the lock-scope race re-check held (exactly one network submission under concurrency). Asterisk recorded: HWI version identity is self-attestation (CT-49) — behaviour held; identity did not.

**🟡 Amber — CHAIN HOLDS.** The audited artifact's chain verified link-by-link with independent re-derivation: 44/44 PyPI identities and hashes, vendored embit exactly its two documented edits, source tarball 109/109 compared files identical, candidate→publish byte equality with dual attestations to both runs at `93cf67a`, secrets masked everywhere, fail-closed gates proven executed in run logs. The finding: A-01 (CT-48) — the branch publish paths, live and unsigned, with the false "no second path" comment.

**⚪ White — PUBLISH.** Every load-bearing claim re-derived and CONFIRMED (zero unverifiable, zero corrected): the seven plan-ordered tripwires broken red under the referee's own hand; the impostor-helper plant accepted (then proven harmless by the key-proof gates); the key-proof digest construction verified byte-identical to Core's scheme; the branch workflows fetched live and read; artifact digests matched against the live API at gate time. Prior ledger CT-01…47 round-tripped in full. Grade computed, not chosen: no lane proved its failure state; CLEARED independently unreachable (carried items without acceptance; four unpinned controls); **CT-48 (open High, and the rubric's BLOCKED clause (d) — "a pipeline able to publish unverified, unsigned, or notarization-skipping bytes" — satisfied by two live ones) sets ⛔ BLOCKED**. Scope re-hash equal. One grade-neutral dissent recorded (Copper E2's definitional reading). Arrangement disclosure carried in the header and coverage.

## What this audit did not do

1. **No real hardware wallets were touched** by any agent (the attached device was enumerated once by the project's own suite); all device-edge conclusions rest on synthetic adversaries with genuine signing power.
2. **Windows/Linux runtime never executed** (no hosts); covered by code review, workflow, locks, digests, SBOMs.
3. **No live workflow dispatch** (read-only rule); the branch-path capability was verified from the live repository contents and the 2026-10-05 run record, not by triggering it.
4. **PyPI verification:** Amber matched all 44 pairs / 1,700+ hashes; the referee sampled and relied on `--require-hashes` install enforcement; the bulk stands as lane evidence.
5. **Attestation predicates** decoded by Amber; the referee verified digest equality live and the attestation counts.
6. **No bit-reproducibility** of binaries (by design of the chain: candidate-promotion digests + attestations stand in).
7. **Dependency internals** out of scope per the signed plan; the vendored embit's behavior was oracle-checked (CT-26's fix), its delta verified to two documented edits.
8. **Prior AI audit reports** (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) unopened by the panel (independence condition); the cycle-2 Color Team report was the referee's exclusive prior input, per the signed plan.
9. **Release-body edit history** is not API-visible; CT-16's status is no-recurrence-observed.
10. **Best-effort, not a guarantee.** "No finding" means "none found within this coverage." The operator model bars treating operator vigilance as a mitigation.
11. **Arrangement disclosure (binding):** the referee sub-agent exhausted the operator's model quota after the five-lane wave completed; the referee duties were performed by the lead auditor in-session per the operator's instruction to continue. The wave's independence is intact (fresh contexts, charters barred priors, dispatched before the referee work began); the referee's independence from the lead is not, and this disclosure carries that fact.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.6.6 · 2026-10-07 · reviewed by a five-specialist Color Team panel with an independent referee (AI audit, framework v1.3.2)**

## ⛔ BLOCKED — but read what that means: the app itself passed every test, including the hardest ones ever run on it; what blocks the grade is a leftover door in the publishing system that was supposed to have been demolished — and a comment that claims it was

This review was written for the person this software is actually for: a spouse, lawyer,
trustee, accountant, or trusted advisor settling an estate that includes Bitcoin, who
knows Bitcoin is dangerous and cannot review the software themselves. Every statement
here is drawn from — and can be checked against — the full technical report above,
completed 2026-10-07 by five specialists plus a referee, working from rules locked in
writing before anyone looked at the code.

## The questions that matter

**Can this app get my Bitcoin sent somewhere I didn't approve?**
**No path to that was found — none — and this time the examiners went further than ever.**
The attacker built a fake signing device smart enough to pass the app's new identity
check *and* its new prove-you-hold-the-key check, and made it hand back a correctly
signed transaction sending money to a thief. The app refused it — because the app checks
*what comes back* against *what you approved*, not who vouches for it. The math checks
all passed against Bitcoin's official published test values, and the money machinery is
unchanged from the last audited version except to add protections.

**Could it leak the unspeakable — our addresses, wallet details, the family's holdings pattern?**
**No leak path was found.** The examiners tried stuffing addresses and wallet data into
every diagnostic and log channel; everything that isn't an approved fixed code is
dropped. Only the lookups you chose go to the block explorers. Nothing credential-like
exists in the public materials.

**Could someone act invisibly — change the software or its downloads without anyone seeing?**
**Inside the app: no. On your download pages: no — they are clean and verified. In the
project's workshop: yes, one door.** When the publishing system was rebuilt, the old
per-platform build pipelines were "retired" — deleted from the main code. But copies of
those old pipelines were left standing in two side branches of the repository, still
switched on, still able to publish unsigned, unverified files to new release pages. One
was actually used the day before this audit's version was built (that stray "0.6.5
Windows" release the last audit flagged — it came from this door). The new pipeline's
own documentation says the door no longer exists. It does. Nothing has come through it
since, and it cannot touch the files you downloaded — but until it is bricked shut, this
audit cannot call the project cleared, because the last audit's "the door is closed"
verdict turned out to be wrong, and this audit's job is to not repeat that mistake.

**What does the grade mean — and not mean?**
The rules were locked before the examination and the grade is the lowest score earned —
never averaged, never negotiated. BLOCKED here means: *the project's publishing
discipline still has one open door it promised was closed.* It does **not** mean
anything was found that could move your money wrongly — for the third audit in a row,
nothing was. It does not mean the v0.6.6 downloads are tainted — they were verified
byte-for-byte against the locked-down pipeline's records. And it is not a permanent
verdict: deleting two files and re-running the audit is the whole distance from here to
the top grade. As always: read the transaction on your hardware wallet's screen before
you approve. That screen is the final check no audit replaces.

## How this review was done

Five independent examiners, one job each, none seeing the others' work until the end,
plus a referee whose only job was to distrust everyone — he re-ran the decisive checks
himself, including deliberately breaking every new safety tripwire to confirm the
project's tests would notice. The grade is the lowest score on the team. (One honesty
note: the referee's independent harness ran out of its compute allowance mid-audit, so
the referee's checks were completed by the lead examiner in the same session — the
panel's independence held, the referee's did not, and the full report says so plainly.)

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Try every way to steal or alter the assets | Every attack blocked — including a counterfeit device returning a correctly-signed thief transaction: refused |
| 🔵 BLUE · The defender | Prove every claimed protection holds and is guarded by a test that fails if broken | 46 protections verified; 21 of 22 break-tests went red as required; 3 small gaps flagged |
| 🟠 ORANGE · The logic specialist | Prove the signature and money math against outside official standards | **All 21 rules proven — the first perfect score** — including the new device key-proof against Bitcoin Core's own code |
| 🟤 COPPER · The edge specialist | Assume every device, network service, and bundled binary is hostile | Every boundary survived; a counterfeit got the challenge, never the transaction |
| 🟡 AMBER · The supply inspector | Verify how the software is built, signed, and published | The v0.6.6 chain verified end-to-end; **found the old publish pipelines still alive in side branches — the finding that set the grade** |
| ⚪ WHITE · The referee | Distrust everyone; re-derive every load-bearing claim; compute the grade from the locked rules | Every claim re-checked — all confirmed; grade computed mechanically: BLOCKED, by Amber's finding; report cleared for publication |

## The audit trail

**Read this first:** across three full audits, **no way has ever been found to move your
Bitcoin wrongly** — and every fix each audit demanded is now proven by a test that fails
if it rots. The items below are about one undemolished door and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| ⛔ DANGER SIGN | **The old publishing pipelines were never actually demolished — copies live in two side branches, switch-on, able to publish unsigned files to new release pages. One was used the day before this version was built. The main pipeline's documentation claims they no longer exist. Your v0.6.6 downloads are unaffected and verified clean.** Fix: delete two files. | CT-48 |
| 🟠 IMPORTANT TO FIX | The source-code-mode helper check trusts the helper's self-introduction (a planted helper can lie); the key-proof still stops it from ever seeing transaction data, and the downloaded app is immune. | CT-49 |
| 🟠 IMPORTANT TO FIX | Four protections hold but lack their tripwire test (the on-screen large-amount mirror, log silence, the publish-guards' bodies, the file-format header). | CT-50–53 |
| 🟡 MINOR IMPROVEMENT | Twelve smaller hardening items: the Mac helper binary's birth certificate, version-number drift across build machines, missing files in the source archive, a use-time check for the broadcaster, and others. | CT-54–60 |
| ⚪ HOUSEKEEPING | Eleven notes for maintainers, plus ten small observations carried from last audit awaiting a one-line owner sign-off. | CT-61–71; CT-35 + carried |

## What this review does not cover

Version 0.6.6 only — one version, one day. Windows and Linux applications were reviewed
as code and build artifacts but never executed. No real hardware wallets were manipulated
(simulated only). Pinned third-party library internals were not re-reviewed (a separate
component audit is the right tool). An AI-panel audit complements, and does not replace,
a qualified human firm. "Nothing found" always means "within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + full ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md` |
| The owner-signed audit plan + scope lock (hashes inside) | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.6.md`, `…-audit-lock-v0.6.6.md` |
| The prior cycle's report (CONDITIONAL, and what changed since) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md` |
| The rulebook (framework, public) | github.com/cjtsh/ai-color-team-audit-framework @ v1.3.2 |
| The exact code examined | github.com/cjtsh/bitcoin-easy-multisig-signer @ tag v0.6.6 (`93cf67a`) |

You can read every page of the evidence yourself.

---

## Appendix — findings ledger (final IDs, referee-numbered; continuous across cycles)

Open totals at this revision: **1 High · 1 Medium · 12 Low · ~18 Info · 0 Critical.**
Prior-cycle accounting (all 47 IDs): verified fixed CT-02…CT-34 (as itemized in the
report body), CT-43, CT-45, CT-46 · partially fixed CT-01 (root cause → CT-48) · closed
as observation CT-22 · open CT-35, CT-36…CT-42, CT-44, CT-47 (carried; closable by dated
owner acceptance) · CT-25 positive holds.

### New findings

| ID | Lane | Severity | Location | Claim |
|---|---|---|---|---|
| CT-48 | Amber | **High** | Branches `windows-port`/`linux-port` `.github/workflows/build-{windows,linux}.yml`; build-candidate.yml:12-14 | Live dispatchable publish paths publishing unsigned/unattested manifests from unreviewed branch code; dispatched 2026-10-05 (run 37264663578, creating the CT-27 release); the audited pipeline's header falsely claims "no second path." Remedy: delete both files (or strip release jobs) + correct the comment |
| CT-49 | Red+Copper+Orange (merged) | **Medium** | probe.py:239-268; launcher:30-32 | HWI helper identity = version-string self-attestation (planted binary accepted — demonstrated ×4); impostor never receives xpub/PSBT (key-proof gates); frozen mode immune; comment overstates. Remedy: hash-pin the helper or challenge-response; reword |
| CT-50 | Blue | Low | ui.html:858 vs gui.py:56 | UI large-amount floor unpinned mirror (backend authoritative) — one DOM test closes it |
| CT-51 | Blue | Low | gui.py:517-520 | Request-log suppression unpinned — one stderr-capture test closes it |
| CT-52 | Blue | Low | tests/test_workflow_config.py | Guard pins assert names/strings not bodies — extract guards to scripts or assert `exit 1` presence |
| CT-53 | Orange | Low | probe.py:99 | BSMS magic-line gate unpinned (unreachable; downstream refuses) — one hostile-header test |
| CT-54 | Amber | Low | vendor/libusb-1.0.0.dylib | macOS dylib exact build lacks an upstream byte anchor (runner-image capture; symbol-set identical) — build from pinned source next bump |
| CT-55 | Amber | Low | workflow pins | Python "3.12" patch level floats (3.12.10 vs 3.12.14 in one run) — pin x.y.z |
| CT-56 | Amber | Low | scripts/build-source.sh | Tarball omits hwi-entitlements.plist (+2 files) — signed macOS rebuild from tarball fails |
| CT-57 | Amber | Low | inputs workflows; build-linux.sh:110 | pip-tools version-pinned not hash-pinned; unpinned pip upgrade |
| CT-58 | Copper | Low | probe.py:197,246-248 | HWI identity cached per path (TOCTOU) — re-verify per signing session |
| CT-59 | Copper | Low | wallet_service.py:142-173 | Stalling explorer can hold one scan tens of minutes (fail-closed, availability only) |
| CT-60 | Copper | Low | gui.py:996-997 | Mainnet broadcaster not genesis-verified at use-time — verify unconditionally at `_broadcast` |
| CT-61 | Red | Info | probe.py:94-193 | Attacker-key BSMS importable by design (mitigations verified; trusted-delivery hop named) |
| CT-62 | Red | Info | gui.py:1174-1178 | Large-amount message understates its own trigger (safe direction) |
| CT-63 | Red | Info | desktop.py:211-217 | `bundled_capabilities` bypasses the identity gate (build-time only, no wallet data) |
| CT-64 | Red | Info | gui.py:464,520,760 | `pending_by_wallet` unpruned per session (bounded, memory) |
| CT-65 | Orange | Info | signing.py:293; gui.py:955 | Two redundant txid clauses unpinned in isolation (cannot fire under SIGHASH_ALL) |
| CT-66 | Orange | Info | probe.py:404-441 | Proof-parse contract nits (all fail closed; no real device emits the shape) |
| CT-67 | Orange | Info | probe.py:461-464 | Key proof at /0/0 not account node — documented Trezor tradeoff |
| CT-68 | Orange | Info | signing.py:44-62 | R-minimality relies on embit strict DER (re-review mandated on any embit bump) |
| CT-69 | Blue | Info | gui.py:874-877 | Device binding matches (type,path); re-verification carries residual |
| CT-70 | Copper | Info | gui.py:91-101 | Browser-mode token persists in that browser's history (documented) |
| CT-71 | Amber | Info | AGENTS.md:58 | "Latest published release is 0.6.4" — stale prose post-publication |

*Fix-it input: each lane's full report — exact evidence, commands, constructed inputs,
break-and-watch transcripts, remedies — is preserved in the owner's private record
(`bitcoin-easy-multisig-signer-colorteam-audit-private-v0.6.6.md`), never published.*

---

*Audit performed 2026-10-06/07 on the public repository and published artifacts only, by
a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White
referee, under framework v1.3.2 with definitions v2.4. Grade rules were locked in the
owner-signed plan (SHA-256 `c8b8531b…`, equal at start and end) before the audit began
and applied as written. No wallet material, credentials, or private data appears in this
report. An audit is evidence about one revision on one day — not a certification, not a
guarantee. Coverage limits, including the referee-arrangement disclosure, are stated
above.*

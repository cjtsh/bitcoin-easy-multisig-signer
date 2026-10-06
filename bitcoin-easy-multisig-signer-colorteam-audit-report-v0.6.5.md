# Color Team Security Audit — Bitcoin Easy Signer v0.6.5 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.5`, commit `29c8002b154a4e968308376b1e514a965ffa92d8` (the commit the unified pipeline built all three platforms from); release `v0.6.5` published 2026-10-06 |
| **Assets declared** | 1. The operator's Bitcoin (reviewed-approved transactions only) · 2. Signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds") · 3. The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) · 4. Release artifact integrity (only verified candidate bytes for the same commit; no asset ever overwritten) · 5. Wallet privacy (xpubs, addresses, BSMS, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel plus a White referee; asset declaration, charters and grade rules locked in writing **before** the build was examined (owner-signed plan hashed before the first specialist ran) |
| **Surveyor** | Harness `Kimi Code desktop app` · session `not exposed by the harness` · model `not exposed by the harness` |
| **Auditor identity** | Harness `ZCode desktop app (3.14.4)` · session `not exposed by the harness` · model `zai-api/GLM-5.3` (declared by the harness, not verified) |
| **Independence** | Surveyor and auditor ran in different harnesses as declared; both session identifiers read "not exposed by the harness", so independence **rests on the operator's declaration** (two harnesses, survey ≠ audit model by methodology) |
| **Cycle** | `v0.6.5` — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md` |
| **Prior audit** | Cycle `v0.6.4`: report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md`, SHA-256 `9cb5c4f573d4582562919c0da84690a0372ad60f8025caaa148d2c2fa58970a3`, grade ⛔ BLOCKED (CT-01 High + CT-02 Medium, release-channel findings). All 25 prior findings are accounted for below — none dropped. |
| **Verification** | Published artifacts re-downloaded and re-hashed against the CI-generated `SHA256SUMS` (8/8 match, lead and Amber independently); `SHA256SUMS.asc` is a good GPG signature from the project release key (Bitseeker LLC, `ACCC2F1C…D6D7`); the app bundle inside the DMG passes `codesign --verify --deep --strict` and Gatekeeper (`spctl`: source=Notarized Developer ID, Developer ID Application: Bitseeker LLC, B8G5L7M8TB), and both the app and the DMG carry valid stapled notarization tickets (`stapler validate` passes; the DMG file itself carries no codesign object — its notarization evidence is the stapled ticket); every release asset carries two GitHub Sigstore build attestations bound to commit `29c8002`; full suite re-run at the tag by the lead, every lane, and the referee (362 tests OK, 0 skipped; 9/9 UI DOM tests); the referee personally re-derived every load-bearing claim — all CONFIRMED, zero UNVERIFIABLE, zero CORRECTED |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.5.md`, SHA-256 `ecc1b42ea0ff581cf81fcae2d835052083753d7f5ae516a7c924321effe80c69` before the first specialist ran and the same hash re-computed by the referee at gate time — **equal: the scope never moved**. Owner-signed `Bitseeker LLC, 2026-10-06`. Order witnessed publicly: the signed plan and lock were pinned to `main` at commit `6bdb083` before the panel ran. |

## The grade: ⚠️ CONDITIONAL — no unforgivable-act path exists and no Critical/High finding is open, but four Mediums (two new, two carried) and a set of unpinned money-path controls hold it below CLEARED under the locked rubric

This is a genuine improvement arc, graded mechanically: cycle 1 (v0.6.4) was ⛔ BLOCKED
because a per-platform workflow could and did publish unsigned bytes from unmerged
commits onto the tagged release page. At v0.6.5 that ability is gone — the retired
per-platform workflows are deleted from the audited tree, one dispatch-only pipeline
(`build-candidate.yml`) builds macOS, Windows and Linux from the same commit in the
same run, and the chain was verified link-by-link to the published bytes
(CHAIN HOLDS). No lane demonstrated a breach, a broken control, wrong logic, a broken
edge, or a broken chain; the referee re-derived the money-path refusals personally and
confirmed every one.

CONDITIONAL is set by the rubric's own conditions, not by judgment:

1. **Four open Mediums.** CT-26 (new): the BIP-143 signature digest — the most
   load-bearing computation in the product — has no in-suite regression test; breaking
   it deliberately leaves all 362 tests green. CT-27 (new): a superseded release
   `v0.6.5-windows-x64` is still live, carrying same-named Windows files with
   **different bytes** and no signed checksum manifest. CT-01 residual and CT-02
   (carried): the manually-published Windows/Linux assets from cycle 1 are still
   downloadable on the v0.6.4 release page.
2. **Ruling 5 — unproven things on the path to declared assets cap the grade.** Orange
   leaves LOGIC UNPROVEN (the BIP-143 digest plus four money-path gates are
   oracle-correct but unpinned); Copper leaves EDGE TRUST UNPROVEN (source-mode HWI
   has no version identity — the shipped DMG is fully pinned); Blue leaves one control
   failing the pinning test (device-identity xpub comparison); Amber's runner images
   float (CT-17). CLEARED requires every claim proven and pinned; it was unreachable
   this cycle, and ambiguity is never resolved in CLEARED's favor.

**The shortest path to CLEARED:** (1) delete or clearly supersede the two stale
releases (`v0.6.5-windows-x64` and the v0.6.4 page's manual Windows/Linux assets) —
owner actions, no code; (2) add the BIP-143 published-vector test (CT-26) and the
one-line xpub test (CT-28); (3) pin the four money-path gates of CT-31 and the
build-time prevout check (CT-32); (4) give the source-mode launcher HWI version
identity (CT-29); (5) pin runner images (CT-17) and work the remaining
Lows/Infos; (6) cut v0.6.6 and re-run the audit.

## The four questions that matter

1. **Could this software get the operator to sign or broadcast a transaction they did not approve — recipient, amount, fee, or change altered between review and broadcast?** — **No path found.** Red ran 60+ live adversarial probes against the real loopback API (swapped recipients, inflated amounts, forged/non-wallet/replayed signatures, dropped signatures, rewritten scripts and prevouts, lying broadcasters, races); every money-path attack was blocked, and the referee independently re-executed the signature-tamper and gate probes with the same results. Orange proved the signature, derivation and encoding logic against Bitcoin's published BIP-143/173/380 standards — zero oracle violations — and confirmed the wallet/transaction/signing engine is byte-identical between the audited v0.6.4 and v0.6.5 tags: this release changed the factory, not the money path.
2. **Could it leak the unspeakable thing — xpubs, addresses, wallet activity, credentials?** — **No leak path found in the app.** Diagnostics now accept only a fixed vocabulary of device classes (CT-06's fix verified pinned); hostile device strings are dropped, demonstrated. No credential value exists anywhere in the repo, artifacts, or visible run logs (all masked; the committed `signing-key.asc` is a public key). One bounded hardening item: in **source mode only**, a same-user attacker could plant a fake `hwi` on PATH and receive account xpubs and PSBTs (CT-29, Low — the signed DMG is immune; signatures from such a device are still refused).
3. **Could a remote party, a dependency, or a local process act invisibly?** — **Inside the app: no.** Lying explorers produce refusals or, at worst, hidden funds — never a misdirected transaction (fabricated funding must hash to claimed txids and match wallet-derived scripts); redirects are doubly refused; TLS is always on; the frozen-payment binding held under every race. **On the release channel: residue remains.** The superseded `v0.6.5-windows-x64` release and the v0.6.4 page's manual assets are still live and unsigned — publishing-discipline leftovers from before the unified pipeline, now outside every gate but not yet cleaned up (CT-27, CT-01 residual, CT-02). Nothing new reached any release page through the audited pipeline.
4. **What should be fixed first?** — In order: CT-27 and the CT-01/CT-02 channel cleanup (delete/supersede the stale releases — an owner action, no code), CT-26 (BIP-143 published-vector test), CT-28 (xpub comparison test), CT-31/CT-32 (pin the remaining money-path gates), CT-29 (source-mode HWI identity), CT-17 (pin runner images), then the open Lows (CT-13, CT-14, CT-20, CT-21's vsize half) and Infos. Every finding carries its exact location and remedy in the ledger below.

## The prior audit's findings: 14 verified fixed, 1 fixed for this cycle, the rest accounted for — none dropped

Cycle 1 ended ⛔ BLOCKED with CT-01…CT-25. The referee enumerated the prior report's
ledger (file hash cited above) and accounted for every ID:

**Verified fixed (14):** CT-03 final-review backstop — now pinned by two fail-capable
tests (referee broke the control and watched both go red) · CT-04 launcher embit guard
now checks the pinned version `0.8.2+besa.1` (pinned by `tests/test_launcher.py`) ·
CT-05 review-id binding pinned · CT-06 diagnostics fixed vocabulary · CT-07 buffer
cap · CT-08 request/PSBT size bounds · CT-09 settings-file permissions · CT-10
stored-state revalidation · CT-11 no-retry rule · CT-12 `LIBUSB_SHA256` script
refusal · CT-15 prevout-ownership refusals pinned (four tests) · CT-18 docstring ·
CT-19 dead token strip removed · CT-24 stale comment erratum recorded.

**Fixed for this cycle (1):** CT-16 — the v0.6.5 release was created and published by
the workflow run itself (github-actions[bot]); no out-of-run edit observed (edit
history is not API-visible, so this is no-recurrence-observed, not proof).

**Partially fixed (2):** CT-01 — the *pipeline* half is remediated and pinned (single
dispatch-only pipeline; retired workflows deleted; guards proven executed in run
logs); the *channel* half is open: the unsigned Windows bytes are still downloadable
on the v0.6.4 page (residual calibrated Medium). CT-21 — fee gates now pinned; the
vsize half is carried as CT-31(c).

**Open (5):** CT-02 (Linux assets from the failure-concluded run still live on
v0.6.4) · CT-13 (broadcast holds the session lock across network I/O — documented
fail-closed design, availability only; no written owner acceptance exists) · CT-14
(an echoing counterfeit device receives the PSBT; its signatures are still refused) ·
CT-17 (floating runner images) · CT-20 (built-in default explorer URLs skip the
genesis re-check at scan; custom URLs and Mutinynet are always checked).

**Closed as observation (1):** CT-22 (fail-closed strictness notes — no defect).
**Carried as components (2):** CT-23's items live on as CT-35 (tokenless quotes) and
CT-29 (source-mode HWI identity); CT-25's positive result still holds.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED** (itemized: all five assets held). Red enumerated the full input surface (loopback API + session token, BSMS file, HWI device responses, explorer/fee/price HTTP, settings file, WebView/JS bridge, concurrent requests — an input that exists but is missing from the list would itself be a finding; none was) and attacked it live with synthetic vectors in a disposable copy: hostile BSMS variants, device-response tampering (with genuine ECDSA signing power over synthetic keys), forged signatures, broadcast-gate bypasses, lying broadcasters, races, diagnostics leakage, redirect/TLS abuse, half-open floods. Every money-path attempt was blocked by a control; every privacy attempt was dropped. Residuals are bounded Lows/Infos (CT-29 shared, CT-35, CT-42…44). One structural discovery verified by the referee: embit's `PSBT.tx`/`OutputScope` properties return fresh objects every access, so property-level tampering silently cannot stick.

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Inventory of 44 claimed controls (from AGENTS.md, README, PRIVACY.md, SIGNING.md, RELEASE-PROCESS.md, the plan, docstrings, comments): all 44 are present, reachable where they matter, effective, and fail-closed — none fails tests 1–4. Break-and-watch pinned 36 experiments red (including the CT-03 backstop, the mainnet dual gates, the signature-import chain, the token/Host/Origin gates, the dev-mode gate, the palette, the dispatch-only workflow guards, the no-credentials build refusal). One gap stayed green: the device-identity full-xpub comparison `_same_xpub` weakened to fingerprint-only leaves the suite green, and a forged-fingerprint xpub passes the weakened check (the intact check refuses it) — CT-28. Three documented fail-open-by-design notes are recorded as Info (CT-38, CT-39, CT-35).

**🟠 Orange — LOGIC UNPROVEN** (zero oracle violations; itemized per 15 invariants). All invariants were stated, independently derived *before* reading the implementation, and matched by execution against outside oracles: BIP-143 (all six published sighash digests, via an independent transcription whose own three errors were caught and fixed against the BIP's published preimages), BIP-173 address vectors, BIP-380 checksums, BIP-48 change policy, fee/amount/dust boundaries, quorum semantics. The vendored embit is oracle-correct at this revision and byte-identical to the two-edit patched source; the v0.6.4→v0.6.5 delta touches **no** named invariant (the money-path files have zero diff between the tags). Five invariants lack an in-suite pin — worst, the BIP-143 digest itself (CT-26): broken to single-SHA256, the full 362-test suite stays green because every repo signature test self-signs and self-verifies through the same function. The remaining four are CT-31(a–d) and CT-32/CT-41.

**🟤 Copper — EDGE TRUST UNPROVEN at the source-mode dependency edge** (every other interface HOLDS with runtime evidence). Six edge interfaces were attacked with Lies/Dies/Stalls/Repeats/Substituted batteries: HWI device boundary (fake HWI subprocess speaking the real protocol — every lie refused, tampered metadata provably discarded), the bundled libusb binary (provenance chain verified to the shipped bytes: vendored hash → build guard → SBOM digests → `__TEXT` sections byte-identical inside the signed app), outbound HTTP (redirects refused incl. same-host 307; wrong-genesis and plain-signet-as-mutinynet caught by checkpoint pins; timeouts everywhere; outcome-unknown broadcast clears state and refuses blind retry), the loopback transport + client (token/Host/Origin gates, rotating CSP nonce, single-script page), the settings file, and the source-mode launcher. The one unproven edge: source mode resolves `hwi` from PATH with no version identity — Copper planted a shim and the core executed it (frozen mode refuses the fallback, pinned by test) — CT-29. The renderer engine's version is not establishable (CT-40, Info).

**🟡 Amber — CHAIN HOLDS.** Chain inventory published link-by-link, then verified: all 1,709 dependency hash pins in the five lock files matched PyPI-published digests for the exact name+version (zero mismatches, no squatter signals, canonical homes); the vendored embit differs from its pinned upstream by exactly the two documented edits and the wheel is byte-identical to the patched source; libusb dylib/DLL provenance verified to upstream and into the shipped bytes; the AppImage runtime is byte-identical to its upstream release asset. The unified pipeline was read line-by-line and its controls proven **executed** in the run logs: dispatch-only, main-branch requirement, candidate-manifest provenance gate (publish run 37411746360 verified candidate run 37409812638 at the same commit, `shasum -c` ×8 in-run), unsigned-publish refusal, no-overwrite guard, GPG signing re-verified in-run against the committed public key, two Sigstore attestations per asset, secrets referenced by name only and masked everywhere. The release `SHA256SUMS` is byte-identical to the candidate run's manifest. Findings: CT-27 (the superseded dual release, Medium), CT-33 (lock-generation tooling unpinned, Low), CT-17 kept open (floating runners), CT-45…47 (Infos).

**⚪ White — PUBLISH.** Every load-bearing claim re-derived personally, findings and clean bills with equal energy: the broken-embit green suite reproduced exactly; the BIP-143 vectors re-derived from the canonical BIP text by independent implementation (intact code matches all published digests; broken code fails the vector); the weakened `_same_xpub` green suite and forged-xpub acceptance reproduced; CT-03's pin broken and watched fail; the frozen PATH refusal broken and watched fail; Red's money-path refusals re-executed with genuine signing power; artifact digests, GPG, notarization, attestations, and the live channel state re-pulled from the APIs — **all CONFIRMED, zero UNVERIFIABLE, zero CORRECTED**. Prior ledger CT-01…CT-25 round-tripped in full (§ above). Grade computed, not chosen: no lane proved its failure state; no open Critical/High; the plan's BLOCKED pipeline clause is not met at the audited revision (the ability is closed and pinned; what remains are live channel states, not abilities); CLEARED failed its pinned-controls and prior-findings clauses; ruling 5 capped through Orange, Copper, Blue and Amber — **⚠️ CONDITIONAL**, floor never averaged. Scope re-hashed: **H_end = H_start — the scope never moved.** Session identifiers: both "not exposed by the harness" — not identical; independence rests on the operator's declaration. No dissents.

## What this audit did not do

1. **No real hardware wallets were touched** by any panel agent, the referee, or the lead (one device attached to the host was enumerated only by the project's own suite, once, as shipped). The HWI boundary was verified against synthetic devices with genuine signing power — the exact trust boundary the app verifies.
2. **Windows and Linux runtime was never executed** (no hosts available). Those platforms are covered by code review, the CI workflow, lock files, digests, and SBOMs only. The macOS chain was verified hands-on.
3. **PyPI bulk verification was sampled by the referee** (4 of 44 pairs plus the embit triple, and every lock hash enforced by `--require-hashes` install); Amber's full 1,709-hash match stands as lane evidence.
4. **Bit-reproducibility of the DMG/zip/AppImage was not attempted** (PyInstaller output is not byte-reproducible); "matched" was established by candidate-promotion digests, SBOMs, and Sigstore attestations — the chain's own design.
5. **The superseded release bytes were not downloaded** (CT-01/CT-02/CT-27 digests are API-reported values); and release-body **edit history is not API-visible**, so CT-16's fix is no-recurrence-observed, not proof.
6. **Run-log secret masking** was scanned by Amber across the pulled jobs; the referee did not re-run the deep scan (guards verified in-file; GPG/codesign/stapler/attestation receipts independently reproduced).
7. **Dependency internals** (hwilib, pywebview, requests, certifi, libusb, upstream embit beyond the documented two-edit delta) remain out of scope per the signed plan; the vendored embit's *behavior* was oracle-checked this cycle (CT-26 records the missing repo-side pin). A separate component audit of the pinned stack is recorded by the project as outstanding.
8. **Live WebKit window behavior and browser mode** were not driven; the bridge was verified statically plus by its tests. Live explorer operators are out of scope; all lying-explorer evidence is synthetic.
9. **Prior AI audit reports** (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) were excluded as inputs by the owner's signed independence condition; the cycle-1 Color Team report was the referee's exclusive prior input, per the same plan.
10. **Best-effort, not a guarantee.** This report serves a nontechnical fiduciary reader and the fixing agent; "the operator should have noticed" was treated as a weakness to report, never a mitigation to assume. "No finding" means "none found within this coverage."

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer v0.6.5 · 2026-10-06 · reviewed by a five-specialist Color Team panel with an independent referee (AI audit, framework v1.3.2)**

## ⚠️ CONDITIONAL — good software with work remaining: every examiner agrees the app itself is safe to use, and last cycle's publishing failure is fixed; what holds the grade back now is cleanup on the download pages and a short list of "prove it forever" tests the factory still owes

This review was written for the person this software is actually for: a spouse, lawyer,
trustee, accountant, or trusted advisor settling an estate that includes Bitcoin, who
knows Bitcoin is dangerous and cannot review the software themselves. Every statement
here is drawn from — and can be checked against — the full technical report above,
completed 2026-10-06 by five specialists plus a referee, working from rules locked in
writing before anyone looked at the code. The evidence and the rulebook are public; the
last section tells you where.

## The questions that matter

**Can this app get my Bitcoin sent somewhere I didn't approve?**
**No path to that was found — none.** A dedicated attacker-examiner ran more than
sixty live attacks (swap the recipient, change the amount, forge a signature, replay an
old approval, confuse it with simultaneous requests); every one was blocked. The referee
independently re-ran the cruelest attacks and watched them fail again. A third examiner
proved the signature and address math against Bitcoin's official published test
standards — and found the money machinery is *byte-identical* to the previous audited
version: this release changed how the software is manufactured, not how it moves money.
The protection you can verify yourself: the app never holds your keys — your hardware
wallets do — and it shows the transaction on those devices' own screens for your
approval.

**Could it leak the unspeakable — our addresses, wallet details, the family's holdings pattern?**
**No leak path was found.** The examiners checked what the app writes to logs and
diagnostics (this cycle they tried stuffing addresses and wallet data into every
diagnostic channel — everything that isn't an approved fixed code is dropped), what it
sends over the network (only what you chose to ask an explorer), and where the
publishing credentials live (nowhere public). One narrow hardening item: if you run the
app *from source code* (not the downloaded Mac app) and someone already controls your
user account on this Mac, they could swap the wallet-device tool the app calls. The
downloaded, signed app refuses that path outright.

**Could someone act invisibly — change the software or its downloads without anyone seeing?**
**Inside the app: no. On the project's download pages: leftovers, yes — and this audit
names them exactly.** Last cycle's BLOCKED grade was about files posted to the download
page outside every safety check. That hole is now closed *structurally*: one locked,
dispatch-only pipeline builds the Mac, Windows and Linux downloads from the same code
in one run, and the audit followed every byte from that run to the published files —
signed, checksummed, and independently attested. But two pieces of old wreckage are
still on the shelf: a superseded "v0.6.5-windows-x64" release with same-named Windows
files of *different* bytes and no signature, and the old unsigned Windows/Linux files
still sitting on the v0.6.4 page. Nothing new got through the new gates; the old stuff
just hasn't been thrown out. Until it is, verify downloads only against the signed
`SHA256SUMS.asc` on the release you actually mean.

**What does the grade mean — and not mean?**
The grade rules were written down and locked **before** the examination started, and
the final grade is the **lowest** score any examiner earned — never an average, never
negotiated. CONDITIONAL here means: *the software passed every safety test we know how
to run, and the publishing process passed too — but four named items (two stale
download-page entries, one missing "tripwire" test for the signature math, and a short
list of other unpinned safeguards) keep it below the top grade.* It does not mean
anything was found that could move your money wrongly — nothing was, in either cycle.
It also does not mean any future version is safe: an audit is evidence about one
version on one day. And one thing always stays yours to do: read the transaction on
your hardware wallet's screen before you approve it. That screen — not this app, not
this report — is where the final check lives.

## How this review was done

Five independent examiners, each with exactly one job, worked separately on the same
code — none saw another's findings until the end — plus a sixth, the referee, whose
only job was to distrust everyone: he re-ran the load-bearing checks himself (including
deliberately breaking the signature math to see if the project's own tests would
notice) and computed the grade mechanically from the locked rules. The grade is the
lowest score on the team.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Try every way to steal or alter the assets | 60+ live attacks, all blocked; no breach of any of the five protected assets |
| 🔵 BLUE · The defender | Prove every claimed protection actually holds and is guarded by a test that fails if broken | 44 protections verified; 36 proven by breaking them and watching tests go red; 1 lacks a guarding test — flagged |
| 🟠 ORANGE · The logic specialist | Prove the signature and money math against outside official standards | Every rule proven against Bitcoin's published standards, zero violations; the math is unchanged from the last audited version; 5 safeguards lack tripwire tests |
| 🟤 COPPER · The edge specialist | Assume every device, network service, and bundled binary is hostile or broken | Every boundary survived everything thrown at it — except one: source-code mode (not the downloaded app) doesn't verify which wallet-device tool it's calling |
| 🟡 AMBER · The supply inspector | Verify how the software is built, signed, and published | The new one-pipeline chain verified end-to-end to the published bytes; found the old superseded Windows release still live on the shelf |
| ⚪ WHITE · The referee | Distrust everyone; re-derive every load-bearing claim; compute the grade from the locked rules | Every claim re-checked personally — all confirmed; grade computed mechanically: CONDITIONAL; report cleared for publication |

## The audit trail

**Read this first:** across two full audits and every re-check, **no way was ever found
to move your Bitcoin wrongly**. The items below are about publishing discipline and
safety margins — real, fixable, and none of them a demonstrated path to your funds.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| ⛔ DANGER SIGN | **None found — in any review, either cycle.** | — |
| 🟠 IMPORTANT TO FIX | **Old files still on the download pages:** a superseded "0.6.5" Windows release with same-named but different, unsigned files, and cycle 1's manual Windows/Linux files still on the v0.6.4 page. Nothing new got through the fixed pipeline; these are pre-fix leftovers awaiting deletion. | CT-27, CT-01 (residual), CT-02 |
| 🟠 IMPORTANT TO FIX | **The signature math has no tripwire:** the app's own test suite wouldn't notice if a future library update silently changed the Bitcoin signature calculation. The math is provably correct today (verified against Bitcoin's official test values); the missing piece is a standing test that fails if it ever drifts. Same for a handful of other safeguards that hold but are unguarded against future rot. | CT-26, CT-28, CT-31, CT-32 |
| 🟡 MINOR IMPROVEMENT | Ten smaller hardening items: source-mode tool identity (CT-29), price-feed disclosure thinning (CT-30), unsigned-transaction file naming (CT-43), lock-tooling pins (CT-33), low-S enforcement (CT-34), and the carried CT-13/14/17/20/21 items. | ledger below |
| ⚪ HOUSEKEEPING | Fourteen notes for maintainers: doc mismatches, console noise, resilience, observations. | CT-35 → CT-47 |

Severity badges: **⛔ DANGER SIGN** — could put the assets at risk (none found). **🟠
IMPORTANT TO FIX** — a weakness in how the software is built or released, not in what it
does when used. **🟡 MINOR IMPROVEMENT** — extra safety margin. **⚪ HOUSEKEEPING** —
notes for maintainers.

## What this review does not cover

It covers **version 0.6.5 only** — one version, one day. The Windows and Linux
*applications* were reviewed as code and build artifacts but never executed (no
Windows/Linux machine was used); their published bytes are verified to come from the
one audited pipeline run. No real hardware wallets were manipulated (simulated devices
only). Internals of the pinned third-party libraries were not re-reviewed (a separate
component audit is the right tool and is recorded as outstanding by the project). This
is an AI-panel audit: it complements, and does not replace, a qualified human security
firm. "Nothing found" always means "nothing found within this coverage."

## Check our homework

| What | Where |
|---|---|
| This report (technical + this review + full ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md` |
| The owner-signed audit plan + scope lock (hashes inside) | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.5.md`, `…-audit-lock-v0.6.5.md` |
| The prior cycle's report (BLOCKED, and what changed since) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md` |
| The rulebook (framework, public) | github.com/cjtsh/ai-color-team-audit-framework @ v1.3.2 |
| The exact code examined | github.com/cjtsh/bitcoin-easy-multisig-signer @ tag v0.6.5 (`29c8002`) |

You can read every page of the evidence yourself.

---

## Appendix — findings ledger (final IDs, referee-numbered; continuous across cycles)

Open totals at this revision: **0 Critical · 0 High · 4 Medium · 10 Low · 14 Info.**
Prior-cycle accounting (all 25 IDs): verified fixed CT-03–CT-12, CT-15, CT-18, CT-19,
CT-24 (14) · fixed this cycle CT-16 (1) · partially fixed CT-01, CT-21 (2) · open
CT-02, CT-13, CT-14, CT-17, CT-20 (5) · closed as observation CT-22 (1) · carried as
components CT-23 → CT-29/CT-35, CT-25 positive still holds (2). None dropped.

### Open and new findings

| ID | Lane | Severity | Location @ `29c8002` / channel | Claim |
|---|---|---|---|---|
| CT-01 (residual) | Amber (prior cycle) | **Medium** | Release `v0.6.4` page, live today | Pipeline half remediated and pinned (unified dispatch-only pipeline; retired workflows deleted); channel half open — the manually-published unsigned Windows bytes (`bb1f630`, updated 2026-10-02T18:18:01Z) remain downloadable; delete or supersede |
| CT-02 | Amber (prior cycle) | **Medium** | Release `v0.6.4` page, live today | Linux assets from the failure-concluded run (`53da293`, 19:27:11Z) and their sums file still live; same remedy |
| CT-26 | Orange | **Medium** | vendored embit `Transaction.sighash_segwit`; `tests/` | BIP-143 digest — the most load-bearing computation — has no in-suite regression detection: broken to single-SHA256, all 362 tests stay green (reproduced by lane and referee). Logic oracle-correct today. Remedy: repo test asserting the published BIP-143 digests/signatures |
| CT-27 | Amber | **Medium** | Live release `v0.6.5-windows-x64` (2026-10-05T04:47:25Z, run 37264663578, retired build-windows.yml @ `897e9e6`, an ancestor of 29c8002) | Second live "0.6.5" Windows artifact set — same filenames as the audited assets, different bytes (`af4ee135…`/`716daefd…` vs `fba949ac…`/`d37c9c97…`), unsigned sums manifest. Weakens operator verification; not High because the audited chain is intact and the signed-manifest control is not defeated. Remedy: delete/mark superseded; never reuse a version number |
| CT-13 | Blue (prior cycle) | Low | `gui.py:961-1007` | Broadcast holds the session lock across explorer I/O (fail-closed; availability only) — open, no written owner acceptance |
| CT-14 | Copper (prior cycle) | Low | `probe.py:306-336`; `gui.py:819-826` | Echoing counterfeit device passes identity and receives the PSBT; its signatures are still refused |
| CT-17 | Amber (both cycles) | Low | `.github/workflows/build-candidate.yml` (floating `ubuntu-latest`/`windows-latest`/`macos-15`) | Runner images float; this release's exact images are recorded in run logs and artifacts are hash/attestation-anchored — pin them |
| CT-20 | Orange (prior cycle) | Low→Info | `gui.py:715-722` | Built-in mainnet/testnet4 explorer URLs skip the genesis re-check at scan (custom URLs and Mutinynet always checked; TLS-pinned canonical URLs) |
| CT-28 | Blue | Low | `probe.py:320-335`; `tests/test_probe.py:160,168,268,389` | Full-xpub device-identity comparison unpinned: fingerprint-only weakening stays green; forged-fingerprint xpub accepted by weakened check, refused by intact. One test closes it |
| CT-29 | Red+Copper (merged) | Low | `probe.py:209-212`; `Start Easy Multisig.command` | Source-mode HWI resolves over PATH with no version identity — a planted `hwi` is executed and receives account xpubs/PSBTs (demonstrated); frozen builds refuse the fallback (pinned). Remedy: launcher `--hwi` path or version check |
| CT-30 | Copper | Low | `gui.py:104-128, 1145-1158` | In-range lying price quote can suppress the USD trigger of the large-amount prompt; absolute 0.1 BTC floor and all confirmations untouched |
| CT-31 | Orange | Low | (a) `signing.py:266` (b) `signing.py:89` (c) `signing.py:174` (d) `wallet_service.py:84-89` | Four money-path gates oracle-correct but unpinned (outputs≤inputs; sign-time 2–3-key; vsize formula; broadcast hex/size/parity). Cross-ref CT-21(c) |
| CT-32 | Orange | Low | `wallet_service.py:850-853` | Build-time prevout/ownership binding unpinned (sign-time twin pinned as CT-15). Fake-explorer test closes it |
| CT-33 | Amber | Low | `windows-inputs.yml:49`; `linux-inputs.yml:49` | Lock-generation tooling (pip-tools) not hash-pinned; compensating control is human review of the reviewable commit |
| CT-34 | Orange | Low | `signing.py:105` | No low-S (BIP-62) enforcement on imported signatures; malicious-device high-S finalizes then fails relay — availability blip |
| CT-35 | Red+Blue (merged) | Info | `gui.py:554-591` | Unauthenticated local GET `/api/price`, `/api/fees` (public data, Host-pinned, cache-bounded, no wallet data). Cross-ref CT-23 |
| CT-36 | Copper | Info | `gui.py:160-186` vs `:1130` | Fee-quote parser bound (≤1000 sat/vB) differs from the policy cap (25) — in-range lies availability-only |
| CT-37 | Copper | Info | `probe.py:320-334` | `_same_xpub` ignores serialization version bytes; comparison-only, no downstream effect |
| CT-38 | Blue | Info | `safe_http.py:89-99` | Trust-bundle pin fails open to platform defaults by documented design; TLS verification never disables |
| CT-39 | Blue+Copper (merged) | Info | `desktop.py:63-77` | DesktopBridge URL pin passes when the window URL is unreadable; documented; the load-bearing byte-equality check is pinned |
| CT-40 | Copper | Info | `desktop.py:260-302` | Client renderer version identity not establishable; no security decision depends on it |
| CT-41 | Orange | Info | vendored embit | Master-key fingerprints read 0x00000000; unreachable from BSMS origins — documented to preempt confusion |
| CT-42 | Red | Info | `gui.py` handler | Full handler tracebacks print to console on malformed bodies/disconnects (source mode); no secrets observed |
| CT-43 | Red | Info | `gui.py:345`; `ui.html` | Saved PSBT keeps the "-unsigned" name after verified signatures attach — mislabeled spend authority (0600, operator-initiated) |
| CT-44 | Red | Info | `gui.py` server | Default listen backlog; 1 connection reset in 160 rapid connects — resilience of the operator's own UI |
| CT-45 | Amber | Info | `scripts/build-linux.sh:375-380` | README-LINUX names `SHA256SUMS-linux-x86_64.txt`; the release ships single `SHA256SUMS` — verbatim instructions fail |
| CT-46 | Amber | Info | `AGENTS.md` ¶57 | "Current published version is 0.6.4" inside the v0.6.5 tag — stale-by-construction |
| CT-47 | Amber | Info | desktop locks ×3 | Cross-platform dependency drift (cryptography 50.0.1 vs 50.0.2, etc.); all hash-pinned; the signed DMG runs the 50.0.1 set |

*Fix-it input: each lane's full report — with exact evidence, commands, constructed
inputs, break-and-watch transcripts, and remedies — is preserved in the owner's private
record for this cycle (`bitcoin-easy-multisig-signer-colorteam-audit-private-v0.6.5.md`),
never published.*

---

*Audit performed 2026-10-06 on the public repository and published artifacts only, by
a five-specialist Color Team panel (Red, Blue, Orange, Copper, Amber) plus a White
referee, under framework v1.3.2 with definitions v2.4. The grade rules were locked in
the owner-signed plan (SHA-256 `ecc1b42e…` recorded above, equal at start and end)
before the audit began and applied as written; the plan was re-hashed at the end and
the scope never moved. No wallet material, credentials, or private data appears in this
report. An audit is evidence about one revision on one day — not a certification, not a
guarantee, and not a promise about any future version. Coverage limits are stated
above.*

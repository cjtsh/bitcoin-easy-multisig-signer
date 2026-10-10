# ZCode Color Team Security Audit — Bitcoin Easy Multisig Signer v0.6.7 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.7`, commit `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b`, release artifacts published 2026-10-07T17:10:37Z. Reconnaissance revision `d525f31` (the tag commit's documentation-only child; six Markdown files differ, no executable file differs — verified in the audit's fresh clone) |
| **Assets declared** | Ranked, all mission-critical: (1) the Bitcoin in the operator's multisig wallet; (2) signing/CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds" — owner); (3) the reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction); (4) release artifact integrity (DMG, bundles, `SHA256SUMS`/`.asc`, SBOM); (5) wallet privacy (xpubs, addresses, BSMS contents, txids, device identities) |
| **Auditor** | A five-specialist Color Team panel plus a referee (framework v1.5.0, definitions v2.4); asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `DeepSeek Harness desktop (com.deepseek.dsh)` · session `session-5d5422fc-382b-428d-93f1-71eb00cd083b` (exposed by that harness) · model `not exposed by the harness` |
| **Auditor identity** | Harness `ZCode desktop (dev.zcode.app, v3.14.4)` · session `not exposed by the harness` · model `zai-api/GLM-5.3` (declared by the harness) |
| **Independence** | Surveyor and auditor ran in different sessions: **yes** — the two session identifiers differ (one exposed, one not exposed by its harness). Different *models* rests on the two harnesses' declarations (DeepSeek harness vs Z.ai GLM), not on independent verification; both lines are declarations, as the framework requires them to be labelled |
| **Cycle** | `v0.6.7` — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`; the plan carrying this cycle is `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md` (named for the surveyed commit because a signed plan file for the v0.6.7 cycle already existed; see plan §1) |
| **Prior audit** | Cycle `v0.6.6`: report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md`, SHA-256 `e1623a984dc0f189f87dd0fd142409ba77b6b7f3fb1f032be0ad9d029cf39e68` (verified identical at tag and main), grade ⛔ BLOCKED |
| **Verification** | Independently re-derived by the referee and re-spot-checked by the lead: full suite 520/520 OK, 0 skipped (macOS, Python 3.12.14); `shasum -a 256 -c SHA256SUMS` 8/8 OK; `gpg --verify` Good signature from `Bitseeker LLC <release@bitseeker.llc>` (key `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7` = the committed `signing-key.asc`); every release-asset digest re-hashed and equal to the GitHub API digest; macOS DMG `codesign --verify --deep --strict` valid, `spctl` accepted (Notarized Developer ID, `B8G5L7M8TB`), `stapler validate` OK; candidate run #106 (`37644267740`) artifacts = published digests = candidate `SHA256SUMS` (byte-identical); source-archive files hash-identical to the tag tree (154/154 shared); two Sigstore attestations verify per asset with all subject digests matching |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`, SHA-256 `ab5c7dbb4b89ed4f485d1e6851ddab20a5950e57bd4aae5d852667d22c5fbed8` before the first agent ran and the same at the end — **equal: the scope never moved.** Owner-signed `Bitseeker LLC, 2026-10-10` (plan §9, revision 8 "final — frozen"). Lock hash published before the panel ran at commit `5742ccd` on public `main` (live-verified) |

## The grade: ⛔ BLOCKED — the wallet engine passed everything; the block falls on release-chain control integrity and a source-mode dependency pin

Three independent bindings, any one of which suffices:

1. **Ruling 4 (a lane proved its own failure state).** Blue computed **DEFENSE BROKEN** and Copper computed **EDGE TRUST BROKEN** on the same demonstrated fact (CT-73): the source-mode HWI payload check pins 2 of the 115 files in the installed `hwilib` package, while its own documentation claims "a poisoned site-packages is refused rather than believed." The referee re-derived it with a pristine hash-matched wheel: a package poisoned in any other file passes verification and its code executes during enumeration.
2. **Plan rubric condition (d): "a pipeline able to publish unverified, unsigned, or unnotarized bytes."** CT-76: thirteen historical tags (`v0.1.11`–`v0.1.23`) still freeze publish-capable workflow text — `contents: write`, `gh release delete --cleanup-tag || true`, `gh release create`, no main-branch guard, no candidate gate — dispatchable today under the active workflow registration, while the repository's own sweep script fetches `+refs/heads/*` only and never examines a tag despite its "any ref" header.
3. **The framework's open-Critical/High clause.** CT-72 (High, open, demonstrated by three lanes independently and re-derived by the referee from the actual guard bytes): the free-text `candidate_run_id` dispatch input is interpolated directly into bash at `build-candidate.yml:69`, so the numeric validation guard executes its own input — a payload like `$(code)12345` runs the code *and* passes validation.

**What this grade is NOT:** no path to either unforgivable act was demonstrated or found — every attempt to divert reviewed transaction bytes, bypass the mainnet consent gates, or exfiltrate wallet-identifying material was refused by code, in every lane and under the referee's own re-runs. No seed, PIN, or private-key handling exists anywhere. No credential value is exposed. The path to CLEARED is named in the findings ledger: fix CT-72, CT-76/CT-77, CT-73, CT-74/CT-75, land the `environment:` wiring in a tagged revision, and cut a new release for a fresh cycle.

## The four questions that matter

1. **Could this software get the operator to sign or broadcast a transaction they did not review — recipient, amount, fee, or change altered between review and broadcast?** — **No path found.** Red attacked the review→sign→finalize→broadcast chain with nine divergence classes (thief-recipient device responses, extra outputs, PSBT-metadata rewrites, wrong-fee reviews, mutated freeze bytes, concurrent double-sign, stale IDs); every one was refused by code with specific refusals, not by operator vigilance. Orange proved displayed==signed==broadcast equality, signature verification (BIP-143 published vectors verified byte-for-byte against the BIP text), finalization math, and change ownership against outside oracles — 74/74 constructed cases. The referee re-ran both batteries under its own hand. Every money-path control tested is held by a test demonstrated able to fail.
2. **Could it leak the unspeakable thing — credentials, xpubs, addresses, device identities?** — **No leak demonstrated.** Diagnostics are fixed-code with device *class* only (hostile strings dropped, verified byte-level); the session token appears in no response, page, or log; explorers receive only operator-consented derived addresses and public txids. The bounded exception class is CT-73: in *source mode* (the developer path, not the shipped app), a substituted `hwilib` file that passes the two-file pin could observe xpubs/PSBTs; frozen builds are immune (whole-binary sidecar sealed inside the notarized bundle), and doctored *device responses* are refused downstream regardless.
3. **Could a remote party, a dependency, or a local process act invisibly?** — **Locally: no.** Host/Origin/token gates, CSP nonce discipline, the absence of any HTML-injection sink, and the fragment-only token all held under direct hostile sockets, including DNS-rebinding and cross-site forms. **In the release chain: yes, by the strongest in-scope actor** (the holder of push/dispatch rights — in practice the owner's account, whose compromise is an external assumption, but whose *workflow-level abuse surface* is in scope): the CT-72 injection, the CT-76 frozen-tag publishers, and the CT-77 matcher blindness all stand demonstrated by construction. **Explorer lies:** refused everywhere tested (wrong genesis, redirects, tampered prevouts, lying outspends, lying broadcast txid); a *stalling* explorer can freeze the app (CT-84, availability only).
4. **What should be fixed first?** — CT-72 (move `candidate_run_id` to `env:`, add an interpolation lint), CT-76/CT-77 (teach the sweep about tags and non-`gh release` publishers, or retire the dangerous tags), CT-73 (pin the whole installed `hwilib` package manifest), CT-74/CT-75 (behavior-level tests for the publish guards — the string-pins stay green when the guard logic is defeated), then CT-78/CT-79 (the two missing constant/guard tripwires). The release-readiness item: land the `environment:` wiring in a tagged revision before the next promotion — the audited tag cannot notarize or publish today (it fails closed).

## The prior audit's findings: all 71 IDs accounted for

The cycle-3 (v0.6.6) report's ledger, CT-01…CT-71, was enumerated by the referee and every ID is accounted for in this cycle's ledger (ruling 8 — the round trip, not a summary):

- **Verified fixed at v0.6.6 and standing at v0.6.7 (not reopened):** CT-02…CT-12, CT-13…CT-15, CT-17…CT-21, CT-24, CT-26…CT-34, CT-43, CT-45, CT-46.
- **Partially fixed, carried forward:** CT-01 (second-publish-path root cause — the tag/matcher residual returns as CT-76/CT-77), CT-48 (its evidence cites thirteen branch commits that are unreachable objects today: "evidence no longer retrievable," neither finding nor clearance; its sweep is now tag-blind — CT-76), CT-49 (frozen-mode half verified against the published DMG; source-mode half → CT-73), CT-52 (string-pins only under logic defeat → CT-74).
- **Closed as observation/decomposition/no-recurrence (v0.6.6 dispositions, carried):** CT-16, CT-22, CT-23, CT-25.
- **Closed by dated owner acceptance 2026-10-07 (records, not re-litigated, per the plan's bounds):** CT-35 (its property recurred unchanged — the Host-only price/fees routes are recorded under it, not as a new finding), CT-36…CT-42, CT-44, CT-47, CT-61, CT-63…CT-70.
- **Open deferrals, hard expiry 2027-10-07:** CT-54 (rebuild the vendored libusb from pinned source at the next dependency bump), CT-59 (stalling-explorer scan bound — its revisit trigger fired this cycle; the new whole-app freeze fact is filed as CT-84 and the deferral is carried).
- **Verified fixed this cycle with fail-capable evidence:** CT-50, CT-51, CT-53, CT-55, CT-56, CT-57, CT-58, CT-60, CT-62, CT-71.

The repository's own claimed-fix ledger, `releases/PATCH-0.6.7.md`, was verified row by row within the plan's §8-Q4 bounds (break-and-watch on release-critical controls; no re-litigation of acceptance-closed rows). Its closing evidence holds for every row except where this cycle's findings say otherwise: CT-48/CT-52's `GuardBodyPins` go red only on *string removal*, not on *logic defeat* (→ CT-74), and CT-49's payload pin refuses only the two files it names (→ CT-73). The plan's new-in-cycle CLEARED condition — "no closing evidence pin that cannot fail, and no claimed control found defeatable as written" — is therefore not met.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED.** Attacked every input surface (12 enumerated, none undocumented): the full review→broadcast chain (T1), mainnet consent (T2), counterfeit device responses (T3), local hostile pages/processes including DNS rebinding (T6), privacy exfiltration (T11), hostile BSMS (T12), and the release workflow's input handling (T8 slice). All five declared assets held. Reported findings: the workflow command injection (CT-72, High), a fail-closed-but-unclean handler crash on non-ASCII token headers (CT-81, Low), and informational observations. Explicitly clean: value binding, consent gates, device-response acceptance, the loopback gate matrix, diagnostics/token/log privacy, BSMS parsing.

**🔵 Blue — DEFENSE BROKEN.** Inventory of 24 claimed protections (K1–K24) from the repo's own claims, judged on present/reachable/effective/fail-closed/pinned with break-and-watch on the release-critical set. Every money-path gate broke RED when defeated (the armor is real and tripwired). One control fails *Effective* (K13 → CT-73): the source-mode payload pin's claim exceeds what it checks, and the demonstrated poison passes — this sets the sub-verdict. Six controls fail *Pinned* only (K17–K20, K22-partial → CT-74/CT-75/CT-82): defeating the publish-guard *logic* leaves all 55 workflow tests green. Two Medium detection gaps in the sweep (→ CT-76/CT-77 with Amber). Sensitivity recorded by Blue and adjudicated by the referee: reading K13's claim narrowly would compute DEFENSES HOLD WITH GAPS; the repo's own words claim the package, so the computed verdict stands.

**🟠 Orange — LOGIC UNPROVEN.** Twelve invariants published first, each with an outside oracle (BIP-141/143/62/173/350/94, BIP-48/129, Bitcoin Core standardness, live chain comparisons against blockstream.info/mempool.space/mutinynet.com). Ten of twelve PROVEN — including displayed==signed==broadcast equality, signature verification against the published BIP-143 vectors (watched fail under a digest break), finalization math, change ownership across all three routes, fee/dust arithmetic, and the mainnet double gate (strict `is True` at both levels; zero HTTP before the gate). Two UNPROVEN on the *pinning* criterion only — no wrong answer was ever computed: the mainnet genesis literal (CT-78) and the bare-`/*` change-inference ban (CT-79) each survive a true-value/logic swap with the suite green. Dependency delta: the vendored embit fork = upstream + exactly the two documented edits; the substantive edit strictly *strengthens* reviewed-transaction fidelity; the wheel is byte-identical to the patched source and hash-locked in four lock files.

**🟤 Copper — EDGE TRUST BROKEN.** Five live edges audited (devices/HWI, loopback HTTP, Esplora/price servers, frozen binaries, BSMS file) against the five hostile behaviours. Every constructed *lie* about transaction bytes was refused at runtime — wrong xpubs, stranger/stale/replayed key proofs, different-transaction PSBTs, forged/high-S/wrong-sighash signatures; dies and repeats surface as safe errors or refusals; frozen-binary digests all recomputed and pinned in recipes *and* tests. Two failures: source-mode HWI substitution (CT-73 — BROKEN on Substituted) and the stalling broadcaster (CT-84 — no total deadline on outbound HTTP, and the broadcast runs under the session lock, freezing every lock-taking endpoint; Low/availability-only). Version identity is established for the shipped bundle (sidecar == SBOM == codesign seal == exact version line, verified from the mounted DMG).

**🟡 Amber — CHAIN UNVERIFIED.** The chain was inventoried link by link (13 links: actions, dependency locks, interpreter, runners, Linux toolchain, vendored inputs, build scripts, the publish gate, published-vs-candidate bytes, immutability, credential wiring, download surface, the audit plan). The T9 core is **fully verified**: every published byte traces to candidate run #106 at the same commit — 8/8 hashes equal, the published `SHA256SUMS` byte-identical to the candidate's, GPG Good, two Sigstore attestations per asset, SBOM self-bound to the commit and run, all five action pins equal to their upstream tags, all seven vendored digests recomputed and matching. The verdict is set by links that cannot be established at all: mutable hosted runner images, a floating apt/docker toolchain, and the publication-time credential wiring (CT-80 — the environments that now scope the signing secrets were created *after* the 2026-10-07 publication, so the release was signed through unprotected placement; the audited tag cannot reproduce its own release today, failing closed). No path was demonstrated by which unreviewed code reached a released artifact.

**⚪ White — PUBLISH.** Every load-bearing claim personally re-derived (CONFIRMED or CORRECTED; nothing grade-bearing unverifiable). Corrections: the three lanes' "locked plan absent / hash matches nothing" observations were wrong — the plan lives on `main` and hashes exactly to the lock value; Blue had read the prior cycle's plan file. One Red reproducer row (CSP nonce) was a harness defect — the artifact held. Two UNVERIFIABLE inferences recorded as such and not grade-bearing alone (the pre-Oct-8 secret placement; the live runner-side hops, forbidden to exercise). Grade computed with the arithmetic shown above; no dissents. Scope hash equal start-to-end; session identifiers differ; the audit is not void.

## What this audit did not do

- **No live hardware device** was attached anywhere. Every device-edge conclusion rests on constructed adversaries — real ECDSA over synthetic PSBTs and mocked HWI exchanges. The plan's §5 records this as the suite's evidence ceiling, and this audit shares it.
- **No workflow was dispatched** by the panel (hard rule). CT-72 and CT-76 rest on deterministic local mechanics plus read-only API artifacts plus documented platform behavior, not on an executed attack. The one dispatch on record (run `38056270688`) was owner-directed, post-survey, and published nothing.
- **No live explorer or broadcaster was attacked on production networks**; hostile-server conclusions rest on loopback fakes (the referee built its own).
- **Windows and Linux artifacts** were digest-verified only (Amber) — never mounted or executed; only the macOS DMG was mounted, signature-checked, and its helper executed for a version read.
- **Runner images and dependency/action internals** are uninspectable hosted/platform surface (CT-87 records the floating apt/docker links); v0.6.7's own bytes are hash-bound end-to-end downstream of them regardless.
- **The Oct-8/9 unreachable commits** are out of scope per plan §7; CT-48's thirteen cited remediation commits are unreachable objects — recorded as evidence no longer retrievable.
- **The tag's own `docs/*.html` staleness** (still pointing at v0.6.4 inside the tagged tree) was found, fixed at `fc65647`, and verified live by the survey; per the plan's §8-Q2 scope ruling it is a next-cycle publication-hygiene item, not a finding against v0.6.7. The live site is correct.
- **Carried "could not determine" items:** the actual placement of the publication-time signing secrets (inferred, CT-80); a second independent oracle for Mutinynet's block-1 hash; macOS runtime seal enforcement and the pywebview bridge at runtime; per-package PyPI identity cross-check of the 33–36 locked dependencies; whether any GitHub App or token beyond the sole collaborator can dispatch.

"Nothing found" above means "nothing found within this coverage," never "none exist."

## Appendix — findings ledger (new findings CT-72…CT-95; final numbering fixed by the referee after the lanes' independent counts collided)

| ID | Sev | Status | Location @ 81f58ec | Claim |
|---|---|---|---|---|
| CT-72 | High | Open | `.github/workflows/build-candidate.yml:69` | Command injection: the free-text `candidate_run_id` dispatch input is interpolated raw into bash inside its own validation guard — the guard executes the input it is validating (payload `$(code)12345` runs the code and passes). Found independently by Red, Blue, Amber; re-derived by the referee from the actual guard bytes. Bounded by owner-only dispatch and `contents: read` at this revision; the safe `env:` pattern already exists at `:702`. Remedy: route through `env:`, add a workflow-lint pin against `${{ inputs.* }}` in `run:` |
| CT-73 | Medium | Open | `probe.py:206-214, :311-348` | Source-mode HWI payload pin hashes 2 of 115 installed `hwilib` files; a package poisoned in any other file passes `_verify_hwi_payload` and executes during enumeration, contradicting "a poisoned site-packages is refused rather than believed." Frozen builds immune (whole-binary sidecar inside the notarized bundle); doctored device responses still refused downstream. **Sets Blue's DEFENSE BROKEN and Copper's EDGE TRUST BROKEN → ruling 4.** Remedy: pin a manifest of every installed file |
| CT-74 | Medium | Open | workflow `:57-61, :738, :978-81` | The unsigned/unnotarized publish refusal is a control whose tests cannot fail: all three refusal layers defeated simultaneously → all 55 workflow tests stay green. The guards stand and function at HEAD; the missing fail-capable evidence violates the repo's own AGENTS.md:37 standard. Remedy: behavior tests that render the release job against mocked `gh`/`shasum`/`git` and assert refusal outcomes |
| CT-75 | Medium | Open | workflow `:65-68, :710-713, :747, :844, :986-996` | Four more publish guards are string-pinned only: inverted tag-guard comparison, `shasum -c … || true` at both sites, jq `conclusion or true`, deleted main-ref `exit 1` — each defeat leaves the suite green. Same class as CT-74 |
| CT-76 | Medium | Open | `scripts/check-publish-paths.sh:61` + tags `v0.1.11`–`v0.1.23` | The sweep never examines tags while its header claims "any ref"; 13 historical tags freeze delete-and-replace publish text (`contents: write`, `gh release delete --cleanup-tag || true`, no main-ref guard, no candidate gate), dispatchable today under the active registration. **Satisfies plan BLOCKED condition (d).** Remedy: fetch `+refs/tags/*` and fail closed, or retire the dangerous tags |
| CT-77 | Medium | Open | `check-publish-paths.sh:48-49, :102-108` | Matcher blindness: `write-all`, `gh api …/releases`, `curl api.github.com/…/releases`, `action-gh-release` publishers all pass the gate. Remedy: match permission grants structurally and release-verb patterns; prefer an allowlist |
| CT-78 | Medium | Open | `network_config.py:48`; `tests/test_network_settings.py` | The mainnet genesis literal has no pinning test: a true-value Signet swap leaves the module green and a Signet explorer then passes `verify_esplora("main")`. Constants are oracle-correct as shipped; the tripwire is missing. Remedy: literal-pin all four chain constants incl. main≠Signet |
| CT-79 | Medium | Open | `wallet_service.py:313`; `AGENTS.md:23` | The bare-`/*` change-inference ban has no pinning test: removing the guard leaves `test_change_branch.py` green. Guard works today (constructed boundary case proves it). Remedy: add the direct-match BSMS shape to the test |
| CT-80 | Medium | Open | workflow (no `environment:` key at the tag); platform state | v0.6.7 was signed/published through secrets the current environment scoping did not protect (environments created ~10.5h after publication); the audited tag cannot notarize/publish today (fails closed); actual placement inferable only. Release-readiness item: land the `environment:` wiring in a tagged revision before the next promotion |
| CT-81 | Low | Open | `gui.py:638-640` | Non-ASCII `X-Local-Token` header → `TypeError`: connection killed without response, traceback to stderr. Fail-closed, no bypass; unclean refusal only |
| CT-82 | Low | Open | `gui.py:638`; `test_gui_integration.py:151-153` | Token-gate pin has no near-miss case: a last-6-chars comparison weakening stays green. Add a shared-prefix/suffix refusal case |
| CT-83 | Low | Open | workflow `:828-834` | The `release` job holds `contents: write` on every dispatch, including `publish=false` candidates. Job-level `if: inputs.publish` would withhold the grant |
| CT-84 | Low | Open | `safe_http.py:143-154`; `gui.py:1027-1035` | No total deadline on outbound HTTP; a dribbling broadcaster holds `state.lock` and freezes every lock-taking endpoint. Availability-only, recoverable; extends CT-59's family. Remedy: deadline-aware reads; move network I/O out of the lock |
| CT-85 | Low | Open | `gui.py:1262`; `desktop.py:316` | No per-connection timeout on the loopback server; stalled bodies hang one thread each (app keeps serving) |
| CT-86 | Low | Open | absence | No automated secret-value scan of repo/artifacts/logs is claimed or exists (manual grep + release verification only). Coverage debt on asset 2 |
| CT-87 | Low | Open | workflow `:562-569, :673` | Linux build toolchain unpinned (floating apt; `ubuntu:24.04` tag not digest). UNVERIFIED-by-nature links feeding the artifact path; downstream hashes bind v0.6.7's own bytes |
| CT-88 | Info | Open | `vendor/README.md:7,16` | The two embit source-archive digests are prose-only (no machine check); the wheel is locked in four lock files and the delta is test-verified |
| CT-89 | Info | Open | `probe.py:161-169` | The change-descriptor key-match check is unreachable as written (template expansion copies the same descriptor). Defense-in-depth that cannot fire |
| CT-90 | Info | Open | `network_config.py:57-58` | Practice-network outpoint recheck is single-source (the plan's named T5 asymmetry; mainnet dual-source ±2 held) |
| CT-91 | Info | Open | vendored embit `liquid/pset.py:129,138` | The sequence-coercion the fork fixed in `psbt.py` survives unused in `pset.py`; note for the next embit bump |
| CT-92 | Info | Open | `Start Easy Multisig.command` | The double-click source launcher installs embit only, so source mode ships without device support; fails closed with a clear message |
| CT-93 | Info | Open | `scripts/build-source.sh` | `signing-key.asc` is excluded from the source archive while the release notes point at it; archive-only users must fetch the repo to verify `SHA256SUMS.asc` |
| CT-94 | Info | Open | platform | Attestation REST endpoints 404 for this repo while `gh attestation verify` succeeds (2 bundles/asset); verification-path note |
| CT-95 | Info | Open | `tests/test_hardening_pins.py:331` | The `HWI_PAYLOAD_PINS` re-assertion tripwire cannot fail against real package bytes (asserts the constant only); the regression path it masks is CT-73 |

**Recurrences recorded under standing acceptances (not new findings):** the browser-mode token-history property (unchanged; the 2026-10-07 CT-70 acceptance stands) and the Host-only price/fees routes (unchanged; CT-35's acceptance stands). **Carried forward:** CT-01, CT-48, CT-49, CT-52 (partially fixed, as itemized above); CT-54, CT-59 (open deferrals, expiry 2027-10-07).

Open totals at this revision: **1 High · 8 Medium · 7 Low · 8 Info**, plus 2 deferrals.

---

# Bitcoin Easy Multisig Signer — Plain-English Safety Review

**Bitcoin Easy Multisig Signer v0.6.7 · 2026-10-10 · reviewed by a ZCode-run Color Team panel (five specialist AI agents and a referee), under the owner-signed audit plan for this cycle**

## ⛔ BLOCKED — the money-handling engine passed every test we threw at it; the block is about how releases are built and checked, not about what the app does with your Bitcoin

This review was written for the person this software is actually for: a fiduciary, family
member, or trusted advisor managing Bitcoin that must survive them. Every statement here
is drawn from — and can be checked against — the full technical report above, produced
this same day by the panel named below. The evidence is public; the last section tells
you where.

## The questions that matter

**Can this app get me to sign and send Bitcoin somewhere I didn't approve?**
No path to that was found — not for trying. A dedicated attacker-agent spent its whole
run trying exactly this: fake devices returning thief-paying transactions, altered
amounts and fees after the review screen, swapped recipients, replayed approvals. Every
single attempt was refused by the app's own code, before anything reached a signer or
the network. A second specialist re-derived the math independently against the Bitcoin
protocol's own published test vectors — every signature check, amount, fee, and
transaction ID computed correctly. The one confirmation screen you see before a real
Bitcoin send is bound, in code, to the exact bytes that get signed and broadcast.

**Could it leak the family's wallet details — addresses, xpubs, who signs?**
No leak was found. The app's diagnostics carry only fixed error codes and a device
*class* (never a serial number or name); the session token appears in no response, page,
or log; the block explorer servers learn only the addresses you chose to scan. One
bounded exception exists for developers running the app from source: a tampered
supporting library could slip past a check that guards only 2 of that library's 115
files. The app you download is not affected — its library bytes are sealed inside the
signed, notarized bundle.

**Could someone act invisibly — change behavior without the owner seeing?**
On your machine: no — hostile web pages and local processes were directly attacked and
refused. Where the audit did find trouble is the **factory**: the automated pipeline
that builds and publishes releases. Three problems, all demonstrated: a text field on
the build form can trick the build's own safety check into running attacker-supplied
commands; thirteen very old release points in the project's history still contain
unguarded "delete-and-republish" machinery that today's safety sweep never looks at; and
several of the pipeline's safety checks have tests that stay green even when the checks
are broken. None of these was used — but a lock that has never been picked is still a
lock worth fixing, and under this audit's pre-committed rules, that combination blocks
the grade.

**What does the grade mean — and not mean?**
The rules were locked in writing before anyone looked at the code, and the grade is the
*lowest* score the panel's evidence forces — never an average, never a judgment about
the team. BLOCKED here means: *do not build the next release from this revision until
the named factory problems are fixed.* It does **not** mean the v0.6.7 app you may
already hold is unsafe — every published v0.6.7 byte was independently verified this
cycle (hashes, signature, notarization, and traceability to the exact build run), and
the money path passed everything. It also is not a guarantee of anything for any future
version. Your own eyes still matter: verify the recipient and amount on the hardware
device's screen every time — that is the one check no audit can do for you.

## How this review was done

Five independent specialist agents examined the same revision with one job each —
attack, defense, math, edges, and factory — none seeing the others' work; a sixth
referee agent re-derived every claim the verdict rests on, personally re-running the
heaviest demonstrations. The scope was locked by a plan the owner signed before the
panel ran, hashed before and after (identical), and the grade was computed from
pre-written rules, not chosen.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Try to steal or silently redirect the Bitcoin | 12 input surfaces attacked, every declared asset held; found the build-form command-injection channel |
| 🔵 BLUE · The defender | Prove every claimed protection actually holds and is tripwired | Every money-path tripwire fired when broken; one claimed library check proved weaker than its own description; several factory checks have tests that cannot fail |
| 🟠 ORANGE · The logic specialist | Check the math no one can afford to get wrong | 10 of 12 invariants proven against Bitcoin's own published test vectors; 2 proven correct but missing their tripwire; zero wrong answers found |
| 🟤 COPPER · The edge specialist | Assume every device, server, and file the app trusts turns hostile | Every transaction-byte lie refused; a slow-dribbling server can freeze the app (recoverable); source-mode library substitution passes |
| 🟡 AMBER · The supply inspector | Trace how the shipped bytes were born | Published v0.6.7 bytes verified end-to-end to the exact build run; the unverifiable links are the hosted build machines and the floating Linux tools |
| ⚪ WHITE · The referee | Distrust everyone; compute the grade and gate publication | Every load-bearing claim re-derived and confirmed/corrected; grade computed ⛔ BLOCKED on three independent grounds; report cleared for publication |

## The audit trail

**Read this first:** across all six examiners, **no way was ever found to do either
unforgivable thing** — no unapproved transaction can be signed or broadcast, and no
fake build under the owner's identity was possible through the audited path. Everything
below is about manufacturing discipline and safety margins.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| **DANGER SIGN — in the factory, not the app** | The release pipeline's ID field executes supplied commands inside its own validation, before validating (CT-72, High); thirteen frozen historical release points carry unguarded delete-and-republish machinery the current sweep cannot see (CT-76); the sweep also misses publishers that don't spell "gh release" (CT-77). None was exploited; all three were demonstrated by construction. | Report §Appendix |
| **IMPORTANT TO FIX** | A claimed library-integrity check guards 2 of 115 files in source mode (CT-73) — the shipped app is sealed differently and unaffected; five release-path safety checks have tests that stay green when their logic is broken (CT-74/75); the genesis-hash constant and one change-address rule lack their tripwire (CT-78/79); the release-signing credentials' protection postdates this release (CT-80). | Report §Appendix |
| **MINOR IMPROVEMENT** | A stalling server can freeze the app until it answers (CT-84, recoverable); an unclean refusal on malformed tokens (CT-81); a too-trusting test (CT-82); the release job holds write power on test builds (CT-83); no automated secret scan (CT-86); unpinned Linux build tools (CT-87). | Report §Appendix |
| **HOUSEKEEPING** | Prose-only provenance digests, unreachable defensive checks, single-source practice-network cross-checks, and similar notes (CT-88…CT-95). | Report §Appendix |

## What this review does not cover

Version-locked to `v0.6.7` at commit `81f58ec`. No physical hardware wallet was
attached — device behavior was tested by constructed responses, the same ceiling the
project's own test suite declares. No release workflow was actually dispatched. Windows
and Linux artifacts were verified by digest only. The AI panel complements — does not
replace — a qualified human firm. "Nothing found" means "within this coverage."

## Check our homework

| Artifact | Where |
|---|---|
| This full report (technical + safety + ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` — this repository |
| The one-page public security statement | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.7.md` — this repository |
| The signed audit plan + scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md` + `…-audit-lock-v0.6.7.md` — this repository |
| The cycle index (every audit this project has had) | `bitcoin-easy-multisig-signer-colorteam-audit-index.md` — this repository |
| The audit method itself | `cjtsh/ai-color-team-audit-framework` (v1.5.0) — public on GitHub |

You can read every page of the evidence yourself.

---

*Audit date 2026-10-10. Auditor: ZCode Color Team panel (lead harness ZCode desktop v3.14.4, model zai-api/GLM-5.3, declared), referee-gated. Surveyor: DeepSeek Harness (session exposed, model not exposed). Performed on the public repository and published artifacts only; the grade rules were locked before the audit began and applied as written; no wallet material, credential value, or secret appears in this report; an audit is evidence about one revision on one day — not a certification, not a guarantee. The companion security statement for this release is `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.7.md`.*

# Audit plan — bitcoin-easy-multisig-signer

**Cycle:** `v0.6.8` — the **first** cycle of this plan lineage. There is no carried-forward plan:
this is a fresh baseline survey, and every scope-bearing statement below is derived from the
owner's own statements of condition plus a first-hand inventory of the tree at the target
revision. No prior report, plan, lock or grade is an input to this document.

**Surveyor:** the Surveyor seat of the Color Team framework, run on the DeepSeek Harness
(provenance in §0). The surveyor wrote this plan only. It did not hash or lock it, did not run
the audit, and did not commit it.

**Written:** 2026-10-11T03:57Z, under the surveyor runbook at framework tag `v1.5.1`. The owner's
statements of condition were given under Color Team definitions framework tag `v1.5.0`; where the
two differ, the owner's statement governs the scope and the runbook governs the form.

**How to read this plan.** Sections 1–8 are the surveyor's findings and proposed scope. Section 0
is the frozen contract: it is written last and repeats the scope in full, so nothing in it points
elsewhere. Section 9 is left empty for the owner — it is step two, and no AI writes in it.

---

## 0. Locked scope

**Definitions in force.** Color Team definitions framework tag `v1.5.0` (the owner's statements),
read against the surveyor runbook at framework tag `v1.5.1` (lane roster: Red, Blue, Orange,
Copper, Amber, White referee). The v1.5 obligations travel with this plan: a mandatory one-page
**Public Security Statement** as a release-specific audit deliverable, written by the auditor
after testing and not by the surveyor; and the explicit evidence budget and stop condition stated
at the end of this section.

**Cycle lineage.** **First audit — fresh baseline.** This plan carries no scope forward from any
earlier cycle, and it is not a continuation of any earlier plan. Recommendation and independent
re-check of prior findings do not apply to this cycle:

| Lineage field | Value |
|---|---|
| Original signed plan carried forward | **none** — this is the first plan in this lineage |
| Prior finding IDs to re-check | **none** — no prior ledger is an input |
| Immediately prior report | **none is an input.** The repository's earlier AI audit reports and its earlier Color Team reports are history and are excluded as evidence per the owner's independence condition. They were removed from `main` for this cycle and survive only in the tagged trees; they are named, path by path, under "The legacy audit artifacts inside the audited tree" in §6. The one bounded exception is recorded under "Exclusions" below |
| Cycle name | `v0.6.8` |
| New finding IDs | A new ledger begins at **CT-01** for this cycle. The panel must not reuse an ID from any earlier cycle, because those ledgers are not inputs and an accidental collision would read as a carried finding |

**Exact target revision.**

| Field | Value |
|---|---|
| Repository | `https://github.com/cjtsh/bitcoin-easy-multisig-signer` (public, MIT, not a fork, not archived) |
| Default branch | `main` |
| Target release | **`v0.6.8`** |
| Tag → commit | `v0.6.8` → `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`), committed `2026-10-10T17:13:08-04:00`, subject "Make the second candidate's tests hold on Windows and in the archive" |
| `version.py` at the tag | `APP_VERSION = "0.6.8"` (`version.py:3`) |
| Published artifacts | the `v0.6.8` GitHub release, **published `2026-10-10T21:31:47Z`, 10 assets**: `bitcoin-easy-multisig-signer-v0.6.8.tar.gz`, `Bitcoin-Easy-Signer-v0.6.8-macOS.dmg`, `Bitcoin-Easy-Signer-v0.6.8-windows-x64.zip`, `Bitcoin-Easy-Signer-v0.6.8-linux-x86_64.AppImage`, `Bitcoin-Easy-Signer-v0.6.8-linux-x86_64.tar.gz`, `BUILD-SBOM.json`, `BUILD-SBOM-linux-x86_64.json`, `BUILD-SBOM-windows-x64.json`, `SHA256SUMS`, `SHA256SUMS.asc` |
| Tree size | 223 tracked files, 348 commits, 2026-09-27 → 2026-10-10; 69 tags |
| Revision rule | Every repo claim in the audit report carries `file:line @ 0d4e01f`. The released **artifacts** are in scope as bytes, but a claim about them must name the release asset, not a tree path |

**Declared assets, ranked (the owner's statements, §1).** The owner declares that **no asset is
optional**: the ranking orders severity, not attention, and a demonstrated path to breach any of
the five is at least CONDITIONAL. A finding may never be dismissed as low-priority because its
asset is ranked fifth.

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GPG release key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. Owner: **"loss of credentials is the same thing as loss of funds."** |
| 3 | The reviewed-transaction integrity chain (frozen prepared payment → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG, the platform bundles, `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten; the public download surface never points at bytes the pipeline did not produce |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

**The unforgivable acts, in plain words (the owner's statements, §2).**

1. The app gets the owner to sign and broadcast a transaction that sends their real Bitcoin
   somewhere they did not approve — a thief's address, a wrong amount, or change quietly
   redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the app
   leaks the wallet's addresses and xpubs so strangers can watch and target the family's savings.

**The rubric as adapted to this target (the owner's statements, §3).** These conditions, and no
others, decide the grade:

| Grade | Conditions that must hold here |
|---|---|
| ✅ CLEARED | The panel finds no path, in in-scope code at `0d4e01f`, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's; (e) expose a credential value. The invariants in `AGENTS.md` hold as stated, with the test evidence the repo claims |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, credential handling, or the release chain in a way that needs an owner decision — including a gap that only opens under explorer misbehavior, device-firmware trust assumptions, or stated invariants that lack the test coverage the repo claims |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check |

**"The operator should have noticed" is never a defense** (owner, 2026-10-06). Any safety property
that depends on the operator spotting a discrepancy is a weakness the panel must report, not a
mitigation it may assume.

**In scope.** The threats the panel must resolve, frozen. Each is grounded in the tree at
`0d4e01f`, is stated in full with its entry point and acceptance test in §5, and is to be answered
with a recorded outcome of HOLDS, BROKEN, or UNPROVEN:

- **Asset 1 — Bitcoin:** T-01 transaction substitution across the signer boundary; T-02 signer
  metadata injection; T-03 final-transaction divergence at the broadcast screen; T-04 stale or
  swapped prepared payment; T-05 mainnet consent bypass; T-06 wrong-network selection or a
  same-genesis Signet masquerading as the chosen chain; T-07 already-spent outpoint selection;
  T-08 fee manipulation; T-09 change redirection through an inferred `/1/*` branch; T-10
  outcome-unknown broadcast mishandled as success or blindly retried; T-11 pending-payment pause
  bypass; T-12 counterfeit device or key-proof forgery; T-13 poisoned HWI payload; T-16 an
  unsigned PSBT input that does not match the independently fetched historical transaction.
- **Asset 2 — credentials and the release workflow:** T-14 credential value committed, archived,
  or logged; T-15 a push alone building or publishing; T-17 dispatch-input command injection;
  T-18 publish without signature or notarization; T-19 an over-broad workflow token on a
  non-publishing run; T-20 the repository-controlled platform controls not being what the
  workflow's comments say they are.
- **Asset 3 — integrity chain:** T-21 prepared-payment state replaced between review and
  finalization; T-22 old signer/final panels left visible under a new review.
- **Asset 4 — release artifacts:** T-23 publication of bytes that are not the verified
  candidate's; T-24 tag or release-asset overwrite; T-25 a second publish path on another branch
  or tag; T-26 the public download surface pointing at non-pipeline bytes; T-27 checksum/attestation
  and SBOM disagreement with the published assets.
- **Asset 5 — wallet privacy:** T-28 wallet material in diagnostics or logs; T-29 wallet material
  reaching a server other than the operator's chosen Esplora, or a redirect/TLS downgrade; T-30
  wallet artefacts committed to the tree; T-31 operator state files readable beyond the operator.

**Out of scope, and why.** The frozen list, each with its reason:

- GitHub account security, GitHub platform compromise, and stolen owner credentials — declared
  external assumptions by the owner; recorded once, never graded.
- The owner's tools going rogue, and standing automation anywhere outside this repository —
  declared external assumptions; recorded once, never graded, and no inventory is sought
  (see §6, *Authorised agentic operation, and no automation*).
- Forks and third-party builds — a fork cannot publish under this identity and is not this
  audit's subject.
- The correctness of the Bitcoin protocol, of Esplora software, of hardware-wallet firmware, of
  `pywebview`/WebKit/Edge, of Python and the OS, and of the pinned third-party libraries at their
  pinned versions — trusted or assumed, with the trust boundary named per threat in §5.
- The prior AI audit reports, the prior-review PDFs that were served from `docs/audits/`, and the
  earlier Color Team reports — history, excluded as evidence; all were removed from `main` for
  this cycle and are named path by path in the subsection below. Bounded exception: the immediately preceding
  Color Team report and the repository's own remediation ledger (`releases/PATCH-0.6.8.md`,
  `releases/OWNER-ACCEPTANCE-2026-10-07.md`) are available to the **White referee** only; the
  specialist lanes run without them.
- Historical tags that freeze pre-guard workflow text — judged by what they can *do* from their
  own ref, and the enumerated case is a recorded residual (T-25), not a new finding class.

**Not examined, and why.** This list is exhaustive; the panel may not read these as settled:

- The **published `v0.6.8` artifact bytes** — outside the tree (published after the tag); examining
  them is the panel's work under T-23 and T-27.
- The **live GitHub platform posture** — `git` cannot show it and `releases/platform-state.json` is
  a dated record (`2026-10-10T18:20:10Z`); the panel must re-read it under T-20.
- The **owner's machine and account state, and any scheduled tasks** — declared external
  assumptions, recorded as *untested — owner-declared*; no artefact is required.
- **Hardware-wallet firmware and adversarial device behaviour** — outside the app's own verification
  code (T-12); physical device testing is the owner's, not the panel's.
- **Practice-network second-source cross-checking** — it does not exist by design
  (`network_config.py:57-58`); recorded as an owner-accepted residual under T-07 rather than
  searched for as a missing control.
- **The two retired input workflows** (`linux-inputs.yml`, `windows-inputs.yml`) beyond establishing
  that they publish nothing; their only office is to regenerate hash locks.

**Excluded by demonstration.** **None.** At survey time the surveyor demonstrated no path to an
unforgivable act, and nothing was excluded from scope on the strength of a demonstration. This
field stays empty unless and until the panel demonstrates a path and the owner narrows the scope
in response.

**Gaps the panel inherits.**

1. The owner's statements of condition (`owners-audit-stattement.md`) live on `main` at commits
   `2ee7747` and `0156db3` and are **not present in the `v0.6.8` tree** (`git ls-tree HEAD` does
   not carry them; `0156db3` is not an ancestor of `0d4e01f`). The statements are therefore an
   owner-supplied scope document that post-dates the audited revision, reproduced verbatim in
   this plan (§0, §1, §2, §3, §6). The panel must not cite them as though they were in the audited
   tree.
2. The published `v0.6.8` artifacts were published after the tag and are not in the tree. Their
   verification requires fetching them and the GitHub attestation API — read-only access the owner
   authorises. The surveyor exercised that route on 2026-10-11: the ten assets match `SHA256SUMS`,
   `SHA256SUMS.asc` verifies against `signing-key.asc`, and one Sigstore attestation binds all ten
   digests to `0d4e01f`. That confirms the route works; T-23 and T-27 remain the panel's own
   evidence to produce.
3. `releases/platform-state.json` was recorded `2026-10-10T18:20:10Z`, before the release at
   `21:31:47Z`. It is a point-in-time record, not live state; the panel must re-read the platform
   (see T-20).
4. The tree the surveyor read is a local clone at the tag. A re-check at lock time must confirm
   the tag still resolves to `0d4e01f` and that `main` has not moved under the audit.

**What the surveyor verified before signature (starting state, not panel evidence).**

Checked read-only on 2026-10-11. Each line says what was done and what was found, so the panel starts
from a known position. None of it discharges a threat row: the panel re-establishes its own evidence,
and a claim here that turns out wrong is a defect in this survey to record, not a finding to inherit.

- **The ten published `v0.6.8` assets.** Downloaded from the release. `shasum -a 256 -c SHA256SUMS`
  returns OK for every file the manifest lists (eight; the manifest does not list itself or its
  signature). `gpg --verify SHA256SUMS.asc SHA256SUMS` returns GOODSIG from
  `Bitseeker LLC <release@bitseeker.llc>`, RSA `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7`, made
  2026-10-10.
- **Attestation.** One Sigstore attestation covers all ten subjects, and every subject digest matches
  the published bytes. It records `predicateType https://slsa.dev/provenance/v1`, workflow
  `.github/workflows/build-candidate.yml`, ref `refs/heads/main`, event `workflow_dispatch`, and
  `resolvedDependencies[0].digest.gitCommit = 0d4e01f60c7695d720099f9d8e9e23b38da63102`.
- **The producing run.** Run `38087360421`, `workflow_dispatch` on `main`, `head_sha 0d4e01f…`,
  conclusion `success`, 2026-10-10T21:22:18Z → 21:31:51Z — bracketing the release published
  2026-10-10T21:31:47Z.
- **SBOMs.** All three are CycloneDX 1.6, name `bitcoin-easy-multisig-signer`, version `0.6.8`
  (33, 29 and 31 components), listing embit `0.8.2+besa.1`, hwi `3.2.0`, pywebview `6.2.1` and
  libusb `1.0.30`.
- **The source archive.** 186 entries. Its root carries about twenty project documents and **no**
  Color Team artifact of any kind, because `scripts/build-source.sh` ships an explicit allowlist. It
  carries `signing-key.asc` byte-identical to the repository's (sha256
  `812f790d37c6a5b97e0e27e536b1371657ac6d8052e33899f331ca9b03ddc54b`) and `version.py` with
  `APP_VERSION = "0.6.8"`.
- **Live repository and platform state.** The `v0.6.8` release exists with ten assets;
  `refs/tags/v0.6.8` resolves to `0d4e01f`; one branch, no forks; the recorded platform state is
  dated 2026-10-10T18:20:10Z and is a point-in-time record the panel must re-read (T-20).
- **No standing automation in the tree.** No `schedule:` and no `cron:` anywhere; the release
  workflow's only trigger is `workflow_dispatch`; the two retired input workflows are push-triggered
  on their own branches, regenerate hash locks, and publish nothing.

**Agent provenance.**

| Field | Value |
|---|---|
| Harness | **DeepSeek Harness** (`__CFBundleIdentifier=com.deepseek.dsh`) |
| Session ID | `session-9dc3f632-29dc-4ce5-adc8-4a79a72b6a98` — read verbatim from the environment variable `DSH_SESSION_ID` |
| Model | **not exposed by the harness** (no model was declared by the operator; the surveyor does not guess or infer one) |
| Declared by | operator handle `cjtsh` (Bitseeker LLC) |
| Survey date | 2026-10-11 |

**Evidence budget and stop condition (framework `v1.5` obligation).**

- **Budget.** The panel works from the tree at `0d4e01f` and the ten published `v0.6.8` assets.
  Every repo claim carries `file:line @ 0d4e01f`; every artifact claim names the asset and its
  digest. No claim is sourced from a prior report, plan, lock, or grade.
- **Environment.** The suite runs on the pinned interpreter: Python 3.12.10 with the locked
  dependencies (`requirements-ci.txt`, `requirements-ci.lock`, `vendor/`). On any other interpreter
  the imports fail first — `ModuleNotFoundError: No module named 'embit'` is an environment state,
  not a defect, and it stops `tests/test_controls_inventory.py` from running at all. A panelist who
  meets it records the interpreter and the pin instead of filing the import error.

- **Stop condition.** Coverage stops when every in-scope threat row in §5 has a recorded outcome
  of HOLDS, BROKEN, or UNPROVEN with its evidence attached. A row with no evidence is recorded
  **UNPROVEN** and blocks CLEARED. Scope is not expanded mid-cycle: a new candidate threat is
  recorded as a next-cycle recommendation, not swept in.
- **Artifact.** The cycle's release-specific **Public Security Statement** — one page — is written
  by the auditor after testing, alongside the report. It is an audit deliverable and is **not**
  written by the surveyor.

**Operator model and report audiences (the owner's statements, §4).**

The target operator is a nontechnical fiduciary or family member — a lawyer, trustee, accountant,
spouse, or trusted advisor settling an estate that includes Bitcoin. They know Bitcoin is dangerous
and cannot audit the app themselves. The report has two audiences and must serve both: (a) that
nontechnical trusted advisor, who needs plain-language evidence of diligence — thorough,
best-effort, and explicitly *not* a guarantee; and (b) the agent that will fix what the audit finds
— every finding must be precise, located, and reproducible enough to serve directly as fix-it
input, so the improvement loop can re-run the audit on the revision.

**One vocabulary correction the panel must honour** (the owner's statements, §4): the product's
documented posture is a *networked loopback desktop app plus hardware signing plus public Esplora
servers* — "airgap", "air-gapped", "offline machine" and "watch-only" appear nowhere in the project,
the app holds no wallet key, it never receives a PIN, and it never asks for seed words. The report
must describe the product in those actual terms rather than importing airgap vocabulary it does not
have.

**Risk residuals the review treats as gates, not assumptions (the owner's statements, §6).**

Tag rulesets, environment protection, and least-privilege tokens are external controls the audit
must not take on faith. As directed: `main` is protected against deletion and non-fast-forward
pushes with no bypass actor, so the protection applies to the owner's own tooling as well; tags are
protected against deletion and force-moves, while tag creation is deliberately left unrestricted so
the release job can still create the release tag; the two signing environments carry a `main`-only
branch policy and, by the owner's explicit decision, no required reviewers; and the release job
holds `contents: write` on every dispatch. These are recorded as residual risk and release-readiness
gates, and the panel must state what it verified itself versus what it took on the document's word.

**Owner's statements of condition.** Reproduced verbatim in this plan, section by section, as the
owner supplied them (`owners-audit-stattement.md`, `main`); the surveyor has not edited them, and
nothing else in this repository amends them.

*Carried in the audit plan, not as owner conditions:* the framework `v1.5` obligations (the
mandatory one-page Public Security Statement and the explicit evidence budget and stop condition),
the out-of-scope list, and the not-examined list. Those belong to the audit's scope and evidence
record, which is the plan.

---

## 1. Target and revision

- Repository `cjtsh/bitcoin-easy-multisig-signer`, public, MIT, default branch `main`, not a fork.
- Audited release **`v0.6.8`**, tag = commit `0d4e01f60c7695d720099f9d8e9e23b38da63102`
  (`0d4e01f`), committed `2026-10-10T17:13:08-04:00`.
- Published artifacts: the `v0.6.8` release of `2026-10-10T21:31:47Z`, 10 assets (listed in §0).
- `version.py:3` carries `APP_VERSION = "0.6.8"`.
- What this revision is, in the repository's own words: `CURRENT-STATUS.md:3-6` calls 0.6.8 "the
  Color Team cycle-4 build-process remediation of the `v0.6.7` tree," with a per-finding row in
  `releases/PATCH-0.6.8.md` and `CONTROLS.md` as the parsed inventory of claimed controls. The
  panel must treat that as a **claim to verify**, not as fact: the statement is in the audited
  tree, and no control may be credited because the repository says so.
- The panel must not state a "latest published release"; the published set is whatever the release
  page carries. `AGENTS.md` records that this specific sentence is a known trap.

**The owner's direction on the target revision (the owner's statements, §5).** The audited revision
is the **published release `v0.6.8`** — tag
`0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`, committed 2026-10-10T17:13:08-04:00) —
together with the release artifacts the repository published on **2026-10-10T21:31:47Z**.

## 2. The declared assets (ranked)

The owner's declarations, reproduced verbatim (the owner's statements, §1).

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GPG release key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** — stolen credentials enable a fake build, which enables theft |
| 3 | The reviewed-transaction integrity chain (frozen prepared payment → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG, the platform bundles, `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten; the public download surface never points at bytes the pipeline did not produce |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

**No asset is optional** (owner, 2026-10-06): the ranking orders severity, not attention. All five
assets are mission-critical; a demonstrated path to breach any of them is at least CONDITIONAL, and
no finding may be dismissed as low-priority because its asset is ranked fifth. The operative ranked
list frozen into the contract is the one in §0.

## 3. The unforgivable acts (in plain words)

The owner's declarations, reproduced verbatim (the owner's statements, §2).

1. The app gets the owner to sign and broadcast a transaction that sends their real Bitcoin
   somewhere they did not approve — a thief's address, a wrong amount, or change quietly
   redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the app leaks
   the wallet's addresses and xpubs so strangers can watch and target the family's savings.

A demonstrated path to either is ⛔ BLOCKED by definition, with no judgement call left to the panel.
The operative statement frozen into the contract is the one in §0.

## 4. Where the assets live

The map below is what the surveyor found by reading the tree. It is orientation for the panel, not
exhaustive: §5 names the entry point for each threat.

**The product boundary.** A networked loopback desktop app, plus hardware signing, plus public
Esplora servers. The app holds no wallet key, never receives a PIN, and never asks for seed words.
"Airgap", "air-gapped", "offline machine" and "watch-only" are not this product's terms and must
not be imported into the report.

**Asset 1 — the Bitcoin.**

- The one engine for every network: `probe.py` (BSMS parse, device identity), `wallet_service.py`
  (scan, outpoints, PSBT build, broadcast), `signing.py` (signature binding, finalization),
  `gui.py` (loopback API, session state, gates), `ui.html` (the screen), `desktop.py` (Mac
  WebKit window), `network_config.py` (chain parameters), `safe_http.py` (bounded, redirect-refusing
  HTTP). `AGENTS.md` forbids a second transaction or signing engine for a network.
- Wallet scope: a single BSMS file; a quorum of two or three total keys, threshold from the file
  (`wallet_service.py:47-49`, refusal of larger sets at `probe.py:166-167`).
- The review→sign→finalize→broadcast chain: `PreparedPayment` frozen state `gui.py:276-313`; the
  review-id binding `gui.py:926-940`; signing `gui.py:942-1000`; finalization `gui.py:1002-1028`;
  the review-vs-final comparison `gui.py:1030-1043`; broadcast `gui.py:1045-1133`.
- Consent gates: per-transaction final-screen confirmation `gui.py:1049`; mainnet backend opt-in
  `gui.py:1051` and `wallet_service.py:86-87` (default `False`, so a caller that omits it fails
  closed).
- Broadcast pre-checks: outpoints against one source for practice networks and two for mainnet
  (`wallet_service.py:190-242`, `network_config.py:57-58`); the broadcaster verified at use on
  every network (`gui.py:1082`).
- Device trust: HWI distribution pinned as a whole-payload manifest (`probe.py:211`, `:418-451`);
  per-device key proof (`probe.py:723-772`).
- Change policy: inferred BIP48 `/1/*` only for the exact standard 2-of-3 case
  (`wallet_service.py:299-333`, `:355`).

**Asset 2 — credentials and the release workflow.**

- The single publish path: `.github/workflows/build-candidate.yml`, dispatch-only, jobs `version`
  (:1-83), `source` (:84), `macos` (:181), `windows` (:419), `linux` (:576), `checksums` (:767),
  `candidate-manifest` (:915), `release` (:978). Top-level permission `contents: read`; write
  grant only on the `release` job (`:987`) gated by `if: ${{ inputs.publish }}`.
- Guard rails inside it: the publish-path sweep gate `:53`; the unsigned-publish refusal `:58-61`;
  the default-branch and candidate-run-id guards `:70-83` (value through `env:`, per the CT-72
  shape); the source-archive secret scan `:153-174`; the notary-credential fail-closed check
  `:249-264`; candidate binding and checksum verification `:785-834`; GPG signing of `SHA256SUMS`
  `:879-898`; release-byte verification `:994-1005`; the notarization refusal `:1101-1104`; the
  tag no-overwrite guard `:1107-1118`; the release command `:1120`.
- The signing environments: `apple-signing` (`:189`) and `release-signing` (`:775`).
- The sweep itself: `scripts/check-publish-paths.sh` — remote heads and tags (`:131-132`), the
  allowlist (`:85-87`), fail-closed on an unreadable body (`:77`, `:194`), legacy-tag residual
  (`:89-96`).
- Platform state recorded and re-read: `releases/platform-state.json`,
  `scripts/check-platform-state.sh`, `tests/test_platform_state.py`.
- Secret handling: `scripts/scan-secrets.py` with a pinned scanner
  (`requirements-ci.txt`, `requirements-ci.lock`).

**Asset 3 — the reviewed-transaction integrity chain.**

- The chain itself is the Asset-1 chain above; the distinct integrity surface is what may enter it.
  `signing.py:156-184` (`accept_signature_update`) clones the reviewed PSBT and imports only
  partial signatures; `signing.py:37` enforces BIP-62 low-S; `signing.py:258-315`
  (`finalize_multisig`) re-verifies every signature and refuses a changed txid or an output total
  above the input total.
- The screen must not keep stale state: `ui.html` clears the old signer/final panels when a payment
  changes, and `tests/ui_state_reuse.cjs` covers it (`AGENTS.md`).

**Asset 4 — release artifacts.**

- The one pipeline (above), plus `SIGNING.md` (what each platform's download carries and the
  release-key policy), `RELEASE-PROCESS.md` (the build/promotion contract and §5 audit tripwires),
  `signing-key.asc` (the committed public release key), `scripts/build-sbom.py`, and the source
  archive built by `scripts/build-source.sh`.
- The public download surface: `docs/` (`index.html`, `privacy.html`, `user-manual.html`,
  `llms.txt`), GitHub Pages environment, and the release page itself.

**Asset 5 — wallet privacy.**

- Diagnostics: `gui.py:71-93` (fixed stage/outcome sets), `_clean_token` `gui.py:402`,
  `_device_class` `gui.py:422`, `note` `gui.py:498-527` (80-event buffer, anything failing the
  token check is dropped, not escaped), `save_diagnostic_report` `gui.py:428`.
- Outbound boundary: `safe_http.py` (`_RefuseRedirects` `:159-184`, `open_url` `:259-281`,
  `_ssl_context` `:218-230`, `Deadline` `:51`), `network_settings.py` (`validate_esplora_url`
  `:52-72`, `verify_esplora` `:122-151`), `wallet_service.explorer_get` `:138-187`.
- Operator state files: `save_prepared_psbt` `gui.py:342` with `assert_private_file` `gui.py:315`;
  settings written 0600 under a 0700 directory (`network_settings.py:99-119`).

## 5. In scope

Each row is a threat the panel must resolve to HOLDS, BROKEN, or UNPROVEN. The fields are, in
order: **(1)** asset at risk and the attacker capability assumed; **(2)** the repository-controlled
entry point and the trust boundary crossed; **(3)** the prohibited outcome; **(4)** the observable
acceptance test or evidence that settles it; **(5)** exclusions and assumptions; **(6)** what its
failure blocks. The panel may add evidence routes but may not drop a row.

### Asset 1 — the Bitcoin

**T-01 — Transaction substitution across the signer boundary.**
1. Asset 1. Attacker capability: a signing device (or a process impersonating HWI) returns a
   signature over, or a PSBT containing, a transaction other than the reviewed one.
2. Entry: `gui._sign` `gui.py:942-1000`; `signing.accept_signature_update` `signing.py:156-184`;
   device call `probe.sign_psbt_with_device` `probe.py:626-640`, timeout 600 s
   (`probe.py:550`). Boundary: app ↔ hardware signer.
3. Prohibited: any signed or finalized bytes differing from the frozen reviewed payment.
4. Evidence: the refusal "The device returned a different transaction, so it was refused."
   (`gui.py:942-1000`); `before.tx.serialize() != after.tx.serialize()` refusal and input/output
   count refusals (`signing.py:156-184`); the final-vs-review comparison `gui.py:1030-1043`
   producing "The final transaction differs from the reviewed payment." The panel must break the
   control on a disposable copy and watch the named test go red — a green suite is not evidence.
5. Exclusions: the device's own firmware display is trusted; the panel does not evaluate device
   firmware. Assumption: the operator confirms on the device screen.
6. Failure blocks: CLEARED. A demonstrated path is an unforgivable act (⛔ BLOCKED).

**T-02 — Signer metadata injection.**
1. Asset 1 (and Asset 3). Attacker capability: a signer response rewrites PSBT metadata (fee,
   outputs, derivations) rather than adding a signature.
2. Entry: `signing.accept_signature_update` `signing.py:156-184`; prepared state stored by
   `replace(payment, psbt_base64=...)` `gui.py:942-1000`. Boundary: app ↔ device response.
3. Prohibited: any metadata from a device response entering prepared-payment or review state.
4. Evidence: `accept_signature_update` builds `merged` from `before.to_base64()` and copies only
   `received.partial_sigs`, then re-runs `verified_input_signatures`; the panel must demonstrate
   that a device that changes metadata while adding a valid signature cannot move the review.
5. Exclusions: none beyond T-01.
6. Failure blocks: CLEARED.

**T-03 — Final-transaction divergence at the broadcast screen.**
1. Asset 1. Attacker capability: state changes between review and broadcast so the broadcast bytes
   differ from what the operator approved (the owner's own observed 0.2.1 defect is the shape).
2. Entry: `gui._check_final_review` `gui.py:1030-1043`; broadcast `gui.py:1045-1133`. Boundary:
   review state ↔ final bytes.
3. Prohibited: broadcasting a txid, fee, recipient, or change output the operator did not approve.
4. Evidence: the comparison of output count, `txid`, `fee_sats`, the recipient output, and the
   change output; plus `tests/ui_state_reuse.cjs` for the screen half.
5. Exclusions: none.
6. Failure blocks: CLEARED.

**T-04 — Stale or swapped prepared payment.**
1. Asset 1. Attacker capability: a second request (a local page or a racing call) prepares or
   replaces a payment while the operator is reviewing or submitting.
2. Entry: `_current_prepared` `gui.py:926-940` (record/chain/generation/review-id binding);
   `_broadcast` `gui.py:1045-1133` under `state.lock`, re-checking `state.prepared is payment` and
   re-verifying after the submit leaves the lock. Boundary: HTTP request ↔ session state.
3. Prohibited: a broadcast of a payment other than the one the caller reviewed.
4. Evidence: `test_send_flow.py::SendFlowTests` cases that a scan going stale before submit is
   refused and that a stalled broadcast blocks neither status nor import; "The payment changed
   before broadcast."
5. Exclusions: the loopback listener is single-operator; a hostile local process is modelled only
   as far as the token and review-id binding let it be.
6. Failure blocks: CLEARED.

**T-05 — Mainnet consent bypass.**
1. Asset 1. Attacker capability: a caller (page, script, or the owner's tool) submits a mainnet
   broadcast with the screen consent omitted, or the backend flag defaulted true.
2. Entry: `gui.py:1049` (confirm) and `gui.py:1051-1053` (mainnet opt-in); the backend refusal
   `wallet_service.py:86-87`; the call site `gui.py:1100-1101`. Boundary: UI ↔ backend.
3. Prohibited: any mainnet broadcast without **both** the per-transaction final-screen consent and
   the backend opt-in.
4. Evidence: `test_send_flow.py::SendFlowTests::test_mainnet_broadcast_requires_separate_per_transaction_opt_in`;
   the panel must also demonstrate a direct `broadcast_transaction(..., mainnet_opt_in` omitted`)`
   call refusing.
5. Exclusions: none. One operator checkbox, not two; the backend flag is defence in depth.
6. Failure blocks: CLEARED, and a live path is ⛔ BLOCKED.

**T-06 — Wrong network, or a same-genesis Signet masquerading as the chosen chain.**
1. Asset 1. Attacker capability: a configured or reached explorer answers for a chain other than
   the selected one; Mutinynet shares ordinary Signet's genesis.
2. Entry: `network_config.py:28-52` (genesis and Mutinynet block-1 checkpoint), `:57-58`
   (secondaries); `network_settings.verify_esplora` `:122-151`; the opening gate and developer mode
   in `ui.html:325-354`; `gui.py:815-820`. Boundary: app ↔ public explorer.
3. Prohibited: reading balances or outpoints for the wrong chain, or accepting a Signet answer as
   mainnet.
4. Evidence: `tests/test_network_settings.py` pinning the four published constants verbatim and
   refusing a Signet genesis as mainnet; `tests/ui_developer_mode.cjs`.
5. Exclusions: the operator's own network choice is trusted; the panel does not model a malicious
   DNS resolver beyond the TLS and redirect-refusal controls.
6. Failure blocks: CLEARED.

**T-07 — Already-spent outpoint selection.**
1. Asset 1. Attacker capability: an explorer reports a stale or dishonest view so a spent outpoint
   is selected, or a double-spend races the payment.
2. Entry: `wallet_service.check_selected_outpoints` `:190-242`; second source for mainnet
   `network_config.py:57`. Boundary: app ↔ explorer.
3. Prohibited: signing or broadcasting a transaction spending an already-spent outpoint.
4. Evidence: `tests/test_outpoint_check.py`; the refusal "A selected Bitcoin output was already
   spent."
5. Exclusions/assumption (owner-recorded residual): practice networks have **one** source
   (`network_config.py:57-58`), so a dishonest practice-network explorer is not cross-checked.
   Practice networks carry no money; the panel records the residual rather than grading it. Owner ruling, 2026-10-11: this is the operator's own practice-network test setting, not a route to real Bitcoin; settled as a recorded residual and not pursued as a finding.
6. Failure blocks: CLEARED on mainnet; a practice-network-only weakness is at most CONDITIONAL.

**T-08 — Fee manipulation.**
1. Asset 1. Attacker capability: a fee quote or a crafted payment produces an excessive or
   mis-stated fee.
2. Entry: `wallet_service.check_fee_safety` `:60-72`; `estimate_fee_preview`; the large-amount and
   fee acknowledgements `ui.html:590`, `:635`; `gui.py:1274`. Boundary: app ↔ fee source.
3. Prohibited: a fee whose value the operator did not see and confirm.
4. Evidence: `tests/test_send_flow.py`; `tests/ui_large_amount.cjs` (a lying price cannot suppress
   the large-amount prompt).
5. Exclusions: fee-rate provenance is an observation, per `AGENTS.md`; the panel does not grade the
   public estimator's honesty, only the app's handling of it.
6. Failure blocks: CLEARED.

**T-09 — Change redirection through an inferred `/1/*` branch.**
1. Asset 1. Attacker capability: a BSMS or wallet layout tricks the app into treating a
   receive-only wildcard as declaring a change branch, so change is sent to an attacker-derived
   path — or change is created where the wallet has no declared change path.
2. Entry: `wallet_service.wallet_layout` `:272-333`; the `bare_receive_only` guard `:299-330`; the
   standard-BIP48 test `:355`; refusals `:327`. Boundary: BSMS document ↔ derived wallet layout.
3. Prohibited: any inferred change branch that the file does not declare and the exact standard
   2-of-3 shape does not justify; any partial send that would create undeclared change.
4. Evidence: `tests/test_change_branch.py` — including the case that builds a bare `/*` reference at
   the branch root and asserts `change is None` — and `CONTROLS.md` CM-05/CM-06. The panel must
   break the `not bare_receive_only` guard and watch that case go red while the older cases stay
   green, which is the only shape that proves the pin is real.
5. Exclusions: Nunchuk's BSMS writer omitting custom branch indices is a documented scope
   limitation (`AGENTS.md`); the panel records it, it is not a new finding.
6. Failure blocks: CLEARED.

**T-10 — Outcome-unknown broadcast mishandled.**
1. Asset 1. Attacker capability: a transport or malformed-response failure during broadcast leaves
   the true outcome unknown, and the app treats it as success or invites a blind retry.
2. Entry: `wallet_service.broadcast_transaction` `:75-135` (`BroadcastOutcomeUnknown` on HTTP≥500,
   `URLError`/`TimeoutError`/`OSError`, and any body that is not exactly 64 lowercase hex);
   `gui._broadcast` `:1116-1127` storing the pending txid. Boundary: app ↔ broadcaster.
3. Prohibited: a second broadcast of a payment whose first outcome is unknown; a false "sent".
4. Evidence: `tests/ui_broadcast_outcome.cjs`; `test_send_flow.py`; the refusal text "Do not send
   this payment again…".
5. Exclusions: the operator may still confirm the outcome independently; the panel grades the app's
   own handling.
6. Failure blocks: CLEARED.

**T-11 — Pending-payment pause bypass.**
1. Asset 1. Attacker capability: a second payment is prepared or sent before the previous outgoing
   broadcast has one confirmation.
2. Entry: the pause at `gui.py:1220`; pending state `gui.py:476-477`, `:839-842`. Boundary:
   consecutive payments in one session.
3. Prohibited: a second outbound payment while the previous one is unconfirmed.
4. Evidence: `tests/test_gui.py` (broadcast stays paused until the explorer confirms it);
   `ui_busy_ownership.cjs` for the screen.
5. Exclusions: incoming pending funds alone must not pause confirmed outputs — an over-pause is also
   a defect to record.
6. Failure blocks: CLEARED.

**T-12 — Counterfeit device or forged key proof.**
1. Asset 1. Attacker capability: a device presents an xpub or a message signature that does not
   belong to a key in the BSMS quorum.
2. Entry: `probe.prove_signer_holds_key` `:723-745`; `verify_signer_device` `:761-772`;
   `_same_xpub`; timeouts 180 s `:549`. Boundary: app ↔ device.
3. Prohibited: accepting a signer that does not hold a quorum key, or a device identity not the one
   the file names.
4. Evidence: `tests/test_probe.py`, `tests/test_hardening_pins.py`; the panel must demonstrate a
   counterfeit device being refused end to end.
5. Exclusions: device firmware trust is assumed; the panel does not evaluate it.
6. Failure blocks: CLEARED.

**T-13 — Poisoned HWI payload.**
1. Asset 1 (and Asset 2). Attacker capability: a modified `hwilib` package, or a substituted HWI
   helper, runs with the app.
2. Entry: `probe._verify_hwi_payload` `:418-451` over the committed manifest
   `vendor/hwi-payload-3.2.0.json`; `HWI_PAYLOAD_PINS` `:211`; sidecar/byte identity
   `_verify_hwi_bytes`; `_verify_hwi_identity` requiring a known `--version` line. Boundary:
   dependency install ↔ code that runs.
3. Prohibited: any code path in which an unpinned HWI module executes.
4. Evidence: `tests/test_hardening_pins.py::HwiIdentityPins` exercising **real bytes** — the panel
   must add/change a module and watch the refusal, not read the docstring.
5. Exclusions: the vendored embit wheel and libusb binaries are covered by their own pins
   (`tests/test_embit_vendor.py`, `tests/test_vendor_pins.py`, `test_libusb_vendor.py`) and are
   treated as a separate dependency-trust row if the panel finds one; HWI is the load-bearing one.
6. Failure blocks: CLEARED; a path that runs unpinned code is ⛔ BLOCKED.

**T-16 — An unsigned PSBT input that does not match the historical transaction.**
1. Asset 1. Attacker capability: a dishonest explorer supplies a previous transaction whose
   script/value does not match the wallet's derived script, so the app signs an unintended input.
2. Entry: `wallet_service.build_unsigned_psbt` `:748`; scan and outpoint agreement
   `_utxos_agree_with_totals`; `gui.verify_selected_outpoints`. Boundary: explorer data ↔ PSBT.
3. Prohibited: any PSBT input not matching an independently fetched historical transaction and the
   derived script/value.
4. Evidence: `tests/test_wallet_service.py`, `tests/test_outpoint_check.py`, `test_send_flow.py`.
5. Exclusions: an explorer that is *consistent* in its dishonesty across the fetch is not modelled
   beyond the mainnet second source.
6. Failure blocks: CLEARED.

### Asset 2 — credentials and the release workflow

**T-14 — Credential value committed, archived, or logged.**
1. Asset 2. Attacker capability: a credential value reaches the repository, the source archive, a
   build artifact, or a log.
2. Entry: the source-archive scan `.github/workflows/build-candidate.yml:153-174` driven by
   `scripts/scan-secrets.py`; `gui.assert_private_file` `:315`; `_clean_token` `:402`. Boundary:
   developer machine ↔ published bytes.
3. Prohibited: any credential value in the tree, the archive, an artifact, or a log.
4. Evidence: `tests/test_secret_scan.py` (canary caught; empty target refused, not called clean;
   scanner pinned by version and hash; the scan runs on the archive before upload).
5. Exclusions: GitHub's own secret-scanning posture is a platform control, assessed under T-20.
6. Failure blocks: CLEARED; an exposed value is ⛔ BLOCKED by the rubric.

**T-15 — A push alone building or publishing.**
1. Asset 2. Attacker capability: a push, schedule, or branch push starts a build or a publication.
2. Entry: every workflow trigger. `build-candidate.yml` is `workflow_dispatch`-only with boolean
   `notarize`/`publish` inputs (`:21-35`); `linux-inputs.yml` and `windows-inputs.yml` are the
   retired input branches and publish nothing; no `schedule:` anywhere. Boundary: git push ↔
   release.
3. Prohibited: any non-dispatched build that can publish.
4. Evidence: `tests/test_workflow_config.py`; the panel must read the trigger blocks of **all**
   three workflow files and enumerate the non-manual triggers it finds.
5. Exclusions: outside-repository automation is a declared assumption (see §6).
6. Failure blocks: CLEARED.

**T-17 — Dispatch-input command injection.**
1. Asset 2. Attacker capability: a dispatcher supplies a `candidate_run_id` (or another input) that
   is substituted into a `run:` body and executed.
2. Entry: `.github/workflows/build-candidate.yml:70-83` — the value travels via `env:
   CANDIDATE_RUN_ID` and is read as `[[ ! "$CANDIDATE_RUN_ID" =~ ^[0-9]+$ ]]`. Boundary: dispatch
   input ↔ shell.
3. Prohibited: any dispatch input reaching a shell as code.
4. Evidence: `tests/test_publish_guards.py::CandidateRunIdInjectionTests` and
   `InterpolationLintTests::test_no_run_body_interpolates_a_github_expression`. The panel must
   re-run the injection payloads, including one that both executes and satisfies the regex.
5. Exclusions: repository-write rights are the owner's, a declared assumption.
6. Failure blocks: CLEARED; a demonstrated execution path is ⛔ BLOCKED (pipeline integrity).

**T-18 — Publish without a signature or notarization.**
1. Asset 2. Attacker capability: a publish dispatch or an edited workflow produces an unsigned or
   unnotarized public release.
2. Entry: the unsigned-publish refusal `:58-61`; the notarize fail-closed check `:249-264`; the
   notarization refusal `:1101-1104`; the release-byte and GPG verification `:994-1005`. Boundary:
   workflow inputs ↔ release command.
3. Prohibited: any public release that is not signed and notarized and not byte-verified.
4. Evidence: `tests/test_publish_guards.py::ReleaseGuardBehaviourTests` (rendered outcome cases,
   not text pins).
5. Exclusions: the Apple notary service itself is trusted.
6. Failure blocks: CLEARED; a pipeline able to publish unverified bytes is ⛔ BLOCKED.

**T-19 — Over-broad token on a non-publishing run.**
1. Asset 2. Attacker capability: a `publish=false` candidate dispatch holds a write grant it does
   not need, so a compromised candidate step can write to the repository.
2. Entry: job split — top-level `permissions: contents: read`; `candidate-manifest` `:915-925`
   (`contents: read`, `if: ${{ !inputs.publish }}`); `release` `:978-987` (`contents: write`,
   `if: ${{ inputs.publish }}`). Boundary: candidate run ↔ repository write.
3. Prohibited: any write-capable job reachable from a candidate dispatch.
4. Evidence: `tests/test_workflow_config.py::LeastAuthorityTests` rendering each job's effective
   `contents` scope and `if:`.
5. Exclusions: repository-level default workflow permissions are a platform control (T-20).
6. Failure blocks: CLEARED.

**T-20 — Platform controls not as described.**
1. Asset 2. Attacker capability: the repository says one thing about rulesets, environment
   protection, or token permissions and the platform enforces another.
2. Entry: the controls the workflow depends on — `main` protected against deletion and
   non-fast-forward with no bypass actor; tags protected against deletion and force-move, creation
   unrestricted; the two signing environments `main`-only with **no** required reviewers; release
   job holding `contents: write`; `allowed_actions: "all"`, `sha_pinning_required: false`. Recorded
   in `releases/platform-state.json` and re-read by `scripts/check-platform-state.sh`.
   Boundary: repository ↔ GitHub platform.
3. Prohibited: a documented control that is not actually configured, or a configured control that
   blocks the owner's tools.
4. Evidence: the panel must re-read the live platform with `scripts/check-platform-state.sh` and
   its own API calls, and must state explicitly **what it verified itself versus what it took on
   the document's word** (the owner made this a condition). The recorded file is dated
   `2026-10-10T18:20:10Z`, before the release, so it is evidence of a past read, not current state.
5. Exclusions: GitHub account security and platform compromise are declared assumptions.
6. Failure blocks: CLEARED, unless the mismatch defeats a gate (then the affected row governs).

### Asset 3 — the reviewed-transaction integrity chain

**T-21 — Prepared-payment state replaced between review and finalization.**
1. Asset 3. Attacker capability: a request replaces the frozen prepared payment after the operator
   reviewed it but before finalization.
2. Entry: `gui._sign` `:942-1000` and `gui._finalize` `:1002-1028` binding to
   `payment.review_id` and the scan generation; `_current_prepared` `:926-940`. Boundary: review ↔
   sign ↔ finalize.
3. Prohibited: finalizing a payment that is not the reviewed one.
4. Evidence: `test_send_flow.py`, `tests/ui_state_reuse.cjs`.
5. Exclusions: none.
6. Failure blocks: CLEARED.

**T-22 — Old signer/final panels under a new review.**
1. Asset 3. Attacker capability: none external — a UI state-reuse defect shows a stale final
   transaction under a new unsigned review, which invites a wrong approval.
2. Entry: `ui.html` panel-clearing logic; `tests/ui_state_reuse.cjs`.
3. Prohibited: a final or signer panel from an earlier payment visible while a different payment is
   under review.
4. Evidence: the named JS test, plus a manual read of the clearing path.
5. Exclusions: the visual design itself is out of scope; only the state relationship is graded.
6. Failure blocks: CLEARED.

### Asset 4 — release artifacts

**T-23 — Publication of bytes that are not the verified candidate's.**
1. Asset 4. Attacker capability: a substituted asset, a rebuilt-from-different-source asset, or a
   candidate from another commit reaches the release.
2. Entry: candidate binding `.github/workflows/build-candidate.yml:785-834` (run id, event,
   conclusion, this workflow, `head_branch == main`, `head_sha == commit`, `notarize=true`), checksum
   verification `:834`, GPG signing `:879-898`, release-byte verification `:994-1005`. Boundary:
   candidate run ↔ public release.
3. Prohibited: any published byte not produced by the verified candidate run for the same commit.
4. Evidence: `tests/test_publish_guards.py::ReleaseGuardBehaviourTests` including a tampered-asset
   case; plus, for the **published** `v0.6.8` set, an independent check that each of the ten assets
   matches `SHA256SUMS`, that `SHA256SUMS.asc` verifies against `signing-key.asc`, and that an
   attestation exists for the expected subject digest.
5. Exclusions: GitHub's release hosting is trusted; the panel verifies bytes and provenance, not the
   host.
6. Failure blocks: CLEARED; publishing unverified bytes is ⛔ BLOCKED.

**T-24 — Tag or release-asset overwrite.**
1. Asset 4. Attacker capability: a dispatch republishes an existing version, replacing assets under
   an unchanged tag.
2. Entry: `git ls-remote --exit-code --tags` guard `.github/workflows/build-candidate.yml:1107-1118`
   (existing tag refuses; unverifiable tag state refuses); `AGENTS.md` forbids moving or deleting a
   published tag. Boundary: dispatch ↔ published release.
3. Prohibited: replacing any published tag's or release's bytes.
4. Evidence: `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_an_existing_tag_is_never_overwritten`
   and `…::test_an_unverifiable_tag_state_refuses_publication`; the panel must confirm the live
   `v0.6.8` tag still resolves to `0d4e01f`.
5. Exclusions: tag *creation* is deliberately unrestricted (owner condition); only overwrite is
   prohibited.
6. Failure blocks: CLEARED.

**T-25 — A second publish path on another branch or tag.**
1. Asset 4. Attacker capability: a branch or tag carries a workflow able to attach bytes to a
   release, outside the audited pipeline.
2. Entry: `scripts/check-publish-paths.sh` (allowlist `:85-87`; remote heads and tags `:131-132`;
   fail-closed unreadable body `:77`, `:194`; legacy-tag residual `:89-96`), run as a dispatch gate
   `build-candidate.yml:53`. Boundary: the whole remote ↔ one publish path.
3. Prohibited: any publish-capable workflow on a ref other than `main`, or a second one on `main`.
4. Evidence: `tests/test_workflow_config.py::PublishPathSweepTests`; the panel must run the sweep
   against the live remote and independently confirm it reads tag refs. The enumerated legacy tags
   (`check-publish-paths.sh:96`) are an accepted residual the panel must re-state, not discover.
5. Exclusions: a publisher placed outside `.github/workflows`, or a GitHub App, is outside the
   sweep's reach and is recorded as a residual.
6. Failure blocks: CLEARED; a live extra publish path on `main` is ⛔ BLOCKED.

**T-26 — The public download surface pointing at non-pipeline bytes.**
1. Asset 4. Attacker capability: the website, a documentation link, or the release page directs a
   downloader to a URL that the pipeline did not produce.
2. Entry: `docs/index.html`, `docs/user-manual.html`, `docs/llms.txt`, the GitHub Pages
   environment, and the release page's asset links. Boundary: published links ↔ release assets.
3. Prohibited: any download link resolving to something other than the audited `v0.6.8` release's
   assets.
4. Evidence: the panel fetches every download URL the documentation offers and matches the
   resolved bytes to a named release asset.
5. Exclusions: GitHub Pages build internals are trusted; only the offered links and their targets
   are graded.
6. Failure blocks: CLEARED.

**T-27 — Checksum, attestation, and SBOM disagreement.**
1. Asset 4. Attacker capability: a manifest, signature, attestation, or SBOM that does not describe
   the published bytes, so verification gives a false assurance.
2. Entry: `SHA256SUMS` generation and signing path `:879-898`; the SBOM via `scripts/build-sbom.py`;
   `SIGNING.md` (the verification instructions a downloader follows); `RELEASE-PROCESS.md` §3. The
   instructions a downloader is told to run are part of the artifact set and must be executable as
   written.
3. Prohibited: any published verification artifact that does not hold for the published bytes.
4. Evidence: `tests/test_release_verification_note.py` (the note's command is executed, not
   grepped), `tests/test_build_sbom.py`, and an independent end-to-end verification of the ten
   published assets.
5. Exclusions: the Sigstore service is trusted to attest faithfully; the panel checks the binding,
   not the service. One wording defect in the same file is already closed and is recorded here so it
   is not re-opened as a new finding: the one-time key setup told the reader to export
   `release@bitseeker.com`, while the shipped key is `Bitseeker LLC <release@bitseeker.llc>`. It is
   corrected on `main` (`336ea6c`), and `tests/test_signing_docs.py` now fails if the two disagree;
   the tagged tree still carries the original wording.
6. Failure blocks: CLEARED.

### Asset 5 — wallet privacy

**T-28 — Wallet material in diagnostics or logs.**
1. Asset 5. Attacker capability: xpubs, addresses, BSMS contents, txids, or device identities are
   captured through diagnostics or error text, and the operator later shares the file.
2. Entry: fixed stage/outcome sets `gui.py:71-93`; `_clean_token` `:402`; `_device_class` `:422`;
   `note` `:498-527` (drop, never escape); `save_diagnostic_report` `:428`. Boundary: internal
   event ↔ operator-shared file.
3. Prohibited: any free-text, key, address, path, serial, fingerprint, or error string in a
   diagnostic record.
4. Evidence: `tests/test_diagnostics.py` (only a known device class is accepted); the panel must
   attempt to smuggle a value through each field and through an error path.
5. Exclusions: the operator may still share a transaction id from the public explorer; the app must
   not write it.
6. Failure blocks: CLEARED.

**T-29 — Wallet material reaching an unintended server, or a redirect/TLS downgrade.**
1. Asset 5. Attacker capability: a redirect, a mis-set custom server, or a TLS-context failure sends
   a query — or a payload — somewhere the operator did not choose.
2. Entry: `safe_http._RefuseRedirects` `:159-184` and `open_url` `:259-281`; `_ssl_context`
   `:218-230`; `read_bounded`/`Deadline` `:51`, `:101`; `network_settings.validate_esplora_url`
   `:52-72` (remote HTTP refused, no credentials/query/fragment); `verify_esplora` `:122-151`;
   `wallet_service.explorer_get` `:138-187` (never sends xpubs). Boundary: app ↔ network.
3. Prohibited: any request carrying wallet material to a server other than the operator's chosen
   endpoint, over a downgraded or unverified transport.
4. Evidence: `tests/test_safe_http.py`, `tests/test_network_settings.py`,
   `tests/test_wallet_service.py`; the panel must drive a redirect and a wrong-network answer.
5. Exclusions: the operator's chosen public Esplora necessarily learns the queried addresses; that
   disclosure is intrinsic and recorded, not a finding. The owner requires an explicit explorer
   disclosure consent (`gui.py:766`).
6. Failure blocks: CLEARED.

**T-30 — Wallet artefacts committed to the tree.**
1. Asset 5. Attacker capability: a real BSMS, xpub, address, PSBT, settings file, or test artefact
   is committed and published.
2. Entry: `.gitignore`, `.gitattributes`; the source-archive contents; `tests/`.
3. Prohibited: any real wallet material in the audited tree or the source archive.
4. Evidence: the panel greps the tree and the archive for wallet-shaped material and for the
   `AGENTS.md`-forbidden classes; it also confirms the tests use only synthetic vectors.
5. Exclusions: already-published history is not re-litigated; the panel reports what is at the tag
   and in the `v0.6.8` archive.
6. Failure blocks: CLEARED.

**T-31 — Operator state files readable beyond the operator.**
1. Asset 5. Attacker capability: a prepared PSBT or settings file is created world-readable, or is
   saved somewhere another local user can read.
2. Entry: `save_prepared_psbt` `gui.py:342` with `assert_private_file` `:315`;
   `network_settings.save_servers` `:99-119` (directory 0700, file 0600, atomic replace). Boundary:
   app ↔ local filesystem.
3. Prohibited: any wallet-bearing state file readable by another local account.
4. Evidence: `tests/test_network_settings.py`; a direct check of the modes the app writes.
5. Exclusions: a fully compromised local OS account is out of scope.
6. Failure blocks: CLEARED.

## 6. Out of scope — and why

1. **GitHub account security, GitHub platform compromise, and stolen owner credentials.** The owner
   declares these external assumptions. Push and dispatch rights on this repository are the
   strongest *in-scope* attacker capability, which is why the workflow guards are graded as
   protection against accidents and workflow-level abuse.
2. **The owner's agent going rogue, and standing automation outside this repository.** Declared
   external assumptions, settled by the owner on 2026-10-11. The inside-repository half is testable
   and is in scope (T-15); the outside half is not testable from the tree, is recorded as *untested
   — owner-declared*, and is never graded. External compromise of the owner's account, machines,
   credentials or tools is not a source of findings (see §6, *Authorised agentic operation, and no
   automation*).
3. **Forks and third-party builds.** A fork cannot publish under this identity and is not this
   audit's subject.
4. **The correctness of Bitcoin, Esplora software, hardware-wallet firmware, `pywebview`/WebKit/Edge,
   Python, the OS, and the pinned third-party libraries at their pinned versions.** Each is a named
   trust boundary in §5, not a thing the panel re-derives. The pinned versions in
   `requirements*.txt`, the `*.lock` files, and `vendor/` **are** the audited versions; per the
   owner's policy, moving a pin invalidates inherited evidence for that component.
5. **Prior audit reports and prior Color Team cycles as evidence.** The earlier Color Team plans,
   reports, locks and grades, and the prior AI audit reports, are history, and were removed from
   `main` for this cycle. No prior conclusion, grade, or finding may be cited. Bounded exception: the immediately preceding Color
   Team report and the repository's own remediation ledger (`releases/PATCH-0.6.8.md`,
   `releases/OWNER-ACCEPTANCE-2026-10-07.md`) go to the **White referee** only; the specialist
   lanes run without them.
6. **Historical tags that freeze pre-guard workflow text.** Judged by what they can *do* from their
   own ref; the enumerated case is a recorded residual under T-25, not a new finding class.
7. **The visual design, copy, and marketing of the app and site, and the exact wording of release
   notes** — except where a claim in them is a security claim, which is then in scope as a claim to
   verify (for example, any sentence asserting what a build or artifact guarantees).

### The legacy audit artifacts inside the audited tree

The audited revision is the tag, and a tag cannot be edited without destroying the release it
names. The `v0.6.8` tree therefore still carries the audit artifacts of the earlier cycles, and
they will still be there when the panel checks out `0d4e01f`. They were removed from `main`
after the release. They are named here so the panel meets them as a known inventory that has
already been ruled on, not as a discovery:

| # | Path inside the `v0.6.8` tree | What it is |
|---|---|---|
| 1 | `bitcoin-easy-multisig-signer-colorteam-audit-index.md` | the earlier cycles' index |
| 2 | `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.4.md` | cycle scope lock |
| 3 | `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.5.md` | cycle scope lock |
| 4 | `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.6.md` | cycle scope lock |
| 5 | `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.7.md` | cycle scope lock |
| 6 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md` | plan of the abandoned line |
| 7 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.4.md` | cycle plan |
| 8 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.5.md` | cycle plan |
| 9 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.6.md` | cycle plan |
| 10 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md` | cycle plan |
| 11 | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` | the superseded unsigned draft this plan replaces |
| 12 | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md` | cycle report |
| 13 | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.5.md` | cycle report |
| 14 | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md` | cycle report |
| 15 | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` | cycle report |
| 16 | `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.7.md` | cycle public statement |
| 17 | `CONTROLS.md` | the parsed control inventory the release ships — **in scope**, see the rule |

**Rule.** Items 1–16 are not inputs, evidence, findings or grades for this cycle. The panel may
read one only to establish that it is not an input, and may not cite it in the report. Item 17 is
the exception and stays in scope: it is a shipped artifact the release itself claims, so §5 holds
it to that claim. A file that refers to a document that no longer exists is recorded as it stands
in the report's environment section — it is not a finding, and it is not resolved by reaching
backwards. The prior AI audit reports (`releases/AUDIT-*.md`) and the four `docs/audits/*.pdf`
files were removed from `main` for this cycle and remain only in the tagged trees.

### The living documents at the tag, and what changed after it

The audit targets `0d4e01f`, so the panel reads those documents as they stood on 2026-10-10. Several
had drifted and were corrected on `main` afterwards. They are listed here as a known inventory, not
as a discovery: none is a defect in the wallet engine, none changes what the code does, and none is
a finding in its own right.

| Document | What it said at `0d4e01f` | Corrected on `main` by |
|---|---|---|
| `SIGNING.md` | the one-time key setup named `release@bitseeker.com`; the shipped key is `release@bitseeker.llc` | `336ea6c`, with the guard `tests/test_signing_docs.py` (`6d17a80`) |
| `DISCLAIMER.md` | opened with "Version 0.6.2 is a maintenance release" | `913ce30` |
| `USER-MANUAL.md` | said version 0.6.3 in three places while the published page said 0.6.8 | `913ce30` |
| `PHASE-HANDOFF.md` | called the cycle-3 plan the input any later audit would start from, and placed the cycle-3 artifacts in the repository root | `913ce30` |
| `CURRENT-STATUS.md` | the same repository-root claim | `913ce30` |
| `LINUX-PORT.md` | said the `linux-port` branch, not `main`, answers for a Linux release | `913ce30` |
| `AGENTS.md` | presented the earlier AI audit reports as live context | `913ce30` |
| `CHANGE-ADDRESS-REVIEW.md` | cited an owner note supplied privately, without saying so | `913ce30` |
| `releases/README.md` | its index stopped at 0.6.1 and described audits no longer in the folder | `913ce30` |

**Rule.** Two of these actively mislead a panelist reading the tag. `PHASE-HANDOFF.md` at `0d4e01f`
tells the reader to treat the cycle-3 plan as their input, and `AGENTS.md` at `0d4e01f` presents the
earlier reports as live context. Both instructions are superseded and wrong for this cycle. Where a
document at the tag disagrees with this plan, this plan and the owner's direction win; the
disagreement is recorded as a document-state note in the report's environment section, not as a
finding. The `SIGNING.md` row is the one case already carried in §5: T-27 holds it, because a setup
step that cannot reproduce the shipped release key is a claim about the release, not a typo.

**`CONTROLS.md` is the counter-example.** It is a shipped artifact the release itself claims, so it
stays in scope (item 17 above). The tag's copy carries 20 control rows; `main` carries 21, the extra
being the guard added by `6d17a80`. The panel audits the tag's 20 rows against the tag's code and
tests, because that is what the release shipped.

### The owner's policies these exclusions rest on

Reproduced verbatim from the owner's statements.

#### Independence condition (owner, 2026-10-06)

This is a fresh audit under this methodology. The prior AI audit reports (`releases/AUDIT-*.md`,
`docs/audits/*.pdf`) are history and are **not inputs**; the panel and the referee run without them,
and no prior conclusion, grade, or finding may be cited as evidence in this cycle's report. One
bounded exception: the cycle-4 Color Team report and the repository's own remediation ledger
(`releases/PATCH-0.6.8.md`, `releases/OWNER-ACCEPTANCE-2026-10-07.md`) are available to the
**referee**; the specialist lanes run without them.

#### Contribution model (owner, 2026-10-06)

The sole collaborator is the owner (`cjtsh`, admin). The repository is public and forkable, but no
third party can push, dispatch workflows, or merge code into it — there are no contributors and no
inbound PR surface (issues are reports, not code). Push and dispatch rights therefore rest entirely
on the owner's GitHub account and are treated as **owner account hygiene, outside the application's
threat model**; the panel does not audit GitHub account security. The workflow guards are evaluated
as protection against accidents and workflow-level abuse, not against compromise of the owner's
account.

The repository-controlled platform settings those guards depend on (rulesets, branch protection,
environment protection rules, token permissions) are **in scope as configured controls**. The panel
must evaluate the publish path as it actually stands, not as the workflow's comments describe it.

#### Authorised agentic operation, and no automation (owner, 2026-10-10)

The owner works through agentic coding tools that act under the owner's own GitHub credentials and
authority. Platform controls must therefore not lock those tools out: no required reviewer is added
to the signing environments, and Actions is left at `allowed_actions: "all"` with
`sha_pinning_required: false`, so a tool the owner runs is never blocked by a platform setting. The
owner accepts the tool set as inside the owner boundary — "the owner's agent went rogue" is a
declared external assumption, never a graded finding — and the workflow guards exist to bound what
a dispatch can do on its own.

Two separate statements sit behind that, and they must not be conflated:

- **Inside the repository.** There is no automatic build and no automatic code update. No
  `schedule:`/cron exists in any workflow, and the only non-manual triggers in the tree are pushes
  to the two retired input branches, which only regenerate hash locks and publish nothing. Nothing
  in this repository starts a build, moves a pin, opens or merges a pull request, or publishes a
  release on its own initiative. Every build, every pin move and every publication is dispatched by
  the owner, or by a tool the owner directs while sitting at the terminal.
- **Outside the repository — declared by the owner, not verifiable from the tree.** The owner
  states that no scheduled or standing automation exists anywhere in their tool estate either: no
  cron job watches this codebase; no cron job watches third-party libraries or their releases; and
  no agent, agentic coding partner or coding framework is standing by to convert a third-party
  change, an outside pull request or a merge into a release or a pin move. Automated build and
  release scripts do exist, but nothing invokes them except the owner at the terminal — if the
  owner is not there as the commander, no work happens. This half is a declaration about systems
  outside this repository and cannot be tested from the tree.

  **Owner ruling, 2026-10-11.** Settled; no inventory is required for this cycle and none will be
  supplied. The panel records this half as *untested — owner-declared*. The owner's reasoning,
  recorded because it is the point: an audit cannot account for what happens if the owner's account,
  machines, credentials or agentic tools are compromised, and those possibilities cannot be
  enumerated. Pursuing them is what made the previous cycle spiral through roughly a hundred loops
  without producing a reproducible finding. External compromise on that ground is therefore a
  declared external assumption: the panel may not open a finding, grade a lane, or request further
  evidence about it, and may not carry it as an open question. What *is* testable stays in scope —
  the repository half above, and the workflow guards that bound what a dispatch can do on its own.
  The owner builds every revision by hand through agentic tools, and no outside code is accepted
  into the release line (see *Distribution and contribution policy*).

#### Distribution and contribution policy (owner, 2026-10-10)

This repository is public so that anyone may read, use, fork and independently verify the software,
and it is MIT-licensed for that purpose. It is **not** open to public collaboration: Bitseeker LLC
is the sole contributor and the only collaborator with write access, and outside pull requests are
not merged into the release line. Release artifacts are produced only from `main`, by the audited
candidate→promote chain, and are signed under the Bitseeker LLC release key. A fork is someone
else's build: it cannot publish under this identity, and it is not this audit's subject.
Consequently this audit treats **push and dispatch rights on this repository** as the strongest
in-scope attacker capability, and treats GitHub account compromise, GitHub platform compromise,
and stolen owner credentials as declared external assumptions — recorded once, never graded as
findings.

#### Downstream dependency policy (owner, 2026-10-10)

The pinned versions in `requirements*.txt`, the `*.lock` files and `vendor/` **are the audited
versions**. The application does not track upstream automatically, and a dependency is not moved to
a newer release without its own review. Moving a pin **invalidates any inherited audit evidence for
that component** until it is re-established. Inherited evidence may be cited only for the exact
pinned version and only where the owner has named the audit that covers it.

## 7. Not examined — and why

1. **The published `v0.6.8` artifact bytes** were not examined by the surveyor. They are outside the
   tree (published after the tag) and examining them is the panel's work (T-23, T-27).
2. **The live GitHub platform posture** was not examined. `git` cannot show it and
   `releases/platform-state.json` is a dated record (`2026-10-10T18:20:10Z`). The panel must re-read
   it (T-20).
3. **The owner's machine and account state, and any scheduled tasks** were not examined and are
   not testable from the tree — declared external assumptions, recorded as *untested —
   owner-declared*.
4. **Hardware-wallet firmware and device behavior under an adversarial device** were not examined
   beyond the app's own verification code (T-12); physical device testing is the owner's, not the
   panel's.
5. **Practice-network second-source cross-checking** does not exist by design
   (`network_config.py:57-58`); the panel records it as an owner-accepted residual under T-07
   rather than searching for a control that is not there. Owner ruling, 2026-10-11: this is the operator's own practice-network test setting, not a route to real Bitcoin; settled as a recorded residual and not pursued as a finding.
6. **The contents of the two retired input workflows** (`linux-inputs.yml`, `windows-inputs.yml`)
   were read only far enough to establish that they publish nothing; they are otherwise out of
   scope, because their only office is to regenerate hash locks.

## 8. Questions for the owner — none outstanding

Every question this survey raised was put to the owner and settled before signature, so nothing here
is waiting on the owner. The record is kept so a later reader can see what was decided, rather than
re-litigate it:

| Question | Settled |
|---|---|
| Was the earlier `…-colorteam-audit-plan-v0.6.8.md` draft to be overwritten? | **Yes.** This file is the single v0.6.8 plan; the earlier draft carries no standing (owner, 2026-10-11). |
| Are the statements in §0, §1, §2, §3 and §6 the owner's own words, and is the tag the audited tree? | **Yes to both.** `owners-audit-stattement.md` lives on `main` and is not in the tag tree (owner, 2026-10-11). |
| May the panel fetch the ten published assets and query the attestation API? | **Yes**, read-only. The surveyor exercised the route on 2026-10-11 (§0, *What the surveyor verified*). |
| Is the single explorer for Testnet4 and Mutinynet a finding? | **No.** The operator's own practice-network setting, not a route to real Bitcoin; recorded as a residual under T-07 (owner, 2026-10-11). |
| Is a scheduled-task inventory needed for the outside-repository declaration? | **No.** Recorded *untested — owner-declared* and never graded (§6, *Authorised agentic operation, and no automation*). |
| Was the release-key address in `SIGNING.md` a defect? | **Yes.** The setup steps named `release@bitseeker.com`; the shipped key is `release@bitseeker.llc`. Corrected, with a guard test (T-27). |

**One gate, not a question.** At lock time the panel re-confirms that `v0.6.8` still resolves to
`0d4e01f` and that `main` has not moved under the audit, per the rubric's scope/lock-mismatch clause.
That is a step in the lock procedure, not something the owner answers.

## 9. Owner review and sign-off — step two, no AI

*Step two. This section is written by the owner only — no AI writes in it. Nothing below is filled
in by the surveyor, and the audit does not begin, and the audit team does not lock the plan, until
the owner has signed at the end of this section.*

**Corrections and notes.** Write one bullet per correction, naming the section it touches. If the
body is correct as written, write `None`.

-

**Sign-off.** *The audit does not begin until the two lines below are filled in by the owner and
the audit team has locked this plan.*

- **Signed:** ______________________________________________
- **Date:** ______________________________________________

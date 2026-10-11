# Audit plan — bitcoin-easy-multisig-signer

## 0. Locked scope

**Definitions in force:** Color Team definitions framework tag `v1.5.0`
(`colorteam-surveyor.md` at that tag was the runbook this survey was run under; it states
that file is all the surveyor needs, so `COLOR-TEAM.md` itself was not fetched) — Red,
Blue, Orange, Copper, Amber, White. This cycle adds the two framework-`v1.5.0`
obligations the earlier cycles did not carry: a **mandatory one-page Public Security
Statement** as an audit output (specified below), and an **explicit evidence budget and
stop condition** (also below).

**Declared assets, and what must not happen to them:**

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GPG release key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** — stolen credentials enable a fake build, which enables theft |
| 3 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG, the platform bundles, `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten; the public download surface never points at bytes the pipeline did not produce |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

**The unforgivable acts, in plain words:**

1. The app gets the owner to sign and broadcast a transaction that sends their real
   Bitcoin somewhere they did not approve — a thief's address, a wrong amount, or
   change quietly redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or
   the app leaks the wallet's addresses and xpubs so strangers can watch and target the
   family's savings.

**The rubric as adapted to this target** — these conditions, and no others, decide the
grade:

| Grade | Conditions that must hold here |
|---|---|
| ✅ CLEARED | The panel finds no path, in in-scope code at the target revision, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's; (e) expose a credential value. The invariants in `AGENTS.md` hold as stated, with test evidence where the repo claims it. **New in this cycle:** no claim in `releases/PATCH-0.6.8.md`'s finding→fix→test table is left with a closing evidence pin that cannot fail, and no control it claims is found to be defeatable as written. |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, credential handling, or the release chain in a way that needs an owner decision — e.g. a gap that only opens under explorer misbehavior, device firmware trust assumptions, or stated invariants that lack the test coverage the repo claims. |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check. |

**No asset is optional** (owner, 2026-10-06): the ranking orders severity, not attention.
All five assets are mission-critical; a demonstrated path to breach any of them is at least
CONDITIONAL, and no finding may be dismissed as low-priority because its asset is ranked
fifth.

**"The operator should have noticed" is never a defense** (owner, 2026-10-06): any safety
property that depends on the operator spotting a discrepancy is a weakness the panel must
report, not a mitigation it may assume.

**Independence condition** (owner, 2026-10-06, carried forward): this is a fresh audit under
this methodology. The prior AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`)
are history and are **not inputs**; the panel and the referee run without them, and no
prior conclusion, grade, or finding may be cited as evidence in this cycle's report. One
bounded exception, carried forward and extended: the cycle-4 Color Team report
(`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`) and the repository's own
remediation ledger (`releases/PATCH-0.6.8.md`, `releases/OWNER-ACCEPTANCE-2026-10-07.md`)
are available to the **referee**, because this is the first audit asked to verify their
remedies; the specialist lanes run without them.

**Contribution model** (owner, 2026-10-06, carried forward and re-verified this cycle from
the GitHub API): the sole collaborator is the owner (`cjtsh`, admin). The repository is
public and forkable, but no third party can push, dispatch workflows, or merge code into
it — there are no contributors and no inbound PR surface (issues are reports, not code).
Push and dispatch rights therefore rest entirely on the owner's GitHub account and are
treated as **owner account hygiene, outside the application's threat model**; the panel
does not audit GitHub account security. The workflow guards are evaluated as protection
against accidents and workflow-level abuse, not against compromise of the owner's account.
**New this cycle:** the *repository-controlled platform settings* that those guards depend
on (rulesets, branch protection, environment protection rules, token permissions) are
**in scope as configured controls**, because framework `v1.4`'s test for external
assumption is whether repository-controlled permissions make the path reachable. Their
measured state is recorded in sections 4, 5 and 7; the panel must evaluate the publish
path as it actually stands, not as the workflow's comments describe it.

**Authorised agentic operation, and no automation** (owner, 2026-10-10 — an owner amendment
to the locked scope, logged in section 9): the owner works through agentic coding tools that
act under the owner's own GitHub credentials and authority. Platform controls must therefore
not lock those tools out: no required reviewer is added to the signing environments, and
Actions is left at `allowed_actions: "all"` with `sha_pinning_required: false`, so a tool the
owner runs is never blocked by a platform setting. The owner accepts the tool set as inside
the owner boundary — "the owner's agent went rogue" is a declared external assumption, never
a graded finding — and the workflow guards exist to bound what a dispatch can do on its own.

Two separate statements sit behind that, and they must not be conflated:

- **Inside the repository — verified.** There is no automatic build and no automatic code
  update. No `schedule:`/cron exists in any workflow; the only non-manual triggers in the tree
  are pushes to the two retired `linux-port` / `windows-port` input branches
  (`linux-inputs.yml:26-29`, `windows-inputs.yml:26-29`), which only regenerate hash locks and
  publish nothing. Nothing in this repository starts a build, moves a pin, opens or merges a
  pull request, or publishes a release on its own initiative. Every build, every pin move and
  every publication is dispatched by the owner, or by a tool the owner directs while sitting
  at the terminal.
- **Outside the repository — declared by the owner, not verifiable from the tree.** The owner
  states that no scheduled or standing automation exists anywhere in their tool estate either:
  no cron job watches this codebase; no cron job watches third-party libraries or their
  releases; and no agent, agentic coding partner or coding framework is standing by to convert
  a third-party change, an outside pull request or a merge into a release or a pin move.
  Automated build and release scripts do exist, but nothing invokes them except the owner at
  the terminal — if the owner is not there as the commander, no work happens. This half is a
  declaration about systems outside this repository and cannot be tested from the tree. A panel
  that wishes to test it must obtain from the owner the scheduled-task inventory of the
  machines and accounts that hold the credentials; absent such an artefact, no finding may be
  graded on it (section 5, burden of proof).

**Distribution and contribution policy** (owner, 2026-10-10 — an owner amendment to the
locked scope, logged in section 9): this repository is public so that anyone may read, use,
fork and independently verify the software, and it is MIT-licensed for that purpose. It is
**not** open to public collaboration: Bitseeker LLC is the sole contributor and the only
collaborator with write access, and outside pull requests are not merged into the release
line. Release artifacts are produced only from `main`, by the audited `build-candidate.yml`
candidate→promote chain, and are signed under the Bitseeker LLC release key. A fork is
someone else's build: it cannot publish under this identity, and it is not this audit's
subject. Consequently this audit treats **push and dispatch rights on this repository** as
the strongest in-scope attacker capability, and treats GitHub account compromise, GitHub
platform compromise, and stolen owner credentials as declared external assumptions —
recorded once, never graded as findings.

**Downstream dependency policy** (owner, 2026-10-10, same amendment): the owner declares
that the pinned versions in `requirements*.txt`, the `*.lock` files and `vendor/` **are the
audited versions**. The application does not track upstream automatically — the measured
platform state agrees, `dependabot_security_updates` being disabled (section 4) — and a
dependency is not moved to a newer release without its own review. Moving a pin
**invalidates any inherited audit evidence for that component** until it is re-established.
Inherited evidence may be cited only for the exact pinned version and only where the owner
has named the audit that covers it: this plan does not assert component coverage the
repository cannot show (section 8, question 6).

**Operator model and report audiences** (owner, 2026-10-06, carried forward): the target
operator is a nontechnical fiduciary or family member — a lawyer, trustee, accountant,
spouse, or trusted advisor settling an estate that includes Bitcoin. They know Bitcoin is
dangerous and cannot audit the app themselves. The report has two audiences and must serve
both: (a) that nontechnical trusted advisor, who needs plain-language evidence of
diligence — thorough, best-effort, and explicitly *not* a guarantee; and (b) the agent that
will fix what the audit finds — every finding must be precise, located, and reproducible
enough to serve directly as fix-it input, so the improvement loop can re-run the audit on
the revision. **One vocabulary correction the panel must honour:** the product's documented
posture is a *networked loopback desktop app plus hardware signing plus public Esplora
servers* — "airgap", "air-gapped", "offline machine" and "watch-only" appear nowhere in the
project, the app holds no wallet key, it never receives a PIN, and it never asks for seed
words. The report must describe the product in those actual terms rather than importing
airgap vocabulary it does not have.

**Target revision (owner's direction, retargeted 2026-10-11):** the published release
**`v0.6.8`** — tag `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`) — together with the
release artifacts published on 2026-10-10T21:31:47Z. This is the revision the audit attaches
to; section 1 carries the full statement. The **reconnaissance revision** this plan carries is
`main` at **`d525f31b600d5aedd2f7a219ec848df540707ffc`** (`d525f31`) — **no tag** — the
cycle-4 survey, one documentation-only commit past the `v0.6.7` tag (author date
`2026-10-07T17:17:29Z`, committer date `2026-10-09T23:45:35Z`, subject "Publish v0.6.7, and
correct the stale claims the tree still carried"). **The tree moved a long way between that
survey and the audited tag** — 37 commits, 81 files, 10,363 insertions and 379
deletions, the whole CT-72…CT-95 remediation included (section 1) — so a statement in
sections 4, 7 or 8 made "at `d525f31`" is the **cycle-4 survey record** and must be
re-verified against the tag, not read as current. The filename is the release this plan
audits; the signed plan for the cycle-4 survey
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`) already exists and the
runbook forbids overwriting it (section 1).

**Out of scope:**

- `docs/` marketing/manual website — GitHub Pages content; ships separately and shares no code with the app. **Its measured staleness was nonetheless recorded** (sections 4, 7 and 8) because asset 4's public surface is a release-channel question, not a code question; it was corrected on `main` after the `v0.6.7` release (`fc65647`, section 8 question 2), and the tagged tree still carries the text the tag itself shipped.
- `releases/` and root status/history documentation (`CURRENT-STATUS.md`, `RELEASE-HISTORY.md`, `PHASE-HANDOFF.md`, `ROADMAP.md`, `PROJECT-HISTORY.md`, `releases/PATCH-*.md`) — historical records, not executable surface; auditing the prose is not this audit's job. **Exception:** `releases/PATCH-0.6.8.md` and `releases/OWNER-ACCEPTANCE-2026-10-07.md` are evidence inputs the referee must verify claim-by-claim (see the independence condition above), not prose to be graded.
- Prior AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) — history only and not inputs to this cycle.
- Internals of pinned third-party dependencies (hwi 3.2.0, pywebview 6.2.1, pyinstaller 6.22.2, requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, upstream embit) — hash-locked; `CURRENT-STATUS.md:113` records an independent component audit of this stack as outstanding; that is a separate effort with its own plan.
- Hardware wallet firmware (Ledger, Trezor, Jade, OneKey) — external devices, not this repository.
- Live Esplora/explorer operators — external services the design already treats as untrusted observations.
- GitHub account security, and the GitHub platform itself (availability, API honesty) — external assumptions, per the contribution model.

**Not examined:**

- The commits pushed to `main` on 2026-10-08/09 and the branches that carried them — they are not reachable from any ref today (section 7); they cannot be audited from the repository and are **not** part of the target revision. The same holds for the thirteen CT-48 remediation commits `releases/PATCH-0.6.7.md:61-80` cites as its branches-kept evidence: no ref holds them.
- `vendor/libusb-1.0.0.dylib` — compiled arm64 binary; provenance and hash pin documented at `vendor/README.md:36-47` but internals not reviewed.
- Vendored embit wheel internals — only the documented two-edit delta vs upstream (`vendor/README.md:10-34`); the full library was not read.
- `ui.html` (129 KB), `gui.py` (51 KB), `wallet_service.py` (36 KB), `probe.py` (30 KB), `tests/test_workflow_config.py` (1112 lines) — sampled at entry points, gates, and stated invariants; not read line-by-line. Full reading is the panel's job.
- Runtime behavior on a live machine, and the contents of the published release artifacts — the survey was static and offline; no build was run, no server started, no device attached, no artifact downloaded, no workflow dispatched *during the survey*. One candidate build was dispatched afterwards at the owner's direction (section 4, revision 5); its artifacts were produced but were not downloaded or executed, and no published release byte was verified. Every published byte was therefore **not** verified at survey time.
- The GitHub Actions run **logs** of the `v0.6.7` candidate and promote runs — run metadata was verified from the API (section 7); the logs themselves were not read.
- `docs/audits/*.pdf` — prior third-party AI audit reports in binary PDF form, not read.
- GitHub secret **values** — only their names were read, from the workflow and the environment list (section 4); values were never requested and are not in the repository.
- Full git history — authorship sampled only; all five commit identities map to the owner.

**Excluded by demonstration:** *(empty — nothing was demonstrated unreachable at survey
time. In particular, the developer-mode network gate is frontend-only and a token holder
can reach mainnet without it; that is recorded as an in-scope weakness, not excluded.)*

**Risk residuals this cycle is explicitly asked to treat as gates, not assumptions**
(owner, 2026-10-06, carried forward): tag rulesets, environment protection, and
least-privilege tokens are external controls the previous cycle could not verify. This cycle
measured them, and the owner then changed some of them before this plan was signed. As they
now stand: `main` carries branch ruleset `protect-main` (`24840839`), which blocks branch
deletion and non-fast-forward pushes with **no bypass actor**, so it applies to the owner's
own tooling as well; **tags are now protected too**, by ruleset `protect-tags` (`24841466`),
which blocks tag deletion and non-fast-forward tag moves across `refs/tags/v*` with no bypass
actor, while deliberately leaving tag **creation** unrestricted so that the release job can
still create the release tag; the two signing environments carry a `main`-only branch policy
and, by the owner's explicit decision (section 0, authorised agentic operation), **no required
reviewers**; and the workflow's `release` job holds `contents: write` on every dispatch. At
the target revision `d525f31` no job entered either signing environment, so the signing
credentials were unreachable and a release could not have been notarized or published — a
release-readiness blocker this survey found and the owner then fixed (sections 4 and 7). These
are recorded as residual risk and release-readiness gates, and the panel must say what it
verified itself versus what it took on the document's word.

**Mandatory audit output — one-page Public Security Statement** (framework `v1.5.0`): the
audit must produce a **one-page, release-specific, public-facing security statement**
alongside the technical report, the plain-English safety review, and the findings ledger.
The surveyor does not write or endorse it. It must state, at minimum:

- the public audience it is written for, and the product, version and commit it describes;
- the exact tested release artifacts **with hashes**, and the audit date;
- the grade and the release-readiness verdict;
- the protected assets and the controls that were actually tested;
- major findings and the unresolved gaps, including coverage limits;
- the operator safety checks the user must perform themselves;
- links to the full report and to the official download location; and **an explicit
  statement if binaries were not verified**;
- a candid AI-provenance statement: the actual agents/models/vendors involved, whether
  different-model independence was *verified* or only *declared*, and what human review
  took place;
- a plain-language posture block for the non-Bitcoin reader: what the app is and is not
  (it holds no wallet key, creates no wallet, never asks for seed words or a PIN, and never
  signs or broadcasts silently), the single BSMS wallet file the operator must supply, the
  one deliberate per-transaction mainnet confirmation, and the operator's own safety checks
  (verify the recipient and amount through a separate trusted channel; check the change in
  your own wallet software); and
- the distribution and contribution policy as stated in section 0, so a reader knows the
  release line is single-maintainer, signed, and built only from `main`.

It must call the process an **AI-assisted or agentic security review**, never human-firm
certification, and must make no claim of perfect security, guaranteed absence of malware,
unhackability, or outside-firm endorsement. A BLOCKED or unpublished build must never be
described as approved or safe to deploy. Tone: calm, helpful, **trust but verify**.

**Evidence budget and stop condition** (framework `v1.4`). Budget for this survey: the
checked-out tree at `d525f31`, its committed history, and read-only GitHub REST API
metadata (repository settings, rulesets, environments, Actions registrations, workflow
runs, releases). No build, no dispatch, no download, no live system, no secret value, no
write of any kind — the read-only rule is the budget. (The owner later set that rule aside
for the owner-directed writes logged in section 9, which include one candidate build dispatch;
the surveyor did not relax it itself, and
no reading budget beyond the above was spent.) The survey stops when the five
declared assets, the two unforgivable acts, the in-scope / out-of-scope / not-examined
lists, and the questions for the owner can each be written with a `file:line @
d525f31` or API-endpoint citation for every claim, and section 0 can be written out in
full. Anything the panel wants beyond that is the panel's budget under its own runbook,
not this plan's. **Stop condition reached:** the survey ended when the reconnaissance above
was sufficient to write this file; nothing further was read to "be sure".

**Frozen — this is the last surveyor revision** (owner's direction, 2026-10-10). Revision 8
is final: the surveyor will publish no further revision of this plan for this cycle. All six
of section 8's questions are answered — 1 and 3 by the owner directly, 2, 4, 5 and 6 by this
revision at the owner's direction — the scope is closed, and the repository is handed to the
incoming review as a clean, committed snapshot. Two consequences the panel must honour: (a)
the plan is a fixed input, so if the review finds a genuine scope defect it is recorded as a
**scope/lock mismatch**, not silently repaired — a later change requires the owner to amend
this file and re-sign, which voids any lock already taken; and (b) the named next-cycle list
(section 5) and the deferred items (section 4) are the correct destination for anything the
review finds that is real but outside this cycle's scope. Nothing in this cycle is waiting on
a further surveyor edit.

**Agent provenance — who ran this, and how you know.**

| | |
|---|---|
| **Surveyor — harness** | DeepSeek Harness desktop app (`__CFBundleIdentifier=com.deepseek.dsh`, `DSH_PROFILE=desktop`, `DSH_SHELL=1`) |
| **Surveyor — session ID** | `DSH_SESSION_ID=session-5d5422fc-382b-428d-93f1-71eb00cd083b` — read out of the environment and copied verbatim; the session identifier is exposed by this harness, unlike the previous cycle's |
| **Surveyor — model** | `not exposed by the harness` — the environment contains no model variable and the operator has not declared one; the surveyor did not ask itself and did not guess |
| **Declared by** | The Surveyor agent running in the harness above, transcribing its own environment; operator handle: `cjtsh` |

The auditor records its own provenance in the report. The referee compares the two session
identifiers: **identical means one run did both jobs, the independence rule is broken, and
the audit is void.** Different identifiers establish different runs, not different models.

---

<!-- The owner does not sign here. Their review and sign-off is the last section of this
     file, section 9. Section 0 is the scope; the signature at the end covers the whole
     document. -->

## 1. Target and revision

- **Repository:** `cjtsh/bitcoin-easy-multisig-signer` (public, MIT, created
  2026-09-27T22:35:04Z; `pushed_at` 2026-10-10, after the post-survey commits logged in
  section 9)
- **Revision under audit (owner's direction, retargeted 2026-10-11): the published release
  `v0.6.8`, tag `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`), together with the
  release artifacts published on 2026-10-10T21:31:47Z.** `v0.6.8` is the current public release: the
  macOS DMG (signed and notarized), the Windows bundle, the Linux AppImage and tarball, the
  source archive, the BUILD-SBOM documents, `SHA256SUMS` and its GPG signature. The owner
  directs that the audit attach to **what users actually hold and download**, not to a branch
  head and not to a release users do not have.
- **Reconnaissance revision:** `main` at
  **`d525f31b600d5aedd2f7a219ec848df540707ffc`** (`d525f31`) — the commit the carried cycle-4
  survey measured. `d525f31` is the documentation-only child of the `v0.6.7` tag commit:
  written 2026-10-07T17:17:29Z, landed on `main` 2026-10-09T23:45:35Z.
- **The survey and the audited tag are not the same tree, and the panel must not read them as
  one.** Between `d525f31` and the `v0.6.8` tag commit `0d4e01f` the branch gained the
  CT-72…CT-95 remediation (`e30d7cf`, `32c9c8b`, `37ae9fb` and the closing commits through
  `8f7fa8f`), the release-engineering work that made the cycle-4 tests portable (`5b1e52e`,
  `0d4e01f`), the 0.6.8 version bump and release notes (`d7dd590`), the new ledger
  `releases/PATCH-0.6.8.md`, and the plan retarget (`246bd41`) — **37 commits, 81 files,
  10,363 insertions, 379 deletions**, including executable surface (`gui.py`, `wallet_service.py`,
  `safe_http.py`, `network_settings.py`, `probe.py`, `Start Easy Multisig.command`, the build
  scripts and all three workflows) and new controls (`CONTROLS.md`, `scripts/scan-secrets.py`,
  `scripts/check-platform-state.sh`, `releases/platform-state.json`,
  `tests/test_ledger_completeness.py`, `tests/test_publish_guards.py`, `tests/test_secret_scan.py`,
  `tests/test_platform_state.py`). Sections 4, 7 and 8 are the **cycle-4 survey record** measured
  at `d525f31`; the panel must re-verify every statement in them against the tag. Survey claims
  already known to have moved: the T10 download-surface staleness was corrected on `main`
  (`fc65647`, then `b0a7324` for v0.6.8); the "13 CT-48 remediation commits" of section 7 belong
  to the `v0.6.7` line; and the ledger the referee verifies for this cycle is
  `releases/PATCH-0.6.8.md`.
- **Why this file is named for the release.** The framework names the cycle for the revision
  surveyed — its release tag, or the short commit when it has no tag. The cycle that audits the
  published `v0.6.8` release is named for its release tag; the signed plan for the cycle-4
  survey is `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`, and the runbook
  forbids overwriting a signed file. The lock and the report should name the cycle **`v0.6.8`**,
  and record that the plan carrying it is this file.
- **The branch has moved since the survey.** Owner-directed commits landed on top of `d525f31`
  and on top of the tag — the remediation and release commits listed above, the publication
  records (`b0a7324`), the earlier cycle-5 signature (`1cf8880`), and this retarget. None of
  them is part of the audited release, and none alters a byte of it. The panel and the referee
  must pin the **tag `v0.6.8` and its artifacts** by hash, never the branch head.
- **Date:** 2026-10-10
- **Surveyed by:** DeepSeek Harness agent (harness `com.deepseek.dsh`, session
  `session-5d5422fc-382b-428d-93f1-71eb00cd083b`, model not exposed by the harness). Must
  NOT be the model that runs the audit.

## 2. The declared assets (ranked)

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GPG release key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** |
| 3 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG, the platform bundles, `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten; the public download surface never points at bytes the pipeline did not produce |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries |

Ranking note (owner, 2026-10-06): all five assets are mission-critical. Funds rank first,
and credentials rank second because the owner equates their loss with loss of funds. Ranks
3–5 are all direct paths to, or protections of, the funds and the owner's identity —
privacy is ranked fifth because a leak does not move funds by itself, **not** because it is
optional. A stuck or blocked payment remains recoverable and sits below every asset on this
table.

## 3. The unforgivable acts (in plain words)

1. The app gets the owner to sign and broadcast a transaction that sends their real
   Bitcoin somewhere they did not approve — a thief's address, a wrong amount, or change
   quietly redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the
   app leaks the wallet's addresses and xpubs so strangers can watch and target the
   family's savings.

## 4. Where the assets live

### Assets 1 & 3 — the funds and the reviewed-transaction chain

- Frozen prepared-payment record: `gui.py:262` (`class PreparedPayment`), fields at
  `gui.py:274` (`review_id`), factory `gui.py:281` (`create`), created for the operator at
  `gui.py:1251` with `secrets.token_urlsafe(18)`.
- Re-parse and drift refusal: `gui.py:290` (`checked_psbt`, raises "The prepared
  transaction changed. Review it again."), and the binding test `_current_prepared`
  `gui.py:869` (identity, chain, scan generation, `preparation_id == review_id`).
- Final-screen binding: `_check_final_review` `gui.py:973-986` compares output count, txid,
  fee, recipient value+address and change value+address against the frozen record.
- Signature acceptance: `signing.py:156` (`accept_signature_update` — equal input/output
  counts, identical `tx` serialization, no removed or changed prior signature, clones the
  **reviewed** PSBT and copies only `partial_sigs`, then re-verifies); completeness and
  finalization `signing.py:258` (`finalize_multisig`, `len(ordered) < threshold` raises,
  txid re-checked).
- PSBT construction and independent observation: `wallet_service.py:731`
  (`build_unsigned_psbt`; docstring at `:736`: "never sign/broadcast"), previous-transaction
  cross-check against the utxo's txid/value/script at `wallet_service.py:850-853`,
  independent-outpoint check `wallet_service.py:181`, gap-limited scan
  `wallet_service.py:498` (`GAP_LIMIT=20` at `:36`, `MAX_INDEX=100` at `:37`).
- Change-policy trust boundary: BSMS-declared vs standard-derived change —
  `probe.py:120-179`, `wallet_service.py:357` (`_conventional_change`), governed by
  `CHANGE-ADDRESS-REVIEW.md`.
- Broadcast gate: `gui.py:994-997` (mainnet requires the per-transaction opt-in) and the
  library's own fail-closed default `wallet_service.py:70-82` (`mainnet_opt_in: bool =
  False`, "Explicit mainnet broadcast confirmation is required."); submit under the session
  lock at `gui.py:1027-1035`.

### Asset 5 — privacy

- Diagnostic discipline: fixed-code 80-event buffer and device *class* only
  `gui.py:414-448`; token scrub (`_clean_token`, drop rather than escape) `gui.py:341`.
- Session token: `secrets.token_urlsafe(32)` `gui.py:453`, delivered only in the launch URL
  fragment `gui.py:91-101`, checked per request `gui.py:634-643`, never logged
  (`log_message` no-op `gui.py:518-520`).
- "Never send xpubs" to explorers: `wallet_service.py:133`; diagnostics file
  `~/Downloads/bitcoin-easy-signer-diagnostics-{APP_VERSION}.json` `gui.py:682`.
- No committed wallet material: `.gitignore` covers `*.bsms`, `*.psbt`, `*.txn`, `*.log`; a
  regex sweep of the tree found no private key or provider token.

### Assets 2 & 4 — credentials and the release chain

- The single publish path: `.github/workflows/build-candidate.yml` — `on:
  workflow_dispatch:` only (`:23-24`), inputs `notarize` (default `false`), `publish`
  (default `false`) and `candidate_run_id` (`:34`). No `push`, `pull_request`,
  `pull_request_target`, `release` or `tag` trigger exists anywhere in the repository.
- Publish guards inside that workflow: publish requires notarize (`:57-61`), ref
  `refs/heads/main` (`:65`), a numeric candidate run id (`:69`), a candidate run that
  succeeded on the same commit through this same file (`:710`), a manifest asserting
  `notarize=true, publish=false` (`:733-739`), `shasum -a 256 -c SHA256SUMS`
  (`:746-754`), an unsigned/unnotarized refusal (`:979`), and a no-overwrite tag guard
  (`:986-996`) before `gh release create` (`:997`).
- Branch sweep control: `scripts/check-publish-paths.sh`, run on every dispatch
  (`build-candidate.yml:56`); it enumerates the **remote's** heads and fails closed on a
  retired workflow filename, an unreadable blob, a literal `contents: write`, or the
  literal string `gh release`.
- Secret **names** (values are not in the repository and were not requested):
  `MAC_CERT_P12_BASE64`, `MAC_CERT_PASSWORD`, `MAC_APP_SPECIFIC_PASSWORD`,
  `MAC_NOTARY_KEY_P8_BASE64`, `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`; environment groups
  `apple-signing` (the three `MAC_*` signing secrets) and `release-signing` (both GPG
  secrets), each with a branch policy of `main` only.
- **Credential wiring at the target revision — found by this survey, fixed after it.** The
  workflow names those six secrets, but `d525f31` declares **no `environment:` key on any
  job** (`grep -c 'environment:' .github/workflows/build-candidate.yml` → `0`; the same is
  true of the run revision `81f58ec`). The only stored copies are the environment-scoped
  secrets above — the repository-level secret list is empty — and a job is handed environment
  secrets only if it names the environment, so a notarized build or a publish would have
  failed closed at `build-candidate.yml:226-227` (`MAC_CERT_P12_BASE64 is not set`) and
  `:794-795` (`GPG_PRIVATE_KEY is not set`). The fix was already written once and lost: the
  discarded 2026-10-08 revision `1a5e9bf` declares `environment: apple-signing` (its line 162)
  and `environment: release-signing` (its line 719), under commit `2f779e2` "Record the
  revision that carries credential recovery (CT-97)". The rewind of `main` dropped that wiring
  and reintroduced CT-97. It was restored after this survey at commit `333b361`. **Consequence
  for the panel:** at `d525f31` the credential resolution cannot be exercised at all, so the
  notarize and publish steps are testable by reading, not by running, until the revision under
  audit carries the fix.
- **The fix, proved by a real build (post-survey, owner-directed).** Reading can show that a job
  names the environment; it cannot show that the stored values arrive, because a wrong
  password, an expired certificate and a secret filed in the wrong store all look identical
  from outside. On 2026-10-10 the owner directed one candidate dispatch to settle it. It is
  recorded here because it is the only hard evidence that the release path still works after
  the rewind, and because the panel must know exactly what it does and does not prove.

  | Fact | Value |
  |---|---|
  | Run | `38056270688` — <https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/38056270688> |
  | Workflow and commit | `build-candidate.yml` dispatched from `main` at `05ae6aeec1a460f1a0faffbdf11850fd2afd2263` |
  | Inputs | `notarize=true`, `publish=false` — the documented candidate step |
  | Result | `completed` / `success`; all seven jobs green |
  | Published | **Nothing.** The newest release is still `v0.6.7`; no tag was created |

  Credential steps, by name, read from the run's own job record
  (`run_attempt` 1): `Import the Developer ID certificate` **success**,
  `Provide notary credentials` **success**, `Build the DMG` **success**,
  `Verify the DMG, the signature and the bundled app` **success**. The guard
  `A requested notarized build must fail closed without credentials` also passed, so the run
  took the credentialed path rather than degrading silently.

  Proof that `publish=false` was honoured, in the same record: in the `SHA256SUMS` job,
  `Sign the checksum manifest with the release key` is **skipped** while
  `Attest build provenance for every asset` **succeeds**.

  Artifact digests, computed by GitHub over the exact uploaded bytes; a referee can re-read
  them at `.../actions/runs/38056270688/artifacts`:

  | Artifact | Bytes | sha256 |
  |---|---|---|
  | `macos-dmg` | 33,743,651 | `6c0a0589edd6bc65dd37c1860f8150f0edefa6898bcc8742219efb81ca103087` |
  | `windows-bundle` | 35,402,302 | `28ec47abb5fc91db6498e4124e9b99304c93b6531c9959af4d0c16aec12d1c61` |
  | `linux-desktop` | 134,966,290 | `3e2bd459ca71ad53cba63a12a2455b5262c9579717724750c97619f80345e0d7` |
  | `source-archive` | 3,450,507 | `085bacc0ef95719c4c7cc89827b56d8e22a30f4d189e9bdbcaaf703dc12ff3f6` |
  | `release-assets` | 207,563,242 | `e88c498c518a369bacf71a287f650ea56b5c84490538df74ac09ce182580c924` |
  | `sha256sums` | 580 | `d473b23f06a5856afaa9ef22e6cb52d315a73a89ad5c6e8e1653d252d9658d7a` |
  | `candidate-manifest` | 254 | `c8a79a40b71e35c649deeac21105e81ba877fc1c4efc0867b1f3f559548add9c` |

  - **What this proves:** the Apple signing certificate and the notary credentials are reachable
    by a dispatched build from `main`; signing, notarization and verification complete; the
    provenance attestation is emitted; and no human approval sits anywhere in the path. No
    session handled a secret value.
  - **What it does not prove:** the GPG half. `Sign the checksum manifest with the release key`
    was skipped by design, so the release key stays unexercised until a real publication. And it
    says nothing about the audited revision — the run is at `05ae6ae`, *after* `d525f31`. The
    panel must still confirm that the revision it locks carries the environment keys, which at
    this post-survey state are `build-candidate.yml:153` and `:700`.
  - **A correction for whoever tries to re-check this:** the Jobs API does not expose a job's
    environment at all — the field is absent from the response, not present-and-null. "No job
    entered a signing environment at `d525f31`" is therefore established by reading the
    workflow text (no `environment:` key), and can never be established from that API.
- Release key: committed public `signing-key.asc` = `rsa4096`, fingerprint `ACCC 2F1C D436
  9128 D549 CC58 E972 85D2 DD0B D6D7`, uid `Bitseeker LLC <release@bitseeker.llc>`; the
  private half lives only in the `release-signing` environment secret and is bound to that
  public key by the `gpg --verify` step at `build-candidate.yml:850-851`.
- Attestation: `actions/attest-build-provenance@4d101475…` (`:813`) with `id-token: write`
  and `attestations: write` (`:693-694`).
- Vendored, hash-pinned inputs: `vendor/` (patched embit wheel, libusb dylib/dll, Linux
  libusb tarball, AppImage runtime) with digests asserted in the build recipes; hash-locked
  dependency sets `requirements*.lock`, installed with `--require-hashes`.

### Entry points (how data or a user gets in)

- Loopback HTTP API: `gui.py:1262` and `desktop.py:316` —
  `ThreadingHTTPServer(("127.0.0.1", 0), …)`, ephemeral port, token-gated; 14 POST routes
  and 3 GET routes.
- Desktop wrapper: `desktop.py:50` (`DesktopBridge`), window creation `desktop.py:323`, PSBT
  save bridge `desktop.py:84-103` (pins the prepared base64).
- Operator-supplied BSMS file: `probe.py:81` (`load_bsms`), `probe.py:93` (`parse_bsms`,
  64 KiB cap at `:25`).
- Hardware signers over USB: HWI 3.2.0 via `scripts/hwi_entry.py`, identity pinning in
  `probe.py:211-214` and `:391-428`, key-possession challenge `probe.py:620-655`.
- Outbound network: Esplora scans/broadcasts and fee/price references through `safe_http.py`
  (`open_url` `:143`, TLS context `:102-114`, redirects refused `:43-68`); explorer base
  URLs `network_config.py:30,38,46`, mainnet secondary `blockstream.info` `:57`.
- Operator-configured explorer URLs persisted at `network_settings.py:25-38`, validated
  `:48-68`, network-verified against genesis/checkpoint `:118-145`, written `0o600` +
  atomic replace.

### Data stores

`~/Library/Application Support/Easy Bitcoin Multisig/settings.json` (macOS; `%APPDATA%` on
Windows, XDG on POSIX) — server URLs only, docstring "Never store wallet data", dir `0700`/
file `0600`; in-memory session state `gui.py:451-482`; the privacy-limited diagnostic
buffer; the diagnostics JSON and saved PSBTs in `~/Downloads` (`gui.py:328-385`,
`gui.py:414-448`). No wallet material is persisted by design.

### Repository-controlled platform settings (measured this cycle, read-only, via the API)

- `main` carries branch ruleset **`protect-main`** (id `24840839`, created 2026-10-10):
  branch deletion and non-fast-forward pushes are blocked, with **no bypass actor**, so it
  binds the owner's own tooling too. Ordinary pushes are unaffected. There is still **no
  classic branch protection** (`/branches/main/protection` → 404 — rulesets are a separate
  mechanism).
- Tags carry ruleset **`protect-tags`** (id `24841466`, created 2026-10-10): tag deletion and
  non-fast-forward tag moves are blocked across `refs/tags/v*`, with **no bypass actor** — the
  rule that AGENTS.md states in prose ("moving or deleting a published tag is forbidden") is
  now enforced by the platform. Tag **creation is deliberately not restricted**: the ruleset
  omits the `creation` rule, because the release job's only tag write is
  `gh release create "$tag" --target "$GITHUB_SHA"` (`build-candidate.yml:1009`), and no
  workflow anywhere deletes or moves a tag (`grep` over `.github/workflows/` returns that one
  line). The control therefore protects published tags without inhibiting an agentic release:
  a dispatched promotion still creates its tag, and only a rewrite of an existing tag is
  refused. Recovery cost, stated plainly: with no bypass actor, withdrawing a tag that a
  failed publication left behind requires an admin to change the ruleset first — the same
  property `protect-main` has, accepted by the owner for the same reason.
- **Considered and deliberately deferred: GitHub "immutable releases".** The setting exists and
  is off (`GET /repos/…/immutable-releases` → `{"enabled": false}`). It would lock a
  published release's assets and tag and emit a signed **release attestation** binding tag,
  commit and assets — all desirable. It is *not* enabled yet because GitHub's own guidance is
  to create the release as a **draft**, attach every asset, then publish, and this workflow does
  the opposite: `gh release create … dist/*` (`build-candidate.yml:1009-1011`) publishes first
  and uploads the assets afterwards, which is exactly the pattern immutability is documented to
  obstruct. Enabling it as-is would risk breaking the *next real publication* — a failure no
  candidate run can detect, and precisely the kind of derailment this plan exists to prevent.
  It is recorded as a named next-cycle improvement: change the release job to draft → upload →
  publish, test that path with a real publication, and only then enable immutability.
- Environments `apple-signing` and `release-signing` each carry a branch policy of `main`
  and `can_admins_bypass: true`, with **no required reviewers** — an owner decision (section
  0), because a human gate would sit in front of the agentic tooling the owner directs.
  `github-pages` allows `gh-pages` and `main`. **No job in `build-candidate.yml` at
  `d525f31` enters any environment** (no `environment:` key exists in the file; the discarded
  revision `1a5e9bf` did declare two), so at the target revision these policies gate nothing
  and the signing secrets are unreachable — see the credential-wiring bullet above.
- Actions: `allowed_actions: "all"`, `sha_pinning_required: false` (owner decision: do not
  lock out authorised tooling); default workflow token `read`; `secret_scanning` and
  `secret_scanning_push_protection` enabled; `dependabot_security_updates` and validity
  checks disabled. Sole collaborator `cjtsh` (admin), zero pending invitations, zero forks,
  and all 57 pull requests (state `all`) were opened from a branch of this repository — no
  fork PR has ever existed. No deploy keys, no webhooks, no repository-level secrets; the
  authorized OAuth/GitHub Apps list could not be enumerated by the surveyor's token, so the
  owner must read it from Settings → Applications.
- The workflow registrations `build-windows.yml` and `build-linux.yml` still exist with
  state `disabled_manually` although their files are absent from every ref.
- The repository's own text now matches the single-maintainer policy: `CONTRIBUTING.md` was
  rewritten and `README.md:95` reworded after this survey (commit `247ca73`). At the target
  revision `d525f31` both still invited outside pull requests, which is the mismatch the
  panel should record against the section 0 policy.

## 5. In scope

- All first-party application code at `d525f31`: `probe.py`, `wallet_service.py`,
  `signing.py`, `gui.py`, `desktop.py`, `network_config.py`, `network_settings.py`,
  `safe_http.py`, `version.py`.
- The entire interface and its gates: `ui.html` (review screens, per-transaction mainnet
  consent, developer-mode/network gate, pending-payment banner, busy/progress ownership,
  large-amount floors, palette invariants).
- The HWI integration boundary: `scripts/hwi_entry.py` and the HWI timeout/retry rules
  stated in `AGENTS.md`.
- Build and release pipeline: `.github/workflows/build-candidate.yml`,
  `.github/workflows/linux-inputs.yml`, `.github/workflows/windows-inputs.yml`,
  `scripts/build-macos.sh`, `scripts/build-linux.sh`, `scripts/build-windows.ps1`,
  `scripts/build-sbom.py`, `scripts/build-source.sh`, `scripts/notary-args.sh`,
  `scripts/verify-windows-bundle.py`, `scripts/check-publish-paths.sh`.
- **Repository-controlled platform settings as controls:** the absence of rulesets/branch
  protection, the environment protection rules, the default token permission, and the
  lingering `disabled_manually` workflow registrations — evaluated as they are, not as the
  comments describe them.
- Dependency pinning as a control: `requirements*.txt`/`*.lock` hash pins and the documented
  `vendor/` delta. The pins and the delta are in scope; the pinned code's internals are not.
- **Invariants with no machine pin, which must be tested rather than cited:** no test asserts
  that the app refuses seed phrases, private keys or PINs; no test asserts that only a
  single BSMS file is accepted; no test binds `AGENTS.md`'s declared version string to
  `version.py`. These three are the invariants closest to the owner's own safety vocabulary.
- **The evidence ceiling of the suite, which the panel must not exceed in its claims:** the
  suite is large (489 Python test methods across 27 modules, plus 10 self-contained `node`
  `.cjs` UI tests) and CI fails closed on any skip
  (`.github/workflows/build-candidate.yml:103-115`; `tests/` contains exactly three skip
  sites and no `xfail`), but the **device layer and every outbound network call are
  exercised only against mocks** — no hardware signer is ever attached and no live explorer
  is ever contacted (`tests/test_probe.py`, `tests/test_hardening_pins.py`,
  `tests/test_desktop.py`, `tests/test_wallet_service.py`, `tests/test_gui.py:51`,
  `tests/test_send_flow.py`). HWI helper byte-identity, the fresh device key-proof before a
  PSBT is sent, and the device→finalize→broadcast journey therefore have **no live exercised
  evidence** — only logic coverage over stubs. That is a stated coverage limit, not a
  control, and the panel must say which of its conclusions rest on it.
- **Vendored provenance gap:** the two embit source archives
  (`vendor/embit-0.8.2+besa.1.tar.gz` and `vendor/embit-upstream-2b375a.tar.gz`) have **no
  machine-checked SHA-256 anywhere in code, tests or scripts** — their digests exist only as
  prose in `vendor/README.md:7,16` — even though they are the stated provenance evidence for
  the hash-locked wheel. Every other `vendor/` input is digest-asserted in code.
- `tests/` as evidence: the panel must check that every control the repository claims is
  actually pinned by a test that can fail. `AGENTS.md` names some; the panel must also test
  the claims made by name in `releases/PATCH-0.6.8.md`.
- `releases/PATCH-0.6.8.md` and `releases/OWNER-ACCEPTANCE-2026-10-07.md` as the
  claimed-fix ledger: every row's "closing evidence" is a claim to be broken, not a
  citation to be trusted. This cycle's ledger carries CT-49, CT-54, CT-56, CT-58, CT-59 and
  CT-72 through CT-95; its dated deferrals are CT-90 (the practice-network secondary explorer
  left unset at `network_config.py:57-58`), CT-59 and CT-54, the last two with a hard expiry
  of 2027-10-07. Any row the ledger closes by a dated owner acceptance note must be confirmed
  against what that note says it is.
- `AGENTS.md` itself as the behavioral contract the code is audited against.

### In-scope threats, in the framework's finite form

Each in-scope threat is recorded below with the six required fields. Ranked by impact and
plausible reachability. These are the threats the audit must test; the list is deliberately
finite, and "conceivable" alone does not promote a conjectural issue into a mandatory test.

**The list is closed.** The panel works T1–T12 and stops. Anything else it imagines is
written onto a next-cycle list — named, dated, and **not investigated in this cycle**. No
threat may be added to section 5 after the lock without the owner amending this file and
re-signing, which voids the lock. An item already closed by a demonstrable test, or by a
dated owner acceptance, is not reopened absent new code at a later revision.

**Burden of proof — the reciprocal of "a test that cannot fail does not count as a fix."**
A finding that would block release must be *demonstrated* against the locked revision: a
command or test the referee can run and watch fail, or an API artifact, at
`file:line @ d525f31`. A concern that cannot be demonstrated is recorded as a **note**, is
never graded, and does not by itself change the grade. Severity cannot inflate a note: a
weakened control with a reproducer is CONDITIONAL; hygiene or robustness without a
demonstrated path is an Info item; a speculation is a speculation. This cuts both ways —
every one of T1–T12 must still be *tested* with evidence of that kind, and an untested
threat cannot be cleared by argument.

| # | Asset + plausible attacker starting capability | Repository-controlled entry point / trust boundary | Concrete prohibited outcome | Observable acceptance test or evidence | Exclusions and assumptions | What result would block release |
|---|---|---|---|---|---|---|
| T1 | Asset 1/3 — the app itself is the attacker's surface; no prior access required beyond the operator using it | Review → prepare → sign → finalize → broadcast pipeline in `gui.py` and `ui.html` | A transaction is signed or broadcast whose recipient, amount, fee or change differs from what the final screen displayed | Byte-level comparison of the frozen `PreparedPayment`, each signer request, the finalized transaction and the broadcast hex; tripwires `tests/test_gui.py`, `tests/test_send_flow.py` broken red by the referee | Assumes the operator's own machine and the app binary are what they claim to be; does not assume the operator can read a hex payload | Any demonstrated divergence between displayed and signed/broadcast bytes |
| T2 | Asset 1 — anyone or anything that reaches the local API with the session token | `POST /api/broadcast` (`gui.py:988-1035`) and the library's `broadcast_transaction` | Mainnet broadcast without the per-transaction human confirmation, or with the confirmation suppressed/forged | `gui.py:994-997` plus `wallet_service.py:81-82`; negative test with the opt-in omitted, and a UI test that the checkbox cannot be defaulted | The token is the control; a test HTTP client is assumed, not a browser | A broadcast path that succeeds with the backend opt-in omitted |
| T3 | Asset 1/3 — a counterfeit or compromised hardware signer (firmware is out of scope; *the app's* acceptance of a hostile response is not) | `signing.py:156` and `probe.py` device-verification path | A device returns a correctly-signed but *different* transaction, and the app accepts it or injects it into the reviewed PSBT | `accept_signature_update` must reject a changed `tx`, a removed signature, or foreign partial sigs; the cycle-3 "counterfeit device returning a thief transaction" scenario must be reproducible as a test that fails red if the check is removed | The device's own display and firmware are trusted to the extent README states; the app must not require the operator to notice | Any path where a device response other than verified partial signatures reaches the finalized transaction |
| T4 | Asset 1/3 — a correct-but-incomplete wallet definition, or a hostile Esplora server answering the scan | BSMS change declaration vs `.1/*` inference (`probe.py:120-179`, `wallet_service.py:357`); change selection in `ui.html` | The operator's change is sent to an address the wallet's own definition does not own, or a sweep is silently substituted | `CHANGE-ADDRESS-REVIEW.md`'s stated rules tested against BSMS with and without a declared change branch; a "no route applies" BSMS must not silently produce a change output | The BSMS file itself is assumed to arrive over a trusted channel (README:41 states the app cannot tell whose key is whose) | Any change output not justified by the file or the stated standard, or a sweep offered as a workaround |
| T5 | Asset 1/5 — a malicious or lying Esplora/price server (external service, but the app's trust in it is internal) | `wallet_service.py:131-192` explorer calls; `network_settings.py:118-145`; the price quote feeding the large-amount floors `gui.py:1195-1209` | Funds sent because the app believed a lie: a wrong balance, a wrong fee, a wrong outpoint, a wrongly-identified network, or a suppressed large-amount prompt | Response shape/range validation, the independent second explorer for mainnet (`wallet_service.py:191-192`, `gui.py:240-258`), genesis/checkpoint verification, and the local 0.1/0.04 BTC floors that a lying-low price cannot suppress | Explorer honesty is assumed *only* to the extent the app cross-checks it; a single-source chain (Testnet4, Mutinynet) is a known asymmetry and must be reported as such | Any money-path decision resting on an unverified single source without a stated, tested fallback |
| T6 | Asset 1/5 — any process or web page on the operator's machine | The loopback HTTP API `gui.py:514-517`, `gui.py:1262`, host/origin/token gate `gui.py:569-572`, `gui.py:634-643` | An unauthorized local page drives the API: rebound DNS name, cross-site form, or a leaked token | Host equality, the Origin clause, constant-time token compare, the fragment-only token delivery, and the absence of an HTML-injection sink (`innerHTML`/`insertAdjacentHTML`/`outerHTML` nowhere; CSP nonce per response `gui.py:536-539`, `gui.py:583-587`) | Other processes on the operator's machine are assumed hostile, which is the point of the gate; the OS account itself is not modelled | Any request that mutates money-path state without the token and an exact Host |
| T7 | Asset 1/2 — a substituted HWI helper or `hwilib` payload | `probe.py:211-214`, `:294-308`, `:391-428`; `scripts/hwi_entry.py`; the `hwi.sha256` sidecar inside the signed bundle | A poisoned helper signs or exfiltrates; a source-mode import loads a tampered `hwilib` | Byte identity before the helper may speak, exact version-line membership, and pins that can actually fail. **Note for the panel:** the tripwire at `tests/test_hardening_pins.py:331` re-asserts the `HWI_PAYLOAD_PINS` constant and can never fail; `probe.py:211-214` pins only `hwilib` and `hwilib._cli` while source mode imports the whole package — this row must be tested, not cited | The packaged helper's own bytes inside the signed bundle are covered by the outer signature; source mode is a developer path | A substitution path into the helper or `hwilib` that the pins do not refuse, or a claimed pin that cannot fail |
| T8 | Asset 2/4 — an actor holding push or dispatch rights on this repository (in practice the owner account: `cjtsh` is the sole collaborator, verified from the API; forks are outside the model per section 0), or a workflow body able to escalate its own token | `.github/workflows/build-candidate.yml`; the dispatch-only trigger and its guards; `scripts/check-publish-paths.sh`; the repository's platform settings | Publish-capable bytes reach a release from a path other than the audited candidate→promote chain: a second publish path, an unsigned/unnotarized publish, a tag or asset overwrite, or code execution inside a `run:` block | The publisher guards (`:57`, `:63`, `:69`, `:698`, `:792`, `:845`, `:954`, `:978`), the branch sweep, the no-overwrite tag guard, and the absence of any other publish-capable file. **Known surface to test, not assume closed:** `build-candidate.yml:69` interpolates the free-text `candidate_run_id` input directly into bash (the safe `env:` handling is at `:702`); `check-publish-paths.sh` matches only literal `contents: write` and the literal string `gh release`, and looks only in `.github/workflows`; `release` holds `contents: write` on every dispatch (`:833`) with no required reviewers on the environment; the `release` job has no job-level `if:`; the "only publish path" claim holds for `main` but not repo-wide — historical tags `v0.1.11`–`v0.6.4` still freeze publish-capable `build-candidate.yml` text with `contents: write` and `gh release create` (the repo discloses this residual itself at `releases/OWNER-ACCEPTANCE-2026-10-07.md:82-98`), and with no non-main remote heads left the sweep now passes trivially | GitHub account compromise, platform compromise and stolen owner credentials are **external assumptions**; the panel evaluates the permissive-workflow path, which *is* in scope | Any demonstrated second publish path, unsigned publish, overwrite, or command injection reachable by a repository-controlled actor |
| T9 | Asset 4/2 — anyone who can alter what the operator downloads | The release page, `SHA256SUMS`/`SHA256SUMS.asc`, the SBOM, and the site that links them | The bytes a user downloads are not the bytes the candidate run produced, or the published list of hashes is not the one the pipeline signed | The candidate run-id/manifest binding (`:707-739`), `gpg --verify` against the committed key (`:850-851`), the no-overwrite guard, and a review of what the *download page* actually points at | The GitHub release page is assumed honest about what it stores; the repository is not assumed to control the CDN | Any published asset that cannot be traced to a successful candidate run at that commit, or a public link to bytes the pipeline did not produce |
| T10 | Asset 4 — the public download surface: measured by the cycle-4 survey on 2026-10-10 as three releases stale (`docs/index.html:31,243-245` then offered **v0.6.4** downloads and `:231,268` presented the **v0.6.4** Z.ai review as the security evidence, while v0.6.5, v0.6.6 and v0.6.7 existed) | `docs/` (GitHub Pages) and the release page | The operator is directed to an older build and to evidence about a revision the audit did not grade, while newer, graded bytes exist | **Found by the cycle-4 survey and corrected on `main` at `fc65647`** — v0.6.7 metadata, labels, download buttons and an honest review-status notice, with the 63 older releases marked *Superseded* in their notes and every tag and asset retained; verified live (`https://bitcoineasysigner.com/` returned `softwareVersion":"0.6.7"` with no v0.6.4 download link; the publication records then moved it to `v0.6.8` at `b0a7324`). The panel must still run the literal comparison of every version string and download URL in `docs/` against the release list, and record the result against the tag. The audit PDFs the site links label those reviews "independent" while the framework lock says independence "cannot be determined" (`bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.6.md:13`) — wording the Public Security Statement must not repeat | The site is not a release artifact and is out of code scope; this is a *release-channel and assurance* claim, which asset 4 covers | Whether anything the operator is directed to download differs from the bytes the pipeline published for the graded revision. A public statement of what to download and what was graded disagreeing with the graded revision is a **publication/hygiene defect** (section 8, question 2), not a code path to an unforgivable act |
| T11 | Asset 5 — a diagnostics file or log shared with a reviewer, or a network observer | `gui.py:414-448` diagnostic events, `gui.py:682`; `log_message` `gui.py:518-520`; the Esplora requests themselves | xpubs, addresses, txids, device identities or the session token reach a log, a diagnostics file, the repository, or a server beyond the operator's chosen explorer | Fixed-code events with device *class* only, token scrubbing, the log-silence tripwire (`tests/test_gui.py:928-951`), and a byte-level check of a produced diagnostics file | The chosen Esplora server learns the addresses the operator scanned for; that disclosure is consented to in the UI and is a stated design property, not a finding | Any wallet-identifying string or token in a persisted file, a log, or an artifact |
| T12 | Asset 1/3 — a hostile or mistaken BSMS file (accepted as a boundary by the owner, but the boundary must be stated where the operator meets it) | `probe.py:93` parse; the step-1 import UI and help text | The operator signs for a wallet definition the file's author chose — an attacker-named key | `tests/test_gui.py` `WalletFileTrustPins` plus the boundary statement in README and the step-1 help; the app must not *claim* to verify whose key is whose | Trusted delivery of the BSMS file is an explicit owner-accepted assumption (CT-61), not a control | Any UI or README text that implies the app verifies key ownership, or a parse that accepts a file the documented rules reject |

## 6. Out of scope — and why

- **`docs/` website** — GitHub Pages marketing and manual content; ships separately (CNAME,
  `.nojekyll`) and shares no code with the application or its build. Its version drift is
  recorded as T10 and section 8 rather than audited as code.
- **`releases/` and root status/history documentation** — the repository's own status and
  release claims; historical records, not executable surface. **Exception:** the two
  claimed-fix ledgers named in section 5 are evidence inputs for the referee.
- **Prior AI audit reports** (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) — history only and
  not inputs to this cycle (independence condition).
- **Internals of pinned third-party dependencies** — hwi 3.2.0, pywebview 6.2.1, pyinstaller
  6.22.2, requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, and upstream embit beyond the
  documented local delta. They are hash-locked, and `CURRENT-STATUS.md:113` records an
  independent component audit of this stack as outstanding — a separate effort with its own
  plan.
- **Hardware wallet firmware** — external devices with their own trust properties; the app
  audits *its side* of the HWI exchange, not the devices.
- **Live explorer operators** — external services the design treats as untrusted
  observations; their own security is not this repository's.
- **GitHub account security and GitHub platform availability/honesty** — external
  assumptions under the contribution model.

## 7. Not examined — and why

- **The 2026-10-08/09 line of development.** Repository push events show commits
  (`1a5e9bf`, `7d43464`, `2f779e2`, `5d826a1`, `fea859c`, `f79203c`, `f4ca17b`, `f13b190`,
  `bf3ba57`, `91aedfa`, `39af55b`) pushed to `refs/heads/main` on 2026-10-08/09, branch
  create/delete events for `cycle5-0.6.8`, `chore/fresh-color-team-v1.5-audit`,
  `archive/legacy-audit-artifacts` and others, Pages builds on those commits, and PR #57
  ("Superseded: audit-artifact reset, not adopted", opened 2026-10-09T19:16:05Z, closed
  unmerged). Today `main` is `d525f31` and `git ls-remote` shows one branch. Those commits
  are unreachable from every ref, but they are not gone: the GitHub API still serves the
  objects by SHA, and this survey read the workflow text at `1a5e9bf` that way — which is how
  the lost credential-recovery wiring (CT-97) was recovered (section 4). What cannot be
  audited is the Oct-8/9 tree **as a whole**: only objects the surveyor knew to ask for were
  read, nothing establishes the list is complete, and the branch that carried the work is
  gone. This cycle does **not** treat the surviving tree as a record of what was pushed; the
  delta is recorded as a provenance gap and a question for the owner.
- **The post-survey fixes.** Three commits landed after the target revision and are therefore
  **not** part of what the panel audits: `247ca73` (the contribution-policy wording in
  `CONTRIBUTING.md` and `README.md:95`), `333b361` (restoring the `environment:` keys that
  make the signing credentials reachable), and the commit that carries this revision of the
  plan. The panel should verify the two *defects* as they stand at `d525f31` and treat the
  fixes as next-cycle verification, exactly as `releases/PATCH-0.6.7.md` stands to the
  cycle-3 audit.
- **The survey's writes.** The runbook's read-only rule was set aside at the owner's explicit
  direction for these commits, for publishing this plan (section 9, revision 3), and for one
  candidate build dispatch made after the survey (revision 5, run `38056270688`). No other
  write was made: no branch was created, no release touched or tag created, no artifact
  downloaded, no secret value requested. The dispatch attached no release, changed no source
  file, and left the tree byte-identical.
- `vendor/libusb-1.0.0.dylib` — a compiled arm64 binary (and the Windows DLL and Linux
  AppImage runtime alongside it). Provenance and hash pins are documented at
  `vendor/README.md:36-47`; the binaries' internals were not reviewed.
- The vendored embit wheel internals — only the documented two-edit delta against the
  pinned upstream archive (`vendor/README.md:10-34`); the full library source was not read.
- `ui.html`, `gui.py`, `wallet_service.py`, `probe.py`, `desktop.py` and
  `tests/test_workflow_config.py` — sampled at entry points, gates and stated invariants
  via targeted search; not read line-by-line. Complete coverage is the panel's job.
- `docs/audits/*.pdf` — four prior third-party AI audit reports in binary PDF form, not
  read.
- **Published release bytes** — no artifact was downloaded or hashed at survey time; the
  survey was static and offline. `releases/PATCH-0.6.7.md` and the `v0.6.7` commit message
  both assert an 8/8 `SHA256SUMS` re-check and a Good GPG signature, and the API confirms
  the tag, the run ids and the current asset list — but **those assertions are unverified by
  this survey** and must be treated as claims, not established facts.
- **The GitHub Actions logs** of candidate run `37644267740` and promote run `37655666900` —
  their event, branch, commit and conclusion were read from the API; the logs were not.
- **GitHub secret values** — only names were read (workflow text and the environment list);
  values were never requested and are not in the repository.
- **The 13 CT-48 remediation commits** — `releases/PATCH-0.6.7.md:61-80` cites thirteen
  commit ids as its "branches kept" evidence for the CT-48 fix, and every one of them
  returns `fatal: Not a valid object name` from this clone;
  `git log --all --grep='Delete the publish-capable workflow'` is empty and the remote has
  only `refs/heads/main`. A claim the referee is told to verify therefore rests on evidence
  that no longer exists in the repository.
- **Full git history** — authorship sampled only: `mypbs`, `CJT.sh` (two identities),
  `Chris Terry`, `Bitseeker LLC` — all map to the owner. The repository documents
  AI-assisted development and prior AI audits, so line-level provenance of individual hunks
  is not answerable from the repository alone.
- **Runtime behavior** — the survey was static: no build, no server, no device, no
  dispatch, no download (read-only rule).

## 8. Questions for the owner

The five cycle-`v0.6.4` questions and their answers are carried forward unchanged (section
9 of the signed cycle-`v0.6.7` plan); the standard does not change until it is passed. This
cycle asks six new ones, each grounded in something measured on 2026-10-10; the sixth
arrived with the owner's 2026-10-10 amendment and is the one the amendment itself depends on:

1. **The rewound default branch — answered by the owner, 2026-10-10.** The Oct-8/9 line was
   abandoned deliberately, by the owner's decision, and the reason is recorded here so the
   panel is told it rather than left to speculate:

   > After the `v0.6.7` release, further audit-cycle work was started with several different
   > agentic tool sets, and it did not converge. Review rounds kept producing additional
   > speculative failure scenarios; each was treated as a defect, fixed, and re-reviewed,
   > without any scenario ever being demonstrated against the code. One cycle ran to roughly a
   > hundred executions without yielding a reproducible finding. The owner stopped it and
   > directed a return to a clean state at the `v0.6.7` release. This is a single-maintainer
   > project and the framework is being adopted incrementally; earlier cycles did not
   > converge, which is why this cycle's plan states a closed scope and a burden of proof.

   **The commissioned reviewer is Z.ai (GLM)** — the same tool set whose earlier run over this
   same release, `v0.6.7`, is the open-ended cycle described above. That earlier run is exactly
   what this reset replaces: the target did not change, the scope did. The incoming review is
   told its own history here so that it works the closed list in section 5 under the burden of
   proof, and does not resume unbounded threat enumeration over `v0.6.7`.

   Facts the panel should have, and need not investigate further:
   - The commits pushed to `main` on 2026-10-08/09 are unreachable from every ref. They remain
     retrievable **by SHA** through the GitHub API — which is how the credential-scoping change
     recorded in section 4 was recovered. Nothing in the `v0.6.7` release depends on them.
   - The work prepared on that line, including a "fresh Color Team v1.5 audit" branch, was
     **never adopted**. Pull request #57, which would have introduced it, was closed unmerged.
   - **No release was published from that line**, and no published byte of `v0.6.7` was altered
     by the reset: the release artifacts predate it by a day.
   - The discarded line is **out of scope** (section 6). The audit target is the published
     release (section 1), not the abandoned work.
2. **The public download page — answered by the fix, 2026-10-10.** The page was found three
   releases behind: `docs/index.html` offered v0.6.4 from every download button and presented
   the v0.6.4 Z.ai review as the current safety evidence, on the same repository whose v0.6.7
   sources had corrected exactly this pattern elsewhere. It is now corrected and verified
   live. Commit **`fc65647`** on `main` moves the JSON-LD metadata, the version label and all
   three download buttons to `v0.6.7`; rewrites the review notices to state that **no review of
   `v0.6.7` has been published yet**, that a Color Team audit of this release is being
   commissioned, and that the older Z.ai reports describe only their own revisions; and
   relabels the footer links per revision. `docs/user-manual.html` carries the same
   corrections. The 63 releases older than `v0.6.7` now open with a *Superseded — do not use
   for new deployments* notice placed in their **notes only**: no tag was moved, no asset was
   added, replaced or deleted, and every published byte is retained. Verification: the Pages
   build for `fc65647` completed (`built`); the live site returns HTTP 200 with
   `softwareVersion":"0.6.7"` and no v0.6.4 download link; and all three `v0.6.7` asset URLs
   resolve.

   **Scope ruling, so this cannot become a loop:** the website is **not a release artifact**.
   It is absent from `SHA256SUMS`, from the DMG, bundle, AppImage and tarball, and it cannot
   affect a payment. A stale download page is a **publication/hygiene defect, not a code
   defect**: it is recorded here as found and fixed, and the panel must not raise it as a
   finding against the published release. The audited revision is the tag, and the tag's own
   `docs/*.html` still contains the text it shipped — the correction to the next release
   lands after it, on `main`, by design. If the
   panel observes the stale text in the tagged tree, this paragraph is the record that it was
   found, fixed and verified, and the item belongs on the named next-cycle list rather than in
   the grade. A future recurrence is likewise a next-cycle item, not an audit finding.
3. **Repository-controlled platform protections — answered by the owner, 2026-10-10.** At the
   target revision there was no branch protection and no ruleset anywhere, and no job entered a
   signing environment. The owner has since protected `main` (`protect-main`) and the release
   tags (`protect-tags`), both with no bypass actor, and has declined required reviewers on the
   signing environments and an Actions allow-list, on the recorded ground that either would sit
   in front of the agentic tooling the owner directs (section 0). The owner's decision rule,
   stated directly: adopt a control when it makes the system safer, does not inhibit agentic
   building of releases, and does not open an unbounded line of inquiry — otherwise defer it by
   name rather than half-adopt it. The panel need not ask this again; it should verify both
   rulesets and record that GitHub's *immutable releases* setting remains off, with the reason
   and the named follow-up in section 4.
4. **The claimed-fix ledger — answered by the owner's decision rule, 2026-10-10.** The
   referee's duty is bounded as follows, and neither half may be widened without the owner's
   amendment:
   - **Break-and-watch the release-critical controls.** For every control in the
     release-critical set — the money-path gates recorded in section 4 and the
     release-integrity gates — the referee must demonstrate that its test **can fail**: disable
     or falsify the control on a scratch copy, watch the named test fail, restore. A control
     whose test cannot fail is not evidenced by that test.
   - **Do not re-litigate the ledger.** The remaining rows of `releases/PATCH-0.6.8.md` are not
     re-broken one by one. Rows closed by a dated acceptance
     (`releases/OWNER-ACCEPTANCE-2026-10-07.md`) are taken as records. CT-54 and CT-59 are
     time-boxed deferrals expiring **2027-10-07** and CT-90 is a dated deferral recorded this
     cycle: none is a finding this cycle, and the report must carry them as open deferrals
     with their expiry dates.
   - **The unverifiable row is neither a finding nor a clearance.** CT-48's evidence cites
     thirteen branch commits (`PATCH-0.6.7.md:61-80`) that are no longer objects in this
     repository. The row cannot be checked from the tree; it is **accepted as a historical
     record** and listed in the report as "evidence no longer retrievable". Unverifiability is
     not by itself a defect — but it is also not proof.
   - **A weak test is a note, not a blocker.** If a named tripwire cannot fail — the
     `HWI_PAYLOAD_PINS` re-assertion at `tests/test_hardening_pins.py:331` is this survey's
     example — that is a **test-hygiene note (Info)** and goes on the named next-cycle list. It
     is graded only if the panel demonstrates a path by which the un-failable test lets a real
     control regress; the burden of proof applies to the panel as much as to the code.
   - The referee's claim-by-claim verification of the ledger (section 0, independence
     condition) is unchanged by this answer.
5. **The Public Security Statement — answered, 2026-10-10.** The statement is no longer gated:
   question 2 is answered by the correction above, so the public download surface and the
   graded revision now agree. The statement is written by the incoming review and published
   with the report, to the specification in section 0; until it exists, the site carries a
   truthful interim notice that the review of `v0.6.7` is being commissioned and that no review
   of this revision has been published yet. **The surveyor's model line stays exactly as
   written** — `not exposed by the harness` (sections 0 and 1). The environment contains no
   model variable, the owner has not declared one, and the plan will not guess; the panel
   should treat an unverifiable provenance line as a recorded fact about the harness, not as an
   omission.
6. **Downstream component coverage — answered from the record, 2026-10-10.** There is **no
   component audit** on record for the pinned stack, and none can be inherited:
   - The documents that exist — `releases/AUDIT-BASELINE-0.1.27.md` (v0.1.27),
     `releases/AUDIT-ZAI-0.4.3.md` and `releases/AUDIT-DEEPSEEK-0.4.3.md` (source version
     0.4.3; two independent reviewers, the DeepSeek target two docs-only commits ahead of the
     Z.ai target), `releases/AUDIT-ZAI-0.6.2.md`, `releases/AUDIT-ZAI-0.6.3.md` and
     `releases/AUDIT-ZAI-0.6.4.md` — audit **this repository's own code** at those revisions.
     The `v0.6.2` report is the only one that records a line-by-line review of inherited
     libraries, and it names **embit 0.8.0, HWI 3.2.0 and the bundled libusb** at that
     revision; the `v0.6.3` and `v0.6.4` reports cover the application and the release
     artifacts at their own tags.
   - The stack actually pinned at `v0.6.7` is **embit `0.8.2+besa.1`** (the vendored fork
     wheel, `requirements.txt`), **hwi 3.2.0** and **pywebview 6.2.1**
     (`requirements-desktop*.txt`), **libusb 1.0.30** (`vendor/`) and **PyInstaller** (per the
     published SBOM). The owner's own rule (section 0, downstream dependency policy) permits
     inherited evidence **only for the exact pinned version and only where the owner names the
     audit** — and the one named review is of embit **0.8.0**, not the pinned `0.8.2+besa.1`,
     so moving that pin invalidated the inherited evidence for it.
   - **Conclusion, and the scope ruling.** No inherited component evidence transfers to this
     revision. `CURRENT-STATUS.md:113` — an independent component audit of the inherited stack
     (embit, HWI, libusb, pywebview and PyInstaller) remains outstanding — is accurate and
     stands. Dependency *internals* are out of scope (section 0): the panel identifies and
     records the dependency boundary and the exact pins, and does **not** clear a dependency by
     citing a report about a different version. A component audit is named as a next-cycle
     item. The prior AI reports remain history and are not inputs to this cycle's conclusions
     (section 0, independence condition); this answer cites them only as the inventory of
     coverage the question asked for, and does not adopt any of their findings.

## 9. Owner review and sign-off — step two, no AI

**Corrections and notes.**

- **Revision 1** (2026-10-10, commit `df3a4b8`): none — the plan was signed as written, with
  no corrections to any section.
- **Revision 2** (2026-10-10, owner-directed amendment, this commit): additions only, except
  where noted. One bullet per change, naming the section it touches.
  - **Section 0 — Distribution and contribution policy added.** States that the repository
    is public to read, use, fork and verify, and is *not* open to public collaboration; that
    release bytes come only from `main` via the audited candidate→promote chain under the
    Bitseeker LLC key; and that push/dispatch rights, not anonymous contributors, are the
    strongest in-scope attacker capability. GitHub platform and account compromise remain
    declared external assumptions.
  - **Section 5, T8 — attacker cell restated** from "a contributor, fork, or branch that can
    push" to the actors that actually exist: holders of push or dispatch rights on this
    repository. This is the **one narrowing edit** in revision 2. It is recorded openly:
    no third party holds write or dispatch rights (`cjtsh` is the sole collaborator, verified
    from the API), so nothing reachable was removed. If an outside contributor is ever added,
    this cell and the section 0 policy must be revisited before a later cycle.
  - **Section 0 — Downstream dependency policy added**, with the rule that the pinned
    versions are the audited versions, that upstream movement is not followed automatically,
    and that moving a pin invalidates inherited evidence for that component. The measured
    platform state supports the "no automatic updates" half (`dependabot_security_updates`
    is disabled).
  - **Section 5 — closed list and burden of proof added.** The panel works T1–T12 and stops;
    anything further is recorded on a next-cycle list and not investigated; no threat may be
    added after the lock without the owner amending this file and re-signing; a closed item
    is not reopened absent new code; and a finding that would block release must be
    demonstrated with a command or test the referee can watch fail. A concern that cannot be
    demonstrated is a note, not a grade.
  - **Section 0, Public Security Statement spec — plain-language posture block added** (what
    the app is and is not, the single BSMS file, the one mainnet confirmation, the operator's
    own checks) and the distribution policy added to the required contents.
  - **Section 8 — question 6 added** on which downstream components have been audited and by
    whom; the section now carries six questions, not five. It was added because the
    downstream policy above asserts nothing about coverage the repository cannot show, and
    `CURRENT-STATUS.md:113` still records a component audit as outstanding.
  - **Not changed:** the three rubric grades, the five ranked assets, the two unforgivable
    acts, the revision under audit (`d525f31`), the operator model, and every in-scope threat
    other than T8's restated attacker cell. No test, control or acceptance criterion was
    weakened.
  - **Timing:** no audit lock and no report exist for this cycle, so no hash has been taken
    over revision 1. This amendment is made before the lock, which is the only point at which
    it is free; revision 1 remains in git history at `df3a4b8`.
- **Revision 3** (2026-10-10, owner-directed, this commit): five changes, each a consequence
  of a decision or a measurement made after revision 2 was published. No threat was added,
  removed, narrowed or re-graded.
  - **Section 0 — "Authorised agentic operation, and no automation" added.** Records the
    owner's standing constraint that the agentic tools acting under the owner's credentials
    must not be locked out; that the tool set sits inside the owner boundary, so "the tool
    went rogue" is a declared assumption rather than a graded finding; and that the
    repository has no scheduled or automatic build or code-update path — verified from the
    workflow triggers, not asserted.
  - **Section 0, risk residuals — corrected to the state now in force.** `main` now carries
    branch ruleset `protect-main`; tags still carry none; required reviewers remain absent by
    the owner's decision; and at `d525f31` the signing credentials were unreachable.
  - **Section 4 — the credential-wiring defect recorded**, with the evidence that the fix had
    already been written once, was lost in the rewind of `main`, and was restored after this
    survey. The section's platform-settings block now separates what was measured at
    `d525f31` from what the owner changed afterwards, and records the contribution-policy
    wording change (`247ca73`).
  - **Section 8, question 3 — narrowed to the gap still open** (tag protection), because the
    owner answered the branch and environment halves by decision rather than by question.
  - **Corrections of fact.** (a) Section 7 said the 2026-10-08/09 commits were "absent from
    the repository"; they are unreachable from every ref, but the API still serves the
    objects by SHA and one was read this cycle — the record now says exactly that. (b)
    Section 7 now names the three post-survey commits and the survey's own writes, so no
    later reader mistakes them for part of the audited revision.
  - **The read-only rule.** Every write in this cycle was owner-directed: the publication of
    revisions 1 and 2, the contribution-policy rewrite, and the credential-wiring fix. The
    surveyor did not relax the rule on its own initiative; the owner set it aside, and this
    log is the disclosure. The surveyor made no other write: no workflow dispatched, no
    branch created, no release touched, no artifact downloaded, no secret value requested.
  - **Not changed:** the three rubric grades, the five ranked assets, the two unforgivable
    acts, the revision under audit (`d525f31`), the operator model, the closed list T1–T12,
    the burden-of-proof rule, and the distribution and dependency policies of revision 2.
- **Revision 4** (2026-10-10, owner-directed, this commit): one paragraph broadened, nothing
  else changed. Section 0's "Authorised agentic operation, and no automation" now separates
  what is **verified inside the repository** (no scheduler; no non-manual trigger that
  publishes anything) from what the **owner declares about the tool estate outside it** (no
  cron job watching the codebase, third-party libraries, outside pull requests or merges; no
  agent standing by; nothing runs unless the owner is at the terminal as the commander), and
  records that the external half is not testable from this repository and needs a
  scheduled-task inventory as its artefact. No other section, threat, grade or asset changed.
- **Revision 5** (2026-10-10, owner-directed, this commit): evidence added, two statements
  corrected, nothing re-scoped and no grade touched.
  - **Section 4 — the post-fix proof run recorded** (run `38056270688`): a notarized candidate
    dispatch from `main`, all seven jobs green, the Apple credential steps and notarization
    demonstrably executed, the GPG signing step demonstrably skipped, nothing published, and
    the artifact digests GitHub computed over the uploaded bytes, with the API path a referee
    can re-read. The block states plainly what the run proves and what it does not, including
    that it ran *after* the audited revision.
  - **Section 6 corrected** — it said no workflow was dispatched. One candidate build was, after
    the survey, at the owner's direction; no artifact was downloaded or executed and no
    published byte was verified, so the exclusion stands.
  - **Section 7 corrected** — "The survey's writes" now names that dispatch alongside the
    commits, and records that it created no release or tag and changed no file.
  - **Note for the panel.** The Jobs API does not expose a job's environment field, so "no job
    entered a signing environment at `d525f31`" rests on the workflow text, not on any API
    value; the run's step outcomes, not that field, are the evidence that the credentials
    resolve.
  - **Not changed:** the revision under audit (`d525f31`), the three rubric grades, the five
    ranked assets, the threat list T1–T12, and the policies of revisions 2–4.
- **Revision 6** (2026-10-10, owner-directed, this commit): one platform control added, one
  deferred item recorded by name, one question closed. No threat re-scoped, no grade touched.
  - **Release tags are protected.** Ruleset `protect-tags` (`24841466`) now blocks tag deletion
    and non-fast-forward tag moves across `refs/tags/v*`, with **no bypass actor**. Tag
    *creation* is deliberately left unrestricted: the release job's only tag write is
    `gh release create "$tag" --target "$GITHUB_SHA"` (`build-candidate.yml:1009`) and no
    workflow anywhere deletes or moves a tag, so the control refuses a rewrite of a published
    tag without inhibiting an agentic promotion. Section 0's residual-risk paragraph and
    section 4's platform-settings list were corrected to match, replacing the earlier
    statement that tags still carried no ruleset.
  - **"Immutable releases" considered and deliberately deferred** (section 4), with the API
    probe (`{"enabled": false}`), GitHub's documented draft → attach-all-assets → publish
    requirement, and the reason for deferral: this workflow publishes in one step and uploads
    the assets afterwards, so enabling the setting as-is could break the *next real
    publication* — a failure no candidate run can detect. Named as the next-cycle improvement
    it should follow.
  - **Section 8 question 3 closed** as answered by the owner, and the owner's decision rule
    recorded in substance: adopt a control when it makes the system safer, does not inhibit
    agentic building of releases, and does not open an unbounded line of inquiry — otherwise
    defer it by name rather than half-adopt it.
  - **Not changed:** the revision under audit (`d525f31`), the three rubric grades, the five
    ranked assets, the two unforgivable acts, the threat list T1–T12, the closed list, the
    burden-of-proof rule, and the policies of revisions 2–5.
- **Revision 7** (2026-10-10, owner-directed, this commit): the audit target moved from the
  surveyed commit to the published release, and one question was closed with the owner's own
  account. No threat added or re-scoped, no grade touched.
  - **Section 1 — the target is the `v0.6.7` release** (tag `81f58ec`) and its published
    artifacts, not a branch head. The surveyed commit `d525f31` is that tag commit's
    documentation-only child; the plan records that the six differing files are all Markdown
    and that every executable file, including the release workflow, is byte-identical at the
    two revisions — so the code under audit is the same either way. The filename keeps the
    surveyed-commit name because a signed plan for the `v0.6.7` cycle already exists in this
    repository and the runbook forbids overwriting it; the lock and the report should name the
    cycle `v0.6.7` and cite this file as the plan carrying it.
  - **Section 8 question 1 closed** with the owner's account of the Oct-8/09 reset: an audit
    cycle run with several agentic tool sets that did not converge — speculative scenarios
    treated as defects, fixed without demonstration, one cycle reaching roughly a hundred
    executions — deliberately stopped and reset to a clean state at `v0.6.7`. The entry
    records what the panel should know (no release published from that line; PR #57 closed
    unmerged; no published byte altered by the reset) and that the line is out of scope.
  - **Not changed:** the three rubric grades, the five ranked assets, the two unforgivable
    acts, the threat list T1–T12, the closed list, the burden-of-proof rule, and the policies
    of revisions 2–6.
- **Revision 8 — final** (2026-10-10, owner-directed, this commit): the plan is frozen for the
  incoming review, the target statement is made internally consistent, and the four remaining
  questions are closed. No threat added, removed or re-graded; no asset, grade or acceptance
  criterion changed.
  - **Section 0 — the target-revision paragraph corrected.** It still read "`main` at
    `d525f31` — no tag", which contradicted section 1's retarget to the `v0.6.7` release and
    would have read to a referee as a scope/lock mismatch. It now names the release as the
    audit target and `d525f31` as the reconnaissance revision, with the six-Markdown-file delta
    and the filename explanation.
  - **Section 0 — the freeze paragraph added**: revision 8 is the last surveyor revision, the
    plan is a fixed input, and a later change requires an owner amendment and re-signing, which
    voids any lock already taken.
  - **Section 8 question 1 — the commissioned reviewer named** (Z.ai/GLM, the tool set whose
    earlier open-ended run over this same release is the cause of the reset), so the incoming
    review is told its own history and the closed scope is not re-opened by accident.
  - **Section 8 question 2 closed** — the stale download page was found, fixed at `fc65647` and
    verified live (v0.6.7 metadata, labels, buttons and review notices; the 63 older releases
    marked *Superseded* in their notes with every tag and asset retained), and the panel is
    told in terms that a public-site defect is a publication/hygiene matter, not a code finding
    against the release.
  - **Section 8 question 4 closed** — the referee's tripwire duty is bounded to break-and-watch
    on the release-critical controls; the ledger's remaining rows are not re-litigated;
    CT-54/CT-59 stand as deferrals expiring 2027-10-07; CT-48's vanished-commit row is recorded
    as evidence no longer retrievable, neither finding nor clearance; and an un-failable
    tripwire is an Info note unless the panel demonstrates a real regression path.
  - **Section 8 question 5 closed** — the Public Security Statement is no longer gated (the
    site now agrees with the graded revision), it is published with the report, and the
    surveyor's `not exposed by the harness` model line stands exactly as written.
  - **Section 8 question 6 closed** — no component audit exists on record and none transfers:
    the only inherited-library review is the `v0.6.2` report's embit 0.8.0 / HWI 3.2.0 /
    bundled-libusb pass, while the pinned embit is `0.8.2+besa.1`; `CURRENT-STATUS.md:113` is
    accurate; the panel identifies dependencies but does not clear them by inheritance.
  - **The surveyor's writes in this revision.** Every write was owner-directed. One
    documentation commit (`fc65647`) corrected the public site and the user manual; one
    API-only edit prepended a *Superseded* notice to the notes of the 63 historical releases
    (no tag moved, no asset added, replaced or deleted); and this revision's commit publishes
    the plan. The repository's own `scripts/check-publish-paths.sh` was also run read-only and
    returned `ok: no non-main ref carries a publish-capable workflow` (exit 0), recorded as
    clean-snapshot evidence. No workflow was dispatched, no branch created, no release
    published or altered, no artifact downloaded, and no secret value requested.
  - **Not changed:** the three rubric grades, the five ranked assets, the two unforgivable
    acts, the threat list T1–T12, the closed list, the burden-of-proof rule, and the policies
    of revisions 2–7.
- **Revision 9 — retarget to the published `v0.6.8` release** (2026-10-11, owner-directed,
  this commit): the audit target moved from the published `v0.6.7` release to the published
  `v0.6.8` release (tag `0d4e01f`, artifacts published 2026-10-10T21:31:47Z); the referee's
  bounded evidence exception moved to the cycle-4 report
  (`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`) and this cycle's ledger
  `releases/PATCH-0.6.8.md`; section 1 records that the carried survey was measured at
  `d525f31`, 37 commits and 81 files before the audited tag, and that sections 4, 7
  and 8 are therefore the cycle-4 survey record to be re-verified against the tag. Nothing
  else changed: the three rubric grades, the five ranked assets, the two unforgivable acts,
  the threat list T1–T12, the closed list, the burden-of-proof rule and the policies of
  revisions 2–8 stand as written. The sign-off lines below are left blank for the owner.
- **Provenance of every sign-off:** recorded on 2026-10-10 at the owner's direction. The
  owner supplied the signature identity and the date, directed publication, and directed each
  amendment; the surveyor agent transcribed the two lines below on every occasion, in the same
  DSH session that produced the plan
  (`DSH_SESSION_ID=session-5d5422fc-382b-428d-93f1-71eb00cd083b`). No human edited any byte of
  this file.

**Answers to the questions above.**

- **All six questions are answered, and none is carried forward open.** Questions 1 and 3 were
  answered by the owner directly: the audit target is the published release rather than a
  branch head (`v0.6.7` when the survey was taken, retargeted to `v0.6.8` for this cycle), the
  Oct-8/09 reset is explained on the record, and `main` and the release tags are now protected
  by rulesets. Questions 2, 4, 5 and 6 are answered in this revision at
  the owner's direction, each by a measurement or a fix rather than by a promise: the public
  download surface was corrected and verified live (question 2); the referee's tripwire duty is
  bounded to break-and-watch on the release-critical controls (question 4); the Public Security
  Statement is ungated and published with the report (question 5); and no component audit
  exists on record or can be inherited for the pinned stack (question 6). Nothing in section 8
  remains open, and the plan is frozen.

**Sign-off.**

- **Signed:**
- **Date:**

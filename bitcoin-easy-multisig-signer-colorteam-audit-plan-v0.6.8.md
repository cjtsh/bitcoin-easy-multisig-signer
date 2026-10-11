# Audit plan — bitcoin-easy-multisig-signer

**Cycle 5 · target release `v0.6.8` · surveyor-authored plan for the auditor to be signed by the owner**

- **Repository:** <https://github.com/cjtsh/bitcoin-easy-multisig-signer>
- **Runbook this plan was authored under:** `colorteam-surveyor.md` at framework tag `v1.5.1`
- **Definitions framework in force:** `v1.5.0`
- **Plan date:** 2026-10-11
- **Prepared by:** the Surveyor agent (section 0, Agent provenance). The owner signs section 9.

> ## Notice — the previous cycle-5 plan is WITHDRAWN and must not be used
>
> The file `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` that stood in this
> repository before this one was **withdrawn by the owner on 2026-10-11** and is **removed**
> from the working tree by the same commit that adds this file (that path is overwritten in
> place, so git shows a modification rather than a delete plus add; the withdrawn bytes are
> recoverable only from history). It must not be used, quoted, locked, or treated as the scope
> for any cycle-5 audit. It is retained only as history inside the immutable `v0.6.8` tag.
>
> Why:
>
> - That file was a prior surveyor's retarget of the signed cycle-4 plan
>   (`bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`), edited **after its own
>   declared freeze**. Its section 9 declared revision 8 final and stated that a later change
>   "requires the owner to amend this file and re-sign, which voids any lock already taken";
>   it then carried a post-freeze entry, revision 9, "retarget to the published `v0.6.8`
>   release". An edit made after a freeze on a plan that governs an audit is a scope integrity
>   failure, not a convenience.
> - It was **signed, and the signature was then removed**. Commit `1cf8880`
>   ("Sign the cycle-5 audit plan for the published v0.6.8 revision") wrote
>   `- **Signed:** Bitseeker LLC` and `- **Date:** 2026-10-10` into its section 9. Commit
>   `313cc15` erased both lines back to blanks. Section 9's later revision log then records
>   instruction that a change voids the lock. At the moment this plan was written the file
>   was post-freeze, its signature was gone, and its own instruction therefore voided it.
> - Its **Agent provenance line named a different surveyor session**
>   (`DSH_SESSION_ID=session-5d5422fc-382b-428d-93f1-71eb00cd083b`) from the session that
>   produced the signed and then unsigned states, and it carried at least one claim about the
>   target that was not true of the audited tag (see below).
> - **The owner stopped the work that was producing it.** The coding agent had gone beyond
>   the surveyor's remit and begun editing the plan itself; the owner halted it and directed
>   a clean restart. This plan is that restart.
>
> The withdrawal is done deliberately and by the owner's direction. The runbook's
> never-overwrite rule exists so that an **audit record** cannot be silently replaced by the
> party being audited; it is not a rule that a withdrawn, unsigned, post-freeze document must
> be preserved as the cycle's scope. The earlier **signed** cycle-4 plan
> (`bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`, SHA-256
> `ab5c7dbb4b89ed4f485d1e6851ddab20a5950e57bd4aae5d852667d22c5fbed8`) is **not** deleted and
> is **not** rewritten: it remains the signed scope of record for cycle 4, and this plan
> carries its scope-bearing content forward unchanged (section 9 records the carry-forward).
>
> **Everything owner-authored from that withdrawn file is carried forward into this one** —
> every owner policy, every declared asset, both unforgivable acts, the adapted rubric, the
> definition set in force, the exclusion lists, the Public Security Statement specification,
> the evidence budget, and the full T1–T12 threat table. Nothing the owner wrote is lost by
> the withdrawal. What is corrected is what was **wrong or stale about the target**: the
> audited revision's own state is described here as it is at the tag, not as a pre-fix
> snapshot of it.
>
> **Reading warning.** The `v0.6.8` tag contains the withdrawn file. The auditor must read
> its scope from **this** plan on `main`, and must treat any other file named
> `...-colorteam-audit-plan-v0.6.8.md` inside the tag as withdrawn. This plan should be
> pinned by the lock step before the panel starts; the lock should name this file by SHA-256.
>
> **What to pin.** `main` at the commit that carries this plan, for the plan document itself;
> and the tag `v0.6.8` = `0d4e01f` for the code surface. The two are reconcilable rather than
> in conflict: `git diff --name-only v0.6.8..<this commit>` contains **only Markdown and the
> two `docs/*.html` pages** — every executable byte is identical between the tag and `main`
> — so a `file:line` citation taken at the tag is valid on `main` and vice versa for every
> in-scope file. `docs/` is out of code scope (section 6) and is the only place the two
> revisions differ. If the panel prefers a single checkout, `main` at this commit is the one
> that carries the governing plan; the code it audits is the tag's code, byte for byte.

---

## 0. Locked scope

**Definitions in force:** Color Team definitions framework tag `v1.5.0`. The survey runbook
that produced this plan is `colorteam-surveyor.md` at tag **`v1.5.1`**; it states that file
is all the surveyor needs, so `COLOR-TEAM.md` itself was not fetched. Roles in force: Red,
Blue, Orange, Copper, Amber, White. This cycle carries the two framework-`v1.5` obligations
the earlier cycles did not have: a **mandatory one-page Public Security Statement** as an
audit output (specified below), and an **explicit evidence budget and stop condition** (also
below).

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

**Contribution model** (owner, 2026-10-06, carried forward and re-read this cycle from the
GitHub API): the sole collaborator is the owner (`cjtsh`, admin). The repository is public
and forkable, but no third party can push, dispatch workflows, or merge code into it —
there are no contributors and no inbound PR surface (issues are reports, not code). Push
and dispatch rights therefore rest entirely on the owner's GitHub account and are treated
as **owner account hygiene, outside the application's threat model**; the panel does not
audit GitHub account security. The workflow guards are evaluated as protection against
accidents and workflow-level abuse, not against compromise of the owner's account.
**New this cycle:** the *repository-controlled platform settings* that those guards depend
on (rulesets, branch protection, environment protection rules, token permissions) are
**in scope as configured controls**, because framework `v1.4`'s test for external
assumption is whether repository-controlled permissions make the path reachable. Their
measured state is recorded in sections 4, 5 and 7; the panel must evaluate the publish
path as it actually stands, not as the workflow's comments describe it.
**Measurement note (this cycle's surveyor):** the surveyor's GitHub token could not read
`/collaborators` (`Requires authentication`); the "sole collaborator `cjtsh`" line is
therefore **taken from the cycle-4 API read**, not re-verified this cycle, and is recorded
as such.

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

**Target revision (owner's direction).** The audited revision is the **published release
`v0.6.8`** — tag `0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`, committed
2026-10-10T17:13:08-04:00) — together with the release artifacts the repository published on
**2026-10-10T21:31:47Z**. This is the revision the audit attaches to; section 1 carries the
full statement, the artifact list and the digests.

**The reconnaissance revision this plan carries is `main` at
`d525f31b600d5aedd2f7a219ec848df540707ffc` (`d525f31`)** — **no tag** — the commit where the
cycle-4 survey of the `v0.6.7` release was taken (one documentation-only commit past the
`v0.6.7` tag; subject "Publish v0.6.7, and correct the stale claims the tree still carried").
The tree moved a long way between that survey and the audited tag: **37 commits, 81 files,
10,363 insertions and 379 deletions**, the whole CT-72…CT-95 remediation included (section 1).
Statements in sections 4, 7 or 8 that describe a state "at `d525f31`" are therefore the
**cycle-4 survey record**, not a description of the audited revision, and every one of them
must be re-verified against the tag. Where this plan cites a `file:line`, the citation is
against the **tag**; section 4 states the verification state of each site.

**Owner amendment carried into this plan — the credential wiring.** The withdrawn plan
presented the missing `environment:` keys as a live defect at the target revision. It is not
true of the audited tag: the tag's workflow **does** declare `environment: apple-signing` and
`environment: release-signing`. This plan records the defect as found at `d525f31`, and the
fix as **present at the audited revision** (section 4). The panel verifies the tag's state,
not the snapshot that contained the defect.

**Out of scope:**

- `docs/` marketing/manual website — GitHub Pages content; ships separately and shares no code with the app. **Its measured staleness was nonetheless recorded** (sections 4, 7 and 8) because asset 4's public surface is a release-channel question, not a code question; it was corrected on `main` after the `v0.6.7` release (`fc65647`) and again for `v0.6.8` (`b0a7324`), and the tagged tree still carries the text the tag itself shipped.
- `releases/` and root status/history documentation (`CURRENT-STATUS.md`, `RELEASE-HISTORY.md`, `PHASE-HANDOFF.md`, `ROADMAP.md`, `PROJECT-HISTORY.md`, `releases/PATCH-*.md`) — historical records, not executable surface; auditing the prose is not this audit's job. **Exception:** `releases/PATCH-0.6.8.md` and `releases/OWNER-ACCEPTANCE-2026-10-07.md` are evidence inputs the referee must verify claim-by-claim (see the independence condition above), not prose to be graded.
- Prior AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) — history only and not inputs to this cycle.
- Internals of pinned third-party dependencies (hwi 3.2.0, pywebview 6.2.1, pyinstaller 6.22.2, requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, upstream embit) — hash-locked; `CURRENT-STATUS.md:113` records an independent component audit of this stack as outstanding; that is a separate effort with its own plan.
- Hardware wallet firmware (Ledger, Trezor, Jade, OneKey) — external devices, not this repository.
- Live Esplora/explorer operators — external services the design already treats as untrusted observations.
- GitHub account security, and the GitHub platform itself (availability, API honesty) — external assumptions, per the contribution model.

**Not examined:**

- The commits pushed to `main` on 2026-10-08/09 and the branches that carried them — they are not reachable from any ref (section 7); they cannot be audited from the repository and are **not** part of the target revision. The same holds for the thirteen CT-48 remediation commits `releases/PATCH-0.6.7.md:61-80` cites as its branches-kept evidence: no ref holds them.
- `vendor/libusb-1.0.0.dylib` — compiled arm64 binary; provenance and hash pin documented at `vendor/README.md:36-47` but internals not reviewed.
- Vendored embit wheel internals — only the documented two-edit delta vs upstream (`vendor/README.md:10-34`); the full library was not read.
- `ui.html` (129 KB), `gui.py`, `wallet_service.py`, `probe.py`, `tests/test_workflow_config.py` — sampled at entry points, gates, and stated invariants; not read line-by-line. Full reading is the panel's job.
- Runtime behavior on a live machine, and the contents of the published release artifacts other than the one source archive named in section 1 — the survey was static; no build was run, no server started, no device attached, no workflow dispatched, and no other artifact downloaded. Every published byte whose digest is not listed as independently checked in section 1 is **unverified by this surveyor** and must be treated as a claim, not an established fact.
- The GitHub Actions run logs of the `v0.6.8` candidate and promotion runs — run metadata was read from the API (section 1); the logs themselves were not read.
- `docs/audits/*.pdf` — prior third-party AI audit reports in binary PDF form, not read.
- GitHub secret **values** — only their names were read, from the workflow and the environment list (section 4); values were never requested and are not in the repository.
- Full git history — authorship sampled only; all sampled commit identities map to the owner.

**Excluded by demonstration:** *(empty — nothing was demonstrated unreachable at survey
time. In particular, the developer-mode network gate is frontend-only and a token holder
can reach mainnet without it; that is recorded as an in-scope weakness, not excluded.)*

**Risk residuals this cycle is explicitly asked to treat as gates, not assumptions**
(owner, 2026-10-06, carried forward; **re-pointed this cycle against the audited tag**): tag
rulesets, environment protection, and least-privilege tokens are external controls the
cycle-3 plan could not verify. As they now stand: `main` carries branch ruleset
**`protect-main`** (id `24840839`, active — re-read this cycle), which blocks branch deletion
and non-fast-forward pushes with **no bypass actor**, so it applies to the owner's own tooling
as well; **tags are protected too**, by ruleset **`protect-tags`** (id `24841466`, active —
re-read this cycle), which blocks tag deletion and non-fast-forward tag moves across
`refs/tags/v*` with no bypass actor, while deliberately leaving tag **creation** unrestricted
so the release job can still create the release tag; the two signing environments carry a
`main`-only branch policy and, by the owner's explicit decision (above), **no required
reviewers**; and the workflow's `release` job holds `contents: write` on every dispatch. At
the audited tag, unlike the `d525f31` snapshot, **every job that needs credentials does enter
its signing environment** (`environment: apple-signing`, `environment: release-signing`), so
the signing credentials are reachable and a notarized build and a publication are possible.
The owner's own `v0.6.8` candidate and promotion runs demonstrate the path end-to-end
(section 1). These are recorded as residual risk and release-readiness gates, and the panel
must say what it verified itself versus what it took on the document's word.

**Mandatory audit output — one-page Public Security Statement** (framework `v1.5`): the
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
- the distribution and contribution policy as stated above, so a reader knows the release
  line is single-maintainer, signed, and built only from `main`.

It must call the process an **AI-assisted or agentic security review**, never human-firm
certification, and must make no claim of perfect security, guaranteed absence of malware,
unhackability, or outside-firm endorsement. A BLOCKED or unpublished build must never be
described as approved or safe to deploy. Tone: calm, helpful, **trust but verify**.

**Evidence budget and stop condition** (framework `v1.4`; the budget for the *panel* is the
panel's own to set under its runbook). Budget actually spent by this surveyor: the
checked-out tree at the audited tag and at `d525f31`, committed history, read-only GitHub
REST API metadata (repository settings, rulesets, environments, Actions registrations,
workflow runs, releases), and **one download** — the published source archive
`bitcoin-easy-multisig-signer-v0.6.8.tar.gz`, fetched solely to confirm the digest the
release page and `SHA256SUMS` publish. No build, no dispatch, no server, no device, no
secret value, and no repository write except the owner-directed publish of this plan
(section 9). **Stop condition reached:** the survey ended when the five declared assets, the
two unforgivable acts, the in-scope / out-of-scope / not-examined lists, the prior-finding
re-check list and the questions for the owner could each be written with a `file:line @
v0.6.8` or API-endpoint citation, and section 0 could be written out in full. Nothing
further was read to "be sure". **This plan is a fixed input:** if the review finds a genuine
scope defect it is recorded as a **scope/lock mismatch**, not silently repaired — a later
change requires the owner to amend this file and re-sign, which voids any lock already
taken. The named next-cycle list (section 5) and the deferred items (section 4) are the
correct destination for anything the review finds that is real but outside this cycle's
scope.

**Agent provenance — who ran this, and how you know.**

| | |
|---|---|
| **Surveyor — harness** | DeepSeek Harness desktop app (`com.deepseek.dsh`; `DSH_PROFILE=desktop`; `DSH_HOME=/Users/christerry/.dsh`) |
| **Surveyor — session ID** | `DSH_SESSION_ID=session-3710045d-1db5-40f4-842b-525231d94bea` — read out of the environment and copied verbatim; the session identifier is exposed by this harness |
| **Surveyor — model** | `not exposed by the harness` — the environment contains no model variable and the operator has not declared one; the surveyor did not ask itself and did not guess |
| **Declared by** | The surveyor agent running in the harness above, transcribing its own environment; operator handle: `cjtsh` |

The auditor records its own provenance in the report. The referee compares the two session
identifiers: **identical means one run did both jobs, the independence rule is broken, and
the audit is void.** Different identifiers establish different runs, not different models.

---

<!-- The owner does not sign here. Their review and sign-off is the last section of this
     file, section 9. Section 0 is the scope; the signature at the end covers the whole
     document. -->

---

## 1. Target and revision

**The audited revision is the published release `v0.6.8`:**

| | |
|---|---|
| Release tag | `v0.6.8` |
| Commit | `0d4e01f60c7695d720099f9d8e9e23b38da63102` (short `0d4e01f`), committed 2026-10-10T17:13:08-04:00, subject "Make the second candidate's tests hold on Windows and in the archive" |
| Publication | draft `false`, prerelease `false`, published **2026-10-10T21:31:47Z** |
| Publication route | the unified `build-candidate.yml` candidate→promote chain only — candidate run [38086778883] (`notarize=true`, `publish=false`, all jobs green, `CANDIDATE-MANIFEST.txt` written), then promotion run [38087360421] (`notarize=true`, `publish=true`, `candidate_run_id=38086778883`, dispatched from the same commit), recorded in `releases/PATCH-0.6.8.md` |
| Owner hardware acceptance | **not required for this release** by the owner's own recorded reasoning: `releases/PATCH-0.6.8.md` states 0.6.8 changes the build process, tests and documentation, not device identity, the signing path or broadcast policy |

**Published assets and their digests.** The ten assets the release carries, each with the
digest the GitHub release page publishes, are:

| Asset | Bytes | sha256 |
|---|---|---|
| `bitcoin-easy-multisig-signer-v0.6.8.tar.gz` | 3,613,426 | `b8e536891a4bb500c9e535771d2a19a8d2fe5e6f18d07abd8d8088c1a7b6e8e6` |
| `Bitcoin-Easy-Signer-v0.6.8-macOS.dmg` | 34,984,795 | `cb55271070bfff17dbc57797e39ee1f9a425dafa89cacdc8dec9178a498fa0d9` |
| `Bitcoin-Easy-Signer-v0.6.8-windows-x64.zip` | 35,465,286 | `725d7818d8fc26d3059a0dd4bc0d718635a4610ee94c8226f09036f5719f2dce` |
| `Bitcoin-Easy-Signer-v0.6.8-linux-x86_64.AppImage` | 68,352,504 | `7eab7271ab2dd8a5a08c6112c25fd86241cea07594a3e6e43604e18c5cf8ff0d` |
| `Bitcoin-Easy-Signer-v0.6.8-linux-x86_64.tar.gz` | 67,408,522 | `4635bebe8bfaf8bc83f553de5366aa02890005457166643aa424c27cd803be59` |
| `BUILD-SBOM.json` | 7,090 | `10bebf783af08dd468a2a85ea2b37c986e4f1ea5aa32c3a13d16542c719d35e2` |
| `BUILD-SBOM-linux-x86_64.json` | 7,159 | `ec598ebafdf1bd8d13cd660e9af768cf5e839c0c514af7570df33f000cd31dab` |
| `BUILD-SBOM-windows-x64.json` | 6,736 | `7a9a2df49444a6c4af8abd35b1853db5318045bc33d27ebd44dcb48c612eac74` |
| `SHA256SUMS` | 820 | `4ccf67e6155a1c9321ca9e396815e9c75b06fd05431ea8e531641b746cdb846e` |
| `SHA256SUMS.asc` | 833 | `857dc697a432080088d3f1c5bda89a835e5ac8082e29be0eb16ed15bb6f8d340` |

The published `SHA256SUMS` file itself was fetched this cycle and contains exactly eight
rows — the three SBOMs, the AppImage, the Linux tarball, the DMG, the Windows zip and the
source tarball — matching the release-page digests above. It does **not** cover
`SHA256SUMS` itself or the detached signature, which is expected.

**What this surveyor verified itself, and what it did not:**

- **Verified.** The tag exists and resolves to `0d4e01f`; the release metadata above was
  read live from `https://api.github.com/repos/cjtsh/bitcoin-easy-multisig-signer/releases/tags/v0.6.8`;
  the published `SHA256SUMS` was fetched and its eight rows recorded verbatim; and the
  published source archive was downloaded and hashed — its SHA-256 is exactly
  `b8e536891a4bb500c9e535771d2a19a8d2fe5e6f18d07abd8d8088c1a7b6e8e6`, matching both the
  release page and the `SHA256SUMS` row. That archive opens to a single top-level directory
  `bitcoin-easy-multisig-signer-v0.6.8/`, contains 186 entries, and **does** carry
  `signing-key.asc`, `requirements-source.lock`, `requirements-piptools.lock` and
  `releases/AUDIT-*.md` — confirming the CT-93 fix and the CT-94 documentation note against
  the published artifact itself.
- **Not verified.** The other nine assets were not downloaded and their digests were not
  recomputed; they are recorded above as the release publishes them. `SHA256SUMS.asc` was
  not signature-checked by this surveyor; `releases/PATCH-0.6.8.md` records a Good signature
  from `Bitseeker LLC <release@bitseeker.llc>` under RSA key fingerprint
  `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7`, and that record is a claim the referee should
  re-run (`gpg --verify SHA256SUMS.asc SHA256SUMS` against the committed `signing-key.asc`).
  The DMG was not stapled-checked; the publication record asserts `xcrun stapler validate`
  passed. The two Sigstore attestations on DMG digest `cb552710…` were not re-read.
- **A property worth stating plainly:** this repository's audit plans are **not** in the
  published source archive — the archive contains zero `colorteam` files. The withdrawn plan
  is in the tag, and neither is in the shipped source. A user who downloads the release does
  not receive the audit paperwork, which is a documentation-distribution observation for the
  referee, not a code finding.

**Cycle lineage — what came before, and what this plan inherits.**

| Cycle | Target | Plan of record | Outcome |
|---|---|---|---|
| 1 | `v0.6.4` = `35cdedb` | `...-plan-v0.6.4.md` | ⛔ BLOCKED (CT-01 High, CT-02, CT-04 Medium) |
| 2 | `v0.6.5` = `29c8002` | `...-plan-v0.6.5.md` | ⚠️ CONDITIONAL (0 Critical/High; CT-26, CT-27, CT-01-residual, CT-02 open) |
| 3 | `v0.6.6` = `93cf67a` | `...-plan-v0.6.6.md` | ⛔ BLOCKED by CT-48 High (retired per-platform publish workflows still dispatchable) |
| 4 | `v0.6.7` = `81f58ec` + its published artifacts | `...-plan-d525f31.md` (**signed**, revision 8 frozen, lock published pre-panel at `5742ccd`) | ⛔ BLOCKED: Red NO BREACH (12 surfaces, 19/19 re-runs held), Orange LOGIC UNPROVEN on two missing tripwires, every published byte traced to candidate run #106; grade set by ruling 4 (Blue DEFENSE BROKEN + Copper EDGE TRUST BROKEN on CT-73), plan condition (d) via CT-76, and open High CT-72 |
| 5 | `v0.6.8` = `0d4e01f` + its published artifacts (**this cycle**) | **this file** | to be determined by the panel |

**This plan supersedes a withdrawn document.** The cycle-5 target is unchanged from the
withdrawn plan — the same release, the same tag, the same artifacts. What changed is that
the plan document itself is re-authored cleanly, under framework `v1.5.1`, by a different
surveyor session, and stated against the audited tag rather than a pre-fix snapshot. The
withdrawn file is deleted; see the notice at the head of this document for the forensic
record and the reasons.

**Scope-bearing content is carried forward unchanged.** Per the runbook's follow-up-cycle
rule, this plan carries the original signed plan's scope-bearing content forward unchanged:
the declared assets and their ranking (section 2, from section 0's table), the unforgivable
acts (section 3), the adapted grade rubric and all owner policies (section 0), the in-scope
requirements including the closed T1–T12 list (section 5), the exclusions (section 6), and
the not-examined list (section 7). Only target-revision and cycle-lineage information has
been updated, together with the two framework-`v1.5` additions, and corrections where a
citation described the `d525f31` snapshot rather than the tag.

**Reconnaissance vs. audited revision.**

- **Reconnaissance revision:** `main` at `d525f31b600d5aedd2f7a219ec848df540707ffc` — the
  cycle-4 survey point, one documentation-only commit past the `v0.6.7` tag.
- **Audited revision:** tag `v0.6.8` = `0d4e01f`, published 2026-10-10T21:31:47Z.
- **The delta:** `git rev-list --count d525f31..0d4e01f` = **37** commits;
  `git diff --stat d525f31 0d4e01f` = 81 files changed, 10,363 insertions, 379 deletions. It
  contains executable surface — `gui.py`, `wallet_service.py`, `safe_http.py`,
  `network_settings.py`, `probe.py`, `Start Easy Multisig.command`, the build scripts and all
  three workflows — and new controls (`CONTROLS.md`, `scripts/scan-secrets.py`,
  `scripts/check-platform-state.sh`, `releases/platform-state.json`,
  `tests/test_publish_guards.py`, `tests/test_secret_scan.py`,
  `tests/test_platform_state.py`), i.e. the whole CT-72…CT-95 remediation. This is why a
  statement about `d525f31` cannot be read as a statement about the audited revision.
- **The delta after the tag:** `main` is now `313cc15`. `git diff --name-only v0.6.8..HEAD`
  is 8 files — `CURRENT-STATUS.md`, `PHASE-HANDOFF.md`, `RELEASE-HISTORY.md`, `ROADMAP.md`,
  the withdrawn plan, `docs/index.html`, `docs/user-manual.html` and
  `releases/PATCH-0.6.8.md`. **Every executable byte is identical between the tag and
  `main`**: the only non-Markdown files in that list are the two `docs/*.html` pages, and
  they are out of code scope (section 6). This is why the panel may read code from either,
  but must cite the **tag**; the `docs/` pages differ and the difference matters only to
  section 8's download-surface record.

**Prior finding IDs the next auditor must re-check, with the evidence to use.** The
cycle-4 report `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` carries
**64 distinct finding IDs**; they are not a contiguous block — the report discusses only
CT-01, 02, 12, 13, 15, 16, 17, 21–26, 34–36, 42–63 and 70–95. Every one of them is listed
here with what the auditor must do to verify its disposition. The remediation ledger
`releases/PATCH-0.6.8.md` (one row per scheduled finding, each naming its fix and its
closing tests) and the signed acceptance note `releases/OWNER-ACCEPTANCE-2026-10-07.md` are
the referee's inputs for this section (section 0, independence condition); the specialist
lanes must not read them.

*Cycle-4 findings scheduled for remediation in `v0.6.8` (verify the fix, then break the test
that claims to pin it):*

| ID | Severity at cycle 4 | What to re-check |
|---|---|---|
| CT-49 | Low | second-publish-path root cause; the frozen-mode half verified at cycle 4, and the tag-blind sweep half is CT-76's fix |
| CT-54 | Low | deferred; rebuild `vendor/libusb-1.0.0.dylib` from pinned source at the next dependency bump — **expiry 2027-10-07** |
| CT-56 | Info | as scheduled by the ledger; confirm the fix still stands at the tag |
| CT-58 | Info | as scheduled by the ledger; confirm the fix still stands at the tag |
| CT-59 | Low | closed by the CT-84 fix; confirm the deadline/`read_bounded` code is present and its test can fail |
| CT-72 | **High** | `candidate_run_id` command injection — confirm `CANDIDATE_RUN_ID: ${{ inputs.candidate_run_id }}` is routed through `env:` and read as `$CANDIDATE_RUN_ID`, and try to defeat the numeric guard |
| CT-73 | Medium | HWI whole-payload pin — confirm `vendor/hwi-payload-3.2.0.json` exists and that `_verify_hwi_payload` refuses a missing, added or changed file |
| CT-74 | Medium | publish guards that could not fail — confirm `tests/workflow_harness.py` and `ReleaseGuardBehaviourTests` actually make them fail |
| CT-75 | Medium | four more string-pinned publish guards — same break-and-watch duty |
| CT-76 | Medium | publish-path sweep tag blindness — confirm it fetches `+refs/tags/*` and applies an allowlist |
| CT-77 | Medium | matcher blindness (`write-all`, `gh api …/releases`, `curl`, `action-gh-release`) — confirm the allowlist matchers refuse each |
| CT-78 | Medium | mainnet genesis literal pinning — confirm the four chain constants are asserted and the network→genesis mapping is exclusive |
| CT-79 | Medium | bare-`/*` change-inference ban — confirm the named pinning test exists and goes red if the guard is removed |
| CT-80 | Medium | missing signing environments — **present at the tag** (see section 4); confirm the platform-state check and its test |
| CT-81 | Low | non-ASCII `X-Local-Token` handling — confirm the UTF-8-before-compare fix and a near-miss case |
| CT-82 | Low | the token-gate pin's missing near-miss case |
| CT-83 | Low | `release` job holding `contents: write` on candidate dispatches — confirm the grant split |
| CT-84 | Low | no total deadline on outbound HTTP — confirm `class Deadline`, `read_bounded`, `open_url`, and the broadcast submit outside the session lock |
| CT-85 | Low | no per-connection timeout — confirm `CONNECTION_TIMEOUT_SECONDS = 15.0` and the desktop server's timeout |
| CT-86 | Low | no automated secret-value scan — confirm `scripts/scan-secrets.py` runs on the extracted archive and the pinned `detect-secrets` |
| CT-87 | Low | unpinned Linux build toolchain — confirm what the ledger claims and what the container proof covers |
| CT-88 | Info | vendored embit archive digests prose-only — confirm the machine check |
| CT-89 | Info | unreachable change-descriptor key-match check — confirm it was deleted or made reachable |
| CT-90 | Info | practice-network secondary explorer left unset — **dated deferral**, record with its date |
| CT-91 | Info | vendored embit `liquid/pset.py` sequence coercion — confirm the fix in place |
| CT-92 | Info | launcher installing embit only — confirm the source-mode device support fix |
| CT-93 | Info | `signing-key.asc` missing from the source archive — **verified present this cycle** in the published archive; confirm at the tag |
| CT-94 | Info | attestation REST endpoint documentation note — confirm the documentation change |
| CT-95 | Info | the un-failable `HWI_PAYLOAD_PINS` re-assertion, folded into CT-73 at `37ae9fb` — confirm the folded fix and whether the tripwire can now fail |

*Cycle-4 findings whose disposition is verified-fixed-and-standing, not reopened at
`v0.6.7` (re-confirm they were not regressed by the CT-72…CT-95 changes):* CT-02, CT-03,
CT-04, CT-05, CT-06, CT-07, CT-08, CT-09, CT-10, CT-11, CT-12, CT-13, CT-14, CT-15, CT-17,
CT-18, CT-19, CT-20, CT-21, CT-24, CT-26, CT-27, CT-28, CT-29, CT-30, CT-31, CT-32, CT-33,
CT-34, CT-43, CT-45, CT-46, CT-50, CT-51, CT-53, CT-55, CT-57, CT-60, CT-62, CT-71.

*Cycle-4 findings partially fixed and explicitly carried forward:* CT-01 (second-publish-path
root cause; its tag/matcher residual became CT-76/CT-77), CT-48 (its evidence cites thirteen
branch commits that are unreachable objects today — "evidence no longer retrievable";
neither finding nor clearance; the sweep is now tag-aware via CT-76), CT-49 (frozen-mode half
verified; source-mode half became CT-73), CT-52 (string-pins only under logic defeat → CT-74).

*Cycle-4 findings closed as observation, decomposition or no-recurrence:* CT-16, CT-22,
CT-23, CT-25.

*Cycle-4 findings closed by the signed owner acceptance of 2026-10-07:* CT-35 (its Host-only
price/fees property recurred unchanged and is recorded under it), CT-36, CT-37, CT-38,
CT-39, CT-40, CT-41, CT-42, CT-44, CT-47, CT-61, CT-63, CT-64, CT-65, CT-66, CT-67, CT-68,
CT-69, CT-70. The acceptance note is the record; do not re-litigate it (section 8, question
4), but confirm nothing in `v0.6.8` contradicts what the note says it accepts.

**Two things the panel should not be surprised by, stated once here.** First, the CT-ID
space is not dense: the cycle-4 report leaves 25 slots between CT-01 and CT-48 undiscussed,
so "missing" IDs are not findings. Second, the repository's own ledger
`releases/PATCH-0.6.8.md` had two candidates precede the published one and records their
defects; the panel should read that record as claims to verify, not as a clean bill.

---

## 2. The declared assets (ranked)

Carried forward unchanged from the original signed plan. **No asset is optional** (owner,
2026-10-06): the ranking orders severity, not attention; all five are mission-critical.

1. **The Bitcoin in the operator's multisig wallet** (mainnet and practice-network funds) —
   the money itself, and the transaction the operator believes they approved.
2. **Signing and CI credentials and the release workflow itself** — the Developer ID
   certificate, the Apple notary key, the GPG release key and the GitHub token, plus the
   workflow that uses them. The owner's own words: *"loss of credentials is the same thing as
   loss of funds."*
3. **The reviewed-transaction integrity chain** — the frozen `PreparedPayment`, the PSBT sent
   to signers, the verified signer responses, and the final transaction. Bytes that differ
   from what was reviewed must never reach a signer or an explorer.
4. **Release artifact integrity** — the published DMG, the platform bundles,
   `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM.
5. **Wallet privacy** — xpubs, addresses, BSMS contents, txids and device identities.

Ranking note (owner, 2026-10-06, carried forward): all five assets are mission-critical.
Funds rank first, and credentials rank second because the owner equates their loss with loss
of funds. Ranks 3–5 are all direct paths to, or protections of, the funds and the owner's
identity — privacy is ranked fifth because a leak does not move funds by itself, **not**
because it is optional. A stuck or blocked payment remains recoverable and sits below every
asset on this table.

The full "what must not happen to each" table is section 0's declared-assets table and
governs this list.

---

## 3. The unforgivable acts (in plain words)

Carried forward unchanged from the original signed plan:

1. The app gets the owner to sign and broadcast a transaction that sends their real Bitcoin
   somewhere they did not approve — a thief's address, a wrong amount, or change quietly
   redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the app
   leaks the wallet's addresses and xpubs so strangers can watch and target the family's
   savings.

A demonstrated path to either act is an automatic ⛔ BLOCKED under section 0's rubric.

---

## 4. Where the assets live

**Every `file:line` below was re-verified this cycle against the audited tag** with
`git show v0.6.8:<path>`, item by item: **37 of the 60 sites checked landed on the claimed
code (HIT)**, **23 had moved by 3–77 lines** and are cited here at their **tag** lines (the
`d525f31` figure is given in parentheses where it differed), and a small number of claims
from the prior survey turned out to be **wrong about the tag** and are corrected below — most
importantly `desktop.py:316` never carried a per-connection timeout (it is `gui.py:535`), and
`safe_http.py` has a single `open_url` at `:259` (the `:143` figure of the prior survey was
never it). The withdrawn plan cited the **pre-fix `d525f31` lines throughout**, which the
CT-72…CT-95 remediation shifted; that is why its section 4 pointed at the wrong places. No
claim in this section should be read as "the panel need not check this" — the panel must
re-confirm every site it relies on.

### Assets 1 & 3 — the funds and the reviewed-transaction chain

- Frozen prepared-payment record: `gui.py:276` (`class PreparedPayment`; was `:262` at
  `d525f31`), field `gui.py:288` (`review_id`; was `:274`), factory `gui.py:295` (`create`;
  was `:281`), created for the operator at `gui.py:1323` with `secrets.token_urlsafe(18)`
  (the nonce at `gui.py:632` is the unrelated CSP nonce; both re-verified at the tag).
- Re-parse and drift refusal: `gui.py:304` (`checked_psbt`; was `:290`, raising at `:308`
  "The prepared transaction changed. Review it again."), and the binding test
  `_current_prepared` `gui.py:926` (was `:869`; identity, chain, scan generation,
  `preparation_id == review_id`).
- Final-screen binding: `_check_final_review` `gui.py:1030-1043` (was `:973-986`) compares
  output count, txid, fee, recipient value+address and change value+address against the
  frozen record.
- Signature acceptance: `signing.py:156` (`accept_signature_update` — equal input/output
  counts, identical `tx` serialization, no removed or changed prior signature, clones the
  **reviewed** PSBT and copies only `partial_sigs`, then re-verifies); completeness and
  finalization `signing.py:258` (`finalize_multisig`; the `len(ordered) < threshold` raise is
  at `:277-279`), txid re-checked.
- PSBT construction and independent observation: `wallet_service.py:748`
  (`build_unsigned_psbt`; was `:731`); previous-transaction cross-check against the utxo's
  txid/value/script at `wallet_service.py:867-870` (was `:850-853`); independent-outpoint
  check `wallet_service.py:190` (`check_selected_outpoints`, independent-source message at
  `:201`; was `:181`); gap-limited scan `wallet_service.py:515` (`scan_wallet`; was `:498`)
  with the gap gate at `:543`, `GAP_LIMIT=20` at `:41` (was `:36`) and `MAX_INDEX=100` at
  `:42` (was `:37`).
- Change-policy trust boundary: BSMS-declared vs standard-derived change —
  `probe.py:120-154` (HIT for the change-declaration handling), `wallet_service.py:374`
  (`_conventional_change`; was `:357`); the bare-`/*` flag/comment is at
  `wallet_service.py:307-318` (HIT) with its enforcement gate at `:327-328`, and the
  nonstandard-change fail-closed branch moved from `:321-326` to `:338-340`. Governed by
  `CHANGE-ADDRESS-REVIEW.md`.
- Broadcast gate: `gui.py:1051-1054` (mainnet requires the per-transaction opt-in; was
  `:994-997`) and the library's own fail-closed default `wallet_service.py:70-82`
  (`mainnet_opt_in: bool = False` at `:77`, "Explicit mainnet broadcast confirmation is
  required."); submit under the session lock at `gui.py:1093-1102` (was `:1027-1035`).

### Asset 5 — privacy

- Diagnostic discipline: fixed diagnostic vocabulary at `gui.py:71-96` (was spread through
  the old `:414-448` block), the 80-event trim at `gui.py:526` (`save_diagnostic_report` at
  `:428`), and device *class* only; token scrub (`_clean_token`, drop rather than escape) at
  `gui.py:402` (was `:341`).
- Session token: `secrets.token_urlsafe(32)` `gui.py:467` (was `:453`), delivered only in the
  launch URL fragment `gui.py:99-109` (fragment literal at `:109`; was `:91-101`), checked per
  request at `gui.py:685-687` via `_token_matches` (the inline compare is `gui.py:604-621`;
  the old `:634-643` figure was the pre-fix site), and never logged (`log_message` no-op
  `gui.py:537-539`; was `:518-520`).
- "Never send xpubs" to explorers: `wallet_service.py:133`; the diagnostics filename literal
  is `gui.py:442` with the route at `gui.py:739` (was `:682`) —
  `~/Downloads/bitcoin-easy-signer-diagnostics-{APP_VERSION}.json`.
- No committed wallet material: `.gitignore` covers `*.bsms`, `*.psbt`, `*.txn`, `*.log`; a
  regex sweep of the tree found no private key or provider token.

### Assets 2 & 4 — credentials and the release chain

- The single publish path: `.github/workflows/build-candidate.yml` — `on:
  workflow_dispatch:` only (`:23-24`), inputs `notarize` (default `false`), `publish`
  (default `false`) and `candidate_run_id` (`:34`). No `push`, `pull_request`,
  `pull_request_target`, `release` or `tag` trigger exists anywhere in the repository.
- Publish guards inside that workflow: publish requires notarize (`:57-61`, HIT), ref
  `refs/heads/main` (`:72`; was `:65`), a numeric candidate run id (`:76`; was `:69`), a
  candidate run that succeeded on the same commit through this same file (`:794-804`; was
  `:710`), a manifest asserting `notarize=true, publish=false` (`:825-826`, write at
  `:949-955`; was `:733-739`), `shasum -a 256 -c SHA256SUMS` (`:834`, `:935`, `:998`; was
  `:746-754`), an unsigned/unnotarized refusal (`:1101-1104`; was `:979`), and a tag-exists
  no-overwrite guard (`:1109-1119`; was `:986-996`) before `gh release create` (`:1120`; was
  `:997`/`:1009-1011`).
- Branch sweep control: `scripts/check-publish-paths.sh`, invoked on every dispatch
  (`build-candidate.yml:53`; was `:56`); at the tag it enumerates the **remote's** heads
  (`:240`) **and tags** (`:251`) and fails closed on a retired workflow filename, an
  unreadable blob, a write-permission grant outside the allowlist, or a release-publishing
  surface outside the allowlist (the CT-76/CT-77 fix; `+refs/tags/*` refspec at `:132`,
  `LEGACY_UNGUARDED_TAGS` allowlist at `:96`, matchers `CONTENT_WRITE_RE` `:104`,
  `WRITE_ALL_RE` `:106`, `RELEASE_SURFACE_RE` `:111`).
- Secret **names** (values are not in the repository and were not requested):
  `MAC_CERT_P12_BASE64`, `MAC_CERT_PASSWORD`, `MAC_APP_SPECIFIC_PASSWORD`,
  `MAC_NOTARY_KEY_P8_BASE64`, `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`; environment groups
  `apple-signing` (the three `MAC_*` signing secrets) and `release-signing` (both GPG
  secrets), each with a branch policy of `main` only.
- **Credential wiring — the defect was real at `d525f31`, and the fix is present at the
  audited tag.** At `d525f31` the workflow named those six secrets but declared **no
  `environment:` key on any job** (`grep -c 'environment:' …` → `0`; the same was true of
  the cycle-4 run revision `81f58ec`). Because a job receives environment-scoped secrets only
  if it names the environment, and the repository-level secret list is empty, a notarized
  build or a publish would have failed closed. The discarded 2026-10-08 revision `1a5e9bf`
  had the wiring (`environment: apple-signing` at its line 162, `environment: release-signing`
  at its line 719, under commit `2f779e2` "Record the revision that carries credential
  recovery (CT-97)"); the rewind of `main` dropped it, and the owner restored it at `333b361`
  before the release. **At the audited tag the keys are present:**
  `git show v0.6.8:.github/workflows/build-candidate.yml` has `environment: apple-signing`
  at line **189** and `environment: release-signing` at line **775**, with
  `CANDIDATE_RUN_ID: ${{ inputs.candidate_run_id }}` at line **70** (comment at `:67`, guard
  at `:76`) and again at `:789` **(re-verified at the tag)**. The withdrawn plan described
  this as a live blocker at the target; it was not true of the tag, and this plan corrects
  it. The panel must still verify the tag's own state, and must **not** try to read a job's
  environment from the Jobs API — the field is absent from that response entirely; the
  workflow text is the only place it is visible.
- **The path was also proved by real builds.** Framework principle: reading can show that a
  job names the environment, but not that the stored values arrive — a wrong password, an
  expired certificate and a secret filed in the wrong store all look identical from outside.
  Two dispatches settle it, and both are part of the publication record:

  | Run | Purpose | Facts |
  |---|---|---|
  | `38056270688` | the post-rewind credential proof (owner-directed, `notarize=true`, `publish=false`, dispatched from `main` at `05ae6ae`) | `completed`/`success`, all seven jobs green; `Import the Developer ID certificate`, `Provide notary credentials`, `Build the DMG` and `Verify the DMG, the signature and the bundled app` all **success**; the "must fail closed without credentials" guard passed; `Sign the checksum manifest with the release key` **skipped** while `Attest build provenance for every asset` succeeded, proving `publish=false` was honoured; nothing published |
  | `38086778883` → `38087360421` | the v0.6.8 candidate and promotion | candidate `notarize=true publish=false` all green; promotion dispatched from the same commit `0d4e01f` with `candidate_run_id=38086778883`, `publish=true`, all green — this is the run that created the release in section 1 |

  The credential proof's artifact digests, as GitHub computed them over the exact uploaded
  bytes (re-readable at `.../actions/runs/38056270688/artifacts`):

  | Artifact | Bytes | sha256 |
  |---|---|---|
  | `macos-dmg` | 33,743,651 | `6c0a0589edd6bc65dd37c1860f8150f0edefa6898bcc8742219efb81ca103087` |
  | `windows-bundle` | 35,402,302 | `28ec47abb5fc91db6498e4124e9b99304c93b6531c9959af4d0c16aec12d1c61` |
  | `linux-desktop` | 134,966,290 | `3e2bd459ca71ad53cba63a12a2455b5262c9579717724750c97619f80345e0d7` |
  | `source-archive` | 3,450,507 | `085bacc0ef95719c4c7cc89827b56d8e22a30f4d189e9bdbcaaf703dc12ff3f6` |
  | `release-assets` | 207,563,242 | `e88c498c518a369bacf71a287f650ea56b5c84490538df74ac09ce182580c924` |
  | `sha256sums` | 580 | `d473b23f06a5856afaa9ef22e6cb52d315a73a89ad5c6e8e1653d252d9658d7a` |
  | `candidate-manifest` | 254 | `c8a79a40b71e35c649deeac21105e81ba877fc1c4efc0867b1f3f559548add9c` |

  What the proof establishes: the Apple signing certificate and the notary credentials are
  reachable by a dispatched build from `main`; signing, notarization and verification
  complete; the provenance attestation is emitted; and no human approval sits anywhere in the
  path. What it does **not** establish: the GPG half, because the release-key step was
  skipped by design — the release key stays unexercised until a real publication, and the
  v0.6.8 promotion run is the publication that exercised it (the panel should read that
  run's record rather than take this row's word).
- Release key: committed public `signing-key.asc` = `rsa4096`, fingerprint `ACCC 2F1C D436
  9128 D549 CC58 E972 85D2 DD0B D6D7`, uid `Bitseeker LLC <release@bitseeker.llc>`; the
  private half lives only in the `release-signing` environment secret and is bound to that
  public key by the `gpg --verify` step at `build-candidate.yml:1004-1005` (also `:898`; was
  `:850-851`).
- Attestation: `actions/attest-build-provenance` (`:813`) with `id-token: write` and
  `attestations: write` (`:693-694`).
- Vendored, hash-pinned inputs: `vendor/` (patched embit wheel, libusb dylib/dll, Linux
  libusb tarball, AppImage runtime) with digests asserted in the build recipes; hash-locked
  dependency sets `requirements*.lock`, installed with `--require-hashes`.

### Entry points (how data or a user gets in)

- Loopback HTTP API: `desktop.py:316` builds the `ThreadingHTTPServer(("127.0.0.1", 0), …)`
  with the ephemeral, token-gated port; the **per-connection timeout** lives in `gui.py:535`
  (`CONNECTION_TIMEOUT_SECONDS = 15.0` is `gui.py:61`) — the withdrawn plan placed it in
  `desktop.py`, which has no such timeout.
- Desktop wrapper: `desktop.py:50` (`DesktopBridge`), window creation `desktop.py:323`, PSBT
  save bridge `desktop.py:84-103` (pins the prepared base64).
- Operator-supplied BSMS file: `probe.py:81` (`load_bsms`), `probe.py:93` (`parse_bsms`,
  64 KiB cap at `:25`).
- Hardware signers over USB: HWI 3.2.0 via `scripts/hwi_entry.py`, the payload pin
  `HWI_PAYLOAD_PINS` at `probe.py:211-214` (HIT) and `_verify_hwi_payload` at `probe.py:418`
  (HIT), the identity check `_verify_hwi_identity` at `probe.py:494` (was `:391-428`), and
  the key-possession challenge `prove_signer_holds_key` at `probe.py:723-758` (was
  `:620-655`).
- Outbound network: Esplora scans/broadcasts and fee/price references through `safe_http.py`
  (`open_url` `:259` — there is only one; TLS context `:102-114`, redirects refused `:43-68`);
  explorer base URLs `network_config.py:30,38,46`, mainnet secondary `blockstream.info`
  `:57`.
- Operator-configured explorer URLs persisted at `network_settings.py:25-38`, validated
  `:48-68`, network-verified against genesis/checkpoint `:118-145`, written `0o600` +
  atomic replace.

### Data stores

`~/Library/Application Support/Easy Bitcoin Multisig/settings.json` (macOS; `%APPDATA%` on
Windows, XDG on POSIX) — server URLs only, docstring "Never store wallet data", dir `0700`/
file `0600`; in-memory session state `gui.py:451-482`; the privacy-limited diagnostic
buffer; the diagnostics JSON and saved PSBTs in `~/Downloads` (`gui.py:328-385`). No wallet
material is persisted by design.

### Repository-controlled platform settings (re-read this cycle, read-only, via the API)

- `main` carries branch ruleset **`protect-main`** (id `24840839`, `active`): branch deletion
  and non-fast-forward pushes are blocked, with **no bypass actor**, so it binds the owner's
  own tooling too. Ordinary pushes are unaffected. There is no classic branch protection
  (rulesets are a separate mechanism).
- Tags carry ruleset **`protect-tags`** (id `24841466`, `active`): tag deletion and
  non-fast-forward tag moves are blocked across `refs/tags/v*`, with **no bypass actor** —
  the rule AGENTS.md states in prose ("moving or deleting a published tag is forbidden") is
  enforced by the platform. Tag **creation is deliberately not restricted**: the ruleset
  omits the `creation` rule, because the release job's only tag write is
  `gh release create "$tag" --target "$GITHUB_SHA"`, and no workflow deletes or moves a tag.
  Recovery cost, stated plainly: with no bypass actor, withdrawing a tag that a failed
  publication left behind requires an admin to change the ruleset first — accepted by the
  owner for the same reason as `protect-main`.
- **Considered and deliberately deferred: GitHub "immutable releases".** The setting exists
  and is off (`GET /repos/…/immutable-releases` → `{"enabled": false}`, read at the
  `d525f31` survey and to be re-read at the tag by the panel). It would lock a published release's assets and tag and emit a signed release
  attestation binding tag, commit and assets — all desirable. It is *not* enabled yet because
  GitHub's own guidance is to create the release as a **draft**, attach every asset, then
  publish, and this workflow does the opposite: `gh release create … dist/*`
  (`build-candidate.yml:1009-1011`) publishes first and uploads the assets afterwards, which
  is exactly the pattern immutability is documented to obstruct. Enabling it as-is would risk
  breaking the next real publication — a failure no candidate run can detect. It is recorded
  as a named next-cycle improvement: change the release job to draft → upload → publish, test
  that path with a real publication, and only then enable immutability.
- Environments `apple-signing` and `release-signing` each carry a branch policy of `main` and
  `can_admins_bypass: true`, with **no required reviewers** — an owner decision (section 0),
  because a human gate would sit in front of the agentic tooling the owner directs.
  `github-pages` allows `gh-pages` and `main`.
- Actions: `allowed_actions: "all"`, `sha_pinning_required: false` (owner decision: do not
  lock out authorised tooling); default workflow token `read`; `secret_scanning` and
  `secret_scanning_push_protection` enabled; `dependabot_security_updates` and validity
  checks disabled. Sole collaborator `cjtsh` (admin) — **taken from the cycle-4 API read,
  not re-verified this cycle, because this surveyor's token could not read
  `/collaborators`**. All 57 pull requests were opened from a branch of this repository; no
  fork PR has ever existed. No deploy keys, no webhooks, no repository-level secrets; the
  authorized OAuth/GitHub Apps list could not be enumerated by this surveyor's token, so the
  owner must read it from Settings → Applications.
- The workflow registrations `build-windows.yml` and `build-linux.yml` still exist with
  state `disabled_manually` although their files are absent from every ref.
- The repository's own text: `CONTRIBUTING.md` and `README.md:95` were reworded after the
  cycle-4 survey (commit `247ca73`) to match the single-maintainer policy, and those edits
  are **in the audited tag**. At the reconnaissance revision `d525f31` both still invited
  outside pull requests; at the tag they do not.

### The target revision's own publication record

`releases/PATCH-0.6.8.md` records the publication in full: two candidate attempts preceded
the published one and their defects are recorded; the published candidate is run
[38086778883] and the promotion is run [38087360421]; ten public assets; an 8/8
`shasum -a 256 -c SHA256SUMS` check; a Good `SHA256SUMS.asc` signature from `Bitseeker LLC
<release@bitseeker.llc>` under key `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7`; a working
`xcrun stapler validate` on the DMG; two Sigstore attestations on DMG digest
`cb552710…`; `draft=false`, `prerelease=false`; and no tag or asset moved, replaced or
deleted. **Every sentence in that paragraph is the repository's claim, reproduced here as a
claim.** This surveyor independently confirmed only the tag, the release metadata, the
published `SHA256SUMS` rows and the source archive's digest (section 1).

---

## 5. In scope

Carried forward from the original signed plan, with the target-revision references updated
to `v0.6.8`:

- All first-party application code at the audited tag `v0.6.8`: `probe.py`,
  `wallet_service.py`, `signing.py`, `gui.py`, `desktop.py`, `network_config.py`,
  `network_settings.py`, `safe_http.py`, `version.py`.
- The entire interface and its gates: `ui.html` (review screens, per-transaction mainnet
  consent, developer-mode/network gate, pending-payment banner, busy/progress ownership,
  large-amount floors, palette invariants).
- The HWI integration boundary: `scripts/hwi_entry.py` and the HWI timeout/retry rules
  stated in `AGENTS.md`.
- Build and release pipeline: `.github/workflows/build-candidate.yml`,
  `.github/workflows/linux-inputs.yml`, `.github/workflows/windows-inputs.yml`,
  `scripts/build-macos.sh`, `scripts/build-linux.sh`, `scripts/build-windows.ps1`,
  `scripts/build-sbom.py`, `scripts/build-source.sh`, `scripts/notary-args.sh`,
  `scripts/build-hwi-manifest.py`, `scripts/verify-windows-bundle.py`,
  `scripts/check-publish-paths.sh`, `scripts/check-platform-state.sh`,
  `scripts/scan-secrets.py`.
- **Repository-controlled platform settings as controls:** the rulesets `protect-main` and
  `protect-tags`, the environment protection rules, the default token permission, and the
  lingering `disabled_manually` workflow registrations — evaluated as they are, not as the
  comments describe them.
- Dependency pinning as a control: `requirements*.txt`/`*.lock` hash pins and the documented
  `vendor/` delta. The pins and the delta are in scope; the pinned code's internals are not.
- **Invariants with no machine pin, which must be tested rather than cited:** no test asserts
  that the app refuses seed phrases, private keys or PINs; no test asserts that only a
  single BSMS file is accepted; no test binds `AGENTS.md`'s declared version string to
  `version.py`. These three are the invariants closest to the owner's own safety vocabulary.
- **The evidence ceiling of the suite, which the panel must not exceed in its claims:** the
  suite is large — this cycle measured **34** `tests/test_*.py` modules, **640** test
  functions across **120** classes, plus **10** self-contained `node` `.cjs` UI tests — and
  CI fails closed on any skip (`build-candidate.yml:103-115`; `tests/` contains exactly three
  skip sites and no `xfail`). But the **device layer and every outbound network call are
  exercised only against mocks** — no hardware signer is ever attached and no live explorer
  is ever contacted (`tests/test_probe.py`, `tests/test_hardening_pins.py`,
  `tests/test_desktop.py`, `tests/test_wallet_service.py`, `tests/test_gui.py:51`,
  `tests/test_send_flow.py`). HWI helper byte-identity, the fresh device key-proof before a
  PSBT is sent, and the device→finalize→broadcast journey therefore have **no live exercised
  evidence** — only logic coverage over stubs. That is a stated coverage limit, not a
  control, and the panel must say which of its conclusions rest on it.
  *(Correction note: the withdrawn plan stated "489 Python test methods across 27 modules".
  That figure does not match the audited tag; the AST census above does. The panel should
  re-measure rather than inherit either number.)*
- **The suite cannot be run in this survey environment, and the plan says so rather than
  implying otherwise.** The repository pins Python **3.12.10** everywhere
  (`build-candidate.yml:102`, `:200`, `:433`, `:588`; `windows-inputs.yml:54`;
  `linux-inputs.yml:51`) with no bare `3.12`; the survey machine has Python 3.14.4, no
  `pytest` and no `embit`. The panel must run the suite in the pinned environment before
  claiming its coverage.
- **Vendored provenance gap:** the two embit source archives
  (`vendor/embit-0.8.2+besa.1.tar.gz` and `vendor/embit-upstream-2b375a.tar.gz`) are the
  stated provenance evidence for the hash-locked wheel; the panel should verify that every
  `vendor/` input's digest is machine-asserted in code and report any that is not.
- `tests/` as evidence: the panel must check that every control the repository claims is
  actually pinned by a test that can fail. `AGENTS.md` names some; the panel must also test
  the claims made by name in `releases/PATCH-0.6.8.md` and `CONTROLS.md` (17 controls
  CM-01…CM-17, whose inventory test `tests/test_controls_inventory.py` fails the build when a
  cited file/line/test/marker stops agreeing).
- `releases/PATCH-0.6.8.md` and `releases/OWNER-ACCEPTANCE-2026-10-07.md` as the
  claimed-fix ledger: every row's "closing evidence" is a claim to be broken, not a
  citation to be trusted. This cycle's ledger carries CT-49, CT-54, CT-56, CT-58, CT-59 and
  CT-72 through CT-95; its dated deferrals are CT-90 (the practice-network secondary explorer
  left unset at `network_config.py:57-58`) and CT-54, the latter with a hard expiry of
  2027-10-07 (CT-59 was closed by the CT-84 fix and is listed with it). Any row the ledger
  closes by a dated owner acceptance note must be confirmed against what that note says it is.
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
`file:line @ v0.6.8`. A concern that cannot be demonstrated is recorded as a **note**, is
never graded, and does not by itself change the grade. Severity cannot inflate a note: a
weakened control with a reproducer is CONDITIONAL; hygiene or robustness without a
demonstrated path is an Info item; a speculation is a speculation. This cuts both ways —
every one of T1–T12 must still be *tested* with evidence of that kind, and an untested
threat cannot be cleared by argument.

**The threat rows below cite the audited tag wherever this cycle's surveyor re-verified a
site, and name the reconnaissance revision `d525f31` wherever a figure comes from the
cycle-4 survey record and must be re-confirmed at the tag.** The CT-72…CT-95 remediation
changed many of them; section 4 and
`releases/PATCH-0.6.8.md` name which. This cycle's surveyor re-verified 60 `file:line` sites
against the tag: 37 landed exactly, 20 had moved (section 4 cites the tag line and gives the
old figure in parentheses), and 3 claims from the withdrawn plan were wrong about the tag and
are corrected here (`desktop.py:316` per-connection timeout → `gui.py:535`; `safe_http.py`
`open_url` `:143` → `:259`; `tests/test_hardening_pins.py:331` → `:375-376`).

| # | Asset + plausible attacker starting capability | Repository-controlled entry point / trust boundary | Concrete prohibited outcome | Observable acceptance test or evidence | Exclusions and assumptions | What result would block release |
|---|---|---|---|---|---|---|
| T1 | Asset 1/3 — the app itself is the attacker's surface; no prior access required beyond the operator using it | Review → prepare → sign → finalize → broadcast pipeline in `gui.py` and `ui.html` | A transaction is signed or broadcast whose recipient, amount, fee or change differs from what the final screen displayed | Byte-level comparison of the frozen `PreparedPayment`, each signer request, the finalized transaction and the broadcast hex; tripwires `tests/test_gui.py`, `tests/test_send_flow.py` broken red by the referee | Assumes the operator's own machine and the app binary are what they claim to be; does not assume the operator can read a hex payload | Any demonstrated divergence between displayed and signed/broadcast bytes |
| T2 | Asset 1 — anyone or anything that reaches the local API with the session token | `POST /api/broadcast` (`gui.py:1051-1054` at the tag; the `d525f31` handler was `:988-1035`) and the library's `broadcast_transaction` | Mainnet broadcast without the per-transaction human confirmation, or with the confirmation suppressed/forged | `gui.py:1051-1054` plus `wallet_service.py:81-82`; negative test with the opt-in omitted, and a UI test that the checkbox cannot be defaulted | The token is the control; a test HTTP client is assumed, not a browser | A broadcast path that succeeds with the backend opt-in omitted |
| T3 | Asset 1/3 — a counterfeit or compromised hardware signer (firmware is out of scope; *the app's* acceptance of a hostile response is not) | `signing.py:156` and `probe.py` device-verification path | A device returns a correctly-signed but *different* transaction, and the app accepts it or injects it into the reviewed PSBT | `accept_signature_update` must reject a changed `tx`, a removed signature, or foreign partial sigs; the cycle-3 "counterfeit device returning a thief transaction" scenario must be reproducible as a test that fails red if the check is removed | The device's own display and firmware are trusted to the extent README states; the app must not require the operator to notice | Any path where a device response other than verified partial signatures reaches the finalized transaction |
| T4 | Asset 1/3 — a correct-but-incomplete wallet definition, or a hostile Esplora server answering the scan | BSMS change declaration vs `.1/*` inference (`probe.py:120-179`, `wallet_service.py:357`); change selection in `ui.html` | The operator's change is sent to an address the wallet's own definition does not own, or a sweep is silently substituted | `CHANGE-ADDRESS-REVIEW.md`'s stated rules tested against BSMS with and without a declared change branch; a "no route applies" BSMS must not silently produce a change output | The BSMS file itself is assumed to arrive over a trusted channel (README:41 states the app cannot tell whose key is whose) | Any change output not justified by the file or the stated standard, or a sweep offered as a workaround |
| T5 | Asset 1/5 — a malicious or lying Esplora/price server (external service, but the app's trust in it is internal) | `wallet_service.py:131-192` explorer calls; `network_settings.py:118-145`; the price quote feeding the large-amount floors `gui.py:1195-1209` | Funds sent because the app believed a lie: a wrong balance, a wrong fee, a wrong outpoint, a wrongly-identified network, or a suppressed large-amount prompt | Response shape/range validation, the independent second explorer for mainnet (`wallet_service.py:191-192`, `gui.py:240-258`), genesis/checkpoint verification, and the local 0.1/0.04 BTC floors that a lying-low price cannot suppress | Explorer honesty is assumed *only* to the extent the app cross-checks it; a single-source chain (Testnet4, Mutinynet) is a known asymmetry and must be reported as such | Any money-path decision resting on an unverified single source without a stated, tested fallback |
| T6 | Asset 1/5 — any process or web page on the operator's machine | The loopback HTTP API `gui.py:514-517` and `gui.py:535` (the per-connection timeout; the `desktop.py:316` figure of the withdrawn plan was wrong), host/origin/token gate `gui.py:569-572`, `gui.py:685-687` | An unauthorized local page drives the API: rebound DNS name, cross-site form, or a leaked token | Host equality, the Origin clause, constant-time token compare (`gui.py:604-621`), the fragment-only token delivery (`gui.py:99-109`), and the absence of an HTML-injection sink (`innerHTML`/`insertAdjacentHTML`/`outerHTML` nowhere; CSP nonce per response `gui.py:536-539`, `gui.py:583-587`) | Other processes on the operator's machine are assumed hostile, which is the point of the gate; the OS account itself is not modelled | Any request that mutates money-path state without the token and an exact Host |
| T7 | Asset 1/2 — a substituted HWI helper or `hwilib` payload | `probe.py:211-214`, `:418`, `:494`; `scripts/hwi_entry.py`; the `hwi.sha256` sidecar inside the signed bundle | A poisoned helper signs or exfiltrates; a source-mode import loads a tampered `hwilib` | Byte identity before the helper may speak, exact version-line membership, and pins that can actually fail. **Note for the panel:** at cycle 4 the tripwire at `tests/test_hardening_pins.py:331` re-asserted the `HWI_PAYLOAD_PINS` constant and could never fail, and `probe.py:211-214` pinned only `hwilib` and `hwilib._cli` while source mode imports the whole package. At the tag the old test is **gone** and the pins are re-asserted inside the manifest-coverage test at `tests/test_hardening_pins.py:375-376`; the CT-73/CT-95 fix is claimed to close exactly this. The row must be **tested**, not cited | The packaged helper's own bytes inside the signed bundle are covered by the outer signature; source mode is a developer path | A substitution path into the helper or `hwilib` that the pins do not refuse, or a claimed pin that cannot fail |
| T8 | Asset 2/4 — an actor holding push or dispatch rights on this repository (in practice the owner account, per section 0), or a workflow body able to escalate its own token | `.github/workflows/build-candidate.yml`; the dispatch-only trigger and its guards; `scripts/check-publish-paths.sh`; the repository's platform settings | Publish-capable bytes reach a release from a path other than the audited candidate→promote chain: a second publish path, an unsigned/unnotarized publish, a tag or asset overwrite, or code execution inside a `run:` block | The publisher guards, the tag-aware branch sweep, the no-overwrite tag guard, and the absence of any other publish-capable file. **Known surface to test, not assume closed** (cycle-4 findings, fixes claimed in the tag): `candidate_run_id` was interpolated directly into bash and was remedied by `env:` routing (CT-72); the publish-path matchers were blind to `write-all`, `gh api …/releases`, `curl` and `action-gh-release` (CT-77); the sweep never examined tags (CT-76); `release` held `contents: write` on every dispatch with no required reviewers (CT-83/CT-80); historical tags still freeze publish-capable workflow text (the repo discloses this residual itself at `releases/OWNER-ACCEPTANCE-2026-10-07.md:82-98`) | GitHub account compromise, platform compromise and stolen owner credentials are **external assumptions**; the panel evaluates the permissive-workflow path, which *is* in scope | Any demonstrated second publish path, unsigned publish, overwrite, or command injection reachable by a repository-controlled actor |
| T9 | Asset 4/2 — anyone who can alter what the operator downloads | The release page, `SHA256SUMS`/`SHA256SUMS.asc`, the SBOM, and the site that links them | The bytes a user downloads are not the bytes the candidate run produced, or the published list of hashes is not the one the pipeline signed | The candidate run-id/manifest binding, `gpg --verify` against the committed key, the no-overwrite guard, and a review of what the *download page* actually points at | The GitHub release page is assumed honest about what it stores; the repository is not assumed to control the CDN | Any published asset that cannot be traced to a successful candidate run at that commit, or a public link to bytes the pipeline did not produce |
| T10 | Asset 4 — the public download surface: measured by the cycle-4 survey as three releases stale (it then offered **v0.6.4** downloads and presented the **v0.6.4** Z.ai review as the security evidence while v0.6.5–v0.6.7 existed) | `docs/` (GitHub Pages) and the release page | The operator is directed to an older build and to evidence about a revision the audit did not grade, while newer, graded bytes exist | **Found by the cycle-4 survey and corrected on `main` at `fc65647`** (v0.6.7 metadata, labels, download buttons, an honest review-status notice; the 63 older releases marked *Superseded* in their notes only, every tag and asset retained). The publication record then moved the surface to `v0.6.8` at commit `b0a7324`. The panel must run the literal comparison of every version string and download URL in `docs/` against the release list, and record the result against the tag. The audit PDFs the site links label those reviews "independent" while the framework lock says independence "cannot be determined" — wording the Public Security Statement must not repeat | The site is not a release artifact and is out of code scope; this is a *release-channel and assurance* claim, which asset 4 covers | Whether anything the operator is directed to download differs from the bytes the pipeline published for the graded revision. A public statement of what to download and what was graded disagreeing with the graded revision is a **publication/hygiene defect**, not a code path to an unforgivable act |
| T11 | Asset 5 — a diagnostics file or log shared with a reviewer, or a network observer | diagnostic events `gui.py:71-96` and the 80-event trim `gui.py:526`, the report route `gui.py:739` (filename literal `gui.py:442`); `log_message` `gui.py:537-539`; the Esplora requests themselves | xpubs, addresses, txids, device identities or the session token reach a log, a diagnostics file, the repository, or a server beyond the operator's chosen explorer | Fixed-code events with device *class* only, token scrubbing, the log-silence tripwire (`tests/test_gui.py:928-951`), and a byte-level check of a produced diagnostics file | The chosen Esplora server learns the addresses the operator scanned for; that disclosure is consented to in the UI and is a stated design property, not a finding | Any wallet-identifying string or token in a persisted file, a log, or an artifact |
| T12 | Asset 1/3 — a hostile or mistaken BSMS file (accepted as a boundary by the owner, but the boundary must be stated where the operator meets it) | `probe.py:93` parse; the step-1 import UI and help text | The operator signs for a wallet definition the file's author chose — an attacker-named key | `tests/test_gui.py` `WalletFileTrustPins` plus the boundary statement in README and the step-1 help; the app must not *claim* to verify whose key is whose | Trusted delivery of the BSMS file is an explicit owner-accepted assumption (CT-61), not a control | Any UI or README text that implies the app verifies key ownership, or a parse that accepts a file the documented rules reject |

**Named next-cycle list** (items deliberately not investigated this cycle, recorded so they
are not lost): a component audit of the inherited stack (embit, HWI, libusb, pywebview,
PyInstaller) per section 8 question 6; enabling GitHub immutable releases after moving the
release job to draft → upload → publish (section 4); the un-failable-tripwire hygiene class
if CT-95's fold did not settle it (section 8 question 4); the `docs/` download-surface
recurrence class (T10); and the unreachable-commit provenance gap (section 7).

---

## 6. Out of scope — and why

Carried forward unchanged:

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

---

## 7. Not examined — and why

Carried forward from the original signed plan, with the revision references re-pointed:

- **The 2026-10-08/09 line of development.** Repository push events showed commits
  (`1a5e9bf`, `7d43464`, `2f779e2`, `5d826a1`, `fea859c`, `f79203c`, `f4ca17b`, `f13b190`,
  `bf3ba57`, `91aedfa`, `39af55b`) pushed to `refs/heads/main` on 2026-10-08/09, branch
  create/delete events for `cycle5-0.6.8`, `chore/fresh-color-team-v1.5-audit`,
  `archive/legacy-audit-artifacts` and others, Pages builds on those commits, and PR #57
  ("Superseded: audit-artifact reset, not adopted", opened 2026-10-09, closed unmerged).
  Those commits are unreachable from every ref but are not gone: the GitHub API still serves
  the objects by SHA, which is how the lost credential-recovery wiring (CT-97) was recovered.
  What cannot be audited is the Oct-8/9 tree **as a whole**: only objects the surveyor knew to
  ask for were read, nothing establishes the list is complete, and the branch that carried the
  work is gone. This cycle does **not** treat the surviving tree as a record of what was
  pushed; the delta is recorded as a provenance gap and a question for the owner (section 8,
  question 1).
- **The fixes the withdrawn plan deferred as "post-survey."** The commits it classed as
  landing after the target revision are **inside the audited tag**: `247ca73` (the
  contribution-policy wording in `CONTRIBUTING.md` and `README.md:95`) and `333b361`
  (restoring the `environment:` keys) are ancestors of `0d4e01f`. They are therefore part of
  what the panel audits, not deferred to a next cycle. This correction is the substantive
  difference between this plan and the withdrawn one.
- **The survey's writes.** The runbook's read-only rule was set aside at the owner's explicit
  direction for publishing this plan (section 9). This surveyor also made **one download**
  (section 0, evidence budget) and no other write: no branch was created, no release touched
  or tag created, no build dispatched, no secret value requested.
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
- **Published release bytes** — only the source archive was downloaded and hashed
  (section 1); the other nine assets' digests are the release's published values, not
  independently recomputed. `SHA256SUMS.asc` was not signature-checked and the DMG was not
  stapled-checked by this surveyor.
- **The GitHub Actions logs** of the `v0.6.8` candidate and promotion runs — their event,
  branch, commit and conclusion were read from the API; the logs were not.
- **GitHub secret values** — only names were read (workflow text and the environment list);
  values were never requested and are not in the repository.
- **The 13 CT-48 remediation commits** — `releases/PATCH-0.6.7.md:61-80` cites thirteen
  commit ids as its "branches kept" evidence for the CT-48 fix, and every one of them
  returns `fatal: Not a valid object name` from this clone; the remote holds only
  `refs/heads/main` plus tags. A claim the referee is told to verify therefore rests on
  evidence that no longer exists in the repository.
- **Full git history** — authorship sampled only: `mypbs`, `CJT.sh` (two identities),
  `Chris Terry`, `Bitseeker LLC` — all map to the owner. The repository documents
  AI-assisted development and prior AI audits, so line-level provenance of individual hunks
  is not answerable from the repository alone.
- **Runtime behavior** — the survey was static: no build, no server, no device, no
  dispatch (read-only rule).

---

## 8. Questions for the owner

The five cycle-`v0.6.4` questions and their answers are carried forward unchanged (section 9
of the signed cycle-`v0.6.7` plan); the standard does not change until it is passed. The
cycle-5 questions were put and answered on 2026-10-10; they are carried forward here with
their answers, re-pointed where `v0.6.8` changed the fact base. The sixth arrived with the
owner's 2026-10-10 amendment.

1. **The rewound default branch — answered by the owner, 2026-10-10.** The Oct-8/9 line was
   abandoned deliberately, by the owner's decision, and the reason is recorded so the panel
   is told it rather than left to speculate:

   > After the `v0.6.7` release, further audit-cycle work was started with several different
   > agentic tool sets, and it did not converge. Review rounds kept producing additional
   > speculative failure scenarios; each was treated as a defect, fixed, and re-reviewed,
   > without any scenario ever being demonstrated against the code. One cycle ran to roughly a
   > hundred executions without yielding a reproducible finding. The owner stopped it and
   > directed a return to a clean state at the `v0.6.7` release. This is a single-maintainer
   > project and the framework is being adopted incrementally; earlier cycles did not
   > converge, which is why this cycle's plan states a closed scope and a burden of proof.

   **The commissioned reviewer is Z.ai (GLM)** — the same tool set whose earlier run over
   `v0.6.7` is the open-ended cycle described above. That earlier run is what the reset
   replaces: the target did not change, the scope did. The incoming review is told its own
   history here so that it works the closed list in section 5 under the burden of proof, and
   does not resume unbounded threat enumeration.

   Facts the panel should have, and need not investigate further:
   - The commits pushed to `main` on 2026-10-08/09 are unreachable from every ref. They
     remain retrievable **by SHA** through the GitHub API. Nothing in the `v0.6.7` or
     `v0.6.8` release depends on them.
   - The work prepared on that line was **never adopted**. Pull request #57 was closed
     unmerged.
   - **No release was published from that line**, and no published byte of `v0.6.7` or
     `v0.6.8` was altered by the reset.
   - The discarded line is **out of scope** (section 6). The audit target is the published
     release (section 1), not the abandoned work.
2. **The public download page — answered by the fix, 2026-10-10, and carried forward.**
   The page was found three releases behind. Commit `fc65647` on `main` moved the JSON-LD
   metadata, the version label and all three download buttons to `v0.6.7`; rewrote the
   review notices to state that no review of `v0.6.7` had been published yet; and relabelled
   the footer links per revision. The 63 releases older than `v0.6.7` open with a
   *Superseded — do not use for new deployments* notice in their **notes only**: no tag was
   moved, no asset was added, replaced or deleted. The publication record then moved the
   surface to `v0.6.8` at commit `b0a7324`, after the tag was cut — which is why the tag's own
   `docs/*.html` still contains the text it shipped while `main` does not.

   **Scope ruling, so this cannot become a loop:** the website is **not a release artifact**.
   It is absent from `SHA256SUMS`, from the DMG, bundle, AppImage and tarball, and it cannot
   affect a payment. A stale download page is a **publication/hygiene defect, not a code
   defect**: recorded here as found and fixed, and the panel must not raise it as a finding
   against the published release. If the panel observes the stale text in the tagged tree,
   this paragraph is the record that it was found, fixed and verified, and the item belongs on
   the named next-cycle list rather than in the grade. A future recurrence is likewise a
   next-cycle item.
3. **Repository-controlled platform protections — answered by the owner, 2026-10-10, and
   re-read this cycle.** At the reconnaissance revision there was no branch protection and no
   ruleset anywhere, and no job entered a signing environment. The owner has since protected
   `main` (`protect-main`) and the release tags (`protect-tags`), both with no bypass actor,
   and has declined required reviewers on the signing environments and an Actions allow-list,
   on the recorded ground that either would sit in front of the agentic tooling the owner
   directs (section 0). The owner's decision rule, stated directly: adopt a control when it
   makes the system safer, does not inhibit agentic building of releases, and does not open an
   unbounded line of inquiry — otherwise defer it by name rather than half-adopt it. The panel
   need not ask this again; it should verify both rulesets and record that GitHub's *immutable
   releases* setting remains off, with the reason and the named follow-up in section 4.
4. **The claimed-fix ledger — answered by the owner's decision rule, 2026-10-10.** The
   referee's duty is bounded as follows, and neither half may be widened without the owner's
   amendment:
   - **Break-and-watch the release-critical controls.** For every control in the
     release-critical set — the money-path gates recorded in section 4 and the
     release-integrity gates — the referee must demonstrate that its test **can fail**:
     disable or falsify the control on a scratch copy, watch the named test fail, restore. A
     control whose test cannot fail is not evidenced by that test.
   - **Do not re-litigate the ledger.** The remaining rows of `releases/PATCH-0.6.8.md` are
     not re-broken one by one. Rows closed by a dated acceptance
     (`releases/OWNER-ACCEPTANCE-2026-10-07.md`) are taken as records. CT-54 is a time-boxed
     deferral expiring **2027-10-07** and CT-90 is a dated deferral recorded this cycle
     (CT-59, closed by the CT-84 fix, is listed with the cycle-4 deferrals): none is a finding
     this cycle, and the report must carry them as open deferrals with their expiry dates.
   - **The unverifiable row is neither a finding nor a clearance.** CT-48's evidence cites
     thirteen branch commits (`PATCH-0.6.7.md:61-80`) that are no longer objects in this
     repository. The row cannot be checked from the tree; it is **accepted as a historical
     record** and listed in the report as "evidence no longer retrievable". Unverifiability is
     not by itself a defect — but it is also not proof.
   - **A weak test is a note, not a blocker.** If a named tripwire cannot fail — the
     `HWI_PAYLOAD_PINS` re-assertion that CT-95 recorded is the example — that is a
     **test-hygiene note (Info)** and goes on the named next-cycle list. It is graded only if
     the panel demonstrates a path by which the un-failable test lets a real control regress;
     the burden of proof applies to the panel as much as to the code.
   - The referee's claim-by-claim verification of the ledger (section 0, independence
     condition) is unchanged by this answer.
5. **The Public Security Statement — answered, 2026-10-10.** The statement is not gated: the
   public download surface and the graded revision now agree. The statement is written by the
   incoming review and published with the report, to the specification in section 0; until it
   exists, the site carries a truthful interim notice that the review of this revision is
   being commissioned and that no review of this revision has been published yet. **The
   surveyor's model line stays exactly as written** — `not exposed by the harness` (section
   0). The environment contains no model variable, the owner has not declared one, and the
   plan will not guess; the panel should treat an unverifiable provenance line as a recorded
   fact about the harness, not as an omission.
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
   - The stack actually pinned at `v0.6.8` is **embit `0.8.2+besa.1`** (the vendored fork
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
     records the dependency boundary and the exact pins, and does **not** clear a dependency
     by citing a report about a different version. A component audit is named as a next-cycle
     item. The prior AI reports remain history and are not inputs to this cycle's conclusions
     (section 0, independence condition); this answer cites them only as the inventory of
     coverage the question asked for, and does not adopt any of their findings.

---

## 9. Owner review and sign-off — step two, no AI

**This section is intentionally empty.** The owner signs below; the surveyor writes nothing
here beyond the instructions and the carry-forward record.

The owner should, before signing:

1. Read **section 0 in full**. It is the locked scope; it governs wherever any later section
   disagrees with it. Confirm the five assets and the two unforgivable acts are right, the
   rubric conditions are the ones that should decide the grade, and every owner policy
   recorded here is the policy you intend.
2. Confirm the **target revision** (section 1): the published `v0.6.8`, tag `0d4e01f`, and the
   ten published assets with the digests listed. Confirm the **prior-finding re-check list**
   in section 1 is the complete set you want the next auditor to verify.
3. Confirm the **withdrawal notice** at the head of this document records what happened
   accurately, and that deleting the withdrawn plan is what you want on the record.
4. Confirm section 5's **closed T1–T12 list** and section 6's exclusions are exactly the
   boundary you intend, and that section 8's six answers are the ones you gave.
5. Sign with an **identity** — a handle, role, or organization (for example "Bitseeker LLC"),
   **not a personal name** — and a date. A signature covers the whole document, section 0
   included.

Signing here also closes the `v1.5.1` follow-up-cycle requirement that the new plan carry the
original signed plan's scope-bearing content unchanged, and that the owner confirm no
silent broadening, narrowing, or omission.

```
Signed:  ______________________________________     (identity, not a personal name)

Date:    ______________________________________

Notes:   ______________________________________________________________________
```

### Carry-forward record (surveyor's, for the owner's review)

- **Original signed plan carried forward:**
  `bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`, SHA-256
  `ab5c7dbb4b89ed4f485d1e6851ddab20a5950e57bd4aae5d852667d22c5fbed8` — the signed cycle-4
  plan, frozen at revision 8, lock published pre-panel at `5742ccd`.
- **Scope-bearing content carried forward unchanged:** the five declared assets and their
  ranking; the two unforgivable acts; the adapted grade rubric; all owner policies
  (no-asset-optional, "the operator should have noticed" is never a defense, independence
  condition, contribution model, authorised agentic operation, distribution and contribution
  policy, downstream dependency policy, operator model and two audiences, closed list and
  burden of proof); the definitions set in force; the in-scope requirements and the closed
  T1–T12 threat table; the exclusions; and the not-examined list.
- **Updated for this cycle:** the target-revision statements (now the published `v0.6.8`, tag
  `0d4e01f`, with the artifact digest table and the stated verification state of each digest);
  the cycle-lineage and prior-finding re-check list (section 1); the two framework-`v1.5`
  obligations (Public Security Statement specification; evidence budget and stop condition);
  the Agent provenance block (this surveyor's own harness, session ID and model line); and
  the withdrawal notice for the superseded plan.
- **Corrected against the audited tag:** the credential-wiring claim (the withdrawn plan
  described the missing `environment:` keys as live at the target; they are **present** at the
  tag, `build-candidate.yml:189` and `:775`); the post-survey-fix classification (`247ca73`
  and `333b361` are ancestors of the tag, so they are in scope, not deferred); the test-suite
  census (640 test functions across 34 modules at the tag, not "489 across 27"); the
  risk-residual paragraph (re-pointed from `d525f31` to the tag); and every
  `d525f31`-relative statement about the target, which now names its revision explicitly.
- **Nothing omitted.** No asset, act, exclusion, or owner policy present in the original
  signed plan is absent here. No threat was added to T1–T12. No scope was narrowed.

### Revision log

- **Revision 1 — 2026-10-11 — re-authored clean cycle-5 survey plan for the published
  `v0.6.8`.** Produced under `colorteam-surveyor.md` at framework tag `v1.5.1`, by a
  DeepSeek Harness session distinct from the withdrawn plan's
  (`DSH_SESSION_ID=session-3710045d-1db5-40f4-842b-525231d94bea`). Carries the signed cycle-4
  scope forward unchanged, adds the framework-`v1.5` Public Security Statement and evidence
  budget, pins the target to tag `0d4e01f` and its published artifacts, adds the prior-finding
  re-check list, corrects every claim the withdrawn plan made about the target that was not
  true of the tag, and records the withdrawal of that plan at the owner's direction.
  **This revision is not frozen.** The owner's signature below freezes it.

# Owner's audit statements of conditions

These are the owner's own statements of condition: what the audit must protect, what counts as
unforgivable, how the grade is decided, and the policies under which the review is run. They are
reproduced here as the owner wrote them; nothing else in this repository amends them.

Owner: `cjtsh` (Bitseeker LLC). Statements dated as noted.

---

## 1. Definitions in force

Color Team definitions framework tag `v1.5.0`. Roles in force: Red, Blue, Orange, Copper,
Amber, White.

Two framework-`v1.5` obligations apply to this cycle: a **mandatory one-page Public Security
Statement** as an audit output, and an **explicit evidence budget and stop condition**.

## 2. The declared assets, and what must not happen to them

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GPG release key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** — stolen credentials enable a fake build, which enables theft |
| 3 | The reviewed-transaction integrity chain (frozen prepared payment → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG, the platform bundles, `SHA256SUMS`/`SHA256SUMS.asc`, and the SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten; the public download surface never points at bytes the pipeline did not produce |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

**No asset is optional** (owner, 2026-10-06): the ranking orders severity, not attention. All
five assets are mission-critical; a demonstrated path to breach any of them is at least
CONDITIONAL, and no finding may be dismissed as low-priority because its asset is ranked fifth.

## 3. The unforgivable acts, in plain words

1. The app gets the owner to sign and broadcast a transaction that sends their real Bitcoin
   somewhere they did not approve — a thief's address, a wrong amount, or change quietly
   redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the app
   leaks the wallet's addresses and xpubs so strangers can watch and target the family's
   savings.

## 4. The rubric as adapted to this target

These conditions, and no others, decide the grade:

| Grade | Conditions that must hold here |
|---|---|
| ✅ CLEARED | The panel finds no path, in in-scope code at the target revision, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's; (e) expose a credential value. The invariants in `AGENTS.md` hold as stated, with test evidence where the repo claims it. |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, credential handling, or the release chain in a way that needs an owner decision — e.g. a gap that only opens under explorer misbehavior, device firmware trust assumptions, or stated invariants that lack the test coverage the repo claims. |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check. |

**"The operator should have noticed" is never a defense** (owner, 2026-10-06): any safety
property that depends on the operator spotting a discrepancy is a weakness the panel must
report, not a mitigation it may assume.

## 5. Policies under which the review is run

### Independence condition (owner, 2026-10-06)

This is a fresh audit under this methodology. The prior AI audit reports (`releases/AUDIT-*.md`,
`docs/audits/*.pdf`) are history and are **not inputs**; the panel and the referee run without
them, and no prior conclusion, grade, or finding may be cited as evidence in this cycle's
report. One bounded exception: the cycle-4 Color Team report
(`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`) and the repository's own
remediation ledger (`releases/PATCH-0.6.8.md`, `releases/OWNER-ACCEPTANCE-2026-10-07.md`) are
available to the **referee**; the specialist lanes run without them.

### Contribution model (owner, 2026-10-06)

The sole collaborator is the owner (`cjtsh`, admin). The repository is public and forkable, but
no third party can push, dispatch workflows, or merge code into it — there are no contributors
and no inbound PR surface (issues are reports, not code). Push and dispatch rights therefore
rest entirely on the owner's GitHub account and are treated as **owner account hygiene, outside
the application's threat model**; the panel does not audit GitHub account security. The workflow
guards are evaluated as protection against accidents and workflow-level abuse, not against
compromise of the owner's account.

The *repository-controlled platform settings* that those guards depend on (rulesets, branch
protection, environment protection rules, token permissions) are **in scope as configured
controls**. The panel must evaluate the publish path as it actually stands, not as the
workflow's comments describe it.

### Authorised agentic operation, and no automation (owner, 2026-10-10)

The owner works through agentic coding tools that act under the owner's own GitHub credentials
and authority. Platform controls must therefore not lock those tools out: no required reviewer
is added to the signing environments, and Actions is left at `allowed_actions: "all"` with
`sha_pinning_required: false`, so a tool the owner runs is never blocked by a platform setting.
The owner accepts the tool set as inside the owner boundary — "the owner's agent went rogue" is
a declared external assumption, never a graded finding — and the workflow guards exist to bound
what a dispatch can do on its own.

Two separate statements sit behind that, and they must not be conflated:

- **Inside the repository.** There is no automatic build and no automatic code update. No
  `schedule:`/cron exists in any workflow; the only non-manual triggers in the tree are pushes
  to the two retired `linux-port` / `windows-port` input branches
  (`linux-inputs.yml:26-29`, `windows-inputs.yml:26-29`), which only regenerate hash locks and
  publish nothing. Nothing in this repository starts a build, moves a pin, opens or merges a
  pull request, or publishes a release on its own initiative. Every build, every pin move and
  every publication is dispatched by the owner, or by a tool the owner directs while sitting at
  the terminal.
- **Outside the repository — declared by the owner, not verifiable from the tree.** The owner
  states that no scheduled or standing automation exists anywhere in their tool estate either:
  no cron job watches this codebase; no cron job watches third-party libraries or their
  releases; and no agent, agentic coding partner or coding framework is standing by to convert
  a third-party change, an outside pull request or a merge into a release or a pin move.
  Automated build and release scripts do exist, but nothing invokes them except the owner at the
  terminal — if the owner is not there as the commander, no work happens. This half is a
  declaration about systems outside this repository and cannot be tested from the tree. A panel
  that wishes to test it must obtain from the owner the scheduled-task inventory of the machines
  and accounts that hold the credentials; absent such an artefact, no finding may be graded on
  it.

### Distribution and contribution policy (owner, 2026-10-10)

This repository is public so that anyone may read, use, fork and independently verify the
software, and it is MIT-licensed for that purpose. It is **not** open to public collaboration:
Bitseeker LLC is the sole contributor and the only collaborator with write access, and outside
pull requests are not merged into the release line. Release artifacts are produced only from
`main`, by the audited `build-candidate.yml` candidate→promote chain, and are signed under the
Bitseeker LLC release key. A fork is someone else's build: it cannot publish under this
identity, and it is not this audit's subject. Consequently this audit treats **push and dispatch
rights on this repository** as the strongest in-scope attacker capability, and treats GitHub
account compromise, GitHub platform compromise, and stolen owner credentials as declared
external assumptions — recorded once, never graded as findings.

### Downstream dependency policy (owner, 2026-10-10)

The pinned versions in `requirements*.txt`, the `*.lock` files and `vendor/` **are the audited
versions**. The application does not track upstream automatically, and a dependency is not moved
to a newer release without its own review. Moving a pin **invalidates any inherited audit
evidence for that component** until it is re-established. Inherited evidence may be cited only
for the exact pinned version and only where the owner has named the audit that covers it.

### Operator model and report audiences (owner, 2026-10-06)

The target operator is a nontechnical fiduciary or family member — a lawyer, trustee,
accountant, spouse, or trusted advisor settling an estate that includes Bitcoin. They know
Bitcoin is dangerous and cannot audit the app themselves. The report has two audiences and must
serve both: (a) that nontechnical trusted advisor, who needs plain-language evidence of
diligence — thorough, best-effort, and explicitly *not* a guarantee; and (b) the agent that will
fix what the audit finds — every finding must be precise, located, and reproducible enough to
serve directly as fix-it input, so the improvement loop can re-run the audit on the revision.

**One vocabulary correction the panel must honour:** the product's documented posture is a
*networked loopback desktop app plus hardware signing plus public Esplora servers* — "airgap",
"air-gapped", "offline machine" and "watch-only" appear nowhere in the project, the app holds no
wallet key, it never receives a PIN, and it never asks for seed words. The report must describe
the product in those actual terms rather than importing airgap vocabulary it does not have.

## 6. Target revision (owner's direction)

The audited revision is the **published release `v0.6.8`** — tag
`0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`, committed 2026-10-10T17:13:08-04:00) —
together with the release artifacts the repository published on **2026-10-10T21:31:47Z**.

## 7. Out of scope

- `docs/` marketing/manual website — GitHub Pages content; ships separately and shares no code
  with the app.
- `releases/` and root status/history documentation (`CURRENT-STATUS.md`, `RELEASE-HISTORY.md`,
  `PHASE-HANDOFF.md`, `ROADMAP.md`, `PROJECT-HISTORY.md`, `releases/PATCH-*.md`) — historical
  records, not executable surface. **Exception:** `releases/PATCH-0.6.8.md` and
  `releases/OWNER-ACCEPTANCE-2026-10-07.md` are evidence inputs the referee must verify
  claim-by-claim, not prose to be graded.
- Prior AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) — history only and not
  inputs to this cycle.
- Internals of pinned third-party dependencies (hwi 3.2.0, pywebview 6.2.1, pyinstaller 6.22.2,
  requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, upstream embit) — hash-locked; an
  independent component audit of this stack is outstanding and is a separate effort with its
  own plan.
- Hardware wallet firmware (Ledger, Trezor, Jade, OneKey) — external devices, not this
  repository.
- Live Esplora/explorer operators — external services the design already treats as untrusted
  observations.
- GitHub account security, and the GitHub platform itself (availability, API honesty) —
  external assumptions, per the contribution model.

## 8. Not examined

- `vendor/libusb-1.0.0.dylib` — compiled arm64 binary; provenance and hash pin documented at
  `vendor/README.md:36-47` but internals not reviewed.
- Vendored embit wheel internals — only the documented two-edit delta vs upstream
  (`vendor/README.md:10-34`); the full library was not read.
- `ui.html` (129 KB), `gui.py`, `wallet_service.py`, `probe.py`,
  `tests/test_workflow_config.py` — sampled at entry points, gates, and stated invariants; not
  read line-by-line. Full reading is the panel's job.
- Runtime behavior on a live machine, and the contents of the published release artifacts other
  than the published source archive — the survey was static; no build was run, no server
  started, no device attached, no workflow dispatched, and no other artifact downloaded.
- The GitHub Actions run logs of the `v0.6.8` candidate and promotion runs — run metadata was
  read from the API; the logs themselves were not read.
- `docs/audits/*.pdf` — prior third-party AI audit reports in binary PDF form, not read.
- GitHub secret **values** — only their names were read; values were never requested and are not
  in the repository.
- Full git history — authorship sampled only.

**Excluded by demonstration:** *(empty — nothing was demonstrated unreachable. In particular,
the developer-mode network gate is frontend-only and a token holder can reach mainnet without
it; that is recorded as an in-scope weakness, not excluded.)*

## 9. Risk residuals the review is asked to treat as gates, not assumptions (owner, 2026-10-06)

Tag rulesets, environment protection, and least-privilege tokens are external controls the
cycle-3 plan could not verify. As they now stand: `main` carries branch ruleset `protect-main`
(id `24840839`, active), which blocks branch deletion and non-fast-forward pushes with **no
bypass actor**, so it applies to the owner's own tooling as well; tags are protected too, by
ruleset `protect-tags` (id `24841466`, active), which blocks tag deletion and non-fast-forward
tag moves across `refs/tags/v*` with no bypass actor, while deliberately leaving tag **creation**
unrestricted so the release job can still create the release tag; the two signing environments
carry a `main`-only branch policy and, by the owner's explicit decision above, **no required
reviewers**; and the workflow's `release` job holds `contents: write` on every dispatch. These
are recorded as residual risk and release-readiness gates, and the panel must say what it
verified itself versus what it took on the document's word.

## 10. Mandatory audit output — one-page Public Security Statement (framework `v1.5`)

The audit must produce a **one-page, release-specific, public-facing security statement**
alongside the technical report, the plain-English safety review, and the findings ledger. The
surveyor does not write or endorse it. It must state, at minimum:

- the public audience it is written for, and the product, version and commit it describes;
- the exact tested release artifacts **with hashes**, and the audit date;
- the grade and the release-readiness verdict;
- the protected assets and the controls that were actually tested;
- major findings and the unresolved gaps, including coverage limits;
- the operator safety checks the user must perform themselves;
- links to the full report and to the official download location; and **an explicit statement
  if binaries were not verified**;
- a candid AI-provenance statement: the actual agents/models/vendors involved, whether
  different-model independence was *verified* or only *declared*, and what human review took
  place;
- a plain-language posture block for the non-Bitcoin reader: what the app is and is not (it
  holds no wallet key, creates no wallet, never asks for seed words or a PIN, and never signs or
  broadcasts silently), the single BSMS wallet file the operator must supply, the one deliberate
  per-transaction mainnet confirmation, and the operator's own safety checks (verify the
  recipient and amount through a separate trusted channel; check the change in your own wallet
  software); and
- the distribution and contribution policy as stated above, so a reader knows the release line
  is single-maintainer, signed, and built only from `main`.

It must call the process an **AI-assisted or agentic security review**, never human-firm
certification, and must make no claim of perfect security, guaranteed absence of malware,
unhackability, or outside-firm endorsement. A BLOCKED or unpublished build must never be
described as approved or safe to deploy. Tone: calm, helpful, **trust but verify**.

## 11. Evidence budget and stop condition

**This plan is a fixed input:** if the review finds a genuine scope defect it is recorded as a
**scope/lock mismatch**, not silently repaired — a later change requires the owner to amend this
file and re-sign, which voids any lock already taken. Anything the review finds that is real but
outside this cycle's scope is recorded as a next-cycle item or a dated deferral, not folded in.

Owner review and sign-off: section 9 of the audit plan, signed by the owner with an identity (a
handle, role, or organization — not a personal name) and a date. The signature covers the whole
document, this statement included.

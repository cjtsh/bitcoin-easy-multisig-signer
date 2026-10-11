# Owner's audit statements of conditions

These are the owner's own statements of condition: what the audit must protect, what counts as
unforgivable, how the grade is decided, and the policies under which the review is run. They are
recorded here as the owner stated them and condensed for signature. Nothing else in this
repository amends them.

Owner: `cjtsh` (Bitseeker LLC). Statements dated as noted. Given under Color Team definitions
framework tag `v1.5.0`.

---

## 1. The declared assets, and what must not happen to them

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

## 2. The unforgivable acts, in plain words

1. The app gets the owner to sign and broadcast a transaction that sends their real Bitcoin
   somewhere they did not approve — a thief's address, a wrong amount, or change quietly
   redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or the app
   leaks the wallet's addresses and xpubs so strangers can watch and target the family's
   savings.

## 3. The rubric as adapted to this target

These conditions, and no others, decide the grade:

| Grade | Conditions that must hold here |
|---|---|
| ✅ CLEARED | The panel finds no path, in in-scope code at the target revision, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's; (e) expose a credential value. The invariants in `AGENTS.md` hold as stated, with test evidence where the repo claims it. |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, credential handling, or the release chain in a way that needs an owner decision — e.g. a gap that only opens under explorer misbehavior, device firmware trust assumptions, or stated invariants that lack the test coverage the repo claims. |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check. |

**"The operator should have noticed" is never a defense** (owner, 2026-10-06): any safety
property that depends on the operator spotting a discrepancy is a weakness the panel must
report, not a mitigation it may assume.

## 4. Policies under which the review is run

### Independence condition (owner, 2026-10-06)

This is a fresh audit under this methodology. The prior AI audit reports (`releases/AUDIT-*.md`,
`docs/audits/*.pdf`) are history and are **not inputs**; the panel and the referee run without
them, and no prior conclusion, grade, or finding may be cited as evidence in this cycle's
report. One bounded exception: the cycle-4 Color Team report and the repository's own remediation
ledger (`releases/PATCH-0.6.8.md`, `releases/OWNER-ACCEPTANCE-2026-10-07.md`) are available to
the **referee**; the specialist lanes run without them.

### Contribution model (owner, 2026-10-06)

The sole collaborator is the owner (`cjtsh`, admin). The repository is public and forkable, but
no third party can push, dispatch workflows, or merge code into it — there are no contributors
and no inbound PR surface (issues are reports, not code). Push and dispatch rights therefore
rest entirely on the owner's GitHub account and are treated as **owner account hygiene, outside
the application's threat model**; the panel does not audit GitHub account security. The workflow
guards are evaluated as protection against accidents and workflow-level abuse, not against
compromise of the owner's account.

The repository-controlled platform settings those guards depend on (rulesets, branch protection,
environment protection rules, token permissions) are **in scope as configured controls**. The
panel must evaluate the publish path as it actually stands, not as the workflow's comments
describe it.

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
  `schedule:`/cron exists in any workflow, and the only non-manual triggers in the tree are
  pushes to the two retired input branches, which only regenerate hash locks and publish
  nothing. Nothing in this repository starts a build, moves a pin, opens or merges a pull
  request, or publishes a release on its own initiative. Every build, every pin move and every
  publication is dispatched by the owner, or by a tool the owner directs while sitting at the
  terminal.
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
`main`, by the audited candidate→promote chain, and are signed under the Bitseeker LLC release
key. A fork is someone else's build: it cannot publish under this identity, and it is not this
audit's subject. Consequently this audit treats **push and dispatch rights on this repository**
as the strongest in-scope attacker capability, and treats GitHub account compromise, GitHub
platform compromise, and stolen owner credentials as declared external assumptions — recorded
once, never graded as findings.

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

## 5. Target revision (owner's direction)

The audited revision is the **published release `v0.6.8`** — tag
`0d4e01f60c7695d720099f9d8e9e23b38da63102` (`0d4e01f`, committed 2026-10-10T17:13:08-04:00) —
together with the release artifacts the repository published on **2026-10-10T21:31:47Z**.

## 6. Risk residuals the review is asked to treat as gates, not assumptions (owner, 2026-10-06)

Tag rulesets, environment protection, and least-privilege tokens are external controls the audit
must not take on faith. As directed: `main` is protected against deletion and non-fast-forward
pushes with no bypass actor, so the protection applies to the owner's own tooling as well; tags
are protected against deletion and force-moves, while tag creation is deliberately left
unrestricted so the release job can still create the release tag; the two signing environments
carry a `main`-only branch policy and, by the owner's explicit decision above, no required
reviewers; and the release job holds `contents: write` on every dispatch. These are recorded as
residual risk and release-readiness gates, and the panel must state what it verified itself
versus what it took on the document's word.

---

*Carried in the audit plan, not as owner conditions:* the framework `v1.5` obligations (the
mandatory one-page Public Security Statement and the explicit evidence budget and stop
condition), the out-of-scope list, and the not-examined list. Those belong to the audit's scope
and evidence record, which is the plan.

# Audit plan — bitcoin-easy-multisig-signer

## 0. Locked scope

**Definitions in force:** Color Team definitions v1.3.2 (framework tag `v1.3.2`,
`colorteam-surveyor.md`; `COLOR-TEAM.md` itself was not fetched — the runbook states
this file is all the surveyor needs) — Red, Blue, Orange, Copper, Amber, White.

**Declared assets, and what must not happen to them:**

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** — stolen credentials enable a fake build, which enables theft |
| 3 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG and SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

**The unforgivable acts, in plain words:**

1. The app gets the owner to sign and broadcast a transaction that sends their real
   Bitcoin somewhere they did not approve — a thief's address, a wrong amount, or
   change quietly redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or
   the app leaks the wallet's addresses and xpubs so strangers can watch and target
   the family's savings.

**The rubric as adapted to this target** — these conditions, and no others, decide the
grade:

| Grade | Conditions that must hold here |
|---|---|
| ✅ CLEARED | The panel finds no path, in in-scope code at the target revision, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's; (e) expose a credential value. The invariants in `AGENTS.md` hold as stated, with test evidence where the repo claims it. |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, credential handling, or the release chain in a way that needs an owner decision — e.g. a gap that only opens under explorer misbehavior, device firmware trust assumptions, or stated invariants that lack the test coverage the repo claims. |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check. |

**No asset is optional** (owner, 2026-10-05): the ranking orders severity, not
attention. All five assets are mission-critical; a demonstrated path to breach any of
them is at least CONDITIONAL, and no finding may be dismissed as low-priority because
its asset is ranked fifth.

**Independence condition (owner, 2026-10-05):** this cycle is a fresh audit under a new
methodology, and the methodology itself is on trial as much as the code. The prior AI
audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) remain in the repository as
history but are **not inputs** — the panel and the referee run without them, and no
prior conclusion, grade, or finding may be cited as evidence in this cycle's report.

**Operator model and report audiences (owner, 2026-10-05):** the target operator is a
nontechnical fiduciary or family member — a lawyer, trustee, accountant, spouse, or
trusted advisor settling an estate that includes Bitcoin. They know Bitcoin is
dangerous and cannot audit the app themselves. Consequences:

- **"The operator should have noticed" is never a defense.** Any safety property that
  depends on the operator spotting a discrepancy is a weakness the panel must report,
  not a mitigation it may assume.
- The report has two audiences and must serve both: (a) the nontechnical trusted
  advisor, who needs plain-language evidence of diligence — thorough, best-effort,
  and explicitly *not* a guarantee; and (b) the agent that will fix what the audit
  finds — every finding must be precise, located, and reproducible enough to serve
  directly as fix-it input, so the improvement loop (step five) can re-run the audit
  on the revision.

**Contribution model (owner, 2026-10-05):** sole collaborator is the owner (`cjtsh`,
admin — verified via the GitHub API at survey time); the repository is public and
forkable, but no third party can push, dispatch workflows, or merge code into it.
There are no contributors and no inbound PR surface: issues are the only inbound
channel, and they are reports, not code. Workflow dispatch and push rights therefore
rest entirely on the owner's GitHub account and are treated as **owner account
hygiene, outside the application's threat model** — the panel does not audit GitHub
account security, and the workflow guards are evaluated as protection against
accidents and workflow-level abuse, not against compromise of the owner's account.

**Target revision:** tag `v0.6.4`, commit `35cdedb150cef6d047c39537324faf1321be3c8d`
— the commit the published, signed and notarized 0.6.4 DMG was built from, so findings
apply byte-for-byte to the shipped artifact. The survey ran at `29249a5`
(`v0.6.4-16-g29249a5`); the 16 commits between the tag and the survey revision are
documentation/website-only — `git diff --stat 35cdedb..29249a5` touches no `.py`,
`.html` app, `scripts/`, `.github/`, `vendor/`, or `tests/` file — so the shipped
application code at the survey revision is byte-identical to the pinned tag
(`version.py:3` reads `APP_VERSION = "0.6.4"`). The owner confirmed that tail is
deliberate: Windows/Linux download and website work kept out of the Apple build path
(section 9). The panel audits the tag, not the docs tail.

**Out of scope:**

- `docs/` marketing/manual website — GitHub Pages content; ships separately and shares no code with the app.
- `releases/` and root status/history docs (`CURRENT-STATUS.md`, `RELEASE-HISTORY.md`, etc.) — historical records, not executable code. **Prior AI audit reports (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) are history only and are NOT inputs to this cycle** — see the independence condition above.
- Internals of pinned third-party dependencies (hwi 3.2.0, pywebview 6.2.1, pyinstaller 6.22.2, requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, upstream embit) — hash-locked; `CURRENT-STATUS.md` already records an independent component audit as outstanding; that is a separate effort.
- Hardware wallet firmware (Ledger, Trezor, Jade, OneKey) — external devices, not this repository.
- Live Esplora/explorer operators — external services the design already treats as untrusted observations.

**Not examined:**

- `vendor/libusb-1.0.0.dylib` — compiled arm64 binary; provenance and hash pin documented at `vendor/README.md:36-47` but internals not reviewed.
- Vendored embit wheel internals — only the documented two-edit delta vs upstream (`vendor/README.md:10-34`); the full library was not read.
- `ui.html` (127 KB), `gui.py` (62 KB), `wallet_service.py` (43 KB), `tests/test_gui.py` (44 KB) — sampled at entry points, gates, and stated invariants; not read line-by-line. Full reading is the panel's job.
- `docs/audits/*.pdf` — prior third-party AI audit reports in binary PDF form, not read.
- GitHub repository settings and secret values — not present in the repository and deliberately not touched (read-only rule); the workflow references them by name only.
- Full git history — authorship sampled via `git shortlog` only; all four author identities map to the owner.
- Runtime behavior on a live machine — the survey was static, per the read-only rule.

**Excluded by demonstration:** *(empty — nothing demonstrated unreachable at survey time)*

**Agent provenance — who ran this, and how you know.**

| | |
|---|---|
| **Surveyor — harness** | Kimi Code desktop app (environment variable `__CFBundleIdentifier=com.kimi.code.desktop`) |
| **Surveyor — session ID** | `not exposed by the harness` (environment inspected for session/KIMI variables; only `KIMI_CODE_REGION_MARKER=off` is present; no session identifier variable exists) |
| **Surveyor — model** | `not exposed by the harness` (the operator has not declared the model, and the surveyor never asks itself) |
| **Declared by** | The Surveyor agent running in the harness above, transcribed from the environment; operator handle: `cjtsh` |

The auditor records its own provenance in the report. The referee compares the two session
identifiers: **identical means one run did both jobs, the independence rule is broken, and
the audit is void.** Different identifiers establish different runs, not different models.

---

## 1. Target and revision

- **Repository:** `cjtsh/bitcoin-easy-multisig-signer` (local clone at
  `/Users/christerry/projects/bitcoin-easy-multisig-signer`)
- **Revision surveyed:** `29249a5413a6f5460d1a5f801cacc9e76152c1d2` (`main`), verified
  byte-identical in application code to the owner-pinned audit target, **tag `v0.6.4`
  (`35cdedb150cef6d047c39537324faf1321be3c8d`)** — see sections 0 and 9. The 16
  intervening commits are documentation/website-only.
- **Date:** 2026-10-05
- **Surveyed by:** Kimi Code agent (harness: `com.kimi.code.desktop`). Must NOT be the
  model that runs the audit.

## 2. The declared assets (ranked)

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | Signing and CI credentials (Developer ID certificate, Apple notary key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published. **Owner: "loss of credentials is the same thing as loss of funds"** — stolen credentials enable a fake build, which enables theft |
| 3 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 4 | Release artifact integrity — the published DMG and SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten |
| 5 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |

Ranking note (owner, 2026-10-05): all five assets are mission-critical. Funds rank
first, and credentials rank second because the owner equates their loss with loss of
funds. Ranks 3–5 are all direct paths to, or protections of, the funds and the
owner's identity — privacy is ranked fifth because a leak does not move funds by
itself, **not** because it is optional: the ranking orders severity, not attention,
and a demonstrated breach path against any declared asset is at least CONDITIONAL.
A stuck or blocked payment remains recoverable and sits below every asset on this
table.

## 3. The unforgivable acts (in plain words)

1. The app gets the owner to sign and broadcast a transaction that sends their real
   Bitcoin somewhere they did not approve — a thief's address, a wrong amount, or
   change quietly redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or
   the app leaks the wallet's addresses and xpubs so strangers can watch and target
   the family's savings.

## 4. Where the assets live

**Assets 1 & 3 — funds and the integrity chain:**

- Frozen prepared-payment state: `gui.py:253` (`class PreparedPayment`), created at
  `gui.py:1155-1156` with a random review ID (`secrets.token_urlsafe(18)`)
- Mainnet broadcast gate: `gui.py:909` (`mainnet_opt_in is not True` fails closed) and
  `gui.py:939-940`; backend default-refuse in `wallet_service.py:70-82`
  (`broadcast_transaction`, "Explicit mainnet broadcast confirmation is required.")
- Signature acceptance and verification: `signing.py:117` (`accept_signature_update` —
  clones reviewed PSBT, imports only partial signatures, verifies each at
  `signing.py:108`); finalization against expected txid: `signing.py:219`
  (`finalize_multisig`)
- PSBT construction: `wallet_service.py:736` ("never sign/broadcast"); second-source
  outpoint check: `wallet_service.py:186`; gap-limited scan: `wallet_service.py:498-526`
- Change-policy trust boundary: BSMS-declared vs inferred change — `probe.py:61-70`,
  governed by `CHANGE-ADDRESS-REVIEW.md`
- Final review and broadcast UI: `ui.html` (review screens, per-transaction mainnet
  consent checkbox, developer-mode network gate)

**Asset 5 — privacy:**

- Diagnostic token discipline: `gui.py:341` (`_clean_token` — drop rather than escape),
  `gui.py:439-448` (fixed-code 80-event buffer, device *class* only)
- "Never send xpubs" to explorers: `wallet_service.py:133`
- Session token handling: `gui.py:391` (`secrets.token_urlsafe(32)`), delivered in the
  URL fragment (`gui.py:85-92`), checked per request (`gui.py:553-557`), never written
  to terminal output (`gui.py:1169-1170`)

**Assets 2 & 4 — credentials and the release chain:**

- Dispatch-only workflow: `.github/workflows/build-candidate.yml:11`
  (`workflow_dispatch`, with separate `notarize` and `publish` inputs);
  publish-requires-candidate guard at lines 43-50; unsigned-publish refusal at
  551-552; no-overwrite guard at 555-563; candidate-manifest provenance verification at
  359-392
- Build scripts: `scripts/build-macos.sh` (release guard fails closed without notary
  credentials — workflow lines 166-188 test this), `scripts/build-sbom.py`,
  `scripts/build-source.sh`, `scripts/notary-args.sh`
- Secret *names* (values are not in the repo): `MAC_CERT_P12_BASE64`,
  `MAC_CERT_PASSWORD`, `MAC_APP_SPECIFIC_PASSWORD`, `MAC_NOTARY_KEY_P8_BASE64`
  (workflow lines 196-235); reviewed variable `LIBUSB_SHA256` (lines 131-135)
- Vendored, hash-pinned inputs: `vendor/` (embit patched wheel, libusb dylib) with
  documented provenance and SHA-256 pins in `vendor/README.md`
- Hash-locked dependencies: `requirements.lock`, `requirements-desktop.lock`,
  `requirements-ci.lock`

**Entry points (how data or a user gets in):**

- Loopback HTTP API: `gui.py:1167` — `ThreadingHTTPServer(("127.0.0.1", 0), …)`,
  random port, token-gated; the whole UI talks to it
- Desktop wrapper: `desktop.py:234-248` — pywebview window (`gui="cocoa"`) with a
  JS bridge (`desktop.py:56`) into the same session state
- Operator-supplied BSMS file: `probe.py:81-87` (size-bounded, UTF-8-checked parse)
- Hardware signers over USB: HWI 3.2.0 subprocess wrapper `scripts/hwi_entry.py`,
  bundled `vendor/libusb-1.0.0.dylib`
- Outbound network: Esplora scans/broadcasts and fee/price references through
  `safe_http.py:143-144` (redirects refused, TLS always verified; `safe_http.py:53-57`)
- Operator-configured explorer URLs persisted at
  `network_settings.py:25-27` (`~/Library/Application Support/Easy Bitcoin
  Multisig/settings.json`), validated at `network_settings.py:38-56`, written with
  `0o600`/atomic-replace at `network_settings.py:85-99`

**Data stores:** the settings JSON above (server URLs only); in-memory session state
(`gui.py:391-403`); the privacy-limited diagnostic buffer; the public-explorer URL kept
in browser memory as a session-only receipt. No wallet material is persisted by design.

## 5. In scope

- All first-party application code: `probe.py`, `wallet_service.py`, `signing.py`,
  `gui.py`, `desktop.py`, `network_config.py`, `network_settings.py`, `safe_http.py`,
  `version.py` @ `v0.6.4`
- The entire interface and its gates: `ui.html` (review screens, mainnet consent,
  developer-mode gate, pending-payment banner, busy/progress ownership, palette
  invariants)
- The HWI integration boundary: `scripts/hwi_entry.py` and the HWI timeout/retry rules
  stated in `AGENTS.md`
- Build and release pipeline: `scripts/build-macos.sh`, `scripts/build-sbom.py`,
  `scripts/build-source.sh`, `scripts/notary-args.sh`,
  `.github/workflows/build-candidate.yml`
- Dependency pinning as a control: `requirements*.txt`/`*.lock` hash pins and the
  documented `vendor/` delta (embit local patch, libusb pin) — the pins and the
  documented delta are in scope; the pinned code's internals are not
- `tests/` as evidence: the panel checks that the invariants the repo claims are
  enforced (`AGENTS.md` names `tests/test_palette.py`, `tests/ui_state_reuse.cjs`,
  diagnostics and change-branch tests) actually exist and test what is claimed
- `AGENTS.md` itself as the behavioral contract the code is audited against

## 6. Out of scope — and why

- **`docs/` website** — GitHub Pages marketing and manual content; ships separately
  (CNAME, `.nojekyll`) and shares no code with the application or its build.
- **`releases/` and root status/history documentation** (`CURRENT-STATUS.md`,
  `RELEASE-HISTORY.md`, `PHASE-HANDOFF.md`, `ROADMAP.md`, `PROJECT-HISTORY.md`,
  `releases/PATCH-*.md`) — the repository's own status and release claims; historical
  records, not executable surface. Auditing the prose is not this audit's job.
- **Prior AI audit reports** (`releases/AUDIT-*.md`, `docs/audits/*.pdf`) — history
  only, and **not inputs to this cycle** (owner, 2026-10-05): this is a fresh audit
  under a new methodology; the panel and referee run without them, and no prior
  conclusion, grade, or finding may be cited as evidence in this cycle's report.
- **Internals of pinned third-party dependencies** — hwi 3.2.0, pywebview 6.2.1,
  pyinstaller 6.22.2, requests 2.32.5, pyyaml 6.0.3, certifi 2026.7.22, and upstream
  embit beyond the documented local delta. They are hash-locked, and
  `CURRENT-STATUS.md` already records an independent component audit of this stack as
  outstanding. That audit is a separate effort with its own plan.
- **Hardware wallet firmware** (Ledger, Trezor, Jade, OneKey) — external devices with
  their own trust properties; the app audits *its side* of the HWI exchange, not the
  devices.
- **Live explorer operators** (mempool.space, Mutinynet's Esplora, etc.) — external
  services the design explicitly treats as untrusted observations; their own security
  is not this repository's.

## 7. Not examined — and why

- `vendor/libusb-1.0.0.dylib` — a 162 KB compiled arm64 binary. Its provenance
  (non-signing CI run, hash pinned against a reviewed repository variable) is
  documented at `vendor/README.md:36-47`; the binary's internals were not reviewed.
- The vendored embit wheel internals — only the documented two-edit delta against the
  pinned upstream archive (`vendor/README.md:10-34`); the full library source was not
  read.
- `ui.html` (127 KB), `gui.py` (62 KB), `wallet_service.py` (43 KB),
  `tests/test_gui.py` (44 KB) — sampled at entry points, gates, and stated invariants
  via targeted search; not read line-by-line. Complete coverage is the panel's job,
  not the survey's.
- `docs/audits/*.pdf` — four prior third-party AI audit reports in binary PDF form
  (Z.ai 0.6.2–0.6.4, plus a safety review); not read.
- GitHub repository settings, branch protection, and secret values — not visible from
  the repository contents and deliberately not touched (read-only rule). Whether only
  the owner can dispatch the publish workflow could not be determined from the code.
- Full git history — authorship sampled only: four commit identities (`Bitseeker LLC`,
  `CJT.sh`, `Chris Terry`, `mypbs`) all map to the owner; the repository documents
  AI-assisted development and prior AI audits, so line-level provenance of individual
  hunks is not answerable from the repository alone.
- Runtime behavior — the survey was static; no build was run, no server started, no
  device attached (read-only rule).

## 8. Questions for the owner

1. **Revision pinning** — *answered in section 9: pin tag `v0.6.4` exactly.* The
   survey ran at `29249a5`, sixteen documentation-only commits past tag `v0.6.4`, with
   the application code byte-identical to the published release.
2. **Ranking check** — *answered in section 9: all five assets are mission-critical;
   credentials rise to rank 2 ("loss of credentials is the same thing as loss of
   funds"), and the ranking orders severity, not attention.*
3. **Prior audits** — *answered in section 9: not shared. Fresh audit, fresh
   methodology; prior audit reports stay in the repository as history but are not
   inputs to this cycle, for the panel or the referee.*
4. **Operator model** — *answered in section 9: the general nontechnical public —
   specifically estate fiduciaries and family members (lawyer, trustee, accountant,
   spouse, trusted advisor). "The operator should have noticed" is never a defense;
   the report must serve both the nontechnical reader and the agent who fixes
   findings.*
5. **Workflow dispatch rights** — *answered in section 9: only the owner. Verified at
   survey time via the GitHub API — sole collaborator is `cjtsh` (admin). Dispatch and
   push rights are owner account hygiene, outside the application's threat model; the
   project is open source and forkable, but there is no inbound code surface —
   issues are the only inbound channel, and they are reports, not code.*

## 9. Owner review and sign-off — step two, no AI

**Corrections and notes.**

- *Sections 0, 1, 5, and the file name (owner-directed, before signing):* the audit
  target was re-pinned from the survey revision `29249a5` to **tag `v0.6.4`
  (`35cdedb`)** — the exact commit the published, signed and notarized DMG was built
  from. Owner's context: the commits after the tag are deliberate Windows/Linux
  download-button and website work on `main`, intentionally kept out of the Apple
  build path so the notarized macOS release and its audit trail are not disturbed.
  The file was renamed from `...-audit-plan-29249a5.md` to `...-audit-plan-v0.6.4.md`
  to match. (Dictated by the owner in an interactive review on 2026-10-05 and
  transcribed by the surveyor at the owner's direction.)
- *Sections 0 and 2 (owner-directed, before signing):* the asset table was re-ranked —
  signing/CI credentials moved from rank 5 to rank 2 with the owner's equivalence
  ("loss of credentials is the same thing as loss of funds"), and the "no asset is
  optional" note was added to the rubric and the ranking note, because the owner
  considers every declared asset mission-critical. (Same review, same transcription.)
- *Sections 0 and 6 (owner-directed, before signing):* prior AI audit reports were
  moved out of this cycle's evidence entirely — they remain in the repository as
  history, but the panel and referee run without them. Owner's context: this cycle is
  a fresh audit under a new methodology the owner developed, and the methodology
  itself is being tested as much as the repository. (Same review, same
  transcription.)
- *Section 0 (owner-directed, before signing):* added the operator model and report
  audiences block. The target operator is a nontechnical estate fiduciary or family
  member; "the operator should have noticed" is never a defense; and the report must
  serve two audiences — the nontechnical trusted advisor reading for diligence
  assurance, and the agent that will fix what the audit finds. (Same review, same
  transcription.)
- *Section 0 (owner-directed, before signing):* added the contribution model block.
  Sole collaborator is the owner (verified via the GitHub API); the repository is
  public and forkable, but there is no inbound code surface — issues are the only
  inbound channel. Workflow dispatch and push rights are owner GitHub account
  hygiene, outside the application's threat model. (Same review, same
  transcription.)

**Answers to the questions above** *(dictated by the owner in the same interactive
review, transcribed by the surveyor; the signature below remains the owner's own act).*

1. **Revision pinning:** pin tag `v0.6.4` (`35cdedb`) exactly. The docs-only tail
   after the tag is intentional and excluded; a future release carrying the
   Windows/Linux build work gets its own audit cycle with its own plan.
2. **Ranking:** all five assets are mission-critical. Funds first; credentials second
   because their loss is equivalent to loss of funds; privacy fifth but not optional —
   a breach path against any asset is at least CONDITIONAL.
3. **Prior audits:** not shared. This is a fresh audit with a fresh methodology —
   stronger and more independent — and the methodology itself is being tested as much
   as the repository. The prior audit reports stay in the repository for history but
   are not inputs to this cycle, for the panel or the referee.
4. **Operator model:** the app is for the general nontechnical public — specifically
   a lawyer, trustee, accountant, spouse, or trusted advisor settling an estate that
   includes Bitcoin: someone who knows Bitcoin is dangerous but cannot review the
   software themselves. The audit is diligence evidence, not a guarantee. The report
   has two end users: that nontechnical trusted advisor, and the agent that will fix
   any issues found — findings must be usable directly as fix-it input so the audit
   can be re-run on the revision.
5. **Workflow dispatch rights:** only the owner. Verified via the GitHub API at survey
   time — the sole collaborator is `cjtsh` (admin). This is an open-source tool the
   owner built for his own family and shared publicly — not a collaborative project;
   anyone may fork it, and anyone may file an issue if they find something, but no
   third party can push code, dispatch workflows, or merge anything. Dispatch and
   push rights are owner GitHub account hygiene, outside the application's threat
   model, and the panel treats them as such.

**Sign-off.**

- **Signed: Bitseeker LLC**
- **Date: 5OCT2026**

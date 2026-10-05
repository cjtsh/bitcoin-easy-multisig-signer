# Audit plan — bitcoin-easy-multisig-signer

## 0. Locked scope

**Definitions in force:** Color Team definitions v1.3.2 (framework tag `v1.3.2`,
`colorteam-surveyor.md`; `COLOR-TEAM.md` itself was not fetched — the runbook states
this file is all the surveyor needs) — Red, Blue, Orange, Copper, Amber, White.

**Declared assets, and what must not happen to them:**

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 3 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |
| 4 | Release artifact integrity — the published DMG and SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten |
| 5 | Signing and CI credentials (Developer ID certificate, Apple notary key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published |

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
| ✅ CLEARED | The panel finds no path, in in-scope code at the target revision, to: (a) sign or broadcast transaction bytes that differ from what the operator reviewed; (b) broadcast on mainnet without both the per-transaction final-screen consent and the fail-closed backend opt-in; (c) write wallet-identifying material to diagnostics, logs, or artifacts; (d) publish release bytes other than the verified candidate's. The invariants in `AGENTS.md` hold as stated, with test evidence where the repo claims it. |
| ⚠️ CONDITIONAL | No unforgivable-act path is demonstrated, but one or more findings weaken a gate, a verification step, privacy hygiene, or the release chain in a way that needs an owner decision — e.g. a gap that only opens under explorer misbehavior, device firmware trust assumptions, or stated invariants that lack the test coverage the repo claims. |
| ⛔ BLOCKED | Any demonstrated path to an unforgivable act; any handling of seeds, PINs, or private keys; any credential value exposed in the repo, artifacts, or logs; a pipeline able to publish unverified, unsigned, or unnotarized bytes; or any scope/lock mismatch at re-check. |

**Target revision:** commit `29249a5413a6f5460d1a5f801cacc9e76152c1d2` (branch `main`,
`git describe`: `v0.6.4-16-g29249a5`; working tree clean at survey time). The 16 commits
since tag `v0.6.4` (`35cdedb`) are documentation/website-only — `git diff --stat
35cdedb..HEAD` touches no `.py`, `.html` app, `scripts/`, `.github/`, `vendor/`, or
`tests/` file — so the shipped application code is byte-identical to published v0.6.4
(`version.py:3` still reads `APP_VERSION = "0.6.4"`).

**Out of scope:**

- `docs/` marketing/manual website — GitHub Pages content; ships separately and shares no code with the app.
- `releases/` and root status/history docs (`CURRENT-STATUS.md`, `RELEASE-HISTORY.md`, etc.) — evidence records the panel checks claims against, not executable code.
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
- **Revision surveyed:** `29249a5413a6f5460d1a5f801cacc9e76152c1d2` (`main`,
  16 docs-only commits past tag `v0.6.4`; application code identical to the published
  0.6.4 release)
- **Date:** 2026-10-05
- **Surveyed by:** Kimi Code agent (harness: `com.kimi.code.desktop`). Must NOT be the
  model that runs the audit.

## 2. The declared assets (ranked)

| Rank | Asset | What must NOT happen to it |
|---|---|---|
| 1 | The Bitcoin in the operator's multisig wallet (mainnet and practice-network funds) | No transaction is signed or broadcast that the operator did not review and explicitly approve — no altered recipient, amount, fee, or change output between review and broadcast |
| 2 | The reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction) | Bytes that differ from the reviewed payment must never reach a signer or an explorer; a signer response must never inject anything but verified partial signatures |
| 3 | Wallet privacy — xpubs, addresses, BSMS contents, txids, device identities | None of it is written to logs, diagnostics, the repository, or any server beyond the operator-chosen Esplora queries; diagnostics carry only fixed codes, the network, device *class*, and timestamps |
| 4 | Release artifact integrity — the published DMG and SBOM | Nothing is published except the exact bytes of a successful signed/notarized candidate run for the same commit; no tag or release asset is ever overwritten |
| 5 | Signing and CI credentials (Developer ID certificate, Apple notary key, GitHub token) and the release workflow itself | Credential values never appear in the repo, artifacts, or logs; a push alone never builds or publishes; an unsigned/unnotarized build can never be published |

Ranking note: theft of funds outranks privacy, which outranks availability (a stuck or
blocked payment is recoverable; a misdirected mainnet payment is not). If the owner
weighs privacy higher, say so in section 9 — it changes specialist emphasis, not the
unforgivable acts.

## 3. The unforgivable acts (in plain words)

1. The app gets the owner to sign and broadcast a transaction that sends their real
   Bitcoin somewhere they did not approve — a thief's address, a wrong amount, or
   change quietly redirected — while the screen showed them something else.
2. Someone ships a fake "Bitcoin Easy Signer" under the owner's signing identity, or
   the app leaks the wallet's addresses and xpubs so strangers can watch and target
   the family's savings.

## 4. Where the assets live

**Asset 1 & 2 — funds and the integrity chain:**

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

**Asset 3 — privacy:**

- Diagnostic token discipline: `gui.py:341` (`_clean_token` — drop rather than escape),
  `gui.py:439-448` (fixed-code 80-event buffer, device *class* only)
- "Never send xpubs" to explorers: `wallet_service.py:133`
- Session token handling: `gui.py:391` (`secrets.token_urlsafe(32)`), delivered in the
  URL fragment (`gui.py:85-92`), checked per request (`gui.py:553-557`), never written
  to terminal output (`gui.py:1169-1170`)

**Asset 4 & 5 — release chain and credentials:**

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
  `version.py` @ `29249a5`
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
  `releases/PATCH-*.md`, `releases/AUDIT-*.md`) — these are evidence and claims the
  panel verifies against the code, not executable surface; auditing the prose is not
  this audit's job.
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

1. **Revision pinning:** the survey ran at `29249a5`, sixteen documentation-only
   commits past tag `v0.6.4`, with the application code byte-identical to the
   published release. Should the audit pin `29249a5`, or exactly tag `v0.6.4`
   (`35cdedb`)?
2. **Ranking check:** assets are ranked funds > integrity chain > privacy > release
   chain > credentials. Is a privacy leak of the wallet's xpubs/addresses actually
   worse to you than item 4/5 imply, or does this order stand?
3. **Prior audits:** should the panel be given the earlier AI audit reports
   (`releases/AUDIT-DEEPSEEK-0.4.3.md`, `releases/AUDIT-ZAI-0.4.3.md`,
   `releases/AUDIT-ZAI-0.6.2.md`, `-0.6.3.md`, `-0.6.4.md`) as input, or does this
   cycle start fresh so the panel is not anchored by them?
4. **Operator model:** is the app still owner-and-family only, or is it now aimed at
   the general nontechnical public the website addresses? This changes how specialist
   lanes weigh "operator error" against "attacker action."
5. **Workflow dispatch rights:** who besides you can dispatch
   `build-candidate.yml`? Repository settings are not visible in the code; if only
   your account can, say so and the release-chain lane can treat dispatch control as
   owner account hygiene rather than an app property.

## 9. Owner review and sign-off — step two, no AI

**Corrections and notes.**

-

**Answers to the questions above.**

-

**Sign-off.**

- **Signed:**
- **Date:**

# Plan 0.4.4 — audit remediation and hardening

**Inputs.** Two independent audits of `main` at `7d622ef` (source version 0.4.3):
[`AUDIT-DEEPSEEK-0.4.3.md`](AUDIT-DEEPSEEK-0.4.3.md) and
[`AUDIT-ZAI-0.4.3.md`](AUDIT-ZAI-0.4.3.md). Where both raise the same item it is
marked **both**; the two reviews were run independently and agree on the
security-critical items, which is the reason for combining them here rather than
tracking two backlogs.

**Why 0.4.4 and not 0.4.5 or 0.5.0.** The published scheme in `AGENTS.md:36` and
`PHASE-HANDOFF.md:21` maps hot fixes to `0.2.x`, warm fixes to `0.3.x` and
nice-to-have work to `0.4.x`. It is exhausted at 0.4.3 and cannot be applied to
anything from here on. The repo's actual observed convention is a patch bump for
corrections (`0.2.1`, `0.2.2`, `0.3.1`, `0.3.2`, `0.4.1`, `0.4.2`), and 0.4.4
contains no new capability — so a patch is honest. **`0.5.0` should be reserved
for the release that first makes real mainnet broadcast possible**, because that
is a genuine change in what the product can do. Fixing the exhausted scheme text
is itself item D-3 below.

**Scope rule for this release.** An item belongs in 0.4.4 only if it is either

1. a fix for a defect that at least one audit identified, **or** hardening that
   makes a future defect less likely; **and**
2. confined to tests, documentation, build or packaging — **or** a strictly
   fail-closed tightening of existing behaviour.

Anything that changes fee policy, changes what the app will broadcast, needs the
owner's hardware, needs the Apple account, or needs a policy decision is **not**
in this release. Those are Phase 5 gates and are listed in Tier 2 so they do not
get lost. A refactor with no behavioural change but a large surface area is Tier
3 — it should not share a release with fail-closed tightening.

---

## Combined recommendation matrix

Every recommendation from both audits, deduplicated, with the tier it lands in.
`T1` = 0.4.4, `T2` = Phase 5 gate (owner / hardware / account), `T3` = deferred.

### Tier 1 — 0.4.4

| ID | Item | Source | Type | Why it is in this release |
| --- | --- | --- | --- | --- |
| A-1 | Regression tests that actually reach the **mainnet broadcast refusal**, plus the removed-prior-signature and non-`ALL`-sighash guards and under-dust change | DS | test | Mutation testing proved deleting any of these guards breaks **no** test. Test-only, and it protects the exact code Phase 5 will edit. |
| A-2 | Regression tests for the CSP / security headers and the "token never echoed into the page" guarantee | DS | test | The whole `Content-Security-Policy` block could be deleted without failing the suite. |
| A-3 | **Test isolation**: stop `test_gui_integration` writing to the real `~/Library/Application Support/…/settings.json` | DS | test | It silently resets a developer's own saved servers and reports a false failure in any read-only-`$HOME` environment. | ✅ done |
| A-4 | Broadcast **HTTP 5xx → `BroadcastOutcomeUnknown`**, not "the network refused" | DS | code | A 5xx can arrive after the node accepted; calling it a refusal is false and leaves the payment retryable without the pending-payment pause armed. Fail-closed tightening. |
| A-5 | Second mainnet refusal at the **engine boundary**, so the headline guarantee does not rest on one call site | DS | code | `wallet_service.broadcast_transaction(chain="main")` will POST if called directly. Stricter, not looser. |
| A-6 | Apply the 10,000-sat ceiling inside `estimate_fee_preview` for partial sends | both | code | A partial-send preview can currently show a fee the builder then refuses. Stricter. |
| A-7 | Surface the 20-address gap numerically and add a **Send-All-specific acknowledgement** | both | UI | "Send All" means "all found by this scan"; today only the generic review checkbox stands in front of it. Stricter gate. |
| A-8 | Session control to **clear signed bytes** | both | UI | Signed-but-unbroadcast bytes are spend authority; today their lifetime in app state is not operator-visible. |
| A-9 | Launcher installs a **hash-pinned** lock and asserts the `embit` version | DS | build | `Start Easy Multisig.command` installs `requirements.txt` (no hashes) and only checks `import embit` — directly contradicting `AGENTS.md:36`. |
| A-10 | Add `LICENSE` and `THIRD-PARTY-NOTICES`, bundle the notices into the DMG, add licence identifiers to the SBOM | DS | legal/dist | The DMG redistributes **LGPL-2.1-or-later** libusb with no notice, and the repo has no licence of its own. |
| A-11 | Missing bundled `hwi` in a frozen build is a **hard failure**, not a `PATH` lookup | DS | code | A packaged app should never silently execute a substituted binary. |
| A-12 | Verify or vendor libusb **before** `brew install`; normalise the SBOM digest case | DS | build | The digest gate currently runs after the unpinned formula has already executed; the SBOM step requires lowercase and CI passes the variable raw. |
| A-13 | Pin or hash `pyyaml` in CI, and add it to the **documented** test command | DS | build/doc | It is the only unhashed dependency in the pipeline, and the README omits it, so following the README silently skips the whole workflow-lint module. |
| A-14 | CI job that exercises the `RELEASE=1` signing/notarization path | DS | build | Every published DMG is the ad-hoc-signed artifact; the notarization branch has never run in CI and would first run on a real release. |
| A-15 | Drop `'unsafe-inline'` from `script-src` via a per-session nonce | both | code | No injection sink exists today, so this is defence in depth — but a money app should not need it. Serving-layer only. |
| A-16 | Fix the six remaining live documentation defects; consolidate the doc set (one `CURRENT-STATUS.md`, trimmed `README`, single `CHANGELOG`) | both | doc | A reviewer who finds `ROADMAP.md` calling signing "future scope" distrusts the whole set. |
| A-17 | Make the release workflow canonical in one file, and fix the stale `_validate_chain` wording | DS | build/doc | Two byte-identical workflow copies are kept in sync by hand; the CLI guard still says "test-only release". |

### Tier 2 — Phase 5 gates (owner, hardware, or Apple account)

These are the gates the *product* needs. They are not code that can be written
ahead of the decision, and both audits rank the first two as the top hot items.

| ID | Item | Source | Blocker |
| --- | --- | --- | --- |
| B-1 | Independently verify the **live wallet's change policy** — first unused change address and its full script/derivation, confirmed in the originating wallet or on a signer screen | both | Needs the live mainnet wallet and devices |
| B-2 | **Mainnet dry run**: prepare → two-device sign → finalise in memory → independent decode and verification → discard, never broadcast | both | Needs B-1 and hardware |
| B-3 | **Fee policy decision**: bounded high-fee override behind a fresh explicit review (with a stubbed busy-mempool quote test), or a documented referral | both | Owner decision |
| B-4 | **Developer ID + notarization** with a reverse-DNS `CFBundleIdentifier` | both | Apple Developer enrolment |
| B-5 | **Mainnet broadcast opt-in**: per-transaction, visible, default-refused, txid-bound, with tests proving it cannot be bypassed | both | Needs B-1…B-4 and explicit owner authorisation |
| B-6 | Keep the **one-engine rule** absolute through Phase 5 — no mainnet-special path, endpoint or flag | both | Standing constraint |
| B-7 | Plain-language **operator guide** and a stuck-payment / fee-bump runbook | both | Needs owner's real device steps |
| B-8 | Supported wallet/export/**device/firmware matrix** | both | No firmware version is recorded anywhere; needs the owner's tested versions |
| B-9 | Resolve the fee ceiling's practical limit — at 10 sat/vB only **8 inputs** fit, so a many-UTXO wallet is unrecoverable with no override | DS | Owner decision; consider a proportional ceiling |
| B-10 | **Second independently operated outpoint source** for Testnet4/Mutinynet, and/or a `testmempoolaccept` pre-check | both | Needs a reliable second service or a user-run node |
| B-11 | Fee-outage policy for urgent recovery (manual rate behind an explicit "no live reference" acknowledgement) | both | Falls out of B-3 |
| B-12 | External review of the two inherited critical components (embit PSBT/ECDSA, HWI transports), or pin to audited releases | both | Procurement |

### Tier 3 — deferred deliberately

| ID | Item | Source | Why not now |
| --- | --- | --- | --- |
| C-1 | Extract the payment lifecycle from `gui.py` into its own module | both | Highest-leverage refactor for reviewability, but a large surface with no behavioural change. Do it **after** 0.4.4 and **before** the mainnet opt-in (B-5), never in the same release as fail-closed tightening. |
| C-2 | Split `ui.html` into HTML/CSS/JS assets | both | Large UI regression surface; A-15 achieves the CSP goal without it. |
| C-3 | Increase scan parallelism (4–8 workers) with per-branch progress and incremental re-scans | both | Performance only; changes explorer traffic patterns. |
| C-4 | Architecture / threat-model page | both | Additive documentation; A-16 already touches the doc set. |
| C-5 | quarterly dependency and pin review | both | Process, not code. Could be a scheduled workflow; owner's call. |

---

## Acceptance criteria for 0.4.4

1. Full suite green with **no skips** on the documented Python 3.12 path, and the
   suite must **fail** when any guard covered by A-1/A-2 is deleted — re-run the
   mutation checks to prove it rather than assuming it.
2. `bash -n` clean on every shell script; `bash scripts/build-source.sh 0.4.4`
   builds and ships **every** root document (the assertion added in 0.4.3 makes
   this a build failure rather than a silent omission).
3. `node tests/ui_state_reuse.cjs` and `node tests/ui_send_mode.cjs` pass.
4. `version.py` reads `0.4.4`, and `RELEASE-HISTORY.md` gains a 0.4.4 entry
   linking this plan and both audits.
5. No change to: fee policy, the set of networks broadcast is possible on, the
   PSBT construction path, or the signature-verification rules. Any diff in
   `wallet_service.build_unsigned_psbt`, `signing.py` verification, or the
   network profile table is a scope violation and must be justified here first.
6. The DMG path is unchanged and mainnet broadcast remains refused in code.

## Explicit non-goals

- **No mainnet broadcast.** 0.4.4 does not enable it, and no item here weakens
  the refusal.
- **No fee-policy change.** B-3 and B-9 are decisions, not code to sneak in.
- **No new device support**, no new networks, no new wallet export formats.
- **No refactor of the transaction or signing engine** (C-1 is explicitly later).

## Release mechanics

The workflow is manual dispatch only, so merging this plan and the 0.4.4 code
does **not** publish anything. Cutting the release is a separate, explicit
action: bump `version.py`, merge, then dispatch the workflow, which builds the
DMG, `BUILD-SBOM.json` and `SHA256SUMS` and publishes an immutable tag. Never
repost under an existing version.

## Delivery note — what landed, and what moved to 0.4.5

**Landed in 0.4.4:** A-1 through A-6, A-9 through A-14, A-16 and A-17 — fourteen
of the seventeen Tier 1 items.

**Moved to 0.4.5: A-7** (Send-All acknowledgement and the 20-address gap number),
**A-8** (session control to clear signed bytes) and **A-15** (drop
`'unsafe-inline'` from `script-src` via a per-session nonce).

All three change what the browser renders from `ui.html`, and this release
process has no browser walkthrough: the automated checks cover the Python API,
the DOM state machine in Node, and the served headers, but nothing loads the page
and executes it. A CSP nonce that does not match the injected `<script>` tag, or
a misplaced acknowledgement control, would present as a blank or broken window —
a worse outcome than the defence-in-depth gap A-15 closes. They are small,
self-contained changes that deserve to be seen on a screen, so they belong in a
release that includes the owner's next walkthrough rather than in the one that is
being published now.

This is a deliberate scope call under the rule at the top of this file, not an
oversight: A-7 and A-8 are user-interface additions rather than strictly
fail-closed tightenings, and A-15 cannot be verified without executing the page.
Tier 2 and Tier 3 are unchanged.

# 0.6.7: Color Team cycle-3 remediation

Version 0.6.7 answers the cycle-3 Color Team audit of the `v0.6.6` tree
(`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md`). That
cycle graded **⛔ BLOCKED** — not on the software. Every lane cleared the
app: Red found no breach, including a counterfeit device that returned a
correctly-signed thief transaction and was refused; Orange recorded its
first-ever LOGIC PROVEN (21/21 invariants against outside oracles);
Amber verified the v0.6.6 supply chain link by link.

The grade was set by one High finding on the **build process**, CT-48:
the per-platform publish workflows "retired" when Windows and Linux were
added were never deleted. `build-windows.yml` on `windows-port` and
`build-linux.yml` on `linux-port` were still live, dispatchable and able
to publish unsigned, unattested manifests — one was dispatched on
2026-10-05 and created the stray `v0.6.5-windows-x64` release that
cycle-2 graded CT-27. Meanwhile `build-candidate.yml`'s header claimed
"no second path can attach bytes to a release", which was false at
repository scope. A comment that overclaims a control is itself a
finding.

This release is a build-process remediation. The wallet, transaction,
signing and broadcast engine is unchanged apart from two hardening items
that add checks (CT-49/CT-58 helper identity, CT-60 broadcaster
verification). No new payment capability is added.

## Finding → fix → test

Every row below is closed either by a test demonstrated able to fail or
by the dated owner acceptance note. Nothing is closed by silence.

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-48 | High | Every publish-capable workflow file deleted from every non-main branch (13 branch commits; branches kept). `scripts/check-publish-paths.sh` enumerates the **remote's** heads and fails closed on a publish-capable workflow at any non-main ref. Every false "no second path" comment corrected. Guard steps pinned by body. | `tests/test_workflow_config.py::PublishPathSweepTests`, `GuardBodyPins`; the sweep script itself, run on every dispatch |
| CT-49 | Med | Helper identified by bytes before it may speak: frozen builds require the `hwi.sha256` sidecar their build wrote; source mode runs `scripts/hwi_entry.py` under the running interpreter and pins `hwilib/__init__.py` + `hwilib/_cli.py` by SHA-256. `shutil.which` PATH lookup is gone. Version line is exact set membership, not a substring. Launcher comment reworded to say what is true. | `tests/test_hardening_pins.py::HwiIdentityPins`, `tests/test_platform_port.py::ProbeHelperPathTests`, `tests/test_build_sbom.py::HelperDigestPins` |
| CT-50 | Low | `ui.html` now carries both large-amount floors and is pinned to `gui.py`. It also reads the 4,000,000-sat untrusted-quote floor, which it never did — a 0.05 BTC prepare under a lying price quote previously pressed straight into a backend refusal. | `tests/ui_large_amount.cjs`; `tests/test_gui.py` cross-file literal pin |
| CT-51 | Low | Request-log suppression pinned by running the real server twice: once asserting nothing is printed, once with the base `log_message` restored showing the line that would have leaked. | `tests/test_gui.py` (log-silence tripwire) |
| CT-52 | Low | Guard pins assert the guard **bodies** — `exit 1` and the specific refusal message — not the step names. A step named "Refuse…" whose body is `true` fails the build. | `tests/test_workflow_config.py::GuardBodyPins` |
| CT-53 | Low | BSMS magic-line gate gets a hostile-header test naming the exact refusal, plus the positive half (BOM and CRLF still parse). | `tests/test_probe.py` |
| CT-54 | Low | **Deferred** — rebuild `vendor/libusb-1.0.0.dylib` from pinned upstream source at the next dependency bump (the audit's own remedy). Hard expiry 2027-10-07. | dated deferral in `releases/OWNER-ACCEPTANCE-2026-10-07.md` |
| CT-55 | Low | All six `python-version:` sites pin the full patch **3.12.10**. The pin is deliberately not "whatever this laptop runs" (3.12.14) or what Linux's tool cache floated to (3.12.15) — see the asset evidence below. | `tests/test_workflow_config.py::PythonInterpreterPinTests` (no PyYAML: cannot skip itself green) |
| CT-56 | Low | `scripts/build-source.sh` ships `scripts/hwi-entitlements.plist`, `LINUX-PORT.md` and `requirements-desktop-linux.txt`. The header comment no longer claims the plist is absent. | `tests/test_build_source.py::ArchiveCompletenessTests` |
| CT-57 | Low | `requirements-piptools.lock` is committed and installed under `--require-hashes` by both inputs workflows. `build-linux.sh`'s unpinned `pip install --upgrade pip` is gone. | `tests/test_workflow_config.py::ToolchainPinTests`, `tests/test_hardening_pins.py::PipToolsPinTests` |
| CT-58 | Low | Folded into CT-49: `begin_signing_session()` clears the identity cache, and `verify_signer_device` starts every signing session with it. The per-path cache no longer outlives a session. | `tests/test_hardening_pins.py::HwiIdentityPins.test_the_verified_helper_is_re_identified_at_each_signing_session` |
| CT-59 | Low | **Deferred** — a stalling explorer can make one scan slow. The scan fails closed and claims nothing about balance. A hard deadline would trade one availability limit for another. Revisited at the next full audit cycle; hard expiry 2027-10-07. | dated deferral in the acceptance note |
| CT-60 | Low | `verify_esplora(chain, broadcaster)` now runs unconditionally in `_broadcast`, before the irreversible submit. The old gate fired for Mutinynet alone (the only chain with a checkpoint), so mainnet and Testnet4 submitted to whatever endpoint was in settings without a genesis check at use time. The check was valid everywhere and was being withheld. Negative half pinned too: a refused broadcaster means no send and nothing pending. | `tests/test_send_flow.py` (both halves) |
| CT-61 | Info | Not accepted as design alone: the boundary is now stated where the operator meets it — the step-1 wallet help and `README.md`'s wallet-import bullet. A BSMS naming an attacker's key **is** the wallet definition; trusted delivery of the file is the boundary. | `tests/test_gui.py::WalletFileTrustPins` + the dated acceptance |
| CT-62 | Info | The large-amount message no longer understates its own trigger. It said "at least 0.1 BTC" and fired at 0.04. It now names the floor it actually fires on. | `tests/test_gui.py` message pin |
| CT-63–CT-70 | Info | Design properties, accepted. Each is a property of a product a lawyer, accountant or spouse is expected to use; "fixing" would mean redesigning it. | `releases/OWNER-ACCEPTANCE-2026-10-07.md`, with per-item tripwires naming when each reopens |
| CT-71 | Info | Stale "latest published release is X" prose is gone as a pattern. `AGENTS.md`, `README.md` and `replit.md` point at `RELEASE-HISTORY.md` and the Releases page instead of hardcoding a number that goes stale the moment `version.py` moves. | `tests/test_hardening_pins.py::VersionStringPins` |
| CT-35, CT-36–42, CT-44, CT-47 | Info | Carried cycle-2 observations, accepted as design properties by dated owner acceptance (rubric ruling 2). | `releases/OWNER-ACCEPTANCE-2026-10-07.md` |

## CT-48: the branch sweep

The claim "no second path can attach bytes to a release" was checked
against the local checkout, which is exactly why it survived two audit
cycles. Twelve non-main branches carried a stale `build-candidate.yml`
copy with its own `contents: write` release job; `dev-mode-0.6.0`'s had
`publish` defaulting to **true**.

Every publish-capable workflow file is now deleted from every non-main
branch. Branches are kept; no history is rewritten and nothing is merged
into `main`. Thirteen branch commits, each named `Delete the
publish-capable workflow from this branch (CT-48)`:

| Branch | Commit |
| --- | --- |
| `windows-port` | `80bc3ee99533` (dropped `build-windows.yml`) |
| `linux-port` | `c028e0c3c642` (dropped `build-linux.yml`) |
| `audit-fixes-0.6.5` | `e981c946bf1f` |
| `dev-mode-0.6.0` | `f61d5dbaa5c3` |
| `codex/release-0.6.4` | `3b4b36243478` |
| `warm-0.3.0` | `93f19f6b43cf` |
| `phase2-transaction-builder` | `2cade9ebb22f` |
| `fix/stale-review-chain` | `9143a6db4165` |
| `docs/platform-installation` | `8bd8edcd768b` |
| `codex/audit-remediation-0.6.3` | `7e6f1ac17903` |
| `codex/release-download-context` | `9b7502c63239` |
| `codex/release-provenance-path` | `f33c703022ae` |
| `codex/release-workflow-only` | `24e79eb6f1ac` |

`v0.0.4-preview` never carried a publish workflow. After the sweep, the
remote is clean:

```
$ bash scripts/check-publish-paths.sh
ok: no non-main ref carries a publish-capable workflow
```

The sweep looks at the **remote's** heads, not the checkout. It fails
closed on any of: the retired per-platform filenames, `contents: write`,
or `gh release`. It runs as a gate on every dispatch, candidate runs too.

**One residual, named rather than implied:** historical tags freeze their
commit's workflow text. Tags from `v0.1.0` to `v0.6.3` still contain
their era's pipeline, and those before v0.6.4 lack the default-branch
guard. Moving or deleting a published tag is itself a CT-01/CT-27-class
finding, so those tags stay. The control that answers this is the one
that was missing: the dispatch ref is always `main`, never a tag; the
sweep keeps every *branch* free of a second publisher; and the publish
job refuses every ref but `refs/heads/main`.

## CT-55: which Python, and why not a newer one

`python-version: "3.12"` is not a pin. `actions/setup-python` resolves a
bare minor to whatever that runner's tool cache already holds. The
2026-10-06 candidate run therefore built **one commit** on three
different interpreters from one identical line:

| Job | Interpreter actually used |
| --- | --- |
| Windows x64 bundle | CPython 3.12.10 |
| Apple Silicon DMG | CPython 3.12.10 |
| Source archive and tests | CPython 3.12.14 |
| Linux x86_64 AppImage | CPython 3.12.15 |

The pin is **3.12.10**, chosen from asset availability rather than
convenience:

- `actions/python-versions` release tags are `3.12.XX-<run_id>`. Tag
  `3.12.10-14343898437` carries `darwin-arm64`, `darwin-x64`,
  `linux-20.04/22.04/24.04` x64+arm64, and `win32-arm64/x64/x86`.
- **3.12.11 and later are Linux-only assets.** There is no Windows or
  macOS build of them in that registry.
- So 3.12.10 is the newest 3.12 that all three pinned runners
  (`macos-15`, `windows-2022`, `ubuntu-24.04`) can actually install.
  Pinning 3.12.14 (this laptop's venv) or 3.12.15 (Linux's float) would
  not fix the drift — it would break the Windows and macOS jobs outright.
- The value is recorded at every one of the six pin sites so a later
  "helpful" bump has to argue with it.

HWI 3.2.0 still caps the range at `<3.13`; that is unchanged.

## Break-and-watch transcripts

Every money-path and release-path control below was broken on a
disposable copy, the named test was observed red, the file was restored
green, and the positive half stayed green. `__pycache__` is cleared
before every run.

### CT-48 — publish path (commit `7077bd5`)

| Break | Test that went red |
| --- | --- |
| sweep scanning only the local checkout | body-pin tests |
| `exit 1` removed from the gate step | `GuardBodyPins` |
| offender count neutered | both sweep refusal tests |

### CT-50 / CT-51 / CT-53 / CT-62 — the four unpinned controls (commit `4c083e8`)

| Break | Test that went red |
| --- | --- |
| UI floor desynced from `gui.py` | cross-file literal pin |
| untrusted-quote floor removed from the UI | `tests/ui_large_amount.cjs` |
| log no-op removed | log-silence tripwire |
| magic-line gate gutted | hostile-header refusal test |
| CT-62 message reverted to "at least 0.1 BTC" | message pin |

### CT-61 — the trust boundary in the product (commit `451fa68`, `/tmp/bw_ct61.py`)

| Break | Test that went red |
| --- | --- |
| in-app step-1 warning dropped | `WalletFileTrustPins` (3 failures) |
| `README.md` warning dropped | `WalletFileTrustPins` (2 failures) |
| claim that the app can tell which key is yours | `WalletFileTrustPins` (1 failure) |

### CT-49 / CT-58 — helper identity (commit `faadfb8`, `/tmp/bw_ct49.py`)

| Break | Test that went red |
| --- | --- |
| A — byte gate removed | planted-echo + no-sidecar tests |
| B — version check back to `in` | substring test (3 failures) |
| C — `shutil.which` restored | path-lookup tests (2 tests) |
| D — `begin_signing_session` dropped | CT-58 re-identify test |
| E — payload pin not compared | substituted-hwilib test |
| F — a build drops the sidecar write | build-write pin |
| G — SBOM accepts a missing sidecar | missing-sidecar test |
| H — disagreeing sidecar accepted | disagreeing test (positive half of H correctly stays green) |

A first draft of the build-write pin matched the word `hwi.sha256` in a
comment and stayed green while the write was renamed away. It now
requires an actual redirection or `Set-Content`, which is the reason the
transcript above is trustworthy.

### CT-55 — interpreter pin (commit `691faf8`, `/tmp/bw_ct55_transcript.txt`)

| Break | Result |
| --- | --- |
| A — one site back to the bare minor `3.12` | RED |
| B — one site drifted to `3.12.15` | RED |
| C — `AGENTS.md` no longer names the exact patch | RED |
| D — `build-macos.sh` stops naming the patch | RED |
| E — the `PINNED` constant moved to 3.12.15 | RED |

All four positives green. A first transcript was untrustworthy and said
so: breaks C and D rewrite a same-length literal (`3.12.10` ↔ `3.12.15`)
and restore it inside one second, so CPython kept the broken `.pyc` and
the next run executed the old module — the positive half reported RED
while the source on disk was correct. The harness now clears
`__pycache__` before every run. Recorded rather than quietly re-run
past, because a break-and-watch that can be fooled is worse than none.

### CT-56 / CT-57 / CT-60 — tarball, lock-writer, broadcaster (commit `d2e9e73`, `/tmp/bw_ct56_60_transcript.txt`)

| Break | Result |
| --- | --- |
| F — scripts/ copy drops the plist | RED |
| G — `root_docs` drops `LINUX-PORT.md` | RED |
| H — the header goes back to claiming the plist is absent | RED |
| I — a workflow installs pip-tools by version alone | RED |
| J — a lock entry is pinned by version alone | RED |
| K — `build-linux.sh` upgrades pip unpinned again | RED |
| L — the checkpoint gate comes back | RED |
| M — a refused broadcaster no longer stops the submit | RED |

Ten positives green. Two of the first breaks were wrong, and both were
caught rather than waved through:

- "the lock loses the artifact hash" deleted one of pip-tools' **two**
  wheel hashes and the test stayed green — correctly, one hash is still
  a pin. The break did not destroy the property. Replaced with a real
  one, and the test now requires **every** `name==version` entry to
  carry a digest, so the same shape of break against `build`, `click` or
  `pyproject-hooks` cannot pass either.
- "the header claims the plist is absent" reworded the false claim with
  a capital `T` and sailed through `assertNotIn("the port has neither")`.
  The assertion is now case-insensitive across several phrasings and also
  requires the header to state affirmatively that the plist ships.

`tests.test_hardening_pins.PipToolsPinTests` already pinned one
pip-tools release across both jobs; CT-57 moved that pin into the lock,
so the test now follows it there (exactly one release in the lock, and
the input file naming the same one) rather than being deleted.

## Deferred, with the reason

Both deferrals are recorded in `releases/OWNER-ACCEPTANCE-2026-10-07.md`
as dated deferrals, not permanent properties. Each carries a hard
trigger.

- **CT-54** — rebuild `vendor/libusb-1.0.0.dylib` from pinned upstream
  source at the next dependency bump. The current dylib's symbol set is
  identical to the pinned build and its provenance chain is in the SBOM.
  The audit's own remedy is "build from pinned source next bump". If no
  dependency bump has landed by **2027-10-07**, the deferral expires and
  the finding reopens.
- **CT-59** — a stalling explorer can make one balance scan slow. The
  scan is bounded per request and fails closed: if it cannot get a
  complete answer it claims **nothing** about the balance. A hard
  deadline would trade one availability limit for another. Revisited at
  the next full Color Team audit cycle; if none has run by
  **2027-10-07**, the deferral expires and the finding reopens.

## Owner acceptance note

`releases/OWNER-ACCEPTANCE-2026-10-07.md`, signed Bitseeker LLC, dated
2026-10-07, closes by rubric ruling 2 the carried cycle-2 Infos (CT-35,
CT-36–42, CT-44, CT-47) and the cycle-3 design-property Infos
(CT-61, CT-63–70). It records the CT-54 and CT-59 deferrals above. It
carries per-item tripwires naming the code property each acceptance
rests on, so a later edit reopens the finding instead of quietly erasing
it. It is not used to close anything that was fixed in code.

## What did not change

No wallet, signing, or broadcast policy changed. Specifically:

- The BSMS import, change-path and Send All rules are untouched.
- `PreparedPayment` binding, signature acceptance, finalization and the
  broadcast gates are untouched except that **one more** check now runs
  before submit (CT-60). Nothing was relaxed.
- The large-amount prompt, the mainnet final-screen consent and the
  backend mainnet opt-in are untouched.
- No seed, PIN or private key input exists; no wallet creation; no silent
  signing.
- The one publish path, `build-candidate.yml`, is the only change to how
  bytes reach a release page.

## Verification

Full suite **500 tests OK, zero skips** at `d2e9e73`, with 10/10
`tests/ui_*.cjs` OK. The version bump itself is a docs-and-version
commit; it is re-verified before the candidate is dispatched.

## Publication

Not yet published. A signed, notarized `publish=false` candidate is
built from this revision through `.github/workflows/build-candidate.yml`.
Promotion (`publish=true`, `candidate_run_id=…`) from the same commit
requires the owner hardware walkthrough first, because CT-49/CT-58 touch
the device-identity path. Manual publication is prohibited.

### Candidate history

To be filled from the candidate run. Do not claim a published version
this file does not carry.

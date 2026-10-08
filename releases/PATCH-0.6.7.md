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
| CT-48 | High | Every publish-capable workflow file deleted from every non-main branch (13 branch commits; branches kept). `scripts/check-publish-paths.sh` enumerates the **remote's** heads and fails closed on a publish-capable workflow at any non-main ref — including on a workflow body it **cannot read**. Every false "no second path" comment corrected. Guard steps pinned by body. | `tests/test_workflow_config.py::PublishPathSweepTests`, `SweepFailClosedPins`, `GuardBodyPins`; the sweep script itself, run on every dispatch |
| CT-49 | Med | Helper identified by bytes before it may speak: frozen builds require the `hwi.sha256` sidecar their build wrote, held **inside the signed bundle** (`Contents/Resources` on macOS, beside the helper elsewhere) so the outer signature covers it; source mode runs `scripts/hwi_entry.py` under the running interpreter and pins `hwilib/__init__.py` + `hwilib/_cli.py` by SHA-256. `shutil.which` PATH lookup is gone. Version line is exact set membership, not a substring. Launcher comment reworded to say what is true. | `tests/test_hardening_pins.py::HwiIdentityPins`, `tests/test_platform_port.py::ProbeHelperPathTests`, `tests/test_build_sbom.py::HelperDigestPins` |
| CT-50 | Low | `ui.html` now carries both large-amount floors and is pinned to `gui.py`. It also reads the 4,000,000-sat untrusted-quote floor, which it never did — a 0.05 BTC prepare under a lying price quote previously pressed straight into a backend refusal. | `tests/ui_large_amount.cjs`; `tests/test_gui.py` cross-file literal pin |
| CT-51 | Low | Request-log suppression pinned by running the real server twice: once asserting nothing is printed, once with the base `log_message` restored showing the line that would have leaked. | `tests/test_gui.py` (log-silence tripwire) |
| CT-52 | Low | Guard pins assert the guard **bodies** — `exit 1` and the specific refusal message — not the step names. A step named "Refuse…" whose body is `true` fails the build. | `tests/test_workflow_config.py::GuardBodyPins` |
| CT-53 | Low | BSMS magic-line gate gets a hostile-header test naming the exact refusal, plus the positive half (BOM and CRLF still parse). | `tests/test_probe.py` |
| CT-54 | Low | **Deferred** — rebuild `vendor/libusb-1.0.0.dylib` from pinned upstream source at the next dependency bump (the audit's own remedy). Hard expiry 2027-10-07. | dated deferral in `releases/OWNER-ACCEPTANCE-2026-10-07.md` |
| CT-55 | Low | All six `python-version:` sites pin the full patch **3.12.10**. The pin is deliberately not "whatever this laptop runs" (3.12.14) or what Linux's tool cache floated to (3.12.15) — see the asset evidence below. | `tests/test_workflow_config.py::PythonInterpreterPinTests` (no PyYAML: cannot skip itself green) |
| CT-56 | Low | `scripts/build-source.sh` ships `scripts/hwi-entitlements.plist`, `LINUX-PORT.md` and `requirements-desktop-linux.txt`. The header comment no longer claims the plist is absent. | `tests/test_build_source.py::ArchiveCompletenessTests` |
| CT-57 | Low | `requirements-piptools.lock` is committed and installed under `--require-hashes` by both inputs workflows. `build-linux.sh`'s unpinned `pip install --upgrade pip` is gone. Every recipe pin reads through `support.find_build_recipe`, so it also runs from the source archive. | `tests/test_workflow_config.py::ToolchainPinTests`, `BuildRecipeLookupTests`; `tests/test_hardening_pins.py::PipToolsPinTests`; `tests/test_windows_portability.py::HardeningPinPortabilityTests` |
| CT-58 | Low | Folded into CT-49: `begin_signing_session()` clears the identity cache, and `verify_signer_device` starts every signing session with it. The per-path cache no longer outlives a session. | `tests/test_hardening_pins.py::HwiIdentityPins.test_the_verified_helper_is_re_identified_at_each_signing_session` |
| CT-59 | Low | **Deferred** — a stalling explorer can make one scan slow. The scan fails closed and claims nothing about balance. A hard deadline would trade one availability limit for another. Revisited at the next full audit cycle; hard expiry 2027-10-07. | dated deferral in the acceptance note |
| CT-60 | Low | `verify_esplora(chain, broadcaster)` now runs unconditionally in `_broadcast`, before the irreversible submit. The old gate fired for Mutinynet alone (the only chain with a checkpoint), so mainnet and Testnet4 submitted to whatever endpoint was in settings without a genesis check at use time. The check was valid everywhere and was being withheld. Negative half pinned too: a refused broadcaster means no send and nothing pending. | `tests/test_send_flow.py` (both halves) |
| CT-61 | Info | Not accepted as design alone: the boundary is now stated where the operator meets it — the step-1 wallet help and `README.md`'s wallet-import bullet. A BSMS naming an attacker's key **is** the wallet definition; trusted delivery of the file is the boundary. | `tests/test_gui.py::WalletFileTrustPins` + the dated acceptance |
| CT-62 | Info | The large-amount message no longer understates its own trigger. It said "at least 0.1 BTC" and fired at 0.04. It now names the floor it actually fires on. | `tests/test_gui.py` message pin |
| CT-63–CT-70 | Info | Design properties, accepted. Each is a property of a product a lawyer, accountant or spouse is expected to use; "fixing" would mean redesigning it. | `releases/OWNER-ACCEPTANCE-2026-10-07.md`, with per-item tripwires naming when each reopens |
| CT-71 | Info | Stale "latest published release is X" prose is gone as a pattern. `AGENTS.md`, `README.md` and `replit.md` point at `RELEASE-HISTORY.md` and the Releases page instead of hardcoding a number that goes stale the moment `version.py` moves. Pinned, not merely cleaned: the claim is a sentence with a version number in it, and the prohibition sentences in those same docs are deliberately still legal. | `tests/test_hardening_pins.py::VersionStringPins.test_no_live_doc_hardcodes_a_latest_published_release` (with `…test_the_published_claim_pattern_is_not_vacuous` as its positive half) |
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

### CT-71 — the claim, pinned (`/tmp/breakwatch_067e.py`, 2/2)

The finding→fix table above once named `VersionStringPins` as CT-71's
closure. That was an overclaim: `VersionStringPins` pins CT-46's
version-string synchronisation and would not have noticed a
reintroduced "the latest published release is 0.6.6". Under this
project's rules that is itself a finding — a test that cannot fail does
not count as a fix — so CT-71 now has a pin of its own rather than a
borrowed one.

`test_no_live_doc_hardcodes_a_latest_published_release` scans the live
current docs (`AGENTS.md`, `README.md`, `CURRENT-STATUS.md`,
`PHASE-HANDOFF.md`, `replit.md`) for a published-release **claim** — the
phrase followed by a version number. The digit is load-bearing: all five
docs are still allowed to quote the prohibition ("... is X"), and they
do. `test_the_published_claim_pattern_is_not_vacuous` is the positive
half, and also holds that the prohibition sentences stay legal, so
nobody can "tighten" the pattern into forcing them out. Archives and the
frozen audit artifacts quote the finding itself and are deliberately out
of scope.

| Break | Test that went red |
| --- | --- |
| `The latest published release is 0.6.6.` put back into `README.md` | `VersionStringPins.test_no_live_doc_hardcodes_a_latest_published_release` (on `README.md hardcodes a published-release claim`) |
| the pattern made to match nothing | `VersionStringPins.test_the_published_claim_pattern_is_not_vacuous` |

## Candidate attempt 37625977035 — what the pipeline caught

The first `notarize=true, publish=false` candidate was dispatched from
`0e6f11a` and **failed three jobs**. None of the three is in wallet,
signing or broadcast code. All three are release plumbing that only a
real three-platform run can reach, which is what the candidate stage is
for. This run is **superseded**; its record is kept rather than erased.

| Job | Failure | Cause |
| --- | --- | --- |
| Windows x64 bundle | 4 `PublishPathSweepTests` failures | `scripts/check-publish-paths.sh` read each workflow body with `git show ref:path 2>/dev/null \|\| true` and matched it with `grep`. On the Windows job that read returned nothing, the `\|\| true` swallowed it, and a branch that publishes was reported clean. The filename check is pure bash and passed there — which is exactly why the body checks looked fine on Mac and Linux. |
| Source archive and tests | `FileNotFoundError` on `.github/workflows/windows-inputs.yml` | `ToolchainPinTests` opened only `.github/workflows/`. The source tarball ships the same recipes under `ci/` (`scripts/build-source.sh`). The **0.6.6** job already caught `PipToolsPinTests` making this exact mistake; the fix was local to that one test, so the next pin repeated it. |
| Apple Silicon DMG | `codesign` refused to seal the `.app` | `hwi.sha256` was written into `Contents/MacOS/`, which macOS reserves for executables: `code object is not signed at all / In subcomponent: .../Contents/MacOS/hwi.sha256`. |

The Windows job also ran **493** tests where macOS ran 500. That gap is
deliberate and documented in `tests/test_notary_args.py`: seven
`@macos_only` cases "are not collected" on other platforms rather than
skipped, so the workflow's `skipped=[1-9]` guard stays meaningful. The
Linux job and the source-archive job run the same 493. Nothing is
silently omitted.

### Fixes

1. **`scripts/check-publish-paths.sh`** — the body now comes from
   `git cat-file blob <oid>` (the object id `git ls-tree` already reports),
   not from `git show ref:path`. An unreadable body is itself an offender
   (`unreadable-workflow`), never a pass. Matching is `[[ ]]` under
   `nocasematch`; there is no `grep` in the script at all, so a missing or
   broken matcher can no longer turn a refusal into silence.
2. **Recipe lookup** — `support.find_build_recipe` is the one resolver,
   checking `.github/workflows/` then `ci/`. `ToolchainPinTests`,
   `PipToolsPinTests` and `test_libusb_vendor` all use it;
   `HardeningPinPortabilityTests` holds that none of them reopens an
   inline lookup. This closes the loop 0.6.6 left open.
3. **`scripts/build-macos.sh`** — the sidecar is written to
   `Contents/Resources/hwi.sha256`, which is legal *and* better: the outer
   signature seals it into `_CodeSignature/CodeResources`, so editing it
   breaks the seal exactly like substituting the helper.
   `probe._hwi_sidecars` and `build_sbom.helper_sidecars` list the same
   places (beside the helper, then `Contents/Resources`) and every present
   copy must agree with the helper's bytes. `HWI-DEPENDENCY.md` now says
   where the sidecar actually lives; its old "beside it" wording would
   have been a lie after this change.

### Tripwires for the fixes (`/tmp/breakwatch_067c.py`, 10/10)

| Break | Test that went red |
| --- | --- |
| body read swallows its failure again (`\|\| true`) | `SweepFailClosedPins.test_the_body_read_is_not_allowed_to_swallow_its_failure` |
| `unreadable-workflow` offender dropped | `SweepFailClosedPins.test_an_unreadable_workflow_body_is_an_offender` |
| write-permission regex never matches | `PublishPathSweepTests.test_the_sweep_refuses_a_remote_branch_carrying_a_release_job` |
| body read back to `git show ref:path` | `SweepFailClosedPins.test_the_bodies_come_from_object_ids_not_from_rev_colon_path` |
| bodies matched with `grep` again | `SweepFailClosedPins.test_the_sweep_matches_bodies_with_bash_and_not_with_grep` |
| every `build-candidate.yml` flagged as retired | `PublishPathSweepTests.test_the_sweep_accepts_a_repo_whose_only_publisher_is_main` |
| sidecar written back to `Contents/MacOS` | `HelperDigestPins.test_the_macos_sidecar_is_written_outside_contents_macos` |
| `probe` stops looking in `Contents/Resources` | `HwiIdentityPins.test_a_frozen_macos_bundle_reads_the_sidecar_from_contents_resources` |
| recipe lookup only `.github/workflows` again | `BuildRecipeLookupTests.test_a_recipe_shipped_only_under_ci_is_found` |
| `build-sbom` looks beside the helper only | `HelperDigestPins.test_the_sbom_reads_the_sidecar_from_the_place_the_app_checks` |

Every case: positive half green → one unique needle broken → named test
red **for the assertion's own message** → restore → green. `__pycache__`
is cleared before every run.

Two of those ten were wrong on the first pass, and both were caught
rather than waved through:

- "drop the `unreadable-workflow` offender" went red, but on the second
  assertion, not the first — the word still appeared in the script's
  comment. The harness was checking for the wrong string. Re-aimed.
- "make the write-permission regex never match" left the test **green**,
  because that fixture carries both `contents: write` and `gh release`
  and the other marker still refused. A real gap in the test, not in the
  harness: the combined fixture could not tell the two markers apart.
  `test_the_sweep_refuses_a_remote_branch_carrying_a_release_job` now
  asserts `grants-contents-write`, the gh-release-only test asserts
  `runs-gh-release`, and the retired-name test asserts
  `retired-per-platform-publisher`. The break then goes red on the
  reason named. The same lesson as CT-50–53: **assert the specific
  refusal, not just that something refused.**

The existing suite also caught the recipe-lookup refactor: moving the
`ci/` fallback into `support.find_build_recipe` broke
`test_piptools_pin_looks_in_ci_as_well_as_github_workflows`, which pinned
the old inline strings. That pin now holds the shared helper instead —
it went red on the refactor, which is what it is for.

## Candidate attempt 37632918993 — one test that could not run

The second `notarize=true, publish=false` candidate was dispatched from
`60f5785`, the commit that carries the three fixes above. **Four of the
five jobs were green**: Read version (whose publish-path sweep ran
against the live remote and reported clean), Source archive and tests,
Apple Silicon DMG, and Linux x86_64 AppImage. SHA256SUMS and Publish
release were skipped, so nothing was published.

Only **Windows x64 bundle** failed, on exactly one test — and it was a
test written for the previous fix, not a control.

| Job | Outcome | Detail |
| --- | --- | --- |
| Read version | success | `check-publish-paths.sh` ran against `origin` and found no publish-capable workflow on any non-main ref |
| Source archive and tests | success | the `ci/` recipe lookup fix held; the suite ran from inside the tarball |
| Apple Silicon DMG | success | the `Contents/Resources` sidecar sealed under codesign |
| Linux x86_64 AppImage | success | — |
| Windows x64 bundle | **failed (errors=1)** | 506 collected, 505 ok. `HwiIdentityPins.test_a_frozen_macos_bundle_reads_the_sidecar_from_contents_resources` raised `OSError: [WinError 193] %1 is not a valid Win32 application` |

### Cause

The test planted a helper as an unconditional `#!/bin/sh` script and then
called `_verify_hwi_identity`, which runs `[path, "--version"]`. Windows
CreateProcess cannot exec a shebang script — WinError 193 — so the test
failed on the platform difference and never reached the sidecar-lookup
control it exists to pin. The same file's `_planted_helper` already
solved this ("Windows CreateProcess cannot exec a shebang script
(WinError 193), so the planted helper must be a real `.cmd` there and a
shell script elsewhere"); the new test did not use it.

This is a **defect in the test, not in the control**. The controls it
pins — the `Contents/Resources` sidecar lookup, and the rule that every
present sidecar must agree with the helper's bytes — were exercised and
passed on macOS and Linux and in the source-archive run. Every
publish-path sweep test passed on Windows. The suite did its job: it
refused to call a green run green.

### Fixes

1. **One platform-aware writer.** `_write_planted_helper` is now the only
   place that decides what a planted helper looks like: `hwi.cmd` with
   `@echo off` on `win32`, `#!/bin/sh` elsewhere. `_planted_helper` and
   both bundle-layout tests call it. A test can no longer plant a helper
   this platform cannot execute by copying the wrong shape by hand.
2. **A pin on the plant itself.**
   `test_the_planted_helper_is_whatever_this_platform_can_execute`
   patches `sys.platform` to each of `win32` and `darwin` and asserts the
   name, the body, and the absence of a shebang in the Windows shape.
   This is the test that would have caught the mistake before dispatch,
   and it runs on **every** runner — a Windows machine is not required to
   notice that the plant stopped changing shape.
3. **An overclaiming test, corrected.**
   `test_two_sidecars_that_disagree_about_the_helper_are_refused` said
   "both present copies are checked" but never presented two: it copied
   the helper bytes into a fake `Contents/MacOS` and wrote the wrong
   digest only in `Resources`, so nothing sat beside the helper and the
   gate saw a single record. It now writes a **correct** sidecar beside
   the helper and a **wrong** one in `Contents/Resources`, asserts both
   are found, and leaves the correct copy first in the lookup order on
   purpose — so a gate that stops at the first match, or that accepts any
   single match, goes red here rather than slipping through. The positive
   half is new: `test_two_sidecars_that_agree_about_the_helper_are_both_believed`
   proves agreement across the two locations is not itself a refusal.

   This is the same lesson as CT-50–53 and as the write-permission regex
   above: **a test whose fixture does not exercise what its docstring
   claims is a finding**, not a green.

### Tripwires for the fixes (`/tmp/breakwatch_067d.py`, 4/4)

| Break | Test that went red |
| --- | --- |
| `probe._hwi_sidecars` stops looking in `Contents/Resources` | `HwiIdentityPins.test_a_frozen_macos_bundle_reads_the_sidecar_from_contents_resources` (on the list comparison: `[] != [.../Resources/hwi.sha256]`) |
| `_verify_hwi_bytes` accepts the first sidecar that matches | `HwiIdentityPins.test_two_sidecars_that_disagree_about_the_helper_are_refused` (on the named digest refusal) |
| `_verify_hwi_bytes` refuses every helper with two records | `HwiIdentityPins.test_two_sidecars_that_agree_about_the_helper_are_both_believed` (on the named digest refusal) |
| the plant writes a shell script whatever the platform says | `HwiIdentityPins.test_the_planted_helper_is_whatever_this_platform_can_execute` (on `hwi.cmd` vs `hwi`) |

Same rule as before: positive half green → one unique needle broken →
named test red **for the assertion's own message** → restore → green.
`__pycache__` cleared before every run. Two of the four were wrong on the
first pass and were corrected rather than waved through: the harness
asked for the `ProbeError` text where the test actually fails on the
lookup list, and asked for "not raised" where the failure is the named
refusal not matching. The tests themselves were right; the harness was
checking the wrong strings.

## Candidate attempt 37637171599 — the refusal that never arrived

The third `notarize=true, publish=false` candidate was dispatched from
`3f6dfe6`, the commit carrying the Windows test fix. **Four of the five
jobs were green again** — Read version, Source archive and tests, Apple
Silicon DMG, Linux x86_64 AppImage — and **Windows failed on one
different test**: `test_gui.LocalGuiTests.test_import_rejects_bad_chain_and_cross_origin_post`,
with `ConnectionAbortedError: [WinError 10053] An established connection
was aborted by the software in your host machine`. 508 collected, 507 ok.

`gui.py` and `tests/test_gui.py` had not changed between the two runs,
and this test **passed** on Windows in run 37632918993. It is not a
regression. It is a race the Windows socket stack resolves differently
depending on load.

### Cause

`do_POST` answers a refusal **without consuming the request body**. The
client is still writing when the connection closes. Closing a socket that
still has unread data sends a reset, and a reset discards the response
the server just wrote: POSIX usually delivers the status line first and
`urlopen` raises a clean `HTTPError`; Windows aborts the socket and the
refusal never arrives.

Two refusals were exposed, both raised before `self.rfile.read`:

1. the gate (`403 Local access only`) for a cross-origin or untokened
   POST — the one that failed;
2. the size-and-type check (`400 Wallet request is too large or
   malformed`), which `test_oversized_requests_are_refused_before_parsing`
   exercises.

The test's first two POSTs are refused **after** the body is read (they
reach `_import` and fail the chain check), so those 400s always arrived.
That is why the failure looked random: it is a race between the client's
`send()` and the server's close, and a loaded Windows runner loses it.
`gui.py` had not changed between the two Windows runs, and this test
**passed** in the earlier one.

### This is not a weakening of the gate

The accept/reject decision is unchanged. A cross-origin request is still
refused; from the attacker's side a connection abort and a 403 are both
"nothing came back". What changed is that the refusal is now
**deliverable** — the operator's own client, and the test, can observe
which rule fired. `_drain_body` discards the body unread, so nothing it
reads is parsed.

### Fixes

1. **`gui.py::_drain_body`** — discard the request body before answering
   a refusal. Bounded at twice the request cap: a declaration that runs
   far past the cap is hostile, and a refusal is allowed to leave that
   client with a transport error rather than spend the app's time reading
   it. `do_GET`'s refusal is untouched (a GET has no body).
2. **Both refusal sites drain** — the gate's `403` and the size-and-type
   `400`.
3. **`tests/test_gui.py::RefusalDeliveryPins`** — asserts the exact
   ordered form `self._drain_body()` immediately before *each* refusal,
   so a drain that lands after the response, or on only one of the two,
   cannot satisfy it; and asserts the drain is bounded and honours
   `Content-Length`.
4. **`WINDOWS-PORT.md`** — the quirk is recorded beside the others
   (`WinError 10053` for an unread body, `WinError 193` for a shebang
   helper) with the required approach and the pin that holds it.

Scoped review, per `RELEASE-PROCESS.md` §3 ("do not change … another
safety invariant without a scoped review and regression tests"): the
change is confined to how a *refusal* is delivered, does not alter any
accept/reject condition, is bounded, and carries the regression tests
above plus the existing `test_import_rejects_bad_chain_and_cross_origin_post`
and `test_oversized_requests_are_refused_before_parsing`, each of which
asserts its specific status code and error text.

### Tripwires for the fixes (`/tmp/breakwatch_067f.py`, 3/3)

| Break | Test that went red |
| --- | --- |
| the drain dropped from the gate refusal | `RefusalDeliveryPins.test_a_refused_post_consumes_the_request_body_before_it_answers` (gate form) |
| the drain unbounded | `RefusalDeliveryPins.test_the_drain_is_bounded_so_being_refused_cannot_read_forever` |
| the drain dropped from the size-and-type refusal | `RefusalDeliveryPins.test_a_refused_post_consumes_the_request_body_before_it_answers` (size-and-type form) |

The behavioural tests cannot demonstrate the race on a POSIX machine —
that is the whole point of the quirk — so the pin is the exact-form
assertion, which fails on every runner.

## Candidate attempt 37642017337 — the job that never started

Commit `fa017d3`, dispatched `notarize=true, publish=false`, 2026-10-07
15:04 UTC. All five build jobs succeeded:

| Job | Conclusion |
| --- | --- |
| Read version | success |
| Windows x64 bundle | success |
| Linux x86_64 AppImage | success |
| Source archive and tests | success |
| Apple Silicon DMG | success |
| SHA256SUMS | **never created** |
| Publish release | skipped |

The run's overall conclusion is **failure**.

### Cause

Not a defect in the tree. `git diff a30d6dc fa017d3 -- .github/workflows/`
is empty — the workflow bytes are identical to commit `a30d6dc`, whose run
(37640731184) created the `SHA256SUMS` job and completed all seven. The
`checksums` job declares `needs: [version, source, macos, windows, linux]`
with no job-level `if`, and every one of those five concluded `success` —
and the job was never scheduled. It is absent from the jobs list entirely,
neither skipped nor failed. `gh run view --log-failed` is empty because no
step failed: there was no step.

GitHub Actions failed to create the job. `run_attempt` is 1 and the event is
`workflow_dispatch`, so this is not a retry and not a concurrency cancel.

### This is not a near-miss that can be promoted

A run whose build jobs are green is not a candidate. The candidate is the
manifest: `checksums` writes `SHA256SUMS`, and the release job binds it to
the run ID and commit in `CANDIDATE-MANIFEST.txt`. Neither exists here. The
promotion path would have failed closed regardless — `release` downloads a
`release-assets` artifact that only `checksums` produces, so `publish=true`
against this run would have found nothing to publish. The control held.

The narrower lesson is worth stating, because it is the same blindness the
publish-path sweep was written to end: **an absent job looks like a success
to anyone reading only the green build rows.** The only acceptable evidence
that a candidate is usable is the `SHA256SUMS` job concluding `success` —
not five builds in a row.

## Three comments that disagreed with the code

Found while preparing this revision's publication record. None changed a
control; each described one inaccurately. The audit framework treats that as
a finding in its own right — cycle 3 was blocked in part by a false "no
second path can attach bytes to a release" comment.

1. **`probe.py`, `_verify_hwi_identity`** said a standalone helper "must
   match the digest recorded beside it". A frozen macOS bundle keeps its
   sidecar in `Contents/Resources` — the whole reason `_hwi_sidecars` looks
   in two places and `_verify_hwi_bytes` requires every present sidecar to
   match. The comment described a rule weaker than the code runs, on the
   money-adjacent helper-identity control. Reworded to name the multi-sidecar
   rule and where a frozen bundle keeps it.
2. **The audit plan, section 0** enumerated the tripwires
   `(CT-48/49/…/62)` beside a reference to `releases/PATCH-0.6.7.md` — a
   snapshot that had already drifted, since that file also carries CT-71 and
   the refusal-delivery pins. The sentence's own rule is "every tripwire
   listed in `releases/PATCH-0.6.7.md`"; the enumeration contradicted it.
   Dropped, so the list lives in one file and cannot drift from the pins the
   repository carries.
3. **`RELEASE-PROCESS.md` §2** said "Record the successful candidate run ID"
   as a step before promotion. Followed literally that record is a commit on
   `main` between the candidate dispatch and the publish dispatch, which
   breaks the same-commit promotion contract the same document states a few
   paragraphs later. Reworded: note the ID for the publish dispatch, and
   write it into the patch record only after publication.

### Tripwires (`/tmp/breakwatch_067g.py`, 2/2)

| Break | Test that went red |
| --- | --- |
| the stale "recorded beside it" claim reintroduced | `HwiIdentityPins.test_the_identity_docstring_names_every_sidecar_it_actually_reads` (refusal half) |
| the multi-sidecar rule dropped from the docstring | `…test_the_identity_docstring_names_every_sidecar_it_actually_reads` (presence half) |

Only the first of the three is pinned, deliberately. It is the one
describing a money-adjacent control, so an edit that re-narrows the comment
goes red on every runner. The other two are prose in documents the referee
reads at the tag; the behaviour they describe is pinned by
`tests/test_workflow_config.py` and by the promotion path's own artifact
checks.

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
(CT-61, CT-63–70). It records the CT-54 and CT-59 deferrals above. For the
acceptances where a later code change could silently erase the rationale it
names an explicit reopening tripwire, and for the rest it states the design
property the acceptance rests on; the note itself says a future note should
carry its own tripwires in that section (CT-104). It is not used to close
anything that was fixed in code.

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

At this revision: full suite **520 tests OK, zero skips**, run both from
the checkout and from inside the extracted
`dist/bitcoin-easy-multisig-signer-v0.6.7.tar.gz` — the same self-test the
source job performs, and both runs collect the same count, so the tarball
is complete. 10/10 `tests/ui_*.cjs` OK. `bash -n` clean on every
`scripts/*.sh`. `node --check` clean on every test and script. The
break-and-watch transcripts above hold 10/10 for the first candidate
attempt, 4/4 for the second, 2/2 for the CT-71 pin, 3/3 for the refusal
delivery, and 2/2 for the identity docstring.

Count by platform, so a reader is not surprised: **macOS collects 520**;
**Linux and Windows collect 513**. The difference is deliberate and
documented in `tests/test_notary_args.py`: seven `@macos_only` cases "are
not collected" on other platforms rather than skipped, so the workflows'
`skipped=[1-9]` guard stays meaningful and a missing dependency cannot
hide behind a skip. Each platform's job runs its own full set with no
skips. The failed Windows runs above collected 506 and 508 at revisions
where macOS collected 513 and 515 — same rule, seven fewer.

Earlier in this revision's history the suite stood at 500 tests at
`d2e9e73`; the twenty added since are the tripwires written for the
candidate attempts above and for the three comment corrections.

## Publication

**Published 2026-10-07** as tag `v0.6.7` = `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b`,
through the unified pipeline and nothing else.

- Candidate [37644267740](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37644267740)
  — `notarize=true, publish=false` from `81f58ec`, all seven jobs green,
  `CANDIDATE-MANIFEST.txt` written.
- Owner hardware acceptance: the owner installed the candidate DMG from that run
  on 2026-10-07, ran a practice-network payment with hardware signers, and
  reported the build good. Owner-reported physical acceptance; no transaction
  identifier, diagnostic file or wallet material is recorded anywhere in this
  repository. CT-49/CT-58 changed the device-identity path, which is why this
  gate stood before promotion.
- Promotion [37655666900](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37655666900)
  — `notarize=true, publish=true, candidate_run_id=37644267740`, dispatched from
  the **same commit** `81f58ec`. All seven jobs green.

### Post-publication verification (RELEASE-PROCESS.md §3)

Checked independently after the publish run, against the public release page:

| Check | Result |
| --- | --- |
| Tag points to the commit named by the publishing run | `v0.6.7` → `81f58ec…`, equal to the publish run's `head_sha` and to the candidate run's `head_sha` — same-commit promotion holds |
| Every public asset downloaded for all three platforms | 10 assets: source tarball, macOS DMG, Windows zip, Linux AppImage + Linux tar.gz, three `BUILD-SBOM.json`, `SHA256SUMS`, `SHA256SUMS.asc` |
| Published `SHA256SUMS` verified | `shasum -a 256 -c SHA256SUMS` — 8/8 **OK** |
| `SHA256SUMS.asc` verified against the committed `signing-key.asc` | **Good signature** from `Bitseeker LLC <release@bitseeker.llc>`, RSA key `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7` |
| Sigstore attestation on an asset | `gh attestation verify` on the macOS DMG — **2 attestations**, both bound to `build-candidate.yml@refs/heads/main` |
| Release is neither draft nor prerelease | `draft=false prerelease=false`, published 2026-10-07T17:10:37Z |

No tag or asset was moved, replaced, or deleted. The candidate and the published
DMG are the same bytes — the owner tested `0f9043c8…a015`, which is the digest
`SHA256SUMS` records.

### Candidate history

| Run | Commit | Dispatch | Outcome |
| --- | --- | --- | --- |
| [37625977035](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37625977035) | `0e6f11a` | `notarize=true, publish=false` | **Superseded — failed.** Three jobs: Windows (sweep went blind on unreadable bodies), source archive (pin test opened only `.github/workflows/`), macOS (sidecar in `Contents/MacOS` broke codesign). Fixed in the next commit; see *Candidate attempt 37625977035* above. No assets were published; SHA256SUMS and Publish release were skipped. |
| [37632918993](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37632918993) | `60f5785` | `notarize=true, publish=false` | **Superseded — failed.** Windows only: one test could not run (`WinError 193` planting a shebang helper). The other four jobs were green, including the live-remote publish-path sweep. Fixed in the next commit; see *Candidate attempt 37632918993* above. No assets were published; SHA256SUMS and Publish release were skipped. |
| [37637171599](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37637171599) | `3f6dfe6` | `notarize=true, publish=false` | **Superseded — failed.** Windows only: one test lost a socket race (`WinError 10053`) because a gate refusal answered without reading the request body. Four jobs green. Fixed in the next commit; see *Candidate attempt 37637171599* above. No assets were published; SHA256SUMS and Publish release were skipped. |
| [37640731184](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37640731184) | `a30d6dc` | `notarize=true, publish=false` | **Superseded — passed.** All seven jobs green, including SHA256SUMS and the candidate-side Publish release (manifest written, nothing published). Not walked through and not promoted: a follow-up hardening commit landed first, to drain the request body at the second refusal site too. |
| [37642017337](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37642017337) | `fa017d3` | `notarize=true, publish=false` | **Superseded — failed.** All five build jobs green; the SHA256SUMS job was **never created** and Publish release was skipped, so the run concluded failure. Not a tree defect — the workflow is byte-identical to `a30d6dc`, whose run completed all seven. See *Candidate attempt 37642017337* above. No assets were published. |
| [37644267740](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37644267740) | `81f58ec` | `notarize=true, publish=false` | **The candidate.** All seven jobs green; `SHA256SUMS` job present and successful; `CANDIDATE-MANIFEST.txt` written. Owner installed this run's DMG and accepted it on hardware. |
| [37655666900](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37655666900) | `81f58ec` | `notarize=true, publish=true, candidate_run_id=37644267740` | **Published — `v0.6.7`.** All seven jobs green. Tag created at the same commit as the candidate; every asset verified, `SHA256SUMS.asc` signed by the release key, Sigstore attestation attached to every asset. |

Do not claim a published version this file does not carry.

Do not claim a published version this file does not carry.

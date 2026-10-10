# 0.6.8: Color Team cycle-4 remediation

Version 0.6.8 answers the cycle-4 Color Team audit of the `v0.6.7` tree
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-d525f31.md`). The
cycle's finding set is worked through in `releases/PLAN-0.6.8.md`; this
ledger records, item by item, what changed and the test that was watched
failing without it.

The cycle-4 grade was set on the build process again: what the release
workflows install, and what they leave unchecked. The wallet,
transaction, signing and broadcast engine is unchanged apart from the
hardening items below. No new payment capability is added.

## Finding → fix → test

Every row below is closed either by a test demonstrated able to fail or
by a dated owner acceptance note. Nothing is closed by silence.

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-72 | High | The candidate-run-id guard interpolated a free-text workflow input straight into the `run:` script at `.github/workflows/build-candidate.yml:69` *(v0.6.7)* — `if [[ ! "${{ inputs.candidate_run_id }}" =~ ^[0-9]+$ ]]` — so GitHub substituted the payload before bash parsed the line, and all three lanes demonstrated command execution, including Amber's `$(touch /tmp/PWNED2; printf 12345)` which ran the payload and *passed* the guard. The value now travels through `env:` (`CANDIDATE_RUN_ID: ${{ inputs.candidate_run_id }}`, `.github/workflows/build-candidate.yml:70`) and is read as `[[ ! "$CANDIDATE_RUN_ID" =~ ^[0-9]+$ ]]` (`:76`). Every other `${{ }}` inside a `run:` body was routed the same way, and an M2 lint refuses a re-interpolated body. | `tests/test_publish_guards.py::CandidateRunIdInjectionTests::test_a_command_substitution_payload_does_not_run`, `…::test_a_payload_that_also_makes_the_guard_pass_does_not_run`, `…::test_a_quote_breaking_payload_does_not_run`, `…::test_the_guard_step_is_actually_reached`, `…::test_a_non_numeric_candidate_run_id_is_refused`; `tests/test_publish_guards.py::InterpolationLintTests::test_no_run_body_interpolates_a_github_expression`; break-and-watch: 17 defeats, each green first — `candidate_run_id goes back into the script text` → `…::test_the_step_that_uses_each_expression_still_receives_it`, plus the guard defeats listed under CT-74/CT-75 |
| CT-73 | High (referee: Med) | `probe.py:211-214` *(v0.6.7)* pinned only `hwilib/__init__.py` and `hwilib/_cli.py` (2 of the 115 `.py` files in the installed package), and `_verify_hwi_payload()` (`:311-348`) hashed exactly those two although its docstring (`:317`) claimed "a poisoned site-packages is refused rather than believed". A poisoned `hwilib/devices/trezor.py` passed the check and ran on `import hwilib._cli` / `scripts/hwi_entry.py:109`. `scripts/build-hwi-manifest.py` now records every regular file of the installed package (excluding `__pycache__`/`.pyc`) into the committed `vendor/hwi-payload-3.2.0.json`, and `probe.py:418` `_verify_hwi_payload` refuses a package with a missing, added or changed file; each platform build gates on the manifest before bundling and the tarball ships it. | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_poisoned_package_is_refused_on_real_bytes`, `…::test_a_poisoned_entry_module_is_refused_before_it_runs`, `…::test_the_manifest_covers_the_whole_payload_not_two_files`, `…::test_the_manifest_tool_refuses_a_stale_manifest`, `…::test_every_platform_build_gates_on_the_manifest`; break-and-watch: 21 defeats caught, baseline 21 test ids green — `payload manifest check reduced to the two entry pins`, `payload check imports the package it is checking`, `manifest staleness comparison neutered`, `a build stops gating on the manifest` |
| CT-74 | High | The version-job refusal `if: ${{ inputs.publish && !inputs.notarize }}` (`build-candidate.yml:57-61` *(v0.6.7)*), the release-job body check (`:738`) and the manifest notarize grep (`:978-981`) were pinned as text, not behaviour: `if: ${{ false }}`, `!= "true"` → `== "impossible-value"` and `grep … \|\| true` each left `tests/test_workflow_config.py` green (`Ran 55 tests … OK`). M1 (`tests/workflow_harness.py`) now renders a step the way the runner does — expressions from a context, `if:` evaluated, `env:` built, body run under `bash -e` with scripted `gh`/`git`/`gpg`/`jq` — and every guard is an outcome case under `tests/test_publish_guards.py::ReleaseGuardBehaviourTests`, with the old `GuardBodyPins` string pins kept as the first layer. | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_the_unsigned_release_guard_runs_exactly_on_publish_without_notarize`, `…::test_the_unsigned_release_guard_refuses_and_names_the_reason`, `…::test_an_unnotarized_publish_is_refused`, `…::test_the_publish_path_requires_the_signature_and_the_public_key`; break-and-watch: 17 defeats, each green first, e.g. `unsigned-release guard disabled` and `unnotarized-publish guard inverted` |
| CT-75 | Med | The tag guard (`build-candidate.yml:986-996` *(v0.6.7)*), both `shasum -a 256 -c SHA256SUMS` sites (`:747`, `:844`), the candidate-binding `jq` `(.conclusion == "success" or true)` (`:710-713`) and the main-ref `exit 1` (`:65-68`) were defeated — inverted comparison, `\|\| true`, `or true`, deleted refusal — while all 55 workflow tests stayed green. The M1 harness converts each into a behaviour case (`ReleaseGuardBehaviourTests`), so the guard's *effect* is asserted and not its spelling; where state must be supplied (e.g. `git ls-remote` tag state) a stub supplies it and the case asserts the branch taken and the refusal text. | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_a_tampered_asset_fails_the_checksum_verification`, `…::test_the_publish_path_verifies_the_signature_and_refuses_a_bad_one`, `…::test_an_existing_tag_is_never_overwritten`, `…::test_an_unverifiable_tag_state_refuses_publication`, `…::test_a_notarized_publish_of_an_absent_tag_reaches_the_release_command`, `…::test_a_candidate_writes_a_manifest_and_publishes_nothing`; break-and-watch: 17 defeats, each green first |
| CT-76 | High | `scripts/check-publish-paths.sh:61` *(v0.6.7)* fetched `+refs/heads/*` only, so tags were never scanned even though the header claimed "on any ref", and tags `v0.1.11`–`v0.1.23` still froze delete-and-replace publish text with no main-branch requirement; a fixture tag carrying a `contents: write` publisher printed `ok: no non-main ref carries a publish-capable workflow` and exited 0. The sweep now fetches `+refs/tags/*` into their own namespace (`scripts/check-publish-paths.sh:132`; heads at `:131`) and applies an allowlist — only `main`, and only `build-candidate.yml` on `main`, may carry publication; a tag is judged by what it can do from its own ref (a guarded tag is inert, the pre-guard tags are an enumerated accepted residual, any other tag is an offender). | `tests/test_workflow_config.py::PublishPathSweepTests::test_the_sweep_refuses_a_tag_carrying_an_unguarded_publisher`, `…::test_the_sweep_accepts_an_enumerated_legacy_tag`, `…::test_the_sweep_accepts_a_tag_whose_publisher_refuses_off_main`, `…::test_the_sweep_fetches_tags_into_their_own_namespace`, `…::test_the_sweep_refuses_a_second_publisher_on_main`, `…::test_the_sweep_accepts_main_publishing_through_the_one_named_file`; break-and-watch: 17 defeats, each green first, incl. `tag refs are never checked` and `main allowlist stops naming the publisher` |
| CT-77 | High | The sweep recognised only the literal `contents:[ ]?write` (`check-publish-paths.sh:48-49` *(v0.6.7)*) and the substring `gh release` (`:102-108`), so a branch with `permissions: write-all` and `gh api -X POST "repos/$GITHUB_REPOSITORY/releases"` printed "ok"; `curl -X POST …/releases`, `softprops/action-gh-release@v1` and `actions/create-release` were invisible too. The denylist is inverted to an allowlist with `CONTENT_WRITE_RE` (`scripts/check-publish-paths.sh:104`), `WRITE_ALL_RE` (`:106`) and `RELEASE_SURFACE_RE` (`:111`, `/releases\|action-gh-release\|create-release`); whole-line comments are skipped and never truncated, so prose cannot flag a file and a `#` cannot hide code. | `tests/test_workflow_config.py::PublishPathSweepTests::test_the_sweep_refuses_a_branch_granting_write_all`, `…::test_the_sweep_refuses_a_branch_that_posts_to_the_rest_api`, `…::test_the_sweep_refuses_a_branch_using_a_release_action`, `…::test_the_sweep_ignores_a_workflow_whose_only_match_is_a_comment`, `…::test_the_sweep_still_flags_a_pattern_after_a_hash_on_a_code_line`; break-and-watch: 17 defeats, each green first, incl. `write-all matcher neutered`, `second-publisher-on-main rule dropped`, `comment stripping removed`, `unreadable body reported as clean` |
| CT-78 | Med | Every case in `tests/test_network_settings.py` built its expectation from `NETWORKS` itself, so swapping `network_config.py:48` *(v0.6.7)* mainnet genesis for true Signet's (`00000008819873e925422c1ff0f99f7cc9bbb232af63a077a480a3633bee1ef6`) agreed with the suite, and a mocked Signet explorer passed `verify_esplora("main", …)`; the Mutinynet block-1 checkpoint (`:43`) was likewise unasserted. The four published constants (mainnet and testnet4 genesis, Mutinynet genesis and its block-1 checkpoint) are now pinned verbatim, the network-to-genesis mapping is asserted exclusive, and a Signet answer to a mainnet check is refused. | `tests/test_network_settings.py::PublishedChainConstantsTests::test_the_published_chain_constants_are_pinned_verbatim`, `…::test_the_network_to_genesis_mapping_is_exclusive`, `…::test_a_signet_genesis_is_not_accepted_as_mainnet`; break-and-watch: 24 defeats caught (was 22) — `mainnet genesis swapped for Signet's`, `the Mutinynet block-1 checkpoint is dropped` |
| CT-79 | Med | `not bare_receive_only` in `wallet_service.py:313` *(v0.6.7)* (`standard_candidate = not declared and not bare_receive_only and _standard_bip48(record)`) is what stops a bare `/*` that matches `xpub/0` from enabling an inferred `/1/*` change branch; all 16 cases in `tests/test_change_branch.py` used a reference at `xpub/0/0`, where the branch is unreachable, so deleting the guard left the file green. A new case builds the shape the guard exists for (reference at `xpub/0`) and asserts `change is None`; the `AGENTS.md:23` invariant is pinned inline at the guard, now `wallet_service.py:330`. | `tests/test_change_branch.py::ChangeBranchTests::test_bare_wildcard_reference_at_the_branch_root_never_infers_change`; break-and-watch: 24 defeats caught (was 22), baseline 24 test ids green — `bare-receive-only wallets may infer standard change`; with the guard deleted the new case fails while the old 16 pass |
| CT-80 | High | At the audited tag `81f58ec` no job declared `environment:` (`grep -c 'environment:'` = 0, workflow-level `contents: read`), so no `MAC_*` or `GPG_*` name could resolve there — yet runs #106/#107 signed, notarized and GPG-signed on 2026-10-07: the credential wiring that made publication work lived on the platform and in no revision. Current `main` declares `environment: apple-signing` (`.github/workflows/build-candidate.yml:189`) and `environment: release-signing` (`:775`); `tests/test_platform_state.py` asserts every secret name a job reads is declared by the environment that job names (with `MAC_NOTARY_KEY_P8_BASE64` proved optional by a real `else` route holding a declared credential), and `releases/platform-state.json` plus `scripts/check-platform-state.sh` record and re-read the live platform, refusing on any unobserved state. | `tests/test_platform_state.py::WorkflowWiringTests::test_every_referenced_secret_is_declared_by_the_job_environment`, `tests/test_platform_state.py::PlatformRecordTests::test_the_record_declares_exactly_the_five_expected_secret_names`, `…::test_the_signing_environments_are_pinned_to_main_with_no_reviewers`, `tests/test_platform_state.py::PlatformCheckScriptTests` (11 tests), `scripts/check-platform-state.sh`. Break-and-watch: all 29 mutations caught by their named tests — dropped platform secret, a differ that stops comparing, an unauthenticated `gh` that no longer stops the read, a job reading secrets without naming its environment, a record that stops shipping |
| CT-81 | Low | A non-ASCII `X-Local-Token` made `hmac.compare_digest` raise `TypeError: comparing strings with non-ASCII characters is not supported` inside the comparison at `gui.py:638` *(v0.6.7)*, so the connection died with a traceback and the caller never received the ordinary 403. `_token_matches()` (`gui.py:604`) now encodes both sides as UTF-8 first, so the comparison is over bytes, stays constant-time, and every non-ASCII or malformed value is a plain mismatch. | `tests/test_gui_integration.py::LocalServerAccessTests::test_a_non_ascii_token_header_is_refused_without_a_traceback`; break-and-watch: all 31 mutations caught — `a non-ascii token header raises instead of refusing` (the comparison back on raw `str`) |
| CT-82 | Low | The only pin was that a wrong token is refused (`tests/test_gui_integration.py:151-153` *(v0.6.7)*), so a comparison accepting any prefix — `state.token.startswith(header)`, a last-six-characters test — stayed green. `LocalTokenComparisonTests` now walks empty, one-character-short, one-character-long, the first six characters, the last six characters, both one-sided truncations, a single substituted character and a doubled value, each expected 403, and pins `hmac.compare_digest` over the two UTF-8 encodings. | `tests/test_gui_integration.py::LocalTokenComparisonTests::test_every_near_miss_of_the_token_is_refused`, `…::test_the_comparison_is_whole_value_and_constant_time`; break-and-watch: all 31 mutations caught — `the token comparison accepts a six-character prefix` |
| CT-83 | Med | The release job held `permissions: contents: write` with no job-level `if:`, and the publish decision was made inside its last step (`build-candidate.yml:828-834` *(v0.6.7)*), so a `publish=false` candidate dispatch also carried the repository write grant. The grant is split across two jobs: `candidate-manifest` (`contents: read`, `if: ${{ !inputs.publish }}`, `.github/workflows/build-candidate.yml:915`/`:925`) verifies the candidate's checksums and uploads the manifest, and `release` (`contents: write`, `if: ${{ inputs.publish }}`, `:978`/`:987`) verifies the signed bytes and creates the release; a candidate run reaches no job that can write. `LeastAuthorityTests` renders each job's effective `contents` scope and `if:` rather than reading text. | `tests/test_workflow_config.py::LeastAuthorityTests::test_a_candidate_dispatch_holds_no_write_grant`, `…::test_a_publish_dispatch_holds_the_write_grant_only_to_publish`, `…::test_the_workflow_default_is_read_only`, `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_the_candidate_job_never_holds_the_write_grant`; break-and-watch: all 33 mutations caught — `the publish job loses its gate and runs on a candidate dispatch`, `the candidate job is handed the repository write grant` |
| CT-84 | Med (referee: Low) | `safe_http.py:143-154` *(v0.6.7)* armed only the socket, so each `recv` restarted the budget and a server dripping one byte at a time held a connection past the 12 s explorer / 20 s broadcaster numbers (`wallet_service.py:96`, `:144`); `gui.py:1027-1035` called `broadcast_transaction` while holding `state.lock`, so a withholding broadcaster froze every lock-taking endpoint (status, scan, prepare, sign). `read_bounded()` now runs under a `Deadline` (monotonic end time) — `safe_http.py:51` `class Deadline`, `read_bounded` at `:101`, `open_url` at `:259` — taking what is left before every read and raising `TimeoutError` once spent (`wallet_service.py:101`/`:151`); in `gui.py` the submit runs outside the lock, re-verified under a short critical section (`:1093-1095`, "The payment changed before broadcast.") and recorded under a second (`:1120`). | `tests/test_safe_http.py::DeadlineTests::test_a_dribbling_server_cannot_outlive_the_deadline`, `…::test_an_expired_deadline_is_refused_before_connecting`; `tests/test_wallet_service.py::OutboundDeadlineTests::test_a_dribbling_explorer_returns_within_its_deadline`, `…::test_a_dribbling_broadcaster_gives_up_within_its_deadline`; `tests/test_send_flow.py::SendFlowTests::test_broadcast_prechecks_and_submit_do_not_hold_the_session_lock`, `…::test_a_scan_that_goes_stale_before_the_submit_is_refused`, `…::test_a_stalled_broadcast_blocks_neither_status_nor_an_import`; break-and-watch: all 37 mutations caught — `the read loop ignores the deadline mid-read`, `the explorer read drops its deadline`, `the accepted outcome is recorded without the session lock`, `the submit's stale-payment gate is removed` |
| CT-85 | Low | `ThreadingHTTPServer` gave every accepted connection a thread, and `gui.py:1262`/`desktop.py:316` *(v0.6.7)* armed it with no timeout, so a client announcing a `Content-Length` and never finishing the body held that thread (and its file descriptor) until the process exited; `_drain_body` (`gui.py:548-567`) did the same on the refusal path. `CONNECTION_TIMEOUT_SECONDS = 15.0` is now a handler-class attribute (`gui.py:61`) that `StreamRequestHandler.setup()` uses to arm the socket before the request line is read, `desktop.py:316` inherits it through `state.handler()`, and a timed-out `_drain_body` closes the connection and returns `False` so the caller skips the refusal instead of writing a 500. | `tests/test_gui_integration.py::StalledConnectionTests::test_stalled_bodies_are_cut_off_and_the_server_keeps_serving`, `…::test_a_refused_request_with_a_stalled_body_is_cut_off_too`, `tests/test_gui.py::RefusalDeliveryPins` (re-pinned to `if not self._drain_body(): return` before the answer); break-and-watch: all 40 defeats caught, 39 test ids green — `the connection timeout is removed`, `a stalled body is answered with a 500`, `the drain stops bounding a stalled body` |
| CT-86 | Med | No workflow or script read the bytes a tag publishes for credentials: there was no secret scan anywhere in `.github/workflows/*` or `scripts/*`, and GitHub's platform secret-scanning posture was a browser setting, not a record. The source job now scans the extracted archive (not the worktree) after the archive is built and before it is uploaded — `.github/workflows/build-candidate.yml:156` — using `detect-secrets==1.5.0` pinned by version and hash in `requirements-ci.lock` and driven by `scripts/scan-secrets.py` (not a floating action); the wrapper chdirs to the target (detect-secrets drops paths outside the CWD), disables the two high-entropy plugins that fire on every digest, decides its own exit code, and refuses rather than reporting clean on a missing/empty target or an unpinned scanner. | `tests/test_secret_scan.py::CanaryTests::test_a_planted_canary_is_caught`, `…::test_a_missing_tree_is_refused_not_called_clean`, `tests/test_secret_scan.py::ScannerPinTests::test_the_lock_pins_the_scanner_by_version_and_hash`, `tests/test_secret_scan.py::ArchiveScanStepTests::test_the_scan_reads_the_archive_before_it_is_uploaded`, `tests/test_platform_state.py::PlatformRecordTests::test_the_record_carries_the_platform_secret_scanning_posture`; break-and-watch: all 45 defeats caught, 44 test ids green — the step removed, findings reported as clean, an empty tree scanned, the status exclusion dropped |
| CT-87 | Med | The container proof runs a digest, not a moving tag. The runner's apt set is declared once (`SYSTEM_PACKAGES` in `scripts/build-linux.sh`), asserted to be exactly what the workflow installs, and the version each resolved to is written into the SBOM by `dpkg-query` (fail closed if a declared package is absent). Exact apt version pins are **declined** for the runner image and recorded below as accepted floating inputs. | `tests/test_workflow_config.py::ToolchainPinTests::test_the_container_proof_runs_a_digest_not_a_moving_tag`, `…test_the_runner_packages_are_the_ones_the_build_script_declares`, `…test_every_floating_input_is_written_down`; `tests/test_build_sbom.py::SystemPackageTests` |
| CT-88 | Low | Every digest `vendor/README.md` states was prose with nothing checking it. `tests/test_vendor_pins.py::VendorPinTests` hashes the committed bytes, asserts the README states each digest, and refuses a file in `vendor/` that no digest covers. The README's regeneration command is real: `scripts/vendor-digests.py` is run by the test and must reproduce the recorded digests. | `tests/test_vendor_pins.py::VendorPinTests` (byte-flip break-and-watch in a disposable copy) |
| CT-89 | Low | `probe.py` claimed to refuse a BSMS whose receive and change branches used different multisig keys. Both branches are expanded from the one `/**` template, so the refusal could never fire. It was **deleted** rather than left in place: a check no accepted input can trip is a claim, not a control. Two tests hold the ground it claimed — the change branch is the receive wallet by construction, and the deleted claim cannot come back unargued. | `tests/test_probe.py::ProbeTests::test_the_expanded_change_branch_is_the_receive_wallet`, `…test_no_refusal_claims_a_key_agreement_the_template_cannot_violate`; `CONTROLS.md` records that no control is claimed here |
| CT-91 | Info | The vendored embit's Liquid/PSET copy kept upstream's `sequence=(self.sequence or 0xFFFFFFFF)`, which rewrites a legal `nSequence=0`; the fork had already fixed that shape in `src/embit/psbt.py`. Both properties in `src/embit/liquid/pset.py` (`vin`, `blinded_vin`) now carry the same explicit check, and the fork's whole delta is machine-held: the wheel must be the archive's `src/embit` tree in both directions, the implicit form must appear nowhere, and no shipped module may import the Liquid surface. | `tests/test_embit_vendor.py::EmbitVendorTests::test_source_diff_is_only_the_declared_version_and_sequence_fixes`, `…test_no_liquid_input_rewrites_a_legal_sequence_of_zero`, `…test_the_wheel_carries_the_source_it_was_built_from`, `…test_the_documentation_states_the_liquid_delta`, `…test_the_application_does_not_import_the_liquid_surface` |
| CT-92 | Low | The source-mode install pinned one library and guarded one library. `requirements.lock` carried the embit wheel and nothing else, `Start Easy Multisig.command` guarded only that version, and `probe.py` refused with "Install hwi 3.2.0 to use devices." — no command, and a venv created before the device library was wanted was never repaired. Added `requirements-source.txt` → `requirements-source.lock`: hwi 3.2.0 and its whole closure under `--require-hashes`, every version and hash set constrained to the reviewed `requirements-desktop.lock`; the launcher now guards both libraries and installs the source lock; the refusal names the exact command. | `tests/test_launcher.py` (9 tests), `tests/test_build_source.py::ArchiveCompletenessTests::test_the_source_mode_lock_reaches_the_archive`; break-and-watch: the lock loses hwi, the lock drifts, the guard drifts, the refusal loses the command |
| CT-93 | Low | `signing-key.asc` is committed and `SIGNING.md`/`RELEASE-PROCESS.md` tell a downloader to import it, but the source archive's allowlist copy left it out, so a tarball reader could not check `SHA256SUMS.asc` — the same dangling-reference class as the missing plist (CT-56). The key now ships: it is on the root copy and on the completeness loop that refuses a shipped document pointing at a file the archive lacks. The test reads the filename out of `SIGNING.md`, so the instruction and the archive cannot drift apart. | `tests/test_build_source.py::ArchiveCompletenessTests::test_the_release_public_key_reaches_the_archive`; break-and-watch: the key leaves the copy, the instruction renames it |
| CT-94 | Low | The v0.6.7 audit asked the repository-attestations API for `/repos/…/attestations/tags/v0.6.7` and for a bare subject digest, got 404 for both, and filed it as a possible API or permission gap. It was the shape of the request. That API exposes only `POST /attestations` and `GET /attestations/{subject_digest}`, and the parameter's own documentation requires the `sha256:HEX_DIGEST` form; nothing is indexed by tag, so there is no tag endpoint to 404 from, and a bare hex digest 404s exactly like a subject that carries no attestation (a syntactically valid unused digest 404s too). No fix was required, so the deliverable is the note the release process should have carried: `RELEASE-PROCESS.md` §3 now documents the supported command (`gh attestation verify "$ASSET" --repo cjtsh/bitcoin-easy-multisig-signer` — exit status is the result, silent on success), the scripted REST form with its required prefix, and both misleading 404 shapes, dated 2026-10-10 and scoped to all eight v0.6.7 assets (bare hex 404, prefixed 200). The asset name is written `v<version>` so the note cannot go stale. | `tests/test_release_verification_note.py::AttestationVerificationNoteTests` — the note's URL and command line are read out of the document and executed, not grepped; break-and-watch: the note drops the digest prefix, the note points at a tag, the note renames the supported command |
| CT-95 | Info | The tripwire at `tests/test_hardening_pins.py:331-336` *(v0.6.7)* asserted only the `HWI_PAYLOAD_PINS` constant and `:338-347` mocked `subprocess.run`, so it could never fail however the installed package bytes changed; the regression path it masked is CT-73. **Folded into CT-73's fix (commit `37ae9fb`) — there is no separate CT-95 change.** | Closed by CT-73's tests, which exercise real bytes: `tests/test_hardening_pins.py::HwiIdentityPins::test_a_poisoned_package_is_refused_on_real_bytes`, `…::test_a_poisoned_entry_module_is_refused_before_it_runs`, `…::test_the_manifest_covers_the_whole_payload_not_two_files`; break-and-watch: 21 defeats caught, baseline 21 test ids green |
| CT-90 | Low | **Deferred** — `network_config.py:57-58` leaves `SECONDARY_EXPLORERS` `None` for testnet4 and mutinynet, so practice-network outpoints have a single source, although mainnet has an independent second Esplora. The fix needs an operator-trusted second endpoint per practice network; choosing a second public oracle is a policy decision and the practice networks carry no money. | Not fixed in 0.6.8; deliberately moved to the next-cycle list (`releases/PLAN-0.6.8.md:210`, `:279`) with trigger "next practice-network change or next cycle, whichever is first". No test. |
| CT-59 | Low | Deferred in v0.6.7 as an availability limitation — a stalling explorer can make one balance scan slow; the scan is bounded per request and fails closed, claiming **nothing** about the balance. Its revisit trigger fired as CT-84, and it is now **CLOSED by the CT-84 fix** (total deadlines on every outbound read, and the submit outside `state.lock`); the deferral's 2027-10-07 expiry is moot. | CT-84's tests close it: `tests/test_safe_http.py::DeadlineTests::test_a_dribbling_server_cannot_outlive_the_deadline`, `tests/test_wallet_service.py::OutboundDeadlineTests::test_a_dribbling_explorer_returns_within_its_deadline`, `tests/test_send_flow.py::SendFlowTests::test_a_stalled_broadcast_blocks_neither_status_nor_an_import`; break-and-watch: CT-84's 37 defeats |
| CT-54 | Low | **Deferred** — rebuild `vendor/libusb-1.0.0.dylib` from pinned upstream source at the next dependency bump, which is when the pin has to move anyway; the current dylib's symbol set is identical to the pinned build and its provenance chain is recorded in the SBOM, and the audit's own remedy is "build from pinned source next bump". | Not fixed in 0.6.8; terms unchanged in `releases/OWNER-ACCEPTANCE-2026-10-07.md` (trigger: the next dependency bump; expiry **2027-10-07**, after which the finding reopens) and `releases/PLAN-0.6.8.md:209`/`:285`. No test. |

## CT-72: the release guard executed the input it validated

The audit (Red RED-1, Blue BLUE-5, Amber AMBER-1) found `.github/workflows/build-candidate.yml:69` *(v0.6.7)* spelled `if [[ ! "${{ inputs.candidate_run_id }}" =~ ^[0-9]+$ ]]`. GitHub substitutes the free-text dispatch input into the `run:` script before bash parses it, so the guard's own regex never gated execution: `$(touch /tmp/red-t8/PWNED-BY-INPUT)` ran when `[[ ]]` was evaluated, a quote-break (`1" ]] || touch /tmp/red-t8/PWNED-BY-INPUT; [[ "1`) also ran, and Amber's `$(touch /tmp/PWNED2; printf 12345)` both ran the payload and **passed** the guard because `12345` matches `^[0-9]+$`.

**What changed.** The value is declared as `CANDIDATE_RUN_ID: ${{ inputs.candidate_run_id }}` in the step's `env:` (`.github/workflows/build-candidate.yml:70`) and read as `[[ ! "$CANDIDATE_RUN_ID" =~ ^[0-9]+$ ]]` (`:76`) — the safe shape the same file already used at `:699-703`/`:702`. No `run:` body interpolates a `${{ }}` expression any more, and `tests/test_publish_guards.py::InterpolationLintTests` fails if one returns (M2); the cases run under M1, `tests/workflow_harness.py`.

**Red first.** The commit records no verbatim red-first failure output; the pre-fix state it names is the audit's three demonstrated payloads above.

**Break and watch.** `candidate_run_id goes back into the script text` (deleting the `env:` line) is caught by `test_the_step_that_uses_each_expression_still_receives_it`; the commit records **17 defeats, each green first**.

## CT-73: the payload pin covered two files of one hundred and fifteen

The audit (Blue BLUE-1, Copper COPPER-1, White F2) found `probe.py:211-214` *(v0.6.7)* pinned only `hwilib/__init__.py` and `hwilib/_cli.py`, and `_verify_hwi_payload()` (`:311-348`) hashed exactly those two while its docstring (`:317`) claimed "a poisoned site-packages is refused rather than believed". Copper counted **2 of 115** installed `hwilib` `.py` files pinned; a poisoned `hwilib/devices/trezor.py` passed the check and then ran on `import hwilib._cli` / `scripts/hwi_entry.py:109`.

**What changed.** `scripts/build-hwi-manifest.py` records every regular file of the installed package, excluding `__pycache__`/`.pyc` by a recorded rule, and refuses a stale record; `vendor/hwi-payload-3.2.0.json` is that record, and its two entry digests equal the two values `probe.py` had pinned by hand. `probe.py:221` names it (`hwi-payload-{EXPECTED_HWI_VERSION}.json`), `_hwi_manifest_path` (`:326`) finds it without importing the package, and `_verify_hwi_payload` (`:418`) refuses a missing, added or changed file. The macOS, Linux and Windows builds gate on it before bundling the helper, and the tarball ships it, so a HWI pin bump fails the build until the record is regenerated and committed.

**Red first.** The commit records no verbatim red-first output; it states the pre-fix state plainly: "a poisoned `hwilib/devices/trezor.py` passed the check and then ran on import."

**Break and watch.** **21 defeats caught, baseline 21 test ids green** — `payload manifest check reduced to the two entry pins`, `payload check imports the package it is checking`, `manifest staleness comparison neutered`, `a build stops gating on the manifest`.

## CT-74: guards pinned by text, not behaviour

The audit (Blue BLUE-2) found the version-job refusal `if: ${{ inputs.publish && !inputs.notarize }}` (`build-candidate.yml:57-61` *(v0.6.7)*), the release-job body check (`:738`) and the manifest notarize grep (`:978-981`) pinned by text only. Replacing the `if:` with `if: ${{ false }}`, the body check's `!= "true"` with `== "impossible-value"`, and the grep with `grep -Fx "notarize=true" "$manifest" || true` each left `tests/test_workflow_config.py` green (`Ran 55 tests … OK`).

**What changed.** M1 (`tests/workflow_harness.py`) runs a step the way the runner does — it renders the expressions from a context, evaluates the step's `if:`, builds the environment from the step's own `env:` block, and executes the body under `bash -e` with scripted stand-ins for `gh`, `git`, `gpg` and `jq`. Every publish guard is now exercised as behaviour in `tests/test_publish_guards.py::ReleaseGuardBehaviourTests` rather than pinned as text; the older `GuardBodyPins` text pins stay as the cheap first layer.

**Red first.** The commit records no verbatim red-first failure output.

**Break and watch.** **17 defeats, each green first.** Named defeats include `unsigned-release guard disabled` → `test_the_unsigned_release_guard_runs_exactly_on_publish_without_notarize`, `unnotarized-publish guard inverted` → `test_an_unnotarized_publish_is_refused`, and `the candidate manifest claims the run published` → `test_a_candidate_writes_a_manifest_and_publishes_nothing`.

## CT-75: the checksum, tag and candidate-binding guards were string pins

The audit (Blue BLUE-3) defeated the tag guard (`build-candidate.yml:986-996` *(v0.6.7)*, comparison inverted to `"$tag_status" == 1`), both `shasum -a 256 -c SHA256SUMS` sites (`:747`, `:844`, each with `|| true`), the candidate-binding `jq` `(.conclusion == "success" or true)` (`:710-713`) and the main-ref `exit 1` (`:65-68`) — and all 55 workflow tests stayed green. `test_workflow_config.py` only asserted the `git ls-remote …` string and the "Bump version.py" text.

**What changed.** Each guard is converted to an outcome case on the M1 harness in `tests/test_publish_guards.py::ReleaseGuardBehaviourTests`. Where a guard's effect depends on external state (the `git ls-remote` tag state), the stub supplies the state and the case asserts the branch taken and the refusal text, so the outcome is tested rather than the spelling.

**Red first.** The commit records no verbatim red-first failure output.

**Break and watch.** **17 defeats, each green first**: `checksum verification neutered` → `test_a_tampered_asset_fails_the_checksum_verification`; `gpg verification neutered` → `test_the_publish_path_verifies_the_signature_and_refuses_a_bad_one`; `existing-tag guard inverted` → `test_an_existing_tag_is_never_overwritten`; `unverifiable-tag guard dropped` → `test_an_unverifiable_tag_state_refuses_publication`; `main-ref guard loses its refusal` → `test_money_path_the_guard_still_refuses_a_non_main_ref`.

## CT-76: the publish-path sweep never looked at tags

The audit (Amber AMBER-2, White F8) found `scripts/check-publish-paths.sh:61` *(v0.6.7)* fetched `+refs/heads/*` only, while the header claimed "Refuse a second publish path on any **ref**". Tags `v0.1.11`–`v0.1.23` still carried a frozen delete-and-replace publish step (`gh release delete "$tag" --yes --cleanup-tag || true; gh api -X DELETE …/git/refs/tags/$tag || true; gh release create …`) with no main-branch requirement and no candidate gate. A fixture remote with a tag carrying `.github/workflows/build-windows.yml` produced `ok: no non-main ref carries a publish-capable workflow` and exit 0.

**What changed.** The sweep fetches heads and tags (`+refs/heads/*:${AUDIT_HEADS}/*` at `scripts/check-publish-paths.sh:131`, `+refs/tags/*:${AUDIT_TAGS}/*` at `:132`) and is inverted from a two-pattern denylist to an allowlist: only `main`, and on `main` only `build-candidate.yml`, may reference release publication. A tag is judged by what it can do *from its own ref* — a guarded tag is inert, the 46 tags published before the guard existed are an enumerated accepted residual, and any other tag is an offender. The header now describes what the code does.

**Red first.** The commit records no verbatim red-first failure output; the digest records the pre-fix run printing "ok" and exiting 0.

**Break and watch.** **17 defeats, each green first**, including `tag refs are never checked` → `test_the_sweep_refuses_a_tag_carrying_an_unguarded_publisher` and `main allowlist stops naming the publisher` → `test_the_sweep_accepts_main_publishing_through_the_one_named_file`.

## CT-77: the sweep's denylist missed every other publish form

The audit (Blue BLUE-4, Amber AMBER-3, White F9) found the matchers read only the literal `contents:[ ]?write` (`check-publish-paths.sh:48-49` *(v0.6.7)*) and the substring `gh release` (`:102-108`). A branch `sneaky` with `permissions: write-all` and `gh api -X POST "repos/$GITHUB_REPOSITORY/releases"` was accepted as "ok"; so were `curl -X POST https://api.github.com/repos/$GITHUB_REPOSITORY/releases` with `github.token` and `softprops/action-gh-release@v1`.

**What changed.** The denylist is inverted to an allowlist with three matchers: `CONTENT_WRITE_RE='contents:[[:space:]]*["'\'']?write["'\'']?'` (`scripts/check-publish-paths.sh:104`), `WRITE_ALL_RE='write-all'` (`:106`) and `RELEASE_SURFACE_RE='(\/releases|action-gh-release|create-release)'` (`:111`). Whole-line comments are skipped and never truncated, so prose cannot flag a file and a `#` cannot hide code.

**Red first.** The commit records no verbatim red-first failure output; the digest records the pre-fix branch accepted with "ok", exit 0.

**Break and watch.** **17 defeats, each green first**: `write-all matcher neutered` → `test_the_sweep_refuses_a_branch_granting_write_all`; `second-publisher-on-main rule dropped` → `test_the_sweep_refuses_a_second_publisher_on_main`; `comment stripping removed` → `test_the_sweep_ignores_a_workflow_whose_only_match_is_a_comment`; `unreadable body reported as clean` → `test_an_unreadable_workflow_body_is_an_offender`.

## CT-78: the chain constants were checked against themselves

The audit (Orange ORANGE-1, ORANGE-4, White F5) found every case in `tests/test_network_settings.py` built its expectation from `NETWORKS` itself, so replacing the mainnet genesis at `network_config.py:48` *(v0.6.7)* with true Signet's `00000008819873e925422c1ff0f99f7cc9bbb232af63a077a480a3633bee1ef6` left the six tests `OK` and a mocked Signet explorer passed `verify_esplora("main", …)`; the Mutinynet block-1 checkpoint at `:43` was unasserted too. The shipped literals were correct — oracle-verified against blockstream.info, an operator independent of the default mempool.space — the defect was that nothing kept them so.

**What changed.** No production constant moved; the missing check was added as `tests/test_network_settings.py::PublishedChainConstantsTests` (`:108`). `test_the_published_chain_constants_are_pinned_verbatim` (`:134`) states mainnet, testnet4 and Mutinynet genesis and the Mutinynet block-1 checkpoint as literals; `test_the_network_to_genesis_mapping_is_exclusive` (`:143`) asserts the four networks map to four distinct hashes; `test_a_signet_genesis_is_not_accepted_as_mainnet` (`:152`) drives `verify_esplora` through a mocked Signet explorer and requires refusal.

**Red first.** The commit (`1100e14`) records no verbatim red-first failure output; its CT-78 paragraph states the pre-fix behaviour in prose (a Signet swap agreed with the suite and passed `verify_esplora("main")`).

**Break and watch.** `mainnet genesis swapped for Signet's` (`break_and_watch.py:213`) and `the Mutinynet block-1 checkpoint is dropped` (`:220`) are both caught; the commit records **24 defeats caught (was 22), baseline 24 test ids green**. Full suite: 560 tests, OK.

## CT-79: the bare-wildcard guard had no reachable test

The audit (Orange ORANGE-2, White F6) found that `not bare_receive_only` in `wallet_service.py:313` *(v0.6.7)* — `standard_candidate = not declared and not bare_receive_only and _standard_bip48(record)` — is what stops a bare `/*` that matches `xpub/0` directly from enabling an inferred `/1/*` change branch, as `AGENTS.md:23` requires. All 16 cases in `tests/test_change_branch.py` anchored their reference at `xpub/0/0`, where the branch is unreachable, so deleting `not bare_receive_only` left the whole file green.

**What changed.** The guard's logic is unchanged; it is now pinned at the reachable shape and explained inline. `tests/test_change_branch.py::ChangeBranchTests::test_bare_wildcard_reference_at_the_branch_root_never_infers_change` (`:56`) builds the case the guard exists for — a bare `/*` whose reference address is `xpub/0` directly, restrictions "No path restrictions" — and asserts `change is None`, so the `change is not None` inference that `AGENTS.md:23` forbids now fails loudly. `wallet_service.py` gains eight comment lines at the flag recording the invariant and naming that test.

**Red first.** The commit (`1100e14`) records no verbatim red-first failure output; its CT-79 paragraph states the pre-fix behaviour in prose (deleting the guard left the 16-test file green).

**Break and watch.** `bare-receive-only wallets may infer standard change` (`break_and_watch.py:206`) is caught: with the guard deleted the new case fails while the old 16 pass. The commit records **24 defeats caught (was 22), baseline 24 test ids green**. Full suite: 560 tests, OK.

## CT-80: the credential wiring lived on the platform, not in a revision

The audit (Amber AMBER-4, Red RED-4, Blue BLUE-9, White F10) found that at the audited tag `81f58ec` the workflow declared no `environment:` at all (`grep -c 'environment:'` = 0), so no `MAC_*` or `GPG_*` name could resolve there — yet runs #106 (candidate `37644267740`) and #107 (publish `37655666900`) succeeded at that head on 2026-10-07 with certificate import, notary credentials and GPG manifest signing. The environments `apple-signing`/`release-signing` were created 2026-10-08, after publication, and the repository-level secret list is now empty: the wiring lived on the platform and in nobody's revision.

**What changed.** Current `main` declares `environment: apple-signing` (`.github/workflows/build-candidate.yml:189`) and `environment: release-signing` (`:775`). `tests/test_platform_state.py` asserts every secret name a job reads is declared by the environment that job names; that `MAC_NOTARY_KEY_P8_BASE64` is proved optional by a real `else` route holding a declared credential; that the two signing environments are main-only with zero required reviewers and `can_admins_bypass: true`; and that a registration with no file behind it is recorded as disabled. `releases/platform-state.json` is the machine-readable half and `scripts/check-platform-state.sh` re-reads the live platform and refuses on a missing or unauthenticated `gh`, an API error, an unreadable record or a repository mismatch; `RELEASE-PROCESS.md` §5 states the placement, and the source archive ships the record.

**Red first.** The commit records no verbatim red-first failure output.

**Break and watch.** The commit adds **five mutations** and **all 29 mutations are caught by their named tests**: `a platform secret is dropped from the record` → `test_the_record_declares_exactly_the_five_expected_secret_names`, `the differ stops comparing and always matches` → `test_a_dropped_secret_is_named_in_the_difference`, `an unauthenticated gh no longer stops the read` → `test_the_script_refuses_when_gh_is_present_but_unusable`, `a job reads secrets without naming its environment` → `test_every_referenced_secret_is_declared_by_the_job_environment`, `the platform record stops shipping in the archive` → `test_the_source_archive_ships_the_record_and_the_script`. Full suite: 582 tests, OK.

## CT-81: a non-ASCII token header was a traceback, not a refusal

The audit (Red RED-2) found that an HTTP header arrives decoded as latin-1 and `hmac.compare_digest` refuses two `str` arguments containing a non-ASCII character with `TypeError: comparing strings with non-ASCII characters is not supported`. A hostile `X-Local-Token` therefore raised inside the comparison at `gui.py:638` *(v0.6.7)*, the connection died with a traceback in the log, and the caller never received the ordinary 403.

**What changed.** `_token_matches()` (`gui.py:604`) encodes both sides as UTF-8 first, so the comparison is over bytes, stays constant-time (`hmac.compare_digest`), and every non-ASCII or malformed value is a plain mismatch.

**Red first.** The commit (`1570dab`) records no fenced output; it states the failure in prose: a hand-built socket POST carrying `X-Local-Token: \xff\xfe\x80` "returned an empty response (`b''` -- the connection died) before the change and `HTTP/1.0 403 Local access only`, with no traceback on stderr and the server still answering, after it."

**Break and watch.** `a non-ascii token header raises instead of refusing` (the comparison back on raw `str`) is caught; **all 31 mutations are caught by their named tests**. Full suite: 566 tests in 149.205s, OK.

## CT-82: the local token was pinned only as "a wrong token is refused"

The audit (Blue BLUE-6) found the only pin was that some wrong token is refused (`tests/test_gui_integration.py:151-153` *(v0.6.7)*), so a comparison accepting any prefix — `state.token.startswith(header)`, a last-six-characters test — stayed green.

**What changed.** `tests/test_gui_integration.py::LocalTokenComparisonTests` (`:282`) adds the near-miss matrix: `test_every_near_miss_of_the_token_is_refused` (`:291`) walks empty, one-character-short, one-character-long, the first six characters, the last six characters, both one-sided truncations, a single substituted character and a doubled value, each expected 403; `test_the_comparison_is_whole_value_and_constant_time` (`:316`) holds the primitive by pinning `hmac.compare_digest` over the two UTF-8 encodings. No production code changed.

**Red first.** The commit (`cf02a1d`) records no fenced output; it states the failure in prose: "with the comparison weakened to `hmac.compare_digest(candidate[:6], expected[:6])` the named case fails (the first six characters are accepted)".

**Break and watch.** `the token comparison accepts a six-character prefix` is caught; **all 31 mutations in `break_and_watch.py` are caught by their named tests**.

## CT-83: the write grant was on the job that decided, not the job that published

The audit (Blue BLUE-7, Amber AMBER-5) read the release job as holding `permissions: contents: write` with no job-level `if:`, making the publish decision inside its last step (`build-candidate.yml:828-834` *(v0.6.7)*). A `publish=false` candidate dispatch therefore also carried the repository write grant.

**What changed.** The grant is split across two jobs: `candidate-manifest` (`contents: read` at `.github/workflows/build-candidate.yml:925`, declared at `:915`, gated `if: ${{ !inputs.publish }}`) verifies the candidate's checksums and uploads the manifest, and `release` (`contents: write` at `:987`, declared at `:978`, gated `if: ${{ inputs.publish }}`) verifies the signed bytes and creates the release; the old candidate branch inside the publish step is gone. `LeastAuthorityTests` verifies by rendering the job structure: it computes each job's effective `contents` scope (a job-level block replaces the workflow default, so an unlisted scope is `none`), renders every job's `if:` through the M1 harness's `evaluate_if`, and asserts a candidate dispatch lists no writer while a publish dispatch lists `release` alone.

**Red first.** The commit records the failure in prose, not a fenced block: "dropping the publish job's `if` makes the candidate dispatch hold the write grant, and granting the candidate job `contents: write` makes the publish/candidate split fail."

**Break and watch.** **All 33 mutations in `break_and_watch.py` are caught**, including `the publish job loses its gate and runs on a candidate dispatch` → `test_a_candidate_dispatch_holds_no_write_grant` and `the candidate job is handed the repository write grant` → `test_the_candidate_job_never_holds_the_write_grant`; the four older mutations whose anchors moved were re-pointed rather than dropped. Full suite: 590 tests, OK.

## CT-84: a per-socket timeout is not a deadline, and the submit held the lock

The audit (Copper COPPER-2, the CT-59 revisit; White F7) found `safe_http.py:143-154` *(v0.6.7)* armed only the socket, so every `recv` restarted the budget: a loopback server dripping one byte per second kept `explorer_get` running past its 12 s and `broadcast_transaction` past its 20 s (`wallet_service.py:96`, `:144`; White saw `urlopen(timeout=12)` still running after 60 s). And `gui.py:1027-1035` called `broadcast_transaction` while holding `state.lock`, so a withholding broadcaster froze every lock-taking endpoint — status, scan, prepare, sign — indefinitely.

**What changed.** `read_bounded()` now runs under a `Deadline`, a monotonic end time: before every read it takes what is left of the budget, arms the socket with that, and raises `TimeoutError` once the budget is spent (`safe_http.py:51` `class Deadline`, `read_bounded` at `:101`, `open_url` at `:259`); the broadcaster (20 s), explorer (12 s per attempt), public fee/price fetches (7 s) and height check (8 s) each pass one (`wallet_service.py:101`, `:151`). In `gui.py` the submit runs outside the lock: the prepared payment and scan generation are re-verified under a short critical section (`:1093-1095`, refusing "The payment changed before broadcast."), the wallet identity is captured, the lock is released for the network call (`:1097-1102`), and the outcome is recorded under a second critical section attributed to the wallet that submitted it (`:1120`). A concurrent import can neither swap what is submitted nor have its outcome recorded against it.

**Red first.** The commit records the failure in prose, not a fenced block: `DeadlineTests` drips one byte per 50 ms (never a second between bytes) and shows the old plain read outliving a 1.0 s deadline; `OutboundDeadlineTests` proves the same through the real `explorer_get`/`broadcast_transaction` wiring — patching `wallet_service.time` rather than `time.sleep`, since stilling the global sleep also stills the dribble server.

**Break and watch.** **All 37 mutations are caught**, including `the read loop ignores the deadline mid-read`, `the explorer read drops its deadline`, `the accepted outcome is recorded without the session lock`, and `the submit's stale-payment gate is removed`. Full suite: 599 tests, OK.

## CT-85: a stalled body could hold a connection thread forever

The audit (Copper COPPER-3) found that `ThreadingHTTPServer` gives every accepted connection a thread and the handler armed it with no timeout (`gui.py:1262`, `desktop.py:316` *(v0.6.7)*; `server.socket.gettimeout()` is None), so a client that announced a `Content-Length` and never finished the body held that thread and its file descriptor until the process exited; `_drain_body` (`gui.py:548-567`) did the same on the refusal path. N stalled bodies were N held threads.

**What changed.** `CONNECTION_TIMEOUT_SECONDS = 15.0` is a handler-class attribute (`gui.py:61`) that `socketserver.StreamRequestHandler.setup()` uses to arm the socket before the request line is read, so every socket operation on an accepted connection is bounded; `desktop.py:316` builds its handler from `state.handler()` and inherits the bound. `_drain_body` (`gui.py:567`) now reports whether the body arrived: a timed-out drain closes the connection and returns `False`, and the caller skips the refusal instead of writing a 500 to a client that is not reading — in the size-and-type branch and the main body read alike. `tests/test_gui.py::RefusalDeliveryPins` (`:954`) was re-pinned to the new ordered form (`if not self._drain_body(): return` before the answer).

**Red first.** Recorded verbatim in the commit (`94ffd85`), with the fix reverted (the fix is one class attribute):

```
    FAIL: test_stalled_bodies_are_cut_off_and_the_server_keeps_serving
      File "tests/test_gui_integration.py", line 259, in _assert_cut_off
        self.assertEqual(sock.recv(64), b"",
    TimeoutError: timed out
    Ran 1 test in 5.101s
    FAILED (errors=1)
```

and, with only the read guard reverted, the client is answered instead of released:

```
    AssertionError: b'HTTP/1.0 500 Internal Server Error\r\nServer: ...' != b''
    : stalled connection 0 was not cut off
```

**Break and watch.** Three defeats added — `the connection timeout is removed`, `a stalled body is answered with a 500`, `the drain stops bounding a stalled body`; **all 40 defeats are caught, 39 test ids green**. `StalledConnectionTests` drives the real server over loopback (8 stalled bodies, then `/api/status` still answers; a second test declares one byte past `MAX_REQUEST_BYTES`), shortening the budget by patching `gui.CONNECTION_TIMEOUT_SECONDS` before the server is built so the wiring itself runs. Full suite: `Ran 601 tests in 161.335s, OK`.

## CT-86: nothing read the bytes a tag publishes for credentials

The audit (Blue BLUE-8) found no secret scan in any workflow or script; no `gitleaks`/`trufflehog`/secret-scan step existed, and GitHub's platform secret scanning was a browser setting rather than a record the repository could diff.

**What changed.** The source job scans the bytes a tag would publish — the extracted tarball, not the worktree — after the archive is built and before it is uploaded (`.github/workflows/build-candidate.yml:156`, "Scan the source archive for secrets"). The scanner is `detect-secrets==1.5.0`, pinned by version and hash in `requirements-ci.lock` and driven by `scripts/scan-secrets.py`; it is deliberately not a floating action. The wrapper decides the exit code itself (`detect-secrets` exits 0 with findings) and refuses with 2 rather than reporting clean on a missing or empty target, an unpinned scanner, or a scanner whose disabled plugins are active. It chdirs to the target because `detect-secrets` drops any path outside the process's working directory, and disables the two high-entropy plugins (194 findings in 12 files of digests), with that tradeoff written in its docstring. The one remaining false positive, the platform record's own status lines, is excluded by a line-shaped pattern that a test proves still catches a credential elsewhere in the same file. `scripts/check-platform-state.sh` and `releases/platform-state.json` now record the repository's secret-scanning posture, all five statuses including the disabled ones.

**Red first.** Observed before the fix, three ways, as the commit recorded them:

```
1. There was no scan at all. tests/test_secret_scan failed 11 of 12:

    can't open file '.../scripts/scan-secrets.py': [Errno 2] No such file or directory
    AssertionError: the source job has no step named 'Scan the source archive for secrets'
```

```
- secret_scanning: not in the record (live: {'dependabot_security_updates':
  'disabled', 'secret_scanning': 'enabled', 'secret_scanning_non_provider_patterns':
  'disabled', 'secret_scanning_push_protection': 'enabled',
  'secret_scanning_validity_checks': 'disabled'})
```

```
releases/platform-state.json:104: Secret Keyword
releases/platform-state.json:105: Secret Keyword
```

**Break and watch.** **All 45 defeats caught, 44 test ids green** — the four new mutations are the step removed, findings reported as clean, an empty tree scanned, and the status exclusion dropped. `tests.test_secret_scan` and `tests.test_platform_state` are green (38 tests); the rebuilt archive scans clean; full suite `Ran 618 tests in 163.195s, OK`.

## CT-87: the build's floating inputs

### The container proof runs a digest, not a tag

`ubuntu:24.04` is a moving pointer: it is republished as the image is
rebuilt, so a proof run against the tag says nothing durable about what
ran. The proof now names the manifest-list digest
`sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`
(published 2026-10-04), and the recipe records the command that refreshes
it so the next reader moves it deliberately:

```
docker buildx imagetools inspect ubuntu:24.04 --format '{{.Manifest.Digest}}'
```

### The runner's packages are declared once and recorded

The four packages the Linux build installs — `squashfs-tools`,
`librsvg2-bin`, `build-essential`, `fuse3` — are declared once, in
`scripts/build-linux.sh` as `SYSTEM_PACKAGES`. The workflow installs
exactly those names (a test compares the two lists), and every Linux
build writes the version each one resolved to into
`dist/BUILD-SBOM.json` with `dpkg-query`, failing closed if a declared
package is not installed. A reader of the SBOM can therefore see the
build's OS inputs even though they are not pinned.

### Accepted floating inputs

Pinning the runner's packages to exact versions is **declined**. The
runner image's `noble-updates` and `noble-security` archives move as
Canonical ships fixes; a pinned version would fail the build on a runner
refresh without making the AppImage's bytes reproducible, because the
package is only one input among many and the pin would have to be
re-derived by hand on every refresh anyway. A pin that breaks the build
and buys nothing is not a control.

What is accepted, and what stands in for the pin:

- **The runner image's packages**: `squashfs-tools`, `librsvg2-bin`,
  `build-essential`, `fuse3`, resolved from the `ubuntu-24.04` runner's
  archives. Recorded per build in the SBOM (name and version). Declared
  once in `scripts/build-linux.sh`; a test asserts the workflow installs
  exactly that set.
- **The proof container's packages**: `fuse3` and `ca-certificates`,
  installed inside the digest-pinned `ubuntu:24.04` container. Printed
  into the run log; the proof is a pass/fail assertion about the
  AppImage, not shipped bytes.
- **The container image**: pinned by the digest above; refresh command
  recorded beside the pin and in this section.

A review of this release should re-run the refresh command, move the
digest, and, if any of the four runner packages changes, update
`SYSTEM_PACKAGES`, this section, and the SBOM expectations in the same
commit.

## CT-88: the vendored digests were prose

`vendor/README.md` stated seven SHA-256 digests and nothing checked any
of them. Each is an input to a signed release — two embit archives, the
embit wheel both lock files require, the libusb dylib, the libusb source
tarball, the Windows DLL, and the AppImage runtime — so a changed byte
would have shipped against a README that still claimed the old value.

`tests/test_vendor_pins.py::VendorPinTests` now asserts three things,
each one a way a prose digest goes wrong:

- every registered file hashes to the digest the README states;
- the README states every registered digest, so editing the prose alone
  breaks the check rather than silently changing what is claimed;
- every file in `vendor/` is either registered or listed in the test
  with a reason it is not (the README itself, `libusb-COPYING`, and the
  generated `hwi-payload-3.2.0.json`, which `build-hwi-manifest.py
  --check` already covers).

The regeneration command the README documents is not prose either:
`scripts/vendor-digests.py` prints `digest  name` for the directory, and
the test runs it and requires it to reproduce the recorded digests.

Break-and-watch, per the plan, is a flipped byte in a disposable copy
rather than in the committed file:

```
cp -R vendor /tmp/vendor-scratch
python -c "from pathlib import Path; p = Path('/tmp/vendor-scratch/embit-upstream-2b375a.tar.gz'); d = bytearray(p.read_bytes()); d[100] ^= 0xFF; p.write_bytes(bytes(d))"
VENDOR_DIR=/tmp/vendor-scratch python -m unittest tests.test_vendor_pins
```

which reports the flipped file as

```
AssertionError: '5e51f2fe3ee28b9e36dd5127efc215c4df1185e151485c99146c67f1bb425068'
!= '3323c77583432be513b346bdc54f86f7ef5fb259e1db0e60975dc51bcbceb0a3' :
embit-upstream-2b375a.tar.gz does not match its recorded digest
```

## CT-89: a refusal that could never fire

`parse_bsms` accepted a BIP 129 `/**` template by expanding it twice —
once to `/0/*` for receive and once to `/1/*` for change — and then
claimed to refuse the result if the two branches did not use the same
multisig keys:

```python
if change_descriptor is not None:
    ...
    raise ProbeError("BSMS receive and change descriptors do not use the same multisig keys.")
```

Both branches come from the same `descriptor_text` through `str.replace`,
so their key sets and thresholds are equal by construction. A BSMS record
cannot express a change branch with different signers, which means the
`if` had no input that could reach it. The audit row named the choice:
make the rejection reachable, or delete it. **It was deleted.**

The reason is the rule this cycle is applying elsewhere: a check no
accepted input can trip is a claim about the code, not a control over it,
and a reader who trusts it stops looking. What the claim was standing in
for is now a stated invariant with a test on it — the change branch is
the receive wallet:

- `test_the_expanded_change_branch_is_the_receive_wallet` asserts the
  `/1/*` branch carries the same signer set, the same threshold, and the
  same native-SegWit `wsh` shape as the `/0/*` branch. If the expansion
  ever stops guaranteeing that, this fails and the refusal has to come
  back as a check that can actually fire.
- `test_no_refusal_claims_a_key_agreement_the_template_cannot_violate`
  reads `probe.py` and fails while the deleted message is present. That is
  the test that was watched failing first:

```
self.assertNotIn("do not use the same multisig keys", source)
AssertionError: 'do not use the same multisig keys' unexpectedly found in '...'
```

`break_and_watch.py` carries two defeats for it: reinstating the deleted
refusal (caught by the removal pin) and expanding the change branch with
a threshold of its own (caught by the invariant test). The comment left
at the expansion site says why no key-agreement check is needed, and
`CONTROLS.md` records that no control is claimed here.

## CT-91: the vendored Liquid copy rewrote a legal sequence

Upstream embit writes a PSBT input's sequence as
`sequence=(self.sequence or 0xFFFFFFFF)`. When the field is a legal
`0` — the value that says the input is final and does not signal
BIP 68 — Python's `or` replaces it with the maximum, so the sequence
that was read is not the sequence that is written. The fork had already
corrected that shape in `src/embit/psbt.py`:

```python
sequence=(0xFFFFFFFF if self.sequence is None else self.sequence)
```

but the Liquid/PSET copy in `src/embit/liquid/pset.py` still carried the
upstream form in both `vin` and `blinded_vin`. The audit row (CT-91,
Info) offered two closes: patch the vendored copy as part of the next
embit delta, or record it with an explicit trigger. **It was patched,
because the fork should ship one behaviour rather than two and the fix
is one line.**

What holds it now is not the patch but the tests around it:

- `test_no_liquid_input_rewrites_a_legal_sequence_of_zero` asserts the
  implicit form appears zero times and the explicit form twice, in
  **both** the source archive and the built wheel, so a corrected
  archive with a stale wheel cannot pass.
- `test_the_wheel_carries_the_source_it_was_built_from` compares every
  packaged `embit/**` file against the archive's `src/embit/**` tree in
  both directions — missing, mismatched and extra each fail. That is the
  `diff -r` the plan asked for, held rather than performed once.
- `test_source_diff_is_only_the_declared_version_and_sequence_fixes`
  narrows the whole fork delta to three files and reproduces each of the
  three edits from upstream bytes, so a fourth edit cannot arrive
  unrecorded.
- `test_the_application_does_not_import_the_liquid_surface` keeps the
  reason `Info` is honest: if a shipped module ever imports embit's
  Liquid surface, this delta is on a money path and the row has to be
  re-graded.

The artifacts changed, so all four locks, `vendor/README.md` and
`tests/test_vendor_pins.py` moved with them:

| Artifact | SHA-256 |
| --- | --- |
| `vendor/embit-0.8.2+besa.1.tar.gz` | `6974ac6dec0866ebbb5ab1f6e17cc78b187bedb40a31e514c94d50d2a3df0ad6` |
| `vendor/embit-0.8.2+besa.1-py3-none-any.whl` | `41a5e7e850a09f58cae0819ead68a96c4600f90b4e83a5a82f6af49b9d5660ba` |

The archive was rebuilt by rewriting the one changed member in place, so
every other member's path, bytes, mode and timestamp are what they were
— the delta really is one file. The tests were watched failing first,
against the old artifacts:

```
AssertionError: 0 != 2 : the Liquid/PSET copy keeps upstream's
`or 0xFFFFFFFF` in vin or blinded_vin
AssertionError: 2 != 0 : the source archive still rewrites a legal
nSequence=0 to 0xFFFFFFFF
AssertionError: 0 != 1 : vendor/README.md does not name the
Liquid/PSET edit exactly once
```

and `break_and_watch.py` carries the defeats for the claims that a text
mutation can reach: the readme stops naming the Liquid file, the notices
stop counting the edits, and a shipped module imports the surface. The
artifact claims are broken the same way CT-88's were — a scratch copy
holding the pre-CT-91 wheel and archive makes three controls fail
(`test_source_diff_is_only_the_declared_version_and_sequence_fixes`,
`test_no_liquid_input_rewrites_a_legal_sequence_of_zero`, and the older
`test_bundled_wheel_is_hash_locked_and_contains_no_native_code`, which
is what pins the wheel hash in the locks).

## CT-92: the source install pinned one library and guarded one library

`requirements.txt` is one line — the vendored embit wheel — and
`requirements.lock` was compiled from it, so source mode installed embit and
stopped. `Start Easy Multisig.command` guarded exactly that:

```
if ! .venv/bin/python3 -c 'import importlib.metadata as m; raise SystemExit(0
if m.version("embit") == "0.8.2+besa.1" else 1)' >/dev/null 2>&1; then
```

A venv created before the device library was needed therefore satisfied the
guard forever and never installed HWI, while the refusal the user actually
meets said:

```
The pinned hardware-wallet library is not installed in this environment.
Install hwi 3.2.0 to use devices.
```

Neither the message nor `HWI-DEPENDENCY.md` named an install command.

**What changed.** A source-mode lock set, in the shape of the existing desktop
one: `requirements-source.txt` is `-r requirements.txt` plus the two extras and
`-c requirements-desktop.lock`; `requirements-source.lock` is the resolved,
hash-verified closure (22 entries: 21 packages plus the wheel file line). The
constraint is the load-bearing part. A fresh resolve today picks *newer* builds
than the release was reviewed with — `charset-normalizer 3.5.2`,
`cryptography 50.0.2` and `pycparser 3.11` against `3.5.1`, `50.0.1` and `3.0`
in `requirements-desktop.lock` — so an unconstrained source install would run a
different build of the same library than the bundle. With the constraint every
source entry is identical in version *and* hash set to its desktop counterpart,
and a test checks that rather than an eye. `Start Easy Multisig.command` now
tests both libraries through `importlib.metadata` (never importing them, so the
launcher cannot be the first thing to execute the library `probe.py` hashes) and
installs `--require-hashes -r requirements-source.lock`; `probe.py` names that
same command; `HWI-DEPENDENCY.md` gains an "Installing it, by mode" section and
its bump procedure now says the pin has three consumers and every lock is
regenerated, the source lock last. The three CI test jobs deliberately stay on
`requirements.lock` and its `hwilib` stub: installing hidapi and libusb1 into
every runner would have changed the environment under test to prove a point
about a different one.

**Red first.** With the fix absent (HEAD plus only the new lock files), the new
module ran `FAILED (failures=8)`:

```
AssertionError: 'm.version("hwi") == "3.2.0"' not found in '#!/bin/zsh…'
AssertionError: 0 != 1 : the launcher must install the source lock exactly once
AssertionError: 'python -m pip install --require-hashes -r requirements-source.lock'
                 not found in '"""Read-only BSMS and USB signer discovery proof.…'
```

plus `test_the_guards_read_metadata_and_never_import_the_package` and the four
`test_every_install_path_names_the_source_lock` subtests (launcher, `probe.py`,
`README.md`, `HWI-DEPENDENCY.md`). The three lock-shape tests passed on the new
lock itself, and the embit guard test passed because that guard is unchanged and
the source lock names the same wheel.

**Break and watch.** Four defeats, each caught by its named test: the source
lock loses the device library (`hwi==3.2.0` and its two hashes deleted) →
`SourceLockTests.test_the_device_library_is_pinned_with_hashes`; the source lock
drifts from the reviewed desktop lock (`cryptography==50.0.1` → `50.0.2`) →
`test_every_source_entry_matches_the_reviewed_desktop_lock`; the launcher's hwi
guard drifts (`"3.2.0"` → `"9.9.9"`) →
`LauncherTests.test_hwi_guard_matches_the_locked_pin`; the refusal loses the
command →
`DocumentedInstallPathTests.test_the_refusal_names_the_command_that_installs_the_library`.
The test module is also its own control: its first run failed with
`AssertionError: 'm.version("embit")' not found in ' command -v python3 >/dev/null 2>&1'`
because the guard test took the first `if !` in the launcher rather than the
install condition; it now anchors on the text before the install string.

## CT-93: the archive told readers to import a key it did not ship

`SIGNING.md` ends with the commands a downloader runs, and one of them is
`gpg --import signing-key.asc`; `RELEASE-PROCESS.md` says to verify the published
`SHA256SUMS` against "the committed `signing-key.asc`". Both are true of the
repository. Neither was true of the source archive: `scripts/build-source.sh` is
an allowlist copy, and the public key was never on it, so an archive-only reader
had to fetch the repository to check the signature over the tarball's own
checksums.

**Included, not reworded.** The key is public, committed, and 1,692 bytes. The
archive already ships the entitlements plist, the vendor libraries and the
platform record for exactly this reason — a shipped document must not point at a
file the archive does not contain — and rewriting the instructions would have
made the tarball a worse copy of the release evidence to save 1.7 KB. The root
copy now carries `signing-key.asc`, the completeness loop checks it (with a note
that it is on the list although it is not a document, because a shipped
`SIGNING.md` that names it is the dangling reference that loop exists to
refuse), and `SIGNING.md`'s verification step states that the source archive
ships the same key.

**Red first.** At the CT-92 commit with only the new test added, the class ran
`Ran 7 tests in 0.005s / FAILED (failures=1)`:

```
AssertionError: 'signing-key.asc' not found in 'set -euo pipefail…'
  : the archive copy must carry the release public key
```

**The first control was not one.** That version asked whether `signing-key.asc`
appeared anywhere in the script and in the document — and both break-and-watch
defeats sailed through it, because the completeness loop names the key too and
`SIGNING.md` names it a second time in the `git add` line of the key setup. The
shipped test instead *reads the filename out of* `SIGNING.md`'s
`gpg --import …` line and requires that exact name on the root copy command, so
renaming the instruction or dropping the file from the copy each fail:

```
MISSED  the archive drops the release public key
MISSED  the verification instructions name a key the archive does not ship
```

Both are `CAUGHT` now, and the whole harness reports `all 64 defeats caught`.

**End to end.** `scripts/build-source.sh 0.6.7` run in a scratch copy of the
tree built the archive; `signing-key.asc` is in it, byte-identical to the
committed file
(`sha256 812f790d37c6a5b97e0e27e536b1371657ac6d8052e33899f331ca9b03ddc54b`), and
the whole tarball contains one `BEGIN PGP PUBLIC KEY BLOCK` and zero
`PRIVATE KEY BLOCK`.

## CT-94: the attestation API is indexed by digest, not by tag

The v0.6.7 audit asked GitHub's repository-attestations API for a tag and got a
404:

    GET /repos/cjtsh/bitcoin-easy-multisig-signer/attestations/tags/v0.6.7  ->  404

The workflow says every asset carries a Sigstore attestation, so the finding was
filed as a possible API or permission gap. It is the shape of the request. The API
exposes only `POST /repos/{owner}/{repo}/attestations` and
`GET /repos/{owner}/{repo}/attestations/{subject_digest}`, and the path parameter's
own documentation is explicit -- it "should be set to the attestation's subject's
SHA256 digest, in the form `sha256:HEX_DIGEST`". Nothing is indexed by tag, so there
is no tag endpoint to 404 from; a bare hex digest 404s exactly like a digest that
carries no attestation, which is why the first reading looked like a gap.

Reproduced 2026-10-10 with `gh` 2.87.3 as `cjtsh`. The verbatim request line
(`gh api --verbose`) is
`> GET /repos/cjtsh/bitcoin-easy-multisig-signer/attestations/tags/v0.6.7 HTTP/1.1`
with `< HTTP/2.0 404 Not Found`; the bare digest answers 404 with
`documentation_url":"https://docs.github.com/rest/repos/attestations#list-attestations"`.
The same digest prefixed answers **200** with
`{"attestations":[{"repository_id":1391463135,"bundle_url":"https://tmaproduction.blob.core.windows.net/attestations/1391463135/2026/10/07/53643606.json.sn?…"}]}`.
All eight subjects in the v0.6.7 `SHA256SUMS` behave identically -- every one
bare `0`, prefixed `1` -- covering `BUILD-SBOM.json` and the three platform SBOMs,
the AppImage, both platform `.tar.gz`s, the `.dmg` and the `.zip`. A syntactically
valid but unused subject (`sha256:` plus 64 zeros) also 404s, so 404 means "no
attestation under this key", never "bad request". `GH_DEBUG=api gh attestation verify
/tmp/v067-sbom.json -R cjtsh/bitcoin-easy-multisig-signer` exits 0 having requested
`> GET /repos/cjtsh/bitcoin-easy-multisig-signer/attestations/sha256:93e7c2d6…a3e9?per_page=30&predicate_type=https://slsa.dev/provenance/v1`
-- the supported path uses the prefixed form, so no fix is required.

What landed is documentation and a test. `RELEASE-PROCESS.md` §3 gained
`### Verifying an asset's attestation`: the supported command, the scripted
`gh api "repos/cjtsh/bitcoin-easy-multisig-signer/attestations/sha256:$DIGEST"` form
(`sha256sum` with a `shasum -a 256` note for macOS), the finding above, and the
date and asset scope of the reproduction. `tests/test_release_verification_note.py`
holds it: the URL is read out of the document and expanded by the same shell an
operator would use, then compared with the prefixed path, and the command case
reads the runnable command line rather than the prose. Red first, with only the
test added:

    Ran 3 tests in 0.001s / FAILED (failures=3)
    AssertionError: 'gh attestation verify' not found in '# Release process...'

`break_and_watch.py` carries three CT-94 defeats (the note drops the digest
prefix, the note points at a tag, the note renames the supported command); all 67
defeats caught. Full suite: `Ran 648 tests in 164.211s OK`.

## Candidate attempt 38082865187 — the tests that were not portable

The first 0.6.8 candidate (dispatch of `d7dd590`, `notarize=true`,
`publish=false`) built and notarized both desktop artifacts, then failed two of
its remaining jobs. Both failures were portability defects in the new cycle-4
tests, not in the product: the macOS and Linux jobs ran the whole suite green.

### Cause

* **Windows job — the platform-state fake `gh` was a shebang script.** The
  differ is handed `PLATFORM_STATE_GH`, which the test planted as a file
  beginning `#!{sys.executable}`. Git Bash runs that form, but the Python side of
  `scripts/check-platform-state.sh` execs the path and Windows CreateProcess
  refuses a `#!` file:
  `OSError: [WinError 193] %1 is not a valid Win32 application`. Seven
  `PlatformCheckScriptTests` cases failed on the platform difference and never
  reached the control they pin.
* **Windows job — Git Bash has no `shasum`.** Three
  `tests/test_publish_guards.py` cases run the workflow's real checksum steps
  through `tests/workflow_harness.py`; those steps call
  `shasum -a 256 -c SHA256SUMS`, and the runner answered
  `shasum: command not found` (exit 127). The workflow itself runs those steps on
  macOS and ubuntu, where `shasum` is the tool that exists.
* **Source archive job — the inventory cited a checkout-only path.** Four
  `ControlInventoryTests::test_every_row_names_code_that_exists` subtests failed
  for `CM-12`…`CM-15`: `CM-1x cites missing
  .github/workflows/build-candidate.yml`. An archive is a source tree —
  `scripts/build-source.sh` ships that recipe as `ci/build-candidate.yml` — and
  `tests/support.py:find_build_recipe` already resolves both places. The
  portability pin lists the modules that must go through it; this module was not
  on the list, which is the third time this class of defect has shipped (0.6.6
  `PipToolsPinTests`, 0.6.7 `ToolchainPinTests`).

### Fixes

* `tests/test_platform_state.py` — `_fake_gh` writes the Python source as
  `gh.py` and, on `win32`, a `gh.cmd` trampoline (`@echo off`, then
  `"<python>" "%~dp0gh.py" %*`), returning that as the program. POSIX keeps the
  shebang file. This is the shape `tests/test_hardening_pins.py` has used since
  the 0.6.7 candidate taught the same lesson.
* `tests/workflow_harness.py` — the stub preamble now defines a real `shasum`
  (`SHASUM_SHIM`): it consumes `-a`/`--algorithm` (sha-256 only; anything else
  refuses with exit 2), then runs `sha256sum` where it exists and the real
  `shasum` where it does not. That is digest math, not a canned answer, so a step
  body under test still verifies real bytes on every runner; a test that passes
  its own `shasum` in `stubs` still overrides it, because that function is
  defined later in the script.
* `tests/test_controls_inventory.py` — `cited_file(relative, root=ROOT)`
  resolves a row's citation through `support.find_build_recipe` when the raw path
  is absent and the citation names `.github/workflows/<name>`.
* `tests/test_windows_portability.py` — `test_controls_inventory.py` joins the
  pinned resolver list, and three behaviour tests were added: the ci/ fallback
  with a temporary root, the platform-state fake `gh`'s shape under a simulated
  `win32`, and the shasum shim (a real digest passes, a changed byte refuses).

### A trap the tripwire run set for the next suite

The mutation harness rewrites a source file and restores it in `finally`. For an
equal-length edit made and undone inside one filesystem timestamp tick, the
`.pyc` compiled from the *mutated* source still matches the restored file on
(mtime, size), so the next run reuses it. The clean suite that followed `all 77
defeats caught` failed four cases with the mutated shim's own refusal message
(`workflow_harness: only sha-256 is available here`), while the file on disk was
correct. `break_and_watch.py` now runs its child suite with `-B` and
`PYTHONPYCACHEPREFIX` pointed at a scratch directory, so a mutation can never
leave bytecode in the checkout — and, more to the point, can never hide a defeat
from the harness itself.

### Tripwires for the fixes (`break_and_watch.py`, 77/77)

Three defeats were added, each caught by a named committed test:

| defeat | caught by |
| --- | --- |
| the shared recipe resolver forgets the archive copy | `tests/test_windows_portability.py::HardeningPinPortabilityTests::test_the_shared_resolver_finds_the_archived_copy` |
| the platform-state fake `gh` is a shebang script again | `tests/test_platform_state.py::PlatformCheckScriptTests::test_the_fake_gh_is_whatever_this_platform_can_execute` |
| the step harness stops answering `shasum` for sha-256 | `tests/test_windows_portability.py::ReleaseChecksumPortabilityTests::test_the_shasum_shim_verifies_real_bytes_and_refuses_a_changed_one` |

The archive-specific half cannot be caught from a checkout, where the
`.github/workflows/` copy exists: it is caught by the archive job itself, and
locally by `scripts/build-source.sh 0.6.8` followed by the suite from the
extracted tree, which is the same step the pipeline runs — `Ran 667 tests in
162.346s / OK`. Full suite from the checkout: `Ran 667 tests in 162.466s / OK`.

## Candidate attempt 38085097103 — three more tests that only held on a POSIX host

The same commit (`5b1e52e`) dispatched a second time, `notarize=true,
publish=false`. The macOS DMG, the Linux AppImage and the suite inside the
source archive all passed this time — the archive job got past the tests that
the first attempt's `cited_file` fix repaired, and the Windows job got past the
shebang-only fake `gh`. Three defects remained, and all three were reachable
only by running on Windows, plus one that the archive's own byte scan found in
this ledger.

### Cause

* **The differ's shell could not see or run a batch file.** On `win32` the fake
  `gh` is a `.cmd`, and the differ's presence gate was `command -v "$gh_bin"` —
  which cannot see a batch file. Seven tests reported `refusing: C:\...\gh.cmd
  is not installed, so the platform state cannot be read.` Even had the gate
  passed, bash cannot execute a `.cmd`: the command interpreter has to read it.
  The one test that plants an extensionless `#!/bin/sh` helper passed on the
  same runner, which is how we know the path form and the backslashes were
  never the problem.
* **An assertion that named the host's spelling of a shebang.** The new
  `test_the_fake_gh_is_whatever_this_platform_can_execute` asserted `"#!/"` for
  its POSIX branch. On a Windows host that branch's first line is
  `#!C:\hostedtoolcache\...\python.exe`, which is a shebang with no `!/` in it.
  The assertion tested the host, not the shape it was written to pin.
* **A checksum file written in the platform's newline.** `write_dist` wrote
  `SHA256SUMS` in text mode; on Windows that put a carriage return between the
  digest and the filename, and the step harness's real `sha256sum -c` reported
  `sha256sum: 'Bitcoin-Easy-Signer-v9.9.9-macOS.dmg'$'\r': No such file or
  directory`, failing three release-guard tests. The shim is real digest math,
  so it reproduced exactly what a Windows runner would do to that file.
* **The scanner refused this ledger.** The archive job's "Scan the source
  archive for secrets" step failed with `refused: 4 secret(s); a tag would
  publish them:` naming `releases/PATCH-0.6.8.md` lines 29, 136, 221 and 223.
  Two were the platform record quoted in Python's repr, whose single quotes the
  status-line exclusion did not cover because it was written for JSON. Two were
  a code span that ends in `;` within fifty non-space characters of the word
  `secret` inside a test name — the keyword plugin's quoted-value rule, which
  reads punctuation, not meaning. Neither was a credential; both were real
  defects in a document that a release publishes.

### Fixes

* `scripts/check-platform-state.sh` — the presence gate now accepts a real file
  at the given path (`[ ! -f "$gh_bin" ]`) as well as a name on `PATH`, and a
  new `gh_run` helper sends `*.cmd`/`*.bat` through `cmd.exe //c` while
  everything else goes straight to the binary. `auth status` runs through it.
  Windows Python can exec a `.cmd` — the HWI identity gate has done so since
  0.6.6 — and now the shell does not have to.
* `tests/test_platform_state.py` — the POSIX branch asserts
  `body.startswith("#!")` and that `sys.executable` appears in the body. The
  `win32` branch is unchanged.
* `tests/test_publish_guards.py` — `write_dist` writes `SHA256SUMS` with
  `newline="\n"`, so the file a shell parses is the same file on every host.
* `scripts/scan-secrets.py` — `STATUS_LINE_EXCLUSION` now accepts single or
  double quotes around the key and the value, so the Python repr of the status
  lines is excluded exactly like the JSON form. It is still a line-shaped
  exclusion: the same line carrying a real token is still a finding, which is
  what the new canary proves.
* `releases/PATCH-0.6.8.md` — in the CT-80 section, the two sentences the
  scanner read as assignments were reworded; no claim changed.
* `tests/test_secret_scan.py` — two canaries for the widened exclusion: the
  repr form is excluded, and a planted `github_token` beside it is still
  refused.
* `tests/test_windows_portability.py` — a new pin that the differ defines
  `gh_run` and hands a batch file to `cmd.exe //c`, and the module and class
  docstrings now record this run as well.

### Tripwires for the fixes (`break_and_watch.py`, 80/80)

Three defeats were added, each caught by a named committed test:

| defeat | caught by |
| --- | --- |
| the differ hands a batch `gh` straight to the shell | `tests/test_windows_portability.py::HardeningPinPortabilityTests::test_the_differ_never_hands_a_batch_gh_to_the_shell_directly` |
| the checksum file carries the platform's newline | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_the_candidate_path_verifies_checksums_and_stops` |
| the status exclusion stops covering the record's repr | `tests/test_secret_scan.py::CanaryTests::test_the_python_rendering_of_the_status_lines_is_excluded_too` |

The Windows behaviour itself cannot be reproduced on this host; what the
tripwires hold is that the batch-file branch exists and that the file a shell
parses has no carriage return in it. Both defects were found by the candidate
pipeline, which is the control that has to work — the point of fixing the
process rather than the symptom.

### Verification

* Checkout suite: `Ran 671 tests in 162.951s / OK`.
* Source archive: `scripts/build-source.sh 0.6.8`, extracted, suite run from the
  extracted tree: `Ran 671 tests in 163.739s / OK`.
* Secret scan: `ok: no secrets in releases/PATCH-0.6.8.md`, and the same scan
  over the extracted archive reports no secrets.
* `break_and_watch.py`: `all 80 defeats caught`.

## Publication

**Published 2026-10-10** as tag `v0.6.8` = `0d4e01f60c7695d720099f9d8e9e23b38da63102`,
through the unified pipeline and nothing else.

- Candidate [38086778883](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/38086778883)
  — `notarize=true, publish=false` from `0d4e01f`, every job green (read version,
  source archive and tests, macOS, Windows, Linux, `SHA256SUMS`), and
  `CANDIDATE-MANIFEST.txt` written; the publish job was skipped, as it must be
  on a candidate dispatch.
- No owner hardware acceptance gate stood for this revision. 0.6.8 changes the
  build process, the tests and the documentation; it does not touch the device
  identity, the signing path or broadcast policy, so the gate that 0.6.7 needed
  for CT-49/CT-58 is not the gate this revision needs. The owner authorized the
  candidate and the promotion as one decision and neither was paused on.
- Promotion [38087360421](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/38087360421)
  — `notarize=true, publish=true, candidate_run_id=38086778883`, dispatched from
  the **same commit** `0d4e01f`. Every job green.

Two candidates preceded this one and their defects are recorded above; both were
found by the pipeline rather than by a reader, which is what the unified path is
for.

### Post-publication verification (RELEASE-PROCESS.md §3)

Checked independently after the publish run, against the public release page:

| Check | Result |
| --- | --- |
| Tag points to the commit named by the publishing run | `v0.6.8` → `0d4e01f…`, equal to the publish run's `head_sha` and to the candidate run's `head_sha` — same-commit promotion holds |
| Every public asset downloaded | 10 assets: source tarball, macOS DMG, Windows zip, Linux AppImage + Linux tar.gz, three `BUILD-SBOM.json`, `SHA256SUMS`, `SHA256SUMS.asc` |
| Published `SHA256SUMS` verified | `shasum -a 256 -c SHA256SUMS` — 8/8 **OK** |
| `SHA256SUMS.asc` verified against the committed `signing-key.asc` | **Good signature** from `Bitseeker LLC <release@bitseeker.llc>`, RSA key `ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7` |
| macOS DMG notarized and stapled | `xcrun stapler validate` — **the validate action worked** |
| Sigstore attestations on an asset | 2 attestations on the DMG digest `cb552710…`, from the publishing workflow |
| Release is neither draft nor prerelease | `draft=false prerelease=false`, published 2026-10-10T21:31:47Z |

No tag or asset was moved, replaced, or deleted. The candidate bytes and the
published bytes are the same artefact set: `SHA256SUMS` is the file the pipeline
wrote, it verifies against every asset, and its signature verifies against the
key this repository ships.

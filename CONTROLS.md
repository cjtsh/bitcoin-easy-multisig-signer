# Controls

This file is the checked inventory of the security controls this project relies
on. Each row names the control in plain English, the exact code site that makes
the claim, and the test that would go red if the claim stopped being true.
`tests/test_controls_inventory.py` reads this file and fails the build when a
cited file or test stops existing, or when a row's own `CONTROL: CM-##` marker
is not inside the line range that row cites — so a citation that moves onto
unrelated lines fails, not just one whose file or line number disappeared.
A document nothing reads rots the moment it is written.

## Controls

| ID | Control claim | Where it is made | Test that proves it |
| --- | --- | --- | --- |
| CM-01 | The explorer's network is checked against the expected genesis before any of its numbers are trusted. | `gui.py:863-868` | `tests/test_gui_integration.py::TransactionJourneyTests::test_scan_of_the_built_in_explorer_still_checks_its_genesis` |
| CM-02 | A broadcast stays paused until the explorer reports one confirmation; a missing or invalid status is not a confirmation. | `gui.py:870-882` | `tests/test_gui.py::LocalGuiTests::test_recent_broadcast_stays_paused_until_explorer_confirms_it` |
| CM-03 | A mainnet broadcast needs the per-transaction final-screen consent and the backend opt-in, which defaults to False. | `gui.py:1099-1102` | `tests/test_send_flow.py::SendFlowTests::test_mainnet_broadcast_requires_separate_per_transaction_opt_in` |
| CM-04 | A signer update contributes only verified partial signatures against the reviewed PSBT; none of its metadata enters prepared state. | `signing.py:156-184` | `tests/test_signing.py::FinalizeTests::test_device_can_only_add_valid_signatures` |
| CM-05 | Nonstandard or custom change origins fail closed to the deliberate Send All path instead of inventing a change branch. | `wallet_service.py:321-326` | `tests/test_change_branch.py::ChangeBranchTests::test_nonstandard_wallet_can_only_sweep_without_creating_change` |
| CM-06 | A bare `/*` matching the branch root never infers an `/1/*` change branch. | `wallet_service.py:307-318` | `tests/test_change_branch.py::ChangeBranchTests::test_bare_wildcard_reference_at_the_branch_root_never_infers_change` |
| CM-07 | A wallet with more than three keys is refused outright. | `probe.py:166-167` | `tests/test_change_branch.py::ChangeBranchTests::test_a_wallet_with_more_than_three_keys_is_refused` |
| CM-08 | The HWI distribution is verified as a whole payload manifest, so a poisoned module cannot pass the two-file pin. | `probe.py:206-221` | `tests/test_hardening_pins.py::HwiIdentityPins::test_a_poisoned_package_is_refused_on_real_bytes` |
| CM-09 | The manifest generator covers the whole payload and refuses a stale manifest, and every platform build gates on it. | `scripts/build-hwi-manifest.py:155-171` | `tests/test_hardening_pins.py::HwiIdentityPins::test_the_manifest_covers_the_whole_payload_not_two_files` |
| CM-10 | The publish-path sweep enumerates remote heads and tags and fails closed when a workflow body cannot be read. | `scripts/check-publish-paths.sh:70-80` | `tests/test_workflow_config.py::SweepFailClosedPins::test_the_body_read_is_not_allowed_to_swallow_its_failure` |
| CM-11 | The platform-state check fails closed: a missing tool, authentication or record is a refusal, never a match. | `scripts/check-platform-state.sh:23-25` | `tests/test_platform_state.py::PlatformCheckScriptTests::test_the_script_fails_closed_by_construction` |
| CM-12 | The publish path verifies the release signature against the committed public key and refuses a bad one. | `.github/workflows/build-candidate.yml:1032-1039` | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_the_publish_path_verifies_the_signature_and_refuses_a_bad_one` |
| CM-13 | An existing release tag is never overwritten, and an unverifiable tag state refuses publication. | `.github/workflows/build-candidate.yml:1139-1149` | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_an_existing_tag_is_never_overwritten` |
| CM-14 | An unsigned public release is refused before any build starts. | `.github/workflows/build-candidate.yml:57-61` | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_the_unsigned_release_guard_refuses_and_names_the_reason` |
| CM-15 | An unnotarized publish is refused and never reaches the release command. | `.github/workflows/build-candidate.yml:1135-1138` | `tests/test_publish_guards.py::ReleaseGuardBehaviourTests::test_an_unnotarized_publish_is_refused` |
| CM-16 | No `run:` body interpolates a GitHub expression; values reach the shell through `env:`. | `tests/test_publish_guards.py:395-412` | `tests/test_publish_guards.py::InterpolationLintTests::test_no_run_body_interpolates_a_github_expression` |
| CM-17 | The source-mode install pins the device library with hashes and the launcher guards both libraries before skipping it. | `Start Easy Multisig.command:25-28` | `tests/test_launcher.py::SourceLockTests::test_the_device_library_is_pinned_with_hashes` |
| CM-18 | Diagnostics carry fixed codes, the selected network and a validated device class, never free text or wallet material. | `gui.py:538-566` | `tests/test_diagnostics.py::DiagnosticTests::test_device_fields_accept_only_a_known_device_class` |
| CM-19 | The source archive ships the release public key its own instructions tell a downloader to import. | `scripts/build-source.sh:37-45` | `tests/test_build_source.py::ArchiveCompletenessTests::test_the_release_public_key_reaches_the_archive` |
| CM-20 | A non-main ref that carries a publish-capable workflow is refused, on every remote head and tag. | `scripts/check-publish-paths.sh:87` | `tests/test_workflow_config.py::PublishPathSweepTests::test_the_sweep_refuses_a_remote_branch_carrying_a_release_job` |
| CM-21 | The release-key setup steps can only name an address the shipped `signing-key.asc` carries, so the documented way to reproduce the release key cannot drift from the key in the tree. | `tests/test_signing_docs.py:109-135` | `tests/test_signing_docs.py::SigningDocumentAddressTests::test_the_export_commands_name_the_shipped_key` |
| CM-22 | The local server answers only a request whose `Host` header names its own loopback address and port. | `gui.py:639-642` | `tests/test_gui_integration.py::LocalServerAccessTests::test_wrong_host_header_is_rejected` |
| CM-23 | Every page carries a fresh script nonce and `script-src` never allows `unsafe-inline`, so no injected script inherits an allowance. | `gui.py:588-599` | `tests/test_gui_integration.py::TransactionJourneyTests::test_the_inline_script_needs_a_nonce_not_unsafe_inline` |
| CM-24 | A broadcaster that reports a transaction id other than the reviewed one is an unknown outcome, never a landing. | `gui.py:1151-1155` | `tests/test_send_flow.py::SendFlowTests::test_mismatched_broadcast_txid_is_unknown_and_blocks_retry` |
| CM-25 | An extreme fee is refused outright and an unusual one comes back as a warning the person must see before downloading. | `wallet_service.py:60-72` | `tests/test_wallet_service.py::WalletServiceTests::test_fee_safety_stops_extreme_fee_and_flags_unusual_rates` |
| CM-26 | A file the app writes is readable only by the operator's own account: mode 0600 on POSIX, inside the operator's own profile on Windows. | `gui.py:355-379` | `tests/test_platform_port.py::PrivateFileTests::test_the_mode_check_becomes_a_profile_check_on_windows` |

## Recorded, no control claimed

| Where | Why |
| --- | --- |
| `probe.py:114-135` | CT-89: no control is claimed here — the receive/change key agreement is the template by construction, and the check that claimed otherwise was deleted. |

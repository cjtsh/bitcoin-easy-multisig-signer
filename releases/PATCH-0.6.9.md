# 0.6.9: Color Team cycle-5 remediation

The v0.6.8 audit graded **⚠️ CONDITIONAL**: the four acts the rubric forbids all
held, the money path refused every attack the lanes brought, and the published
`v0.6.8` bytes verified end to end — but four Low findings each described a
control that was *believed* rather than *pinned*, and the instrument that is
supposed to catch that class (`CONTROLS.md` and its reader) was itself one of
them.

This release closes all twelve findings. The order below is the coaching
document's: CT-03 first, because it is the instrument that would have caught
CT-01 and CT-02 on its own; then the three remaining money-path and
documentation pins; then the eight housekeeping items the audit recorded.

Every row cites a test the build loads (`tests/test_ledger_completeness.py`
holds this file to the plan), and every row was break-and-watched: the control
was broken on a disposable copy, the named test was watched going red, and the
copy was restored. Where a fix is a platform setting rather than code, the row
says what was read back.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-01 | Low | `wallet_service.py:130-134`. The malformed-body branch — a broadcast response that is not 64 hex characters raises `BroadcastOutcomeUnknown` — was unpinned because the GUI backstop at `gui.py:1103-1107` already makes the outcome safe, so no test could fail. The branch is now pinned directly, in both directions: five malformed shapes must raise, and an upper-case 64-hex body must be accepted and lower-cased so the check cannot be replaced by an unconditional refusal. Break-and-watch: deleting the length/hex test turned the malformed cases red; refusing everything turned the positive case red. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_a_malformed_body_is_unknown_not_a_transaction_id` and `tests/test_wallet_service.py::BroadcastOutcomeTests::test_an_upper_case_txid_is_accepted_and_lower_cased` |
| CT-02 | Low | Three first-line guards were pinned only by the deeper guard behind them: `gui.py:978-982` (the device returned a different transaction), `gui.py:1219-1220` (a payment from this wallet is waiting for one confirmation), and the `/api/sign` review-id path through `_current_prepared`. Per the coaching document each layer is now pinned by its own name and message rather than deleted, because each produces the sentence the operator reads. `test_a_device_returning_a_different_transaction_is_refused` asserts the message, that the prepared payment is unchanged and that no partial signature was attached; the new `test_prepare_refuses_while_a_payment_waits_for_confirmation` asserts the message and that the PSBT builder was never called; `test_signing_requires_the_reviewed_transaction` asserts the review-id refusal text for three bad ids. Break-and-watch: renaming each refusal in `gui.py` turned the named case red. | `tests/test_send_flow.py::SendFlowTests::test_a_device_returning_a_different_transaction_is_refused`, `tests/test_send_flow.py::SendFlowTests::test_prepare_refuses_while_a_payment_waits_for_confirmation` and `tests/test_send_flow.py::SendFlowTests::test_signing_requires_the_reviewed_transaction` |
| CT-03 | Low | `tests/test_controls_inventory.py` checked that a cited file existed and that the last cited line fell inside it — nothing more — while `CONTROLS.md:6-8` claimed the build "fails when a cited file, line, test or `CONTROL: CM-##` marker stops agreeing with it". The referee re-pointed CM-18 at `gui.py:10-20` and the suite stayed green. `ControlInventoryTests::test_every_row_cites_its_own_marker` now resolves each row's cited range and requires that row's own marker inside it, and every one of the 26 rows carries a marker on an existing line inside its range (so no cited line number moved). Five stale gui.py citations and CM-10's under-wide range were re-pointed as part of this. Break-and-watch: the referee's own CM-18 re-point now fails with `CM-18 cites gui.py:10-20, which carries no CONTROL: CM-18 marker`. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_cites_its_own_marker` |
| CT-04 | Low | At the `v0.6.8` tag `docs/index.html` pointed at the *previous* release's assets; it was corrected on `main` after publication, and the tag is immutable and still wrong. Pages serves the committed file, so there is no template step to hook. Every version reference on the page now names the releasing version, and a new test derives the expected version from `version.APP_VERSION` and refuses any download URL, visible version label, JSON-LD `softwareVersion` or finding-record link that disagrees — with at least one download link required per shipped platform, so a silent deletion is caught too. Break-and-watch: repointing the Windows button at `v0.6.8` failed with `docs/index.html download URLs names a version other than 0.6.9: ['0.6.8']`. | `tests/test_docs_version.py::DocsVersionTests::test_every_download_url_names_the_current_version`, `tests/test_docs_version.py::DocsVersionTests::test_every_visible_version_label_names_the_current_version`, `tests/test_docs_version.py::DocsVersionTests::test_the_finding_record_link_names_the_current_cycle`, `tests/test_docs_version.py::DocsVersionTests::test_the_json_ld_names_the_current_version` and `tests/test_docs_version.py::DocsVersionTests::test_every_platform_still_has_a_download_link` |
| CT-05 | Info | `ui.html` read the local access token out of `location.hash` and left it there, so the fragment — and the token — survived in that browser's session history for as long as the tab lived. The fragment is now read once, the value is copied into per-tab `sessionStorage` (which dies with the tab and lets a reload keep working), and the address bar is rewritten with `history.replaceState` so no history entry names it. The new JS suite drives the real page script in a Node `vm` and asserts both halves — the token reaches the app and the next request carries it, and the address bar left behind does not — so a fix that only cleared the bar would fail. Break-and-watch: removing the rewrite turned the case red. | `tests/test_ui_scripts.py::UiScriptTests::test_ui_token_history` (runs `tests/ui_token_history.cjs`) |
| CT-06 | Info | `desktop.py` wrote `"".join(traceback.format_exception(...))` into the startup failure log, which carries absolute paths from the operator's own machine. The failure is pre-wallet, so no wallet material was implicated, but the log now records the failure's type and message only, bounded to `STARTUP_FAILURE_LIMIT = 2000` characters. Break-and-watch: restoring the traceback write turned both cases red. | `tests/test_desktop.py::StartupFailureTests::test_a_failed_start_writes_the_failure_beside_the_settings` and `tests/test_desktop.py::StartupFailureTests::test_a_long_failure_message_is_bounded` |
| CT-07 | Info | `CONTROLS.md` omitted protections the code claims and pins elsewhere. Five rows and their markers were added: CM-22 the loopback `Host` gate, CM-23 the per-page script nonce and the absence of `unsafe-inline`, CM-24 the unknown-broadcast outcome, CM-25 the fee floors, CM-26 the private-file modes. Each row carries a `CONTROL: CM-##` marker on an existing line inside its cited range, so CT-03's new reader checks it like any other. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_cites_its_own_marker` plus the five rows' own closing tests: `tests/test_gui_integration.py::LocalServerAccessTests::test_wrong_host_header_is_rejected`, `tests/test_gui_integration.py::TransactionJourneyTests::test_the_inline_script_needs_a_nonce_not_unsafe_inline`, `tests/test_send_flow.py::SendFlowTests::test_mismatched_broadcast_txid_is_unknown_and_blocks_retry`, `tests/test_wallet_service.py::WalletServiceTests::test_fee_safety_stops_extreme_fee_and_flags_unusual_rates` and `tests/test_platform_port.py::PrivateFileTests::test_the_mode_check_becomes_a_profile_check_on_windows` |
| CT-08 | Info | `gui.py`'s `do_GET` answered `/api/price` and `/api/fees` without a token. Both are reads and the loopback and `Host` gates still applied, but "public" is not "unauthenticated". The market reads now sit behind the same token check as every other endpoint, and the page sends `X-Local-Token` on both fetches. The new case asserts 403 on each route with the upstream fetchers untouched; the two cached-read cases now carry the token. Break-and-watch: dropping the new branch turned the refusal case red. | `tests/test_gui.py::LocalGuiTests::test_the_market_reads_refuse_without_the_local_token`, `tests/test_gui.py::LocalGuiTests::test_price_endpoint_is_token_gated_and_cached` and `tests/test_gui.py::LocalGuiTests::test_mainnet_fee_reference_is_token_gated_and_cached` |
| CT-09 | Info | The 15-second connection budget was enforced per thread and the thread count was unbounded, so a burst of stalled connections could hold arbitrarily many threads. `gui.py` now defines `MAX_CONNECTIONS = 32` and a `BoundedThreadingHTTPServer` that acquires a `BoundedSemaphore` non-blockingly before dispatch and closes the socket rather than queueing when the ceiling is reached; both `gui.main()` and `desktop.py` build the bounded class. The new suite holds more sockets than its ceiling, asserts the excess are closed, asserts the same server answers again once slots return, and asserts `gui.main()` builds the bounded class. Break-and-watch: raising the ceiling to unbounded turned the closure case red. | `tests/test_gui_integration.py::ConnectionCeilingTests::test_sockets_beyond_the_ceiling_are_closed`, `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_same_server_answers_once_the_slots_come_back` and `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_shipped_server_is_the_bounded_class` |
| CT-10 | Info | Overwrite protection rested on the workflow's existing-tag guard, the tags ruleset and account hygiene. The platform's own immutable-release setting was off and nothing in the repository read it. It is now enabled (`{"enabled": true, "enforced_by_owner": false}` read back), read by `scripts/check-platform-state.sh` through a new `release_immutability()` reader, and recorded in `releases/platform-state.json`, so an unrecorded change to it fails the differ. Break-and-watch: the differ reported `release_immutability: not in the record` before `--record`; after recording it reports a match. | `tests/test_platform_state.py::PlatformRecordTests::test_the_platform_makes_published_releases_immutable` |
| CT-11 | Info | `build-linux.yml` and `build-windows.yml` were deleted from every branch, but the platform still lists both registrations as `disabled_manually`, and `gh api --method DELETE` answers 404 because the files survive in the immutable tag trees. A fail-closed step, `Refuse while a retired publisher is runnable`, now runs first in the `checksums` job on both the candidate and the publish path: it reads the live workflow registrations and refuses if either retired publisher is not `disabled_manually`, and it refuses on a read that did not happen, because a guard that passes by not looking is the defect. Break-and-watch: deleting the step turned the wiring case red. | `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_a_disabled_pair_is_accepted`, `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_a_re_enabled_publisher_refuses_and_names_it`, `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_a_registration_that_is_gone_is_not_a_re_enabled_one`, `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_an_unreadable_platform_refuses` and `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_the_guard_runs_on_a_candidate_and_on_a_publish` |
| CT-12 | Info | `vendor/libusb-1.0.dll` is pinned in four agreeing places — `tests/test_libusb_vendor.py`'s `REVIEWED["win32"]`, `vendor/README.md`, `scripts/build-windows.ps1`'s `$reviewedLibusbSha256`, and the `LIBUSB_WINDOWS_SHA256` repository variable — but the one-time producing run no longer survived, so the pin could not be re-matched from evidence. `windows-inputs.yml` was re-dispatched from `main` (run 38145193244, commit `48a3842a5eb390254615bd4d02876cdf1091a553`), the `windows-libusb` artifact was downloaded, and its `libusb-1.0.dll` digest was compared to the pins. | `tests/test_libusb_vendor.py::LibusbVendorTests::test_the_shipped_native_libraries_are_the_reviewed_ones` |

## Accepted floating inputs

Pinning the runner's packages to exact versions remains **declined**, for the
reason recorded in the 0.6.8 ledger and unchanged by this cycle. The runner
image's `noble-updates` and `noble-security` archives move as Canonical ships
fixes; a pinned version would fail the build on a runner refresh without making
the AppImage's bytes reproducible, because the package is only one input among
many and the pin would have to be re-derived by hand on every refresh. A pin
that breaks the build and buys nothing is not a control.

What is accepted, and what stands in for the pin:

- **The runner image's packages**: `squashfs-tools`, `librsvg2-bin`,
  `build-essential`, `fuse3`, resolved from the `ubuntu-24.04` runner's
  archives. Recorded per build in the SBOM (name and version). Declared once in
  `scripts/build-linux.sh`; a test asserts the workflow installs exactly that
  set.
- **The proof container's packages**: `fuse3` and `ca-certificates`, installed
  inside the digest-pinned `ubuntu:24.04` container. Printed into the run log;
  the proof is a pass/fail assertion about the AppImage, not shipped bytes.
- **The container image**: pinned by the digest
  `sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`;
  the refresh command is recorded beside the pin and in
  `scripts/build-linux.sh`.

A review of this release should re-run the refresh command, move the digest,
and, if any of the four runner packages changes, update `SYSTEM_PACKAGES`, this
section, and the SBOM expectations in the same commit.

## Notes

**What did not change.** No wallet, signing or broadcast behaviour changed. The
engine's refusals, the money-path gates, the fee logic, the PSBT handling and the
device handling are byte-for-byte what `v0.6.8` shipped except where a finding
named them above (CT-01's branch and CT-02's guards are comments and tests only —
no refusal message moved). `tests/test_money_path_pins.py` and the full engine
suite pass unchanged.

**The one new mechanism.** Three tiers of tests now exist where two did before:
the page-script suites under `tests/ui_*.cjs` are executed by
`tests/test_ui_scripts.py`, so they run inside `python -m unittest discover -s
tests` on every platform and a ledger row can cite one by a name that
`tests/support.py` can resolve. Before this a `.cjs` pin was unreachable
evidence: CI ran it from a glob, and the completeness reader could not see it.

**Evidence not kept in the repository.** The break-and-watch runs were performed
on a disposable copy and restored in each case; the observations are recorded
inline in the rows above rather than as kept artefacts, matching the practice
recorded in the 0.6.8 ledger.

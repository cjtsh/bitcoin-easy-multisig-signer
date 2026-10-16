# 0.7.0: Color Team cycle-6 remediation

The v0.6.9 audit graded **⚠️ CONDITIONAL**. The conversion gate was met in full —
the White referee re-broke every one of the twelve prior findings and watched its
new test go red, so all twelve are verified fixed **by execution**, and the delta
introduced no Critical or High. The grade was held by one new Low in the same
pin-accuracy family that held the two cycles before it, plus one availability
trade the new connection ceiling introduced and four housekeeping notes.

This release closes all six. Every row below cites a test the build loads
(`tests/test_ledger_completeness.py` holds this file to `releases/PLAN-0.7.0.md`),
and every control was break-and-watched: broken on a disposable copy, the named
test watched going red, the copy restored. Code citations are at the `v0.7.0`
revision — `file:line` in the tree that ships this file — unless a row says the
location is the prior revision's.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-13 | Low | `gui.py:98-137`. The cycle-5 ceiling closed every socket beyond `MAX_CONNECTIONS`, so a local process could hold all thirty-two open — a silent socket for the connection timeout, a slow drip indefinitely — and freeze the operator's own window until it stopped. The shape is changed rather than the trade accepted: `BoundedThreadingHTTPServer` now keeps an admitted-socket registry and **fair admission**. A newcomer is refused only when every admitted connection is busy; otherwise the oldest *idle* connection is retired and the newcomer takes its slot. A connection is idle from accept until a complete request head has arrived — so silence and a half-sent head are both idle — and idle again between keep-alive requests. Only a connection actually being served is protected, and reaching that state requires a complete request, which for every route that does anything requires the page's token; no unauthenticated local process can protect its own sockets from eviction. A retired socket is recorded so its handler closes without answering, rather than writing a refusal into a socket that has been shut down. The residual is stated plainly: a local process that actively serves requests — which takes the token — can still consume capacity, and that is inherent to a loopback service. **The lockout this finding described no longer exists, so no dated owner acceptance stands in for a fix.** Break-and-watch: restoring the plain refuse-when-full ceiling turned both admission cases red with a reset connection while the busy-ceiling case stayed green, and the fix turned them green again. | `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_window_is_admitted_while_idle_sockets_hold_the_ceiling`, `tests/test_gui_integration.py::ConnectionCeilingTests::test_a_slow_drip_does_not_hold_the_window_out_either` and `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_ceiling_still_refuses_when_every_slot_is_busy` |
| CT-14 | Low | `wallet_service.py:867-870` checks three prevout limbs — txid, value, script. The two tests named for the value and script limbs mutated the serialized previous transaction, which changes its txid, so both exercised the txid limb and the referee deleted each of their own limbs and watched the suite stay green. Each limb now has a case where the served transaction is left **byte-for-byte intact** and the *scan's UTXO list* is the liar: the value case claims one satoshi more per output than the honest transaction pays (with the address totals raised to match, so the consistency gate is not what refuses it), and the script case lists an outpoint under a wallet receive address while the honest transaction for that txid pays a script the wallet does not own. Only the named limb can refuse either one. The two rewritten-bytes cases were renamed to say what they actually pin — the txid limb — instead of being deleted, so that coverage is kept and honestly labelled. Break-and-watch, both directions: deleting the value limb turned only the value case red, with the fee backstop's message (its regex requires the prevout message, so the backstop cannot stand in for the limb); deleting the script limb turned only the script case red. | `tests/test_money_path_pins.py::BuildTimePrevoutPins::test_a_lying_utxo_list_value_is_refused_by_the_value_limb` and `tests/test_money_path_pins.py::BuildTimePrevoutPins::test_a_lying_utxo_list_script_is_refused_by_the_script_limb` |
| CT-15 | Info | Five protections the previous release added were claimed and pinned but missing from the parsed inventory. Six rows and their `CONTROL: CM-##` markers were added, each inside the range it cites: `CM-27` the connection ceiling and its fair-admission rule, `CM-28` the constant-time whole-token comparison, `CM-29` the market-read token gate, `CM-30` the token-history eviction, `CM-31` the bounded startup record, and `CM-32` the per-connection time budget — the last surfaced *by* the widened net rather than by the audit, which is the point of widening it. `PHRASES` gained four phrases: the claim shapes this delta used in ordinary words ("is bounded", "bounded by", "admits a fixed number", "not an open oracle"). Each addition was checked against every shipped comment block before being pinned, so widening the net cannot fail the build on wording alone, and the durable rule is recorded beside the list: a delta that adds a protection adds its row in the same commit. Break-and-watch: the reader refuses a row whose own marker is not inside its cited range, and every one of the 32 rows carries one. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_cites_its_own_marker` — plus each new row's own closing test: `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_window_is_admitted_while_idle_sockets_hold_the_ceiling`, `tests/test_gui_integration.py::LocalTokenComparisonTests::test_the_comparison_is_whole_value_and_constant_time`, `tests/test_gui.py::LocalGuiTests::test_the_market_reads_refuse_without_the_local_token`, `tests/test_ui_scripts.py::UiScriptTests::test_ui_token_history`, `tests/test_desktop.py::StartupFailureTests::test_a_long_failure_message_is_bounded` and `tests/test_gui_integration.py::StalledConnectionTests::test_stalled_bodies_are_cut_off_and_the_server_keeps_serving` |
| CT-16 | Info | `.github/workflows/build-candidate.yml`, the `Refuse while a retired publisher is runnable` step. The step read one page of the workflow registrations and concluded from it. It now refuses when `total_count` is not an integer or is larger than the page it asked for, and refuses when the returned list does not match `total_count` — a re-enabled publisher could otherwise sit on a page nobody looked at, which is the CT-11 failure shape. Pagination is deliberately *not* used: the count is what fails closed, so the guard does not depend on the runner's `gh` version supporting a pagination flag. Break-and-watch: deleting the page-limit branch turned the oversized-registration case red; restoring it turned it green. | `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_more_registrations_than_the_page_holds_refuses` and `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_a_page_shorter_than_the_reported_count_refuses` |
| CT-17 | Info | `desktop.py:388-394`. The Windows startup-failure dialog interpolated the raw exception while the file beside it held the bounded `Type: message` record, so a very long platform error became a message box that ran off the screen — and, unlike the log, was never bounded. The dialog now shows the same bounded record the log holds and names the file the full text is in. Break-and-watch: interpolating the raw exception again turned the bounded-dialog case red. | `tests/test_desktop.py::StartupFailureTests::test_the_windows_dialog_shows_the_bounded_record_too` and `tests/test_desktop.py::StartupFailureTests::test_windows_also_shows_a_dialog_naming_the_report` |
| CT-18 | Info | `releases/PATCH-0.6.9.md`, the CT-12 row. Its "unchanged" sentence described the whole `windows-inputs.yml` file as differing only in comments and the `windows-latest` → `windows-2022` runner pin, which omitted the separate `lock` job's hardening. The sentence is now scoped to the `libusb` job it is about and enumerates the rest of the file's delta since the producing run's commit `a1564c0`: comments, the runner pin on both jobs, and the `lock` job's interpreter pinned from `3.12` to `3.12.10` and `pip-tools` installed under `--require-hashes -r requirements-piptools.lock`. The correction is marked inline in that row, dated to this cycle, so the amendment is visible rather than silent — the repository's rule is that a record is not rewritten to match the present, and a record that misdescribed its own file is corrected in the open. The load-bearing claim was re-verified true: the four `libusb` pins still agree with each other and with the shipped file. Recorded evidence, not a test; the pins themselves are held by the cited test. | `tests/test_libusb_vendor.py::LibusbVendorTests::test_the_shipped_native_libraries_are_the_reviewed_ones` |

## Accepted floating inputs

Pinning the runner's packages to exact versions remains **declined**, for the
reason recorded in the 0.6.8 and 0.6.9 ledgers and unchanged by this cycle. The
runner image's `noble-updates` and `noble-security` archives move as Canonical
ships fixes; a pinned version would fail the build on a runner refresh without
making the AppImage's bytes reproducible, because the package is only one input
among many and the pin would have to be re-derived by hand on every refresh. A
pin that breaks the build and buys nothing is not a control.

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

## Corrections to earlier records

- **`releases/PATCH-0.6.9.md`, CT-12 row (CT-18):** the "only differences"
  sentence is corrected in place and marked as a correction, as described in the
  row above. No other earlier record was edited: the v0.6.9 audit plan, lock,
  report and security statement, and the v0.6.8 artifacts archived under
  `audit-history/`, are byte-identical to what was published.

## Notes

**What did not change.** No wallet, signing or broadcast behaviour changed. The
engine's refusals, the money-path gates, the fee logic, the PSBT handling and the
device handling are byte-for-byte what `v0.6.9` shipped except where a finding
named them above — and the two money-path rows are tests only, with no change to
`wallet_service.py`'s conditions. The full engine suite passes unchanged.

**The one behaviour change, and where it is felt.** Fair admission changes what a
*local flood* sees: the thirty-third socket is no longer refused outright while
an idle connection holds a slot; instead the oldest idle connection is hung up
and the newcomer is served. A clean client sees no difference at all, and a
surplus connection with every slot busy is still refused exactly as before.

**Evidence not kept in the repository.** The break-and-watch runs were performed
on a disposable copy and restored in each case; the observations are recorded
inline in the rows above rather than as kept artefacts, matching the practice
recorded in the earlier ledgers.

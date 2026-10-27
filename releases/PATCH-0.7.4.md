# 0.7.4: Color Team cycle-10 remediation

The v0.7.3 audit graded **⚠️ CONDITIONAL**. The v0.7.2 block was discharged **by
execution** — the referee personally re-broke CT-27's marker arm and its clear,
CT-29's reconcile and CT-33's transport tuple, and watched each named pin go red;
CT-32, CT-34 and CT-35 were closed by written dated owner acceptance; CT-01…CT-26
were carried with no regression — and the grade holds on two new findings in the
delta, **CT-36 (Medium)** and **CT-41 (Low)**, plus a record-accuracy Low (CT-43).

CT-36 is the floor-setter: `broadcast_transaction` treated every HTTP 4xx as a
definite refusal, and the GUI handler then cleared the in-flight marker and recorded
nothing, under a comment saying a definite refusal sent nothing. But a 4xx arrives
after the server has the complete signed transaction — an honest Esplora answers
exactly that way when it already holds the payment — so a second, differently
reviewed payment of the same wallet could leave with the pause the v0.7.3 cycle
added never armed. One examiner demonstrated that end to end and the referee
re-executed it. CT-41 is the missing alarm behind the early in-flight half of the
same gate: the behaviour was right, but deleting the half left every named pin
green, so the CLEARED clause "held by a test that can fail" was not met.

This release closes CT-36 and CT-37 (the same classification defect in its raw-
exception form), CT-41, CT-43, and the two inventory gaps CT-39 and CT-40. It
records the three notes it called housekeeping (CT-38, CT-42, CT-44). Every row
below cites a test the build loads (`tests/test_ledger_completeness.py` holds this
file to `releases/PLAN-0.7.4.md`), and every control was break-and-watched on a
disposable copy — broken, the named test watched going red, the copy restored
byte-for-byte and re-run green. The transcripts are in
`releases/BREAK-AND-WATCH-0.7.4.md`. Code citations are `file:line` in the tree that
ships this file (0.7.4), unless a row quotes coordinates at the prior revision
`a227da4` to describe the defect.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-36 | Med | `wallet_service.py:100-146` and `gui.py:1366-1399`. The app can prove nothing was sent only for the checks that run before the POST is written, so those now raise a new `BroadcastNotSent(WalletError)`: unsupported network, missing mainnet opt-in, unusable size, invalid hex, and a settings refusal from `validate_esplora_url`. Everything after that point — every HTTP answer, 4xx included — raises `BroadcastOutcomeUnknown` carrying the server's own words as evidence ("The server said: …") and a message that says the result is unknown, never that it was refused. In `gui.py` the old two handlers collapse into two arms that ask the type: `except BroadcastNotSent` clears the in-flight marker and re-raises, so the reviewed payment stays retryable because the app proved it never left; `except BaseException` converts anything else into `BroadcastOutcomeUnknown`, then under the lock clears the marker, records `record_pending(wallet, txid, True)`, drops the prepared payment and raises with `exc.explorer` attached. Threads are handled by type, not by status code. Break-and-watch: the 4xx re-classified as `WalletError` turned the engine pin red with `wallet_service.WalletError: The network refused this transaction HTTP 400 after receiving this payment…`; the pre-POST raise turned into a plain `WalletError` turned the not-sent pin red on its `chain='bogus'` subTest. Rows `CM-46`, `CM-49`, `CM-50`. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_a_client_rejection_is_unknown_not_a_definite_refusal` |
| CT-41 | Low | `gui.py:1280-1293`. The early gate refuses a second payment while this wallet's earlier submit is on the wire, before any explorer is asked about the wallet's outputs — but no test could fail if that half were deleted, because the request then reached the in-lock half and was refused there a moment later. The new pin arms `broadcast_in_flight[wallet]` before the POST and asserts the refusal, the message, that the broadcaster was never called and that `verify_selected_outpoints` was never called. Production code is unchanged: the behaviour was already right; the alarm was missing. Break-and-watch: the half replaced by `if False:` turned the pin red with `AssertionError: Expected 'verify_selected_outpoints' to not have been called. Called 1 times.`; the restore was byte-identical and the pin went green again. Row `CM-38`. | `tests/test_send_flow.py::SendFlowTests::test_a_broadcast_racing_an_in_flight_submit_asks_no_explorer` |
| CT-37 | Low | `gui.py:1366-1399`. The same handler caught `BaseException` and treated every escape as a definite refusal, so a raw `RuntimeError` from the submit path popped the marker and left the payment retryable with no evidence that nothing was sent. The handler now converts anything that is not `BroadcastNotSent` into `BroadcastOutcomeUnknown`, records the payment against the wallet and reports `outcome_unknown` — the fail-safe direction, because a raw escape proves nothing about whether bytes were written. Break-and-watch: the conversion branch replaced by `if False:` turned the pin red with `AssertionError: 500 != 409`; the restore was byte-identical and the pin went green again. Row `CM-46`. | `tests/test_send_flow.py::SendFlowTests::test_an_unclassified_submit_failure_pauses_the_wallet` |
| CT-43 | Low | `RELEASE-HISTORY.md` and `CURRENT-STATUS.md`. The v0.7.3 row recorded two runs and two attempts; the live window is five dispatched runs and nine attempts. Both records now name every one: run `40432734241` cancelled (dispatched twenty seconds before the tag it named existed), run `40432782352` a candidate dispatched without `notarize=true` whose macOS job therefore skipped signing and notary and which promote `40433752825` refused at the manifest check after two staple/validate flakes of its own, run `40436678735` whose first attempt failed on Apple's staple/validate service (`Error 68`, CloudKit `-1005`, after the notary service had answered `Accepted`) and second on `hdiutil: create failed - Resource busy` before finishing green, and promote `40439588346` which published on its first attempt. Nothing was published from any failure, and the manifest check firing on the unsigned candidate is recorded as the safety system working, not as a gap. Nowhere is a run credited that did not happen. | `tests/test_hardening_pins.py::ReleaseWindowDisclosureTests::test_the_0_7_3_row_names_every_run_of_its_window` (with `…::test_the_pin_would_fail_on_the_old_two_run_record` as its negative half) |
| CT-39 | Info | `CONTROLS.md:67` at `a227da4` cited `gui.py:1329-1349` for `CM-43`, five lines short of `state.broadcast_in_flight[wallet] = txid` at `gui.py:1354` — the arm the row's claim is about. `CM-43` now cites `gui.py:1333-1354`, which contains the arm, and the `CONTROL: CM-43` marker sits above the check-and-arm block. The inventory test binds the citation to its own marker, so a range that stops short of the arm is now a red build rather than a reading exercise. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_cites_its_own_marker` |
| CT-40 | Info | `gui.py:1145-1160` and `gui.py:1251-1265`. The final-versus-review comparison (outputs, amounts, fee, the change output's address) and the `preparation_id` binding on the money endpoints were real protections — the panel broke both and watched them refuse — but neither had a `CONTROLS.md` row. `CM-47` and `CM-48` are those rows, each with its own `CONTROL:` marker inside its cited range and its own pin. Break-and-watch: the comparison removed turned `…::test_broadcast_refuses_a_final_transaction_that_differs_from_the_review` red with `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.`; the binding removed turned `…::test_money_endpoints_refuse_a_stale_review_id_by_name` red with `AssertionError: 'Review the current transaction' not found in 'Input 1 has 0 of 2 required signatures.'`. Every restore was byte-identical and every pin went green again. `CONTROLS.md` is at 50 rows. | `tests/test_send_flow.py::SendFlowTests::test_broadcast_refuses_a_final_transaction_that_differs_from_the_review` |

## Observations recorded

The audit called these three housekeeping and graded none of them with an asset
path; none changes behaviour, so none has a closing test and none is scheduled.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| **CT-38** | The signed v0.7.3 plan's §5 T-10 cites a test name that does not exist at this revision. | The pinned plan is hash-locked (SHA-256 `83534f9e…4c` at start and end), so rewriting it after the audit would void the cycle. The substance the citation was reaching for is covered by `tests/test_send_flow.py::SendFlowTests::test_a_definite_refusal_clears_the_in_flight_marker` and `tests/test_gui.py::LocalGuiTests::test_a_second_payment_cannot_clear_the_first_one_s_pause`, both green in this tree. This plan's every `file:line` was taken from the tree at `a227da4` and re-checked against the tree that ships it. |
| **CT-42** | A lying-txid pause records the intended txid, which an honest explorer can never report confirmed, so the wallet stays paused until the session ends. | Accepted as a residual in the fail-closed direction: the alternative, trusting a txid the server invented, is what the pause exists to prevent. The message already tells the operator to check an explorer before retrying. The status-endpoint remedy is on the next-cycle list. |
| **CT-44** | Legacy-tag residual: 46 dispatchable tags enumerated; sweep green. | Restated here and on the next-cycle list. `scripts/check-publish-paths.sh:89-96` still enumerates them and the sweep is green in this tree; nothing new is claimed about the legacy tags. |

## Accepted floating inputs

Unchanged from `releases/PATCH-0.7.0.md` … `releases/PATCH-0.7.3.md`, and restated
here because a reviewer should be able to read this ledger on its own. Pinning the
runner's packages to exact versions remains **declined**: the `noble-updates` and
`noble-security` archives move as Canonical ships fixes, a pin would fail the build
on a runner refresh without making the AppImage reproducible, and the package is
only one input among many. A pin that breaks the build and buys nothing is not a
control.

What is accepted, and what stands in for the pin:

- **The runner image's packages**: `squashfs-tools`, `librsvg2-bin`,
  `build-essential`, `fuse3`, resolved from the `ubuntu-24.04` runner's archives.
  Recorded per build in the SBOM (name and version), declared once in
  `scripts/build-linux.sh`, and a test asserts the workflow installs exactly that
  set.
- **The proof container's packages**: `fuse3` and `ca-certificates`, installed
  inside the digest-pinned container. Printed into the run log; the proof is a
  pass/fail assertion about the AppImage, not shipped bytes.
- **The container image**: pinned by the digest
  `sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`;
  the refresh command is recorded beside the pin and in `scripts/build-linux.sh`.

## Notes

- **The candidate manifest is part of the release check.** The v0.7.3 window's
  refused promote is the reason the workflow's gate exists: a candidate built
  without `notarize=true` produces an unsigned DMG, and the promote's
  `grep -Fx "notarize=true"` manifest check refuses it. Before dispatching a
  promote, read the candidate's `manifest.txt`, which records `version`, `commit`,
  `run_id`, `notarize` and `publish`.
- **What CT-36 does not claim.** It does not claim an Esplora is honest or that a
  4xx means the payment was accepted. It claims the app cannot tell, which is the
  only thing the bytes in hand support, and it acts on that: unknown outcome,
  wallet paused, operator told to check an explorer.
- **No lock is held across the submit.** The classification change adds no I/O
  under `state.lock`; the handler takes the lock only to clear the marker, record
  the payment and drop the prepared transaction, exactly as before.

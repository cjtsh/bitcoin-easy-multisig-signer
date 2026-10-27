# 0.7.5: Color Team cycle-11 remediation

The v0.7.4 audit graded **⚠️ CONDITIONAL**, with everything else in the cycle at
CLEARED level. The v0.7.3 block was discharged **by execution** — the referee
personally re-broke the 4xx→unknown branch (`wallet_service.py`) and the
unknown-conversion branch (`gui.py`), watched each named pin go red, restored the
copy byte-for-byte and watched it go green — and CT-36 and CT-41 are converted by
execution. CT-01…CT-44 were carried with no regression.

The grade holds on two missing alarm tests over one control. **CT-47** is the
settings-refusal branch of the not-sent boundary: the app refuses to send when the
configured Esplora URL is not a plain URL, and that refusal is provably pre-POST, so
it raises `BroadcastNotSent` and the reviewed payment stays retryable — but no test
exercised the branch, so its regression to the old definite-refusal text would leave
the suite green. **CT-49** is the same control's claim about *position*: the pin
asserts the exception class for each input shape, not that no request object was
built, so moving a raise below the `Request(...)` construction would keep every pin
green while the app claimed a provable non-send after the point of no return.

This release adds the two alarms without changing production behaviour, adds the
argument-type guard the engine's own contract implies (CT-45), keeps a deliberate
abort distinct from a lost reply (CT-46), and makes the newest release window's
history row a pinned test (CT-51). It records the three notes the audit called
housekeeping (CT-48, CT-50, CT-52) and restates the two carried ones (CT-38,
CT-44). Every row below cites a test the build loads (`tests/test_ledger_completeness.py`
holds this file to `releases/PLAN-0.7.5.md`), and every control was
break-and-watched on a disposable copy — broken, the named test watched going red,
the copy restored byte-for-byte and re-run green. The transcripts are in
`releases/BREAK-AND-WATCH-0.7.5.md`. Code citations are `file:line` in the tree that
ships this file (0.7.5), unless a row quotes coordinates at the prior revision
`9d4d7bb` to describe the defect.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-47 | Info | `wallet_service.py:113-116` at `9d4d7bb` — the settings-refusal branch. The branch already behaved correctly: `validate_esplora_url` raising `SettingsError` is converted to `BroadcastNotSent`, so the payment is left retryable and nothing is sent. The defect was that no named test could fail if the conversion were reverted. The new pin drives three settings-rejected `base_url` shapes (credentials, query string, fragment) through `broadcast_transaction`, asserts the exception class and the settings message, and asserts `urlopen` was never called. Production code is unchanged. Break-and-watch: reverting the conversion to `WalletError` turned the pin red on the `base_url='http://example.com/api'` subTest with `wallet_service.WalletError: Use a plain Esplora URL without credentials, query, or fragment.`; the restore was byte-identical and the pin went green again. Row `CM-50`. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_a_settings_rejected_url_is_provably_not_sent` |
| CT-49 | Low | `tests/test_wallet_service.py:73-93` against `wallet_service.py:103,116` at `9d4d7bb`. The pin checked the class per shape but not the checks' position, so the invariant "no not-sent answer after the request is written" was pinned for the mainnet, size and hex branches and unpinned for chain and settings. The new pin patches `wallet_service.Request` with `wraps=` and `urlopen`, drives five provably pre-POST refusal shapes (unknown chain, mainnet without opt-in, unusable size, invalid hex, settings-refused URL), and asserts neither was called. Production code is unchanged. Break-and-watch: constructing a `Request` above the gate turned the pin red with `AssertionError: Expected 'Request' to not have been called. Called 1 times.`; the restore was byte-identical and the pin went green again. Row `CM-50`. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_no_not_sent_answer_is_raised_after_the_request_is_built` |
| CT-45 | Low | `wallet_service.py:102-122`. The engine is a public entry point, so its argument types are part of its contract: a non-string `chain` used to reach the `EXPLORERS[...]` lookup and escape as `TypeError: unhashable type: 'list'`, and a non-string hex reached `.strip()` as an `AttributeError` — raw tracebacks out of a function that promises the not-sent refusal for everything it refuses before writing. Both are now `BroadcastNotSent` ("Unsupported broadcast network.", "The finalised transaction is not valid hex.") before any other work. The GUI passes a pinned chain and a `str` hex, so app behaviour is unchanged. Break-and-watch: removing the `isinstance(chain, str)` guard turned the pin red with `TypeError: unhashable type: 'list'` on the `chain="['testnet4']"` subTest; the restore was byte-identical and the pin went green again. Row `CM-50`. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_non_contract_argument_types_are_refused_before_anything_is_sent` |
| CT-46 | Info | `gui.py:1382-1405`. Inside the `except BaseException` arm the pause is armed and the payment recorded — correct, because bytes may have left — but the exception was then replaced by `BroadcastOutcomeUnknown`, so an embedding host could not tell a deliberate abort from a lost reply. After the payment is recorded, a `BaseException` that is not an `Exception` is now re-raised unchanged; an ordinary failure is still converted to the unknown outcome. The fail-closed property is identical either way. Break-and-watch: replacing the bare re-raise with `if False: raise` turned the pin red with `AssertionError: KeyboardInterrupt not raised`; the restore was byte-identical and the pin went green again. Row `CM-46`. | `tests/test_send_flow.py::SendFlowTests::test_an_interrupt_during_the_submit_arms_the_pause_and_still_propagates` |
| CT-51 | Info | `RELEASE-HISTORY.md` and `tests/test_hardening_pins.py::ReleaseWindowDisclosureTests`. The v0.7.4 row records its window accurately — candidate `40498861357` green on its first attempt, promote `40500477931` whose first attempt failed on Apple's staple (`Error 68`, CloudKit `-1005`, after the notary service answered `Accepted`) and whose second published — but only the v0.7.3 row was held by a test, and at the tag the newest row does not exist. The class now carries `LATEST_WINDOW` (version, both run ids, the counts phrase) and a test that reads the newest `| **<version>** |` row and requires every run id, the counts and "nothing was published from" in it, with a negative half that shows a one-run sentence fails. The constant moves with each cycle. Break-and-watch: renaming run `40498861357` to `40498861399` turned the pin red with `AssertionError: '40498861357' not found in "| **0.7.4** | Color Team cycle-10 remediation…"`; the restore was byte-identical and the pin went green again. | `tests/test_hardening_pins.py::ReleaseWindowDisclosureTests::test_the_newest_row_names_every_run_of_its_window` (with `…::test_the_newest_window_pin_would_fail_without_a_run` as its negative half) |

## Observations recorded

The audit graded these with no asset path or as accepted residuals; none changes
behaviour, so none has a closing test and none is scheduled.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| **CT-48** | CT-43's negative half is static string arithmetic on an embedded record, not an execution of the pin against it. | The substance holds: the referee executed the composition by hand, and the main pin discriminates — it is break-and-watched above (renaming a run turns it red). The negative half stays a string assertion because the alternative, a second fixture history file, would test a copy of the record instead of the record. |
| **CT-50** | A pause recorded against a lying txid can never be reconciled by an honest explorer, so the wallet stays paused until the session ends. | Accepted residual in the fail-closed direction, unchanged: the alternative — trusting a txid the server invented — is what the pause exists to prevent. The message already tells the operator to check an explorer before retrying, and the status-endpoint remedy is on the next-cycle list. |
| **CT-52** | The Apple staple flake recurred in this window's promote attempt 1; it has now appeared in the 0.7.2, 0.7.3 and 0.7.4 windows. | Restated residual: every failure is fail-closed and publishes nothing, the failed job was re-run once, and attempt 2 published. No work order — the only alternative is weakening the gate during a release, which was declined. |

## Accepted floating inputs

Unchanged from `releases/PATCH-0.7.0.md` … `releases/PATCH-0.7.4.md`, and restated
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

- **The candidate manifest is part of the release check.** Before dispatching a
  promote, read the candidate's `manifest.txt`, which records `version`, `commit`,
  `run_id`, `notarize` and `publish`; the promote's `grep -Fx "notarize=true"`
  check refuses a candidate built without it, and that guard has already fired for
  real once (the v0.7.3 window).
- **What the CT-47 and CT-49 alarms do not claim.** They do not claim the settings
  refusal could fail in production — it cannot, because it runs before the request
  is built. They claim the suite would have stayed green if it had, which is the
  clause the grade binds on.
- **CT-45's guard is not an input-validation program.** It covers the two argument
  types the engine itself dereferences. The values inside a correctly typed chain
  and hex are still validated by the existing gates below it.
- **No lock is held across the submit.** None of this cycle's changes adds I/O
  under `state.lock`; the handler takes it only to clear the marker, record the
  payment and drop the prepared transaction, as before.

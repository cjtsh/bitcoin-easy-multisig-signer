# Break-and-watch — 0.7.5 <span>·</span> cycle 11

Recorded: 2026-10-27, 12:03 EDT. Every control this cycle claims to have added,
widened or moved was broken on a disposable copy of the tree
(`/Users/christerry/projects/kimicode/scratch/bw075`), the named test was watched
going red, the copy was restored byte-for-byte, and the same test was re-run green.
The driver is `/Users/christerry/projects/kimicode/scratch/break-and-watch-0.7.5.py`;
the raw transcript is `break-and-watch-0.7.5.log`, which ends
`summary: all controls discriminated` (5 cases, every one red then green).

The fifteen cases recorded in `releases/BREAK-AND-WATCH-0.7.4.md` were then re-run
against this tree with
`/Users/christerry/projects/kimicode/scratch/break-and-watch-0.7.4.py`; all fifteen
were red then green again and the driver ended `summary: all controls
discriminated`. Twenty cases in total, no restore leaving a discrepancy.

| Control | Claim it stands for | Broken by | Watched red as |
| --- | --- | --- | --- |
| `CM-50` (settings branch) — CT-47 | A settings-refused Esplora URL is a provable not-send, so the reviewed payment stays retryable and nothing is written. | Reverting the `except SettingsError` conversion to `WalletError`. | `ERROR: test_a_settings_rejected_url_is_provably_not_sent (…) (base_url='http://example.com/api')` — `wallet_service.WalletError: Use a plain Esplora URL without credentials, query, or fragment.` |
| `CM-50` (position) — CT-49 | No not-sent refusal is raised after the request object exists; every pre-POST refusal is before the point of no return. | Constructing a `Request` above the first gate. | `FAIL: test_no_not_sent_answer_is_raised_after_the_request_is_built (…) (chain='bogus')` — `AssertionError: Expected 'Request' to not have been called. Called 1 times.` |
| `CM-50` (argument types) — CT-45 | The engine refuses a non-contract argument type with the not-sent refusal, because nothing can have been written. | Removing the `isinstance(chain, str)` guard. | `ERROR: test_non_contract_argument_types_are_refused_before_anything_is_sent (…) (chain="['testnet4']")` — `TypeError: unhashable type: 'list'` |
| `CM-46` (abort) — CT-46 | A deliberate abort arms the pause and is then re-raised unchanged, so a host can tell it from a lost reply. | Replacing the bare re-raise with `if False: raise`. | `FAIL: test_an_interrupt_during_the_submit_arms_the_pause_and_still_propagates (…)` — `AssertionError: KeyboardInterrupt not raised` |
| `CT-51` (rolling window) | The newest release window's history row names every run of its window, cancelled and flake-failed ones included. | Renaming run `40498861357` in the 0.7.4 row to `40498861399`. | `FAIL: test_the_newest_row_names_every_run_of_its_window (…) (run='40498861357')` — `AssertionError: '40498861357' not found in "| **0.7.4** | Color Team cycle-10 remediation…"` |

## Notes on three that need a sentence of their own

**The two Tier-1 alarms are tests of absence, and the break is the only thing that
proves they exist.** CT-47's branch and CT-49's position are right in production —
the referee executed them at zero I/O — so no functional test can go red when the
alarm is missing. Reverting the branch (CT-47) and constructing the request early
(CT-49) are the two edits a careless future change would make, and each turns
exactly one named pin red.

**CT-45's break is a raw traceback, which is the defect the audit named.** With the
guard removed the list-shaped chain reaches the `EXPLORERS[...]` lookup and Python
raises `TypeError: unhashable type: 'list'`. The pin asserts `BroadcastNotSent`
*before* the lookup, so the red is the type of the exception, not its message.

**CT-51's red comes from prose, and the test says so.** The pin reads
`RELEASE-HISTORY.md`, so a renumbered run is a red build rather than a history that
quietly disagrees with GitHub. Its second test pins the negative: a row naming only
the run that published fails the same check.

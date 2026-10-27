# Break-and-watch — 0.7.3 <span>·</span> cycle 9

Recorded: 2026-10-26, 22:40 EDT. Every control this cycle claims to have added or
moved was broken on a disposable copy of the tree
(`/Users/christerry/projects/kimicode/scratch/bw073`), the named test was watched
going red, the copy was restored byte-for-byte, and the same test was re-run green.
The driver is `/Users/christerry/projects/kimicode/scratch/break-and-watch-0.7.3.py`;
the raw transcript is `break-and-watch-0.7.3.log`, which ends
`summary: all controls discriminated`.

| Control | Claim it stands for | Broken by | Watched red as |
| --- | --- | --- | --- |
| `CM-38` | The pause is asserted at the submit, before any explorer is asked about the wallet's outputs. | Replacing the early `if pending_txid:` with `if False:`. | `AssertionError: Expected 'verify_selected_outpoints' to not have been called. Called 1 times.` |
| `CM-43` (pending) | The pause is re-asserted under the pre-submit lock, so a payment that becomes unconfirmed mid-request is refused. | Replacing the in-lock `if state.pending_for(wallet)[0]:` with `if False:`. | `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.` |
| `CM-43` (arm) | The in-flight marker is armed inside the same critical section that checks it, before the lock is released. | Deleting `state.broadcast_in_flight[wallet] = txid`. | `AssertionError: 409 != 400` — the second payment reached the broadcaster and the request returned the unknown-outcome refusal. |
| `CM-43` (in-flight) | The in-lock check reads the marker, so a submit mid-air refuses the next one. | Replacing the in-lock `if state.broadcast_in_flight.get(wallet):` with `if False:`. | `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.` |
| `CM-43` (clear) | Every exit clears the marker, so a refused submit does not lock the wallet out. | Deleting the `except BaseException:` pop. | The armed-marker assertion in `test_a_definite_refusal_clears_the_in_flight_marker` failed on the set difference it printed. |
| `CM-44` | A scan clears only the txids the explorer confirms, and keeps the rest of the pause. | Deleting the reconciliation loop in `_scan`. | `urllib.error.HTTPError: HTTP Error 500: Internal Server Error` — the pin's second scan hits the unarmed clear. |
| `CM-40` | A reset mid-reply is the documented settings refusal, not a 500. | Removing `OSError` from `verify_esplora`'s tuple. | `ConnectionResetError: [Errno 54] Connection reset by peer` escaping the caller. |
| `CM-45` | The archive scan reads the extracted tarball, not the worktree. | Rewriting the step to scan `.` instead of `tar xzf … -C "$RUNNER_TEMP/scanned"`. | `AssertionError: 'tar xzf' not found in …` |

## Notes on the two that needed a second shape

**`CM-43` (arm) first failed on the wrong axis.** The original pin let the broken
build hang: with the marker never armed, the second submit reached the held
broadcaster and never returned, so the test timed out instead of failing. The fake
broadcaster now returns `"11" * 32` for the second call, which turns the same
defect into `409 != 400` — a refusal the test can name — while the assertion that
`broadcast_transaction` was called exactly once stays the real claim.

**`CM-44`'s red came through the HTTP layer.** The pin drives `/api/scan`, so the
broken copy answers 500 before any assertion runs. That is still the pin
discriminating (the restored tree answers 200 and the assertion passes), but it is
worth saying plainly: this is a test that fails by refusing to answer, not by
printing a message, and a reader should not mistake the 500 for an unrelated
breakage.

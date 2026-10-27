# Break-and-watch — 0.7.4 <span>·</span> cycle 10

Recorded: 2026-10-27, 07:35 EDT. Every control this cycle claims to have added,
widened or moved was broken on a disposable copy of the tree
(`/Users/christerry/projects/kimicode/scratch/bw074`), the named test was watched
going red, the copy was restored byte-for-byte, and the same test was re-run green.
The driver is `/Users/christerry/projects/kimicode/scratch/break-and-watch-0.7.4.py`;
the raw transcript is `break-and-watch-0.7.4.log`, which ends
`summary: all controls discriminated` (15 cases, every one red then green).

| Control | Claim it stands for | Broken by | Watched red as |
| --- | --- | --- | --- |
| `CM-49` (was the engine's 4xx branch) | An HTTP answer received after the signed bytes were written is an unknown outcome, never a refusal. | Re-classifying the 4xx branch as `raise WalletError("The network refused this transaction …")`. | `wallet_service.WalletError: The network refused this transaction HTTP 400 after receiving this payment, so it may already have been accepted. Do not send this p…` — the engine pin asserts `BroadcastOutcomeUnknown`. |
| `CM-50` | The not-sent refusal is reserved for the checks that run before the POST is written. | Turning the first pre-POST raise into a plain `WalletError`. | `wallet_service.WalletError: Unsupported broadcast network.` — thrown out of the `chain='bogus'` subTest of `test_only_a_preflight_refusal_is_provably_not_sent`. |
| `CM-46` (raw escape) | Once the bytes are handed over, every failure that is not provably not-sent is recorded as unknown. | Replacing the type check that converts a raw escape with `if False:`. | `AssertionError: 500 != 409` — the unclassified `RuntimeError` reached the generic handler instead of pausing the wallet. |
| `CM-46`/`CM-49` (the same 4xx break, seen from the GUI side) | The reviewed payment is not left retryable on the strength of a status code. | The `WalletError` re-classification above. | The engine pin's `BroadcastOutcomeUnknown` assertion failed as shown. |
| `CM-38` (pending half) | The pause is asserted at the submit, before any explorer is asked about the wallet's outputs. | Replacing the early `if pending_txid:` with `if False:`. | `AssertionError: Expected 'verify_selected_outpoints' to not have been called. Called 1 times.` |
| `CM-43` (in-flight half, early) | The early gate refuses a second payment while the first is on the wire, before any explorer is asked. | Replacing the early `if in_flight:` with `if False:`. | `AssertionError: Expected 'verify_selected_outpoints' to not have been called. Called 1 times.` — the CT-41 pin, which exists because nothing else could fail here. |
| `CM-43` (pending, in-lock) | The pause is re-asserted under the pre-submit lock. | Replacing the in-lock `if state.pending_for(wallet)[0]:` with `if False:`. | `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.` |
| `CM-43` (arm) | The in-flight marker is armed inside the same critical section that checks it, before the lock is released. | Deleting `state.broadcast_in_flight[wallet] = txid`. | `AssertionError: 409 != 400` — the second payment reached the broadcaster and the request returned the unknown-outcome refusal. |
| `CM-43` (in-flight, in-lock) | The in-lock check reads the marker, so a submit mid-air refuses the next one. | Replacing the in-lock `if state.broadcast_in_flight.get(wallet):` with `if False:`. | `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.` |
| `CM-43` (clear) | A provable not-sent refusal clears the marker and records nothing, so the reviewed payment stays retryable. | Deleting the `except BroadcastNotSent:` pop. | The armed-marker dict assertion in `test_a_definite_refusal_clears_the_in_flight_marker` failed on the set difference it printed. |
| `CM-47` | The finalised transaction is compared output by output and fee by fee with the reviewed payment before any submit. | Replacing the comparison condition with `if False and (…)`. | `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.` |
| `CM-48` | A money endpoint refuses a stale `preparation_id`. | Replacing `if data.get("preparation_id") != payment.review_id:` with `if False:`. | `AssertionError: 'Review the current transaction' not found in 'Input 1 has 0 of 2 required signatures.'` |
| `CM-44` | A scan clears only the txids the explorer confirms, and keeps the rest of the pause. | Deleting the reconciliation loop in `_scan`. | `urllib.error.HTTPError: HTTP Error 500: Internal Server Error` — the pin's second scan hits the unarmed clear. |
| `CM-40` | A reset mid-reply is the documented settings refusal, not a 500. | Removing `OSError` from `verify_esplora`'s tuple. | `ConnectionResetError: [Errno 54] Connection reset by peer` escaping the caller. |
| `CM-45` | The archive scan reads the extracted tarball, not the worktree. | Rewriting the step to scan `.` instead of `tar xzf … -C "$RUNNER_TEMP/scanned"`. | `AssertionError: 'tar xzf' not found in …` |
| `CT-43` disclosure | The 0.7.3 history row names every run of its window, cancelled and refused ones included. | Renaming run `40432734241` in the row to `40432739999`. | `AssertionError: '40432734241' not found in "| **0.7.3** | Color Team cycle-9 remediation…"` on the `run='40432734241'` subTest. |

## Notes on three that need a sentence of their own

**`CM-49` and `CM-46` were watched separately because they are different halves of
one decision.** The engine decides what a reply means; the GUI decides what to do
with a failure that escapes the engine. Breaking the 4xx branch reddens the engine
pin (`test_a_client_rejection_is_unknown_not_a_definite_refusal`); replacing the
GUI conversion reddens the wallet-state pin (`test_an_unclassified_submit_failure_pauses_the_wallet`).
Neither break covers the other, which is why CT-36 and CT-37 are separate rows.

**The CT-41 pin only exists to be broken.** Deleting the early in-flight half
reddens nothing else — the request falls through to the in-lock half and is refused
there, as the audit demonstrated. That is exactly why the pin asserts on the
explorer-facing pre-check rather than on the refusal: what the half uniquely buys
is that no explorer is asked before the refusal.

**`CT-43`'s red comes from prose, and the test says so.** The pin reads
`RELEASE-HISTORY.md`, so a renumbered run is a red build rather than a history that
quietly disagrees with GitHub. Its second test pins the negative: the old
two-run sentence fails the same check.

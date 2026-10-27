# 0.7.3: Color Team cycle-9 remediation

The v0.7.2 audit graded **⛔ BLOCKED**. The v0.7.1 conversion criterion was met
**by execution** — the referee re-broke CT-22, CT-24 and CT-25 and watched each
named pin go red, CT-23 and CT-26 were closed by dated owner acceptance, and
CT-01…CT-21 were carried with no regression — but the delta introduced
**CT-27 (Medium)**, which is grade-binding: both halves of the broadcast pause read
a record that was written only after the first broadcast returned, so for up to
`BROADCAST_TIMEOUT_SECONDS = 20.0` (`wallet_service.py:40`) the pause was empty and
a second, separately reviewed payment could pass both halves and be broadcast. Two
examiners demonstrated it end to end through the real `/api/*` routes. Threat row
T-11 forbids exactly that outcome, and the framework's ruling 4 makes a T-11
violation blocking at any severity.

This release closes CT-27 and its false comment (CT-28), the per-txid record the
defect exposed (CT-29), one missing exception class beside the transport tuples
(CT-33), and the two inventory gaps the audit called out (CT-30, CT-31). It records
the three notes it called housekeeping (CT-32, CT-34, CT-35). Every row below
cites a test the build loads (`tests/test_ledger_completeness.py` holds this file
to `releases/PLAN-0.7.3.md`), and every control was break-and-watched on a
disposable copy — broken, the named test watched going red, the copy restored
byte-for-byte and re-run green. The transcripts are in
`releases/BREAK-AND-WATCH-0.7.3.md`. Code citations are `file:line` in the tree that ships this file (0.7.3),
unless a row quotes coordinates at the prior revision `1e51dcf` to describe the
defect.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-27 | Med | `gui.py:1278-1292` and `gui.py:1325-1346`. The fix is one marker, not a lock: `state.broadcast_in_flight[wallet] = txid` is armed inside the same critical section that checks for it (`gui.py:1340`), and the lock is released before `broadcast_transaction` runs, so no network I/O is held across it (the CT-13 rule). Both halves read it — the early refusal before any explorer pre-check (`gui.py:1283`) and the in-lock refusal immediately before arming — and it is cleared on every exit: on an unknown outcome after `record_pending(…, True)`, on a definite refusal without recording anything (so the reviewed payment stays retryable), and on success. The state is also per-wallet now (`pending_by_wallet`, `broadcast_in_flight` keyed by wallet identity), so a wallet imported mid-flight inherits no pause and a swapped-in wallet cannot have its answer attributed to the wrong payment. The comment above the in-lock check now states only what the code guarantees: a request that passed the early check cannot submit while another is mid-air, because the first thing it does under the lock is leave its marker (CT-28). Break-and-watch: the early refusal replaced by `if False:` turned its pin red with `Expected 'verify_selected_outpoints' to not have been called. Called 1 times.`; the arm deleted turned the held-broadcast pin red with `409 != 400`; the in-lock marker read replaced by `if False:` turned the mid-request race pin red with `Expected 'broadcast_transaction' to not have been called. Called 1 times.`; the clear deleted turned the definite-refusal pin red on its armed-marker assertion. Every restore was byte-identical and every pin went green again. Rows `CM-38` and `CM-43`. | `tests/test_send_flow.py::SendFlowTests::test_a_second_payment_cannot_ride_a_broadcast_in_flight`, `tests/test_send_flow.py::SendFlowTests::test_a_broadcast_racing_an_in_flight_submit_is_refused_under_the_lock` and `tests/test_send_flow.py::SendFlowTests::test_a_definite_refusal_clears_the_in_flight_marker` |
| CT-28 | Info | `gui.py:1331-1343`. The comment above the in-lock pause claimed that the two checks together meant two requests which had both passed the early check could not both submit. They could: the early check read a record written only after the broadcast returned, so both requests passed it and both reached the broadcaster — that is CT-27 itself. The comment now states only what the code guarantees: a request that passed the early check cannot submit while another is mid-air, because the first thing that lock section does is leave the marker, and a later request finds the recorded outcome there. The guarantee and the comment are one fix, so the break-and-watch is CT-27’s. | `tests/test_send_flow.py::SendFlowTests::test_a_second_payment_cannot_ride_a_broadcast_in_flight` |
| CT-29 | Low | `gui.py:1056-1061`. The pending record was one `(txid, unknown)` pair per wallet, last-writer-wins: a second completed broadcast overwrote the first, and a scan cleared the whole record when the newer payment confirmed — lifting the pause while the older payment was still unspent, or leaving the wallet paused for the session when the older one never confirmed. The record is now `{txid: outcome_unknown}` per wallet in submission order; `record_pending` keeps every txid (`records[txid] = records.get(txid, False) or unknown`), `clear_pending` drops exactly one, and a scan reconciles txid by txid, clearing only what the explorer reports confirmed. `pending_broadcast_txid` and `pending_broadcast_unknown` became read-only views over the open wallet's record, so the waiting-on message and the prepare gate kept their behaviour unchanged. Break-and-watch: the reconciliation loop deleted turned the pin red with an HTTP 500 from the unarmed scan; the restore was byte-identical and the pin went green again. Row `CM-44`. | `tests/test_gui.py::LocalGuiTests::test_a_second_payment_cannot_clear_the_first_one_s_pause` |
| CT-33 | Low | `network_settings.py:150-158`. `verify_esplora`'s tuple named `HTTPError`, `URLError`, `HTTPException`, `TimeoutError`, `UnicodeError` and `ValueError`, but not `OSError`; a peer that resets the connection mid-reply raises `ConnectionResetError`, a plain `OSError`, so it escaped the documented `SettingsError` and its stage diagnostic and reached the generic handler as a fixed 500 — fail-closed, but with the message lost. `OSError` is now in the tuple, matching the two tuples in `wallet_service.py` that already carry it (`:138-145`, `:183-190`). The existing tests patch `urlopen` and cannot produce a reset, so the pin drives a real socket that sends the reply head and then closes with `SO_LINGER` set. Break-and-watch: `OSError` removed turned the pin red with `ConnectionResetError: [Errno 54] Connection reset by peer`; the restore was byte-identical and the pin went green again. Row `CM-40`. | `tests/test_network_settings.py::BrokenReplyTests::test_a_reset_connection_is_reported_as_unavailable` |
| CT-30 | Info | `CONTROLS.md`. The `CM-38` row cited only the early half of the pause (`gui.py:1218-1231` at the prior revision) and only its first test, so the in-lock half's marker and its independent pin were tracked by no row. `CM-38` now names the early half and says the pause is asserted before any explorer is asked; `CM-43` is the new row for the in-lock check-and-arm (`gui.py:1325-1346`) with its own pin, and `CM-44` names the per-txid reconcile. The inventory test binds every row to a `CONTROL: CM-##` marker inside its cited range and to a loadable test. Breaking either half of the pause — as the four transcripts above do — turns a pin red while the rows stay truthful; the row/pin binding itself is what `tests/test_controls_inventory.py` holds. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_names_a_test_that_loads` |
| CT-31 | Info | `.github/workflows/build-candidate.yml:150-174`. The source-archive secret scan — the control that stops a credential reaching a tag — had no `CONTROLS.md` row. `CM-45` now cites the step (which plants a canary built from fragments, runs `scripts/scan-secrets.py` against the *extracted* tarball, and only then uploads the artifact) and the test that binds the step to the archive. Break-and-watch: the step rewritten to scan the worktree instead of the archive turned the pin red with `AssertionError: 'tar xzf' not found in …`; the restore was byte-identical and the pin went green again. | `tests/test_secret_scan.py::ArchiveScanStepTests::test_the_scan_reads_the_archive_before_it_is_uploaded` |

## Observations recorded

The audit called these three housekeeping and graded none of them; none changes
behaviour, so none has a closing test. They are recorded here anyway, because a
note that closes by silence is how the next cycle finds it again.

| Note | What was recorded |
| --- | --- |
| **CT-32** | The previous plan's §4/§5 `gui.py` citations were stale at the revision the audit read (it cited `gui.py:1030-1043` for the final-review comparison, which is `gui.py:1190-1203` at `1e51dcf`), and §0 "In scope" cited the prior revision's commit where the revision rule says `1e51dcf`. The new plan is written from a fresh survey of the tree it names, cites the revision rule's commit throughout, and leaves pinned `file:line` ranges to `CONTROLS.md`, where the inventory's own test binds every range to a `CONTROL: CM-##` marker inside it. Discharged by writing the plan, not by scheduling work. |
| **CT-34** | `explorer_get`'s bounded read can return a truncated body rather than raise: the bound is a deadline and a byte ceiling, not the reply's own `Content-Length`. The audit demonstrated that the callers fail closed — a cut JSON or text reply becomes the named "invalid data" refusal through the `ValueError`/`UnicodeError` arm at `wallet_service.py:193-197`, and every caller applies its own shape check to what it receives. The contract is now documented at the function that owns it, in `explorer_get`'s docstring, so the next reader does not have to re-derive it. No behaviour change, so no test is added. |
| **CT-35** | The v0.7.2 release window had **six** candidate attempts, five of them failing inside the macOS DMG job — four on the Apple staple/validate step (`Error 68`, once behind a CloudKit `NSURLErrorDomain Code=-1005`) and one on `hdiutil: create failed - Resource busy` — with the publish jobs skipped every time, so nothing was published by any failed attempt; attempt six succeeded. The promote run succeeded on its first attempt. All five are named in `RELEASE-HISTORY.md` and `CURRENT-STATUS.md` as of this release, the way CT-26's conversion recorded the prior window's three events. |

## Accepted floating inputs

Unchanged from `releases/PATCH-0.7.0.md`, `releases/PATCH-0.7.1.md` and
`releases/PATCH-0.7.2.md`, and restated here because a reviewer should be able to
read this ledger on its own. Pinning the runner's packages to exact versions
remains **declined**: the `noble-updates` and `noble-security` archives move as
Canonical ships fixes, a pin would fail the build on a runner refresh without
making the AppImage reproducible, and the package is only one input among many. A
pin that breaks the build and buys nothing is not a control.

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

**What changed, and what did not.** Three app files change: `gui.py` (the
broadcast pause, its marker, and the per-txid record), `network_settings.py` (one
catch tuple) and `wallet_service.py` (one docstring; no code). No transaction
construction, signing, fee, network or consent rule changes. This revision must
never be described as engine-unchanged: `gui.py` changes behaviour.

**The one behaviour change, and where it is felt.** While a payment is on the wire
the wallet now refuses the next submit with "A payment from this wallet is still
being submitted. Wait for that result before sending another.", and it keeps the
pause until **every** recorded payment is confirmed rather than only the newest.
A definite refusal still leaves the reviewed payment ready to retry, because
nothing was sent and nothing is recorded. The user manual's "Wait for
confirmation" step says so.

**What the fix does not claim.** The marker bounds the window the audit
demonstrated — the gap between the check and the network call. It does not make the
explorer a source of truth about unconfirmed spends; that question (`/outspend`
mempool semantics) stays on the next-cycle list in the plan, and the pause still
depends on the explorer reporting the first spend once the broadcast has returned.

**Evidence kept in the repository, and evidence that is not.** The eight
break-and-watch transcripts are in `releases/BREAK-AND-WATCH-0.7.3.md`; the closing
tests are in the tree. The audit's own lane reports, the referee's private coaching
document and the signed plan are held outside the repository, by design, and are
named in the plan rather than reproduced.

**No earlier record was edited.** `releases/PATCH-0.7.0.md`, `PATCH-0.7.1.md`,
`PATCH-0.7.2.md`, their plans and the prior cycles' artifacts under
`audit-history/` are unchanged by this release.

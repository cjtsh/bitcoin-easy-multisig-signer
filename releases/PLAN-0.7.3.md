# Plan 0.7.3 — remediation of the v0.7.2 Color Team findings

**Inputs.** The cycle-9 Color Team audit of the published release `v0.7.2`
(tag `1e51dcfa45d6f61c83c14aeb1998725fbd705ba9`, committed
2026-10-26T16:36:29-04:00, ten release artifacts published `2026-10-26T21:48:23Z`),
graded **⛔ BLOCKED**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.2.md`
  — the public report, grade and ledger CT-27…CT-35;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.2.md`
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.2.md`
  — the scope lock (plan SHA-256 `36d30916b2447b2b26cf82353fe478ef543139e3b2856e6b573d496bd03913b4`
  at start and end);
- the auditor's private briefing, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The v0.7.1 conversion criterion was met **by
execution** — CT-22, CT-24 and CT-25 were each re-broken and their named tests
watched going red, CT-23 and CT-26 closed by dated owner acceptance, CT-01…CT-21
carried with no regression — and the block is **one new finding in the new code,
CT-27 (Medium)**: both halves of the broadcast pause created for CT-22 read a
field that was written only after the first broadcast returned, so while a submit
was on the wire the pause was still empty and a second, separately reviewed
payment could pass both halves and be broadcast. Threat row T-11 forbids exactly
that outcome, and the framework's ruling 4 makes a T-11 violation mechanically
blocking at any severity.

**Why this plan is short.** CT-27 is a gate that was placed where the record is
written rather than where the intent exists: the refusal is right, the state it
reads is one write too late. The fix is one marker, armed inside the lock that
already checks it, and cleared on every exit. CT-29 is the same state made
per-txid instead of last-writer-wins, CT-33 is one missing exception class in one
tuple, and the four remaining items are inventory and record-keeping. No capability
is added and no transaction construction, signing, fee or network rule changes.

---

## 1. What is actually wrong (in plain terms)

1. **The pause that reads a record written too late (CT-27).** After a payment is
   broadcast the app records its txid and refuses the next payment at the submit
   (`gui.py:1219-1230`) and again under the pre-submit lock (`gui.py:1265-1272` at
   `1e51dcf`). But the field both checks read was assigned only after
   `broadcast_transaction` returned (`gui.py:1291-1297`, `:1299-1307`), and that
   call is bounded by `BROADCAST_TIMEOUT_SECONDS = 20.0`
   (`wallet_service.py:40`). For up to twenty seconds per payment the pause was
   empty and both halves passed. Two examiners demonstrated it end to end through
   the real `/api/*` routes: two payments, each individually reviewed, device-signed
   and consented, both left the device. Nothing was signed that the operator had not
   seen — this is a sequencing defect, not a substitution — but it is the outcome
   T-11 prohibits, so it blocks.
2. **A record that remembers only the last payment (CT-29).** The pause kept one
   txid per wallet, so a second completed broadcast overwrote the first
   (`gui.py:1299-1307` at `1e51dcf`). With CT-27 fixed the ordering that reaches it
   narrows, but the record is still last-writer-wins: if the newer payment
   confirmed first, the scan cleared the pause while the older payment was still
   unspent, and if the older one stayed unconfirmed the wallet could stay paused for
   the rest of the session.
3. **One exception class missing from one tuple (CT-33).** `verify_esplora`'s catch
   tuple (`network_settings.py:154` at `1e51dcf`) names `HTTPError`, `URLError`,
   `HTTPException`, `TimeoutError`, `UnicodeError` and `ValueError`, but not
   `OSError`. A peer that resets the connection mid-reply raises
   `ConnectionResetError`, which is a plain `OSError`, so it escaped the documented
   `SettingsError` and its stage diagnostic and became a raw 500. The explorer and
   broadcaster tuples already carry `OSError` (`wallet_service.py:131`, `:178`), so
   this is one path out of step with the other two.
4. **A comment that claimed a guarantee the code did not have (CT-28).** The
   pre-submit comment said two requests that both passed the early check "cannot
   both submit". Two concurrent submits of the same prepared payment both reached
   the broadcaster; consensus deduplicated them. The claim was false for the reason
   CT-27 describes.
5. **Inventory gaps (CT-30, CT-31).** The `CM-38` row cited only the early half of
   the pause and only its first test, so the in-lock half's marker and its
   independent pin were tracked by no row; and the source-archive secret scan — the
   control that stops a credential reaching a tag — had no row at all.

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the `AGENTS.md`
rule: break the control on a disposable copy, watch the named test go red, restore.
Full transcripts are in `releases/BREAK-AND-WATCH-0.7.3.md`.

### Tier 1 — the finding that sets the floor

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-27, CT-28 | Medium | `gui.py:1219-1230` and `gui.py:1265-1272` (at `1e51dcf`) read `state.pending_broadcast_txid`, which was assigned only after `broadcast_transaction` returned (`gui.py:1291-1297`, `:1299-1307`) — a window bounded by `BROADCAST_TIMEOUT_SECONDS = 20.0` (`wallet_service.py:40`). While the first broadcast was in flight a second, differently reviewed payment passed both halves and was broadcast. The pre-submit comment's claim that two requests "cannot both submit" was therefore false (CT-28). | One marker, `state.broadcast_in_flight[wallet] = txid`, armed inside the same critical section that checks for it and released before the network call, so no lock is held across I/O (the CT-13 rule). Both halves read it: the early check before any explorer pre-check, the in-lock check immediately before arming. Every exit clears it — the unknown-outcome path after recording the pause, the definite-refusal path without recording anything — so a refused payment stays retryable. The comment is rewritten to what the code now guarantees. | `tests/test_send_flow.py::SendFlowTests::test_a_second_payment_cannot_ride_a_broadcast_in_flight` (a held broadcaster; the second payment must be refused with one broadcaster call), `…::test_a_broadcast_racing_an_in_flight_submit_is_refused_under_the_lock` (the marker armed from a `finalize_multisig` side effect mid-request, so only the in-lock read can refuse it) and `…::test_a_definite_refusal_clears_the_in_flight_marker` (a `WalletError` refusal leaves nothing armed and the payment retryable); rows `CM-38` and `CM-43`. Break-and-watch: early refusal → `if False:` gives `Expected 'verify_selected_outpoints' to not have been called. Called 1 times.`; the arm deleted gives `409 != 400`; the in-lock read → `if False:` gives `Expected 'broadcast_transaction' to not have been called. Called 1 times.`; the clear deleted gives the armed-marker assertion failure. Every restore re-ran green. |
| W2 | CT-29 | Low | `gui.py:1299-1307` (at `1e51dcf`). The pause was one `(txid, unknown)` pair per wallet, so a second completed broadcast overwrote the first, and a scan cleared the whole record when the newer payment confirmed — lifting the pause while the older payment was still unspent, or leaving it stuck when the older one never confirmed. | The record is now a dict per wallet, `{txid: outcome_unknown}`, in submission order; `record_pending` keeps every txid, `clear_pending` drops exactly one, and a scan reconciles txid by txid, clearing only what the explorer reports confirmed. `pending_broadcast_txid` and `pending_broadcast_unknown` become read-only views over the open wallet's record, so the waiting-on messages and the prepare gate keep working unchanged. | `tests/test_gui.py::LocalGuiTests::test_a_second_payment_cannot_clear_the_first_one_s_pause` records two txids, confirms only the newer, and asserts the pause survives naming the older one — then clears on a later scan; row `CM-44`. Break-and-watch: the reconciliation loop deleted → the pin goes red with an HTTP 500 from the unarmed scan; restore → green. |
| W3 | CT-33 | Low | `network_settings.py:154` (at `1e51dcf`). The tuple omitted `OSError`, so a connection reset mid-reply (`ConnectionResetError`) escaped the documented `SettingsError` and reached the generic handler as a fixed 500 — fail-closed, but without the message or the stage diagnostic. | `OSError` added to `verify_esplora`'s tuple, matching the two tuples in `wallet_service.py` that already carry it. | `tests/test_network_settings.py::BrokenReplyTests::test_a_reset_connection_is_reported_as_unavailable` drives a real socket that sends the reply head and then resets with `SO_LINGER`; the existing tests patch `urlopen` and cannot raise `ConnectionResetError`; row `CM-40`. Break-and-watch: `OSError` removed → `ConnectionResetError: [Errno 54] Connection reset by peer` escapes the test; restore → green. |

### Tier 2 — the inventory gaps

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W4 | CT-30, CT-31 | Info | `CONTROLS.md:62` (at `1e51dcf`) cited only `gui.py:1218-1231` and one test, so the in-lock half's marker and its independent pin were tracked by no row; the source-archive secret scan had no row at all. | `CM-38` keeps the early half and says the pause is asserted before any explorer is asked; `CM-43` is the new row for the check-and-arm under the pre-submit lock with its own pin; `CM-45` is the new row for the archive scan, citing the workflow step and the test that binds the step to the tarball; `CM-44` is the new row for the per-txid reconcile. `CONTROLS.md` is at 45 rows. | `tests/test_controls_inventory.py` binds every row to a `CONTROL: CM-##` marker inside its cited range and to a loadable test; rows `CM-43`, `CM-44`, `CM-45`. Break-and-watch: the scan step made to read the worktree instead of the archive → `AssertionError: 'tar xzf' not found in …`; restore → green. |

### Work in this cycle that is not a finding

- **Release mechanics.** `version.py` moves to 0.7.3 and every user-facing version
  reference moves in the same commit — the download page's URLs, labels, JSON-LD
  and patch-record link, the manuals, the README, the status documents, this plan
  and the ledger. `releases/RELEASE-NOTES-0.7.3.md` and the cycle's
  `RELEASE-HISTORY.md` row are part of the same commit. The promote run has to
  pass `notarize=true`, because the workflow refuses to publish an unsigned build
  (`.github/workflows/build-candidate.yml:58`).
- **The five failed candidate attempts of the last window.** Recorded here as
  CT-35 asked, in `RELEASE-HISTORY.md` and `CURRENT-STATUS.md`: run `40397174519`
  failed five times, four on the Apple staple/validate step and once on
  `hdiutil`, every one inside the macOS DMG job with the publish jobs skipped, so
  nothing was published; attempt six succeeded. This was a platform flake, not a
  defect in the release bytes, but a window that fails five times and says nothing
  is the CT-26 pattern repeating.

## 6. The four record-keeping notes

The audit graded none of these with an asset path, and none changes behaviour, so
none is a work order and none has a closing test — which means this plan names them
here rather than letting them close by silence.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| CT-32 | Next plan: the §4/§5 `gui.py` citations are stale (the plan cites `gui.py:1030-1043` for the final-review comparison, which is `gui.py:1190-1203` at this revision), and §0 "In scope" cites the prior revision's commit where the revision rule says `1e51dcf`. | The v0.7.3 plan is written from a fresh survey of the tree it names; §4 and §5 cite the revision rule's commit throughout, and every `file:line` is checked against the tree at that commit. The pinned ranges live in `CONTROLS.md`, where the inventory test binds them. |
| CT-34 | `explorer_get`'s bounded read can return a truncated body as success; the callers' format checks catch it (fail-closed demonstrated). | Documented at the function, where the next reader will be: the docstring now says the bound is a deadline and a byte ceiling rather than the reply's `Content-Length`, that a cut JSON or text reply becomes the named "invalid data" refusal through the `ValueError`/`UnicodeError` arm, and that every caller applies its own shape check to what it receives. No behaviour changes, so no test is added. |
| CT-35 | The release window's five failed candidate attempts were not recorded. | `RELEASE-HISTORY.md`'s 0.7.2 row and `CURRENT-STATUS.md` name all five, the job they failed in and the fact that nothing was published by them. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the prior plan and the ledger, unchanged and with their triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Real-Esplora `/outspend` mempool semantics — does a public Esplora report an unconfirmed spend of an output? | Next cycle (still open; the new in-flight marker no longer depends on the answer) |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey; pywebview/WebView2 JS-bridge runtime test | When an emulator or Windows/GUI host is available |
| Per-package PyPI identity cross-check of every locked dependency; second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next cycle / next practice-network change |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering; concurrent-API interleaving fuzz; Jade PIN-relay trust | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |

## 10. Decisions the owner is asked to make

1. **Release number.** A patch bump to **0.7.3**, on the owner's instruction: the
   cycle-9 report blocks the grade on CT-27, and the remediation ships as the next
   patch.
2. **CT-27 — a marker, not a lock.** The fix arms an in-flight marker under the
   existing pre-submit lock and releases it before the network call, rather than
   holding the lock across I/O. The framework's ruling and the CT-13 precedent both
   point the same way.
3. **CT-29 — fix it in this cycle.** It is now reachable only through timing that
   CT-27 closes, but the record is wrong on its own terms: last-writer-wins is a
   defect whether or not the window that reaches it is open, and the fix is small.
4. **CT-33 — widen the tuple.** `OSError` joins the other two transport tuples, so
   the three paths describe the same class of failure.
5. **CT-32 and CT-34 — record, do not schedule.** Neither changes behaviour; CT-32
   is discharged by writing the next plan from a fresh survey, CT-34 by documenting
   the contract at the function that owns it.
6. **Who executes.** The plan is written to be executed item by item, each with its
   own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every work order above
is recorded row by row in `releases/PATCH-0.7.3.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`1e51dcf`, where the audit found them; the closing code and tests live in the tree
that ships this file.

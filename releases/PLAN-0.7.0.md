# Plan 0.7.0 — remediation of the v0.6.9 Color Team findings

**Inputs.** The cycle-6 Color Team audit of the published release `v0.6.9`
(tag `e90e5b93ece284f990ca2b75be1e798baa3efc9c`, committed
2026-10-11T11:12:08-04:00, artifacts published `2026-10-11T15:33:09Z`), graded
**⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.9.md`
  — the public report, grade and ledger CT-13…CT-18;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.9.md`
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.9.md`
  — the scope lock (plan SHA-256 `133ce23afe0bca80d884bcff7b9cfa428d2f8bbb965a7d2ff84182aa0be8a8c3`
  at start and end);
- the auditor's private coaching document, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The conversion gate was met in full — the
referee re-broke every one of the twelve prior findings and watched its new test
go red, so all twelve are verified fixed **by execution** — the delta introduced
no Critical or High, and the grade is held below CLEARED by one new Low in the
same pin-accuracy family that held the two cycles before it.

**Why this plan is short.** Cycle 5 rebuilt nothing: it answered four Lows and
eight Informationals, and the panel confirmed each answer by re-running the
break the finding described. What remains is one defective pair of test names,
one deliberate availability trade that needs either a shape change or a dated
owner decision, and four recorded housekeeping items. Every one of them is a
corrections-only change; none adds capability, and none touches what is signed
or broadcast.

---

## 1. What is actually wrong (in plain terms)

1. **The grade-setter: two tests named for something they do not test (CT-14).**
   The build-time prevout match at `wallet_service.py:867-870` checks three
   limbs — the previous transaction's txid, the value it pays, and the script it
   pays. Two tests were named for the value limb and the script limb, but both
   mutate the *serialized* previous transaction, and any mutation changes its
   txid, so both were actually exercising the txid limb. The referee deleted the
   value limb and the script limb one at a time and the whole money-path suite
   stayed green. The protection itself holds — the txid limb is pinned, and the
   fee backstop independently refuses a value mismatch — but the shipped test
   evidence does not exist *for the named limbs*, which is what the rubric's
   CONDITIONAL clause names.
2. **The availability trade the ceiling introduced (CT-13).** `gui.py`'s
   connection ceiling from cycle 5 closed the thirty-third socket. A hostile
   *local* process could therefore open thirty-two sockets, say nothing, and
   freeze the operator's own window until it stopped; a slow drip could hold a
   slot indefinitely. No declared asset is reachable and recovery is immediate,
   but the operator's window is the one thing the ceiling must not take away.
   The auditor offered either a dated owner decision or a change to the shape.
3. **The six housekeeping notes (CT-15…CT-18).** Five protections the previous
   release added were claimed and pinned but not tracked in the inventory the
   build parses (CT-15), and the inventory's claim-phrase net missed all five
   because their comments used ordinary words. The retired-publisher guard read
   only the first page of the workflow registrations (CT-16, latent at six
   registrations). The Windows startup *dialog* still interpolated the unbounded
   exception while the log beside it was bounded (CT-17). And one sentence in
   the 0.6.9 ledger understated the `windows-inputs.yml` delta by naming only
   comments and the runner pin, omitting the separate `lock` job's hardening
   (CT-18).

---

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the AGENTS.md
rule: break the control on a disposable copy, watch the named test go red,
restore it.

### Tier 1 — the grade-setter

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-14 | Low | `wallet_service.py:867-870` checks txid, value and script. `tests/test_money_path_pins.py`'s two cases named for the value and script limbs both rewrote the serialized transaction, which changes the txid, so neither could fail if its own limb were deleted. | Give each limb a discriminating case against a transaction left byte-for-byte intact: a **lying UTXO list** whose value disagrees with the honest transaction served for that txid (only the value limb can refuse it), and an outpoint listed under a wallet address while the honest transaction for that txid pays a script the wallet does not own (only the script limb can refuse it). Both lies are internally consistent, so the consistency gate is not what catches them. Rename the two rewritten-bytes cases to the limb they actually exercise instead of deleting the coverage. | `tests/test_money_path_pins.py::BuildTimePrevoutPins::test_a_lying_utxo_list_value_is_refused_by_the_value_limb` and `…::test_a_lying_utxo_list_script_is_refused_by_the_script_limb`. Break-and-watch: delete the value limb → the value case goes red with the fee-backstop message; the script case stays green. Delete the script limb → the script case goes red and the value case stays green. Recorded in `PATCH-0.7.0.md`. |

### Tier 2 — the availability trade

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W2 | CT-13 | Low | `gui.py:98-137`. The cycle-5 ceiling closed every socket beyond `MAX_CONNECTIONS`, so a local process holding all the slots locked the operator's own window out for as long as it held them — a silent socket for the connection timeout, a slow drip indefinitely. | Change the shape rather than accept the trade: fair admission. A newcomer is refused only when every admitted connection is *busy*; otherwise the oldest idle connection is retired for it. A connection is idle from accept until a complete request head has arrived (so silence and a half-sent head are both idle) and idle again between keep-alive requests. Only a connection actually being served is protected, and reaching that state requires a complete request — which for every route that does anything requires the page's token. A retired connection is remembered so its handler answers nothing instead of writing to a shut-down socket. | `tests/test_gui_integration.py::ConnectionCeilingTests::test_the_window_is_admitted_while_idle_sockets_hold_the_ceiling`, `…::test_a_slow_drip_does_not_hold_the_window_out_either` and `…::test_the_ceiling_still_refuses_when_every_slot_is_busy`. Break-and-watch: restore the plain refuse-when-full ceiling → both admission cases go red with a reset connection while the busy-ceiling case stays green. |

### Tier 3 — the housekeeping the audit recorded

| # | ID | Sev | Location | Fix | Acceptance |
| --- | --- | --- | --- | --- | --- |
| W3 | CT-15 | Info | `CONTROLS.md` | Add a row per protection the previous release added and pinned but left untracked — the connection ceiling (CM-27), the constant-time token comparison (CM-28), the market-read token gate (CM-29), the token-history eviction (CM-30), the bounded startup record (CM-31) — plus the per-connection time budget (CM-32), which the widened phrase net then surfaced. Each row carries its own `CONTROL: CM-##` marker inside the range it cites and a closing test the build loads. Widen `PHRASES` with the claim shapes the net missed, each verified against every shipped comment block. | `tests/test_controls_inventory.py::ControlInventoryTests::test_every_row_cites_its_own_marker` reads all 32 rows; every new row's own closing test is named in the ledger. |
| W4 | CT-16 | Info | `.github/workflows/build-candidate.yml` (`Refuse while a retired publisher is runnable`) | The step reads one page of the workflow registrations. Refuse when `total_count` is not an integer or exceeds the page limit, and refuse when the returned list does not match `total_count`, so a re-enabled publisher on a page nobody read is a refusal rather than a pass. Pagination flags are deliberately not used: the count is what fails closed, so the guard does not depend on a runner's `gh` version. | `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_more_registrations_than_the_page_holds_refuses` and `…::test_a_page_shorter_than_the_reported_count_refuses`. Break-and-watch: delete the page-limit branch → the first case goes red. |
| W5 | CT-17 | Info | `desktop.py:388-394` | The Windows startup dialog interpolates the same bounded type-and-message record the log holds, not the raw exception. A message box cannot be scrolled, so an enormous platform error used to become a dialog that ran off the screen; the full text is in the file the dialog names. | `tests/test_desktop.py::StartupFailureTests::test_the_windows_dialog_shows_the_bounded_record_too`, plus the existing dialog case asserting the title, the sentence and the report path. Break-and-watch: interpolate the raw exception again → the bounded case goes red. |
| W6 | CT-18 | Info | `releases/PATCH-0.6.9.md`, the CT-12 row | Scope the "unchanged" sentence to the `libusb` job it describes and enumerate the delta it omitted: comments, the `windows-latest` → `windows-2022` runner pin on both jobs, and the `lock` job's hardening (`3.12` → `3.12.10`, `pip-tools` installed under `--require-hashes -r requirements-piptools.lock`). Mark the correction inline, dated to this cycle, so the amendment is visible rather than silent. | Recorded evidence, not a test: the diff between `a1564c0` (the producing run's commit) and this tree, and the ledger row in `PATCH-0.7.0.md`. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the ledger and the auditor's coaching document, with triggers:

| Item | Trigger |
| --- | --- |
| `_clean_token`'s pass-through shape is unpinned but unreachable past the pinned device-class vocabulary check | Next cycle's Blue lane (referee's referral, no finding id) |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Per-package PyPI identity cross-check of every locked dependency | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey | When an emulator host is available |
| pywebview/WebView2 JS-bridge runtime test (needs a Windows/GUI host) | Next Windows-capable review |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next practice-network change |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering | Next cycle |
| Concurrent-API interleaving fuzz beyond T1-8/T2-5; Jade PIN-relay trust | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |
| Archive of the audit reproducer scripts (currently under `/tmp`, documented in writing only) | Housekeeping; not security-relevant |

## 10. Decisions the owner is asked to make

1. **Release number.** This plan assumes a minor bump to **0.7.0**, on the
   owner's instruction. It is corrections only — no new capability — and the
   ledger records it as such; say so if a patch number is wanted instead.
2. **CT-13, change the shape or accept the trade.** This plan changes the
   shape: the operator's window is never refused while an idle connection holds
   a slot. The residual is stated plainly in the ledger — a local process that
   actively serves requests can still consume capacity, which is inherent to a
   loopback service — and no dated owner acceptance is needed for the lockout
   this finding described, because that lockout no longer exists.
3. **CT-15's meta-pattern.** The phrase net is widened to the claim shapes this
   delta used, but a net made of words can always be avoided by new words. The
   durable rule, recorded in the ledger and in `tests/test_controls_inventory.py`,
   is that a delta which adds a protection adds its row in the same commit.
4. **Who executes.** The plan is written to be executed item by item, each with
   its own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every item above is
recorded row by row in `releases/PATCH-0.7.0.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`e90e5b9`, where the audit found them; the closing code and tests live in the
tree that ships this file.

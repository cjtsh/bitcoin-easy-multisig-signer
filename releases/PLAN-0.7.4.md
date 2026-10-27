# Plan 0.7.4 — remediation of the v0.7.3 Color Team findings

**Inputs.** The cycle-10 Color Team audit of the published release `v0.7.3`
(tag `a227da4073f705cbb4ca47f939e80fc0921c77d7`, committed
2026-10-26T21:28:27-04:00, ten release artifacts published `2026-10-27T02:47:51Z`),
graded **⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.3.md`
  (SHA-256 `3682471ba8fc37ebfb1f43a8cf0f20487a5ec1bb36c3fbdbebded1e7f174da3d`)
  — the public report, grade and ledger CT-36…CT-44;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.3.md`
  (SHA-256 `6f5c902e6e230b9bda99650c9ebab200ccb9ebb89b361902eb1e3432e77ea826`)
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.3.md`
  (SHA-256 `ae3065efc1c68cda846b04863caecc877f00bef15cbc4219541bce85f96db26c`)
  — the scope lock (plan SHA-256 `83534f9ee9909fcdbb6f09505d1dc26b883aae2b1dd6a6a76b1b557a84dfa64c`
  at start and end, so the scope never moved);
- the auditor's private briefing, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The v0.7.2 block was discharged **by execution** —
the referee personally re-broke CT-27's marker arm and its clear, CT-29's reconcile
and CT-33's tuple, and watched each named test go red — and the grade holds on two
new findings: **CT-36 (Medium)**, a 4xx answered after the complete signed bytes
were written was classified as a definite refusal, so the in-flight marker came
down and a second, differently reviewed payment could leave with no pause armed;
and **CT-41 (Low)**, which independently sustains the grade under ruling 5 because
the early in-flight half of the gate is held by no test that can fail.

**Why this plan is short.** CT-36 and CT-37 are one classification decision in one
function (`broadcast_transaction`) plus the handler that consumes it: the app can
prove nothing was sent only for the checks that run *before* the POST is written,
so those raise a new `BroadcastNotSent` and everything else is an unknown outcome.
CT-41 is one test. CT-43 is a record. The two Infos this plan does schedule
(CT-39, CT-40) are one widened citation range and two new inventory rows. No
capability is added and no transaction construction, signing, fee or network rule
changes.

---

## 0. The ledger, round trip

The prior ledger is accounted for in full, and this cycle's plan names every ID
`CT-01`…`CT-44` — the defect CT-38 records is that the previous plan's own table
skipped CT-26…CT-34 while still claiming to account for everything, and the plan it
pointed at was hash-locked, so the correct place to fix it is here.

| ID | Status at `a227da4` | Where this cycle records it |
| --- | --- | --- |
| CT-01…CT-21 | carried, verified fixed; no regression | §5 W1–W5 carried; no new work |
| CT-22…CT-26 | converted in v0.7.2; carried, no regression | §5 W1–W5 carried; no new work |
| CT-27 | converted by execution (the block is discharged) | §6 — carried, the marker architecture is unchanged |
| CT-28 | converted by execution | §6 — carried |
| CT-29 | converted by execution | §6 — carried |
| CT-30, CT-31 | converted by execution | §6 — carried; this cycle adds rows CM-47…CM-50 |
| CT-32, CT-34, CT-35 | closed by written, dated owner acceptance | §6 — carried |
| CT-33 | converted by execution | §6 — carried |
| **CT-36** | **open — Medium, the floor-setter** | §5 W1 |
| **CT-37** | **open — Low** | §5 W3 |
| **CT-38** | **open — Info (note, not scheduled)** | §6 |
| **CT-39** | **open — Info** | §5 W5 |
| **CT-40** | **open — Info** | §5 W5 |
| **CT-41** | **open — Low, independently sustaining CONDITIONAL** | §5 W2 |
| **CT-42** | **open — Info (note, not scheduled)** | §6 |
| **CT-43** | **open — Low** | §5 W4 |
| **CT-44** | **open — Info (note, not scheduled)** | §6 |

## 1. What is actually wrong (in plain terms)

1. **A "no" that arrives after the money left (CT-36).** `broadcast_transaction`
   treated every 4xx as a refusal (`wallet_service.py:122-125` at `a227da4`) and
   `gui.py`'s generic handler cleared the in-flight marker and recorded nothing
   (`gui.py:1377-1383` at `a227da4`), under a comment that said a definite refusal
   sent nothing. But a server answers 400 *after* it has the complete signed
   transaction — an honest Esplora answers exactly that way when it already holds
   the payment ("already in mempool"). One examiner drove it end to end: two
   payments, each reviewed and consented, both left the device, and the pause that
   v0.7.3 added was never armed for the second. Both payments were theirs to send,
   so this is not theft; it is the gate promising more than it can prove, which is
   what the CLEARED clause binds on.
2. **Anything else that escapes is treated as a refusal too (CT-37).** The same
   handler caught `BaseException`, so a `RuntimeError` from the submit path — which
   proves nothing about whether bytes were written — was also classified as
   not-sent. The instrument had to default the other way.
3. **The early in-flight half is held by no test (CT-41).** The early gate refuses
   a second payment while the first is on the wire, before any explorer is asked
   about the wallet's outputs. Deleting that half left every named pin green: the
   request then reached the check inside the pre-submit lock and was refused
   there, so no test could tell the two halves apart. The behaviour is right; the
   alarm was missing.
4. **This release window's history is under-recorded (CT-43).** The 0.7.3 row and
   `CURRENT-STATUS.md` recorded two runs and two attempts; the live history is five
   dispatched runs and nine attempts — a cancelled run, a candidate dispatched
   without notarization that the promote's manifest check correctly refused, and
   one candidate whose first two attempts failed inside the macOS job. Nothing was
   published from any failure, but a window that says less than it did is the
   CT-35 pattern repeating.
5. **Two inventory gaps (CT-39, CT-40).** `CM-43`'s cited range stopped five lines
   short of the arm it claims, and the final-versus-review comparison and the
   review-id binding — both real protections, both broken and watched red by the
   panel — carried no rows at all.

## 4. What the tree that ships this plan verifies

These are the facts the audit is asked to re-check at the delta, taken from the
tree that carries this file, not from the audit's description of it.

- **The suite.** `PYTHONPATH=tests python -m unittest discover -s tests -q` →
  `Ran 738 tests`, `OK`, in the checkout and again in the extracted source
  archive. `SendFlowTests` is 38 tests and `BroadcastOutcomeTests` carries the two
  classification pins.
- **The JavaScript suites.** All eleven `node tests/ui_*.cjs` exit 0.
- **The inventory.** `CONTROLS.md` is 50 rows; every row is bound by
  `tests/test_controls_inventory.py` to a `CONTROL: CM-##` marker inside the range
  it cites and to a test the build loads.
- **The ledger.** `tests/test_ledger_completeness.py` holds this plan to
  `releases/PATCH-0.7.4.md`: one row per scheduled id, six rows, each with a
  severity and a closing test that loads, and no deferral.
- **The corpus.** §0 accounts for CT-01…CT-44 with no gap: every id the v0.7.3
  report graded is either carried, converted by execution, accepted in writing,
  closed in this cycle, or recorded as a note.
- **Break-and-watch.** 15 cases, each broken on a disposable copy, watched red, the
  copy restored byte-for-byte and the same check re-run green
  (`releases/BREAK-AND-WATCH-0.7.4.md`).
- **The published set.** `v0.7.3` is the newest published tag at the time of
  writing (`a227da4`, ten assets); `v0.7.2`, `v0.7.1` and their predecessors are
  present and untouched. This plan is signed against `v0.7.3`, the revision the
  audit read.
- **The `0.7.4` tag does not exist yet.** It is cut by the promote run after this
  file's publication placeholders are filled, so this plan's §4 is a statement
  about the source tree, not about bytes on the Releases page.

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the `AGENTS.md`
rule: break the control on a disposable copy, watch the named test go red, restore.
Full transcripts are in `releases/BREAK-AND-WATCH-0.7.4.md`.

### Tier 1 — the finding that sets the floor

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-36 | Medium | `wallet_service.py:122-125` at `a227da4` classified every HTTP 4xx as `WalletError`, and `gui.py:1377-1383` cleared the in-flight marker and recorded nothing for it, so a second, differently reviewed payment of the same wallet could broadcast with no pause armed — demonstrated end to end. | A new `BroadcastNotSent(WalletError)` is raised only by the checks that run before the POST is written (unsupported network, missing mainnet opt-in, unusable size, invalid hex, a settings refusal), and those keep the reviewed payment retryable. Every answer received after the request exists — 4xx included — raises `BroadcastOutcomeUnknown` with the server's own words attached as evidence, and the message no longer says "refused" anywhere. `gui.py`'s handler maps a raw escape into the same unknown outcome, records the payment against the wallet and clears the marker, so nothing is left retryable on the strength of a status code. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_a_client_rejection_is_unknown_not_a_definite_refusal` (HTTP 400 → `BroadcastOutcomeUnknown`, message names HTTP 400 and the explorer and does not say "refused") and `tests/test_send_flow.py::SendFlowTests::test_an_unclassified_submit_failure_pauses_the_wallet` (a `RuntimeError` from the submit → 409, `outcome_unknown`, marker cleared, txid recorded, prepared payment dropped); rows `CM-46`, `CM-49`, `CM-50`. Break-and-watch: the 4xx re-classified as `WalletError` → `wallet_service.WalletError: The network refused this transaction HTTP 400 after receiving this payment…`; the raw-escape branch removed → `AssertionError: 500 != 409`; the pre-POST raise turned into a plain `WalletError` → the not-sent pin goes red. Every restore re-ran green. |
| W2 | CT-41 | Low | `gui.py:1292-1295` at `a227da4`. The early gate's in-flight half refuses before the explorer pre-check, but no test could fail if it were deleted: the in-lock half refuses the same request a moment later. | One test that arms the marker before the POST and asserts the explorer-facing pre-check was never called, mirroring the pending path's `assert_not_called` pin. No production change. | `tests/test_send_flow.py::SendFlowTests::test_a_broadcast_racing_an_in_flight_submit_asks_no_explorer`; row `CM-38`. Break-and-watch: that half → `if False:` gives `AssertionError: Expected 'verify_selected_outpoints' to not have been called. Called 1 times.`; restore → green. |

### Tier 2 — the other scheduled findings

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W3 | CT-37 | Low | `gui.py:1377-1383` at `a227da4`. The handler caught `BaseException` and treated every escape as a definite refusal, so a `RuntimeError` from the submit path left the marker down and the payment retryable with no evidence that nothing was sent. | The handler asks the type, not the circumstances: `BroadcastNotSent` is the only answer that clears without recording, and anything else is converted to `BroadcastOutcomeUnknown`, recorded, and reported as outcome-unknown. | `tests/test_send_flow.py::SendFlowTests::test_an_unclassified_submit_failure_pauses_the_wallet`; row `CM-46`. Break-and-watch: the conversion → `if False:` gives `AssertionError: 500 != 409`; restore → green. |
| W4 | CT-43 | Low | `RELEASE-HISTORY.md` 0.7.3 row and `CURRENT-STATUS.md` at `8e207a6` recorded two runs and two attempts; the live window is five runs and nine attempts, including a cancelled run and a notarize-free candidate the promote's manifest check refused. | Both records now name every run: the cancelled dispatch, the candidate built without notarization (whose macOS job correctly skipped signing and notary, so the promote's manifest check refused it), the candidate whose first attempt failed on Apple's staple/validate service and second on `hdiutil`, and the promote that published first time. | `tests/test_hardening_pins.py::ReleaseWindowDisclosureTests::test_the_0_7_3_row_names_every_run_of_its_window` reads the history row and requires all five run ids and both counts in it, with a negative half that shows the old two-run sentence fails the same check. |
| W5 | CT-39, CT-40 | Info | `CONTROLS.md:67` at `a227da4` cited `gui.py:1329-1349` for `CM-43`, five lines short of `state.broadcast_in_flight[wallet] = txid` at `gui.py:1354`; and the final-vs-review comparison (`gui.py:1249-1263`) and the review-id binding (`gui.py:1145-1160`) carried no rows. | `CM-43` cites `gui.py:1333-1354`, which contains the arm; `CM-47` is the new row for the final-vs-review comparison and `CM-48` for the review-id binding, each with its own marker and its own pin. `CONTROLS.md` is at 50 rows. | `tests/test_controls_inventory.py` binds every row to a marker inside its own range and to a loadable test; rows `CM-43`, `CM-47`, `CM-48`. Break-and-watch: the final-vs-review comparison removed → `AssertionError: Expected 'broadcast_transaction' to not have been called. Called 1 times.`; the review-id binding removed → `AssertionError: 'Review the current transaction' not found in 'Input 1 has 0 of 2 required signatures.'`; the arm excluded from `CM-43`'s range → the inventory test goes red. Every restore re-ran green. |

### Work in this cycle that is not a finding

- **Release mechanics.** `version.py` moves to 0.7.4 and every user-facing version
  reference moves in the same commit — the download page's URLs, labels, JSON-LD
  and patch-record link, the manuals, the README, the status documents, this plan
  and the ledger. `releases/RELEASE-NOTES-0.7.4.md` and the cycle's
  `RELEASE-HISTORY.md` row are part of the same commit. The promote run has to
  pass `notarize=true`, because the workflow refuses to publish an unsigned build
  (`.github/workflows/build-candidate.yml:58`), and the candidate's manifest must
  be checked for `notarize=true` before any promote is dispatched — the v0.7.3
  window's second refactor of that lesson.
- **The audit's own inventory work.** Four rows are new (`CM-46`…`CM-49`) and one
  widened (`CM-43`); `CM-50` is the not-sent boundary behind them. The inventory
  test is the only thing standing between "a control exists" and "a control is
  cited", and it now reads 50 rows.

## 6. The record-keeping notes

The audit graded none of these with an asset path, and none changes behaviour, so
none is a work order and none has a closing test — which means this plan names them
here rather than letting them close by silence.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| CT-38 | The signed `v0.7.3` plan's §5 T-10 cites a test name that does not exist at this revision. | The pinned plan cannot be edited — it is hash-locked, and rewriting a locked plan after the audit would void it. The citation is recorded here, and the substance it was reaching for is covered by `tests/test_send_flow.py::SendFlowTests::test_a_definite_refusal_clears_the_in_flight_marker` and `tests/test_gui.py::LocalGuiTests::test_a_second_payment_cannot_clear_the_first_one_s_pause`. Every `file:line` in this plan was taken from the tree at `a227da4` and re-checked against the tree that ships it. |
| CT-42 | A pause recorded against a lying txid can never be reconciled by an honest explorer, so the wallet stays paused until the session ends. | Recorded as an accepted residual in the fail-closed direction: the alternative — trusting a txid the server invented — is what the pause exists to prevent. The remedy when it happens is the one the message already gives: check an explorer, then restart. Not scheduled; the status-endpoint remedy is on the next-cycle list. |
| CT-44 | The legacy-tag residual is restated: 46 dispatchable tags enumerated, sweep green. | Restated in `releases/PATCH-0.7.4.md` and carried on the next-cycle list. Nothing new is claimed about the legacy tags. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the prior plan and the ledger, unchanged and with their triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Real-Esplora `/outspend` mempool semantics — does a public Esplora report an unconfirmed spend of an output? | Next cycle (still open; CT-36 sharpens it: does an honest Esplora answer 400 after acceptance, as the model assumes?) |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey; pywebview/WebView2 JS-bridge runtime test | When an emulator or Windows/GUI host is available |
| Per-package PyPI identity cross-check of every locked dependency; second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next cycle / next practice-network change |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering; concurrent-API interleaving fuzz; Jade PIN-relay trust | Next cycle |
| CT-42's status-endpoint remedy for a lying-txid pause; CT-44's legacy-tag enumeration restated each cycle | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |

## 10. Decisions the owner is asked to make

1. **Release number.** A patch bump to **0.7.4**, on the owner's instruction: the
   cycle-10 report holds the grade on CT-36, and the remediation ships as the next
   patch.
2. **CT-36 — classify by type, not by status code.** The app raises the not-sent
   refusal only where it can prove it (the checks before the request is written)
   and calls everything else unknown. This is the report's first remedy; the
   alternative — asking an explorer whether the payment exists before clearing the
   marker — needs a second network round trip inside the failure path and still
   trusts one server to describe another's state, so it is deferred to the
   next-cycle item above.
3. **CT-41 — add the test, change no code.** The behaviour was verified correct in
   production; what was missing was the alarm.
4. **CT-39 and CT-40 — schedule, do not record.** Both are inventory precision
   with executable pins, so both close in this cycle rather than being carried as
   prose.
5. **CT-38, CT-42, CT-44 — record, do not schedule.** CT-38 cannot be fixed in a
   locked plan, CT-42 is a fail-closed residual with a known remedy, and CT-44 is a
   restatement of an accepted one. None changes behaviour, so none can have a
   closing test.
6. **Who executes.** The plan is written to be executed item by item, each with its
   own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every work order above
is recorded row by row in `releases/PATCH-0.7.4.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`a227da4`, where the audit found them; the closing code and tests live in the tree
that ships this file.

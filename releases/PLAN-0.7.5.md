# Plan 0.7.5 — remediation of the v0.7.4 Color Team findings

**Inputs.** The cycle-11 Color Team audit of the published release `v0.7.4`
(tag `9d4d7bb471c80512cac7b7dc6c014855393cac4f`, committed
2026-10-27T07:47:58-04:00, ten release artifacts published `2026-10-27T12:26:15Z`),
graded **⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.4.md`
  (SHA-256 `6bf67462f2953bba1d56f462d7ed6047c3112b2af6bf7e4b0829b16f6a018a65`)
  — the public report, grade and ledger CT-45…CT-52;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.4.md`
  (SHA-256 `e11f57ef39386c4e677a64807f09fea3309a92f1924838080464584989273781`)
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.4.md`
  (SHA-256 `d8c75a9df3f350218e178ea7fcbdbcfc6b00206d14a73893a886640eaa4a7799`)
  — the scope lock (plan SHA-256 `ae9f557401317cf7857c821fe3fd935809b7855de734b6358746c7b841894ae8`
  at start and end, so the scope never moved);
- the auditor's private briefing, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The `v0.7.3` block was discharged **by execution**
— the referee personally re-broke the 4xx→unknown branch and the unknown-conversion
branch, red → byte-identical restore → green — CT-36 and CT-41 are **converted by
execution**, and the grade holds on two missing alarm tests over one control:
**CT-47 (Info, binding under ruling 1)**, the settings-refusal branch of the
not-sent boundary, which no test could fail, and **CT-49 (Low, independently
sustaining CONDITIONAL under ruling 5)**, a pin that asserts the exception class
for each input shape but not that the refusal happens *before* the request is
written — position is the whole point of that control.

**Why this plan is short.** Both binding findings are tests, not production
changes: the behaviour is right and fail-closed, and the referee proved it at zero
I/O. The two Low/Info findings the plan also schedules are one type guard at the
engine boundary (CT-45) and one `raise` that keeps a deliberate abort distinct from
a lost reply (CT-46), plus a rolling history pin (CT-51). No capability is added and
no transaction construction, signing, fee or network rule changes.

---

## 0. The ledger, round trip

Every id the v0.7.4 report grades is accounted for here; the count runs CT-01…CT-52
with no gap and no silent close.

- **CT-01…CT-35** — closed in the earlier cycles of this lineage: carried with no
  regression, converted by execution, or accepted in writing. The v0.7.4 report
  re-read the chain and found it intact.
- **CT-36, CT-37, CT-41** — **converted by execution** in the v0.7.4 audit. The
  referee re-broke `wallet_service.py`'s 4xx branch and `gui.py`'s unknown
  conversion, watched each named pin go red, restored byte-identically and watched
  them go green. The scenario the previous audit demonstrated — a 4xx after the
  signed bytes, then a second payment with no pause armed — now fails closed.
- **CT-39, CT-40** — **converted by execution**: `CM-43`'s range now contains the
  arm, and `CM-47`/`CM-48` exist as rows with their own markers and pins.
- **CT-38** — **closed in writing** by the signed `v0.7.4` plan: its §5 T-10 cites
  real test names at the audited revision. (The hash-locked `v0.7.3` plan could not
  be rewritten after its audit; the fix moved to the next signed plan.)
- **CT-42, CT-44** — recorded residuals, carried with their triggers (§9), with no
  claim of a fix.
- **This cycle's findings** — CT-45, CT-46, CT-47, CT-49 and CT-51 are **scheduled**
  (§5, five rows: CT-47 and CT-49 as Tier 1); CT-48, CT-50 and CT-52 are **recorded**
  (§6) and have no closing test because none of the three changes behaviour.

## 1. What is actually wrong (in plain terms)

1. **The check that refuses a settings-invalid explorer URL has no alarm.** The app
   refuses to send when the configured Esplora URL is not a plain URL — that is a
   provable non-send, so it raises the not-sent refusal and the reviewed payment
   stays retryable. But the test that covers this hidden branch by moving the branch
   back to the definite-refusal text would be a test of nothing: the branch is
   never exercised by the engine tests at all, so its deletion leaves the suite
   green. The behaviour is right; the alarm is absent. That is the clause the grade
   binds on.
2. **The pin checks the class, not the order.** `CM-50` claims the not-sent refusal
   is reserved for checks that run *before* the request object exists. The pin runs
   five input shapes through the function and asserts the class per shape; it does
   not assert that no request was built. A future edit that moved a raise below the
   `Request(...)` construction would keep every named pin green while the app
   claimed a provable non-send after the point of no return — exactly CT-36's class.
3. **The engine takes argument types on trust.** `broadcast_transaction` indexes a
   dict with `chain` and calls `.strip()` on the hex. Called through the GUI these
   are always the right types, but the function is public and documented as the
   engine's entry point: a caller passing a list or `None` gets a raw `TypeError` or
   `AttributeError` out of a function whose own contract says provable not-sent
   failures are `BroadcastNotSent`. Nothing can have been written at that point, so
   the correct answer is the refusal, not a traceback.
4. **A deliberate abort is reported as a transport unknown.** If the operator
   interrupts the submit (Ctrl-C, interpreter shutdown) the handler converts the
   `KeyboardInterrupt` into `BroadcastOutcomeUnknown`. Arming the pause is correct —
   bytes may have left — but replacing the exception type means an embedding host
   cannot tell "the user aborted" from "the network swallowed the reply".
5. **The newest release window's history is unpinned.** The v0.7.4 window's row is
   accurate and names every run, but the pin that holds the v0.7.3 row looks only at
   that row, and at the `v0.7.4` tag the window's row does not exist yet. The
   undercount shape that CT-43 disclosed could therefore recur in the row a reader
   consults first, with the suite green.

## 4. What the tree that ships this plan verifies

These are the facts the audit is asked to re-check at the delta, taken from the
tree that carries this file, not from the audit's description of it.

- **The suite.** `PYTHONPATH=tests python -m unittest discover -s tests -q` →
  `Ran 744 tests`, `OK`, in the checkout and again in the extracted source
  archive. `BroadcastOutcomeTests` is 40 tests and `SendFlowTests` is 39.
- **The JavaScript suites.** All eleven `node tests/ui_*.cjs` exit 0.
- **The inventory.** `CONTROLS.md` is 50 rows; every row is bound by
  `tests/test_controls_inventory.py` to a `CONTROL: CM-##` marker inside the range
  it cites and to a test the build loads.
- **The ledger.** `tests/test_ledger_completeness.py` holds this plan to
  `releases/PATCH-0.7.5.md`: one row per scheduled id, five rows, each with a
  severity and a closing test that loads, and no deferral.
- **The corpus.** §0 accounts for CT-01…CT-52 with no gap: every id the v0.7.4
  report graded is either carried, converted by execution, accepted in writing,
  closed in this cycle, or recorded as a note.
- **Break-and-watch.** 20 cases — the five this cycle adds and the fifteen the
  previous cycle recorded, re-run against this tree — each broken on a disposable
  copy, watched red, the copy restored byte-for-byte and the same check re-run
  green (`releases/BREAK-AND-WATCH-0.7.5.md`).
- **The published set.** `v0.7.4` is the newest published tag at the time of
  writing (`9d4d7bb`, ten assets); `v0.7.3`, `v0.7.2` and their predecessors are
  present and untouched. This plan is signed against `v0.7.4`, the revision the
  audit read.
- **The `0.7.5` tag does not exist yet.** It is cut by the promote run after this
  file's publication placeholders are filled, so this plan's §4 is a statement
  about the source tree, not about bytes on the Releases page.

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the `AGENTS.md`
rule: break the control on a disposable copy, watch the named test go red, restore.
Full transcripts are in `releases/BREAK-AND-WATCH-0.7.5.md`.

### Tier 1 — the two findings that set the floor

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-47 | Info (binds CONDITIONAL under ruling 1) | `wallet_service.py:113-116` at `9d4d7bb`. The settings-refusal branch (`validate_esplora_url` raising → `BroadcastNotSent`) is unexercised by every named engine test, so its regression to the old definite-refusal text leaves the suite green. | One test that runs three settings-rejected `base_url` shapes through `broadcast_transaction`, asserts `BroadcastNotSent` with the settings message, and asserts `urlopen` was never called. No production change: the branch already behaves correctly. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_a_settings_rejected_url_is_provably_not_sent`; row `CM-50`. Break-and-watch: the `except SettingsError` conversion reverted to `WalletError` gives `wallet_service.WalletError: Use a plain Esplora URL without credentials, query, or fragment.` out of the `base_url='http://example.com/api'` subTest; restore → green. |
| W2 | CT-49 | Low (independently sustaining CONDITIONAL under ruling 5) | `tests/test_wallet_service.py:73-93` vs `wallet_service.py:103,116` at `9d4d7bb`. The pin asserts the exception class per input shape but not that no request object was built, so the not-sent refusal's *position* — its entire claim — is unpinned for the chain and settings branches. | One test that patches `wallet_service.Request` with `wraps=` and `urlopen`, drives five pre-POST refusal shapes, and asserts both were never called. No production change. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_no_not_sent_answer_is_raised_after_the_request_is_built`; row `CM-50`. Break-and-watch: a `Request` constructed above the gate gives `AssertionError: Expected 'Request' to not have been called. Called 1 times.`; restore → green. |

### Tier 2 — the other scheduled findings

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W3 | CT-45 | Low | `wallet_service.py:102-112` at `9d4d7bb`. A non-string `chain` or hex reaches a dict lookup or `.strip()` and escapes as a raw `TypeError`/`AttributeError`, so a direct engine caller sees a traceback where the contract promises the not-sent refusal. | The engine now checks the two argument types before anything else: a non-string chain is "Unsupported broadcast network." and a non-string hex is "The finalised transaction is not valid hex.", both `BroadcastNotSent`, both provably pre-POST. The GUI already passes correct types, so no app behaviour changes. | `tests/test_wallet_service.py::BroadcastOutcomeTests::test_non_contract_argument_types_are_refused_before_anything_is_sent` (list and `None` chain, bytes and `None` hex, bytes `base_url`); rows `CM-50`. Break-and-watch: the `isinstance(chain, str)` guard removed gives `TypeError: unhashable type: 'list'`; restore → green. |
| W4 | CT-46 | Info | `gui.py:1374-1399` at `9d4d7bb`. `KeyboardInterrupt`/`SystemExit` inside the submit window is converted to `BroadcastOutcomeUnknown`, so the host cannot distinguish a deliberate abort from a lost reply. | After the pause is armed and the payment recorded, a `BaseException` that is not an `Exception` is re-raised unchanged. An ordinary failure still becomes the unknown outcome. The pause is identical either way — only the exception type the host sees is restored. | `tests/test_send_flow.py::SendFlowTests::test_an_interrupt_during_the_submit_arms_the_pause_and_still_propagates`; row `CM-46`. Break-and-watch: the re-raise replaced by `if False: raise` gives `AssertionError: KeyboardInterrupt not raised`; restore → green. |
| W5 | CT-51 | Info | `RELEASE-HISTORY.md` 0.7.4 row and `CURRENT-STATUS.md` at `27d04f6`. The window's record is accurate on `main` but the automatic test pins only the 0.7.3 row, and at the tag the 0.7.4 row does not exist. | `ReleaseWindowDisclosureTests` gains `LATEST_WINDOW` — the version, both run ids and the counts phrase — and a test that reads the newest `| **<version>** |` row and requires every id, the counts and "nothing was published from" in it, with a negative half. The constant moves with each cycle. | `tests/test_hardening_pins.py::ReleaseWindowDisclosureTests::test_the_newest_row_names_every_run_of_its_window` (with `…::test_the_newest_window_pin_would_fail_without_a_run` as its negative half). Break-and-watch: run `40498861357` renamed to `40498861399` gives `AssertionError: '40498861357' not found in "| **0.7.4** | Color Team cycle-10 remediation…"`; restore → green. |

### Work in this cycle that is not a finding

- **Release mechanics.** `version.py` moves to 0.7.5 and every user-facing version
  reference moves in the same commit — the download page's URLs, labels, JSON-LD
  and patch-record link, the manuals, the README, the status documents, this plan
  and the ledger. `releases/RELEASE-NOTES-0.7.5.md` and the cycle's
  `RELEASE-HISTORY.md` row are part of the same commit. The promote run has to
  pass `notarize=true`, because the workflow refuses to publish an unsigned build
  (`.github/workflows/build-candidate.yml:58`), and the candidate's manifest must
  be checked for `notarize=true` before any promote is dispatched — the v0.7.3
  window's second refactor of that lesson.
- **The audit's own inventory work.** No row is added: `CM-46` now names the abort
  half and `CM-50` names the settings branch, the position test and the type guard,
  all inside the ranges they already cited. The inventory test still reads 50 rows,
  and the two rows now carry five named pins between them.
- **The v0.7.4 cycle's public artifacts.** The report, security statement and
  index row the audit published are committed in this cycle, and the four v0.7.4
  plan artifacts move to `audit-history/` unedited, as every earlier cycle's did.

## 6. The record-keeping notes

The audit graded none of these with an asset path, and none changes behaviour, so
none is a work order and none has a closing test — which means this plan names them
here rather than letting them close by silence.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| CT-48 | CT-43's negative half is static string arithmetic on an embedded record, not an execution of the pin against it. | Substance holds: the referee executed the composition by hand and the main pin discriminates (it is break-and-watched). The negative half remains a string assertion because the alternative — a second fixture history file — would test a copy of the record rather than the record. Recorded in `releases/PATCH-0.7.5.md`; no code change. |
| CT-50 | The lying-txid pause residual re-demonstrated: a pause recorded against an invented txid cannot be reconciled by an honest explorer. | Accepted residual, in the fail-closed direction, unchanged from the last two cycles; the status-endpoint remedy stays on the next-cycle list. Restated in `releases/PATCH-0.7.5.md`. |
| CT-52 | The Apple staple flake recurred in this window's promote attempt 1 (and in the 0.7.2 and 0.7.3 windows). | Restated residual: every failure is fail-closed and publishes nothing; the failed job was re-run once and attempt 2 published. No work order — the alternative is weakening the gate during a release, which was declined. |
| CT-38 | Carried: the hash-locked `v0.7.3` plan's T-10 citation. | Closed in writing by the signed `v0.7.4` plan (§5 T-10 now cites real test names at its audited revision). Nothing left to fix; restated so the chain shows the close. |
| CT-44 | The legacy-tag residual: 46 dispatchable tags enumerated, sweep green. | Restated in `releases/PATCH-0.7.5.md` and carried on the next-cycle list. Nothing new is claimed about the legacy tags. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the prior plan and the ledger, unchanged and with their triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Real-Esplora `/outspend` mempool semantics — does a public Esplora report an unconfirmed spend of an output, and does an honest Esplora answer 400 after acceptance? | Next cycle (still open; the fail-closed classification no longer depends on the answer) |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey; pywebview/WebView2 JS-bridge runtime test | When an emulator or Windows/GUI host is available |
| Per-package PyPI identity cross-check of every locked dependency; second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next cycle / next practice-network change |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering; concurrent-API interleaving fuzz; Jade PIN-relay trust | Next cycle |
| CT-50's status-endpoint remedy for a lying-txid pause; CT-44's legacy-tag enumeration restated each cycle; CT-52's staple flake restated each cycle | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |

## 10. Decisions the owner is asked to make

1. **Release number.** A patch bump to **0.7.5**, on the owner's instruction: the
   cycle-11 report holds the grade on CT-47 and CT-49, and the remediation ships as
   the next patch.
2. **CT-47 and CT-49 — add the alarms, change no production code.** Both behaviours
   were verified correct and fail-closed by the referee, who executed them; what
   was missing was the test that could fail. Writing the test is the whole fix.
3. **CT-45 — refuse the argument types at the boundary.** The engine is public and
   the refusal is provably pre-POST, so the type guard belongs in the engine rather
   than in a comment telling callers to be careful. It cannot affect the app, whose
   call sites pass a pinned chain and a `str` hex.
4. **CT-46 — preserve the abort.** The pause is armed before the re-raise, so the
   fail-closed property is unchanged; only the exception type the host sees is
   restored. The alternative — swallowing the interrupt — would be a fail-closed
   pause with a lie about why.
5. **CT-51 — pin the newest window, not just the last one.** The constant is
   updated each cycle; that is a small ongoing cost in exchange for the history row
   a reader consults first being held by a test.
6. **CT-48, CT-50, CT-52 — record, do not schedule.** None changes behaviour: CT-48
   is a note about a negative half whose substance holds, CT-50 an accepted
   residual, CT-52 an external flake that stays fail-closed.
7. **Who executes.** The plan is written to be executed item by item, each with its
   own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every work order above
is recorded row by row in `releases/PATCH-0.7.5.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`9d4d7bb`, where the audit found them; the closing code and tests live in the tree
that ships this file.

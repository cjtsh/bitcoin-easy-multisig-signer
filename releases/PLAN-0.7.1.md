# Plan 0.7.1 — remediation of the v0.7.0 Color Team findings

**Inputs.** The cycle-7 Color Team audit of the published release `v0.7.0`
(tag `4fe8f2955e29cae6838e2ba0b8029c9abae9fdeb`, committed
2026-10-16T01:10:30-04:00, ten release artifacts published `2026-10-16T06:15:36Z`),
graded **⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.0.md`
  — the public report, grade and ledger CT-19…CT-21;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.0.md`
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.0.md`
  — the scope lock (plan SHA-256 `0ce8aeda808ff2f5e770c19ea74ed3db5e63654165249ee99b421e483ea8cdb5`
  at start and end);
- the auditor's private coaching document, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The conversion gate was met in full — the referee
re-broke both conversion-gating findings from the cycle before (the fair-admission
server in both directions, and each of the three prevout limbs) and watched the
discriminating tests fail, so 18 of 18 prior findings are verified fixed **by
execution** and none was closed by acceptance — the delta introduced no Critical
or High, and the grade is held below CLEARED by CT-21 and CT-20: two Informational
findings in the same pin-accuracy family that held the three cycles before it, both
of them about the test and tracking apparatus rather than the signer.

**Why this plan is short.** Cycle 6 rebuilt one shape (fair admission) and answered
the housekeeping; the panel confirmed each answer by re-running the break the
finding described. What remains is a guard with no test that can fail, a scanned
file set that did not include the release workflow, and one docstring that
described the availability trade inaccurately. Every item is corrections-only: no
capability is added, no wallet, signing or broadcast path is touched, and the
signed and broadcast bytes of 0.7.1 are the bytes of 0.7.0.

---

## 1. What is actually wrong (in plain terms)

1. **The guard nobody could break (CT-21).** `gui.py:669-679` closes a connection
   the server retired while its request was being read, so the operator's console
   never sees a broken-pipe traceback. The referee deleted the guard and the whole
   integration suite stayed green. The guarded *behaviour* was established
   independently by direct experiment, and the guard's precondition — a retirement
   that lands between accept and parse — is not reachable under the server's
   HTTP/1.0 semantics, so an honest end-to-end test cannot exist. But the
   repository's own rule is that a control has a test that can fail, and the
   rubric's CONDITIONAL clause names "stated invariants that lack the test
   coverage the repo claims".
2. **The net that did not read the workflow (CT-20).** `CONTROLS.md`'s claim-phrase
   net scanned the shipped Python and the release scripts, not
   `.github/workflows/*.yml`. The referee added a "fail closed" comment to the
   workflow and the inventory suite passed it unseen, and the CT-16 guard's own
   claim comment had arrived untracked for the same reason. The guard is present,
   effective, fail-closed and pinned; the gap is in the tracking layer.
3. **The docstring that overstated the token (CT-19).** The connection ceiling's
   class docstring implied that the page's token was what protected a slot. It is
   not: a slot is claimed by a complete request head, and the token is required by
   the routes that do something. The underlying trade — a local process that keeps
   complete requests in flight can occupy every slot — is accepted by the owner and
   self-heals within the 15 s read budget, with no declared asset reachable; what
   was wrong was the description, and a description nothing pins is how the next
   cycle finds it again.

---

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the `AGENTS.md`
rule: break the control on a disposable copy, watch the named test go red, restore
it. Full transcripts are in `releases/BREAK-AND-WATCH-0.7.1.md`.

### Tier 1 — the two findings that set the floor

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-21 | Info | `gui.py:669-679` (at `4fe8f29`). The retired-set guard in the handler's `parse_request` had no test that could fail: deleting it left the full integration suite green, because its precondition is not reachable under the server's HTTP/1.0 semantics. | Keep the guard and pin it synthetically rather than dropping it. One handler instance is driven over a `socket.socketpair()` so the retirement can be made observable: the server is a real `BoundedThreadingHTTPServer`, the connection is admitted, a newcomer evicts it through the production `_admit` path with `gui._shutdown_quietly` patched to a no-op, and only then is a malformed request written and the handler run. The test asserts the retired connection sends **zero bytes** and that no route was dispatched; the positive half runs the same malformed request on a live connection and expects the 400 with no dispatch. No line was added to `gui.py` on account of this test — the `CONTROL: CM-36` marker is appended to an existing comment line, so no other row's citation moved. | `tests/test_gui_integration.py::RetiredConnectionGuardTests::test_a_retired_connection_is_closed_without_an_answer` and `…::test_a_live_connection_still_answers_a_malformed_request`; row `CM-36`. Break-and-watch: delete the guard → the retired half fails with an HTTP 400 body where it expects `b""`; restore → green. |
| W2 | CT-20 | Info | `tests/test_controls_inventory.py:34-39` (at `4fe8f29`). The inventory's claim-phrase net did not read `.github/workflows/*.yml`, so a "fail closed" claim comment added to the workflow passed the inventory suite unseen — and the CT-16 guard's own claim arrived untracked. The guard itself is present, effective and pinned; the gap is the tracking layer. | Widen `SHIPPED` to the release workflow files and give each claim the workflow makes its own row: `CM-33` (retired-publisher pagination, `.github/workflows/build-candidate.yml:785-798`), `CM-34` (notarisation credential, `…:344-346`), `CM-35` (release-key signing, `…:934-937`) — each with its own `CONTROL: CM-##` marker inside the cited range and a closing test the build loads. `CM-33` reuses the CT-16 pins; `CM-34` and `CM-35` gain executable pins that run the workflow's step body with stubbed `bash` and `gpg`, assert the exact refusal message the gate prints, and assert the positive half. `ui.html` stays outside the scanned set, and the reason is recorded in the inventory's preamble: its one control claim is already `CM-30`, pinned by `tests/test_ui_scripts.py`, so widening the set again would add a scanned file without adding a control. A test now fails if the workflow file class leaves `SHIPPED`. | `tests/test_controls_inventory.py::ControlInventoryTests::test_the_release_workflow_files_are_scanned` and `…::test_every_marker_has_a_row_in_the_same_file`; `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_more_registrations_than_the_page_holds_refuses` (CM-33); `…::CredentialGuardTests::test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused` (CM-34); `…::CredentialGuardTests::test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one` (CM-35). Break-and-watch: remove the workflow glob from `SHIPPED` → the scanned-set test goes red; delete the notarisation refusal → the CM-34 pin goes red; replace the key check with `if false:` → the CM-35 pin goes red. |

### Tier 2 — the recorded observation

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W3 | CT-19 | Info | `gui.py:163-176, 183-189` (at `4fe8f29`). A sustained tokenless busy-flood can still hold all 32 slots. The auditor accepted this as the design's stated trade — availability only, self-healing within the 15 s read budget, no declared asset reachable — but the class docstring described it inaccurately: it implied the page's token was what protected a slot, when a complete request head is. | Accept the trade and document it exactly: a slot is claimed by a complete request head "and nothing more", the token is required only by the routes that do something, and a newcomer is refused only when every admitted connection is busy. Then pin the corrected sentence, because a comment the suite does not hold is the same finding one cycle later: a new test class drives a real bounded server over a socketpair and asserts (a) a complete head claims the slot with no token present — the route is then dispatched and refuses it with 403 — and (b) a half-sent head claims no slot at all. Row `CM-37` names the claim. No behaviour changed. | `tests/test_gui_integration.py::SlotClaimSemanticsTests::test_a_complete_request_head_claims_the_slot_without_the_token` and `…::test_a_half_sent_request_head_claims_no_slot`; row `CM-37`. Break-and-watch: make the busy claim require the token → (a) fails with `[False] != [True]`; put admitted connections straight into the busy set → (b) fails. |

### Work in this cycle that is not a finding

- **The terms of use.** On 2026-10-25 the owner asked that the project's terms
  carry the default legal section published at
  [cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer)
  (framework v1.2.2, effective 2026-10-21). `DISCLAIMER.md` is now the project's
  copy of that framework with the Bitcoin Easy Signer specifics folded in, and
  every surface that points at it — README, user manual, the three `docs/` pages,
  the in-app About dialog and footer, current status — names both the project's
  copy and the canonical URL. The framework's own rule is stated rather than
  softened: notice or a link alone may not establish contractual assent. No
  acceptance gate was added, because that would be a functional change.
- **Release mechanics.** `version.py` moves to 0.7.1 and every user-facing version
  reference moves in the same commit; `releases/RELEASE-NOTES-0.7.1.md` and this
  cycle's `RELEASE-HISTORY.md` row are part of that commit.

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the prior plan and the ledger, unchanged and with their triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey; pywebview/WebView2 JS-bridge runtime test | When an emulator or Windows/GUI host is available |
| Per-package PyPI identity cross-check of every locked dependency; second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next cycle / next practice-network change |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering; concurrent-API interleaving fuzz; Jade PIN-relay trust | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |

## 10. Decisions the owner is asked to make

1. **Release number.** A patch bump to **0.7.1**, on the owner's instruction. No
   functional change is in this release, and the ledger records it as such.
2. **CT-21 — pin it, or drop it.** This plan pins it. The alternative the auditor
   offered (drop the guard and record the reliance on shutdown semantics) was
   considered and rejected: the guard costs nothing at runtime and the pin is
   honest about what it demonstrates.
3. **CT-20 — widen the set, or record a rationale.** This plan widens it to the
   workflow files and excludes `ui.html` with a reason in the inventory's own
   preamble, because the workflow held an untracked claim and the page did not.
4. **CT-19 — accept the trade.** Accepted and documented, with the corrected
   description pinned so it cannot drift back.
5. **Who executes.** The plan is written to be executed item by item, each with
   its own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every item above is
recorded row by row in `releases/PATCH-0.7.1.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`4fe8f29`, where the audit found them; the closing code and tests live in the tree
that ships this file.

# Plan 0.6.9 — remediation of the v0.6.8 Color Team findings

**Inputs.** The cycle-5 Color Team audit of the published release `v0.6.8`
(tag `0d4e01f60c7695d720099f9d8e9e23b38da63102`, artifacts published
2026-10-11), graded **⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md`
  — the public report, grade and ledger CT-01…CT-12;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.6.8.md`
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.8.md`
  — the scope lock (plan SHA-256 `20e7f55f8b2e4913327fd0be099ad5992eaff6c987ede6af66349cbe8cf371a1`
  at start and end);
- the auditor's private coaching document, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** Nothing unforgivable was reached — the four acts
the rubric forbids all held, the money path refused every attack the lanes
brought, and the published `v0.6.8` bytes verified end to end — but four Low
findings each describe a control that is *believed* rather than *pinned*, and one
of them is the instrument that is supposed to catch the other three.

**Why this plan is short.** The 0.6.8 plan rebuilt the pipeline's evidence
machinery from the ground up: the M1 render harness, the M4 control inventory,
the M5 publish-path sweep, the M7 platform record. Those instruments did their
job — the audit that produced CT-01…CT-12 was able to *use* them. What it found
is that four of them still have a soft spot, and eight housekeeping items that
were recorded rather than fixed. 0.6.9 is a corrections-only patch release: it
pins the soft spots, sweeps the housekeeping, and adds no capability.

**The owner's instruction, verbatim:** *"OK FIX THE ITEMS !"*

---

## 1. What is actually wrong (in plain terms)

The graded findings are four Lows. Each one is the same shape: a control the
build *claims* to pin, which a referee can move or delete without the suite
noticing. In ascending order of importance by the coaching document's own
ordering:

1. **The instrument of record cannot detect rot (CT-03).** `CONTROLS.md` says in
   its header that the build "fails when a cited file, line, test or
   `CONTROL: CM-##` marker stops agreeing with it". Fifteen of twenty rows were
   content-bound to nothing: the reader checked that a cited file existed and
   that the last cited line was inside it, and nothing else. The referee moved
   CM-18 from `gui.py:498-530` onto `gui.py:10-20` — the module's import block —
   and the suite stayed green. This is fixed first because it is the instrument
   that would have caught CT-01 and CT-02 automatically next cycle.
2. **A branch that no test can fail (CT-01).** `wallet_service.py:130-134`
   refuses a broadcast response body that is not a 64-hex transaction id, and
   raises `BroadcastOutcomeUnknown`. The behaviour is safe — the GUI backstop at
   `gui.py:1103-1107` converts any wrong body to "outcome unknown" anyway — but
   the branch itself was pinned by nothing, so deleting it would have changed
   nothing the build could see.
3. **Three first-line guards pinned only by their deeper twins (CT-02).**
   `gui.py:978-982` (the device returned a different transaction),
   `gui.py:1219-1220` (a payment is already waiting for a confirmation) and the
   `/api/sign` review-id path each have a cheap first check and a deeper check
   behind it. Only the deeper one was tested. The first check is the one that
   produces the message a person reads, and it is the one that is unpinned.
4. **The download page was correct only after the fact (CT-04).** The tag's
   `docs/index.html` pointed at the *previous* release's assets until the page was
   corrected on `main` after publication. The live site is right; the tag is
   immutable and still wrong. Nothing in the build compared the page to the
   version being released.

The remaining eight findings are Info-severity housekeeping, recorded by the
audit and scheduled here so that "recorded" does not mean "forgotten": the token
in browser history (CT-05), tracebacks in the startup failure log (CT-06),
protections missing from the inventory (CT-07), two unauthenticated market reads
(CT-08), an unbounded connection pool (CT-09), GitHub immutable releases not
enabled (CT-10), retired publisher registrations still on the platform (CT-11),
and the one-time libusb producing run that no longer survives to re-match
(CT-12).

---

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the AGENTS.md
rule: break the control on a disposable copy, watch the named test go red,
restore it.

### Tier 1 — the instrument (first, by the coaching document's instruction)

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-03 | Low | `tests/test_controls_inventory.py` read `CONTROLS.md` and checked only that a cited file existed and that the last cited line was inside it. `CONTROLS.md:6-8` claims more than that: "fails the build when a cited file, line, test or `CONTROL: CM-##` marker stops agreeing with it". The referee re-pointed CM-18 at `gui.py:10-20` and the suite stayed green. | Add `ControlInventoryTests::test_every_row_cites_its_own_marker`: for every row, resolve the cited range through the existing `site()`/`cited_file()` helpers and assert the row's own `CONTROL: CM-##` marker appears inside it. Then give every row a marker by appending one to an existing line inside its range, so no cited line number moves, and re-point the rows my own edits had already made stale. | Break-and-watch: re-point CM-18 at `gui.py:10-20` → the new case fails with the citation named; restore and it passes. Recorded in `PATCH-0.6.9.md`. |

### Tier 2 — the money-path pins

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W2 | CT-01 | Low | `wallet_service.py:130-134` raises `BroadcastOutcomeUnknown` for a body that is not 64 lowercase hex characters. The GUI backstop at `gui.py:1103-1107` makes the *behaviour* safe, so no test could fail: a test that patched the branch away would still see a safe outcome. | Pin the branch itself: patch `wallet_service.urlopen` to return each malformed body shape and assert `BroadcastOutcomeUnknown` with the "Do not send" instruction. Add the positive half — an upper-case 64-hex body is accepted and lower-cased — so the check cannot be replaced by an unconditional refusal. | New cases in `tests/test_wallet_service.py::BroadcastOutcomeTests`. Break-and-watch: delete the length/hex check → the malformed cases go red; make it refuse everything → the positive case goes red. |
| W3 | CT-02 | Low | Three first-line guards were unpinned duplicates of deeper pinned guards: `gui.py:978-982` (device returned a different transaction — the existing test asserted only HTTP 400), `gui.py:1219-1220` (a payment is waiting for one confirmation), and the `/api/sign` review-id path. | Decide per layer, as the coaching document allows: pin each first-line guard by its own name and message rather than deleting it, because each one is the guard that produces the sentence a person reads. Assert the refusal text, not just the status code, and assert the side effects did *not* happen (nothing was accepted into the reviewed transaction, nothing was built). | `tests/test_send_flow.py::SendFlowTests`: `test_a_device_returning_a_different_transaction_is_refused` now asserts the message, the unchanged prepared payment and no partial signatures; the new `test_prepare_refuses_while_a_payment_waits_for_confirmation` asserts the message and that the builder was never called; `test_signing_requires_the_reviewed_transaction` asserts "Review the current transaction". Break-and-watch: rename each refusal in `gui.py` → the named case goes red. |
| W4 | CT-04 | Low | `docs/index.html` hard-coded the previous release's version in the JSON-LD `softwareVersion`/`downloadUrl`, the `Version …` eyebrow, the three download buttons and the risk paragraph. At the `v0.6.8` tag the page pointed at `v0.6.7`'s assets; it was corrected on `main` after publication and the tag is immutable. | There is no template step — Pages serves the committed file — so bind the page to the single source of truth instead of templating it: bump every reference to the releasing version and add a test that derives the expected version from `version.APP_VERSION` and refuses any download URL, visible version label, JSON-LD `softwareVersion` or finding-record link that names another version. Require at least one download link per shipped platform so a silent deletion is caught too. | New `tests/test_docs_version.py`. Break-and-watch: repoint the Windows button at `v0.6.8` → the case fails naming `['0.6.8']`; restore. |

### Tier 3 — the housekeeping the audit recorded

| # | ID | Sev | Location | Fix | Acceptance |
| --- | --- | --- | --- | --- | --- |
| W5 | CT-05 | Info | `ui.html` read the local access token from `location.hash` and left it there, so the fragment — and the token — survived in the browser's session history for as long as the tab lived. | Read the fragment once, copy the value into per-tab `sessionStorage` (which dies with the tab and lets a reload keep working), and rewrite the address bar with `history.replaceState` so no history entry names it. | New `tests/ui_token_history.cjs`, driven through the real page script in a Node `vm`, asserts both halves: the token reaches the app and the next request carries it; the address bar left behind does not. Loadable from the ledger as `tests/test_ui_scripts.py::UiScriptTests::test_ui_token_history`. Break-and-watch: remove the rewrite → the case goes red. |
| W6 | CT-06 | Info | `desktop.py` wrote `"".join(traceback.format_exception(...))` to the startup failure log, which carries absolute host paths from the operator's own machine. The failure is pre-wallet, so no wallet material was implicated. | Record the failure's type and message only, bounded to a fixed length, instead of the traceback. Keep the file where it was so the operator can still find it. | `tests/test_desktop.py::StartupFailureTests`: the rewritten `test_a_failed_start_writes_the_failure_beside_the_settings` asserts the exact one-line record and the absence of `Traceback` and `File "`; `test_a_long_failure_message_is_bounded` asserts a 10,000-character error is truncated to the limit. Break-and-watch: restore the traceback write → both go red. |
| W7 | CT-07 | Info | `CONTROLS.md` omitted protections the code claims and pins elsewhere: the loopback `Host` gate, the script nonce, the unknown-broadcast outcome, the fee floors, and the private-file modes. | Add a row per protection with its real location, its own `CONTROL: CM-##` marker inside the cited range, and a closing test that loads — CM-22 to CM-26. | `tests/test_controls_inventory.py` reads all 26 rows and exits green; W1's new case proves each new row's marker is inside its own range. |
| W8 | CT-08 | Info | `gui.py`'s `do_GET` answered `/api/price` and `/api/fees` without a token. Both are reads, neither is wallet material, and the loopback + `Host` gate still applied — but "public" is not the same as "unauthenticated". | Put the market reads behind the same token check as every other endpoint, and have the page send `X-Local-Token` on both fetches. | New `tests/test_gui.py::LocalGuiTests::test_the_market_reads_refuse_without_the_local_token` asserts 403 on both routes with the upstream fetchers untouched; the two cached-read cases now carry the token. Break-and-watch: drop the new branch → the refusal case goes red. |
| W9 | CT-09 | Info | A 15-second connection budget was enforced per thread, and the thread count was unbounded, so a burst of stalled connections could hold arbitrarily many threads. | Bound the pool with a `BoundedSemaphore` acquired non-blockingly before the request is dispatched: when the ceiling is reached, the socket is closed rather than queued. Use the bounded server in both `gui.main()` and `desktop.py`. | New `tests/test_gui_integration.py::ConnectionCeilingTests` holds more sockets than the ceiling and asserts the excess are closed, that the server answers again once slots come back, and that `gui.main()` builds the bounded class. Break-and-watch: raise the ceiling to unbounded → the closure case goes red. |
| W10 | CT-10 | Info | Overwrite protection rested on the workflow's existing-tag guard, the tag ruleset and account hygiene; the platform's own immutable-release setting was off, and nothing in the repository read it. | Enable immutable releases on the repository, read the setting in `scripts/check-platform-state.sh`, record it in `releases/platform-state.json`, and assert the recorded value. | `tests/test_platform_state.py::PlatformRecordTests::test_the_platform_makes_published_releases_immutable`; the differ reports the live posture matches the record. |
| W11 | CT-11 | Info | `build-linux.yml` and `build-windows.yml` were deleted from every branch, but the platform still lists both registrations (state `disabled_manually`). The deletion API answers 404 because the files survive in the immutable tag trees, so the registrations can be re-enabled from the UI after a release with nothing in the repository noticing. | Make the run itself refuse: a fail-closed step on the candidate-and-publish path reads the live workflow registrations and fails if either retired publisher is not `disabled_manually`. It fails closed on a read that did not happen, because a guard that passes by not looking is the defect. | New `tests/test_publish_guards.py::RetiredPublisherGuardTests` covers the disabled pair, a re-enabled one (refused and named), a registration that is gone, an unreadable platform, and that the step runs on both `publish` values. Break-and-watch: delete the step → the wiring case goes red. |
| W12 | CT-12 | Info | `vendor/libusb-1.0.dll` is pinned in four agreeing places, but the one-time producing run no longer survives, so the pin could not be re-matched from evidence. | Re-dispatch `.github/workflows/windows-inputs.yml` from `main`, download the `windows-libusb` artifact, and compare its digest to the four recorded pins. Record the run URL, the digest and the comparison in `PATCH-0.6.9.md`. | `tests/test_libusb_vendor.py::LibusbVendorTests::test_the_shipped_native_libraries_are_the_reviewed_ones` loads the four pins; the comparison itself is recorded evidence, which is what the finding asks for. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the ledger and the auditor's coaching document, with triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Per-package PyPI identity cross-check of every locked dependency | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey | When an emulator host is available |
| pywebview/WebView2 JS-bridge runtime test (needs a Windows/GUI host) | Next Windows-capable review |
| Second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next practice-network change |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | Resolved for the run path by W11; the registrations themselves stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering | Next cycle |
| Concurrent-API interleaving fuzz beyond T1-8/T2-5; Jade PIN-relay trust | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |
| Archive of the audit reproducer scripts (currently under `/tmp`, documented in writing only) | Housekeeping; not security-relevant |

## 10. Decisions the owner is asked to make

1. **Release number.** This plan assumes a patch bump to **0.6.9** — corrections
   only, no new capability, per `AGENTS.md` and the 0.4.4/0.6.8 plan precedent.
   Say so if you want a minor bump instead.
2. **CT-02, pin or delete.** The coaching document leaves both open. This plan
   pins, because each first-line guard produces the sentence the operator reads
   and deleting it would move that sentence into a deeper branch. Confirm that is
   the trade you want rather than a smaller handler.
3. **CT-11, run-path guard or platform cleanup.** GitHub's API answers 404 for a
   delete on a registration whose file still exists in any tag, so the guard is on
   the run path. If you would rather the registrations disappear, the tag trees
   are immutable and this plan cannot do it.
4. **Who executes.** The plan is written to be executed item by item, each with
   its own commit and its own break-and-watch record.

---

**Status.** Draft for owner review. Nothing in this plan has been applied to the
code yet on the owner's behalf beyond the work recorded in `PATCH-0.6.9.md`.

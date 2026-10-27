# Findings ledger — owner-maintained convenience index

> *Owner-maintained convenience index. It is **not** an audit artifact. The
> authoritative status source is the audit reports and the per-cycle audit index;
> every row cites the record it was transcribed from. Where a record states a status
> for a bundle of findings, the row says so rather than implying a per-finding
> finding.*

**What this file is for.** Answering "is CT-31 open?" in one lookup instead of a
four-document read. It carries labels, not arguments: no reasoning, no finding text,
no severity justification. A label points at the record; it never replaces it.
Where this file and a report disagree, the report wins and this file is wrong.

**Two sections, two namespaces.** The audit numbering restarted at v0.6.8. The
earlier lineage (v0.6.4–v0.6.7) and the current lineage (v0.6.8 onward) **reuse the
same `CT-NN` ids for different findings** — earlier `B/CT-48` is "live dispatchable
publish paths", current CT-48 is "CT-43's negative half is static string
arithmetic". The sections are never merged, renumbered or cross-mapped, and **no id
appears in both**. Section B ids carry a `B/` prefix for exactly that reason: the
bare string is ambiguous, so **an unqualified `CT-NN` always means the current
lineage**, and only a `B/`-prefixed id means the earlier one.

**Words, not artefacts.** The tokens *BSMS*, *PSBT* and *xpub* appear below only
where they are part of a transcribed finding label ("Request-size and 2 MB PSBT
bounds unpinned"). No record, key, address, transaction or device path is reproduced
in this file.

**Path shorthand.** `…-report-v<cycle>.md` means
`bitcoin-easy-multisig-signer-colorteam-audit-report-v<cycle>.md`, under
`audit-history/` for v0.6.8–v0.7.4 and at the repository root for v0.7.5. In
Section B the same shorthand is used inside the named tag tree.

**Status vocabulary.** Table cells use these short forms; the record wording they
stand for is quoted here once, so a cell never invents a status.
`Closed — carried` = *carried, verified fixed; no regression*. `Closed — converted
v0.7.4` = *converted v0.7.4; carried, no regression*. `Closed — execution` =
*CONVERTED (closed) by execution* (parenthesised ruling number = the v0.7.4 ruling
discharged). `Closed — owner acceptance` = *closed by written, dated owner
acceptance* (ruling 2; substances verified). `Open — future maintenance` = the
report's future-maintenance lane. Section B forms are literal transcriptions of that
lineage's own wording: `Verified fixed v0.6.6`, `Partially fixed`, `Open`, `Open
deferral → 2027-10-07`, `Closed as observation`, `Positive holds`, `accounted
v0.6.7` (the v0.6.7 report accounts for every prior id without restating each one).

**Counts, transcribed not totalled.** Section A holds 57 ids: **52 closed, 5 open**
(CT-53…CT-57, future maintenance). Of the 52 closed, the appendix names **six**
owner-acceptance closures (CT-38, CT-42, CT-44, CT-48, CT-50, CT-52), five
per-finding execution closures this cycle (CT-45, CT-46, CT-47, CT-49, CT-51), six
converted at v0.7.4 (CT-36, CT-37, CT-39, CT-40, CT-41, CT-43), and the rest carried
with no regression. Section B holds 95 ids; its final record is the v0.6.7 report,
which reports **1 High · 8 Medium · 7 Low · 8 Info** open plus 2 deferrals.

**Updating.** Never delete a row. A correction is a new dated line, never a rewrite
of a row to a later state. This file may not claim a closure or a grade that no
record records, and may not restate a finding's text. IDs, cycles, short labels and
paths only: no BSMS record, xpub, address, PSBT, device path or wallet artefact.

---

## Section A — current lineage (v0.6.8 onward): CT-01…CT-57

| ID | Sev | First recorded | Title (label, not argument) | Status | Status source | Evidence |
|---|---|---|---|---|---|---|
| CT-01 | Low | v0.6.8 | The malformed-broadcast-body branch has no test that can fail … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-02 | Low | v0.6.8 | Three first-line guards are unpinned duplicates of deeper pinned guards | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-03 | Low | v0.6.8 | 15 of 20 inventory rows are not content-bound … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-04 | Low | v0.6.8 | The tag's download page pointed at the previous release's assets until corrected on … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-05 | Info | v0.6.8 | Browser-mode #token= can persist in browser history for the session; desktop product unaffected | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-06 | Info | v0.6.8 | Startup-failure log carries tracebacks (host paths); pre-wallet, so no wallet material can appear | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-07 | Info | v0.6.8 | The 20-row inventory omits several claimed-and-pinned protections | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-08 | Info | v0.6.8 | /api/price and /api/fees require no token; bounded public data only | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-09 | Info | v0.6.8 | The 15 s connection budget is per-thread with unbounded threads … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-10 | Info | v0.6.8 | GitHub immutable releases not enabled … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-11 | Info | v0.6.8 | Retired publishers remain registered (disabled_manually) … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-12 | Info | v0.6.8 | Pinned in four agreeing places … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.8.md` → v0.7.5 appendix |
| CT-13 | Low | v0.6.9 | A hostile local process can hold all 32 connection slots (idle for 15 … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-14 | Low | v0.6.9 | The value and script limbs of the build-time prevout match lack discriminating pins … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-15 | Info | v0.6.9 | Five claimed-and-pinned protections added by this release (the connection ceiling, the token gate … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-16 | Info | v0.6.9 | The retired-publisher guard reads only page 1 of the workflow registrations (no --paginate … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-17 | Info | v0.6.9 | The Windows startup-failure dialog interpolates the unbounded exception text … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-18 | Info | v0.6.9 | The row understates the windows-inputs.yml delta since the producing run (the lock job's … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.6.9.md` → v0.7.5 appendix |
| CT-19 | Info | v0.7.0 | A sustained tokenless busy-flood can still hold all 32 connection slots … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.0.md` → v0.7.5 appendix |
| CT-20 | Info | v0.7.0 | The inventory's claim-phrase net is blind to .github/workflows/*.yml (and ui.html) … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.0.md` → v0.7.5 appendix |
| CT-21 | Info | v0.7.0 | The retired-set execution guard has no test that can fail … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.0.md` → v0.7.5 appendix |
| CT-22 | Low | v0.7.1 | The pending-payment pause has no broadcast-time gate: a second fully-reviewed payment can be … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.1.md` → v0.7.5 appendix |
| CT-23 | Info | v0.7.1 | Plan §4's gui.py line citations are stale at this revision (substance of every … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.1.md` → v0.7.5 appendix |
| CT-24 | Low | v0.7.1 | check_selected_outpoints does not refuse a duplicated input inside one PSBT (demonstrated at the … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.1.md` → v0.7.5 appendix |
| CT-25 | Low | v0.7.1 | The explorer-failure contract leaks http.client failure shapes (RemoteDisconnected/BadStatusLine … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.1.md` → v0.7.5 appendix |
| CT-26 | Info | v0.7.1 | The release window had three failure events … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.1.md` → v0.7.5 appendix |
| CT-27 | Medium | v0.7.2 | Both gate halves read pending_broadcast_txid, written only after broadcast_transaction returns … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-28 | Info | v0.7.2 | The CM-38 comment "cannot both submit" is false (concurrent same-payment submits both 200 … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-29 | Low | v0.7.2 | Last-recorder-wins on the pending record can stick the pause for the session (restart … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-30 | Info | v0.7.2 | CM-38's inventory row cites only the early half … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-31 | Info | v0.7.2 | The source-archive secret-scan control is untracked in the inventory (CT-07/15 class) | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-32 | Info | v0.7.2 | Plan §4/§5 stale gui.py citations (one instance corrected by the referee … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-33 | Low | v0.7.2 | Pure RST mid-response raises ConnectionResetError (OSError), absent from verify_esplora's catch tuple … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-34 | Info | v0.7.2 | explorer_get's bounded read returns truncated bodies as success; callers' format checks demonstrated fail-closed | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-35 | Info | v0.7.2 | This release window's five failed candidate attempts (run 40397174519 attempts 1–5, all in … | Closed — carried | v0.7.5 appendix — row `CT-01…CT-35` (bundle) | `…-report-v0.7.2.md` → v0.7.5 appendix |
| CT-36 | Medium | v0.7.3 | A broadcaster that receives the complete signed bytes then replies 400 is classified … | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-37 | Low | v0.7.3 | Raw non-WalletError escapes (RuntimeError demonstrated) classify as definite … | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-38 | Info | v0.7.3 | Plan §5 T-10 cites a test name that does not exist at this … | Closed — owner acceptance | v0.7.5 appendix — row `CT-38, 42, 44` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-39 | Info | v0.7.3 | CM-43's cited range stops five lines short of the arm it claims | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-40 | Info | v0.7.3 | The final-vs-review comparison and the review-id binding carry no CM row (protections hold … | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-41 | Low | v0.7.3 | The early gate's in-flight half is unpinned: deleting it leaves every named pin … | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-42 | Info | v0.7.3 | A lying-txid pause records the intended txid … | Closed — owner acceptance | v0.7.5 appendix — row `CT-38, 42, 44` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-43 | Low | v0.7.3 | This release window's disclosure undercount: five runs/nine attempts live (cancelled run … | Closed — converted v0.7.4 | v0.7.5 appendix — row `CT-36, 37, 39, 40, 41, 43` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-44 | Info | v0.7.3 | Legacy-tag residual: 46 dispatchable tags enumerated; sweep green | Closed — owner acceptance | v0.7.5 appendix — row `CT-38, 42, 44` (bundle) | `…-report-v0.7.3.md` → v0.7.5 appendix |
| CT-45 | Low | v0.7.4 | Raw TypeError/AttributeError for non-contract input types at the engine boundary (pre-POST provable not-sent … | Closed — execution | v0.7.5 appendix — row `CT-45` (per-finding) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-46 | Info | v0.7.4 | KeyboardInterrupt/SystemExit in the submit window are converted to unknown (exception type replaced) | Closed — execution | v0.7.5 appendix — row `CT-46` (per-finding) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-47 | Info | v0.7.4 | CM-50's settings-refusal branch (validate_esplora_url → BroadcastNotSent) is held by no test that can … | Closed — execution (ruling 1) | v0.7.5 appendix — row `CT-47` (per-finding) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-48 | Info | v0.7.4 | CT-43's negative half is static string arithmetic on an embedded record, not an … | Closed — owner acceptance | v0.7.5 appendix — row `CT-48, 50, 52` (bundle) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-49 | Low | v0.7.4 | CM-50's pin asserts the exception class but not the checks' position relative to … | Closed — execution (ruling 5) | v0.7.5 appendix — row `CT-49` (per-finding) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-50 | Info | v0.7.4 | The CT-42 residual re-demonstrated unchanged (lying-txid pause persists, fail-closed) | Closed — owner acceptance | v0.7.5 appendix — row `CT-48, 50, 52` (bundle) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-51 | Info | v0.7.4 | This window's disclosure is unpinned and absent at the tag (the pin guards … | Closed — execution | v0.7.5 appendix — row `CT-51` (per-finding) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-52 | Info | v0.7.4 | The Apple staple flake recurred (this window's promote attempt 1 … | Closed — owner acceptance | v0.7.5 appendix — row `CT-48, 50, 52` (bundle) | `…-report-v0.7.4.md` → v0.7.5 appendix |
| CT-53 | Low | v0.7.5 | The CT-45 type guard admits str subclasses … | Open — future maintenance | v0.7.5 appendix — new-findings row `CT-53` (per-finding) | `…-report-v0.7.5.md` (root) |
| CT-54 | Info | v0.7.5 | The 0.7.5 window record is unpinned at its own tag (LATEST_WINDOW pins 0.7.4 … | Open — future maintenance | v0.7.5 appendix — new-findings row `CT-54` (per-finding) | `…-report-v0.7.5.md` (root) |
| CT-55 | Info | v0.7.5 | CT-51's negative half is static string arithmetic and never reads the record … | Open — future maintenance | v0.7.5 appendix — new-findings row `CT-55` (per-finding) | `…-report-v0.7.5.md` (root) |
| CT-56 | Info | v0.7.5 | Pin-coverage seam: CT-49's five-shape tuple omits the two type-guard shapes and CT-45's test … | Open — future maintenance | v0.7.5 appendix — new-findings row `CT-56` (per-finding) | `…-report-v0.7.5.md` (root) |
| CT-57 | Info | v0.7.5 | Plan T-10's "exactly 64 lowercase hex" is stricter than the code (64 uppercase … | Open — future maintenance | v0.7.5 appendix — new-findings row `CT-57` (per-finding) | `…-report-v0.7.5.md` (root) |

---

## Section B — earlier lineage (v0.6.4–v0.6.7): CT-01…CT-95

**Superseded numbering. Not on `main`. These files survive only in tag trees, and
the tag varies per file (see the table below). Do not merge, renumber or cross-map
with Section A.**

The earlier artifacts were removed from `main` by `d21ef6c3d` (2026-10-11, "Leave
one audit plan in the repository root"). Each file's earliest tag, verified with
`git cat-file -e`:

| Cycle | Report file | Earliest tag containing it |
|---|---|---|
| v0.6.4 | `…-report-v0.6.4.md` | `v0.6.5` |
| v0.6.5 | `…-report-v0.6.5.md` | `v0.6.6` |
| v0.6.6 | `…-report-v0.6.6.md` | `v0.6.7` |
| v0.6.7 | `…-report-v0.6.7.md` | `v0.6.8` — its own tag does not contain it |

This lineage's final record is the **v0.6.7 report**, which closes the range at 95
ids (new findings CT-72…CT-95) and states that all 71 prior ids are accounted for,
singling out CT-01, CT-48, CT-49 and CT-52 as partially fixed and CT-54 and CT-59 as
open deferrals. Status here is that report's wording; `accounted v0.6.7` means the
report carries the id forward without restating it, so `accounted v0.6.7` is the
strongest claim the record supports — do not read it as a per-finding closure.

| ID | Sev | First recorded | Title (label, not argument) | Final status (as recorded) | Status source | Evidence |
|---|---|---|---|---|---|---|
| B/CT-01 | High | v0.6.4 | Unsigned Windows bytes from an unmerged commit manually uploaded past every gate, checksum … | Partially fixed v0.6.6 and v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-02 | Medium | v0.6.4 | Linux bytes from a different unmerged commit attached by a failure-concluded run … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-03 | Medium | v0.6.4 | _check_final_review (final-vs-review recipient/amount/change/fee backstop, documented in … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-04 | Medium | v0.6.4 | Source-mode embit guard validates == "0.8.0" while the lock pins 0.8.2+besa.1 … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-05 | Low | v0.6.4 | _current_prepared binding (wallet/chain/generation/review-id) unpinned … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-06 | Low | v0.6.4 | Diagnostics device tokens pattern-sanitized (≤20 chars) rather than a whitelisted … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-07 | Low | v0.6.4 | 80-event diagnostics buffer cap unpinned | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-08 | Low | v0.6.4 | Request-size and 2 MB PSBT bounds unpinned | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-09 | Low | v0.6.4 | settings.json 0600/atomic-write permissions unpinned | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-10 | Low | v0.6.4 | checked_psbt() stored-state revalidation unpinned | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-11 | Low | v0.6.4 | No-retry-after-timeout half of the HWI rule lacks a fail-capable test … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-12 | Low | v0.6.4 | LIBUSB_SHA256 mandatory refusal enforced only by CI execution … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-13 | Low | v0.6.4 | Broadcast holds the session lock across explorer network I/O — a stalling explorer … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-14 | Low | v0.6.4 | Device identity is key-material only … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-15 | Low | v0.6.4 | Prevout-ownership refusals (script-owns-output, prevout match, vout range) have no in-repo … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-16 | Low | v0.6.4 | Release notes rewritten outside any run (workflow's own notes step failed … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-17 | Low | v0.6.4 | Runner images float (ubuntu-latest, macos-15); actions SHA-pinned and deps hash-pinned | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-18 | Info | v0.6.4 | Launch-URL docstring overstates fragment confidentiality (browser-mode history can … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-19 | Info | v0.6.4 | Dead __LOCAL_TOKEN__ strip in GET / (placeholder absent from ui.html) | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-20 | Info | v0.6.4 | Built-in mainnet/testnet4 explorer URLs not genesis-verified at scan (custom URLs … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-21 | Info | v0.6.4 | Build-fee consistency check and vsize math unpinned in-repo (Orange pinned … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-22 | Info | v0.6.4 | Fail-closed strictness observations (uppercase bech32 refused, high-S refused … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-23 | Info | v0.6.4 | Tokenless price/fees/GET / carry no wallet data … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-24 | Info | v0.6.4 | Stale self-contradicting comment ("stays unstapled") vs the actual staple-then-image order | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-25 | Info | v0.6.4 | Positive: redirect refusal doubly enforced (two independently sufficient layers, one … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.5`: `…-report-v0.6.4.md` |
| B/CT-26 | Medium | v0.6.5 | BIP-143 digest — the most load-bearing computation — has no … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-27 | Medium | v0.6.5 | Second live "0.6.5" Windows artifact set … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-28 | Low | v0.6.5 | Full-xpub device-identity comparison unpinned: fingerprint-only weakening stays green … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-29 | Low | v0.6.5 | Source-mode HWI resolves over PATH with no version identity … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-30 | Low | v0.6.5 | In-range lying price quote can suppress the USD trigger of the large-amount prompt … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-31 | Low | v0.6.5 | Four money-path gates oracle-correct but unpinned (outputs≤inputs … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-32 | Low | v0.6.5 | Build-time prevout/ownership binding unpinned (sign-time twin pinned as … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-33 | Low | v0.6.5 | Lock-generation tooling (pip-tools) not hash-pinned … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-34 | Low | v0.6.5 | No low-S (BIP-62) enforcement on imported signatures … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-35 | Info | v0.6.5 | Unauthenticated local GET /api/price, /api/fees (public data, Host-pinned, cache-bounded, no … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-36 | Info | v0.6.5 | Fee-quote parser bound (≤1000 sat/vB) differs from the policy cap (25) … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-37 | Info | v0.6.5 | _same_xpub ignores serialization version bytes; comparison-only, no downstream effect | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-38 | Info | v0.6.5 | Trust-bundle pin fails open to platform defaults by documented design … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-39 | Info | v0.6.5 | DesktopBridge URL pin passes when the window URL is unreadable … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-40 | Info | v0.6.5 | Client renderer version identity not establishable; no security decision depends on it | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-41 | Info | v0.6.5 | Master-key fingerprints read 0x00000000 … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-42 | Info | v0.6.5 | Full handler tracebacks print to console on malformed bodies/disconnects (source mode) … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-43 | Info | v0.6.5 | Saved PSBT keeps the "-unsigned" name after verified signatures attach … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-44 | Info | v0.6.5 | Default listen backlog; 1 connection reset in 160 rapid connects — resilience of … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-45 | Info | v0.6.5 | README-LINUX names SHA256SUMS-linux-x86_64.txt; the release ships single SHA256SUMS … | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-46 | Info | v0.6.5 | "Current published version is 0.6.4" inside the v0.6.5 tag — stale-by-construction | Verified fixed v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-47 | Info | v0.6.5 | Cross-platform dependency drift (cryptography 50.0.1 vs 50.0.2, etc.) … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.6`: `…-report-v0.6.5.md` |
| B/CT-48 | High | v0.6.6 | Live dispatchable publish paths publishing unsigned/unattested manifests from unreviewed branch code … | Partially fixed v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-49 | Medium | v0.6.6 | HWI helper identity = version-string self-attestation (planted binary accepted … | Partially fixed v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-50 | Low | v0.6.6 | UI large-amount floor unpinned mirror (backend authoritative) — one DOM test closes it | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-51 | Low | v0.6.6 | Request-log suppression unpinned — one stderr-capture test closes it | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-52 | Low | v0.6.6 | Guard pins assert names/strings not bodies … | Partially fixed v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-53 | Low | v0.6.6 | BSMS magic-line gate unpinned (unreachable; downstream refuses) — one hostile-header test | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-54 | Low | v0.6.6 | macOS dylib exact build lacks an upstream byte anchor (runner-image capture … | Open deferral → 2027-10-07 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-55 | Low | v0.6.6 | Python "3.12" patch level floats (3.12.10 vs 3.12.14 in one run) … | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-56 | Low | v0.6.6 | Tarball omits hwi-entitlements.plist (+2 files) — signed macOS rebuild from tarball fails | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-57 | Low | v0.6.6 | pip-tools version-pinned not hash-pinned; unpinned pip upgrade | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-58 | Low | v0.6.6 | HWI identity cached per path (TOCTOU) — re-verify per signing session | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-59 | Low | v0.6.6 | Stalling explorer can hold one scan tens of minutes (fail-closed, availability only) | Open deferral → 2027-10-07 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-60 | Low | v0.6.6 | Mainnet broadcaster not genesis-verified at use-time — verify unconditionally at _broadcast | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-61 | Info | v0.6.6 | Attacker-key BSMS importable by design (mitigations verified; trusted-delivery hop named) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-62 | Info | v0.6.6 | Large-amount message understates its own trigger (safe direction) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-63 | Info | v0.6.6 | bundled_capabilities bypasses the identity gate (build-time only, no wallet data) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-64 | Info | v0.6.6 | pending_by_wallet unpruned per session (bounded, memory) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-65 | Info | v0.6.6 | Two redundant txid clauses unpinned in isolation (cannot fire under SIGHASH_ALL) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-66 | Info | v0.6.6 | Proof-parse contract nits (all fail closed; no real device emits the shape) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-67 | Info | v0.6.6 | Key proof at /0/0 not account node — documented Trezor tradeoff | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-68 | Info | v0.6.6 | R-minimality relies on embit strict DER (re-review mandated on any embit bump) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-69 | Info | v0.6.6 | Device binding matches (type,path); re-verification carries residual | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-70 | Info | v0.6.6 | Browser-mode token persists in that browser's history (documented) | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-71 | Info | v0.6.6 | "Latest published release is 0.6.4" — stale prose post-publication | Open v0.6.6; accounted v0.6.7 | v0.6.7 appendix — carried-forward line (bundle) | tag `v0.6.7`: `…-report-v0.6.6.md` |
| B/CT-72 | High | v0.6.7 | Command injection: the free-text candidate_run_id dispatch input is interpolated raw into bash inside … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-73 | Medium | v0.6.7 | Source-mode HWI payload pin hashes 2 of 115 installed hwilib files … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-74 | Medium | v0.6.7 | The unsigned/unnotarized publish refusal is a control whose tests cannot fail: all three … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-75 | Medium | v0.6.7 | Four more publish guards are string-pinned only: inverted tag-guard comparison, shasum -c … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-76 | Medium | v0.6.7 | The sweep never examines tags while its header claims "any ref"; 13 historical … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-77 | Medium | v0.6.7 | Matcher blindness: write-all, gh api …/releases, curl api.github.com/…/releases, action-gh-release publishers … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-78 | Medium | v0.6.7 | The mainnet genesis literal has no pinning test: a true-value Signet swap leaves … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-79 | Medium | v0.6.7 | The bare-/* change-inference ban has no pinning test: removing the guard leaves test_change_branch.py … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-80 | Medium | v0.6.7 | v0.6.7 was signed/published through secrets the current environment scoping did not protect (environments … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-81 | Low | v0.6.7 | Non-ASCII X-Local-Token header → TypeError: connection killed without response, traceback to stderr. Fail-closed … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-82 | Low | v0.6.7 | Token-gate pin has no near-miss case: a last-6-chars comparison weakening stays green. Add … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-83 | Low | v0.6.7 | The release job holds contents: write on every dispatch, including publish=false candidates. Job-level … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-84 | Low | v0.6.7 | No total deadline on outbound HTTP; a dribbling broadcaster holds state.lock and freezes … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-85 | Low | v0.6.7 | No per-connection timeout on the loopback server … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-86 | Low | v0.6.7 | No automated secret-value scan of repo/artifacts/logs is claimed or exists (manual grep + … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-87 | Low | v0.6.7 | Linux build toolchain unpinned (floating apt … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-88 | Info | v0.6.7 | The two embit source-archive digests are prose-only (no machine check) … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-89 | Info | v0.6.7 | The change-descriptor key-match check is unreachable as written (template expansion copies the same … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-90 | Info | v0.6.7 | Practice-network outpoint recheck is single-source (the plan's named T5 asymmetry … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-91 | Info | v0.6.7 | The sequence-coercion the fork fixed in psbt.py survives unused in pset.py … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-92 | Info | v0.6.7 | The double-click source launcher installs embit only … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-93 | Info | v0.6.7 | signing-key.asc is excluded from the source archive while the release notes point at … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-94 | Info | v0.6.7 | Attestation REST endpoints 404 for this repo while gh attestation verify succeeds (2 … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |
| B/CT-95 | Info | v0.6.7 | The HWI_PAYLOAD_PINS re-assertion tripwire cannot fail against real package bytes (asserts the constant … | Open v0.6.7 | v0.6.7 appendix — new-findings row (per-finding) | tag `v0.6.8`: `…-report-v0.6.7.md` |

---

## Section C — living-document citations that resolve outside the current lineage

Ids cited by a living document that do **not** resolve in Section A. All currently
resolve in Section B; **no id is currently unresolved**.

| Cited id | Living document | Where it resolves | Note |
|---|---|---|---|
| `B/CT-46`, `B/CT-71` | `CURRENT-STATUS.md:140` | Section B | Cited as "the CT-46/CT-71 defect class" to forbid restating a latest-published-version sentence. Both resolve in the earlier lineage (CT-71 filed the stale-version prose); current CT-46 is a different finding, so a reader who looks up the bare id lands in the wrong section. |
| `B/CT-49`, `B/CT-58` | `HWI-DEPENDENCY.md:70`, `:98` | Section B | "Helper identity (CT-49, CT-58)" and the one-line CT-58 control statement both describe the earlier lineage's helper-identity findings (CT-49: version-string self-attestation; CT-58: identity cached per path, re-verify per signing session). Current-lineage CT-49 is a wallet-service position pin and is unrelated, so a bare-id lookup lands on the wrong finding. |
| `B/CT-80` | `RELEASE-PROCESS.md:216` | Section B | Credential-wiring finding from the v0.6.7 cycle, cited as the origin of the `environment:` rule. |
| `B/CT-89` | `CONTROLS.md:80` | Section B — **not** unresolved | Earlier-lineage CT-89 is "the change-descriptor key-match check is unreachable as written (template expansion copies the same descriptor) — defense-in-depth that cannot fire", at `probe.py:161-169`. That is the same subject the `CONTROLS.md` cell describes ("the check that claimed otherwise was deleted"), so the citation **resolves and is correct in substance**. It is recorded here because the plan's ruling N4 treated `CT-89` as a typo in no lineage; the v0.6.7 report at tag `v0.6.8` is the record that contradicts that premise. |
| `B/CT-94` | `RELEASE-PROCESS.md:132` | Section B | Attestation-endpoint finding from the v0.6.7 cycle, cited as the reason both repository-attestation URL halves are load-bearing. |

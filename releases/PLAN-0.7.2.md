# Plan 0.7.2 — remediation of the v0.7.1 Color Team findings

**Inputs.** The cycle-8 Color Team audit of the published release `v0.7.1`
(tag `8923ca0273380a9cb1ea7e7e964c6332dda5a777`, committed
2026-10-26T17:40:02Z, ten release artifacts published `2026-10-26T18:13:21Z`),
graded **⚠️ CONDITIONAL**:

- `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.7.1.md`
  — the public report, grade and ledger CT-22…CT-26;
- `bitcoin-easy-multisig-signer-colorteam-security-statement-v0.7.1.md`
  — the public statement;
- `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.7.1.md`
  — the scope lock (plan SHA-256 `6137530d0117fa31a076e0738cc9e82ecbc73825ba688785b64951f0d711d88c`
  at start and end);
- the auditor's private coaching document, evidence index and lane reports
  (held outside the repository, by design).

**The grade, in one sentence.** The conversion gate was met by execution — the
referee deleted the retired-set guard, removed the workflow glob from the
inventory's scanned set and neutralised the `CM-35` key check, and watched each
named pin go red, while Blue break-and-watched all eleven tripwires; `gui.py` was
AST-identical with docstrings stripped and all seven engine files blob-identical at
`v0.7.0` and `v0.7.1`, so 21 of 21 prior findings are verified fixed **by
execution** — the delta introduced no Critical or High, and the grade is held below
CLEARED by **CT-22 (Low)**: the pending-payment pause is stated by threat row T-11
but was asserted only at preparation, so a second fully reviewed payment could be
submitted while the first was unconfirmed whenever the explorer stayed silent about
the first spend.

**Why this plan is short.** CT-22 is one gate in the wrong place: the refusal that
already exists one step earlier belongs at the step that moves the money. The two
others are hardening margins the audit proved unreachable in-product (CT-24) or
already fail-closed end-to-end (CT-25), and the two remaining notes (CT-23, CT-26)
are record-keeping. No capability is added and no transaction construction,
signing, fee or network rule changes — but this is the first revision since 0.5.1
that changes app behaviour, so the release notes say so plainly instead of reusing
the "engine unchanged" sentence.

---

## 1. What is actually wrong (in plain terms)

1. **The pause that was one step too early (CT-22).** After a payment is
   broadcast, the app shows a pending notice and refuses to *prepare* another
   payment from that wallet (`gui.py:1379-1380` at `8923ca0`). The pause is armed
   only after a submit succeeds (`:1286`), and `_broadcast` (`:1205-1293`) itself
   never looks at it. An honest explorer still refuses the second spend through
   the outspend recheck (`wallet_service.py:238-242`), so the window opens when
   the explorer is silent about the first spend — the exact case the pause exists
   for. The audit named the path: refuse in `_broadcast` when the wallet has a
   pending payment, or re-check the pause under the pre-submit lock. This plan
   does both, because a check that is not under the same lock as the submit can
   still be overtaken by a second request.
2. **A duplicated input nobody reaches (CT-24).** `check_selected_outpoints`
   (`wallet_service.py:190-242` at `8923ca0`) refuses an output the explorer says
   is spent, but not the same output named twice inside one PSBT. The audit
   proved four independent refusals behind it — scan dedup, the builder, the
   transaction-identity gate and consensus relay — so this is hardening, not a
   live path. Hardening that costs one pass over the inputs is worth having, and
   the refusal is free because it happens before any explorer is asked.
3. **The error contract with a hole in it (CT-25).** `verify_esplora`'s except
   tuple (`network_settings.py:146-151` at `8923ca0`) names `HTTPError`, `URLError`,
   `TimeoutError`, `UnicodeError` and `ValueError`, but not
   `http.client.HTTPException` — the shape a server produces when it hangs up
   mid-reply (`RemoteDisconnected`, `BadStatusLine`). The outcome was verified
   fail-closed (a fixed 500, nothing broadcast, settings unsaved), but the
   documented message and the stage diagnostic are lost, and the same tuple shapes
   matter more on the broadcast path, where "unknown outcome" is what pauses the
   wallet. The existing tests patch `urlopen`, so none of them can produce these
   shapes; the pins have to drive a real socket.

## 5. Work orders

Severity is the referee's calibrated value. "Break-and-watch" is the `AGENTS.md`
rule: break the control on a disposable copy, watch the named test go red, restore.
Full transcripts are in `releases/BREAK-AND-WATCH-0.7.2.md`.

### Tier 1 — the finding that sets the floor

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W1 | CT-22 | Low | `gui.py:1205-1293` (at `8923ca0`). `_broadcast` asserted no pending-payment pause: the pause armed at `:1286` and gated only `_prepare` at `:1379-1380`, so a second reviewed and separately consented payment could be submitted while the first was unconfirmed, whenever the explorer stayed silent about the first spend. An honest explorer refused it at the outspend recheck (`wallet_service.py:238-242`), which is why the audit rated it Low rather than High. | Refuse at both places, because one gate is overtakeable. In `_broadcast`, after the confirmed-transaction check, read `state.pending_broadcast_txid` under the state lock and refuse with one message — "A payment from this wallet is waiting for one confirmation. Check that it went through before sending another." — before any explorer pre-check runs. Re-assert the identical refusal inside the lock the submit takes, before the prepared-payment identity check, so two requests that both pass the early check cannot both submit. Two tests, because either half alone can pass while the other is missing: the first primes a pending txid and asserts the refusal *and* that no explorer was asked (`verify_selected_outpoints` not called), the second arms the pause from a `finalize_multisig` side effect during the request, so only the in-lock check can refuse it, and asserts the broadcaster was never called. | `tests/test_send_flow.py::SendFlowTests::test_broadcast_refuses_while_a_payment_waits_for_confirmation` and `…::test_a_broadcast_racing_a_pending_payment_is_refused_under_the_lock`; row `CM-38`. Break-and-watch: the early refusal replaced by `if False:` → the first case fails with `Expected 'verify_selected_outpoints' to not have been called. Called 1 times.`; the in-lock re-assertion replaced by `if False:` → the second fails with `Expected 'broadcast_transaction' to not have been called. Called 1 times.` Both restores re-ran green. |

### Tier 2 — the two hardening margins

| # | ID | Sev | Defect and location | Fix | Acceptance (test + break-and-watch) |
| --- | --- | --- | --- | --- | --- |
| W2 | CT-24 | Low | `wallet_service.py:190-242` (at `8923ca0`). `check_selected_outpoints` did not refuse a duplicated input inside one PSBT. Proven unreachable in-product against an honest explorer, by scan dedup, the builder, the transaction-identity gate and consensus relay — so this is defence in depth, and the audit recorded it as a coverage note rather than an open path. | One pass over `packet.tx.vin` before any explorer call, building `(txid, vout)` tuples into a set and refusing a repeat with "The transaction spends the same Bitcoin output twice. Refresh the balance and prepare it again; nothing was sent." The refusal is placed first so it costs no explorer round trip and cannot be mistaken for a spent-output refusal. | `tests/test_outpoint_check.py::OutpointCheckTests::test_a_duplicated_input_is_refused_before_any_explorer_is_asked`, with a new `packet_with_a_repeated_input()` helper asserting the message and `asked == []`; row `CM-39`. Break-and-watch: the refusal deleted → `AssertionError: WalletError not raised`; restore → green. |
| W3 | CT-25 | Low | `network_settings.py:146-151` (at `8923ca0`), the outer contract at `gui.py:929`, and the two transport tuples in `wallet_service.py`. The explorer-failure contract leaked `http.client.HTTPException` shapes (`RemoteDisconnected`, `BadStatusLine`), so a peer that is not speaking HTTP escaped the documented refusal and reached the generic handler as a fixed 500 — fail-closed, but without the message or the stage diagnostic. On the broadcast path the same shape must become an unknown outcome, which is what pauses the wallet. | Add `http.client.HTTPException` to all three tuples: `verify_esplora` (`network_settings.py:148-156`), `broadcast_transaction` (`wallet_service.py:127-134`, still raising `BroadcastOutcomeUnknown`) and `explorer_get` (`wallet_service.py:174-181`). Because the existing tests patch `urlopen` and cannot produce these shapes, three socket-level tests pin them: a raw socket that answers a non-HTTP status line, and a small `HTTPServer` whose handlers write the same garbage, exercised against the settings check, the explorer read and the broadcaster. | `tests/test_network_settings.py::BrokenReplyTests::test_a_reply_that_is_not_http_is_reported_as_unavailable` and `…::test_a_reply_that_stops_before_the_hash_is_refused_by_name`; `tests/test_wallet_service.py::BrokenReplyTests::test_an_explorer_that_does_not_speak_http_is_a_named_outage` and `…::test_a_broadcaster_that_does_not_speak_http_is_an_unknown_outcome`; rows `CM-40`, `CM-41`, `CM-42`. Break-and-watch: `HTTPException` removed from each tuple in turn → each pin fails with `http.client.BadStatusLine:  not-http` escaping the caller; restores re-ran green. |

### Work in this cycle that is not a finding

- **Release mechanics.** `version.py` moves to 0.7.2 and every user-facing version
  reference moves in the same commit — the download page's URLs, labels, JSON-LD
  and patch-record link, the manuals, the README, the status documents, this plan
  and the ledger. `releases/RELEASE-NOTES-0.7.2.md` and the cycle's
  `RELEASE-HISTORY.md` row are part of the same commit. The promote run has to
  pass `notarize=true`, because the workflow refuses to publish an unsigned build
  (`.github/workflows/build-candidate.yml:58`).
- **The `/outspend` question.** Ruling 5 of the audit left one fact unestablished:
  whether a public Esplora's `/outspend` reports a *mempool* spend for an output,
  which decides how often CT-22's backstop rather than the new gate would have
  been what refused the second payment. This plan does not resolve it, because the
  gate no longer depends on the answer; it is recorded as an open question for the
  next cycle (§9) rather than left implicit.

## 6. The two record-keeping notes

The audit graded neither of these as a finding with an asset path, and neither
changes behaviour, so neither is a work order and neither has a closing test —
which means this plan names them here rather than letting them close by silence.

| Note | What it said | Where this cycle records it |
| --- | --- | --- |
| CT-23 | The v0.7.1 plan's §4 `gui.py` line citations were stale at the revision the audit read; the substance of every claim was verified true, and the engine citations were accurate. | This plan and `releases/PATCH-0.7.2.md` cite a file and function for every claim, and give a line range only where the defect is a line in the prior revision; `CONTROLS.md` keeps the pinned `file:line` citations, and its own test binds each range to the marker inside it, which is how three of them were caught and retargeted in this cycle. |
| CT-26 | The release window had three failure events, and the cycle documents named two: the promote run's failed attempt 1 (macOS staple, `Error 68`, 18:01:11Z, publish jobs skipped) was unnamed, and the plan's "two earlier candidate attempts" conflated one run having two failed jobs. Nothing was published from any failure, and immutability held. | `RELEASE-HISTORY.md`'s 0.7.1 row, `CURRENT-STATUS.md` and `releases/PATCH-0.7.2.md` name all three events and the run that had them. |

---

## 9. Next-cycle list (named, deliberately out of scope)

Carried from the prior plan and the ledger, unchanged and with their triggers:

| Item | Trigger |
| --- | --- |
| Independent component audit of the pinned stack: embit 0.8.2+besa.1, HWI 3.2.0, libusb 1.0.30, pywebview 6.2.1, PyInstaller | Before 1.0, or the next dependency bump, whichever is first |
| Real-Esplora `/outspend` mempool semantics — does a public Esplora report an unconfirmed spend of an output? | Next cycle (decides how often the outspend recheck, rather than the new broadcast gate, would have refused a second payment) |
| A node runtime that survives a Homebrew `libllhttp` break, so the 11 JS suites rest on the same day as the Python baseline | Before the next cycle's suite baseline is taken |
| Reproducibility program: rebuild from the source archive and compare to the published hashes | Next cycle |
| HWI-emulator counterfeit-device end-to-end journey; pywebview/WebView2 JS-bridge runtime test | When an emulator or Windows/GUI host is available |
| Per-package PyPI identity cross-check of every locked dependency; second public Testnet4 Esplora and a second Mutinynet block-1 oracle | Next cycle / next practice-network change |
| `build-linux.yml` / `build-windows.yml` `disabled_manually` registrations | The registrations stay until the platform offers a delete that names them (CT-11) |
| `allowed_actions: "all"` and no platform-level action SHA pinning | Owner decision |
| macOS bundle-seal enforcement against same-user resource edits; `SSL_CERT_FILE` fallback in `safe_http.trust_bundle()`; device error-string social engineering; concurrent-API interleaving fuzz; Jade PIN-relay trust | Next cycle |
| CT-54 libusb rebuild from pinned source | Next dependency bump (expiry 2027-10-07) |

## 10. Decisions the owner is asked to make

1. **Release number.** A patch bump to **0.7.2**, on the owner's instruction:
   "Fix it, push to v0.7.2 and we will resubmit."
2. **CT-22 — where the gate lives.** Both halves are asserted, as the audit's
   first option proposed, rather than only the early check: the early refusal keeps
   the explorer out of the request, and the in-lock re-assertion is the one that
   holds when two requests arrive together.
3. **CT-24 — harden or record a rationale.** This plan hardens it. The refusal is
   free and the alternative is a ledger row arguing that four other layers make it
   unnecessary.
4. **CT-25 — widen all three tuples.** The explorer and broadcaster tuples are
   widened together, because a fix that made the settings path precise while the
   broadcast path still turned a dropped connection into a generic failure would
   leave the more important path unimproved.
5. **The `/outspend` question — record, do not resolve.** The gate no longer
   depends on it; the next cycle's referee should still have it in hand.
6. **Who executes.** The plan is written to be executed item by item, each with its
   own break-and-watch record.

---

**Status.** Executed. This plan was the cycle's work order; every work order above
is recorded row by row in `releases/PATCH-0.7.2.md` with its closing test, and each
closing test was break-and-watched on a disposable copy before the release was
built. The locations named as defects are the locations at the prior revision
`8923ca0`, where the audit found them; the closing code and tests live in the tree
that ships this file.

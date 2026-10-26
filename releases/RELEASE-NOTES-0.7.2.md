# Bitcoin Easy Signer 0.7.2

This release answers the Color Team cycle-8 audit of the `v0.7.1` tree. That cycle
re-checked the conversion gate: the referee deleted three guards the previous cycle
had pinned, watched each named test go red, and confirmed all twenty-one earlier
findings fixed **by execution**; `gui.py` was AST-identical with docstrings
stripped and all seven engine files blob-identical at both tags. The grade was held
at **CONDITIONAL** by one new **Low** finding, **CT-22**: the pause that stops a
wallet sending a second payment while the first is unconfirmed was asserted at
preparation and not at the broadcast, so the second payment could be submitted
whenever the explorer stayed silent about the first spend. An honest explorer
refused it at the outspend recheck, which is why the finding is Low and not High,
but the pause exists exactly for the case where the explorer says nothing.

Two hardening margins were reported beside it and are fixed here as well, and two
record-keeping notes are recorded. Each finding this cycle closed is in
`releases/PATCH-0.7.2.md` row by row, with its closing test and its break-and-watch
result.

**This release changes app behaviour**, unlike the three before it. It does not
change how an honest payment is prepared, signed, checked or broadcast, or which
networks are offered, or the fee ceilings.

## What changed

- **The unconfirmed-payment pause now holds at the submit, not only at
  prepare.** `_broadcast` refuses when the wallet has a submitted payment waiting
  for confirmation, before any explorer is asked, and re-asserts the same refusal
  under the lock the submit takes so two requests that both reach the final screen
  cannot both submit. The operator sees one fixed sentence on the final screen:
  "A payment from this wallet is waiting for one confirmation. Check that it went
  through before sending another." Two tests pin it — one that the early refusal
  keeps the explorer out of the request, one that arms the pause mid-request so
  only the in-lock check can refuse it — and both were break-and-watched. Row
  `CM-38`.
- **A transaction that names the same Bitcoin output twice is refused.** The app
  already could not reach this state — the scan dedups, the builder and the
  transaction-identity gate refuse it, and consensus relay would too — so this is
  hardening rather than a fix to a live path. The refusal now happens before any
  explorer is asked, with its own message. Row `CM-39`.
- **A network server that is not speaking HTTP is the documented refusal, not a
  generic failure.** The transport tuples now include `http.client.HTTPException`,
  the shape a server produces when it hangs up mid-reply. The settings check, the
  explorer read and the broadcaster all name it: on the first two it is the
  documented "check its /api URL and availability" or "could not connect" refusal,
  and on the broadcast path it remains an unknown outcome, which pauses the wallet
  rather than inviting a retry that might double-send. Four socket-level tests pin
  all three paths, because the older tests stubbed `urlopen` and could not produce
  the shape. Rows `CM-40`, `CM-41`, `CM-42`.
- **Two record-keeping notes are recorded rather than left implicit.** The audit
  noted that the previous plan's line citations had gone stale at the revision it
  read (the claims themselves verified true), and that the previous release's
  documents named two of the three failure events in its window — the promote run's
  failed first attempt was unnamed. Both are recorded in `RELEASE-HISTORY.md` and
  `CURRENT-STATUS.md`; `CONTROLS.md` keeps the pinned citations, and its test binds
  every range to the marker inside it.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The release
carries one checksum file covering macOS, Windows and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance policy, and
`releases/platform-state.json` for the platform posture this release was built
under.

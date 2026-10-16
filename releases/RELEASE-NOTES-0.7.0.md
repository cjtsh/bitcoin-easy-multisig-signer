# Bitcoin Easy Signer 0.7.0

This release answers the Color Team cycle-6 audit of the `v0.6.9` tree. That
cycle was the conversion re-check of the previous grade: the panel verified all
twelve earlier findings fixed **by execution** — the referee re-broke each fix
and watched its new test go red — and held the grade at **CONDITIONAL** on one
new Low in the same pin-accuracy family that held the two cycles before it, plus
one availability trade the new connection ceiling had introduced.

The wallet, transaction, signing and broadcast engine is unchanged: no capability
is added and no refusal message moves. Each finding this cycle closed is recorded
row by row, with its closing test and its break-and-watch result, in
`releases/PATCH-0.7.0.md`.

## What changed

- **The build-time prevout match now has a test that can fail for each of its
  limbs.** `wallet_service.py` checks three things about the previous transaction
  an explorer serves: that it hashes to the claimed txid, that it pays the claimed
  value, and that it pays the wallet's own script. The two tests named for the
  value and script limbs were rewriting the transaction — which changes its txid —
  so they were really testing the txid limb, and the audit demonstrated it by
  deleting each limb and watching the suite stay green. Each limb now has a case
  where the served transaction is untouched and the *scanned UTXO list* is the
  liar, so only that limb can refuse it.
- **The connection ceiling no longer lets a local process freeze the app.** The
  ceiling from 0.6.9 closed every socket beyond its limit, so a local program
  could hold all the slots and lock the operator's own window out. Admission is
  now fair: a newcomer is refused only when every admitted connection is busy;
  otherwise the oldest *idle* connection is hung up to make room. Silence and a
  half-sent request head are both idle; only a connection actively being served
  is protected, and serving one requires the page's access token. A surplus
  connection with every slot busy is still refused, exactly as before.
- **Six protections are now tracked in `CONTROLS.md`** as `CM-27`…`CM-32` — the
  connection ceiling, the constant-time token comparison, the market-read token
  gate, the token-history eviction, the bounded startup record, and the
  per-connection time budget — each with a marker inside the range it cites and a
  closing test the build loads. The inventory's claim-phrase net was widened to
  the claim shapes those comments used, so the same omission is caught next time.
- **The retired-publisher guard fails closed on a partial list.** It reads one
  page of the platform's workflow registrations; it now refuses when the platform
  reports more registrations than that page holds, or when the list it got does
  not match the reported count, instead of concluding from a partial view.
- **The Windows startup dialog shows the same bounded record as the log.** A
  message box cannot be scrolled, so a very long platform error used to become a
  dialog that ran off the screen; the full text is in the file the dialog names.
- **One sentence in the 0.6.9 record is corrected, in the open.** The provenance
  row for the vendored libusb DLL described its whole workflow file as differing
  only in comments and a runner pin, which omitted the separate lock job's
  hardening. The sentence is scoped to the job it is about, the rest of the delta
  is enumerated, and the correction is marked inline and dated.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The release
carries one checksum file covering macOS, Windows and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance policy, and
`releases/platform-state.json` for the platform posture this release was built
under.

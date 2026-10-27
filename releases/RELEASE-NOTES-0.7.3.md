# Bitcoin Easy Signer 0.7.3

This release answers the Color Team cycle-9 audit of the `v0.7.2` tree, which
graded **⛔ BLOCKED** on one new **Medium** finding, **CT-27**. The v0.7.1
conversion criterion was met **by execution** — the referee re-broke CT-22, CT-24
and CT-25 and watched each named test go red, CT-23 and CT-26 closed by dated owner
acceptance, and all twenty-one earlier findings were carried with no regression —
but the code added for CT-22 placed its pause in the wrong place in time.

Both halves of the broadcast pause read a record that was written only **after**
the first broadcast returned, and that call is bounded by
`BROADCAST_TIMEOUT_SECONDS = 20.0`. While the first payment was on the wire the
pause was still empty, so a second, separately reviewed and consented payment
passed both halves and was broadcast. Two examiners demonstrated it end to end
through the real `/api/*` routes. Threat row T-11 forbids exactly that outcome, and
the framework's ruling 4 makes a T-11 violation blocking at any severity. Nothing
was signed that the operator had not reviewed: this was a sequencing defect, not a
substitution.

This release closes CT-27 and the false comment beside it (CT-28), makes the
pending record per-transaction (CT-29), adds one missing exception class to the
settings transport tuple (CT-33), and closes the two inventory gaps the audit named
(CT-30, CT-31). Each is in `releases/PATCH-0.7.3.md` row by row, with its closing
test and its break-and-watch result.

**This release changes app behaviour.** It does not change how an honest payment is
prepared, signed, checked or broadcast, or which networks are offered, or the fee
ceilings, and `wallet_service.py` changes only a docstring.

## What changed

- **The pause is armed before the money leaves, not after.** A per-wallet in-flight
  marker is set inside the same critical section that checks for it, and the lock is
  released before the network call — so no slow broadcaster can stall the rest of
  the app. Both halves of the pause read the marker: the early refusal, which runs
  before any explorer is asked, and the one under the pre-submit lock. Every exit
  clears it, so a refused payment is still there to retry. The operator sees one
  fixed sentence: "A payment from this wallet is still being submitted. Wait for
  that result before sending another." Three tests pin it — a held broadcast, a
  marker armed mid-request so only the in-lock read can refuse, and a definite
  refusal that must leave nothing armed — and all three were break-and-watched.
  Rows `CM-38` and `CM-43`.
- **The pause remembers every payment, not just the last one.** The record is now a
  dictionary per wallet in submission order, and a refresh clears only the
  transactions the explorer reports confirmed. A second completed payment can no
  longer overwrite the first, and confirming the newer one can no longer lift the
  pause the older one still needs. Row `CM-44`.
- **A connection reset mid-reply is the documented refusal, not a generic
  failure.** `verify_esplora`'s tuple now carries `OSError`, the class a
  `ConnectionResetError` belongs to, matching the explorer and broadcaster tuples
  that already do. A real-socket test resets the connection after the reply head,
  because the older tests stubbed `urlopen` and could not produce the shape. Row
  `CM-40`.
- **The inventory now names both halves of the pause and the archive scan.**
  `CM-38` covers the early half, `CM-43` the check-and-arm, `CM-44` the reconcile,
  and `CM-45` the source-archive secret scan — the control that stops a credential
  reaching a tag, which had no row before. `CONTROLS.md` is at 45 rows, each bound
  by a test to a marker inside its cited range and to a test that loads.
- **Three record-keeping notes are recorded rather than left implicit.** The
  previous plan's line citations had gone stale (CT-32), `explorer_get`'s
  truncated-body contract is now documented at the function (CT-34), and the
  previous release window's five failed candidate attempts are named in
  `RELEASE-HISTORY.md` and `CURRENT-STATUS.md` (CT-35).

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The release
carries one checksum file covering macOS, Windows and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance policy, and
`releases/platform-state.json` for the platform posture this release was built
under.

# Bitcoin Easy Signer 0.7.4

This release answers the Color Team cycle-10 audit of the `v0.7.3` tree, which
graded **⚠️ CONDITIONAL**. The v0.7.2 block was discharged **by execution** — the
referee personally re-broke CT-27's marker arm and its clear, CT-29's reconcile and
CT-33's transport tuple, and watched each named pin go red; CT-32, CT-34 and CT-35
were closed by written dated owner acceptance; and all twenty-six earlier findings
were carried with no regression. The grade holds on two new findings in the delta.

**CT-36 (Medium)** is the one that matters. `broadcast_transaction` treated every
HTTP 4xx as a *definite refusal*: the payment had not been sent, so the wallet
stayed retryable and the in-flight marker was cleared. But a 4xx arrives **after**
the server has the complete signed transaction — an honest Esplora answers exactly
that way when it already holds the payment — so a second, differently reviewed
payment of the same wallet could leave with the pause the previous cycle added
never armed. One examiner demonstrated that end to end and the referee
re-executed it. **Nothing the operator had not reviewed was ever signed**; this is
a classification defect in what the app told itself about a reply, not a
substitution or a forged payment.

**CT-41 (Low)** is the missing alarm behind the early in-flight half of the same
gate: deleting that half left every named pin green, because the request simply
fell through to the in-lock half and was refused there. The protection worked; the
test that was supposed to hold it could not fail.

This release closes CT-36, CT-37 (the same defect in its raw-exception form),
CT-41, CT-43 (the previous window's history under-counted its runs) and the two
inventory gaps CT-39 and CT-40. Each is in `releases/PATCH-0.7.4.md` row by row,
with its closing test and its break-and-watch result, and every control the cycle
touches was broken on a disposable copy and watched red before being restored
(`releases/BREAK-AND-WATCH-0.7.4.md`).

**This release changes app behaviour in one direction: a payment whose outcome the
app cannot prove is now treated as unknown, not as refused.** It does not change
how an honest payment is prepared, signed, checked or broadcast, or which networks
are offered, or the fee ceilings. The engine's wire behaviour is unchanged — only
its classification of an answer.

## What changed

- **A status code is not proof that nothing was sent.** Only the checks that run
  before the request is written — unsupported network, missing mainnet opt-in,
  unusable size, invalid hex, a settings refusal — raise `BroadcastNotSent`, and
  those keep the reviewed payment retryable because the app can prove it never
  left. Everything after the bytes are handed over, 4xx included, raises
  `BroadcastOutcomeUnknown`, carries the server's own words as evidence, records
  the payment against the wallet and pauses it with one sentence: "The broadcast
  result is unknown: the server answered HTTP 400 after receiving this payment, so
  it may already have been accepted. Do not send this payment again. Check the
  transaction on an explorer or ask for help before proceeding." Rows `CM-49` and
  `CM-50`.
- **Anything else that escapes the submit is treated the same way.** A raw failure
  from the submit path — a `RuntimeError`, a bug, an uncatalogued exception — is
  converted to the unknown outcome under the same lock, because it proves nothing
  about whether bytes were written. The fail-safe direction is the pause. Row
  `CM-46`.
- **The early in-flight half now has its own alarm.** The test arms the marker
  before the request and asserts the refusal, the message, that the broadcaster was
  never called, and that no explorer was asked about the wallet's outputs. Row
  `CM-38`.
- **The previous window is disclosed as it happened.** The v0.7.3 row in
  `RELEASE-HISTORY.md` now names all five dispatched runs and nine attempts — the
  cancelled dispatch, the candidate built without notarization that the promote's
  manifest check refused, the two failed attempts inside the macOS job — with the
  plain statement that nothing was published from any failure. A new pin reads that
  row and fails if any run id or either count goes missing.
- **Two protections that had no row now have one.** The final-versus-review
  comparison (`CM-47`) and the `preparation_id` binding on the money endpoints
  (`CM-48`) were real — the panel broke both and watched them refuse — and
  `CONTROLS.md` is now at 50 rows, each bound by a test to a marker inside its
  cited range.
- **Three notes are recorded, not fixed.** The previous plan's stale test
  citation (CT-38), the lying-txid residual that keeps a wallet paused (CT-42) and
  the legacy-tag inventory (CT-44), each with where this cycle records it.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The release
carries one checksum file covering macOS, Windows and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance policy, and
`releases/platform-state.json` for the platform posture this release was built
under.

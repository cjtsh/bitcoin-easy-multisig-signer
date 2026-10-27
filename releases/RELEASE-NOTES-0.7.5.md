# Bitcoin Easy Signer 0.7.5

This release answers the Color Team cycle-11 audit of the `v0.7.4` tree, which
graded **⚠️ CONDITIONAL** with everything else in the cycle at CLEARED level. The
`v0.7.3` findings are **converted by execution**: the referee personally re-broke
the 4xx→unknown branch and the unknown-conversion branch, watched each named pin go
red, restored the copy byte-for-byte and watched it go green. All forty-four
earlier findings were carried with no regression.

**The grade is held by two missing alarm tests, not by a defect.** CT-47 is the
settings-refusal branch of the not-sent boundary: when the configured Esplora URL
is not a plain URL the app refuses to send, and because that happens before the
request is written the reviewed payment stays retryable — the right behaviour, but
no test could fail if the branch regressed. CT-49 is the same control's claim about
*position*: the existing pin checked which exception each input shape raises, not
that no request object had been built, so moving a refusal below the point of no
return would have kept the suite green.

**Nothing the operator had not reviewed was ever signed or sent in any version of
this software.** This release changes no transaction construction, signing, fee or
network rule, and no button does anything new. Three of its five scheduled items are
tests; the other two are a type guard at the engine's own entry point and one
`raise` that keeps a Ctrl-C distinguishable from a lost reply.

This release closes CT-45, CT-46, CT-47, CT-49 and CT-51, records the three notes
the audit called housekeeping (CT-48, CT-50, CT-52) and restates the two carried
ones (CT-38, CT-44). Each is in `releases/PATCH-0.7.5.md` row by row, with its
closing test and its break-and-watch result, and every control the cycle touches was
broken on a disposable copy and watched red before being restored
(`releases/BREAK-AND-WATCH-0.7.5.md`).

## What changed

- **The settings refusal now has an alarm.** A settings-rejected Esplora URL is a
  provable non-send: the app refuses before writing anything and the reviewed
  payment stays retryable. The new test drives three rejected URL shapes through the
  engine and asserts the refusal class and that no request was opened. Row `CM-50`.
- **The not-sent boundary's position is pinned.** A second test patches the request
  constructor and the opener, drives five pre-POST refusals, and asserts neither was
  ever called — so the claim "the refusal happens before the point of no return" is
  now a test rather than a comment. Row `CM-50`.
- **The engine refuses non-contract argument types.** A non-string chain or hex
  passed directly to the engine used to escape as a raw `TypeError` or
  `AttributeError`; both are now the not-sent refusal, because nothing can have been
  written at that point. The app's own call sites are unchanged. Row `CM-50`.
- **A deliberate abort stays a deliberate abort.** If the submit is interrupted
  (Ctrl-C, interpreter shutdown) the wallet is still paused and the payment still
  recorded — bytes may have left — but the `KeyboardInterrupt` is re-raised
  unchanged instead of being reported as an unknown broadcast outcome. Row `CM-46`.
- **The newest release window's history is pinned.** The automatic record test now
  reads the newest row of `RELEASE-HISTORY.md` and requires every run id and the
  counts in it, the same way the 0.7.3 row is held, so a window cannot under-count
  itself silently again. Tests in `tests/test_hardening_pins.py`.

## Verification

The suite is 744 tests, green in the checkout and in the extracted source archive;
all eleven page-script suites pass; `CONTROLS.md` is 50 rows with every row bound to
a marker inside its own range and to a test the build loads. Every claim above was
broken on a disposable copy, watched red, restored byte-for-byte and watched green.

## What this release does not claim

It does not claim the settings branch or the boundary's position could fail in
production at 0.7.4 — they could not, and the referee executed both. It claims the
suite would have stayed green if they had, which is the clause the audit's grade
binds on, and that is now false. It does not weaken the release gate: the Apple
notarization staple is still required, and a failure still publishes nothing.

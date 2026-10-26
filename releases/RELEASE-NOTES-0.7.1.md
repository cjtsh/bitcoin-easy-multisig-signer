# Bitcoin Easy Signer 0.7.1

This release answers the Color Team cycle-7 audit of the `v0.7.0` tree. That
cycle re-checked the previous grade: the panel verified all eighteen earlier
findings fixed **by execution** — the referee re-broke each fix and watched its
new test go red — and held the grade at **CONDITIONAL** on two new
Informational findings, both of them in the same pin-accuracy family: a claimed
control whose shipped test could not fail. It also recorded one further
Informational observation, about the connection ceiling's availability trade,
which the owner accepted and asked to have described accurately.

The wallet, transaction, signing and broadcast engine is unchanged: no capability
is added and no refusal message moves. This release also folds in the owner's
terms of use, which are documentation, not behaviour. Each finding this cycle
closed is recorded row by row, with its closing test and its break-and-watch
result, in `releases/PATCH-0.7.1.md`.

## What changed

- **The loopback server's retired-connection guard now has a test that can fail.**
  When a connection is retired by the fair-admission rule, the server closes it
  without answering, so the operator's console sees no broken-pipe traceback. That
  guard had no test, so it could have been deleted without anything going red. The
  new test drives a retired connection with a malformed request: with the guard in
  place the client receives no bytes at all, and without it the server would have
  answered with an HTTP 400. The same request on a live connection still gets its
  400, which is the half of the behaviour that must not change.
- **The control inventory now reads the GitHub workflow files.** `CONTROLS.md`
  parses the code that ships, and it did not parse `.github/workflows/`, so three
  claimed guards in the release workflow were invisible to it: the retired-publisher
  pagination guard, the notarisation credential guard, and the checksum-signing
  guard. The workflow is now in scope, each of those guards is a tracked row
  (`CM-33`…`CM-35`) with a marker inside the range it cites, and the two
  credential guards each have an executable pin that runs the workflow step and
  refuses the exact way the workflow refuses.
- **The busy-slot docstring now says what the slot actually requires.** The
  comment claimed that a busy connection needs the page's access token; the slot
  is actually held from the moment a complete request head has arrived, token or
  not. The comment now matches the code, and the corrected sentence is pinned by
  two tests — one asserting that a tokenless complete head claims the slot (and
  is then refused by the route), one asserting that a half-sent head claims
  nothing — so the description cannot drift away from the code again.
- **The terms of use are updated.** `DISCLAIMER.md` is now the project's copy of
  the Bitseeker LLC Standard Software Disclaimer & Limitation of Liability
  published at [cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer),
  with the Bitcoin Easy Signer specifics folded in: the warranty disclaimer, the
  limitation of liability, the limited indemnity, the Wyoming governing law and
  forum provisions, the assumption of risk, and the statement that this notice is
  general information and not legal advice. The README, the user manual, the
  download page and the app's About box link to it.

  A notice alone may not establish contractual assent. The app presents no
  acceptance gate, because adding one would change the software; whoever
  distributes, hosts or deploys it is responsible for obtaining whatever assent
  their distribution and jurisdiction require.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The release
carries one checksum file covering macOS, Windows and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance policy, and
`releases/platform-state.json` for the platform posture this release was built
under.

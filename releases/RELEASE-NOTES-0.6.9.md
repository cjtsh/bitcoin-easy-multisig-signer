# Bitcoin Easy Signer 0.6.9

This release answers the Color Team cycle-5 audit of the `v0.6.8` tree. That
cycle held everything the rubric asks a release to hold — the money path, the
devices, the pipeline, and the published bytes — and graded **CONDITIONAL** on
four Low findings. Each one described a control that was *believed* rather than
*pinned*: a branch no test could fail, three first-line guards tested only
through the deeper guard behind them, a download page that was corrected after
the tag instead of before it, and — most importantly — the inventory that is
supposed to catch exactly that class, which could not detect a citation moving
off its subject.

The wallet, transaction, signing, and broadcast engine is unchanged: no
capability is added, and no refusal message moves. Each finding this cycle
closed is recorded row by row, with its closing test, in
`releases/PATCH-0.6.9.md`.

## What changed

- `CONTROLS.md` citations are now content bindings, not line numbers that
  happen to exist. Every one of the 26 rows carries its own `CONTROL: CM-##`
  marker inside the range it cites, and the build fails if a row's marker is
  not inside its own range. Moving a citation onto an unrelated part of the
  file — the referee's own trick against the `v0.6.8` tree — now fails.
- The malformed-broadcast-body branch in `wallet_service.py` is pinned in
  both directions: a response that is not a 64-hex transaction id raises
  `BroadcastOutcomeUnknown`, and an upper-case id is accepted and lower-cased.
- The three first-line money-path guards are pinned by name and message, so
  each refusal keeps the sentence the operator reads, and each is separately
  break-and-watchable.
- `docs/index.html` derives its release version from the same single source as
  the app, under a test that refuses any download link, version label,
  JSON-LD version or finding-record link naming another version — with one
  download link required per platform.
- The local access token no longer survives in the browser's session history:
  the fragment is read once, kept in per-tab storage, and replaced out of the
  address bar. A new page-script suite runs under `node` and is executed by
  the Python suite, so the page scripts are evidence the ledger can cite.
- A startup failure is logged as one bounded line instead of a traceback, so
  the failure record no longer carries the operator's own paths.
- The two market reads (`/api/price`, `/api/fees`) require the local token,
  like every other endpoint.
- Concurrent connections are bounded; when the ceiling is reached the socket
  is closed rather than queued.
- GitHub immutable releases are enabled and recorded, so a change to that
  setting is a visible diff rather than a browser fact.
- A re-enabled retired publisher now refuses the run on both the candidate and
  the publish path, and a registration read that did not happen also refuses.
- `vendor/libusb-1.0.dll` was re-matched against the pin it ships under by
  re-running the producing workflow.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The
release carries one checksum file covering macOS, Windows, and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance
policy, and `releases/platform-state.json` for the platform posture this
release was built under.

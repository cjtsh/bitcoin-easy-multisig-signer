# Bitcoin Easy Signer 0.6.7

This release fixes the repository's release process after the Color Team
audit of v0.6.6 graded it BLOCKED. The audit cleared the app itself. No
wallet, signing, or broadcast policy changed, and no new payment capability
is added.

## What changed

- There is now exactly one way to publish this project. The old
  per-platform Windows and Linux publish workflows, which were never
  deleted and were still able to publish unsigned files, are gone from
  every branch. A guard check refuses to start a release if one reappears.
- A hardware helper is identified by the bytes it is made of, not by the
  version number it reports about itself. A planted program that simply
  printed the expected version is refused. The identity is re-checked at
  every signing session.
- Release builds run on one exact Python patch level instead of "whatever
  version each build machine happened to have", so the macOS, Windows,
  Linux, and source builds are built by the same interpreter.
- The tool that writes the dependency locks is itself hash-locked, and the
  Linux build no longer upgrades its own installer before installing a
  locked set of packages.
- The source download now contains every file needed to rebuild the signed
  Mac app from itself.
- The app verifies that its broadcast server is actually on the network it
  says it is, on every network, before anything is submitted.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The
release carries one checksum file covering macOS, Windows, and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance
policy.

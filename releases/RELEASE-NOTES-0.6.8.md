# Bitcoin Easy Signer 0.6.8

This release answers the Color Team cycle-4 audit of the `v0.6.7` tree. The
cycle's grade was set on the build process again: what the release
workflows install, and what they leave unchecked. The wallet, transaction,
signing, and broadcast engine is unchanged, and no new payment capability
is added. Each finding this cycle closed is recorded row by row, with its
closing test, in `releases/PATCH-0.6.8.md`.

## What changed

- The audit ledger is a checked record instead of a convention. Every
  finding the cycle's plan schedules must have exactly one row in
  `releases/PATCH-0.6.8.md` with a severity, a fix, and a closing test the
  build actually loads; a row may close without a test only for a deferral
  the plan itself makes. The rows that had been closed by silence are
  restored.
- `CONTROLS.md` is the checked inventory of the security controls the app
  relies on: the claim in plain English, the line that makes it, and the
  test that would go red without it. A cited file, line or test that stops
  existing, a `CONTROL: CM-##` marker with no row, or a comment that claims
  a control and names no entry now fails the build.
- The release process documents how to verify a release asset's
  attestation. The API is indexed by `sha256:` digest rather than by tag,
  and the note records the two misleading `404` shapes a reader can hit.
- The launcher installs the device library from a checked lock file, so the
  dependency set the source build runs is the one the repository pins.
- The source archive ships `CONTROLS.md`, and the check that reads the
  archive's file list covers it.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The
release carries one checksum file covering macOS, Windows, and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance
policy.

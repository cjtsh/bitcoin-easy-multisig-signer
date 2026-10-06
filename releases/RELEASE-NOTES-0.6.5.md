## What is new in 0.6.5

This is the first release that carries **macOS, Windows and Linux on one page,
built from one commit in one gated pipeline run**. It follows an independent
Color Team security audit of v0.6.4, whose full report is in this repository
(`bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.4.md`). The audit
found no way to move a user's Bitcoin wrongly in the macOS app; its grade was
set by release-channel findings, which this release fixes structurally:

- **One pipeline, one page.** macOS, Windows x64 and Linux x86_64 are now built
  from the same commit in the same dispatch-only workflow run and published as
  one release. The per-platform workflows that once let unverified bytes reach
  the v0.6.4 page are retired; the unified pipeline is the only publish path.
- **Verifiable downloads everywhere.** `SHA256SUMS` is generated inside CI and
  covers every asset; it is signed by the project's release GPG key
  (`SHA256SUMS.asc`, public key in `signing-key.asc`); every asset carries a
  GitHub Sigstore build attestation binding it to this commit and run. The
  macOS DMG keeps its Developer ID signature and Apple notarization; the
  Windows and Linux builds are unsigned by policy — see `SIGNING.md` for what
  that means and how to verify them.
- **Audit findings fixed:** the source-mode launcher's substituted-library
  guard now checks the pinned embit version (it previously validated a version
  the lock no longer used); the final-review backstop, the preparation binding,
  the prevout-ownership refusals and six smaller controls are now pinned by
  tests that fail if they are ever weakened; diagnostic reports accept only a
  fixed vocabulary of hardware-device classes.

The wallet, transaction, signing and broadcast engine is unchanged from the
audited 0.6.4. One confirmation still names real Bitcoin before any mainnet
send, and the app never asks for a seed or PIN.

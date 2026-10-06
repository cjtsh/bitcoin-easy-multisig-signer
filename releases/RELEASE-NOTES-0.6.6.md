# Bitcoin Easy Signer 0.6.6

This release hardens the signing and release path after the Color Team
audit of 0.6.5. It adds no new payment capability.

## What changed

- A hardware device must now prove it holds the wallet key before it
  receives a payment. One extra on-device confirmation may appear while
  signing.
- The large-amount mainnet prompt also fires at 0.04 BTC, so a lying price
  feed cannot hide a large payment. Amounts from 0.04 to 0.1 BTC may ask
  for that confirmation when they previously did not.
- The app no longer freezes during a slow explorer check before broadcast.
- Saved transactions that already carry signatures are named `-signed`
  rather than `-unsigned`.
- Source mode refuses a hardware helper that does not identify as the
  pinned HWI 3.2.0.
- Published BIP-143 test vectors guard the signature digest.
- Release builds pin their runner images and lock tooling.

## Downloads

Verify every download against `SHA256SUMS` and its `SHA256SUMS.asc`. The
release carries one checksum file covering macOS, Windows, and Linux, plus
`BUILD-SBOM.json`. See `SIGNING.md` for the signature and provenance
policy.

# v0.5.0 candidate — LIVE BTC transactions

## Change

Enable mainnet transaction broadcast in the first full-Bitcoin-on-LiveNet
candidate. The operator must review the exact finalized transaction and click the
final confirmation before broadcast. The mainnet endpoint additionally requires a
mainnet-specific opt-in field, and the transport helper rejects mainnet unless
that opt-in is present. The build and test process does not broadcast a
transaction.

The existing fee policy remains: 1–25 sat/vB and a 10,000-sat estimated-fee
ceiling. A live standard quote above 25 sat/vB blocks preparation. The app has no
in-app fee-bump workflow; transactions signal RBF, and a compatible external
wallet may be able to replace a stuck transaction. Mainnet outpoint rechecking,
network binding, immutable prepared-payment checks, final-output verification,
session locking and unknown-outcome no-retry handling remain in place.

## Verification

- Python 3.12 full suite: 238 tests passed.
- Extracted 0.5.0 source archive full suite: 238 tests passed; all `ui_*.cjs`
  regressions passed.
- UI stale-state regression: passed.
- `bash -n` checks on build scripts and `git diff --check`: passed.
- Focused tests cover mainnet transport refusal without opt-in, helper dispatch
  with opt-in, and API-route refusal without the final mainnet confirmation.
- The packaged app passed bundle-resource, temporary PSBT-save, and live HTTPS
  checks for Testnet4 and Mutinynet. Its HWI helper loaded libusb and queried USB
  descriptors during packaging; this does not claim a physical OneKey test in
  0.5.0.
- Apple Silicon Developer ID app signing and Apple notarization were accepted;
  the app and DMG were stapled and validated. Gatekeeper accepted the app mounted
  from the DMG. `hdiutil verify` reported a valid image.
- Local test DMG: `/Users/christerry/Downloads/Bitcoin-Easy-Signer-v0.5.0-macOS.dmg`.
  SHA-256: `c1831dde2042c8bebae14d6c545531dcb609a1f2fcedb71a433626bca5f8e056`.
- Matching source archive: `dist/bitcoin-easy-multisig-signer-v0.5.0.tar.gz`.
  SHA-256: `3a65fe936023dcd5b44735648ccec1afc69d73dcdc1f21935960efdb7d5d854f`.

## Owner walkthrough and limits

The owner reports a successful, unbroadcast 0.4.15 mainnet dry run using OneKey
Classic 1S and another signer; the signed transaction was cleared. That is not a
live-broadcast test. Candidate 0.5.0 is intended for the owner's first mainnet
transaction walkthrough. No on-chain transaction was sent by this build process,
and no 0.5.0 live send or confirmation is claimed here.

This candidate is not published. A physical owner walkthrough, independent
explorer verification, confirmation, and an independent full-tool review remain
open release evidence.

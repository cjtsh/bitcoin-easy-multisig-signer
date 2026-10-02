# 0.4.14 — BSMS quorum with up to three physical keys

## Scope

Accept existing native-SegWit multisig BSMS wallets with two or three cosigner
keys. The wallet file defines the quorum, and any valid threshold for those key
counts is followed through transaction planning and signing. Wallet creation,
seed entry and software signing remain outside the product. Wallets with more
than three keys are refused.

The main screen states: “Supports hardware multisig wallets with up to three
physical keys.”

Change safety is unchanged: infer standard BIP48 change only for the anchored
sorted 2-of-3 case. Other partial sends require a declared change path. If the
change path is unavailable, the operator can deliberately choose Send All, which
has no change output.

## Verification

- Python unit/integration suite: 233 tests passed locally.
- All `tests/ui_*.cjs` DOM tests passed locally.
- `bash -n` checks, Python compile check, and `git diff --check` passed.
- The local Apple Silicon release build used the Developer ID certificate,
  completed Apple notarization, stapled the app and DMG, and passed the packaged
  Gatekeeper and staple checks. The final DMG is in Downloads.
- The owner reported that the local installation worked. No physical transaction
  using the newly supported quorum shapes has been reported; automated fixtures
  are not hardware acceptance evidence.
- GitHub Actions run `36794617048` passed: source tests and archived-source tests,
  UI tests, signed Apple Silicon build, packaged-app checks, notarization,
  checksums, SBOM, and immutable release publication. It signed with the configured
  Developer ID certificate and submitted the build to Apple. Published assets are
  the notarized DMG, source archive, `BUILD-SBOM.json`, and `SHA256SUMS`.

Mainnet broadcast remains disabled. No wallet material, transaction data, or
private device identifiers are included in this record.

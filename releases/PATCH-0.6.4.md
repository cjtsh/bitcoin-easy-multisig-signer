# v0.6.4 — automated release-path proof and audit regression coverage

**Published 2026-10-02** as [`v0.6.4`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.4).
This release changes no wallet, transaction, signing, finalization, or broadcast
behavior. It updates the displayed/diagnostic version, adds regression tests and
SBOM provenance, and changes how a verified candidate is promoted through the
GitHub release workflow.

## Changes

- T3 / BESA-27: added API-level refusal tests for a missing device binding, a
  stale-review binding, and a failed signing-time device identity check. Each
  confirms no signature or broadcast is produced.
- T4 / BESA-28: added an API-level test for an explorer returning a txid
  different from the reviewed txid. The payment is marked outcome-unknown,
  cleared from prepared state, and cannot be retried blindly.
- T5 / BESA-31: the CycloneDX SBOM records the exact SHA-256 of the vendored
  embit wheel and identifies its PyPI purl as symbolic because the patched
  wheel is local.
- The publish workflow is restricted to main and requires a successful
  notarized candidate run from the same commit. It verifies the run provenance
  and candidate SHA256SUMS, then publishes the exact candidate bytes. The
  publishing run independently verifies downloaded release bytes, checks the
  remote tag, and enforces unsigned-build refusal.
- The source archive now uses its explicit root-document allowlist for its
  completeness check. Ignored owner-local Markdown files cannot break the
  build or enter a public source archive.
- RELEASE-PROCESS.md documents the candidate → owner acceptance when app
  behavior changes → workflow publication sequence for all future builds.
- Local builds remain available for quick development iterations. Every public
  release must use the GitHub workflow; manual publication is prohibited. If
  that workflow is unavailable, publication waits.
- Documentation records that the local embit sequence correction is not yet
  upstream and must be reviewed on every embit upgrade; the app does not import
  Liquid/PSET code and round-trips recipient addresses against the selected
  network.
- README test instructions now install the CI tools from their hash-locked file.

## Verification evidence

- Final source commit: `35cdedb150cef6d047c39537324faf1321be3c8d`.
- Signed and notarized nonpublishing candidate run: [37008418851](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37008418851), with `publish=false`.
- Automated publishing run: [37009396873](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/37009396873), with `publish=true`, `notarize=true`, and candidate run `37008418851`.
- The publishing workflow verified the candidate run and manifest on the same commit, downloaded and checksum-verified the candidate bytes, passed package/signature/notarization and release-byte checks, confirmed the version tag was unused, and created the public release. Tag `v0.6.4` points to the final source commit; the release is neither a draft nor a prerelease.
- The public DMG, source archive, and SBOM were downloaded and checked against `SHA256SUMS`. Their SHA-256 values are respectively:
  - DMG: `5c7f1481be301a5cb6ca02533e24308eddc97608457d6ce721e2b28fad5336a8`
  - Source archive: `8a23ea80b8fddb02bfe85ad83ce499a30ec752dfaa9a1f014f3e7089d23cff8c`
  - `BUILD-SBOM.json`: `400068e9fbb9ffce6870351f2ea903b6840051e629c3adecac94e15f290382c5`
- Two earlier publication attempts stopped before creating a tag or release: run `37006075418` exposed an incorrect workflow-run provenance path, and run `37007620401` exposed a missing repository context for artifact download. Both defects were fixed in separate reviewed commits; both attempts failed closed without publishing artifacts. The final candidate and publication runs above succeeded after those fixes.
- A documentation-only commit after publication records this evidence. The source archive and release tag remain immutable snapshots from the release commit; the post-publication record on `main` explains the difference.
- Independent follow-up audit of v0.6.4 is pending. The v0.6.3 audit grade
  remains Yellow until its reviewer records a new grade.

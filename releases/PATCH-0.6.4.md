# v0.6.4 — automated release-path proof and audit regression coverage

**Preparation in progress.** The latest published release remains v0.6.3.
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
- Documentation records that the local embit sequence correction is not yet
  upstream and must be reviewed on every embit upgrade; the app does not import
  Liquid/PSET code and round-trips recipient addresses against the selected
  network.
- README test instructions now install the CI tools from their hash-locked file.

## Verification evidence

- Candidate source commit: pending.
- Signed, notarized nonpublishing candidate run: pending.
- Automated publishing run: pending. It must use publish=true,
  notarize=true, and the successful candidate_run_id for the same commit.
- Published tag must target the candidate commit. Public release bytes must
  pass the publishing run's downloaded-file SHA256SUMS check.
- Independent follow-up audit of v0.6.4 is pending. The v0.6.3 audit grade
  remains Yellow until its reviewer records a conversion.

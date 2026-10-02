# Release process for every Bitcoin Easy Signer build

This is a project rule for any human or coding agent working on a Mac DMG,
regardless of which AI tool they use. `AGENTS.md` defines the product safety
boundaries; this file defines the repeatable build and release gates. The Apple
Developer instructions outside this repository explain credentials and Apple's
tools, but do not replace these project gates.

## 1. Prepare a new candidate

1. Read `AGENTS.md`, `CURRENT-STATUS.md`, `HWI-DEPENDENCY.md`, and the latest
   `releases/PATCH-*.md` record. Use a new patch version after a published
   release; never alter an existing release's assets.
2. Use the checked-in `scripts/build-macos.sh` or the manually dispatched
   `.github/workflows/build-candidate.yml`. Do not construct a DMG with an ad hoc
   PyInstaller command. Preserve the single BSMS workflow, exact payment review,
   signer verification, network gates, and mainnet consent rules.
3. Keep Python, HWI, embit, the hash locks, vendored libusb, and the expected
   libusb digest in sync. A changed dependency or native binary requires an
   explicit provenance review, regenerated locks where applicable, updated
   licenses and SBOM rules, full tests, and a fresh signed candidate. A package
   install or download must not run after Apple signing secrets are loaded.
4. Keep private audit work orders, wallet files, xpubs, addresses, PSBTs, raw
   transactions, device paths, credentials, and diagnostic files out of the
   repository, release notes, and build artifacts.

## 2. Verify before owner testing

1. Run the complete Python and `tests/ui_*.cjs` suites, JavaScript syntax and
   `bash -n` checks, and the source archive's own tests. A skip is a failure.
2. Dispatch the workflow with `notarize=true` and `publish=false`. A source
   push alone never publishes. The workflow must verify the vendored libusb
   digest, install dependencies with hashes before loading credentials, sign
   and notarize the app and DMG, validate staples and Gatekeeper, run packaged
   app and HWI checks, produce the shipped-component SBOM, and verify all
   downloaded files against `SHA256SUMS`.
3. Inspect the exact candidate DMG and its checksums. Give the owner one clear
   install and hardware-test request for the milestone. Automated tests do not
   count as a physical payment. Never make a mainnet payment during build or
   testing.

## 3. Publish only after acceptance

The owner reports whether the candidate passed the required practice-network
hardware payment. Record the outcome in the version's release evidence without
transaction IDs or wallet material. Publish only after acceptance, using the
**same verified DMG bytes** the owner tested, along with the matching source
archive, `BUILD-SBOM.json`, and `SHA256SUMS`. Check that the remote version tag
does not exist before creating it. Do not rerun a build and silently substitute
a new DMG under the tested version. If anything affecting the artifact changes,
make and test a new candidate first.

The current candidate, publication status, and remaining gates belong in
`CURRENT-STATUS.md`, `PHASE-HANDOFF.md`, `RELEASE-HISTORY.md`, and the versioned
record under `releases/`. Keep historical audit and release records intact.

# v0.6.3 — audit remediation candidate

**Candidate in progress; not published.** The latest published app is v0.6.2.
This record tracks changes made after the public Z.ai audit of v0.6.2. The audit
is a dated review of that release, not a certification of this candidate. Do not
turn this record into a release claim until the gates below have evidence.

## Changes

- **BESA-01, BESA-04:** Hash-pin the PyYAML CI tool. Complete dependency installs,
  native-library acquisition, and tests before importing the Developer ID
  certificate or setting up notary credentials. Keep the temporary keychain
  password within its step.
- **BESA-03:** Vendor the verified libusb binary so the final build runs no
  Homebrew formula code. Preserve the mandatory input digest check. Final
  nonpublishing workflow verification remains open.
- **BESA-05:** Verify downloaded release files against `SHA256SUMS` and check the
  remote tag before any publication.
- **BESA-06, BESA-18:** Build the SBOM from the PyInstaller inventory, include the
  CPython runtime, and record hashes of both shipped, re-signed libusb copies as
  well as the verified input digest.
- **BESA-07, BESA-11, BESA-12:** Bundle libusb under both names the USB loader
  expects; resolve its absolute bundled path in frozen HWI and fail closed if
  either bundled file is absent. The self-check reports the loaded path.
- **BESA-08:** Bind signing requests to devices successfully probed for the
  current wallet, chain, and payment review, then repeat the account-level public
  xpub comparison on the chosen device immediately before `signtx`.
- **BESA-02, BESA-09, BESA-10, BESA-13–17:** Vendor the reviewed upstream embit
  source after its v0.8.2 tag, with an explicit local parser fix and corrected
  package version. Pin the resulting pure-Python wheel by hash in both lock
  files. The app still performs its own verify-then-finalize process. Regression
  tests cover PSBT global transaction bytes and truncated parsing.
- **BESA-19:** Turn malformed explorer previous-transaction parser failures into
  the intended fail-closed wallet error.
- **BESA-21:** Explain in the release history why an in-tag source archive can
  retain its prepublication status stamp.
- Document the frozen HWI USB loader and vanished-device handling in
  `HWI-DEPENDENCY.md`, plus the lack of automatic updates in the user guidance.
- Update maintainer, safety, and privacy wording; package the safety and privacy
  notices with the next Mac app.

## Evidence to complete before publication

1. Full Python suite, UI DOM suite, Bash syntax, source-archive tests, and
   packaged Apple Silicon self-checks pass from the final commit.
2. Nonpublishing, signed and notarized workflow candidate succeeds. Record the
   commit, run, artifact hashes, staple validation, and final SBOM results here.
3. Review license and source availability for the exact bundled dependency set.
4. Owner installs the final candidate and completes one physical Mutinynet
   payment with the intended hardware devices. Record the outcome without wallet
   identifiers, transaction bytes, device paths, or other private material.
5. Only after that acceptance, publish a new immutable `v0.6.3` tag and release
   with the candidate's DMG, source archive, SBOM, and `SHA256SUMS`.

No independent end-to-end review of v0.6.3 is claimed by these fixes or tests.

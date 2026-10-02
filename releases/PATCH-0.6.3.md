# v0.6.3 — audit remediation candidate

**Signed and notarized candidate built; not published.** The latest published app is v0.6.2.
This record tracks changes made after the public Z.ai audit of v0.6.2. The audit
is a dated review of that release, not a certification of this candidate. Do not
turn this record into a release claim until the gates below have evidence.

## Changes

- **BESA-01, BESA-04:** Hash-pin the PyYAML CI tool. Complete dependency installs,
  native-library acquisition, and tests before importing the Developer ID
  certificate or setting up notary credentials. Keep the temporary keychain
  password within its step.
- **BESA-03:** Vendor the verified libusb binary so the final build runs no
  Homebrew formula code. Preserve the mandatory input digest check. The
  nonpublishing signed workflow candidate passed.
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
- Add an agent-neutral `RELEASE-PROCESS.md` and link it from `AGENTS.md` and the
  local Apple instructions. Make manual dispatch nonpublishing by default and
  refuse any attempt to publish an unsigned build.

## Candidate evidence

- Built from app source commit `f19bc460a2cb64590e8e37268b5be1df1a1f84b0`
  by [nonpublishing workflow run 36969063265](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36969063265).
  All five jobs passed. `v0.6.3` has no public tag or release.
- The full local suite passed 253 Python tests. The workflow passed the Python
  suite, UI DOM tests, tests from its own source archive, signed Apple Silicon
  build, packaged app checks, SBOM generation, and downloaded-byte checksum
  verification.
- The downloaded candidate DMG has SHA-256
  `79326d6d407e8fa6fae4fad3504e300b6cce2207dabb312b79f1a49bed23513b`.
  The matching source archive is
  `9ae1d124419f5cb93da8f2302ea66ef0ebbf36036c0f56a051e1f72c38063821`;
  `BUILD-SBOM.json` is
  `610d904b47376a7e182734ac42d2756f41e3232f650f68e251991c3170cefa1c`.
  All match the run's `SHA256SUMS`.
- Independently mounting the downloaded DMG passed `hdiutil verify`, app and
  DMG staple validation, strict code-signature verification, and Gatekeeper
  assessment as `Notarized Developer ID` from Bitseeker LLC. Bundle, unsigned
  PSBT-save, and device-bridge self-checks passed with zero devices attached.
  Both embedded libusb digests match the shipped-component SBOM, and the bundled
  LGPL text matches the pinned upstream source archive.

## Gates to complete before publication

1. Review license and source availability for the exact bundled dependency set,
   beyond the libusb source/license check above.
2. Owner installs the final candidate and completes one physical Mutinynet
   payment with the intended hardware devices. Record the outcome without wallet
   identifiers, transaction bytes, device paths, or other private material.
3. Only after that acceptance, publish a new immutable `v0.6.3` tag and release
   with the candidate's DMG, source archive, SBOM, and `SHA256SUMS`.

No independent end-to-end review of v0.6.3 is claimed by these fixes or tests.

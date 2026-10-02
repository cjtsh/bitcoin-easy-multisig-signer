# Release process for every Bitcoin Easy Signer build

This is the required process for any human or coding agent preparing a Mac DMG,
regardless of which AI tool or machine they use. AGENTS.md defines product
safety boundaries; this file defines the repeatable build and publication gates.
The Apple Developer instructions outside this repository supply credential and
notarization details, but do not replace these gates.

## 1. Prepare the release commit

1. Read AGENTS.md, CURRENT-STATUS.md, HWI-DEPENDENCY.md, and the latest
   releases/PATCH-*.md record. Bump version.py after every published release;
   never alter a published tag or its assets.
2. Update RELEASE-HISTORY.md, the versioned patch record, current-status
   documents, and user-facing version references together. State whether wallet,
   signing, and broadcast behavior changed. Keep private audit work orders,
   wallet files, xpubs, addresses, PSBTs, raw transactions, device paths,
   credentials, and diagnostic files out of the repository and build artifacts.
   The source archive uses an explicit root-document allowlist; never replace it
   with a wildcard that could sweep ignored local files into a public archive.
3. Keep Python, HWI, embit, hash locks, vendored libusb, expected libusb digest,
   license notices, and SBOM rules in sync. A dependency or native-binary change
   requires provenance review, regenerated locks where applicable, license and
   SBOM updates, complete tests, and a new candidate. Do not change signing.py,
   safe_http.py, or another safety invariant without a scoped review and
   regression tests.
4. Build only with scripts/build-macos.sh or
   .github/workflows/build-candidate.yml. Never assemble a release DMG with an
   ad hoc PyInstaller command. Dependency installation and all other
   third-party code must finish before Apple signing secrets are loaded.
   Local builds are useful for quick development checks. They are not release
   artifacts: the release candidate must be produced by the GitHub workflow,
   and the owner tests that candidate when a hardware walkthrough is required.

## 2. Run the signed candidate

1. Before the build, confirm the working tree is clean, record the full commit
   SHA, confirm version.py matches the intended release, and confirm the
   corresponding remote tag does not already exist.
2. Run the full Python suite without skips, every tests/ui_*.cjs test,
   JavaScript syntax checks, bash -n, and the source archive's own tests.
3. Dispatch build-candidate.yml from main at the final release commit with
   notarize=true and publish=false. A source push alone never builds or
   publishes a release. The run must check the vendored libusb digest; install
   dependencies with hashes before importing credentials; sign and notarize
   the app and DMG; validate staples, signatures, and Gatekeeper; run packaged
   app and HWI checks; create the shipped-component SBOM; and verify candidate
   checksums. Record the successful candidate run ID.
4. Inspect the candidate DMG and its checksums. Request one owner practice-network
   hardware walkthrough when the release changes app behavior. Automated tests
   do not count as physical acceptance. The candidate workflow retains a
   manifest binding the signed artifacts to the run ID and commit. Never make
   a mainnet payment during build or testing.

## 3. Publish through the workflow

After the candidate checks and any required owner acceptance, dispatch the same
workflow from main at the same final source commit with notarize=true,
publish=true, and candidate_run_id set to the successful candidate run ID. This
second run is the publication event. It must itself pass all source, signing,
notarization, packaging, checksum, and release jobs. The workflow verifies that
the candidate run succeeded on the same commit, checks its notarization
manifest, downloads the candidate's signed artifacts, and verifies their
SHA256SUMS before publishing those exact tested bytes. It also checks that the
remote version tag does not exist and refuses an unsigned or unnotarized build
before creating a release. Record both run URLs and the full commit SHA in the
patch record.

Never use a manual gh release create, website upload, or tag push as the normal
publication route. Do not dispatch publish=true without the candidate run ID
from the same final commit on main. If a required gate fails, fix it in a new
commit, rerun the signed candidate on that commit, and publish only from that
commit.

After publication, independently check that the tag points to the commit named
by the publishing run; download every public asset; verify the published
SHA256SUMS; and check the release is neither a draft nor a prerelease. Do not
replace an existing tag or asset. Record the publication run and verification
in releases/PATCH-VERSION.md, then update current-status files in a
documentation-only commit. The source archive and tag are immutable snapshots;
the post-publication records on main must explain any documented differences.

Manual publication bypasses machine-enforced release gates. Do not use it as a
normal route. Any emergency decision to publish manually must be written and
dated by the owner before a tag or release is created, must name the skipped
gates and accepted residual risk, and must be preserved in the release record.
The v0.6.3 release used a manual route; v0.6.4 is intended to prove the
workflow's automated publication path.

## 4. Keep the record current

The latest candidate, published version, tested commit, build-run evidence, and
remaining owner or audit gates belong in CURRENT-STATUS.md,
PHASE-HANDOFF.md, RELEASE-HISTORY.md, and the versioned record under releases/.
Keep dated audit reports intact. Do not claim a newer audit grade until the
independent reviewer records it.

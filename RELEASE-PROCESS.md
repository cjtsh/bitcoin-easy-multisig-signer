# Release process for every Bitcoin Easy Signer build

This is the required process for any human or coding agent preparing a release —
macOS, Windows, or Linux — regardless of which AI tool or machine they use.
AGENTS.md defines product safety boundaries; this file defines the repeatable
build and publication gates; **SIGNING.md defines what each platform's download
carries (signature and provenance) and the release-key policy**. The Apple
Developer instructions outside this repository supply credential and
notarization details, but do not replace these gates.

One pipeline publishes everything: `.github/workflows/build-candidate.yml`
builds macOS, Windows x64 and Linux x86_64 from the same commit in the same
dispatch-only run and is the only publish path. The retired per-platform
workflows are deleted from every branch and must not return; a second publish
path is how unverified bytes once reached a tagged release.
`scripts/check-publish-paths.sh` runs as a gate on every dispatch and fails
closed if any non-main branch carries a publish-capable workflow. Historical
tags freeze their commit's workflow text, so the dispatch ref is always
`main` and never a tag.

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
4. Build only with the platform build script for local checks
   (scripts/build-macos.sh, scripts/build-windows.ps1, scripts/build-linux.sh)
   or .github/workflows/build-candidate.yml for anything that could ship.
   Never assemble a release artifact with an ad hoc PyInstaller command.
   Dependency installation and all other third-party code must finish before
   Apple signing secrets are loaded.
   Local builds are useful for quick development checks. They are not release
   artifacts: the release candidate must be produced by the GitHub workflow,
   and the owner tests that candidate when a hardware walkthrough is required.

## 2. Run the signed candidate

1. Before the build, confirm the working tree is clean, record the full commit
   SHA, confirm version.py matches the intended release, and confirm the
   corresponding remote tag does not already exist.
2. Run the full Python suite without skips, every tests/ui_*.cjs test,
   JavaScript syntax checks, bash -n, and the source archive's own tests.
   The suite must pass on **macOS, Linux and Windows** — the unified workflow
   runs it on each runner before that platform builds. Windows portability
   rules (bash via `tests/support.py`, LF scripts, `assert_private_file`,
   restore CWD before temp cleanup) are documented in `WINDOWS-PORT.md`;
   do not call `bash -c` with a multiline script from Python or assert POSIX
   `0600` directly on Windows.
3. Dispatch build-candidate.yml from main at the final release commit with
   notarize=true and publish=false. A source push alone never builds or
   publishes a release. The run must check the vendored libusb digests; install
   dependencies with hashes before importing credentials; sign and notarize
   the macOS app and DMG; validate staples, signatures, and Gatekeeper; build
   and self-check the Windows and Linux bundles; create the shipped-component
   SBOMs; and write one candidate SHA256SUMS covering every platform's assets.
   Note the successful candidate run ID for the publish dispatch in section 3,
   but write it into the patch record only after publication: a commit that
   lands on main between the candidate and the publish dispatch breaks the
   same-commit promotion contract.
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
manifest, downloads the candidate's signed artifacts for every platform, and
verifies their SHA256SUMS before signing that manifest with the release GPG key
(SHA256SUMS.asc — it fails closed without GPG_PRIVATE_KEY; see SIGNING.md) and
attaching a Sigstore build attestation to every asset. It also checks that the
remote version tag does not exist and refuses an unsigned or unnotarized macOS
build before creating one release that carries all three platforms. Record both
run URLs and the full commit SHA in the patch record.

Never use a manual gh release create, website upload, or tag push as the normal
publication route. Do not dispatch publish=true without the candidate run ID
from the same final commit on main. If a required gate fails, fix it in a new
commit, rerun the signed candidate on that commit, and publish only from that
commit.

After publication, independently check that the tag points to the commit named
by the publishing run; download every public asset for all three platforms;
verify the published SHA256SUMS; verify SHA256SUMS.asc against the committed
signing-key.asc; verify at least one asset's Sigstore attestation; and check
the release is neither a draft nor a prerelease. Do not replace an existing tag
or asset. Record the publication run and verification in releases/PATCH-VERSION.md,
then update current-status files in a documentation-only commit. The source
archive and tag are immutable snapshots; the post-publication records on main
must explain any documented differences.

Manual publication bypasses machine-enforced release gates and is prohibited.
If the workflow is unavailable, wait to publish; do not create a tag, GitHub
release, or substitute upload by hand. The v0.6.3 release used a manual route;
v0.6.4 demonstrates the required automated publication path.

## 4. Keep the record current

The latest candidate, published version, tested commit, build-run evidence, and
remaining owner or audit gates belong in CURRENT-STATUS.md,
PHASE-HANDOFF.md, RELEASE-HISTORY.md, and the versioned record under releases/.
Keep dated audit reports intact. Do not claim a newer audit grade until the
independent reviewer records it.

## 5. Audit tripwires and release-channel hygiene (learned the hard way)

Cycles 1 and 2 spent more effort re-proving the software than building it.
These rules exist so cycle N does not repeat that. They apply to every future
revision, including 0.7.0.

**A test that cannot fail does not count as a fix.** Every load-bearing
money-path or release-path control needs a tripwire demonstrated able to fail:
break the control on a disposable copy, watch the named test go red, restore.
Record that transcript beside the change. Cycle 3's referee will break-and-watch
every pin. The test must assert the *specific* refusal message the gate produces
(so a weaker backend fallback cannot make it pass) and must include the positive
half (the honest path still works).

**External oracles catch what shared code cannot.** Sign-then-verify tests that
call the same function twice stay green under a digest substitution. Pin
published test vectors (BIP-143 and friends) and recompute them without the
library under test. See `tests/test_bip143_vectors.py`.

**Release-channel hygiene is part of the release.** A GitHub release page is the
shop window. Same-named different-byte files and unsigned sums destroy operator
verification even when the bytes themselves are fine. Before the next audit
cycle: delete or clearly supersede any out-of-gate asset; never leave two files
with one name; keep exactly one `SHA256SUMS` covering every platform and its
`.asc`. A supersession banner must say which files were removed and where the
supported binaries now live.

**Pin what used to float.** Runner images must name a specific
(`ubuntu-24.04`, `windows-2022`, `macos-15`) — never a `-latest` alias.
Source-mode tool resolution must prove the helper's identity (the pinned HWI
release) before it sees an account xpub or PSBT. Actions stay pinned to full
commit SHAs. `tests/test_workflow_config.py` and
`tests/test_hardening_pins.py` hold these.

**Stale version strings are findings.** When `version.py` moves, update
`AGENTS.md`, release notes, user-facing references and the audit plan's target
revision together in the same commit. "Current published version is X" inside
tag X+1 is stale-by-construction and was filed as CT-46.

**The audit ledger is the backlog.** Work the appendix of the latest
color-team report as the fix list. Close each finding with a test demonstrated
able to fail, or with a written owner acceptance — never by silence.

**Release credentials are environment-scoped, never repository-level.** The
signing credentials live in the `release-signing` and `apple-signing`
environments, each deployable only from `main`, and each job that names a
credential declares its environment. A repository secret reaches a job on **any**
ref, so a dispatch at a historical tag would run that tag's frozen workflow text
with today's signing keys; all 58 tags from `v0.1.0` on carry a dispatchable
`build-candidate.yml` and the pre-0.6.4 ones lack the default-branch guard.
Tags are immutable, so the protection is a rule about which ref a run is on, and
it holds for tags that do not exist yet. Run
`scripts/check-release-credentials.sh` before every promotion and in every audit
cycle: it is read-only and refuses if a credential is repository-level, an
environment is missing or not `main`-only, its secret set changed, a job names a
credential without declaring an environment, or an environment declares a human
gate (a required reviewer or a wait timer). The set it watches is derived from
the `secrets.NAME` references in the workflow text, so a newly named credential
becomes watched the day it appears rather than when someone remembers to edit a
list; `--print-scope` shows the derived rows. Neither
environment pauses for a person, so any agent team the owner authorises can cut a
release. `tests/test_workflow_config.py` holds the repository half of the
control; `SIGNING.md` carries the recovery steps.

**A credential moves by re-deriving it, never by reading it back.**
`scripts/provision-release-credentials.sh` is the supported way to put a value in
its environment: it exports `GPG_PRIVATE_KEY` from the release key in the
maintainer's GnuPG keyring, exports `MAC_CERT_P12_BASE64` plus a fresh
`MAC_CERT_PASSWORD` from the `Developer ID Application: Bitseeker LLC
(B8G5L7M8TB)` identity in the login keychain, takes
`MAC_APP_SPECIFIC_PASSWORD` from a hidden prompt or a file, takes
`MAC_NOTARY_KEY_P8_BASE64` from `--notary-key-file` when the App Store Connect
API-key notary route is in use, and then deletes whatever repository-level copies
remain (`--prune`). It never prints a value and no value reaches GitHub through a
shell history, a log or a transcript; `gh secret set` receives it on standard
input and the two local-tool argv windows noted in `SIGNING.md` are the
exception. It finishes by running the check above. GitHub
cannot return a secret's value to anyone, so a lost environment secret is a
re-run of that script, not a new certificate.

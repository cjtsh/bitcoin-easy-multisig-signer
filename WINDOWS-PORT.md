# Windows port

This document explains the Windows build, why it lives here, and what has to be
reviewed before the first one can be published.

## Why this is a separate project

The macOS app in `besa-audit` is frozen at v0.6.4 (`35cdedb`) and covered by the
Z.ai audits checked into that repository. A Windows port has to change source
files, so it cannot land there without decoupling "what was audited" from "what is
shipped". This directory is a clone of that repository with the port applied, so
the audited revision keeps meaning exactly what it meant before.

Two things follow from that and are easy to get wrong:

* This is not a branch of the audited tree, and the audit does not cover it. A
  Windows release is a new artifact under the project's own release discipline, not
  a rebuild of an audited one.
* The website (`bitcoineasysigner.com`) is served from the frozen repository's
  `docs/` directory, so it cannot link a Windows download until that freeze is
  lifted. Windows builds live on the GitHub Releases page.

`docs/` was deleted here rather than kept, because a second copy of the site would
either collide with the first or drift from it.

## What changed

Porting surface, in the order it matters:

| Area | Change |
| --- | --- |
| `desktop.py` | Runs on Windows too: the platform guard accepts `win32`, and pywebview is pinned to the `edgechromium` renderer so a missing WebView2 fails loudly instead of silently degrading to legacy MSHTML. |
| `gui.py` | New `assert_private_file()`: Windows `chmod` only toggles the read-only attribute and `st_mode` always reports `0666`, so "is this file private?" is answered by the OS access list (the file must live under the user's own profile) instead of POSIX mode bits. |
| `probe.py` | The frozen HWI helper is looked up as `hwi.exe` on Windows. |
| `network_settings.py` | Settings live in `%APPDATA%\Easy Bitcoin Multisig\settings.json`. |
| `scripts/hwi_entry.py` | Bundles and verifies `libusb-1.0.dll` on Windows, `libusb-1.0.dylib` on macOS. |
| `scripts/build-windows.ps1` | New. Same gate order as `build-macos.sh`, no signing step. |
| `scripts/build-source.sh` | Ships the Windows scripts, the `.ico`, and the manual artwork that used to live under `docs/assets/`. |
| `.github/workflows/build-windows.yml` | New. Candidate-then-promote, mirroring the macOS workflow. |
| `.github/workflows/windows-inputs.yml` | New. Produces the two inputs that only Windows can produce. |
| `requirements-ci.txt` | Adds `certifi`. The desktop suites stand a real CA bundle in for the one the app ships, and Windows has no default OpenSSL verify path — without it those two tests report a skip, and both workflows refuse a suite that skips at all. Test-only: it cannot reach the bundle, which is built from `requirements-desktop-windows.lock`. |

Removed: `docs/` (website), the macOS signing and notarisation scripts, the
macOS-only tests, and the `.command` launcher.

## Bootstrap: two inputs that only Windows can produce

PyInstaller cannot cross-compile, and the desktop dependency lock for Windows
cannot be resolved on macOS (`requirements-desktop.lock` pins `pyobjc` and
`macholib`; the Windows resolve pins `pythonnet` instead). Both inputs are
therefore produced once, reviewed, and committed rather than resolved during a
release build — a build that fetches its own dependencies has nothing to compare
against.

Until both artifacts are committed, the suite reports exactly one skip
(`tests/test_build_sbom.py`, which cannot hash a lock that does not exist yet) and
both workflows refuse a suite that reports any skip. That fail-closed state is
intended: the repository is not buildable before the bootstrap has run once, and
the Windows job's first step says so by name.

1. Dispatch **`.github/workflows/windows-inputs.yml`** (manual, `workflow_dispatch`
   only). It uploads two artifacts:
   * `windows-desktop-lock` → commit as `requirements-desktop-windows.lock`
   * `windows-libusb` → the `libusb-1.0.dll` compiled from the pinned
     `vendor/libusb-1.0.30.tar.bz2`
2. Review the DLL. It is built from a source tarball whose SHA-256 is pinned in
   the workflow and in `vendor/README.md`, with tests, examples and benchmarks
   disabled.
3. Commit it as `vendor/libusb-1.0.dll`.
4. Record its SHA-256 in four places:
   * `$reviewedLibusbSha256` in `scripts/build-windows.ps1`
   * the `win32` entry of `REVIEWED` in `tests/test_libusb_vendor.py`
   * `vendor/README.md`
   * the `LIBUSB_WINDOWS_SHA256` repository variable (used by the workflow)

Until step 4 is done, the build and the vendor test both fail closed rather than
accepting whatever file happens to be in `vendor/`.

## Building locally

```powershell
$env:PYTHON = 'C:\Python312\python.exe'
$env:LIBUSB_SHA256 = '<the reviewed digest>'
.\scripts\build-windows.ps1 0.6.4
```

The script requires Windows x64 and Python 3.10–3.12, refuses a version that does
not match `version.py`, installs `.build-venv` from the hash-locked Windows lock,
verifies the vendored DLL against both the reviewed digest and `LIBUSB_SHA256`,
builds the app and the one-file HWI helper, proves the helper can load the bundled
libusb, and writes
`dist\Bitcoin-Easy-Signer-v<version>-windows-x64.zip`.

A local build is a development check, not a release artifact.

## Releasing

Publication goes through `.github/workflows/build-windows.yml`, which is
manually dispatched only:

1. **Candidate.** Dispatch with `publish=false` (the default). The workflow builds,
   verifies, and uploads the bundle plus `CANDIDATE-MANIFEST.txt`. Nothing is
   created.
2. **Test.** Install the candidate on a real Windows machine. Owner hardware
   acceptance is required when app behaviour changes.
3. **Promote.** Dispatch again *from the same commit* with `publish=true`,
   `allow_unsigned=true`, and `candidate_run_id` set to the candidate run's id.
   The workflow re-downloads that run's artifacts, proves the run id, commit and
   workflow path, verifies `SHA256SUMS`, and only then creates the release.

The build is not code-signed. Windows SmartScreen will warn on first launch, and
`allow_unsigned=true` exists so that an unsigned release is a deliberate decision
rather than an accident. If the project ever buys an Authenticode certificate, the
right change is to sign in `build-windows.ps1` and delete that input.

## Verification

`scripts/verify-windows-bundle.py` runs in the workflow after the build and checks
what PyInstaller will not tell you: that the reviewed icon frames are really inside
the executable (a stock PyInstaller icon shipped once before), that the licences
and `ui.html` are in `_internal`, that no `.dylib` leaked into a Windows bundle,
that the zip and the SBOM exist, and that PyInstaller's own build analyses are
where the SBOM step expects them.

`tests/test_workflow_config.py` is the executable specification of the workflow:
every shell block must parse, every action must be pinned to a commit, the release
job is the only job that may write, checksums are verified before anything is
published, and the release notes are generated from the workflow itself and
checked for the wording that keeps the network story straight.

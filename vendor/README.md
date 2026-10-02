# Pinned embit source for 0.6.4

`embit-upstream-2b375a.tar.gz` is the upstream GitHub archive at commit
`2b375a33bd8926caec7e53d7cfd41b165d196566`, two commits after signed tag
`v0.8.2`. Those commits include the upstream short-read parser correction.
Its SHA-256 is
`3323c77583432be513b346bdc54f86f7ef5fb259e1db0e60975dc51bcbceb0a3`.
At the time of this release, PyPI still offered only embit 0.8.0, and this
upstream source still declared package version `0.8.1` in `pyproject.toml`.

`embit-0.8.2+besa.1.tar.gz` has the same files as that upstream commit. Its
only content edits are `version = "0.8.1"` to `version = "0.8.2+besa.1"` in
`pyproject.toml`, and an explicit `is None` check for an absent input sequence
in `src/embit/psbt.py`. The latter preserves a legal `nSequence=0` instead of
rewriting it to `0xFFFFFFFF`; see upstream issue #146. Its SHA-256 is
`d358dc1bb0faeb532172ed587afd88af9a704926df833b2ec5af8edaaf6bc77b`.
The bundled wheel was built from that source on Python 3.12 using
`setuptools==80.9.0` and `wheel==0.47.0`, without build isolation or dependency
resolution. Its SHA-256 is
`77aec9344be124c0718503eb1f7f3c44dfbb01a929e5b974f7edfe2ad206dce0`.
Both lock files require that exact wheel hash. The wheel is pure Python and
contains no prebuilt crypto library; its MIT license is in the wheel metadata.

The PSBT sequence correction is a local project patch and had not been merged
upstream at the 0.6.3 audit. Re-check this exact source delta whenever embit is
upgraded. The app does not import embit's Liquid/PSET code; adding that surface
requires a separate review. App address parsing also round-trips the decoded
script back to the selected network's canonical address, which rejects unknown
HRPs even though the library helper alone does not.

This vendoring step avoids an unhashable VCS install and any package build
while the release job holds signing credentials. The original archive and
patched source are shipped alongside the wheel so the two local edits
and the bundled code can be independently compared.

## Pinned libusb for the Apple Silicon helper

`libusb-1.0.0.dylib` is the arm64 macOS libusb 1.0.30 binary obtained by the
nonpublishing GitHub Actions macOS-15 run
[`36968320299`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36968320299)
before any signing secret was imported. The run verified its SHA-256 against the
previously reviewed `LIBUSB_SHA256` repository variable and uploaded the exact
input bytes. SHA-256:
`8f6ad6c17c16f1e7769ad2f780ed2ddf98234ae6580cf5d87d9648cee1769201`.
The build and workflow verify the vendored bytes against that pin and do not
install Homebrew packages. PyInstaller signs the two bundled copies; the SBOM
separately records their resulting shipped digests.

`libusb-1.0.30.tar.bz2` is the upstream release source at
`https://github.com/libusb/libusb/releases/download/v1.0.30/libusb-1.0.30.tar.bz2`.
Its SHA-256 is
`fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf`,
matching the Homebrew 1.0.30 formula's source checksum. `libusb-COPYING` is the
unmodified LGPL-2.1-or-later license from that source archive and is bundled
with the app. The dylib is a separate dynamically loaded library.

## Pinned libusb for the Windows helper

Windows ships `libusb-1.0.dll`, compiled from the same pinned
`libusb-1.0.30.tar.bz2` source rather than downloaded as someone else's binary.
That compile can only happen on Windows, so the manual
`.github/workflows/windows-inputs.yml` workflow produces it once, the resulting
bytes are reviewed against the pinned source, and the reviewed file is committed.
PyInstaller bundles two copies: one beside the HWI helper, which
`scripts/hwi_entry.py` loads and verifies, and one inside the `usb1` package,
because libusb1 searches its own package directory at import time before the
helper can choose a library.

| Artifact | SHA-256 |
| --- | --- |
| `vendor/libusb-1.0.dll` | `f7ca6ca40f70e06140e1fab01deedb262464b45bface9eff62c1864e74ff1311` |

That digest is recorded in four places: here, in `$reviewedLibusbSha256` in
`scripts/build-windows.ps1`, in the `win32` entry of `REVIEWED` in
`tests/test_libusb_vendor.py`, and in the `LIBUSB_WINDOWS_SHA256` repository
variable. The Windows build and the vendor test both fail closed if any of the
four is missing or disagrees with the committed file, rather than accept
whatever file happens to be in `vendor/`.

Build settings used, so the DLL can be rebuilt and compared: libusb's own MSVC
project, `msvc\libusb_dll.vcxproj` from inside this same tarball, built with
MSBuild and the Visual Studio 2022 x64 toolset as `Release-MT` -- the `-MT`
variant links the C runtime statically, so the shipped DLL does not make the app
depend on the Visual C++ redistributable. `libusb-1.0.30.tar.bz2` is the
autotools `make dist` archive: it carries `configure`, the MSVC projects and a
pre-generated `msvc\config.h`, but no `CMakeLists.txt`, which is why the MSVC
project is used rather than CMake. `libusb-COPYING` above is the license for both
builds.

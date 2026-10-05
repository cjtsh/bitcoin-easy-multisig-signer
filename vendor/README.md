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

`appimage-runtime-x86_64` is the launcher half of the Linux AppImage, taken
from the AppImage project's `type2-runtime` release
[`20251108`](https://github.com/AppImage/type2-runtime/releases/tag/20251108),
asset `runtime-x86_64`, 944,632 bytes. SHA-256:
`2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d`.
It is a statically linked musl binary with squashfuse and libfuse compiled in,
so the AppImage never asks the host for `libfuse.so.2` -- the missing library
that makes a downloaded AppImage do nothing on a current Ubuntu. The digest is
the trust anchor: it is recorded here, enforced by `scripts/build-linux.sh`
before the runtime is concatenated, and checked by `tests/test_linux_port.py`,
so changed bytes fail the build instead of shipping. The release also publishes
a detached signature; it is not verified because no gpg keyring is trusted in
the build environment. The runtime is concatenated, never patched, and is
LGPL-2.1-or-later like the rest of libfuse.

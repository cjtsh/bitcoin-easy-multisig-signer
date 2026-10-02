# Pinned embit source for 0.6.3

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

This vendoring step avoids an unhashable VCS install and any package build
while the release job holds signing credentials. The original archive and
patched source are shipped alongside the wheel so the two local edits
and the bundled code can be independently compared.

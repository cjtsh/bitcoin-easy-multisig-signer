# Third-party notices

Bitcoin Easy Signer is distributed under the [MIT License](LICENSE). It bundles
and depends on the components below. Licences are reproduced or referenced here
because the Apple Silicon DMG redistributes them; the source archive relies on
the dependency locks in this repository.

This project writes no cryptography and holds no keys. The components below do
the descriptor parsing, transaction construction and device communication.

## Bundled in the macOS DMG

| Component | Version | Licence | Upstream |
| --- | --- | --- | --- |
| [libusb](https://libusb.info/) | 1.0.30 | **LGPL-2.1-or-later** | <https://github.com/libusb/libusb> |
| [embit](https://github.com/diybitcoinhardware/embit) | 0.8.0 | MIT | <https://github.com/diybitcoinhardware/embit> |
| [Bitcoin Core HWI](https://github.com/bitcoin-core/HWI) | 3.2.0 | MIT | <https://github.com/bitcoin-core/HWI> |
| [pywebview](https://pywebview.flowrl.com/) | 6.2.1 | BSD-3-Clause | <https://github.com/r0x0r/pywebview> |
| [PyInstaller](https://pyinstaller.org/) | 6.22.2 | GPL-2.0-or-later **with the PyInstaller exception** | <https://github.com/pyinstaller/pyinstaller> |
| [certifi](https://github.com/certifi/python-certifi) | 2026.7.22 | MPL-2.0 | <https://github.com/certifi/python-certifi> |
| [requests](https://requests.readthedocs.io/) | 2.32.5 | Apache-2.0 | <https://github.com/psf/requests> |
| Python runtime | 3.12 | PSF-2.0 | <https://www.python.org/> |

### libusb (LGPL-2.1-or-later)

`libusb-1.0.0.dylib` is bundled **unmodified**, exactly as installed from the
Homebrew formula and verified against the reviewed `LIBUSB_SHA256` digest during
the build. Its complete corresponding source is available from the upstream
repository linked above, and the exact version bundled is recorded in
`BUILD-SBOM.json` alongside its SHA-256.

The LGPL requires that a recipient be able to replace the library. Because the
`libusb` dynamic library ships as a separate file inside the application bundle
rather than being statically linked into the executable, replacing that file
with a compatible build is sufficient. No modification of libusb is made or
required by this project.

### PyInstaller

PyInstaller is GPL-2.0-or-later, but carries an explicit exception permitting
the packaging of other, differently licensed programs with it. This project
relies on that exception: PyInstaller is used only as a build tool, and the
bundled application is MIT-licensed.

## Used in development and CI only, not distributed

| Component | Version | Licence | Purpose |
| --- | --- | --- | --- |
| [PyYAML](https://pyyaml.org/) | 6.0.3 | MIT | Linting the GitHub Actions workflow in the test suite |

## Regenerating this list

The version pins are the ones in `requirements-desktop.lock`,
`requirements.lock` and the workflow. If a dependency is upgraded, update this
table, `LICENSE`-adjacent notices in the bundle, and the licence identifiers in
`scripts/build-sbom.py` in the same change — `AGENTS.md` already requires
dependency upgrades to land with their locks.

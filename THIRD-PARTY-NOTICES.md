# Third-party notices

Bitcoin Easy Signer is maintained and distributed by Bitseeker LLC under the
[MIT License](LICENSE). The table below identifies selected components included
in the Apple Silicon DMG. It is a summary, not a substitute for each component's
full license and copyright notices. Review the upstream project materials and
the exact build's `BUILD-SBOM.json` when redistributing the application.

The app does not accept or store seed words or private keys. It relies on
third-party libraries for cryptographic primitives, transaction handling, and
hardware-device communication; see the component licenses and source projects.

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

`libusb-1.0.0.dylib` is bundled as a separate, unmodified dynamic library. The
fact that a library is dynamically linked does not by itself establish that a
combined application's packaging satisfies every condition of LGPL-2.1.
Redistributors should review the complete license and corresponding-source
requirements for their distribution. The build records the bundled library's
version and digest in `BUILD-SBOM.json`; its source is available from the
upstream project linked above.

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

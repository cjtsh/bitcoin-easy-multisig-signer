# The HWI dependency — devices, version and rebuild triggers

Bitcoin Core HWI (Bitcoin Hardware Wallet Interface) is the single most
consequential dependency in this project. It is the only code that talks to a
hardware signer, so it decides **which devices this app supports**, **which Python
version it builds on**, and **when a rebuild is mandatory**. This file exists so
that none of that has to be rediscovered.

## What it does, and why nothing here replaces it

`hwi` is invoked as a bundled subprocess. This repository contains **no USB
driver, no device protocol and no private-key handling** — by design. Device
discovery, public-identity comparison, all on-device review, and every signing
request go through HWI and the device's own screen.

That is also why a device problem is often an HWI problem, and why upgrading HWI
is the only way to gain support for a new device or a changed firmware.

## The pinned version

| | |
|---|---|
| Version | **`hwi==3.2.0`** |
| Declared by | `requirements-desktop.txt`, hash-locked in `requirements-desktop.lock` |
| Install mode | `--require-hashes`, so only the reviewed artifact can be installed |
| Recorded in | `BUILD-SBOM.json`, published with every release alongside the DMG |
| Home | <https://github.com/bitcoin-core/HWI> |

Because the pin is hash-locked, a change to HWI's `master` branch — including a
compromised one — cannot reach a released build. Only a deliberate version bump
can.

## Bundled HWI helper changes

The app packages stock HWI 3.2.0 behind `scripts/hwi_entry.py`. That wrapper
adds two local diagnostic flags: `--dsh-capabilities` reports whether Jade's
HTTP PIN relay was bundled, and `--dsh-check-libusb` lists USB descriptors
without opening a wallet and reports the resolved bundled libusb path in a
frozen build. Neither flag is an upstream HWI option or a signing command.

The wrapper also patches `usb1.USBDeviceHandle.releaseInterface` to tolerate
`USBErrorNotFound` when a device disappears during enumeration. Other USB
errors still fail. In a frozen build it requires both bundled libusb archive
entries and binds usb1 to the extracted `libusb-1.0.dylib` before HWI can use
USB. This is a deliberate packaging change around HWI, not a change to its
wallet or signing protocol. Recheck it whenever HWI or libusb1 changes.

## Helper identity (CT-49, CT-58)

The helper is identified by **bytes, not by what it says about itself**. Before
0.6.7, `probe.py` believed `hwi --version` if the output merely contained
`3.2.0`, so a planted binary whose whole vocabulary was `hwi-3.2.0` was
accepted. That check is now exact-line membership, and it runs **after** a
byte check that the helper does not get a vote in:

- **Frozen builds** execute the bundled helper beside the app and require
  `hwi.sha256` beside it to match. Each of `scripts/build-macos.sh`,
  `build-linux.sh` and `build-windows.ps1` writes that sidecar from the
  helper it just built and signed; `scripts/build-sbom.py` records the same
  digest as `hwi_helper_sha256` and fails rather than publish an SBOM that
  disagrees with the artifact.
- **Source mode executes no helper binary at all.** It runs the repository's
  own `scripts/hwi_entry.py` under the running interpreter, so there is
  nothing on `PATH` for a neighbour to replace — `shutil.which` is gone from
  `probe.py`. The remaining substitution surface is the `hwilib` that entry
  imports, and `HWI_PAYLOAD_PINS` in `probe.py` pins `hwilib/__init__.py`
  and `hwilib/_cli.py` by SHA-256, hashed by the anchored interpreter.
- **An explicitly named helper** (`--hwi /path/to/hwi`) must carry its own
  `hwi.sha256`. Without one it is refused before it is executed.

**CT-58:** the identity is cached only for the current signing session.
`verify_signer_device` calls `begin_signing_session()`, which clears the cache,
so every signing session re-identifies the helper from its bytes.

## What this dependency decides for the project

1. **The device list.** See below.
2. **The Python version.** HWI 3.2.0 declares `Requires-Python >=3.9,<3.13`, so
   this project builds on **Python 3.12** and cannot move to 3.13 or 3.14 while
   pinned here. This was verified against upstream metadata, and **HWI is the only
   dependency that caps Python below 3.13**. The vendored embit source requires
   Python >=3.10, which remains compatible with the pinned 3.12 build.
3. **When a rebuild is required.** See "When you must act".

## Devices

This app does **not** keep its own device list. It passes `--device-type` and
`--device-path` straight through to HWI, so the authoritative list of supported
hardware is HWI's:

- HWI's device support matrix: <https://hwi.readthedocs.io/en/latest/devices/index.html>

What this project *does* own is the plain-language guidance shown when a device
needs attention. `probe.py` carries tailored advice for:

| Device | Handled here |
|---|---|
| **Ledger** | unlock, open the correct network app, close Ledger Live / Nunchuk if they hold the device |
| **Trezor** | unlock, including passphrase and bootloader prompts |
| **Blockstream Jade** | on-device PIN entry; the app never receives it |
| **Coldcard** | unlock |
| **BitBox** | unlock |

Anything else HWI can drive would be discovered and matched, but would fall back
to generic advice rather than a device-specific instruction.

### OneKey Classic 1S (detection confirmed; owner-verified signing in the dry run)

The owner-connected [OneKey Classic 1S](https://onekey.so/products/onekey-classic-1s/)
was enumerated by direct and bundled HWI 3.2.0 as `type=trezor`,
`label=OneKey Classic 1S`, `model=trezor_1`. OneKey documents that Trezor Compatibility Mode is enabled by
default on Classic 1S; see [OneKey's compatibility guide](https://help.onekey.so/en/articles/12058029-introduction-to-trezor-compatibility-mode-features)
and the [Classic 1S firmware source](https://github.com/OneKeyHQ/firmware-classic1s).
This is HWI's Trezor transport and signing backend, not a separate OneKey HWI
driver. The 0.4.15 candidate preserves HWI's OneKey label in the app and fixes
the hardened-runtime loading of the bundled libusb in its HWI helper.

Enumeration proves only that the host can identify the device. The owner reports
app-driven wallet xpub matching and two verified signer responses with this device
in the 0.4.15 mainnet dry run, which reached the final review and then refused the
mainnet broadcast, as every pre-0.5.0 build does. That is an owner-reported dry
run, not an on-chain payment. The later 0.5.0 candidate went further: the same
device signed a mainnet payment that was broadcast and confirmed on chain. HWI
version and Python remain unchanged.

### The Jade's PIN relay is an HWI-specific trap

A Jade cannot be unlocked at all unless HWI can reach Blockstream's PIN server.
`hwilib` **disables that relay unless `requests` is importable**, so `requests` is
pinned explicitly in `requirements-desktop.txt` and must not be dropped as
"unused". The PIN itself never leaves the device. This dependency has broken the
Jade path before and is easy to remove by accident.

## When you must act

Bump HWI and cut a new release if any of these becomes true:

1. **One of your own devices ships firmware HWI 3.2.0 does not handle.** This is
   the likeliest trigger, and the one pinning cannot protect you from.
2. **You want to support a device HWI 3.2.0 does not know.**
3. **A security fix lands in HWI.** Check its release notes rather than assuming.
4. **You want a newer Python.** Blocked here until HWI widens its range.

A pinned HWI is stable and reproducible. It does **not** track device firmware.
That is the deliberate trade: reliability now, in exchange for an occasional
deliberate upgrade.

## What a version bump costs

Nothing about this is a one-line change. In order:

1. Bump `hwi` in `requirements-desktop.txt`.
2. Regenerate **both** hash-locked files for **Python 3.12**.
3. **Recompute `HWI_PAYLOAD_PINS` in `probe.py`** from the new `hwilib/__init__.py`
   and `hwilib/_cli.py`, and update `test_the_payload_pins_pin_the_published_hwilib_files`
   with the new literals. This is not optional: the pins are what make a
   substituted `hwilib` refuse to run, and a bump that leaves the old pins in
   place fails every source-mode device command. The new digests also go in
   `releases/PATCH-<version>.md`.
4. Update the Python guard in `scripts/build-macos.sh` if the supported range moved.
5. Update the Python pin in **both** workflow jobs (`.github/workflows/build-candidate.yml`).
6. If the Jade PIN relay or any bundled binary changed, re-verify signing on real
   hardware — automated tests use fake devices and cannot cover this.
7. Run the full suite, the Node UI tests, `bash -n`, and the packaged Apple
   Silicon self-checks.
8. Publish a new version. **Never replace an existing release's assets.**

## Checking whether a newer HWI exists

```bash
curl -s https://pypi.org/pypi/hwi/json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin)["info"]; print(d["version"], d["requires_python"])'
```

Worth doing before the mainnet gate, and after any device firmware update.

## Provenance

Recorded so this is a judgement rather than a guess:

| | |
|---|---|
| Owned by | the **`bitcoin-core`** GitHub organization (an organization, not a personal account) |
| Created | August 2017 |
| Licence | **MIT** — fully open source |
| PyPI package owner | Ava Chow (`achow101`) |
| Scale | ~600 stars, ~240 forks |
| Development | commits into `master` through **August 2026**, PGP-signed and OpenTimestamps-stamped |

It is maintained primarily by **one Bitcoin Core maintainer**, with contributions
from a small circle of established Bitcoin Core developers. That is a real
**bus-factor of one** on a critical component — mitigated by the hash-locked pin,
and by the fact that the maintainer and reviewers are long-standing,
well-known figures in this ecosystem.

### Release cadence is not maintenance status

HWI releases when there is a reason to, not on a schedule. Its previous gap was
**3.1.0 (September 2024) → 3.2.0 (February 2026)** — seventeen months. A
seven-month-old release with commits from five weeks ago is normal for this
project, and is not a sign of abandonment. Check the **commit** date, not the
release date, before drawing conclusions.

## Related

- `THIRD-PARTY-NOTICES.md` — HWI's licence and those of the other bundled dependencies.
- `PHASE-HANDOFF.md` — current release status and the remaining mainnet and operator-readiness gates.
- `AGENTS.md` — the Python-version rule and the full release checklist.

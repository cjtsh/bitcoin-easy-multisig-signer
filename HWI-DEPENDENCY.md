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

## What this dependency decides for the project

1. **The device list.** See below.
2. **The Python version.** HWI 3.2.0 declares `Requires-Python >=3.9,<3.13`, so
   this project builds on **Python 3.12** and cannot move to 3.13 or 3.14 while
   pinned here. This was verified against upstream metadata, and **HWI is the only
   dependency that caps Python** — `embit` declares no `Requires-Python` at all.
   Nothing else stands in the way.
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

### OneKey Classic 1S (detection confirmed; signing walkthrough pending)

The owner-connected [OneKey Classic 1S](https://onekey.so/products/onekey-classic-1s/)
was enumerated by direct and bundled HWI 3.2.0 as `type=trezor`,
`label=OneKey Classic 1S`, `model=trezor_1`. OneKey documents that Trezor Compatibility Mode is enabled by
default on Classic 1S; see [OneKey's compatibility guide](https://help.onekey.so/en/articles/12058029-introduction-to-trezor-compatibility-mode-features)
and the [Classic 1S firmware source](https://github.com/OneKeyHQ/firmware-classic1s).
This is HWI's Trezor transport and signing backend, not a separate OneKey HWI
driver. The 0.4.15 candidate preserves HWI's OneKey label in the app and fixes
the hardened-runtime loading of the bundled libusb in its HWI helper.

Enumeration proves only that the host can identify the device. App-driven wallet
xpub matching and a physical Testnet4 or Mutinynet multisig signature still need
the owner's walkthrough. Do not claim tested transaction support until that is
recorded. HWI version and Python remain unchanged.

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
3. Update the Python guard in `scripts/build-macos.sh` if the supported range moved.
4. Update the Python pin in **both** workflow jobs (`.github/workflows/build-candidate.yml`).
5. If the Jade PIN relay or any bundled binary changed, re-verify signing on real
   hardware — automated tests use fake devices and cannot cover this.
6. Run the full suite, the Node UI tests, `bash -n`, and the packaged Apple
   Silicon self-checks.
7. Publish a new version. **Never replace an existing release's assets.**

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

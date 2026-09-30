# Bitcoin Easy Signer

**Current version: 0.4.3** — the [published Apple Silicon test build](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.3). Phases 1–4 are complete with practice-network evidence: confirmed Testnet4 payments signed by Jade, Trezor Safe 3 and Ledger Nano S Plus, and owner-verified Mutinynet payments through the same engine, most recently Ledger + Jade on 0.4.1. Mainnet preparation, signing, and finalization are available for a controlled dry run, but **mainnet broadcast is refused in code**. No real-Bitcoin transaction has ever been prepared, signed, or tested by this app. This is not yet a production recovery tool — read [the risk notice](DISCLAIMER.md). The version-by-version record of changes, corrections and evidence is in [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md).

Bitcoin Easy Signer helps a spouse, estate professional, or other nontechnical person send Bitcoin from an **existing** 2-of-3 multisig wallet. It does not create a wallet, generate keys, or ask for seeds or PINs. The intended screen is simple: open the wallet definition, see the balance, enter a destination, review the payment, approve it on two hardware devices, and confirm the final transaction.

Standing cautions that survive across versions: Mutinynet needs a funded 2-of-3 BSMS wallet, and existing Testnet4 coins cannot move between networks. Very old installed builds (0.2.1) could show stale signing/final details when a new payment was prepared; **never broadcast from a screen that mixes two payments** — close the old app and install the current release. Never send a sweep to work around a missing change path, and never sweep a real wallet merely to test Send All.

## What this version does

- Imports a BSMS 1.0 definition for a 2-of-3 native-SegWit multisig wallet. The app checks its reference receive address, public cosigner identities, and selected network.
- Scans receive and established change branches through a selected Esplora server. A gap-limited scan is an observation, not proof of a complete balance. Derived addresses are disclosed to that server after consent; seeds and private keys remain on hardware.
- Builds a PSBT from confirmed, independently checked previous outputs. Partial sends use a BSMS-declared change branch or the strict BIP48 standard `/1/*` branch for an anchored 2-of-3 native-SegWit sorted wallet. The latter is labelled as standard-derived, since the BSMS does not explicitly declare it. If neither route applies, the owner can explicitly choose **Send All confirmed outputs found by the scan**, producing no change.
- Checks connected hardware signers through bundled Bitcoin Core HWI, asks them to sign, and shows **one box per cosigner** so the missing signer is visible at a glance rather than described in a sentence. Retains only signatures that verify against the reviewed transaction, and discards all returned wallet metadata before finalization. Each device must display the intended payment; the person using the app must check its screen.
- Shows the destination, amount, network, every change output, fee, effective fee rate, and transaction ID together at the final confirmation. Practice-network broadcast requires a separate explicit action. Mainnet broadcast remains disabled.
- After an outgoing payment is accepted, shows a prominent notice that it is waiting for one confirmation and offers **Check again**. Another payment from that wallet is paused until the refreshed explorer state confirms it. Pending incoming funds alone do not pause confirmed outputs.
- In 0.4.0, after that confirmation the app keeps a visible explorer-link receipt for the latest payment in the current browser session. It is cleared when opening a different wallet or changing networks and is not long-term transaction history.
- Can save an unsigned PSBT and, on request, a privacy-limited diagnostic report in Downloads. The report has fixed pass/fail codes and timestamps, without wallet identifiers, balances, transaction bytes, or device paths.

The app uses **one** wallet/PSBT/signing engine. [`network_config.py`](network_config.py) supplies the selected network's address prefix, BIP48 coin type, Esplora endpoint, genesis hash and any custom-Signet checkpoint. A mainnet wallet uses BIP48 coin type `0'`, while both practice networks use `1'`; each network needs its own correct wallet definition and coins. `gui.py` retains explicit mainnet safety gates; there is no separate mainnet transaction implementation.

## Mac installation and one-session test

The published DMG is for Apple Silicon. Until Developer ID enrollment and notarization are complete, it is ad-hoc signed and macOS requires **right-click → Open** on first launch. Verify the download against the release's `SHA256SUMS` before opening it. Do not disable Gatekeeper globally.

Each release's DMG is published only after its downloaded image and checksums are verified. Practice-network evidence to date: on 0.3.2 the owner imported the funded Nunchuk BSMS alone and reported two successful Mutinynet payments, including a second in the same app session (owner-reported, without transaction IDs or diagnostic records for independent verification); on 0.4.1 the owner signed with Ledger and Jade and broadcast a Mutinynet payment that later confirmed on Mutinynet. The 0.4.2 longer Jade authorization wait and 0.4.3 itself are not yet physically tested. Any further payment should still be checked on each hardware device: destination, amount, fee and change must match the intended payment. Save the diagnostic report only if something fails or a reviewer needs evidence; the button is at the bottom of the window. Keep wallet files, xpubs, addresses, PSBTs, and raw signed transactions out of public issue reports and the repository.

If neither declared nor guarded standard change is available, the app offers a no-change Send All path. **Do not sweep a real wallet merely to test this feature.**

## Supported scope and limitations

| Item | Current support (0.4.3) |
| --- | --- |
| Wallet | Existing BSMS 1.0, 2-of-3 P2WSH multisig with xpub origins |
| Networks | Testnet4, Mutinynet and mainnet through one engine; mainnet broadcast disabled |
| Hardware exercised | Jade, Trezor Safe 3, Ledger Nano S Plus — Testnet4 through 0.2.1; Mutinynet on 0.3.2 and 0.4.1. Owner-reported, not independently reproduced; no firmware versions are recorded |
| Distribution | Apple Silicon test DMG, source archive; no trusted/notarized release yet |
| Fees | Mainnet mempool.space guidance for mainnet/Testnet4; Mutinynet's Esplora reference in Mutinynet mode; 1–25 sat/vB and 10,000-sat estimated fee caps |
| Scan | 20-address unused gap, at most 100 addresses per known branch; historical or unusual funds can be missed |
| Recovery | No built-in fee bump, no support for arbitrary wallet policies or legacy address types |

## Developer and reviewer entry point

Read [`AGENTS.md`](AGENTS.md) and [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md) first for current status, safety boundaries and the exact handoff; then [`RELEASE-HISTORY.md`](RELEASE-HISTORY.md) for the version record, and [`CHANGE-ADDRESS-REVIEW.md`](CHANGE-ADDRESS-REVIEW.md) for the BSMS change-path trust boundary. The [original audit](AUDIT-BASELINE-0.1.27.md), the [0.2.0 fix record](SECURITY-REVIEW-0.2.0.md), and [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md) / [`ROADMAP.md`](ROADMAP.md) preserve earlier decisions and phase history. Two independent 0.4.3 audits are recorded: [`AUDIT-DEEPSEEK-0.4.3.md`](AUDIT-DEEPSEEK-0.4.3.md) and [`AUDIT-ZAI-0.4.3.md`](AUDIT-ZAI-0.4.3.md). Both reviewed `main` at `7d622ef`, two documentation-only commits after the `v0.4.3` build commit `e7f97ac`; neither exercised a mainnet transaction or a physical device. Current behavior in source and tests takes precedence over historical descriptions and over any review's description of it.

Use Python 3.12 for the Mac build (HWI 3.2.0 does not support 3.13+). Source tests:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
# PyYAML is only needed to lint the workflow itself. Without it the entire
# workflow-lint module skips itself, which looks exactly like a pass.
.venv/bin/python -m pip install pyyaml==6.0.3
.venv/bin/python -m unittest discover -s tests -q
```

The Mac build installs [`requirements-desktop.lock`](requirements-desktop.lock) with hashes. A reviewed `LIBUSB_SHA256` is mandatory. [`scripts/build-source.sh`](scripts/build-source.sh) creates the source archive; [`scripts/build-macos.sh`](scripts/build-macos.sh) creates the DMG on Apple Silicon. The GitHub workflow is **manual dispatch only** and publishes an immutable version with `BUILD-SBOM.json` and `SHA256SUMS` after its tests and bundled checks pass. Never republish under an existing version; use a new patch version for any correction to a published build.

## External components

- [embit](https://github.com/diybitcoinhardware/embit): descriptors, derivation, Bitcoin transactions and PSBTs.
- [Bitcoin Core HWI](https://github.com/bitcoin-core/HWI): hardware discovery and signing requests; no USB driver or private-key code is written here.
- [pywebview](https://pywebview.flowrl.com/): native Mac WebKit window over the loopback-only local app.
- [PyInstaller](https://pyinstaller.org/): bundled runtime and binaries.
- [Esplora](https://github.com/Blockstream/esplora): public address/UTXO/transaction API and practice-network broadcast endpoints.

These components do not remove the need to verify release provenance, wallet policy, signer display, and the final transaction.

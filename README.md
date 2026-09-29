# Bitcoin Easy Signer

Bitcoin Easy Signer helps a spouse, estate professional, or other nontechnical person send Bitcoin from an **existing** 2-of-3 multisig wallet. It does not create a wallet, generate keys, or ask for seeds or PINs. The intended screen is simple: open the wallet definition, see the balance, enter a destination, review the payment, approve it on two hardware devices, and confirm the final transaction.

**[Version 0.2.2](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.2.2) is an experimental test build.** Testnet4 signing and broadcast were demonstrated in earlier versions with Jade, Trezor Safe 3, and Ledger Nano S Plus; two transactions confirmed. The 0.2.0 build rejected legitimate Jade and Ledger signing responses because HWI reordered PSBT fields. Version 0.2.1 repaired that comparison and broadcast another Testnet4 payment after two verified signatures. Version 0.2.2 adds a clear waiting-for-confirmation notice and pauses the next payment until one block confirms the prior outgoing payment. Mainnet preparation, signing, and finalization are available for a controlled dry run, but **mainnet broadcast is refused in code**. No real-Bitcoin transaction has been tested. This is not yet a production recovery tool. Read [the risk notice](DISCLAIMER.md).

The `warm-0.3.0` branch is development work, not a released build. It adds Mutinynet as a faster practice network through the **same** wallet/signing engine, fixes an old signing/final panel remaining visible below a new payment, and hardens transaction state and broadcast checks. Its scope and remaining gates are in [`PLAN-0.3.0.md`](PLAN-0.3.0.md) and [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md). Mutinynet needs a new funded 2-of-3 BSMS wallet; the existing Testnet4 funds cannot move between these networks. The 0.2.1 app can show stale signing/final details when a new payment is prepared: **close and reopen it before making another payment if the screen mixes two transactions**. No completed 0.3.0 DMG is available yet.

## What this version does

- Imports a BSMS 1.0 definition for a 2-of-3 native-SegWit multisig wallet. The app checks its reference receive address, public cosigner identities, and selected network.
- Scans receive and declared change branches through a selected Esplora server. A gap-limited scan is an observation, not proof of a complete balance. Derived addresses are disclosed to that server after consent; seeds and private keys remain on hardware.
- Builds a PSBT from confirmed, independently checked previous outputs. Partial sends require a change branch established by the descriptor or the BSMS path restrictions. A receive-only export can **Send All confirmed outputs found on its scanned receiving addresses**, producing no change output. The app does not guess change ownership.
- Checks connected hardware signers through bundled Bitcoin Core HWI, asks them to sign, rejects a returned PSBT that changes reviewed wallet data, and verifies each signature before finalization. Each device must display the intended payment; the person using the app must check its screen.
- Shows the destination, amount, network, every change output, fee, effective fee rate, and transaction ID together at the final confirmation. Testnet4 broadcast requires a separate explicit action. Mainnet broadcast remains disabled.
- After an outgoing payment is accepted, shows a prominent notice that it is waiting for one confirmation and offers **Check again**. Another payment from that wallet is paused until the refreshed explorer state confirms it. Pending incoming funds alone do not pause confirmed outputs.
- Can save an unsigned PSBT and, on request, a privacy-limited diagnostic report in Downloads. The report has fixed pass/fail codes and timestamps, without wallet identifiers, balances, transaction bytes, or device paths.

The app uses **one** wallet/PSBT/signing engine. [`network_config.py`](network_config.py) supplies the selected network's address prefix, BIP48 coin type, Esplora endpoint, genesis hash and any custom-Signet checkpoint. The published 0.2.2 build has Testnet4 and mainnet; the in-progress 0.3.0 branch adds Mutinynet. `gui.py` retains explicit mainnet safety gates; there is no separate mainnet transaction implementation.

## Mac installation and one-session test

The published DMG is for Apple Silicon. Until Developer ID enrollment and notarization are complete, it is ad-hoc signed and macOS requires **right-click → Open** on first launch. Verify the download against the release's `SHA256SUMS` before opening it. Do not disable Gatekeeper globally.

No separate 0.2.2 installation or payment was requested for the confirmation notice. The prior Testnet4 payment has now confirmed. The owner found a stale signing/final panel while preparing the next payment in installed 0.2.1; its outcome and a new Trezor signature have not been reported. The next requested owner install is the completed 0.3.0 milestone. Save the diagnostic report only if something fails or a reviewer needs evidence; the button is at the bottom of the window. Do not send wallet files, xpubs, addresses, PSBTs, or raw signed transactions to an agent.

If the import is receive-only, the app offers a no-change Send All path instead of guessing a change branch. **Do not sweep a real wallet merely to test this feature.**

## Supported scope and limitations

| Item | Published 0.2.2 support |
| --- | --- |
| Wallet | Existing BSMS 1.0, 2-of-3 P2WSH multisig with xpub origins |
| Networks | Testnet4 and mainnet through one engine; mainnet broadcast disabled |
| Hardware tested before 0.2.0 | Jade, Trezor Safe 3, Ledger Nano S Plus on the owner's Testnet4 wallet |
| Distribution | Apple Silicon test DMG, source archive; no trusted/notarized release yet |
| Fees | Mainnet mempool.space guidance on both networks; 1–25 sat/vB and 10,000-sat estimated fee caps. The 0.3.0 branch uses Mutinynet's own Esplora fee reference in Mutinynet mode. |
| Scan | 20-address unused gap, at most 100 addresses per known branch; historical or unusual funds can be missed |
| Recovery | No built-in fee bump, no support for arbitrary wallet policies or legacy address types |

## Developer and reviewer entry point

Read [`AGENTS.md`](AGENTS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), the [original audit](AUDIT-BASELINE-0.1.27.md), the [0.2.0 fix record](SECURITY-REVIEW-0.2.0.md), [the 0.2.1 patch record](PATCH-0.2.1.md), and [the 0.2.2 patch record](PATCH-0.2.2.md) before editing. [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md) preserves earlier decisions; [`ROADMAP.md`](ROADMAP.md) preserves phase acceptance history. Current behavior in source and tests takes precedence over historical descriptions.

Use Python 3.12 for the Mac build (HWI 3.2.0 does not support 3.13+). Source tests:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m unittest discover -s tests -q
```

The Mac build installs [`requirements-desktop.lock`](requirements-desktop.lock) with hashes. A reviewed `LIBUSB_SHA256` is mandatory. [`scripts/build-source.sh`](scripts/build-source.sh) creates the source archive; [`scripts/build-macos.sh`](scripts/build-macos.sh) creates the DMG on Apple Silicon. The GitHub workflow is **manual dispatch only** and publishes an immutable version with `BUILD-SBOM.json` and `SHA256SUMS` after its tests and bundled checks pass. Never republish under an existing version; use 0.2.3 for any correction after 0.2.2 is published.

## External components

- [embit](https://github.com/diybitcoinhardware/embit): descriptors, derivation, Bitcoin transactions and PSBTs.
- [Bitcoin Core HWI](https://github.com/bitcoin-core/HWI): hardware discovery and signing requests; no USB driver or private-key code is written here.
- [pywebview](https://pywebview.flowrl.com/): native Mac WebKit window over the loopback-only local app.
- [PyInstaller](https://pyinstaller.org/): bundled runtime and binaries.
- [Esplora](https://github.com/Blockstream/esplora): public address/UTXO/transaction API and Testnet4 broadcast endpoint.

These components do not remove the need to verify release provenance, wallet policy, signer display, and the final transaction.
